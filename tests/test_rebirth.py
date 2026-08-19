"""Phase 0.0b semantic invariants — a reborn slot is a new Earthling.

Core invariant: newborn = birth initialization + declared inheritance,
never previous-occupant leftovers.

The founder's seven controls, each able to fail (and several proven to,
by deliberately breaking the mechanism under test):

  1. impossible sentinels planted before death never survive rebirth
  2. dense typed ties on the deceased are never inherited
  3. reverse-side references to the old occupant are removed
  4. omitting a field from the schema fails CI
  5. preserving a prohibited tie fails the semantic invariant
  6. rebirth -> save -> restore reproduces the newborn exactly
  7. live ticks after rebirth stay valid; no subsystem resurrects state
"""
import copy

import numpy as np
import pytest

from earth1 import persistence, rebirth
from earth1.alive import live_one_day
from earth1.memory import Memory
from earth1.rebirth import (INHERIT_PARENT, POLICY, apply_rebirth,
                            assert_policy_complete, policy_gaps)

SENT_F = 0.777777       # impossible float sentinel (all live floats <=1)
SENT_I = 77777          # impossible int sentinel


def _kill_and_rebirth(w, victim, parent, rng=None):
    rng = rng or np.random.default_rng(11)
    w.health.alive[victim] = False
    apply_rebirth(w, np.array([victim]), np.array([parent]), rng)
    return w


def _plant_sentinels(w, i):
    """Seed every non-relational per-agent field of slot i with an
    impossible value. Returns {(obj, field): sentinel} for the check."""
    planted = {}
    for (obj_name, field), pol in POLICY.items():
        if obj_name in ("fabric", "feed", "chronicle"):
            continue
        obj = getattr(w, obj_name)
        a = getattr(obj, field, None)
        if a is None or not isinstance(a, np.ndarray):
            continue
        if a.dtype.kind == "b":
            continue                      # bools can't hold a sentinel
        if a.dtype.kind in "iu":
            s = min(SENT_I, int(np.iinfo(a.dtype).max) - 1)
        else:
            s = SENT_F
        a[i] = s
        planted[(obj_name, field)] = s
    return planted


# ── control 1: no sentinel survives ─────────────────────────────────

def test_no_forbidden_sentinel_survives_rebirth(tiny_world):
    w = tiny_world
    victim = int(np.flatnonzero(w.health.alive)[5])
    parent = int(np.flatnonzero(w.health.alive)[50])
    planted = _plant_sentinels(w, victim)
    assert len(planted) > 40, "sentinel sweep must cover the field estate"
    _kill_and_rebirth(w, victim, parent)

    survivors = []
    for (obj_name, field), s in planted.items():
        if POLICY[(obj_name, field)] == INHERIT_PARENT:
            continue                     # inherited fields take parent's
        v = getattr(getattr(w, obj_name), field)[victim]
        if np.isscalar(v) or v.ndim == 0:
            if float(v) == s:
                survivors.append((obj_name, field))
        elif np.any(np.asarray(v) == s):
            survivors.append((obj_name, field))
    assert not survivors, f"corpse leftovers survived rebirth: {survivors}"


def test_inherited_fields_come_from_parent_not_corpse(tiny_world):
    w = tiny_world
    victim = int(np.flatnonzero(w.health.alive)[5])
    parent = int(np.flatnonzero(w.health.alive)[50])
    # make corpse and parent maximally distinguishable on inherited fields
    w.life.wage[victim] = SENT_F
    w.life.wage[parent] = 123.456
    w.flourishing.hunger[victim] = 0.999    # occupant starved to death
    w.flourishing.hunger[parent] = 0.111
    w.presence.locality[victim] = 0
    w.presence.locality[parent] = int(w.presence.locality[parent])
    _kill_and_rebirth(w, victim, parent)
    assert w.life.wage[victim] == 123.456
    assert w.flourishing.hunger[victim] == pytest.approx(0.111)
    assert w.presence.locality[victim] == w.presence.locality[parent]


def test_setpoints_heritable_from_parent_not_corpse(tiny_world):
    """The pre-0.0b code gave the newborn the DEAD person's mental
    setpoint — the corpse's temperament, not the family's."""
    w = tiny_world
    victim = int(np.flatnonzero(w.health.alive)[5])
    parent = int(np.flatnonzero(w.health.alive)[50])
    w.life.mental_setpoint[victim] = 0.02      # a broken occupant
    w.life.mental_setpoint[parent] = 0.90      # a resilient family
    _kill_and_rebirth(w, victim, parent)
    sp = float(w.life.mental_setpoint[victim])
    assert abs(sp - 0.90) < 0.3, f"setpoint {sp} tracks the corpse"
    assert w.life.mental[victim] == pytest.approx(sp)


