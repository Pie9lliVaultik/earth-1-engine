"""Review M03a/b/c — complete state identity and checkpoint verification.

Regressions from EXTERNAL_REVIEW_VERIFICATION_2026-09-08, reproducing
the review's probes (probe_m03a_hash_blindspots / probe_m03b_rebirth_sex
/ probe_m03c_checkpoint_acceptance) and asserting the fixed behaviour:

  M03a — world_hash was blind to dynamically attached state (civ.sex,
         life.firm_distress, chronicle.cascade_residues): equal hashes,
         divergent next tick. The v1 hash is now FROZEN (that blindness
         is permanent by design, so the paper's recorded digests stay
         reproducible) and world_hash_full covers the stragglers.
  M03b — rebirth kept the corpse's sex because the dynamic field was
         invisible to the completeness gate. Now declared, in POLICY,
         and drawn from a slot-keyed spawned generator that leaves the
         MAIN rng stream untouched (frozen physics).
  M03c — checkpoints accepted a missing checksum sidecar, a tampered
         .adj.npz (as "verified"), and a wrong physics label. All three
         now refuse, with legacy-tolerant escapes.
"""
import copy
import json
import pickle

import numpy as np
import pytest

from earth1 import persistence
from earth1.alive import PHYSICS_VERSION, birth_world, live_one_day
from earth1.persistence import (DYNAMIC_FIELDS, WORLD_FIELDS_V1,
                                SnapshotError, load_world, save_world,
                                world_fields, world_hash, world_hash_full)

C2_POP = 2_000
C2_SEED = 13


@pytest.fixture(scope="module")
def _c2_template():
    """One c2plus birth per module — the substrate that carries civ.sex."""
    return birth_world(C2_POP, C2_SEED, substrate="c2plus_v1")


@pytest.fixture
def c2_world(_c2_template):
    return copy.deepcopy(_c2_template)


# ── M03a: the frozen v1 hash and the full hash ──────────────────────

def test_v1_field_list_is_frozen_and_current():
    """WORLD_FIELDS_V1 must equal today's World — the freeze is only
    honest while the two agree; a new World field must extend
    world_hash_full (DYNAMIC_FIELDS or a successor version), never
    silently join the v1 walk."""
    assert WORLD_FIELDS_V1 == world_fields(), (
        "World grew or lost a field. Do NOT regenerate WORLD_FIELDS_V1 "
        "— that would change recorded v1 digests. Cover the new field "
        "via world_hash_full and bump the hash version deliberately.")


def test_sex_flip_changes_full_hash_not_v1(c2_world):
    """The review's probe 1: flipping civ.sex left world_hash unchanged.
    That stays true FOR v1 (frozen, reproducible); world_hash_full must
    see it."""
    w = c2_world
    assert w.civ.sex is not None, "c2plus world must carry sex"
    h_v1, h_full = world_hash(w), world_hash_full(w)
    w.civ.sex = w.civ.sex.copy()
    w.civ.sex[:100] = 1 - w.civ.sex[:100]
    assert world_hash(w) == h_v1, "v1 hash is frozen; sex must not move it"
    assert world_hash_full(w) != h_full, "full hash is BLIND to civ.sex"


def test_firm_distress_twins_differ_under_full_hash(tiny_world):
    """The review's probe 3: two worlds differing only in firm_distress
    hashed equal, then diverged after one tick."""
    wA = copy.deepcopy(tiny_world)
    wB = copy.deepcopy(tiny_world)
    nf = int(wA.life.n_firms)
    wA.life.firm_distress = np.zeros(nf)
    wB.life.firm_distress = np.full(nf, 0.9)
    assert world_hash(wA) == world_hash(wB)          # v1: frozen blindness
    assert world_hash_full(wA) != world_hash_full(wB), (
        "full hash is BLIND to life.firm_distress")


def test_distress_layoffs_counter_reaches_full_hash(tiny_world):
    v1 = world_hash(tiny_world)
    h0 = world_hash_full(tiny_world)
    tiny_world.life.distress_layoffs = 7             # dynamic companion
    assert world_hash_full(tiny_world) != h0
    assert world_hash(tiny_world) == v1              # v1 stays frozen


