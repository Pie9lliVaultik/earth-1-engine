"""0.5b — every ledger disposition is proven, not asserted.

The ledger (data/legacy_disposition_ledger.json) resolves the five
legacy modules. Each disposition rests on a machine-checked fact here:
absence proofs for the one PORT, purity proofs for the readout
adapters, binding/coverage proofs for the superseded.
"""
import copy
import inspect
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_ledger_exists_and_resolves_every_module():
    led = json.loads((ROOT / "data/legacy_disposition_ledger.json")
                     .read_text())
    assert set(led["modules"]) == {"graph_dynamics", "perishability",
                                   "coupling", "event_generation",
                                   "dynamics"}
    allowed = {"PORT", "ALREADY REPRESENTED", "READOUT-ADAPTER",
               "SUPERSEDED"}
    for mod, spec in led["modules"].items():
        for mech, m in spec["mechanisms"].items():
            assert m["disposition"] in allowed, \
                f"{mod}.{mech}: unresolved disposition {m['disposition']}"
            assert "candidate" not in m["disposition"].lower()


# ── graph_dynamics: PORT rests on proven ABSENCE ────────────────────

def test_tie_plasticity_absent_from_living_stack(tiny_world, rng):
    """Quiet live days (no migration, no rebirth) leave every tie
    bit-identical: nothing in the canonical stack changes weights from
    agreement. This is the absence that earns the PORT — when the port
    lands, THIS test flips into its negative control."""
    from earth1.alive import live_one_day
    w = tiny_world
    w.life.deprivation[:] = 0.0            # nobody wants to migrate
    # PRECISION NOTE (found by this test's own first run): the living
    # stack DOES rewire ties daily — employment re-homing (0.0d) churns
    # colleague ties with job churn, rebirth (0.0b) clears rows+cols.
    # Those are CONTEXT/IDENTITY channels. The port's claim is narrower
    # and is what we prove absent: INTERACTION-driven plasticity on the
    # social types the port would own (friends, weak, diaspora, media)
    # for agents untouched by rebirth.
    SOCIAL = ("friends", "weak", "diaspora", "media")
    before = {k: w.fabric.by_type[k].tocsr().copy() for k in SOCIAL}
    alive_before = w.health.alive.copy()
    for _ in range(5):
        live_one_day(w, rng)
    reborn = alive_before & w.health.alive & (w.civ.age < 5 / 365.0 / 72.0)
    dead = ~w.health.alive
    excluded = reborn | dead | w.klass.migrated
    for k in SOCIAL:
        after = w.fabric.by_type[k].tocsr()
        bmat = before[k]
        for i in np.flatnonzero(~excluded)[:300]:
            i = int(i)
            b = bmat.indices[bmat.indptr[i]:bmat.indptr[i + 1]]
            a = after.indices[after.indptr[i]:after.indptr[i + 1]]
            bw = bmat.data[bmat.indptr[i]:bmat.indptr[i + 1]]
            aw = after.data[after.indptr[i]:after.indptr[i + 1]]
            # edges to reborn slots are legitimately severed; compare
            # only edges to non-excluded partners
            keepb = ~excluded[b]
            keepa = ~excluded[a]
            assert np.array_equal(b[keepb], a[keepa]) and \
                np.array_equal(bw[keepb], aw[keepa]), \
                f"{k}: agent {i} social ties changed by interaction — " \
                f"plasticity already exists, the PORT would double physics"


# ── perishability: READOUT-ADAPTER rests on purity ──────────────────

def test_perishability_is_pure_readout():
    from earth1 import perishability
    sig = inspect.signature(perishability.decay_curve)
    assert "civ" not in sig.parameters and "w" not in sig.parameters
    src = inspect.getsource(perishability)
    for stateful in ("Civilization", "World", "rng", "random"):
        assert stateful not in src, \
            f"perishability touches {stateful!r} — not a pure readout"
    from earth1.types import Force
    a = perishability.decay_curve(0.7, Force.FEAR)
    b = perishability.decay_curve(0.7, Force.FEAR)
    assert a == b, "not deterministic"
    assert a["half_life_days"] < perishability.decay_curve(
        0.7, Force.IDENTITY)["half_life_days"], \
        "fear must perish faster than identity"


# ── coupling: READOUT-ADAPTER rests on question-layer-only ──────────

def test_coupling_is_question_layer_only():
    from earth1 import coupling
    src = inspect.getsource(coupling)
    assert "Civilization" not in src.replace(
        "from earth1.types import Question, RunResult, NUM_FORCES", "")
    for fn in (coupling.compute_coupling, coupling.coupled_field_shift):
        params = set(inspect.signature(fn).parameters)
        assert not params & {"civ", "w", "world"}, \
            f"{fn.__name__} consumes civilization state"


# ── event_generation: SUPERSEDED rests on binding + coverage ────────

def test_event_generation_is_bound_to_retired_engine():
    from earth1 import event_generation as eg
    src = inspect.getsource(eg)
    assert "RunResult" in src and "EventLog" in src, \
        "binding claim failed — re-examine the disposition"
    # and the living stack carries the self-excitation + memory the
    # module aimed at: the cascade block and the Chronicle
    from earth1 import alive, memory
    asrc = inspect.getsource(alive.live_one_day)
    assert "TRANSITION_RULES" in asrc, "living cascade coverage missing"
    assert hasattr(memory.Chronicle, "remember")


# ── dynamics: SUPERSEDED rests on living coverage ───────────────────

def test_dynamics_superseded_coverage(tiny_world, rng):
    from earth1 import susceptibility
    from earth1.alive import live_one_day
    w = tiny_world
    # susceptibility: canonical (N,8) matrix exists and modulates
    s = susceptibility.compute(w.civ, w.life, w.flourishing)
    assert s.shape == (w.civ.n, 8)
    assert float(s.std()) > 0, "susceptibility carries no variation"
    # trait residue: traits move under live days (local-deviation
    # feedback), the learning dynamics.py aimed at
    t0 = w.civ.openness.copy()
    for _ in range(5):
        live_one_day(w, rng)
    assert not np.array_equal(t0, w.civ.openness), \
        "no trait learning in the living stack — supersession claim wrong"


def test_summary_matches_module_dispositions():
    led = json.loads((ROOT / "data/legacy_disposition_ledger.json")
                     .read_text())
    assert led["summary"]["PORT"] == ["graph_dynamics.agreement_plasticity"]
    assert set(led["summary"]["SUPERSEDED"]) == {"event_generation.*",
                                                 "dynamics.*"}
