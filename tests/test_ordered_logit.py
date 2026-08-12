"""Tests for ordered-logit distribution mapping."""
import numpy as np
import pytest
from earth1.ordered_logit import (
    predict_distribution,
    predict_agent_probs,
    calibrate_cutpoints,
    calibrate_cutpoints_global,
    _cutpoints_from_raw,
    _raw_from_cutpoints,
    _jsd,
)
from earth1.rng import logit


class TestCutpointParametrization:
    def test_roundtrip(self):
        cuts = np.array([-1.5, -0.3, 0.8, 2.1])
        raw = _raw_from_cutpoints(cuts)
        recovered = _cutpoints_from_raw(raw)
        np.testing.assert_allclose(recovered, cuts, atol=1e-6)

    def test_ordering_preserved(self):
        raw = np.array([0.5, -2.0, 0.1, 3.0])
        cuts = _cutpoints_from_raw(raw)
        assert all(cuts[i] < cuts[i + 1] for i in range(len(cuts) - 1))


class TestPredictDistribution:
    def test_sums_to_one(self):
        rng = np.random.RandomState(42)
        stances = rng.beta(2, 2, size=10_000)
        cuts = np.array([-1.0, 0.0, 1.0])
        dist = predict_distribution(stances, cuts)
        assert dist.shape == (4,)
        assert abs(dist.sum() - 1.0) < 1e-6

    def test_two_options(self):
        stances = np.full(1000, 0.8)
        cuts = np.array([0.0])
        dist = predict_distribution(stances, cuts)
        assert dist.shape == (2,)
        assert dist[1] > 0.75

    def test_symmetric_stances_symmetric_distribution(self):
        rng = np.random.RandomState(42)
        stances = rng.beta(5, 5, size=50_000)
        cuts = np.array([-0.5, 0.5])
        dist = predict_distribution(stances, cuts)
        assert abs(dist[0] - dist[2]) < 0.02

    def test_extreme_stances(self):
        stances = np.concatenate([np.full(5000, 0.05), np.full(5000, 0.95)])
        cuts = np.array([0.0])
        dist = predict_distribution(stances, cuts)
        assert dist[0] > 0.3 and dist[1] > 0.3

    def test_country_differentiation(self):
        """Different stance distributions should produce different response dists."""
        cuts = np.array([-0.5, 0.5])
        stances_a = np.full(5000, 0.3)
        stances_b = np.full(5000, 0.7)
        dist_a = predict_distribution(stances_a, cuts)
        dist_b = predict_distribution(stances_b, cuts)
        assert dist_a[0] > dist_b[0]
        assert dist_a[2] < dist_b[2]


class TestPredictAgentProbs:
    def test_shape(self):
        z = np.array([0.0, 1.0, -1.0])
        cuts = np.array([-0.5, 0.5])
        probs = predict_agent_probs(z, cuts)
        assert probs.shape == (3, 3)

    def test_rows_sum_to_one(self):
        z = np.linspace(-3, 3, 100)
        cuts = np.array([-1.0, 0.0, 1.0])
        probs = predict_agent_probs(z, cuts)
        np.testing.assert_allclose(probs.sum(axis=1), 1.0, atol=1e-6)

    def test_monotonicity(self):
        """Higher z should give higher probability to higher options."""
        z = np.linspace(-3, 3, 100)
        cuts = np.array([-1.0, 0.0, 1.0])
        probs = predict_agent_probs(z, cuts)
        low_z_mean = probs[:20].mean(axis=0)
        high_z_mean = probs[-20:].mean(axis=0)
        assert low_z_mean[0] > high_z_mean[0]
        assert low_z_mean[-1] < high_z_mean[-1]


