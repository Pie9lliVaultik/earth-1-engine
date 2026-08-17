"""Batched rewiring must be EXACTLY the sequential reference.

The batch path (2026-08-17) exists purely for performance — O(edges)
instead of O(agents x edges) per tick. Physics must be unchanged:
identical final adjacency for identical inputs and RNG, including the
subtle cases (later agents seeing earlier rewires, 0.5-weight ties).
"""
import numpy as np
import pytest
from scipy import sparse

from earth1.graph_dynamics import update_graph, _update_graph_reference


def _canon(m):
    m = m.tocsr().copy()
    m.sum_duplicates()
    m.sort_indices()
    return m


def _random_graph(seed, n=400):
    rng = np.random.default_rng(seed)
    r = rng.integers(0, n, size=n * 8)
    c = rng.integers(0, n, size=n * 8)
    keep = r != c
    r, c = r[keep], c[keep]
    w = rng.choice([0.5, 0.5, 0.8, 1.0, 0.06, 0.3],
                   size=len(r)).astype(np.float32)
    adj = sparse.csr_matrix(
        (np.concatenate([w, w]),
         (np.concatenate([r, c]), np.concatenate([c, r]))),
        shape=(n, n), dtype=np.float32)
    adj.sum_duplicates()
    return adj, rng.random(n)


@pytest.mark.parametrize("seed", range(6))
def test_batch_equals_reference(seed):
    adj, settled = _random_graph(seed)
    a = _canon(update_graph(adj, settled, np.random.default_rng(seed + 50)))
    b = _canon(_update_graph_reference(adj, settled,
                                       np.random.default_rng(seed + 50)))
    assert a.shape == b.shape and a.nnz == b.nnz
    assert np.array_equal(a.indptr, b.indptr)
    assert np.array_equal(a.indices, b.indices)
    assert np.array_equal(a.data, b.data)


def test_batch_equals_reference_chained():
    adj, settled = _random_graph(99)
    a, b = adj.copy(), adj.copy()
    for i in range(3):
        a = _canon(update_graph(a, settled, np.random.default_rng(7 + i)))
        b = _canon(_update_graph_reference(b, settled,
                                           np.random.default_rng(7 + i)))
        assert np.array_equal(a.indices, b.indices)
        assert np.array_equal(a.data, b.data)
