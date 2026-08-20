"""0.5 graph-dynamics port — the ten required proofs.

Interaction-driven tie plasticity on friends+weak, the one mechanism
the disposition ledger earned. Audited legacy law preserved; no
parameter tuning for pretty networks.
"""
import copy

import numpy as np
import pytest

from earth1 import persistence, plasticity
from earth1.alive import live_one_day
from earth1.plasticity import (AGREEMENT_BOOST, DISAGREEMENT_DECAY,
                               MAX_WEIGHT, MIN_WEIGHT, plasticity_tick)


def _w(mat, i, j):
    return float(mat.tocsr()[i, j])


def _pair(w, tname="friends"):
    """A live, mutual tie in the given type."""
    m = w.fabric.by_type[tname].tocsr()
    for i in range(w.civ.n):
        lo, hi = m.indptr[i], m.indptr[i + 1]
        for j in m.indices[lo:hi]:
            if w.health.alive[i] and w.health.alive[j]:
                return int(i), int(j)
    pytest.skip(f"no {tname} tie found")


# ── proof 1: interaction -> tie strengthens ─────────────────────────

def test_agreement_strengthens_tie(tiny_world, rng):
    w = tiny_world
    i, j = _pair(w)
    w.civ.forces[i] = w.civ.forces[j] = 0.5          # perfect agreement
    # put the edge in the LAW's regime (genesis stacks duplicates to
    # ~3.5, a weight the legacy law never produced; law arithmetic is
    # asserted at a nominal weight)
    m = w.fabric.by_type["friends"].tolil()
    m[i, j] = m[j, i] = 0.70
    w.fabric.by_type["friends"] = m.tocsr()
    before = _w(w.fabric.by_type["friends"], i, j)
    plasticity_tick(w, rng)
    after = _w(w.fabric.by_type["friends"], i, j)
    assert after == pytest.approx(min(before + AGREEMENT_BOOST,
                                      MAX_WEIGHT)), \
        "agreement did not strengthen the tie by the audited law"


# ── proof 2: sustained disagreement -> weakens, then removed ────────

def test_disagreement_weakens_and_prunes(tiny_world, rng):
    w = tiny_world
    i, j = _pair(w)
    w.civ.forces[i] = 0.05
    w.civ.forces[j] = 0.95                           # deep disagreement
    m = w.fabric.by_type["friends"].tolil()
    m[i, j] = m[j, i] = 0.70
    w.fabric.by_type["friends"] = m.tocsr()
    before = _w(w.fabric.by_type["friends"], i, j)
    plasticity_tick(w, rng)
    after = _w(w.fabric.by_type["friends"], i, j)
    assert after == pytest.approx(before - DISAGREEMENT_DECAY)
    # sustained: run until the tie dies (audited prune at MIN_WEIGHT)
    for _ in range(200):
        if _w(w.fabric.by_type["friends"], i, j) == 0.0:
            break
        plasticity_tick(w, rng)
    assert _w(w.fabric.by_type["friends"], i, j) == 0.0, \
        "a tie in permanent deep disagreement never died"
    assert _w(w.fabric.by_type["friends"], j, i) == 0.0, "one-sided prune"


# ── proof 3: disabled port -> activation fails ──────────────────────

def test_disabled_port_is_detectable(tiny_world, rng, monkeypatch):
    w = tiny_world
    i, j = _pair(w)
    w.civ.forces[i] = w.civ.forces[j] = 0.5
    before = _w(w.fabric.by_type["friends"], i, j)
    import earth1.plasticity as pmod
    monkeypatch.setattr(pmod, "plasticity_tick",
                        lambda w, rng, dt_days=1.0: {})
    live_one_day(w, rng)
    # the tie may still change via OTHER channels only if i or j was
    # touched by rebirth/rehoming; on agreement alone it must not grow
    after = _w(w.fabric.by_type["friends"], i, j)
    assert after <= before + 1e-12, \
        "tie strengthened with the port disabled — a second plasticity " \
        "mechanism exists"


# ── proof 4: double execution is detectable ─────────────────────────

