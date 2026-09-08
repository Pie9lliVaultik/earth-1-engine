"""EARTH1_SOCIAL_TRANSMISSION — the transmission-off arm switch.

Founder ruling 2026-09-08: emergence experiment (APPARATUS_CYCLE_1.md /
RULING_REQUEST_BINARY_READOUT.md cycle). The flag (default 'on') gates
the dyadic influence delta at its single shared computation point
(earth1.influence.dyadic_move), which feeds BOTH canonical application
sites: influence.propagate (tie encounters) and feed.feed_tick (the
hub/media path). 'off' must be STREAM-PRESERVING: identical RNG draws,
identical encounter structure (partners, susceptibility, evidence
mechanism), zero applied force movement.

Pinned constants below were captured on THIS host from pristine HEAD
29be962 ("Apparatus Cycle 1") on 2026-09-08, before the gate landed:
numpy 2.0.2, scipy 1.13.1, python 3.9.6, macOS arm64. They pin this
host's trajectory; on a different platform regenerate them with the
documented snippets rather than trusting cross-platform float identity.
"""
import copy
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from earth1 import influence
from earth1.influence import new_day_scratch, propagate, update_conviction

FLAG = "EARTH1_SOCIAL_TRANSMISSION"

# Pre-change day-10 world hash: fresh process, freeze09 env sourced,
# birth_world(2000, 42, substrate="c2plus_v1"), 10 x live_one_day with
# np.random.default_rng(42), earth1.persistence.world_hash. Captured at
# pristine HEAD 29be962 (scratchpad run_day10.py protocol, 2026-09-08).
PRE_CHANGE_DAY10_HASH = (
    "287df2dd88f37e86b6b236624fdf7a636caaf031eda67b85b1df3115f1e5191c")

# Pre-change small-propagate expectation (test 2): sha256 over
# (propagate output, drive_acc, enc_count, update_conviction output)
# bytes for the _small_case below at day=3. Captured at pristine HEAD
# 29be962 before the gate landed.
PRE_CHANGE_SMALL_PROPAGATE_HASH = (
    "7d7bff698d4af602de17db575b6f47f6d16b7aaf1defe808343172e187f62c18")


def _small_case(n=64, k=8, seed=20260908):
    """Deterministic small world for the unit tests. MUST stay byte-for-
    byte identical to the pre-change capture snippet (constant above)."""
    r = np.random.default_rng(seed)
    forces = r.random((n, k))
    alpha = r.random(n)
    sus = r.random((n, k)) * 0.9 + 0.1
    rows = np.repeat(np.arange(n), 3)
    cols = (rows + r.integers(1, n, rows.size)) % n
    adj = sparse.csr_matrix((r.random(rows.size) + 0.1, (rows, cols)),
                            shape=(n, n))
    adj = adj + adj.T
    return forces, alpha, adj, sus


# bound ONCE at import so a spy never wraps another arm's spy
_ORIG_SAMPLE_PARTNERS = influence.sample_partners


class _PartnerSpy:
    """Wraps influence.sample_partners: records, per encounter, the rng
    state at entry, the rng state after the draw, and copies of the
    (partner, has) outputs — the registered draw-sequence instrument."""

    def __init__(self):
        self.entry_states = []
        self.exit_states = []
        self.partners = []
        self.has = []
        self._orig = _ORIG_SAMPLE_PARTNERS

    def __call__(self, csr, rng):
        self.entry_states.append(repr(rng.bit_generator.state))
        partner, has = self._orig(csr, rng)
        self.exit_states.append(repr(rng.bit_generator.state))
        self.partners.append(partner.copy())
        self.has.append(has.copy())
        return partner, has


def _run_propagate_arm(monkeypatch, flag_value, k=None):
    """One arm of the paired experiment: identical inputs, spy on the
    partner sampler, flag set (or unset) for this call only."""
    forces, alpha, adj, sus = _small_case()
    if flag_value is None:
        monkeypatch.delenv(FLAG, raising=False)
    else:
        monkeypatch.setenv(FLAG, flag_value)
    spy = _PartnerSpy()
    monkeypatch.setattr(influence, "sample_partners", spy)
    scratch = new_day_scratch(forces.shape[0])
    kwargs = {} if k is None else {"k": k}
    out = propagate(forces, alpha, adj, day=3, scratch=scratch,
                    susceptibility=sus, **kwargs)
    return forces, out, scratch, spy


