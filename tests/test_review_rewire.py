"""Randomized-graph arm utility — regression suite.

founder ruling 2026-09-08: emergence experiment. The rewire transform
(scripts/emergence/rewire_graph.py) randomizes WHO knows WHOM in a
birthed world while preserving HOW CONNECTED everyone is. This suite
pins the full contract on a 2,000-agent c2plus world:

  * per-type structural degree sequences preserved EXACTLY for the
    swapped types (colleagues, neighbours, friends, weak, diaspora);
  * HOUSEHOLD EXEMPT and bit-identical — households are co-residence
    structures tied to locality (fabric.py builds houses inside one
    country; partnership/rebirth/rehome consume the fabric.household
    id array), so the experiment randomizes acquaintance structure,
    not physical cohabitation;
  * MEDIA preserved in degree only: hubs stay hubs (exact per-node
    degree), audience relabelled by permutation (degree multiset
    exact, membership random);
  * weight multisets preserved per type (weights travel with edges);
  * symmetry preserved (mutual ties in, mutual ties out);
  * composed adjacency rebuilt through the engine's own
    earth1.rehome._recompose_adj and consistent with by_type;
  * edge sets ACTUALLY changed (Jaccard overlap with the original
    well below 1 — reported);
  * deterministic under the seed;
  * dead slots untouched (rewire runs among alive agents only).

This is a harness transform: no engine file changes, so freeze-0.9
trajectory neutrality is n/a by construction.

Run only this file:  python3 -m pytest -q tests/test_review_rewire.py
"""
import copy

import numpy as np
import pytest
from scipy import sparse

from earth1.alive import birth_world
from scripts.emergence.rewire_graph import (EXEMPT_TYPES, MEDIA_TYPE,
                                            _media_hub_mask,
                                            rewire_world_graph)

POP = 2_000
WORLD_SEED = 42
REWIRE_SEED = 20260908

SWAPPED_TYPES = ("colleagues", "neighbours", "friends", "weak",
                 "diaspora")


# ── helpers ─────────────────────────────────────────────────────────

def _triu(m):
    coo = sparse.triu(m.tocsr(), k=1).tocoo()
    return (coo.row.astype(np.int64), coo.col.astype(np.int64),
            coo.data.copy())


def _edge_keys(m):
    r, c, _ = _triu(m)
    n = m.shape[0]
    return set((np.minimum(r, c) * n + np.maximum(r, c)).tolist())


def _deg(m):
    return m.tocsr().getnnz(axis=1)


def _jaccard(m_before, m_after):
    a, b = _edge_keys(m_before), _edge_keys(m_after)
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def _same_matrix(m1, m2):
    m1, m2 = m1.tocsr(), m2.tocsr()
    m1.sum_duplicates()
    m2.sum_duplicates()
    return (m1.shape == m2.shape
            and np.array_equal(m1.indptr, m2.indptr)
            and np.array_equal(m1.indices, m2.indices)
            and np.array_equal(m1.data, m2.data))


# ── fixtures ────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def pair():
    """(original, rewired) 2k c2plus worlds — READ-ONLY for tests.

    One birth + one rewire per module; any test that must mutate makes
    its own deepcopy.
    """
    orig = birth_world(POP, WORLD_SEED, substrate="c2plus_v1")
    assert bool(orig.health.alive.all()), "birthed world must be alive"
    rew = copy.deepcopy(orig)
    assert rewire_world_graph(rew, REWIRE_SEED) is None  # in place
    return orig, rew


# ── household exemption (documented) ────────────────────────────────

def test_household_exempt_and_bit_identical(pair):
    """founder ruling 2026-09-08: the experiment randomizes
    acquaintance structure, not physical cohabitation. The household
    matrix must stay aligned with the fabric.household id array that
    partnership/rebirth/rehome consume, so both pass through
    bit-identical."""
    orig, rew = pair
    assert "household" in EXEMPT_TYPES
    assert _same_matrix(orig.fabric.by_type["household"],
                        rew.fabric.by_type["household"])
    assert np.array_equal(orig.fabric.household, rew.fabric.household)


# ── (a) degree sequences ────────────────────────────────────────────

def test_per_node_degrees_exact_for_swapped_types(pair):
    orig, rew = pair
    for name in SWAPPED_TYPES:
        d0 = _deg(orig.fabric.by_type[name])
        d1 = _deg(rew.fabric.by_type[name])
        assert np.array_equal(d0, d1), (
            f"{name}: per-node structural degree not preserved")


def test_media_hubs_stay_hubs_by_degree(pair):
    """Media is preserved in degree only: the hub set is unchanged,
    each hub's degree is exact, and the audience degree multiset is
    carried by the relabelling permutation."""
    orig, rew = pair
    m0, m1 = orig.fabric.by_type[MEDIA_TYPE], rew.fabric.by_type[MEDIA_TYPE]
    hub0, hub1 = _media_hub_mask(m0.tocsr()), _media_hub_mask(m1.tocsr())
    assert hub0.any(), "2k world should carry at least one media hub"
    assert np.array_equal(hub0, hub1), "hub set changed"
    d0, d1 = _deg(m0), _deg(m1)
    assert np.array_equal(d0[hub0], d1[hub0]), "hub degrees changed"
    assert np.array_equal(np.sort(d0), np.sort(d1)), (
        "media degree multiset not preserved")


