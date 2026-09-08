"""Randomized-graph arm for the emergence experiment.

founder ruling 2026-09-08: emergence experiment — the randomized-graph
arm asks what the OBSERVED fabric contributes beyond its degree
sequence. This module supplies the arm's one transform: rewire a
birthed world's social graph so that WHO is connected to WHOM is
random while HOW CONNECTED each agent is stays exactly what genesis
made it.

HARNESS TRANSFORM, NOT ENGINE PHYSICS. This file lives under
scripts/emergence/ on purpose: no engine module imports it, it adds no
flag, and it changes nothing unless an experiment runner explicitly
calls it on a world it has already birthed in memory. Frozen physics
is untouched by construction.

What is preserved, per relationship type in ``fabric.by_type``:

  (a) each node's STRUCTURAL degree (tie count) — exactly, via a
      seeded double-edge-swap on the existing edge list (the classic
      degree-preserving randomization: pick two edges (a,b),(c,d),
      replace with (a,d),(c,b), reject self-loops and duplicates);
  (b) the multiset of edge weights — every weight travels with its
      swapped edge, so sorted(triu.data) is identical before/after
      (weighted PER-NODE strength is not an invariant when weights
      are heterogeneous — genesis stacks duplicate draws into single
      heavier ties — and no randomization can preserve both; the
      experiment's contract is tie-count degree + global weight mass);
  (c) symmetry — the typed matrices are mutual (built with
      m.maximum(m.T)); verified on entry, and the rebuild emits each
      undirected edge once and symmetrizes, so it stays exact;
  (d) aliveness — only edges whose BOTH endpoints are alive
      (world.health.alive) participate; edges incident to dead slots
      are carried through untouched and no dead slot gains a partner.

HOUSEHOLD IS EXEMPT — documented choice (founder ruling 2026-09-08:
the experiment randomizes acquaintance structure, not physical
cohabitation). Households in Earth-1 are co-residence structures tied
to locality, not acquaintances: fabric.py builds houses strictly
inside one country with sizes drawn from that country's fertility, and
the ``fabric.household`` id array is load-bearing state — partnership
pairs the two oldest adults of the SAME house (partnership.py),
rebirth seats newborns in the parent's house (rebirth.py), rehome
issues movers fresh house ids (rehome.py), and the income-pooling
story of the household channel assumes the members share a roof.
Rewiring the household matrix while that id array stands would tear
the matrix loose from the ids and create "households" spanning
borders. So the household matrix and the id array pass through
bit-identical.

MEDIA IS SPECIAL — hubs stay hubs by degree, partners randomized. The
media type is a hub-and-spoke graph (HUB_SHARE of the population with
~two orders of magnitude more ties than their audience). A plain
double-edge-swap is near-rigid on a star: with one hub every swap
proposal is a self-loop or a duplicate, so the arm would silently keep
the observed audience. Instead the audience is relabelled by a seeded
permutation of the alive non-hub population: every hub keeps its exact
degree and every audience-degree is carried to the permuted slot, so
the full degree MULTISET is preserved (per-node degree is preserved on
hubs, permuted among the audience), weights travel with their edges,
and who actually hears each hub is random. Hub-hub edges and edges to
dead slots pass through unchanged.

After the typed matrices are rewired the composed adjacency is rebuilt
with the engine's OWN composition, earth1.rehome._recompose_adj (adj =
sum of the typed matrices, and the civ.adj alias re-pointed) — not a
reimplementation, so the arm and the incumbent share one composition
law by construction.

Usage (experiment runner, world already birthed in memory):

    from scripts.emergence.rewire_graph import rewire_world_graph
    rewire_world_graph(world, seed=arm_seed)   # in place, returns None

Regression coverage: tests/test_review_rewire.py (owned by the same
cycle; run with  python3 -m pytest -q tests/test_review_rewire.py).
"""
from __future__ import annotations

import numpy as np
from scipy import sparse

# Attempted double-edge swaps per movable edge. At 10x the chain is far
# past mixing for graphs of this sparsity (the standard prescription);
# the acceptance rate is high because the graphs are sparse, so the
# realized swap count is many multiples of the edge count.
SWAP_FACTOR = 10

# The one type whose ties are co-residence, not acquaintance — see the
# module docstring for the full documented exemption.
EXEMPT_TYPES = ("household",)

MEDIA_TYPE = "media"


def _require_symmetric(name: str, m) -> None:
    """The fabric contract is mutual ties; refuse loudly if broken."""
    if (m != m.T).nnz != 0:
        raise ValueError(
            f"fabric.by_type[{name!r}] is not symmetric — the rewire "
            "utility only defines a randomization for mutual-tie "
            "matrices (fabric.py builds them with m.maximum(m.T))")


def _triu_edges(m):
    """Each undirected edge once (i<j), weights attached."""
    coo = sparse.triu(m, k=1).tocoo()
    return (coo.row.astype(np.int64), coo.col.astype(np.int64),
            coo.data.copy())


def _rebuild_symmetric(rows, cols, data, n, dtype):
    """One entry per undirected edge (either orientation) -> full
    symmetric CSR. half + half.T is exact because no pair appears in
    both orientations (the swap loop enforces canonical uniqueness)."""
    half = sparse.csr_matrix(
        (data.astype(dtype, copy=False), (rows, cols)), shape=(n, n))
    full = (half + half.T).tocsr()
    full.sum_duplicates()
    return full


