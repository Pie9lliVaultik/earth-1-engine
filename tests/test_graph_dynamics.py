"""Tests for dynamic graph — evolving social topology."""
import numpy as np
import pytest
from scipy import sparse

from earth1.graph_dynamics import update_graph, graph_stats
from earth1.genesis import genesis


def _mutable_civ(pop=1_000, seed=42):
    civ = genesis(pop=pop, seed=seed, min_per_country=5)
    return civ


def _simple_graph(n=100, k=6, seed=42):
    """Create a simple ring-lattice-like graph."""
    rng = np.random.default_rng(seed)
    rows, cols, data = [], [], []
    for i in range(n):
        for d in range(1, k // 2 + 1):
            j = (i + d) % n
            w = rng.uniform(0.3, 1.0)
            rows.extend([i, j])
            cols.extend([j, i])
            data.extend([w, w])
    return sparse.csr_matrix((data, (rows, cols)), shape=(n, n), dtype=np.float32)


class TestUpdateGraph:
    def test_agreement_strengthens_edges(self):
        n = 100
        adj = _simple_graph(n)
        rng = np.random.default_rng(42)
        settled = np.full(n, 0.5)  # all same opinion = agreement

        initial_mean = adj.data.mean()
        adj_new = update_graph(adj, settled, rng, agreement_boost=0.1, rewire_rate=0.0)
        assert adj_new.data.mean() > initial_mean

    def test_disagreement_weakens_edges(self):
        n = 100
        adj = _simple_graph(n)
        rng = np.random.default_rng(42)
        # Alternate opinions
        settled = np.zeros(n)
        settled[::2] = 0.95
        settled[1::2] = 0.05

        initial_mean = adj.data.mean()
        adj_new = update_graph(adj, settled, rng, disagreement_decay=0.1, rewire_rate=0.0)
        assert adj_new.data.mean() < initial_mean

    def test_dead_edges_removed(self):
        n = 100
        adj = _simple_graph(n)
        rng = np.random.default_rng(42)
        settled = np.zeros(n)
        settled[::2] = 0.95
        settled[1::2] = 0.05

        # Many rounds of disagreement decay should kill edges
        for _ in range(50):
            adj = update_graph(adj, settled, rng, disagreement_decay=0.05, rewire_rate=0.0)
        assert adj.nnz < _simple_graph(n).nnz

    def test_rewiring_creates_new_connections(self):
        n = 200
        adj = _simple_graph(n)
        rng = np.random.default_rng(42)
        settled = np.zeros(n)
        settled[:100] = 0.8
        settled[100:] = 0.2

        adj_before = adj.copy()
        adj_new = update_graph(adj, settled, rng, rewire_rate=0.1)
        # Structure should differ
        diff = (adj_new - adj_before)
        diff.eliminate_zeros()
        assert diff.nnz > 0

    def test_weights_stay_bounded(self):
        n = 100
        adj = _simple_graph(n)
        rng = np.random.default_rng(42)
        settled = np.full(n, 0.5)

        for _ in range(100):
            adj = update_graph(adj, settled, rng, agreement_boost=0.1, max_weight=2.0)
        assert adj.data.max() <= 2.0

    def test_graph_shape_preserved(self):
        civ = _mutable_civ()
        rng = np.random.default_rng(42)
        settled = np.random.default_rng(42).random(civ.n)
        adj_new = update_graph(civ.adj, settled, rng)
        assert adj_new.shape == civ.adj.shape

    def test_empty_graph_handled(self):
        n = 50
        adj = sparse.csr_matrix((n, n), dtype=np.float32)
        rng = np.random.default_rng(42)
        settled = np.full(n, 0.5)
        adj_new = update_graph(adj, settled, rng)
        assert adj_new.shape == (n, n)

    def test_multiple_updates_deterministic(self):
        n = 100
        adj1 = _simple_graph(n)
        adj2 = _simple_graph(n)
        settled = np.random.default_rng(99).random(n)
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        r1 = update_graph(adj1, settled, rng1)
        r2 = update_graph(adj2, settled, rng2)
        assert abs(r1.data.mean() - r2.data.mean()) < 1e-6


class TestGraphStats:
    def test_stats_on_genesis_graph(self):
        civ = _mutable_civ()
        stats = graph_stats(civ.adj)
        assert stats["n_edges"] > 0
        assert stats["mean_degree"] > 0
        assert stats["mean_weight"] > 0
        assert stats["isolated_nodes"] >= 0

    def test_stats_on_empty_graph(self):
        adj = sparse.csr_matrix((50, 50), dtype=np.float32)
        stats = graph_stats(adj)
        assert stats["n_edges"] == 0
        assert stats["mean_degree"] == 0

    def test_edge_count_consistent(self):
        n = 100
        adj = _simple_graph(n)
        stats = graph_stats(adj)
        assert stats["n_edges"] == adj.nnz // 2
