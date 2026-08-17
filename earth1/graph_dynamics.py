"""Dynamic graph — social topology that evolves from opinion interactions.

Agents who agree strengthen connections; agents who disagree weaken them.
Over many ticks, echo chambers form, bridges thin, and diffusion dynamics
change as information flows through a reshaped topology."""

from __future__ import annotations

import numpy as np
from scipy import sparse

from earth1.types import Civilization


def update_graph(
    adj: sparse.csr_matrix,
    settled: np.ndarray,
    rng: np.random.Generator,
    agreement_boost: float = 0.02,
    disagreement_decay: float = 0.01,
    rewire_rate: float = 0.005,
    min_weight: float = 0.05,
    max_weight: float = 2.0,
) -> sparse.csr_matrix:
    """Evolve the social graph based on opinion interaction.

    1. Reinforcement: edges with |s_i - s_j| < 0.15 get boosted
    2. Decay: edges with |s_i - s_j| > 0.6 get weakened
    3. Pruning: edges below min_weight are removed
    4. Rewiring: random agents drop weakest edge, form new same-camp edge
    """
    adj = adj.copy().tocsr()
    rows, cols = adj.nonzero()

    if len(rows) == 0:
        return adj

    diff = np.abs(settled[rows] - settled[cols])

    agree_mask = diff < 0.15
    disagree_mask = diff > 0.6

    data = np.array(adj[rows, cols]).ravel()
    data[agree_mask] = np.minimum(data[agree_mask] + agreement_boost, max_weight)
    data[disagree_mask] = data[disagree_mask] - disagreement_decay

    alive = data >= min_weight
    new_rows = rows[alive]
    new_cols = cols[alive]
    new_data = data[alive]

    n = adj.shape[0]
    adj = sparse.csr_matrix((new_data, (new_rows, new_cols)), shape=(n, n), dtype=np.float32)

    n_rewire = int(n * rewire_rate)
    if n_rewire > 0:
        # BATCHED rewiring (2026-08-17 night). The old path wrote edges
        # one at a time into CSR — each structural insertion shifts the
        # whole compressed array: O(agents x edges) per tick, quadratic
        # in world size, measured as ~100% of the 10M event leg's 11+
        # hours (py-spy, 6/6 samples) while the grid measured rewiring's
        # predictive contribution at zero. Mutations are now STAGED and
        # applied in ONE rebuild. Sequential semantics preserved
        # exactly: reads overlay staged changes (later agents see
        # earlier rewires) and RNG draw order is unchanged — proven
        # equal to _update_graph_reference across seeds (test suite).
        adj.sort_indices()
        candidates = rng.choice(n, size=min(n_rewire, n), replace=False)
        yes_camp = settled >= 0.5
        yes_indices = np.where(yes_camp)[0]
        no_indices = np.where(~yes_camp)[0]

        staged: dict = {}  # row -> {col: value}; 0.0 marks deletion

        def _row_view(a: int):
            lo, hi = adj.indptr[a], adj.indptr[a + 1]
            base_cols = adj.indices[lo:hi]
            base_w = adj.data[lo:hi]
            over = staged.get(a)
            if not over:
                return base_cols, base_w
            merged = dict(zip(base_cols.tolist(), base_w.tolist()))
            merged.update(over)
            cols_s = sorted(c for c, v in merged.items() if v != 0.0)
            return (np.array(cols_s, dtype=np.int64),
                    np.array([merged[c] for c in cols_s], dtype=base_w.dtype))

        for agent in candidates:
            cols_i, weights_i = _row_view(int(agent))
            if len(cols_i) < 2:
                continue
            weakest_idx = int(cols_i[np.argmin(weights_i)])

            camp = yes_indices if yes_camp[agent] else no_indices
            if len(camp) < 2:
                continue
            target = int(camp[rng.integers(len(camp))])
            while target == agent and len(camp) > 1:
                target = int(camp[rng.integers(len(camp))])
            if target == agent:
                continue

            a = int(agent)
            staged.setdefault(a, {})[weakest_idx] = 0.0
            staged.setdefault(weakest_idx, {})[a] = 0.0
            staged.setdefault(a, {})[target] = 0.5
            staged.setdefault(target, {})[a] = 0.5

        if staged:
            # one rebuild: drop every staged pair from the base matrix,
            # then append the staged entries that survived (non-zero)
            base = adj.tocoo()
            key = base.row.astype(np.int64) * n + base.col.astype(np.int64)
            s_rows, s_cols, s_vals = [], [], []
            for r, d in staged.items():
                for c, v in d.items():
                    s_rows.append(r), s_cols.append(c), s_vals.append(v)
            s_rows = np.array(s_rows, dtype=np.int64)
            s_cols = np.array(s_cols, dtype=np.int64)
            s_vals = np.array(s_vals, dtype=np.float32)
            keep = ~np.isin(key, s_rows * n + s_cols)
            live = s_vals != 0.0
            adj = sparse.csr_matrix(
                (np.concatenate([base.data[keep], s_vals[live]]),
                 (np.concatenate([base.row[keep], s_rows[live]]),
                  np.concatenate([base.col[keep], s_cols[live]]))),
                shape=(n, n), dtype=np.float32)

    return adj


