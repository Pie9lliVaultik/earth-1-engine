"""Probe-1 repair — cascade cooldown negative controls (founder
contract, 0.8). The flag EARTH1_CASCADE_COOLDOWN=1 restores the
DECLARED event semantics; default-off preserves incumbent behavior
bit-exactly (pinned hashes untouched).

H-CASCADE-1 (ops/alive/H_CASCADE_1.md): identity_collapse and
collective_surge now fire on episode ENTRY only, so the cooldown-only
contract is exercised here on panic_cascade (ECON<0.3, FEAR>0.5), whose
semantics are unchanged (KA7). Episode-entry semantics for the scoped
rules are tested at the bottom of this file.
"""
import os

import numpy as np
import pytest

from earth1 import persistence
from earth1.alive import birth_world, live_one_day
from earth1.thresholds import TRANSITION_RULES
from earth1.types import Force

RULE = "panic_cascade"
SURGE = next(r for r in TRANSITION_RULES if r.name == RULE)


def _force_hot(w, everywhere=True, country=None):
    """Hold panic_cascade conditions true (ECON<0.3, FEAR>0.5) for
    all agents or one country."""
    mask = np.ones(w.civ.n, dtype=bool) if everywhere \
        else (w.civ.country == country)
    w.civ.forces[mask, Force.ECONOMICS] = 0.1
    w.civ.forces[mask, Force.FEAR] = 0.8


def _run_day(w, rng):
    _force_hot(w)
    return live_one_day(w, rng)


@pytest.fixture
def flag(monkeypatch):
    monkeypatch.setenv("EARTH1_CASCADE_COOLDOWN", "1")


def test_no_refire_inside_cooldown(flag):
    w = birth_world(2000, 3)
    rng = np.random.default_rng(3)
    st1 = _run_day(w, rng)
    assert st1["cascades_fired"] > 0, "trigger did not arm"
    fired_day1 = {k: v for k, v in
                  w.chronicle.cascade_last_fired.items()
                  if k[0] == RULE}
    assert fired_day1, "no cooldown state recorded"
    st2 = _run_day(w, rng)
    refired = [k for k, v in w.chronicle.cascade_last_fired.items()
               if k[0] == RULE and v >= 1]
    assert not refired, "collective_surge refired inside its cooldown"
    assert st2["cascades_fired"] < st1["cascades_fired"]


def test_eligible_again_after_cooldown(flag):
    w = birth_world(2000, 3)
    rng = np.random.default_rng(3)
    _run_day(w, rng)
    state = w.chronicle.cascade_last_fired
    keys = [k for k in state if k[0] == RULE]
    # fast-forward: pretend the fire happened beyond the cooldown
    for k in keys:
        state[k] = -int(SURGE.cooldown_days) - 1
    st = _run_day(w, rng)
    assert any(state[k] >= 1 for k in keys), \
        "rule did not become eligible after its cooldown expired"
    assert st["cascades_fired"] > 0


def test_locality_independence(flag):
    w = birth_world(2000, 3)
    rng = np.random.default_rng(3)
    _run_day(w, rng)                      # everyone fires day 1
    state = w.chronicle.cascade_last_fired
    keys = sorted(k for k in state if k[0] == RULE)
    assert len(keys) >= 2, "need >=2 localities for independence"
    # locality A ready again, locality B still cooling
    state[keys[0]] = -100
    before = dict(state)
    _run_day(w, rng)
    assert state[keys[0]] >= 1, "eligible locality was blocked"
    assert state[keys[1]] == before[keys[1]], \
        "cooling locality fired — cooldowns are not per-locality"


def test_restart_preserves_cooldown_state(flag, tmp_path):
    w = birth_world(2000, 3)
    rng = np.random.default_rng(3)
    _run_day(w, rng)
    state_before = dict(w.chronicle.cascade_last_fired)
    assert state_before
    persistence.save_world(w, tmp_path / "w.pkl",
                           np.random.default_rng(1))
    w2, _r, _i = persistence.load_world(tmp_path / "w.pkl")
    assert dict(w2.chronicle.cascade_last_fired) == state_before, \
        "exact restart lost cascade cooldown state"
    # and the restarted world still refuses to refire
    st = _run_day(w2, np.random.default_rng(4))
    refired = [k for k, v in
               w2.chronicle.cascade_last_fired.items()
               if k[0] == RULE and v >= 1]
    assert not refired


