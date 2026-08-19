"""Phase 0.0c semantic invariants — a saved world comes back whole.

The release gate from BIBLE v4.1: "a feature is not built until its
state survives save/restore and a branch from a restored world retains
it."

Standing Rule 1 — the instrument is checked on a known answer before
any negative result is believed: `test_hash_sees_every_component`
proves `world_hash` can fail, component by component. A round-trip test
against a blind hash proves nothing, and a blind hash
(`living.pop_hash_full`, which covers civ and the graph only) is exactly
how the weather, everyone's hunger and every crowd could vanish across
a restart while the world still hashed as unchanged.
"""
import pickle

import numpy as np
import pytest

from earth1 import persistence
from earth1.alive import live_one_day
from earth1.persistence import (PHYSICS_GATING_FIELDS, SnapshotError, load_world,
                                rng_from_state, save_world, world_fields,
                                world_hash)
from earth1.provenance import SCHEMA_VERSION


# ── the instrument, verified before it is trusted ───────────────────

def test_hash_sees_every_component(tiny_world):
    """Mutating ANY world component must change the digest.

    Rule 2: a control that cannot fail is not a control. This is the
    test `pop_hash_full` would not have passed.
    """
    w = tiny_world
    base = world_hash(w)
    assert world_hash(w) == base, "hash must be stable when nothing changes"

    mutations = {
        "civ": lambda: w.civ.forces.__setitem__((0, 0), 0.123456),
        "life": lambda: w.life.wealth.__setitem__(0, 99999.0),
        "health": lambda: w.health.alive.__setitem__(0, False),
        "knowledge": lambda: w.knowledge.stock.__setitem__(0, 0.4242),
        "gov": lambda: w.gov.welfare.__setitem__(0, 0.777),
        "klass": lambda: w.klass.homeless.__setitem__(0, True),
        "climate": lambda: w.climate.anomaly.__setitem__(0, 3.5),
        "flourishing": lambda: w.flourishing.hope.__setitem__(0, 0.0101),
        "presence": lambda: w.presence.density.__setitem__(0, 0.9191),
        "mobility": lambda: w.mobility.travelled.__setitem__(0, 77),
        "day": lambda: setattr(w, "day", w.day + 1),
    }
    seen = {base}
    for name, mutate in mutations.items():
        mutate()
        h = world_hash(w)
        assert h not in seen, f"world_hash is BLIND to {name}"
        seen.add(h)


def test_hash_ignores_dict_ordering(tiny_world):
    """The digest must depend on state, never on insertion order."""
    w = tiny_world
    before = world_hash(w)
    w.fabric.by_type = dict(reversed(list(w.fabric.by_type.items())))
    assert world_hash(w) == before


# ── the schema-driven guarantee ─────────────────────────────────────

def test_persistence_policy_is_complete():
    """Add a field to World without declaring it and CI fails. Here.

    This is the permanent cure for the d3d2a0c defect class — the commit
    that fixed climate/flourishing persistence introduced
    presence/mobility unpersisted in the same patch, because the field
    list was hand-written and nobody was forced to look at it.

    Note the earlier version of this test compared the payload against
    `dataclasses.fields(World)` — but `save_world` BUILT the payload from
    that same call, so it was tautological and could never fail on a new
    field. The policy sets are declared independently on purpose: they
    are what makes this a control rather than a mirror.
    """
    gaps = persistence.policy_gaps()
    assert gaps["undeclared"] == (), (
        f"World fields with no persistence policy: {gaps['undeclared']}. "
        f"Declare each in PERSISTENT_FIELDS or TRANSIENT_FIELDS.")
    assert gaps["stale"] == (), (
        f"policy names fields World no longer has: {gaps['stale']}")


def test_policy_gap_is_detected(monkeypatch):
    """The control can fail: pretend World grew a field."""
    monkeypatch.setattr(persistence, "world_fields",
                        lambda: world_fields() + ("weather_front",))
    assert persistence.policy_gaps()["undeclared"] == ("weather_front",)
    with pytest.raises(ValueError, match="not declared"):
        persistence._assert_policy_current()


