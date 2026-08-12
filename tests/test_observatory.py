"""Tests for the emergence observatory — measuring unprogrammed structure."""
import numpy as np
import pytest

from earth1.observatory import (
    EmergenceMetrics,
    measure_emergence,
    detect_surprises,
    _stance_entropy,
    _kl_divergence,
)
from earth1.genesis import genesis
from earth1.tick import WorldState, run_world
from earth1.event_log import EventLog
from earth1.questions import QUESTIONS


class TestStanceEntropy:
    def test_maximum_at_half(self):
        assert abs(_stance_entropy(0.5) - 1.0) < 1e-10

    def test_zero_at_extremes(self):
        assert _stance_entropy(0.0) == 0.0
        assert _stance_entropy(1.0) == 0.0

    def test_symmetric(self):
        assert abs(_stance_entropy(0.3) - _stance_entropy(0.7)) < 1e-10


class TestKLDivergence:
    def test_zero_for_identical(self):
        assert abs(_kl_divergence(0.5, 0.5)) < 1e-6

    def test_positive_for_different(self):
        assert _kl_divergence(0.7, 0.3) > 0

    def test_asymmetric(self):
        assert _kl_divergence(0.8, 0.2) != _kl_divergence(0.2, 0.8)


class TestMeasureEmergence:
    def test_baseline_vs_itself(self):
        civ = genesis(pop=2_000, seed=42, min_per_country=5)
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"][:3]
        metrics = measure_emergence(civ, civ, questions=qs)
        assert metrics.surprise_index < 1e-6
        assert metrics.trait_drift_magnitude < 1e-6

    def test_metrics_structure(self):
        civ = genesis(pop=2_000, seed=42, min_per_country=5)
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"][:3]
        metrics = measure_emergence(civ, civ, questions=qs)
        assert isinstance(metrics, EmergenceMetrics)
        assert metrics.entropy >= 0
        assert metrics.graph_n_edges > 0
        assert len(metrics.question_divergences) == 3

    def test_evolved_state_has_nonzero_metrics(self):
        state = WorldState.create(pop=5_000, seed=42, min_per_country=10)
        baseline = genesis(pop=5_000, seed=42, min_per_country=10)
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"][:3]

        list(run_world(state, n_ticks=15, questions=qs, batch_size=3, learning_rate=0.05))

        metrics = measure_emergence(
            state.civ, baseline, questions=qs,
            event_log=state.event_log, t=state.t,
            tick_count=state.tick_count,
        )
        assert metrics.tick_count == 15
        assert metrics.trait_drift_magnitude > 0

    def test_unprogrammed_events_counted(self):
        log = EventLog()
        from earth1.event_log import WorldEvent
        log.append(WorldEvent.create(timestamp=0.0, force_deltas={"fear": 0.1}, source="manual"))
        log.append(WorldEvent.create(timestamp=1.0, force_deltas={"fear": 0.1}, source="threshold:test"))
        log.append(WorldEvent.create(timestamp=2.0, force_deltas={"fear": 0.1}, source="emergent:cascade"))

        civ = genesis(pop=2_000, seed=42, min_per_country=5)
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"][:2]
        metrics = measure_emergence(civ, civ, questions=qs, event_log=log)
        assert metrics.n_unprogrammed_events == 2


class TestDetectSurprises:
    def test_no_surprises_on_baseline(self):
        civ = genesis(pop=2_000, seed=42, min_per_country=5)
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"][:3]
        surprises = detect_surprises(civ, civ, questions=qs, min_divergence=0.001)
        assert len(surprises) == 0

    def test_surprises_after_evolution(self):
        state = WorldState.create(pop=5_000, seed=42, min_per_country=10)
        baseline = genesis(pop=5_000, seed=42, min_per_country=10)
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"][:5]

        list(run_world(state, n_ticks=20, questions=qs, batch_size=5, learning_rate=0.05))

        surprises = detect_surprises(
            state.civ, baseline, questions=qs,
            event_log=state.event_log, t=state.t,
            min_divergence=0.0001,
        )
        # After 20 ticks with feedback, should see some divergence
        assert len(surprises) > 0

    def test_surprises_sorted_by_divergence(self):
        state = WorldState.create(pop=5_000, seed=42, min_per_country=10)
        baseline = genesis(pop=5_000, seed=42, min_per_country=10)
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"][:5]

        list(run_world(state, n_ticks=10, questions=qs, batch_size=5, learning_rate=0.05))

        surprises = detect_surprises(
            state.civ, baseline, questions=qs,
            event_log=state.event_log, t=state.t,
            min_divergence=0.0,
        )
        for i in range(len(surprises) - 1):
            assert surprises[i]["kl_divergence"] >= surprises[i + 1]["kl_divergence"]

    def test_surprise_structure(self):
        state = WorldState.create(pop=2_000, seed=42, min_per_country=5)
        baseline = genesis(pop=2_000, seed=42, min_per_country=5)
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"][:3]

        list(run_world(state, n_ticks=10, questions=qs, batch_size=3, learning_rate=0.05))

        surprises = detect_surprises(
            state.civ, baseline, questions=qs, min_divergence=0.0,
        )
        if surprises:
            s = surprises[0]
            assert "question_id" in s
            assert "baseline_yes" in s
            assert "evolved_yes" in s
            assert "delta" in s
            assert "kl_divergence" in s