# ── (1) flag off: zero movement, stream-preserving ────────────────────

def test_flag_off_forces_bit_identical_and_draws_match_flag_on(monkeypatch):
    f_in_on, out_on, scr_on, spy_on = _run_propagate_arm(monkeypatch, None)
    f_in_off, out_off, scr_off, spy_off = _run_propagate_arm(
        monkeypatch, "off")

    # zero applied movement: bit-identical before/after the influence
    # step (propagate copies, so compare bytes of output vs input)
    assert out_off.tobytes() == f_in_off.tobytes()
    # the on arm actually moved — the gate gates something real
    assert out_on.tobytes() != f_in_on.tobytes()

    # identical draw sequence: rng states at every encounter's entry and
    # exit, and the drawn partners/has masks, match the flag-on arm
    assert spy_off.entry_states == spy_on.entry_states
    assert spy_off.exit_states == spy_on.exit_states
    assert len(spy_off.partners) == len(spy_on.partners) == 3
    for p_off, p_on in zip(spy_off.partners, spy_on.partners):
        assert np.array_equal(p_off, p_on)
    for h_off, h_on in zip(spy_off.has, spy_on.has):
        assert np.array_equal(h_off, h_on)

    # evidence mechanism identical: encounter counts match exactly; the
    # accumulated drive of encounters 2..k reflects "forces not moving"
    # (flag-on forces drift between encounters), which is the registered
    # semantics — the k=1 test below pins full bitwise evidence identity
    assert np.array_equal(scr_off.enc_count, scr_on.enc_count)


def test_flag_off_first_encounter_evidence_bit_identical(monkeypatch):
    # with a single encounter there is no intra-day force drift, so the
    # whole evidence scratch must be bit-identical between arms
    _, _, scr_on, _ = _run_propagate_arm(monkeypatch, None, k=1)
    _, _, scr_off, _ = _run_propagate_arm(monkeypatch, "off", k=1)
    assert scr_off.drive_acc.tobytes() == scr_on.drive_acc.tobytes()
    assert np.array_equal(scr_off.enc_count, scr_on.enc_count)


def test_flag_is_read_per_call_not_at_import(monkeypatch):
    forces, alpha, adj, sus = _small_case()

    def run():
        scratch = new_day_scratch(forces.shape[0])
        return propagate(forces, alpha, adj, day=3, scratch=scratch,
                         susceptibility=sus)

    monkeypatch.setenv(FLAG, "off")
    assert run().tobytes() == forces.tobytes()
    # same process, flag flipped: the very next call must transmit —
    # proves function-level os.environ.get, no import-time cache
    monkeypatch.setenv(FLAG, "on")
    assert run().tobytes() != forces.tobytes()
    monkeypatch.delenv(FLAG)
    assert run().tobytes() != forces.tobytes()


def test_flag_off_gates_feed_hub_media_site_too(monkeypatch, tiny_world):
    # APPLICATION SITE 2: earth1/feed.py::feed_tick imports dyadic_move
    # at call time, so the same gate must zero the hub/media delta
    from earth1.feed import feed_tick
    w_on = tiny_world
    w_off = copy.deepcopy(tiny_world)

    monkeypatch.delenv(FLAG, raising=False)
    scr_on = new_day_scratch(w_on.civ.n)
    before_on = w_on.civ.forces.copy()
    st_on = feed_tick(w_on.civ, w_on.feed, w_on.civ.alpha, day=1,
                      scratch=scr_on)
    assert st_on["feed_readers"] > 0          # the case is non-degenerate
    assert w_on.civ.forces.tobytes() != before_on.tobytes()

    monkeypatch.setenv(FLAG, "off")
    scr_off = new_day_scratch(w_off.civ.n)
    before_off = w_off.civ.forces.copy()
    st_off = feed_tick(w_off.civ, w_off.feed, w_off.civ.alpha, day=1,
                       scratch=scr_off)
    assert w_off.civ.forces.tobytes() == before_off.tobytes()
    # same encounter structure on the feed graph: same readers, and the
    # single feed encounter's evidence is bit-identical (f_pre is the
    # same in both arms — evidence accumulates BEFORE the move)
    assert st_off["feed_readers"] == st_on["feed_readers"]
    assert scr_off.drive_acc.tobytes() == scr_on.drive_acc.tobytes()
    assert np.array_equal(scr_off.enc_count, scr_on.enc_count)