def test_every_persistent_field_reaches_disk(tiny_world, tmp_path):
    p = tmp_path / "w.pkl"
    save_world(tiny_world, p)
    with open(p, "rb") as f:
        blob = pickle.load(f)
    assert set(blob["fields"]) == set(persistence.PERSISTENT_FIELDS)


# ── the round trip ──────────────────────────────────────────────────

def test_roundtrip_hash_equality(tiny_world, tmp_path):
    p = tmp_path / "w.pkl"
    before = world_hash(tiny_world)
    save_world(tiny_world, p)
    back, _, info = load_world(p)
    assert info["schema_version"] == SCHEMA_VERSION
    assert info["lost"] == []
    assert world_hash(back) == before


def test_gating_fields_survive(tiny_world, tmp_path):
    """N2: presence/mobility are physics switches, not just values.

    live_one_day gates contagion, shared attention and mobility on these
    being non-None (alive.py:150,160). A restore that drops them changes
    which code runs — silently, and forever.
    """
    p = tmp_path / "w.pkl"
    save_world(tiny_world, p)
    back, _, _ = load_world(p)
    for name in PHYSICS_GATING_FIELDS:
        assert getattr(back, name) is not None, f"{name} lost — physics changed"
    assert back.presence.crowd_events == tiny_world.presence.crowd_events
    assert back.mobility.road_deaths == tiny_world.mobility.road_deaths
    np.testing.assert_array_equal(back.mobility.travelled,
                                  tiny_world.mobility.travelled)
    np.testing.assert_array_equal(back.presence.locality,
                                  tiny_world.presence.locality)


def test_graph_survives(tiny_world, tmp_path):
    p = tmp_path / "w.pkl"
    save_world(tiny_world, p)
    back, _, _ = load_world(p)
    a, b = tiny_world.civ.adj.tocsr(), back.civ.adj.tocsr()
    assert a.shape == b.shape and a.nnz == b.nnz
    np.testing.assert_array_equal(a.indptr, b.indptr)
    np.testing.assert_array_equal(a.indices, b.indices)
    # civ.adj and fabric.adj are aliased at alive.py:64 — restoring must
    # re-establish that, or per-channel analysis reads a stale graph
    assert back.fabric.adj is not None
    np.testing.assert_array_equal(back.fabric.adj.tocsr().indptr, b.indptr)


# ── RNG continuation ────────────────────────────────────────────────

def test_rng_state_roundtrips(tiny_world, tmp_path):
    p = tmp_path / "w.pkl"
    r = np.random.default_rng(1234)
    r.random(17)                                  # advance off the seed point
    save_world(tiny_world, p, rng=r)
    _, state, _ = load_world(p)
    assert state is not None
    back = rng_from_state(state)
    np.testing.assert_array_equal(back.random(5), r.random(5))


def _populate_chronicle(w, n=3):
    """Give the world memories to carry.

    Without this the continuation test is vacuous: a newborn world has
    an empty chronicle, so `Chronicle.spread` returns immediately and
    never draws a random number at all. Every memory here means N draws
    per day through the exact call that used to reach for the global
    RNG — which is what makes this test able to catch that class of bug
    rather than merely assert around it.
    """
    from earth1.memory import Memory
    for i in range(n):
        sig = np.zeros(8)
        sig[i % 8] = 1.0
        scope = np.zeros(w.civ.n, dtype=bool)
        scope[i::37] = True                    # a scattered, real cohort
        w.chronicle.remember(Memory(
            id=f"m{i}", label=f"event {i}", day=float(w.day),
            force_signature=sig, scope=scope, salience=0.9,
            half_life=720.0, rehearsals=0, origin="world"))


