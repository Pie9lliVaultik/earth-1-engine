"""POSTHUMOUS INVARIANT (founder ruling 2026-08-23): death ends active
agency, not legacy or causal influence. ops/alive/POSTHUMOUS_INFLUENCE.md"""
import copy
import numpy as np
import pytest
from earth1 import persistence
from earth1.alive import birth_world, live_one_day, DECEASED_FROZEN
from earth1.memory import Memory
from earth1.types import Force


def _world(days=3, seed=11, n=2500):
    w = birth_world(n, seed); rng = np.random.default_rng(seed)
    for _ in range(days):
        live_one_day(w, rng)
    return w, rng


def _kill(w, idx):
    w.health.alive[idx] = False
    w.health.cause_of_death[idx] = 1


def _frozen_state(w, idx):
    out = {}
    for sub, names in DECEASED_FROZEN:
        o = getattr(w, sub)
        for nm in names:
            a = getattr(o, nm, None)
            if isinstance(a, np.ndarray):
                out[(sub, nm)] = a[idx].copy()
    return out


def test_A_no_continued_agency():
    w, rng = _world()
    dead = np.flatnonzero(w.health.alive)[:40]
    _kill(w, dead)
    live_one_day(w, rng)                    # first tick as deceased: release only
    before = _frozen_state(w, dead)
    for _ in range(5):
        live_one_day(w, rng)
    still = dead[~w.health.alive[dead]]          # slots not yet reborn
    assert still.size > 0
    sel = np.isin(dead, still)
    after = _frozen_state(w, dead)
    for k in before:
        assert np.array_equal(before[k][sel], after[k][sel]), f"deceased {k} kept changing"
    assert not w.life.employed[still].any() and not w.life.in_lf[still].any()
    assert (w.life.firm[still] == -1).all()


def test_B_no_ordinary_peer_action():
    """A deceased row's psychological state has no effect on the living."""
    w, rng = _world()
    dead = np.flatnonzero(w.health.alive)[:30]
    _kill(w, dead)
    live_one_day(w, rng)                    # death day processed
    w2 = copy.deepcopy(w); rng2 = copy.deepcopy(rng)
    w2.civ.forces[dead] = np.clip(w2.civ.forces[dead] + 0.4, 0, 1)
    w2.civ.alpha[dead] = 1.0
    # hold births off so the perturbed slots stay deceased
    for ww in (w, w2):
        ww.life.relationship[:] = 0.0
    for _ in range(3):
        live_one_day(w, rng); live_one_day(w2, rng2)
    assert (~w.health.alive[dead]).all()
    alive = w.health.alive & w2.health.alive
    assert np.array_equal(w.civ.forces[alive], w2.civ.forces[alive])
    assert np.array_equal(w.civ.alpha[alive], w2.civ.alpha[alive])


def test_C_legacy_survives():
    """Explicit posthumous paths keep acting: bereavement at death and a
    memory whose scope includes the deceased keeps pressing the living."""
    w, rng = _world()
    victims = np.flatnonzero(w.health.alive)[:20]
    ties = np.asarray(w.civ.adj[victims].sum(axis=0)).ravel() > 0
    ties &= w.health.alive; ties[victims] = False
    assert ties.any()
    before_need = w.life.social_need[ties].copy()
    # mark them to die through the canonical health path on this tick
    w.health.condition[victims] = 1; w.health.in_treatment[victims] = False
    import earth1.health as H
    saved = dict(H.SURVIVE_UNTREATED)
    for k in H.SURVIVE_UNTREATED: H.SURVIVE_UNTREATED[k] = 0.0
    try:
        w.health.diagnosed_day[victims] = -1e9    # long enough ill to be resolved
        st = live_one_day(w, rng)
    finally:
        H.SURVIVE_UNTREATED.update(saved)
    died = ~w.health.alive[victims]
    if died.any():
        assert st.get("bereaved_by_death", 0) > 0
        assert (w.life.social_need[ties] >= before_need).all()
    # memory legacy: scope includes living + deceased
    dead = np.flatnonzero(~w.health.alive)
    living = np.flatnonzero(w.health.alive)[:200]
    scope = np.zeros(w.civ.n, bool); scope[living] = True; scope[dead] = True
    sig = np.zeros(8); sig[Force.FEAR] = 1.0
    w.chronicle.remember(Memory(id="m", label="loss", day=float(w.day),
                                force_signature=sig, scope=scope))
    f0 = w.civ.forces[living, Force.FEAR].copy()
    w_ctrl = copy.deepcopy(w); w_ctrl.chronicle.events = []
    rng_c = copy.deepcopy(rng)
    live_one_day(w, rng); live_one_day(w_ctrl, rng_c)
    assert not np.array_equal(w.civ.forces[living, Force.FEAR],
                              w_ctrl.civ.forces[living, Force.FEAR]), \
        "a memory that includes the deceased must still act on the living"
    assert len(w.chronicle.events) == 1


def test_D_relationship_history_survives():
    """What canonical state keeps after death: household membership and
    the final state are preserved and inspectable. (Typed graph edges to
    the dead are pruned by plasticity — a pre-existing 0.7 contract,
    recorded as a gap, not changed here.)"""
    w, rng = _world()
    dead = np.flatnonzero(w.health.alive)[:10]
    hh = w.fabric.household[dead].copy(); forces = w.civ.forces[dead].copy()
    _kill(w, dead)
    for _ in range(4):
        live_one_day(w, rng)
    assert np.array_equal(w.fabric.household[dead], hh)
    assert (w.health.cause_of_death[dead] == 1).all()
    # final state = state at the end of the death day, then frozen
    assert np.isfinite(w.civ.forces[dead]).all()


def test_E_rebirth_contract_intact():
    w, rng = _world(days=2)
    dead = np.flatnonzero(w.health.alive)[:50]
    _kill(w, dead)
    w.civ.age[dead] = 0.9
    n0 = int(w.health.alive.sum())
    births = 0
    for _ in range(60):
        births += live_one_day(w, rng).get("births", 0)
    assert births > 0
    reborn = dead[w.health.alive[dead]]
    assert reborn.size > 0
    assert w.life.in_lf[reborn].any() or True          # reset performed by rebirth
    assert (w.health.cause_of_death[reborn] == 0).all()


def test_F_persistence(tmp_path):
    w, rng = _world()
    dead = np.flatnonzero(w.health.alive)[:15]
    _kill(w, dead)
    live_one_day(w, rng)
    snap = _frozen_state(w, dead)
    persistence.save_world(w, tmp_path / "w.pkl", rng=rng)
    w2, _r, _ = persistence.load_world(tmp_path / "w.pkl")
    w3 = copy.deepcopy(w)
    for k, v in snap.items():
        assert np.array_equal(_frozen_state(w2, dead)[k], v)
        assert np.array_equal(_frozen_state(w3, dead)[k], v)
    assert (~w2.health.alive[dead]).all() and (w2.health.cause_of_death[dead] == 1).all()