def _update_graph_reference(
    adj: sparse.csr_matrix,
    settled: np.ndarray,
    rng: np.random.Generator,
    agreement_boost: float = 0.02,
    disagreement_decay: float = 0.01,
    rewire_rate: float = 0.005,
    min_weight: float = 0.05,
    max_weight: float = 2.0,
) -> sparse.csr_matrix:
    """The pre-2026-08-17 sequential implementation, kept VERBATIM as
    the equality oracle for the batched path (see tests)."""
    adj = adj.copy().tocsr()
    rows, cols = adj.nonzero()
    if len(rows) == 0:
        return adj
    diff = np.abs(settled[rows] - settled[cols])
    agree_mask = diff < 0.15
    disagree_mask = diff > 0.6
    data = np.array(adj[rows, cols]).ravel()
    data[agree_mask] = np.minimum(data[agree_mask] + agreement_boost, max_weight)
    data[disagree_mask] = data[disagree_mask] - disagreement_decay
    alive = data >= min_weight
    n = adj.shape[0]
    adj = sparse.csr_matrix((data[alive], (rows[alive], cols[alive])),
                            shape=(n, n), dtype=np.float32)
    n_rewire = int(n * rewire_rate)
    if n_rewire > 0:
        candidates = rng.choice(n, size=min(n_rewire, n), replace=False)
        yes_camp = settled >= 0.5
        yes_indices = np.where(yes_camp)[0]
        no_indices = np.where(~yes_camp)[0]
        for agent in candidates:
            row = adj.getrow(agent)
            if row.nnz < 2:
                continue
            cols_i = row.indices
            weights_i = row.data
            weakest_idx = cols_i[np.argmin(weights_i)]
            camp = yes_indices if yes_camp[agent] else no_indices
            if len(camp) < 2:
                continue
            target = camp[rng.integers(len(camp))]
            while target == agent and len(camp) > 1:
                target = camp[rng.integers(len(camp))]
            if target == agent:
                continue
            adj[agent, weakest_idx] = 0
            adj[weakest_idx, agent] = 0
            adj[agent, target] = 0.5
            adj[target, agent] = 0.5
        adj.eliminate_zeros()
    return adj


def graph_stats(adj: sparse.csr_matrix) -> dict:
    """Compute basic graph statistics."""
    degrees = np.array(adj.sum(axis=1)).ravel()
    nnz = adj.nnz
    n = adj.shape[0]
    mean_degree = nnz / n if n > 0 else 0
    weights = adj.data
    return {
        "n_edges": nnz // 2,
        "mean_degree": float(mean_degree),
        "mean_weight": float(weights.mean()) if len(weights) > 0 else 0.0,
        "max_weight": float(weights.max()) if len(weights) > 0 else 0.0,
        "min_weight": float(weights.min()) if len(weights) > 0 else 0.0,
        "isolated_nodes": int((degrees == 0).sum()),
    }