def test_cooldown_is_unconditional_post_canonicalization(monkeypatch):
    """Phase 0.5 Program 3: the cooldown contract is canonical physics —
    no environment flag can switch it off. The pathological
    daily-refiring reference lives on only as the Stage-B broken twin
    (the resurrected accumulator), never as a runtime option."""
    monkeypatch.setenv("EARTH1_CASCADE_COOLDOWN", "0")
    w = birth_world(2000, 3)
    rng = np.random.default_rng(3)
    _run_day(w, rng)
    _run_day(w, rng)
    assert isinstance(getattr(w.chronicle, "cascade_last_fired", None),
                      dict), "cooldown state must exist regardless of env"
    # a (rule, locality) that fired cannot fire again within its cooldown
    from earth1.thresholds import TRANSITION_RULES
    cd = {r.name: r.cooldown_days for r in TRANSITION_RULES}
    for (rule, loc), last in list(w.chronicle.cascade_last_fired.items()):
        assert w.day - last <= cd[rule]


def test_never_triggered_rule_has_no_state(flag):
    w = birth_world(2000, 3)
    rng = np.random.default_rng(3)
    # polarization_lock needs IDENTITY>0.8 — hold it low
    w.civ.forces[:, Force.IDENTITY] = 0.1
    _run_day(w, rng)
    assert not any(k[0] == "polarization_lock"
                   for k in w.chronicle.cascade_last_fired), \
        "a never-triggered rule acquired cooldown state"


# ── H-CASCADE-1: episode-entry semantics for the scoped rules ──────
def _surge_hot(w, on=True):
    w.civ.forces[:, Force.COLLECTIVE] = 0.9 if on else 0.1
    w.civ.forces[:, Force.FEAR] = 0.8 if on else 0.1


def _surge_fires(w):
    return sorted(r["day"] for r in (w.chronicle.cascade_residues or [])
                  if r["rule"] == "collective_surge")


def test_episode_entry_no_refire_after_cooldown():
    """hot→hot never fires, even when the cooldown (20d) has elapsed."""
    w = birth_world(2000, 3)
    rng = np.random.default_rng(3)
    _surge_hot(w, False); live_one_day(w, rng)       # establish cold state
    for _ in range(45):
        _surge_hot(w, True); live_one_day(w, rng)
    # a locality crossing pop 9→10 is a genuine cold→hot entry (pop>=10
    # is part of "hot"); judge only localities that fired on entry day
    # 1 — none of them may fire again while continuously hot
    res = [r for r in w.chronicle.cascade_residues
           if r["rule"] == "collective_surge"]
    entry = {r["loc"] for r in res if r["day"] == 1}
    assert entry
    later = [r for r in res if r["loc"] in entry and r["day"] > 1]
    assert not later, later


def test_episode_entry_fires_on_reentry():
    w = birth_world(2000, 3)
    rng = np.random.default_rng(3)
    _surge_hot(w, False); live_one_day(w, rng)
    _surge_hot(w, True); live_one_day(w, rng)
    for _ in range(25):
        _surge_hot(w, False); live_one_day(w, rng)
    _surge_hot(w, True); live_one_day(w, rng)
    days = sorted(set(_surge_fires(w)))
    assert len(days) == 2 and days[1] - days[0] == 26, days


def test_episode_initialization_no_day_zero_event():
    w = birth_world(2000, 3)
    rng = np.random.default_rng(3)
    _surge_hot(w, True); live_one_day(w, rng)         # already hot at init
    assert _surge_fires(w) == []
    assert any(k[0] == "collective_surge"
               for k in w.chronicle.cascade_episode_active)


def test_episode_state_persists(tmp_path):
    w = birth_world(2000, 3)
    rng = np.random.default_rng(3)
    _surge_hot(w, False); live_one_day(w, rng)
    _surge_hot(w, True); live_one_day(w, rng)
    ep = set(w.chronicle.cascade_episode_active)
    persistence.save_world(w, tmp_path / "w.pkl", np.random.default_rng(1))
    w2, _r, _i = persistence.load_world(tmp_path / "w.pkl")
    assert set(w2.chronicle.cascade_episode_active) == ep
    n = len(_surge_fires(w2))
    _surge_hot(w2, True); live_one_day(w2, np.random.default_rng(4))
    assert len(_surge_fires(w2)) == n                  # no duplicate