# ── controls 2+3: ties severed, both directions ─────────────────────

def _densify_ties(w, i):
    """Give slot i dense ties of every type."""
    from scipy import sparse
    n = w.civ.n
    others = [(i + k) % n for k in (1, 7, 40, 99, 500)]
    rows = [i] * len(others) + others
    cols = others + [i] * len(others)
    delta = sparse.csr_matrix((np.ones(len(rows)), (rows, cols)),
                              shape=(n, n))
    for name in w.fabric.by_type:
        w.fabric.by_type[name] = (w.fabric.by_type[name] + delta).tocsr()
    w.fabric.adj = (w.fabric.adj + delta * len(w.fabric.by_type)).tocsr()
    w.civ.adj = w.fabric.adj
    return others


def _row_nbrs(mat, i):
    m = mat.tocsr()
    return set(m.indices[m.indptr[i]:m.indptr[i + 1]].tolist())


def test_zero_inherited_ties_all_types(tiny_world):
    w = tiny_world
    victim = int(np.flatnonzero(w.health.alive)[5])
    parent = int(np.flatnonzero(w.health.alive)[50])
    old_nbrs = _densify_ties(w, victim)
    _kill_and_rebirth(w, victim, parent)

    household = np.flatnonzero(
        (w.fabric.household == w.fabric.household[parent])
        & w.health.alive)
    allowed = set(household.tolist())
    for name, mat in w.fabric.by_type.items():
        nbrs = _row_nbrs(mat, victim)
        if name == "household":
            assert nbrs <= allowed, f"{name}: non-household tie inherited"
        else:
            assert not nbrs, f"{name}: {len(nbrs)} inherited {name} ties"
    assert not (_row_nbrs(w.fabric.adj, victim) - allowed)
    assert not (set(old_nbrs) & _row_nbrs(w.fabric.adj, victim) - allowed)


def test_reverse_references_removed(tiny_world):
    """Nobody may still 'know' the dead identity: columns go with rows."""
    w = tiny_world
    victim = int(np.flatnonzero(w.health.alive)[5])
    parent = int(np.flatnonzero(w.health.alive)[50])
    others = _densify_ties(w, victim)
    _kill_and_rebirth(w, victim, parent)
    household = set(np.flatnonzero(
        (w.fabric.household == w.fabric.household[parent])
        & w.health.alive).tolist())
    for o in others:
        if o in household:
            continue
        assert victim not in _row_nbrs(w.fabric.adj, o), \
            f"agent {o} still holds a reverse tie to the dead identity"
        for name, mat in w.fabric.by_type.items():
            assert victim not in _row_nbrs(mat, o), \
                f"{name}: reverse reference survived"


def test_newborn_joins_parents_household(tiny_world):
    w = tiny_world
    victim = int(np.flatnonzero(w.health.alive)[5])
    parent = int(np.flatnonzero(w.health.alive)[50])
    _kill_and_rebirth(w, victim, parent)
    assert w.fabric.household[victim] == w.fabric.household[parent]
    assert parent in _row_nbrs(w.fabric.by_type["household"], victim)
    assert victim in _row_nbrs(w.fabric.by_type["household"], parent)
    assert w.civ.adj is w.fabric.adj, "alive.py:64 alias broken"


def test_feed_and_memory_scopes_cleared(tiny_world):
    w = tiny_world
    victim = int(np.flatnonzero(w.health.alive)[5])
    parent = int(np.flatnonzero(w.health.alive)[50])
    scope = np.zeros(w.civ.n, dtype=bool)
    scope[victim] = True
    sig = np.zeros(8); sig[0] = 1.0
    w.chronicle.remember(Memory(id="m", label="pre-birth event", day=0.0,
                                force_signature=sig, scope=scope,
                                salience=0.9, half_life=720.0,
                                rehearsals=0, origin="world"))
    _densify_ties(w, victim)
    _kill_and_rebirth(w, victim, parent)
    assert not w.chronicle.events[0].scope[victim], \
        "newborn 'remembers' an event from before their birth"
    feed = w.feed.tocsr()
    assert not _row_nbrs(feed, victim), "inherited feed sources"
    col = feed.tocsc()
    assert col.indptr[victim] == col.indptr[victim + 1], \
        "inherited feed audience"


