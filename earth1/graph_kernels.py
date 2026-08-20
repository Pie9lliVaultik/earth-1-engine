"""Fused graph kernels — 0.7 performance work, bit-exact by
construction and proven by trajectory hash.

Two kernels, both replacing multi-pass scipy/numpy pipelines whose
intermediate materializations dominate the memory traffic of a 4M
world-day at ensemble concurrency:

- merge_typed_csr: k-way row merge of the typed tie matrices into the
  summed adjacency in ONE pass. Duplicate (i,j) entries accumulate
  LEFT-TO-RIGHT in type order — the identical float association the
  chained csr_plus_csr binops used — and diagonal entries and exact
  zero sums are dropped exactly as the guarded setdiag/eliminate did.

- edge_distance: per-edge mean |Δforce| without materializing the
  (E, K) gather twice. Sequential per-edge channel accumulation in the
  forces dtype — the same order numpy's mean(axis=1) uses below its
  pairwise blocksize.

Numba is an acceleration DEPENDENCY, not a semantics one: when it is
unavailable the callers keep their pure scipy/numpy paths, which these
kernels are proven bit-identical to.
"""
from __future__ import annotations

import numpy as np

try:
    from numba import njit
    HAVE_NUMBA = True
except ImportError:                                     # pragma: no cover
    HAVE_NUMBA = False

    def njit(*a, **k):
        def deco(f):
            return f
        return deco(a[0]) if a and callable(a[0]) else deco


@njit(cache=True)
def _merge_count(indptrs, indices, n):
    """Pass 1: distinct off-diagonal, nonzero-sum column count/row."""
    k = indptrs.shape[0]
    counts = np.zeros(n, dtype=np.int64)
    pos = np.empty(k, dtype=np.int64)
    end = np.empty(k, dtype=np.int64)
    for i in range(n):
        for t in range(k):
            pos[t] = indptrs[t, i]
            end[t] = indptrs[t, i + 1]
        c = 0
        while True:
            j = -1
            for t in range(k):
                if pos[t] < end[t]:
                    cj = indices[t][pos[t]]
                    if j < 0 or cj < j:
                        j = cj
            if j < 0:
                break
            for t in range(k):
                while pos[t] < end[t] and indices[t][pos[t]] == j:
                    pos[t] += 1
            if j != i:
                c += 1
        counts[i] = c
    return counts


@njit(cache=True)
def _merge_fill(indptrs, indices, datas, out_indptr, out_indices,
                out_data, n, zero):
    """Pass 2: fill, accumulating duplicates left-to-right in type
    order; drop diagonal and exact-zero sums (adjusting indptr)."""
    k = indptrs.shape[0]
    pos = np.empty(k, dtype=np.int64)
    end = np.empty(k, dtype=np.int64)
    w = 0
    for i in range(n):
        for t in range(k):
            pos[t] = indptrs[t, i]
            end[t] = indptrs[t, i + 1]
        while True:
            j = -1
            for t in range(k):
                if pos[t] < end[t]:
                    cj = indices[t][pos[t]]
                    if j < 0 or cj < j:
                        j = cj
            if j < 0:
                break
            acc = zero
            for t in range(k):
                while pos[t] < end[t] and indices[t][pos[t]] == j:
                    acc = acc + datas[t][pos[t]]
                    pos[t] += 1
            if j != i and acc != 0.0:
                out_indices[w] = j
                out_data[w] = acc
                w += 1
        out_indptr[i + 1] = w
    return w


def merge_typed_csr(mats, n):
    """Sum the typed CSR matrices into the adjacency in one pass.
    Returns (indptr, indices, data) ready for csr_matrix. Falls back
    to None when numba is unavailable (caller keeps the chained path)."""
    if not HAVE_NUMBA:
        return None
    csrs = [m.tocsr() for m in mats]
    indptrs = np.stack([c.indptr.astype(np.int64) for c in csrs])
    from numba.typed import List
    idx_list = List()
    dat_list = List()
    for c in csrs:
        idx_list.append(c.indices)
        dat_list.append(c.data)
    counts = _merge_count(indptrs, idx_list, n)
    total = int(counts.sum())
    out_dtype = np.result_type(*[c.data.dtype for c in csrs])
    # int32 throughout — nnz < 2^31, and a mixed-width (indptr,
    # indices) pair makes scipy upcast BOTH to int64, doubling the
    # index bytes the merge exists to save
    out_indptr = np.zeros(n + 1, dtype=np.int32)
    out_indices = np.empty(total, dtype=np.int32)
    out_data = np.empty(total, dtype=out_dtype)
    zero = np.zeros(1, dtype=out_dtype)[0]
    w = _merge_fill(indptrs, idx_list, dat_list, out_indptr,
                    out_indices, out_data, n, zero)
    return out_indptr, out_indices[:w], out_data[:w]


@njit(cache=True)
def _edge_dist8(forces, rows, cols, out):
    """K=8, numpy's pairwise-tree association exactly:
    ((a0+a1)+(a2+a3))+((a4+a5)+(a6+a7)) — a sequential loop differs
    by ULPs and breaks bit identity (caught by direct comparison)."""
    for e in range(rows.size):
        i = rows[e]
        j = cols[e]
        d0 = abs(forces[i, 0] - forces[j, 0])
        d1 = abs(forces[i, 1] - forces[j, 1])
        d2 = abs(forces[i, 2] - forces[j, 2])
        d3 = abs(forces[i, 3] - forces[j, 3])
        d4 = abs(forces[i, 4] - forces[j, 4])
        d5 = abs(forces[i, 5] - forces[j, 5])
        d6 = abs(forces[i, 6] - forces[j, 6])
        d7 = abs(forces[i, 7] - forces[j, 7])
        out[e] = (((d0 + d1) + (d2 + d3))
                  + ((d4 + d5) + (d6 + d7))) / 8


def edge_distance(forces, rows, cols):
    """Fused per-edge mean |Δforce|; None when numba is unavailable."""
    if not HAVE_NUMBA:
        return None
    if forces.shape[1] != 8:
        return None                       # caller keeps the numpy path
    out = np.empty(rows.size, dtype=forces.dtype)
    if rows.size:
        _edge_dist8(forces, rows.astype(np.int64),
                    cols.astype(np.int64), out)
    return out