def test_cascade_residues_reach_full_hash(tiny_world):
    """The review's probe 2, plus the sentinel: ATTACHING the attribute
    is itself a state change, distinct from attaching it empty."""
    v1 = world_hash(tiny_world)
    h_absent = world_hash_full(tiny_world)
    tiny_world.chronicle.cascade_residues = []
    h_empty = world_hash_full(tiny_world)
    assert h_empty != h_absent, "absent vs present-empty must differ"
    tiny_world.chronicle.cascade_residues = [
        {"rule": "synthetic_probe", "day": 3.0, "loc": 7, "level": 0.5}]
    assert world_hash_full(tiny_world) != h_empty
    assert world_hash(tiny_world) == v1              # v1 stays frozen


def test_full_hash_registry_matches_review_inventory():
    covered = {f"{c}.{a}" for c, a in DYNAMIC_FIELDS}
    for needed in ("civ.sex", "life.firm_distress",
                   "chronicle.cascade_residues"):
        assert needed in covered, f"M03a inventory item missing: {needed}"


# ── M03b: rebirth and the sex field ─────────────────────────────────

def _dead_slot_with_parent(w):
    """A slot to kill and a living parent of the OPPOSITE sex."""
    sex = w.civ.sex
    for s in range(w.civ.n):
        others = np.flatnonzero((sex != sex[s]) & w.health.alive)
        others = others[others != s]
        if others.size:
            return int(s), int(others[0])
    raise AssertionError("no opposite-sex pair in the world")


def test_completeness_gate_now_sees_sex(c2_world):
    """The review's probe: discovery walked __dataclass_fields__ only,
    so the dynamic sex attr was invisible and the gate passed vacuously.
    Declared, it must be discovered AND declared in POLICY."""
    from earth1.rebirth import (POLICY, assert_policy_complete,
                                discover_per_agent_fields)
    assert ("civ", "sex") in POLICY
    assert ("civ", "sex") in discover_per_agent_fields(c2_world)
    assert_policy_complete(c2_world)                 # gate stays green


def test_reborn_slot_gets_fresh_slot_keyed_sex(c2_world):
    """The newborn's sex comes from the slot-keyed spawned generator —
    deterministic for the same (seed, day, slot), never a corpse copy."""
    from earth1.rebirth import apply_rebirth
    w = c2_world
    slot, parent = _dead_slot_with_parent(w)
    w.health.alive[slot] = False
    twin = copy.deepcopy(w)

    apply_rebirth(w, [slot], [parent], np.random.default_rng(3))
    apply_rebirth(twin, [slot], [parent], np.random.default_rng(3))
    assert int(w.civ.sex[slot]) == int(twin.civ.sex[slot]), (
        "sex draw must be deterministic in (seed, day, slot)")

    # the documented contract, pinned: generator spawned from the
    # slot-keyed seed, one uniform per slot, threshold 0.5
    ss = np.random.SeedSequence(
        [0x5E11D, int(w.civ.seed) & 0xFFFFFFFF, int(w.day), slot])
    expect = int(np.random.default_rng(ss).random(1)[0] < 0.5)
    assert int(w.civ.sex[slot]) == expect


def test_sex_draw_leaves_main_rng_stream_untouched(c2_world):
    """Frozen physics: a world WITH a sex field and one WITHOUT must
    consume the main rng identically through rebirth, and every shared
    newborn field must come out bit-identical."""
    from earth1.rebirth import apply_rebirth
    w_sex = c2_world
    slot, parent = _dead_slot_with_parent(w_sex)
    w_sex.health.alive[slot] = False
    w_no = copy.deepcopy(w_sex)
    w_no.civ.sex = None                              # pre-M03b world

    rng_a, rng_b = np.random.default_rng(3), np.random.default_rng(3)
    apply_rebirth(w_sex, [slot], [parent], rng_a)
    apply_rebirth(w_no, [slot], [parent], rng_b)

    np.testing.assert_array_equal(rng_a.random(8), rng_b.random(8))
    for f in ("openness", "forces", "alpha", "age"):
        np.testing.assert_array_equal(getattr(w_sex.civ, f),
                                      getattr(w_no.civ, f))
    np.testing.assert_array_equal(w_sex.life.wage, w_no.life.wage)
    np.testing.assert_array_equal(w_sex.life.mental, w_no.life.mental)


def test_sex_feeds_no_dynamics_over_days(c2_world):
    """Twin trajectories differing ONLY in civ.sex must produce the
    same v1 world hash after real ticks — sex is state, not physics,
    and the v1 digest stays reproducible across the M03b change."""
    wA = c2_world
    wB = copy.deepcopy(wA)
    wB.civ.sex = wB.civ.sex.copy()
    wB.civ.sex[:] = 1 - wB.civ.sex[:]                # maximal flip
    rA, rB = np.random.default_rng(99), np.random.default_rng(99)
    for _ in range(3):
        live_one_day(wA, rA)
        live_one_day(wB, rB)
    assert world_hash(wA) == world_hash(wB)


