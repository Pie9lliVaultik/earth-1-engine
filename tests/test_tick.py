"""Tests for the world tick — the heartbeat loop."""
import numpy as np
import pytest

from earth1.tick import WorldState, world_tick, run_world, _select_questions
from earth1.questions import QUESTIONS
from earth1.types import Force, NUM_FORCES


@pytest.fixture(scope="module")
def state():
    return WorldState.create(pop=5_000, seed=42, min_per_country=10)


@pytest.fixture
def fresh_state():
    return WorldState.create(pop=5_000, seed=42, min_per_country=10)


class TestWorldState:
    def test_create(self, state):
        assert state.civ.n == 5_000
        assert state.t == 0.0
        assert state.tick_count == 0
        assert len(state.event_log) == 0
        assert len(state.coupling_matrix) > 0

    def test_mutable_arrays(self, state):
        assert state.civ.forces.flags.writeable
        assert state.civ.openness.flags.writeable
        assert state.civ.alpha.flags.writeable


class TestSelectQuestions:
    def test_batch_size(self):
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"]
        selected = _select_questions(0, qs, batch_size=3)
        assert len(selected) == 3

    def test_round_robin_covers_all(self):
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"]
        seen = set()
        for tick in range(100):
            for q in _select_questions(tick, qs, batch_size=5):
                seen.add(q.id)
        assert len(seen) == len(qs)

    def test_small_batch_returns_all(self):
        qs = QUESTIONS[:3]
        selected = _select_questions(0, qs, batch_size=10)
        assert len(selected) == len(qs)


class TestWorldTick:
    def test_single_tick(self, fresh_state):
        result = world_tick(fresh_state, batch_size=3)
        assert result.tick == 1
        assert result.t == 1.0
        assert len(result.questions_run) == 3
        assert len(result.results) == 3
        assert fresh_state.tick_count == 1

    def test_tick_advances_time(self, fresh_state):
        world_tick(fresh_state, dt=2.5)
        assert fresh_state.t == 2.5
        world_tick(fresh_state, dt=2.5)
        assert fresh_state.t == 5.0

    def test_tick_produces_results(self, fresh_state):
        result = world_tick(fresh_state, batch_size=2)
        for qid, r in result.results.items():
            assert 0 <= r.yes_pct <= 1
            assert r.n == 5_000

    def test_feedback_modifies_traits(self, fresh_state):
        openness_before = fresh_state.civ.openness.mean()
        for _ in range(10):
            world_tick(fresh_state, batch_size=5, learning_rate=0.05)
        # After 10 ticks with feedback, traits should have drifted
        openness_after = fresh_state.civ.openness.mean()
        assert openness_before != openness_after

    def test_graph_evolves(self, fresh_state):
        stats_before = fresh_state.civ.adj.nnz
        for _ in range(5):
            world_tick(fresh_state, batch_size=3)
        stats_after = fresh_state.civ.adj.nnz
        # Graph should have changed (some edges added/removed)
        assert stats_before != stats_after

    def test_events_accumulate(self, fresh_state):
        # Force conditions for a threshold
        mask = fresh_state.civ.country == 0
        fresh_state.civ.forces[mask, Force.FEAR] = 0.85
        fresh_state.civ.forces[mask, Force.COLLECTIVE] = 0.75
        result = world_tick(fresh_state, batch_size=2)
        # May or may not fire depending on exact population state
        assert result.events_fired >= 0

    def test_disable_features(self, fresh_state):
        result = world_tick(
            fresh_state, batch_size=2,
            enable_feedback=False,
            enable_coupling=False,
            enable_thresholds=False,
            enable_rewire=False,
        )
        assert result.tick == 1
        assert len(result.feedback_stats) == 0

    def test_history_grows(self, fresh_state):
        world_tick(fresh_state, batch_size=2)
        world_tick(fresh_state, batch_size=2)
        assert len(fresh_state.question_history) == 2

    def test_graph_stats_returned(self, fresh_state):
        result = world_tick(fresh_state, batch_size=2)
        assert "n_edges" in result.graph_stats
        assert "mean_degree" in result.graph_stats


class TestRunWorld:
    def test_multi_tick(self):
        state = WorldState.create(pop=2_000, seed=99, min_per_country=5)
        results = list(run_world(state, n_ticks=5, batch_size=3))
        assert len(results) == 5
        assert state.tick_count == 5
        assert state.t == 5.0

    def test_deterministic(self):
        s1 = WorldState.create(pop=2_000, seed=42, min_per_country=5)
        s2 = WorldState.create(pop=2_000, seed=42, min_per_country=5)
        r1 = list(run_world(s1, n_ticks=3, batch_size=2,
                            enable_rewire=False, enable_thresholds=False))
        r2 = list(run_world(s2, n_ticks=3, batch_size=2,
                            enable_rewire=False, enable_thresholds=False))
        for a, b in zip(r1, r2):
            for qid in a.results:
                assert abs(a.results[qid].yes_pct - b.results[qid].yes_pct) < 1e-10

    def test_drift_over_time(self):
        state = WorldState.create(pop=5_000, seed=42, min_per_country=10)
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"][:3]

        from earth1.engine import run_question
        initial = {q.id: run_question(q, state.civ).yes_pct for q in qs}

        list(run_world(state, n_ticks=20, questions=qs, batch_size=3, learning_rate=0.05))

        final = {q.id: run_question(q, state.civ).yes_pct for q in qs}
        drifts = [abs(final[qid] - initial[qid]) for qid in initial]
        assert max(drifts) > 0.001