def _double_edge_swap(rows, cols, alive, rng, n):
    """Degree-preserving randomization of the movable edge slots.

    Mutates ``rows``/``cols`` in place; the weight in slot k stays in
    slot k, so weights travel with their edges. Returns the number of
    accepted swaps and the movable-edge count.
    """
    movable = alive[rows] & alive[cols]
    mov = np.flatnonzero(movable)
    e_mov = int(mov.size)
    if e_mov < 2:
        return 0, e_mov

    # Canonical (min,max) key set of ALL current edges of the type —
    # duplicates must be rejected against fixed edges too.
    lo = np.minimum(rows, cols).astype(np.int64)
    hi = np.maximum(rows, cols).astype(np.int64)
    edge_set = set((lo * n + hi).tolist())

    # Deterministic: the whole proposal stream is drawn up front from
    # the seeded Generator, so acceptance decisions never perturb the
    # draw sequence.
    attempts = SWAP_FACTOR * e_mov
    pick_a = rng.integers(0, e_mov, attempts)
    pick_b = rng.integers(0, e_mov, attempts)
    flip = rng.random(attempts) < 0.5

    swapped = 0
    for t in range(attempts):
        e1 = mov[pick_a[t]]
        e2 = mov[pick_b[t]]
        if e1 == e2:
            continue
        a, b = int(rows[e1]), int(cols[e1])
        c, d = int(rows[e2]), int(cols[e2])
        if flip[t]:
            c, d = d, c
        # proposal: (a,b),(c,d) -> (a,d),(c,b) — every endpoint keeps
        # its tie count.
        if a == d or c == b:
            continue
        k1 = (a * n + d) if a < d else (d * n + a)
        k2 = (c * n + b) if c < b else (b * n + c)
        if k1 == k2 or k1 in edge_set or k2 in edge_set:
            continue
        old1 = (a * n + b) if a < b else (b * n + a)
        old2 = (c * n + d) if c < d else (d * n + c)
        edge_set.discard(old1)
        edge_set.discard(old2)
        edge_set.add(k1)
        edge_set.add(k2)
        rows[e1], cols[e1] = a, d
        rows[e2], cols[e2] = c, b
        swapped += 1
    return swapped, e_mov


def _media_hub_mask(m) -> np.ndarray:
    """Hubs by degree gap. Genesis gives hubs ~TIE_SPEC audience x40
    ties and audience members single digits, two orders of magnitude
    apart, so any threshold in the gap identifies the hubs; a quarter
    of the max degree (floor 3) sits comfortably inside it."""
    deg = m.getnnz(axis=1)
    dmax = int(deg.max()) if deg.size else 0
    if dmax == 0:
        return np.zeros(m.shape[0], dtype=bool)
    return deg >= max(3, dmax // 4)


def _permute_media_audience(m, alive, rng, n):
    """Hubs stay hubs by degree; the audience is relabelled by a seeded
    permutation of the alive non-hub population. Bijective, so no
    self-loops, no collisions, exact degree-multiset preservation."""
    hub = _media_hub_mask(m)
    if not hub.any():
        return m.tocsr(), hub, 0
    rows, cols, data = _triu_edges(m)

    pool = np.flatnonzero(alive & ~hub)
    mapping = np.arange(n, dtype=np.int64)
    if pool.size >= 2:
        mapping[pool] = rng.permutation(pool)

    new_rows, new_cols = rows.copy(), cols.copy()
    # partner = the non-hub endpoint, relabelled only while alive
    i_is_hub, j_is_hub = hub[rows], hub[cols]
    mask_j = i_is_hub & ~j_is_hub & alive[cols]     # j is the audience
    mask_i = j_is_hub & ~i_is_hub & alive[rows]     # i is the audience
    new_cols[mask_j] = mapping[cols[mask_j]]
    new_rows[mask_i] = mapping[rows[mask_i]]
    # hub-hub edges, dead partners, and any stray non-hub pair pass
    # through unchanged.
    moved = int(mask_i.sum() + mask_j.sum())
    return (_rebuild_symmetric(new_rows, new_cols, data, n, m.dtype),
            hub, moved)


def rewire_world_graph(world, seed: int) -> None:
    """Randomize the world's social graph in place (see module doc).

    founder ruling 2026-09-08: emergence experiment. Degree sequences,
    weight multisets, symmetry and aliveness preserved per type;
    household exempt (co-residence, not acquaintance); media audience
    permuted (hubs stay hubs by degree). The composed adjacency is
    rebuilt with the engine's own earth1.rehome._recompose_adj.
    """
    fab = world.fabric
    alive = np.asarray(world.health.alive, dtype=bool)
    n = int(alive.size)
    rng = np.random.default_rng(seed)

    # sorted() so the rng consumption order is a property of the type
    # NAMES, not of dict insertion history; values are replaced under
    # their existing keys so the engine's composition order is
    # untouched.
    for name in sorted(fab.by_type):
        m = fab.by_type[name].tocsr()
        _require_symmetric(name, m)
        if name in EXEMPT_TYPES:
            continue    # documented household exemption, module doc
        if m.nnz == 0:
            continue
        if name == MEDIA_TYPE:
            new_m, _, _ = _permute_media_audience(m, alive, rng, n)
            fab.by_type[name] = new_m
            continue
        rows, cols, data = _triu_edges(m)
        _double_edge_swap(rows, cols, alive, rng, n)
        fab.by_type[name] = _rebuild_symmetric(rows, cols, data, n,
                                               m.dtype)

    # The engine's own composition — adj = sum of typed matrices and
    # the civ.adj alias re-pointed. Never reimplemented here.
    from earth1.rehome import _recompose_adj
    _recompose_adj(world)
