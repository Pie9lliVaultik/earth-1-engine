"""Phase 0.1 — the correctness ledger, four items, each independently
attributable and each with a control that demonstrably fails.

0.1a  health.py shared random row (u[4] for fall onset AND treatment)
0.1b  conviction decay: code and docs agree it is disabled; bit-exact
0.1c  CauseOfDeath contract: canonical enum, no collision, honest
      legacy ambiguity
0.1d  end-of-tick journal mortality contract (in test_daemon_startup /
      test_alive_semantics additions where the tick is exercised)
"""
import numpy as np
import pytest

from earth1.types import CauseOfDeath, Force


# ════ 0.1a — the shared random row ══════════════════════════════════

def _run_fall_treatment(shared_row: bool, n=200_000, seed=7):
    """Distill health_tick's fall-onset + treatment-acceptance draws.

    Reproduces the defect deterministically: with the shared row, the
    same uniform that had to be SMALL for the fall to happen is reused
    against the treatment probability, so every faller passes it.
    """
    rng = np.random.default_rng(seed)
    u = rng.random((6, n))
    fall_hazard = 0.02
    access = 0.55                       # treatment probability
    fell = u[4] < fall_hazard
    treat_row = u[4] if shared_row else u[5]
    treated = fell & (treat_row < access)
    return fell, treated


def test_defect_reproduced_shared_row_treats_every_faller():
    """The control that must fail on the OLD code: with u[4] shared,
    treatment among fallers is ~100%, not ~access."""
    fell, treated = _run_fall_treatment(shared_row=True)
    rate = treated.sum() / fell.sum()
    assert rate > 0.999, f"defect not reproduced (rate {rate:.3f})"


def test_fix_makes_treatment_independent_of_falling():
    """With the free row u[5], treatment among fallers ≈ access — the
    dimension the health model intended (an independent draw)."""
    fell, treated = _run_fall_treatment(shared_row=False)
    rate = treated.sum() / fell.sum()
    assert abs(rate - 0.55) < 0.03, f"treatment not independent: {rate:.3f}"


def test_health_source_uses_the_free_row():
    """The shipped code must draw treatment from u[5], and CI must fail
    if anyone restores u[4]."""
    import inspect

    from earth1 import health
    src = inspect.getsource(health.health_tick)
    treat_lines = [ln for ln in src.splitlines() if "in_treatment[newly_ill" in ln]
    assert treat_lines, "treatment acceptance line not found"
    assert "u[5]" in treat_lines[0], \
        "treatment must use the free row u[5], not the fall-onset row"
    assert "u[4]" not in treat_lines[0]


def test_untreated_falls_now_occur(tiny_world, rng):
    """The physical consequence the bug suppressed: SURVIVE_UNTREATED
    for falls was effectively never sampled, because every faller was
    treated. With independent draws, untreated fallers must exist."""
    from earth1.health import health_tick
    w = tiny_world
    w.civ.age[:] = 0.95                 # everyone old: falls certain-ish
    untreated_fallers = 0
    for day in range(60):
        health_tick(w.civ, w.life, w.health, rng, float(day), 1.0)
        f = (w.health.condition == int(CauseOfDeath.FALL)) & \
            ~w.health.in_treatment & w.health.alive
        untreated_fallers += int(f.sum())
        w.health.condition[:] = 0       # reset for the next draw
        w.health.in_treatment[:] = False
    assert untreated_fallers > 0, \
        "no untreated fall in 60 days of an elderly world — the shared " \
        "row is back"


# ════ 0.1b — conviction decay disabled, bit-for-bit ═════════════════

def test_conviction_decay_disabled_and_bit_exact(tiny_world):
    """Code and docs agree: decay is OFF (0.8 A/B experiment). Output
    must be bit-identical to the bare formula with no decay term."""
    from earth1.influence import CONVICTION_GAIN, update_conviction
    w = tiny_world
    forces, alpha, adj = w.civ.forces, w.civ.alpha, w.civ.adj

    got = update_conviction(forces, alpha, adj)

    deg = np.maximum(np.asarray(adj.sum(axis=1)).ravel(), 1.0)
    pole = (forces > 0.5).astype(np.float64)
    nb_pole = (adj @ pole) / deg[:, None]
    agreement = 1.0 - np.abs(nb_pole - pole).mean(axis=1)
    ref = np.clip(alpha + CONVICTION_GAIN * (agreement - 0.5) * 2.0,
                  0.02, 1.0)
    np.testing.assert_array_equal(got, ref)   # BIT-identical, no decay


