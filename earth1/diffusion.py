"""Attention layer: bounded-confidence diffusion (Hegselmann-Krause).

s_i^(l+1) = alpha_i * s_i^(0) + (1 - alpha_i) * mean{ s_j : j in N(i), |s_j - s_i| < epsilon }

Fully vectorized using sparse matrix ops — no Python per-agent loops.
"""
from __future__ import annotations
from typing import List
import numpy as np
from scipy import sparse


def diffuse(
    s0: np.ndarray,
    alpha: np.ndarray,
    adj: sparse.csr_matrix,
    epsilon: float,
    layers: int,
) -> List[np.ndarray]:
    """Run K layers of bounded-confidence diffusion. Returns list of (N,) snapshots."""
    n = len(s0)
    snapshots = [s0.copy()]
    cur = s0.copy()

    rows, cols = adj.nonzero()

    for _ in range(layers):
        # compute |s_j - s_i| for every edge
        diffs = np.abs(cur[cols] - cur[rows])
        mask = diffs < epsilon

        # build masked adjacency with values = s_j where within epsilon
        masked_vals = cur[cols] * mask
        masked_adj = sparse.csr_matrix((masked_vals, (rows, cols)), shape=(n, n))
        counts_adj = sparse.csr_matrix((mask.astype(np.float64), (rows, cols)), shape=(n, n))

        sums = np.asarray(masked_adj.sum(axis=1)).ravel()
        counts = np.asarray(counts_adj.sum(axis=1)).ravel()

        safe_counts = np.where(counts > 0, counts, 1.0)
        social = np.where(counts > 0, sums / safe_counts, cur)
        cur = alpha * s0 + (1.0 - alpha) * social
        snapshots.append(cur.copy())

    return snapshots