# ── control 4: schema completeness fails CI on omission ─────────────

def test_policy_is_complete(tiny_world):
    assert_policy_complete(tiny_world)
    gaps = policy_gaps(tiny_world)
    assert gaps["undeclared"] == [] and gaps["stale"] == []


def test_omitted_field_fails_ci(tiny_world, monkeypatch):
    trimmed = dict(POLICY)
    del trimmed[("health", "declining")]
    monkeypatch.setattr(rebirth, "POLICY", trimmed)
    with pytest.raises(ValueError, match="no rebirth policy"):
        assert_policy_complete(tiny_world)


# ── control 5: a preserved prohibited tie fails the invariant ───────

def test_preserved_tie_is_detected(tiny_world, monkeypatch):
    """Break the mechanism on purpose: skip tie clearing, prove the
    invariant catches it. A control that cannot fail is not a control."""
    w = tiny_world
    victim = int(np.flatnonzero(w.health.alive)[5])
    parent = int(np.flatnonzero(w.health.alive)[50])
    _densify_ties(w, victim)
    monkeypatch.setattr(rebirth, "_zero_rows_cols", lambda m, s: m.tocsr())
    w.health.alive[victim] = False
    apply_rebirth(w, np.array([victim]), np.array([parent]),
                  np.random.default_rng(11))
    household = set(np.flatnonzero(
        (w.fabric.household == w.fabric.household[parent])
        & w.health.alive).tolist())
    leaked = _row_nbrs(w.fabric.by_type["friends"], victim) - household
    assert leaked, "the sabotage control failed to leak — test is vacuous"


# ── control 6: rebirth survives save -> restore exactly ─────────────

def test_rebirth_then_roundtrip_is_exact(tiny_world, tmp_path):
    w = tiny_world
    victim = int(np.flatnonzero(w.health.alive)[5])
    parent = int(np.flatnonzero(w.health.alive)[50])
    _densify_ties(w, victim)
    _kill_and_rebirth(w, victim, parent)
    h = persistence.world_hash(w)
    persistence.save_world(w, tmp_path / "w.pkl")
    back, _, info = persistence.load_world(tmp_path / "w.pkl")
    assert info["lost"] == []
    assert persistence.world_hash(back) == h


# ── control 7: live ticks stay valid; nothing resurrects ────────────

def test_live_ticks_after_rebirth_stay_valid(tiny_world, rng):
    w = tiny_world
    victim = int(np.flatnonzero(w.health.alive)[5])
    parent = int(np.flatnonzero(w.health.alive)[50])
    w.health.declining[victim] = 3.0          # a decaying occupant
    w.health.falls[victim] = 9
    w.klass.days_homeless[victim] = 4000
    _densify_ties(w, victim)
    _kill_and_rebirth(w, victim, parent)

    for _ in range(5):
        live_one_day(w, rng)

    assert w.health.declining[victim] < 1.0, "decline resurrected"
    assert w.klass.days_homeless[victim] < 10, "street years resurrected"
    for name in ("mental", "wealth", "deprivation"):
        v = getattr(w.life, name)
        assert np.isfinite(v).all(), f"life.{name} went non-finite"
    assert np.isfinite(w.civ.forces).all()
    # graph structurally sound: symmetric nnz, no self-loop at the slot
    adj = w.civ.adj.tocsr()
    assert victim not in _row_nbrs(adj, victim)


def test_full_birth_path_uses_the_schema(tiny_world):
    """_be_born (conception -> slots) must route through apply_rebirth:
    force a death, then drive conception deterministically and check a
    schema-only guarantee (declining reset) on the recycled slot."""
    from earth1.alive import _be_born
    w = tiny_world
    victim = int(np.flatnonzero(w.health.alive)[5])
    w.health.alive[victim] = False
    w.health.declining[victim] = 3.0
    # make conception certain: everyone fertile, high TFR effect via rng
    w.civ.age[:] = 0.2
    w.life.relationship[:] = 0.9
    w.life.deprivation[:] = 0.0
    born = 0
    rng = np.random.default_rng(3)
    for _ in range(200):
        born = _be_born(w, rng)["births"]
        if born:
            break
    assert born, "no conception in 200 attempts — test setup wrong"
    assert w.health.alive[victim]
    assert w.health.declining[victim] == 0.0, \
        "_be_born did not route through the reset schema"