class TestJSD:
    def test_identical(self):
        p = np.array([0.3, 0.4, 0.3])
        assert _jsd(p, p) < 1e-10

    def test_symmetric(self):
        p = np.array([0.7, 0.2, 0.1])
        q = np.array([0.1, 0.3, 0.6])
        assert abs(_jsd(p, q) - _jsd(q, p)) < 1e-10

    def test_bounded(self):
        p = np.array([1.0, 0.0, 0.0])
        q = np.array([0.0, 0.0, 1.0])
        assert 0 < _jsd(p, q) <= np.log(2) + 1e-6

    def test_uniform_baseline(self):
        """JSD between a peaked distribution and uniform should be moderate."""
        p = np.array([0.1, 0.8, 0.1])
        u = np.array([1 / 3, 1 / 3, 1 / 3])
        jsd = _jsd(p, u)
        assert 0.05 < jsd < 0.5


class TestCalibrateGlobal:
    def test_recovers_unimodal(self):
        rng = np.random.RandomState(42)
        stances = rng.beta(2, 5, size=20_000)
        target = np.array([0.5, 0.3, 0.15, 0.05])
        cuts = calibrate_cutpoints_global(stances, target, n_options=4)
        pred = predict_distribution(stances, cuts)
        assert _jsd(pred, target) < 0.01

    def test_two_options(self):
        rng = np.random.RandomState(42)
        stances = rng.beta(3, 3, size=10_000)
        target = np.array([0.6, 0.4])
        cuts = calibrate_cutpoints_global(stances, target, n_options=2)
        pred = predict_distribution(stances, cuts)
        np.testing.assert_allclose(pred, target, atol=0.02)


class TestCalibrateCutpoints:
    def test_multi_country(self):
        rng = np.random.RandomState(42)
        n = 30_000
        country = np.repeat(np.arange(3), n // 3)
        stances = np.empty(n)
        stances[country == 0] = rng.beta(2, 5, size=(country == 0).sum())
        stances[country == 1] = rng.beta(5, 5, size=(country == 1).sum())
        stances[country == 2] = rng.beta(5, 2, size=(country == 2).sum())

        targets = {
            "A": np.array([0.6, 0.3, 0.1]),
            "B": np.array([0.2, 0.6, 0.2]),
            "C": np.array([0.1, 0.3, 0.6]),
        }
        indices = {"A": 0, "B": 1, "C": 2}

        cuts = calibrate_cutpoints(stances, country, targets, indices, n_options=3)

        total_jsd = 0.0
        for code, idx in indices.items():
            mask = country == idx
            pred = predict_distribution(stances[mask], cuts)
            total_jsd += _jsd(pred, targets[code])
        avg_jsd = total_jsd / 3

        assert avg_jsd < 0.02

    def test_too_few_countries_returns_default(self):
        stances = np.full(100, 0.5)
        country = np.zeros(100, dtype=int)
        targets = {"A": np.array([0.5, 0.5])}
        indices = {"A": 0}
        cuts = calibrate_cutpoints(stances, country, targets, indices, n_options=2)
        assert len(cuts) == 1

    def test_many_options(self):
        rng = np.random.RandomState(42)
        n = 20_000
        country = np.repeat(np.arange(4), n // 4)
        stances = np.empty(n)
        for i in range(4):
            mask = country == i
            stances[mask] = rng.beta(2 + i, 5 - i * 0.5, size=mask.sum())

        n_opts = 6
        targets = {}
        indices = {}
        for i, code in enumerate(["A", "B", "C", "D"]):
            indices[code] = i
            raw = rng.dirichlet(np.ones(n_opts) * 2)
            targets[code] = raw / raw.sum()

        cuts = calibrate_cutpoints(stances, country, targets, indices, n_options=n_opts)
        assert len(cuts) == n_opts - 1

        total_jsd = 0.0
        for code, idx in indices.items():
            mask = country == idx
            pred = predict_distribution(stances[mask], cuts)
            total_jsd += _jsd(pred, targets[code])
        avg_jsd = total_jsd / len(targets)
        assert avg_jsd < 0.10