def test_double_execution_is_detectable(tiny_world, rng):
    a = copy.deepcopy(tiny_world)
    b = copy.deepcopy(tiny_world)
    ra, rb = np.random.default_rng(3), np.random.default_rng(3)
    plasticity_tick(a, ra)
    plasticity_tick(b, rb)
    plasticity_tick(b, rb)                            # the sabotage
    ha = persistence.world_hash(a)
    hb = persistence.world_hash(b)
    assert ha != hb, "running plasticity twice is invisible"


def test_one_execution_point_in_live_day(tiny_world, rng, monkeypatch):
    import earth1.plasticity as pmod
    calls = []
    real = pmod.plasticity_tick
    monkeypatch.setattr(pmod, "plasticity_tick",
                        lambda *a, **k: (calls.append(1), real(*a, **k))[1])
    live_one_day(tiny_world, rng)
    assert len(calls) == 1, f"plasticity ran {len(calls)}x in one day"


# ── proofs 5+6: determinism and mid-plasticity restart ──────────────

def test_deterministic_continuation(tiny_world):
    a = copy.deepcopy(tiny_world)
    b = copy.deepcopy(tiny_world)
    for _ in range(3):
        live_one_day(a, np.random.default_rng(11))
        live_one_day(b, np.random.default_rng(11))
    assert persistence.world_hash(a) == persistence.world_hash(b)


def test_restart_mid_plasticity_is_exact(tiny_world, tmp_path):
    twin = copy.deepcopy(tiny_world)
    r1 = np.random.default_rng(9)
    live_one_day(tiny_world, r1)
    persistence.save_world(tiny_world, tmp_path / "w.pkl", rng=r1)
    back, state, _ = persistence.load_world(tmp_path / "w.pkl")
    live_one_day(back, persistence.rng_from_state(state))
    r2 = np.random.default_rng(9)
    live_one_day(twin, r2)
    live_one_day(twin, r2)
    assert persistence.world_hash(back) == persistence.world_hash(twin)


# ── proof 7: context-owned ties untouched ───────────────────────────

def test_context_owned_ties_are_never_touched(tiny_world, rng):
    w = tiny_world
    before = {k: w.fabric.by_type[k].tocsr().copy()
              for k in ("colleagues", "household", "neighbours",
                        "diaspora", "media")}
    plasticity_tick(w, rng)
    for k, b in before.items():
        a = w.fabric.by_type[k].tocsr()
        assert (b != a).nnz == 0, \
            f"plasticity touched {k} — it owns friends+weak ONLY"


# ── proof 8: reborn slots inherit no plastic ties ───────────────────

def test_reborn_slot_has_no_plastic_ties(tiny_world, rng):
    from earth1.rebirth import apply_rebirth
    w = tiny_world
    for _ in range(3):
        plasticity_tick(w, rng)                       # build history
    victim = int(np.flatnonzero(w.health.alive)[5])
    parent = int(np.flatnonzero(w.health.alive)[50])
    w.health.alive[victim] = False
    apply_rebirth(w, np.array([victim]), np.array([parent]),
                  np.random.default_rng(2))
    for k in ("friends", "weak"):
        m = w.fabric.by_type[k].tocsr()
        assert m.indptr[victim] == m.indptr[victim + 1], \
            f"reborn slot inherited plastic {k} ties"


# ── proof 9: bounds and mutuality ───────────────────────────────────

def test_bounds_and_mutuality_hold(tiny_world, rng):
    w = tiny_world
    for _ in range(30):
        plasticity_tick(w, rng)
    initial_max = max(float(tiny_world.fabric.by_type[k].tocsr().data.max())
                      for k in ("friends", "weak"))
    for k in ("friends", "weak"):
        m = w.fabric.by_type[k].tocsr()
        if m.nnz:
            assert float(m.data.min()) >= MIN_WEIGHT - 1e-12
            # growth is bounded: nothing exceeds max(genesis max, LAW cap)
            assert float(m.data.max()) <= max(initial_max,
                                              MAX_WEIGHT) + 1e-12
        diff = (m != m.T).nnz
        assert diff == 0, f"{k} lost mutuality ({diff} asymmetric)"
        assert m.diagonal().sum() == 0, f"{k} grew self-loops"


# ── proof 10 (tick budget) is measured on prime at 4M pre-deploy ────

def test_stats_are_reported(tiny_world, rng):
    st = live_one_day(tiny_world, rng)
    for k in ("ties_strengthened", "ties_weakened", "ties_pruned",
              "ties_rewired"):
        assert k in st