# ── (b) weight multisets ────────────────────────────────────────────

def test_weight_multisets_preserved_per_type(pair):
    orig, rew = pair
    for name in orig.fabric.by_type:
        _, _, w0 = _triu(orig.fabric.by_type[name])
        _, _, w1 = _triu(rew.fabric.by_type[name])
        assert np.array_equal(np.sort(w0), np.sort(w1)), (
            f"{name}: edge-weight multiset not preserved")


# ── (c) symmetry ────────────────────────────────────────────────────

def test_symmetry_preserved(pair):
    orig, rew = pair
    for name, m in rew.fabric.by_type.items():
        m = m.tocsr()
        assert (m != m.T).nnz == 0, f"{name}: symmetry broken"
        assert np.count_nonzero(m.diagonal()) == 0, (
            f"{name}: self-loop introduced")
    adj = rew.fabric.adj.tocsr()
    assert (adj != adj.T).nnz == 0, "composed adj not symmetric"


# ── composed adjacency via the engine's own recompose ───────────────

def test_composed_adjacency_consistent_with_by_type(pair):
    """fab.adj must equal the engine's composition of by_type (the
    utility calls earth1.rehome._recompose_adj, never its own sum),
    and the civ.adj alias must point at it."""
    orig, rew = pair
    total = None
    for m in rew.fabric.by_type.values():
        total = m if total is None else total + m
    total = total.tocsr()
    diff = (rew.fabric.adj - total).tocsr()
    if diff.nnz:
        assert float(np.abs(diff.data).max()) == 0.0, (
            "composed adj diverges from sum of typed matrices")
    assert rew.civ.adj is rew.fabric.adj, "civ.adj alias not re-pointed"


# ── edge sets actually changed ──────────────────────────────────────

def test_edge_sets_actually_changed(pair):
    orig, rew = pair
    report = {}
    for name in SWAPPED_TYPES + (MEDIA_TYPE,):
        j = _jaccard(orig.fabric.by_type[name], rew.fabric.by_type[name])
        report[name] = round(j, 4)
        assert j < 0.5, (
            f"{name}: Jaccard overlap {j:.4f} — rewire did not "
            "randomize the edge set (must be well below 1)")
    # printed so the run log carries the measured overlaps
    print(f"\nrewire Jaccard overlap by type: {report}")


# ── determinism ─────────────────────────────────────────────────────

def test_same_seed_identical_rewire(pair):
    orig, _ = pair
    w1, w2 = copy.deepcopy(orig), copy.deepcopy(orig)
    rewire_world_graph(w1, REWIRE_SEED)
    rewire_world_graph(w2, REWIRE_SEED)
    for name in orig.fabric.by_type:
        assert _same_matrix(w1.fabric.by_type[name],
                            w2.fabric.by_type[name]), (
            f"{name}: same seed produced different rewires")
    assert _same_matrix(w1.fabric.adj, w2.fabric.adj)


def test_different_seed_differs(pair):
    orig, rew = pair
    w2 = copy.deepcopy(orig)
    rewire_world_graph(w2, REWIRE_SEED + 1)
    assert any(
        not _same_matrix(rew.fabric.by_type[name], w2.fabric.by_type[name])
        for name in SWAPPED_TYPES + (MEDIA_TYPE,)), (
        "different seeds produced the identical rewire")


# ── (d) aliveness: dead slots untouched ─────────────────────────────

def test_dead_slots_untouched(pair):
    """Rewiring runs among alive agents only: every edge incident to a
    dead slot passes through bit-identical and no dead slot gains a
    partner (degree sequences still exact everywhere)."""
    orig, _ = pair
    w = copy.deepcopy(orig)
    rng = np.random.default_rng(7)
    dead = rng.choice(POP, size=60, replace=False)
    w.health.alive[dead] = False
    before = {name: m.tocsr().copy()
              for name, m in w.fabric.by_type.items()}
    rewire_world_graph(w, REWIRE_SEED)
    dead_mask = np.zeros(POP, dtype=bool)
    dead_mask[dead] = True
    for name, m0 in before.items():
        m1 = w.fabric.by_type[name].tocsr()
        # per-node degree still exact for the swapped types
        if name in SWAPPED_TYPES:
            assert np.array_equal(_deg(m0), _deg(m1)), (
                f"{name}: degree broken with dead slots present")
        # dead-incident edges identical: compare the rows of the dead
        r0, c0, w0 = _triu(m0)
        r1, c1, w1 = _triu(m1)
        n = POP
        inc0 = dead_mask[r0] | dead_mask[c0]
        inc1 = dead_mask[r1] | dead_mask[c1]
        k0 = np.sort(np.minimum(r0[inc0], c0[inc0]) * n
                     + np.maximum(r0[inc0], c0[inc0]))
        k1 = np.sort(np.minimum(r1[inc1], c1[inc1]) * n
                     + np.maximum(r1[inc1], c1[inc1]))
        assert np.array_equal(k0, k1), (
            f"{name}: edges incident to dead slots were rewired")