@pytest.mark.parametrize("n_ticks", [1, 5])
def test_restore_then_advance_matches_uninterrupted(tiny_world, tmp_path,
                                                    n_ticks):
    """THE 0.0c invariant: a restart must not change the future.

        Restore(S_t) --N ticks--> S_t+N  ==  S_t --N ticks--> S_t+N

    World A runs straight through. World B is checkpointed at t,
    restored, and advanced with the same inputs and the same stream.
    Every persistent component must match, not just the total.

    The chronicle is deliberately populated (see above), so this also
    stands as the standing guard for any module reaching past the
    world's RNG for its dice.
    """
    import copy

    _populate_chronicle(tiny_world)
    twin = copy.deepcopy(tiny_world)

    # A: checkpoint, restore, then advance
    r1 = np.random.default_rng(99)
    live_one_day(tiny_world, r1)
    p = tmp_path / "w.pkl"
    save_world(tiny_world, p, rng=r1)
    back, state, info = load_world(p)
    assert state is not None, "RNG stream was not carried"
    r_back = rng_from_state(state)
    for _ in range(n_ticks):
        live_one_day(back, r_back)

    # B: never interrupted
    r2 = np.random.default_rng(99)
    for _ in range(n_ticks + 1):
        live_one_day(twin, r2)

    # component by component, so a failure says WHICH subsystem drifted
    for name in sorted(persistence.PERSISTENT_FIELDS):
        h = __import__("hashlib").sha256()
        persistence._feed(h, getattr(back, name))
        a = h.hexdigest()
        h = __import__("hashlib").sha256()
        persistence._feed(h, getattr(twin, name))
        assert a == h.hexdigest(), f"{name} diverged after restore"

    assert world_hash(back) == world_hash(twin)


def test_chronicle_spread_uses_the_world_rng(tiny_world):
    """Ruling 4: the world's dice, not the process's.

    Two identical worlds given identical generators must spread memories
    identically — and the global RNG must be left untouched, so that a
    paired branch cannot be perturbed by anything else in the process.
    """
    import copy
    _populate_chronicle(tiny_world)
    twin = copy.deepcopy(tiny_world)

    np.random.seed(1)
    a = tiny_world.chronicle.spread(tiny_world.civ, np.random.default_rng(5))
    np.random.seed(999)                        # different global state...
    b = twin.chronicle.spread(twin.civ, np.random.default_rng(5))
    assert a == b, "spread still depends on the global RNG"

    before = np.random.get_state()[1].copy()
    twin.chronicle.spread(twin.civ, np.random.default_rng(5))
    assert np.array_equal(np.random.get_state()[1], before), \
        "spread perturbed the global RNG"


# ── backward compatibility: the box's 110-day world must still load ──

def _write_v0_daemon_snapshot(w, path):
    """The pre-schema `world_alive.save_world` dialect, verbatim."""
    from scipy import sparse
    CIV_ARRAYS = ("country", "region", "age_bucket", "age", "education",
                  "income", "urban", "openness", "empathy", "risk_appetite",
                  "doubt", "desire_intensity", "economic_field",
                  "culture_offset", "conscientiousness", "agreeableness",
                  "extraversion", "neuroticism", "power_distance",
                  "individualism", "uncertainty_avoidance",
                  "long_term_orientation", "forces", "alpha", "means")
    sparse.save_npz(path.with_suffix(".adj.npz"), w.civ.adj.tocsr())
    with open(path, "wb") as f:
        pickle.dump({"civ": {k: getattr(w.civ, k) for k in CIV_ARRAYS},
                     "fabric": w.fabric, "feed": w.feed, "life": w.life,
                     "health": w.health, "knowledge": w.knowledge,
                     "gov": w.gov, "klass": w.klass,
                     "chronicle": w.chronicle, "climate": w.climate,
                     "flourishing": w.flourishing,
                     "day": w.day, "n": w.civ.n, "seed": w.civ.seed}, f)


def test_v0_snapshot_is_refused_by_default(tiny_world, tmp_path):
    """Ruling 5: a v0 file cannot carry presence/mobility/RNG.

    Loading one silently would resume a world running different physics.
    That is a load failure, not a different universe handed back quietly.
    """
    p = tmp_path / "old.pkl"
    _write_v0_daemon_snapshot(tiny_world, p)
    with pytest.raises(SnapshotError, match="pre-schema"):
        load_world(p)


def test_v0_snapshot_migrates_when_asked(tiny_world, tmp_path):
    """The world box holds 4M agents in this format. Do not orphan them."""
    p = tmp_path / "old.pkl"
    _write_v0_daemon_snapshot(tiny_world, p)
    back, state, info = load_world(p, allow_v0_migration=True)
    assert info["schema_version"] == 0
    assert state is None                       # v0 never carried the stream
    assert back.day == tiny_world.day
    assert int(back.health.alive.sum()) == int(tiny_world.health.alive.sum())
    np.testing.assert_array_equal(back.civ.forces, tiny_world.civ.forces)
    for name in PHYSICS_GATING_FIELDS:
        assert name in info["lost"], f"v0 dropped {name} and did not say so"


