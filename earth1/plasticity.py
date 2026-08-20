"""TIE PLASTICITY — the fabric responds to interaction. Phase 0.5 port.

The one mechanism the disposition ledger earned from the retired
engine family (data/legacy_disposition_ledger.json): interaction-driven
plasticity for FRIENDS and WEAK ties. Agreement strengthens a tie,
disagreement weakens it, dead ties are pruned, and a small fraction of
agents rewire a lost tie toward someone force-similar — over many days
this is how echo chambers form and bridges thin (risk register R15).

THE AUDITED LEGACY LAW, preserved where defensible (0.5 rule: no
parameter tuning for pretty networks — calibration belongs to later
phases):

    agreement  |Δstance| < 0.15  ->  weight + 0.02   (cap 2.0)
    disagree   |Δstance| > 0.60  ->  weight − 0.01
    prune      weight < 0.05     ->  edge removed (both directions)
    rewire     0.5%/day of agents replace one lost/weak tie with a new
               same-camp edge

8-dimensional adaptation (the legacy law read a single settled stance;
the living world has 8 force channels): stance distance is the MEAN
absolute force difference across channels — same [0,1] scale, same
thresholds. "Same-camp" partner selection becomes nearest-of-k by force
distance among k random candidates, which preserves the legacy
semantics (a random same-side partner) probabilistically without an
O(N) camp scan.

OWNERSHIP (ledger tie_type_ownership): this module owns friends+weak
ONLY. Colleague/household/neighbour ties belong to their context
mechanisms (0.0d), diaspora is intentionally non-plastic (kinship),
media is static pending D4-i. Rebirth (0.0b) clears plastic ties with
the occupant; migration (0.0d) converts friends to diaspora before
plasticity ever sees the mover's new row. One execution point in
live_one_day, world RNG only, canonical fabric owns the graph.
"""
from __future__ import annotations

import numpy as np

PLASTIC_TYPES = ("friends", "weak")

AGREE_DIST = 0.15
DISAGREE_DIST = 0.60
AGREEMENT_BOOST = 0.02
DISAGREEMENT_DECAY = 0.01
MIN_WEIGHT = 0.05
MAX_WEIGHT = 2.0
REWIRE_RATE = 0.005
REWIRE_CANDIDATES = 8
_CHUNK = 4_000_000          # edge-gather chunk: bounds peak memory


def _edge_distance(forces, rows, cols):
    """Mean |Δforce| per edge, chunked so 4M-scale gathers stay bounded."""
    out = np.empty(rows.size, dtype=forces.dtype)
    for s in range(0, rows.size, _CHUNK):
        e = min(s + _CHUNK, rows.size)
        out[s:e] = np.abs(forces[rows[s:e]] - forces[cols[s:e]]).mean(axis=1)
    return out


def plasticity_tick(w, rng, dt_days: float = 1.0) -> dict:
    """One day of tie plasticity on friends+weak. Returns counters."""
    from scipy import sparse
    fab = w.fabric
    civ = w.civ
    alive = w.health.alive
    n = civ.n
    stats = {"ties_strengthened": 0, "ties_weakened": 0,
             "ties_pruned": 0, "ties_rewired": 0}

    new_edges_rows, new_edges_cols, new_edges_type = [], [], []

    for tname in PLASTIC_TYPES:
        m = fab.by_type[tname].tocsr()
        if m.nnz == 0:
            continue
        # 0.7: the law is symmetric per edge (dist and aliveness are the
        # same for (i,j) and (j,i)), so both stored directions compute
        # the same new weight independently — no upper-triangle +
        # mirror + full sorted reconstruction (that rebuild was the
        # single hottest non-physics cost of a 4M world-day). The edit
        # runs on CSR arrays in place; pruning is a linear masked
        # rebuild that preserves canonical form. Bit-identical to the
        # mirrored construction — proven by trajectory world_hash A/B.
        indptr, ecols = m.indptr, m.indices
        erows = np.repeat(np.arange(n), np.diff(indptr))
        dist = _edge_distance(civ.forces, erows, ecols)

        agree = dist < AGREE_DIST
        disagree = dist > DISAGREE_DIST
        data = m.data.copy()      # working copy in the graph's own dtype
        # growth clamp only: never grow past MAX_WEIGHT, never collapse
        # a pre-existing heavier tie (genesis stacks duplicates up to
        # ~3.5 — a regime the legacy law never saw; collapsing it would
        # be a mass edit hiding inside a growth rule)
        data[agree] = np.minimum(data[agree] + AGREEMENT_BOOST * dt_days,
                                 np.maximum(data[agree], MAX_WEIGHT))
        data[disagree] = data[disagree] - DISAGREEMENT_DECAY * dt_days
        keep = (data >= MIN_WEIGHT) & alive[erows] & alive[ecols]
        upper = erows < ecols              # stats count each tie once
        stats["ties_strengthened"] += int((agree & upper).sum())
        stats["ties_weakened"] += int((disagree & upper).sum())
        stats["ties_pruned"] += int((~keep & upper).sum())

        csum = np.concatenate(([0], np.cumsum(keep)))
        fab.by_type[tname] = sparse.csr_matrix(
            (data[keep], ecols[keep], csum[indptr]), shape=(n, n))
        new_edges_type.append((tname, int(keep.sum()) // 2))

    # ── rewiring: a few agents replace a lost tie with a kindred one ─
    n_rewire = int(n * REWIRE_RATE * dt_days)
    if n_rewire > 0:
        movers = rng.choice(n, size=min(n_rewire, n), replace=False)
        movers = movers[alive[movers]]
        # 0.7: membership test straight on CSR (indices are sorted per
        # row) — the tolil() this replaces was ~14% of a 4M world-day
        # of pure format conversion. RNG draw order is untouched.
        friends = fab.by_type["friends"].tocsr()
        f_indptr, f_indices = friends.indptr, friends.indices
        add_r, add_c = [], []
        for i in movers:
            i = int(i)
            cand = rng.integers(0, n, size=REWIRE_CANDIDATES)
            cand = cand[alive[cand] & (cand != i)]
            if cand.size == 0:
                continue
            d = np.abs(civ.forces[cand] - civ.forces[i]).mean(axis=1)
            j = int(cand[int(np.argmin(d))])
            row = f_indices[f_indptr[i]:f_indptr[i + 1]]
            pos = np.searchsorted(row, j)
            present = pos < row.size and row[pos] == j
            if not present:
                add_r.extend([i, j])
                add_c.extend([j, i])
        if add_r:
            delta = sparse.csr_matrix(
                (np.full(len(add_r), 0.70,
                         dtype=fab.by_type["friends"].dtype),
                 (add_r, add_c)), shape=(n, n))
            # additions target empty slots only (checked above), so no
            # clamp is needed — and a global clamp here would silently
            # rewrite every existing weight (caught by proof 2's run)
            fab.by_type["friends"] = (fab.by_type["friends"].tocsr()
                                      + delta).tocsr()
            stats["ties_rewired"] = len(add_r) // 2

    # recompose the summed graph so civ.adj stays the one truth
    from earth1.rehome import _recompose_adj
    _recompose_adj(w)
    return stats