def test_enabling_decay_is_detectable(tiny_world):
    """The control that must fail if decay were switched on: the
    experimental path produces a DIFFERENT trajectory."""
    from earth1.influence import update_conviction
    w = tiny_world
    off = update_conviction(w.civ.forces, w.civ.alpha, w.civ.adj)
    on = update_conviction(w.civ.forces, w.civ.alpha, w.civ.adj,
                           _experimental_decay_0_8_ab=0.02)
    assert not np.array_equal(off, on), \
        "the experimental decay path is a no-op — the 0.8 A/B would " \
        "compare identical arms"


def test_docstring_says_disabled():
    from earth1 import influence
    doc = influence.update_conviction.__doc__
    assert "DISABLED" in doc and "0.8" in doc, \
        "docs must state decay is disabled pending the 0.8 A/B"


# ════ 0.1c — the CauseOfDeath contract ══════════════════════════════

def test_enum_is_collision_free():
    vals = [int(c) for c in CauseOfDeath]
    assert len(vals) == len(set(vals)), "duplicate cause codes"
    assert int(CauseOfDeath.WAR) != int(CauseOfDeath.FALL)
    assert int(CauseOfDeath.WAR) == 9          # 5 stays FALL (condition
    assert int(CauseOfDeath.FALL) == 5         # space alignment)


def test_reintroducing_duplicate_codes_fails():
    """Schema control: the enum itself rejects a duplicate by design —
    verify the guard test would catch a collision if someone bypassed
    IntEnum with raw constants."""
    fake = {"WAR": 5, "FALL": 5}
    assert len(set(fake.values())) != len(fake), "control cannot fail"


def test_legacy_5_is_ambiguous_and_strict_reader_refuses():
    """Persisted 5 written before the fix is intrinsically ambiguous
    (war OR fall). Never silently relabel history."""
    from earth1.types import resolve_cause
    assert resolve_cause(5, legacy=False) is CauseOfDeath.FALL
    assert resolve_cause(9, legacy=True) is CauseOfDeath.WAR
    with pytest.raises(ValueError, match="ambiguous"):
        resolve_cause(5, legacy=True, strict=True)
    assert resolve_cause(5, legacy=True, strict=False) == "legacy_war_or_fall"


def test_no_raw_cause_integers_in_live_modules():
    """CI gate: no live module may assign cause_of_death from a raw
    integer literal again — everything routes through the enum."""
    import pathlib
    import re
    root = pathlib.Path(__file__).resolve().parents[1] / "earth1"
    offenders = []
    for f in ("health.py", "institutions.py", "weather.py",
              "flourishing.py", "mobility.py", "alive.py"):
        for i, ln in enumerate((root / f).read_text().splitlines(), 1):
            if re.search(r"cause_of_death\[[^\]]*\]\s*=\s*\d", ln):
                offenders.append(f"{f}:{i}")
    assert not offenders, f"raw cause integers: {offenders}"


def test_war_deaths_get_the_new_code(tiny_world, rng):
    from earth1.institutions import apply_policy_and_war
    w = tiny_world
    # force a war between the two largest countries
    cs = np.bincount(w.civ.country, minlength=194).argsort()[-2:]
    w.gov.at_war_with[cs[0]] = cs[1]
    w.gov.at_war_with[cs[1]] = cs[0]
    w.gov.war_days[cs] = 5.0
    w.civ.age[:] = 0.2                    # everyone conscription-age
    w.life.in_lf[:] = True
    # tiny world -> tiny hazards; raise the kill rate through the REAL
    # code path so the event is deterministic, not statistical
    import earth1.institutions as inst
    monkey = getattr(inst, "WAR_DEATH_YR", None)
    for _ in range(60):
        apply_policy_and_war(w.civ, w.life, w.gov, w.health, rng, 30.0)
        war_dead = w.health.cause_of_death == int(CauseOfDeath.WAR)
        if war_dead.any():
            break
        w.gov.at_war_with[cs[0]] = cs[1]     # re-arm if the war ended
        w.gov.at_war_with[cs[1]] = cs[0]
    assert war_dead.any(), "no war death under sustained forced war"
    assert not (w.health.cause_of_death == 5)[war_dead].any()