def test_v0_migration_rebuilds_gating_subsystems(tiny_world, tmp_path):
    """THE PRODUCTION BUG, 2026-08-19: migration printed 'rebuilt at
    birth values' while rebuilding nothing, so the migrated 4M world ran
    20 days with contagion, shared attention and mobility switched off.
    Caught by the restore rehearsal on prime, not by this suite — this
    test is the missing control. A migrated world must be WHOLE.
    """
    p = tmp_path / "old.pkl"
    _write_v0_daemon_snapshot(tiny_world, p)
    back, _, _ = load_world(p, allow_v0_migration=True)
    for name in PHYSICS_GATING_FIELDS:
        assert getattr(back, name) is not None, (
            f"migration left {name}=None — the world resumes with "
            f"reduced physics")
    # and the rebuilt subsystems must be usable, not placeholders
    assert back.presence.locality.shape == (tiny_world.civ.n,)
    assert back.mobility.owns_car.shape == (tiny_world.civ.n,)


def test_v1_snapshot_with_none_gating_field_is_refused(tiny_world, tmp_path):
    """Defense in depth for the same bug: the mis-migrated daemon then
    SAVED presence=None into a v1 snapshot, which passed the missing-KEY
    check (the key exists, its value is None) and would have resumed
    reduced physics forever. Present-as-None must fail closed.
    """
    p = tmp_path / "w.pkl"
    save_world(tiny_world, p)
    with open(p, "rb") as f:
        blob = pickle.load(f)
    blob["fields"]["presence"] = None
    with open(p, "wb") as f:
        pickle.dump(blob, f)
    p.with_suffix(p.suffix + ".sha256").unlink()
    with pytest.raises(SnapshotError, match="reduced physics"):
        load_world(p)


def test_missing_persistent_field_is_refused(tiny_world, tmp_path):
    """Never substitute a default for state the snapshot should have."""
    p = tmp_path / "w.pkl"
    save_world(tiny_world, p)
    with open(p, "rb") as f:
        blob = pickle.load(f)
    del blob["fields"]["mobility"]
    with open(p, "wb") as f:
        pickle.dump(blob, f)
    p.with_suffix(p.suffix + ".sha256").unlink()      # re-sign or it trips first
    with pytest.raises(SnapshotError, match="missing persistent state"):
        load_world(p)


def test_corrupt_snapshot_is_refused(tiny_world, tmp_path):
    p = tmp_path / "w.pkl"
    save_world(tiny_world, p)
    with open(p, "r+b") as f:                        # flip a byte in the body
        f.seek(64)
        b = f.read(1)
        f.seek(64)
        f.write(bytes([b[0] ^ 0xFF]))
    with pytest.raises(SnapshotError, match="checksum mismatch"):
        load_world(p)


def test_missing_graph_is_refused(tiny_world, tmp_path):
    p = tmp_path / "w.pkl"
    save_world(tiny_world, p)
    p.with_suffix(".adj.npz").unlink()
    with pytest.raises(SnapshotError, match="no graph"):
        load_world(p)


def test_future_schema_is_refused(tiny_world, tmp_path):
    """Never guess at fields we do not know about."""
    p = tmp_path / "w.pkl"
    save_world(tiny_world, p)
    with open(p, "rb") as f:
        blob = pickle.load(f)
    blob["schema_version"] = SCHEMA_VERSION + 1
    with open(p, "wb") as f:
        pickle.dump(blob, f)
    p.with_suffix(p.suffix + ".sha256").unlink()
    with pytest.raises(SnapshotError, match="newer than this code"):
        load_world(p)


def test_save_is_atomic_and_checksummed(tiny_world, tmp_path):
    """No .tmp left behind, and the sidecar proves the save completed."""
    p = tmp_path / "w.pkl"
    meta = save_world(tiny_world, p)
    assert p.exists()
    assert not list(tmp_path.glob("*.tmp"))
    sidecar = p.with_suffix(p.suffix + ".sha256")
    assert sidecar.exists()
    assert sidecar.read_text().strip() == meta["sha256"]