# ── M03c: the three checkpoint guards ───────────────────────────────

def _resign(p):
    """Recompute the pickle digest after deliberately editing the blob."""
    digest = persistence._sha256_stream(p)
    p.with_suffix(p.suffix + ".sha256").write_text(digest + "\n")


def test_missing_checksum_sidecar_refuses(tiny_world, tmp_path):
    p = tmp_path / "w.pkl"
    save_world(tiny_world, p)
    p.with_suffix(p.suffix + ".sha256").unlink()
    with pytest.raises(SnapshotError, match="no checksum sidecar"):
        load_world(p)
    back, _, info = load_world(p, allow_missing_checksum=True)
    assert info["checksum"] == "missing"
    assert int(back.civ.n) == tiny_world.civ.n


def test_tampered_graph_refuses(tiny_world, tmp_path):
    """The review's probe 2: a modified .adj.npz loaded as 'verified'
    and handed back a DIFFERENT world."""
    from scipy import sparse
    p = tmp_path / "w.pkl"
    save_world(tiny_world, p)
    ap = p.with_suffix(".adj.npz")
    m = sparse.load_npz(ap).tocsr()
    m.data = m.data.copy()
    m.data[:50] = m.data[:50] * 7.0 + 1.0
    sparse.save_npz(ap, m)
    with pytest.raises(SnapshotError, match="graph checksum mismatch"):
        load_world(p)


def test_legacy_sidecar_without_adj_digest_loads_as_legacy(tiny_world,
                                                           tmp_path):
    """An EXISTING valid checkpoint with only the old one-line .sha256
    must still load — reported as 'legacy', never 'verified', because
    its graph bytes are unverifiable."""
    p = tmp_path / "w.pkl"
    save_world(tiny_world, p)
    p.with_suffix(p.suffix + ".meta.json").unlink()   # pre-M03c layout
    back, _, info = load_world(p)
    assert info["checksum"] == "legacy"
    assert world_hash(back) == world_hash(tiny_world)


def test_physics_mismatch_refuses(tiny_world, tmp_path):
    """The review's probe 3: an incompatible physics label loaded
    silently under the frozen label."""
    p = tmp_path / "w.pkl"
    save_world(tiny_world, p)
    blob = pickle.loads(p.read_bytes())
    assert blob["physics_version"] == PHYSICS_VERSION
    blob["physics_version"] = "review-incompatible-physics-9.9"
    p.write_bytes(pickle.dumps(blob, protocol=pickle.HIGHEST_PROTOCOL))
    _resign(p)
    with pytest.raises(SnapshotError, match="physics"):
        load_world(p)
    back, _, info = load_world(p, allow_physics_mismatch=True)
    assert info["physics"] == "review-incompatible-physics-9.9"
    assert int(back.civ.n) == tiny_world.civ.n


def test_unlabelled_legacy_blob_loads_as_unrecorded(tiny_world, tmp_path):
    """Blobs old enough to predate the physics label must keep loading."""
    p = tmp_path / "w.pkl"
    save_world(tiny_world, p)
    blob = pickle.loads(p.read_bytes())
    del blob["physics_version"]
    p.write_bytes(pickle.dumps(blob, protocol=pickle.HIGHEST_PROTOCOL))
    _resign(p)
    back, _, info = load_world(p)
    assert info["physics"] == "unrecorded"
    assert int(back.civ.n) == tiny_world.civ.n


def test_ordinary_roundtrip_still_passes(tiny_world, tmp_path):
    """The happy path: save, load, both hashes intact, fully verified."""
    p = tmp_path / "w.pkl"
    before_v1 = world_hash(tiny_world)
    before_full = world_hash_full(tiny_world)
    meta = save_world(tiny_world, p)
    assert meta["world_hash"] == before_v1
    assert meta["world_hash_full"] == before_full
    sidecar_meta = json.loads(
        p.with_suffix(p.suffix + ".meta.json").read_text())
    assert sidecar_meta["adj_sha256"] == meta["adj_sha256"]
    assert sidecar_meta["world_hash"] == before_v1
    assert sidecar_meta["world_hash_full"] == before_full
    back, _, info = load_world(p)
    assert info["checksum"] == "verified"
    assert info["physics"] == PHYSICS_VERSION
    assert world_hash(back) == before_v1
    assert world_hash_full(back) == before_full
