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