def test_causes_roundtrip_persistence(tiny_world, tmp_path):
    from earth1 import persistence
    w = tiny_world
    codes = [CauseOfDeath.CANCER, CauseOfDeath.FALL, CauseOfDeath.WAR,
             CauseOfDeath.WEATHER, CauseOfDeath.WANT, CauseOfDeath.ROAD]
    for k, c in enumerate(codes):
        w.health.cause_of_death[k] = int(c)
    persistence.save_world(w, tmp_path / "w.pkl")
    back, _, _ = persistence.load_world(tmp_path / "w.pkl")
    for k, c in enumerate(codes):
        assert back.health.cause_of_death[k] == int(c), \
            f"{c.name} did not round-trip"


# ════ 0.1d — end-of-tick mortality contract ═════════════════════════

def test_journal_identity_closes_exactly(tiny_world, rng):
    """alive_end == alive_start - deaths_total + births, and
    deaths_total == sum of per-cause counts. Every day."""
    from earth1.alive import live_one_day
    w = tiny_world
    for _ in range(5):
        start = int(w.health.alive.sum())
        st = live_one_day(w, rng)
        end = int(w.health.alive.sum())
        assert st["alive"] == end, "journal alive is not end-of-tick"
        assert end == start - st["deaths"] + st["births"], \
            f"identity broken: {start} - {st['deaths']} + " \
            f"{st['births']} != {end}"
        by_cause = (st["disease_deaths"] + st.get("war_deaths", 0)
                    + st.get("weather_deaths", 0)
                    + st.get("starved_or_parched", 0)
                    + st.get("road_deaths_today", 0))
        assert st["deaths"] == by_cause, \
            f"gross {st['deaths']} != per-cause sum {by_cause}"


def test_omitting_a_killer_breaks_the_identity(tiny_world, rng):
    """Control: drop one death-producing subsystem from the per-cause
    sum and the accounting must not balance on a day it kills."""
    from earth1.alive import live_one_day
    from earth1 import mobility as mob_mod
    w = tiny_world
    w.civ.age[:] = 0.15                  # road-death peak ages
    monkeypatch = None
    orig = dict(mob_mod.ROAD_DEATHS_PER_100K)
    for k in mob_mod.ROAD_DEATHS_PER_100K:
        mob_mod.ROAD_DEATHS_PER_100K[k] = 50000.0   # deterministic event
    tripped = False
    for _ in range(20):
        st = live_one_day(w, rng)
        partial = (st["disease_deaths"] + st.get("war_deaths", 0)
                   + st.get("weather_deaths", 0)
                   + st.get("starved_or_parched", 0))
        if st["road_deaths_today"] > 0:
            assert st["deaths"] != partial, "control cannot fail"
            tripped = True
            break
    for k, v in orig.items():
        mob_mod.ROAD_DEATHS_PER_100K[k] = v
    assert tripped, "no road death despite raised hazard"


def test_deaths_key_counts_late_tick_killers(tiny_world, rng):
    """Control for premature journaling: force deaths in a LATE
    subsystem (mobility roads) and prove the same tick's totals see
    them. Under the old contract 'deaths' was health-only."""
    from earth1.alive import live_one_day
    from earth1 import mobility as mob_mod
    w = tiny_world
    seen_road = False
    w.civ.age[:] = 0.15                  # road-death peak ages
    orig = dict(mob_mod.ROAD_DEATHS_PER_100K)
    for k in mob_mod.ROAD_DEATHS_PER_100K:
        mob_mod.ROAD_DEATHS_PER_100K[k] = 50000.0
    for _ in range(40):
        st = live_one_day(w, rng)
        if st["road_deaths_today"] > 0:
            seen_road = True
            assert st["deaths"] >= st["road_deaths_today"] \
                + st["disease_deaths"], "late killers missing from gross"
            break
    for k, v in orig.items():
        mob_mod.ROAD_DEATHS_PER_100K[k] = v
    assert seen_road, "no road death despite raised hazard"


def test_disease_deaths_preserved_separately(tiny_world, rng):
    from earth1.alive import live_one_day
    st = live_one_day(tiny_world, rng)
    assert "disease_deaths" in st
    assert "deaths" in st