# ── (2) flag on / unset: bit-identical to pre-change code ─────────────

@pytest.mark.parametrize("flag_value", [None, "on"])
def test_flag_on_default_matches_prechange_expectation(monkeypatch,
                                                       flag_value):
    if flag_value is None:
        monkeypatch.delenv(FLAG, raising=False)
    else:
        monkeypatch.setenv(FLAG, flag_value)
    forces, alpha, adj, sus = _small_case()
    scratch = new_day_scratch(forces.shape[0])
    out = propagate(forces, alpha, adj, day=3, scratch=scratch,
                    susceptibility=sus)
    h = hashlib.sha256()
    h.update(out.tobytes())
    h.update(scratch.drive_acc.tobytes())
    h.update(scratch.enc_count.tobytes())
    alpha2 = update_conviction(out, alpha, adj, scratch=scratch)
    h.update(alpha2.tobytes())
    assert h.hexdigest() == PRE_CHANGE_SMALL_PROPAGATE_HASH


# ── (3) rule-2 trajectory neutrality, flag UNSET, fresh process ───────

_DAY10_PROBE = """
import sys
sys.path.insert(0, {root!r})
import numpy as np
from earth1 import persistence
from earth1.alive import birth_world, live_one_day
w = birth_world(2000, 42, substrate="c2plus_v1")
rng = np.random.default_rng(42)
for _ in range(10):
    live_one_day(w, rng)
print(persistence.world_hash(w))
"""


def _freeze09_env():
    """Exactly the freeze09 flag set: ambient EARTH1_* stripped, then
    scripts/env/freeze09.env exports applied. The arm flag stays UNSET."""
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("EARTH1_")}
    for line in (ROOT / "scripts" / "env" / "freeze09.env").read_text() \
            .splitlines():
        line = line.strip()
        if line.startswith("export ") and "=" in line:
            key, val = line[len("export "):].split("=", 1)
            env[key.strip()] = val.strip()
    env.pop(FLAG, None)
    return env


def test_day10_trajectory_neutrality_rule2_flag_unset(tmp_path):
    probe = tmp_path / "day10_probe.py"
    probe.write_text(_DAY10_PROBE.format(root=str(ROOT)))
    res = subprocess.run([sys.executable, str(probe)], cwd=str(ROOT),
                         env=_freeze09_env(), capture_output=True,
                         text=True, timeout=300)
    assert res.returncode == 0, res.stderr
    assert res.stdout.strip() == PRE_CHANGE_DAY10_HASH


# ── (4) smoke: flag off, forces still move; convergence is weaker ─────

def test_flag_off_material_channels_move_but_convergence_weaker(
        monkeypatch, tiny_world):
    """5-day 2k paired arms. With transmission off, forces must still
    change (life circumstances, contagion, weather, relax-toward-target
    are ungated) but neighbour force-convergence must be weaker — the
    dyadic channel IS the convergence channel. Smoke assertion only,
    not a calibrated claim."""
    from earth1.alive import live_one_day

    start = tiny_world.civ.forces.copy()
    coo = tiny_world.civ.adj.tocoo()      # fixed day-0 dyads: isolates
    ii, jj = coo.row.copy(), coo.col.copy()   # forces from rewiring

    def disagreement(forces):
        return float(np.abs(forces[ii] - forces[jj]).mean())

    def run_arm(world, flag_value):
        if flag_value is None:
            monkeypatch.delenv(FLAG, raising=False)
        else:
            monkeypatch.setenv(FLAG, flag_value)
        rng = np.random.default_rng(7)
        for _ in range(5):
            live_one_day(world, rng)
        return world.civ.forces

    f_on = run_arm(copy.deepcopy(tiny_world), None)
    f_off = run_arm(tiny_world, "off")

    # material channels still move the world with transmission off
    assert f_off.tobytes() != start.tobytes()
    # ...but neighbours converge less than they do with transmission on
    assert disagreement(f_off) > disagreement(f_on)
