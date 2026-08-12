"""Tests for the event log — accumulated experience layer."""
import numpy as np
import pytest

from earth1.event_log import WorldEvent, EventLog, _decay_factor
from earth1.genesis import genesis
from earth1.engine import run_question
from earth1.questions import QUESTIONS
from earth1.types import Force, NUM_FORCES


@pytest.fixture(scope="module")
def civ():
    return genesis(pop=10_000, seed=42, min_per_country=10)


@pytest.fixture
def log():
    return EventLog()


class TestWorldEvent:
    def test_create(self):
        e = WorldEvent.create(timestamp=0.0, force_deltas={"fear": 0.1})
        assert e.timestamp == 0.0
        assert e.force_deltas["fear"] == 0.1
        assert e.source == "manual"
        assert len(e.id) == 8

    def test_frozen(self):
        e = WorldEvent.create(timestamp=0.0, force_deltas={"fear": 0.1})
        with pytest.raises(AttributeError):
            e.timestamp = 1.0


class TestDecay:
    def test_no_decay_at_event_time(self):
        e = WorldEvent.create(timestamp=10.0, force_deltas={"fear": 0.1}, decay_half_life=30.0)
        assert abs(_decay_factor(10.0, e) - 1.0) < 1e-10

    def test_half_life(self):
        e = WorldEvent.create(timestamp=0.0, force_deltas={"fear": 0.1}, decay_half_life=30.0)
        assert abs(_decay_factor(30.0, e) - 0.5) < 1e-10

    def test_double_half_life(self):
        e = WorldEvent.create(timestamp=0.0, force_deltas={"fear": 0.1}, decay_half_life=30.0)
        assert abs(_decay_factor(60.0, e) - 0.25) < 1e-10

    def test_future_event_no_effect(self):
        e = WorldEvent.create(timestamp=100.0, force_deltas={"fear": 0.1})
        assert _decay_factor(50.0, e) == 0.0

    def test_zero_half_life_no_decay(self):
        e = WorldEvent.create(timestamp=0.0, force_deltas={"fear": 0.1}, decay_half_life=0.0)
        assert _decay_factor(1000.0, e) == 1.0


class TestEventLog:
    def test_append_and_len(self, log):
        assert len(log) == 0
        log.append(WorldEvent.create(timestamp=0.0, force_deltas={"fear": 0.1}))
        assert len(log) == 1

    def test_active_events(self, log):
        log.append(WorldEvent.create(timestamp=0.0, force_deltas={"fear": 0.1}, decay_half_life=10.0))
        assert len(log.active_events(0.0)) == 1
        assert len(log.active_events(1000.0)) == 0

    def test_events_returns_copy(self, log):
        log.append(WorldEvent.create(timestamp=0.0, force_deltas={"fear": 0.1}))
        events = log.events()
        events.clear()
        assert len(log) == 1


class TestEffectiveDeltasVectorized:
    def test_empty_log(self, civ):
        log = EventLog()
        deltas = log.effective_deltas_vectorized(0.0, civ)
        assert deltas.shape == (civ.n, NUM_FORCES)
        assert np.all(deltas == 0)

    def test_global_event(self, civ):
        log = EventLog()
        log.append(WorldEvent.create(
            timestamp=0.0, force_deltas={"fear": 0.1, "economics": -0.05},
            region_pattern="*",
        ))
        deltas = log.effective_deltas_vectorized(0.0, civ)
        assert deltas.shape == (civ.n, NUM_FORCES)
        assert np.allclose(deltas[:, Force.FEAR], 0.1)
        assert np.allclose(deltas[:, Force.ECONOMICS], -0.05)
        assert np.allclose(deltas[:, Force.DESIRE], 0.0)

    def test_global_event_with_decay(self, civ):
        log = EventLog()
        log.append(WorldEvent.create(
            timestamp=0.0, force_deltas={"fear": 0.1},
            decay_half_life=30.0,
        ))
        deltas = log.effective_deltas_vectorized(30.0, civ)
        assert np.allclose(deltas[:, Force.FEAR], 0.05, atol=0.001)

    def test_regional_event(self, civ):
        log = EventLog()
        log.append(WorldEvent.create(
            timestamp=0.0, force_deltas={"fear": 0.2},
            region_pattern="IT-*",
        ))
        deltas = log.effective_deltas_vectorized(0.0, civ)
        it_mask = np.zeros(civ.n, dtype=bool)
        from earth1.genesis import GENESIS_COUNTRIES
        it_idx = next(i for i, c in enumerate(GENESIS_COUNTRIES) if c["iso2"] == "IT")
        it_mask = civ.country == it_idx
        assert deltas[it_mask, Force.FEAR].sum() > 0
        non_it = ~it_mask
        assert np.allclose(deltas[non_it, Force.FEAR], 0.0)

    def test_demographic_filter(self, civ):
        log = EventLog()
        log.append(WorldEvent.create(
            timestamp=0.0, force_deltas={"desire": 0.15},
            demographic_filter={"income": 2},
        ))
        deltas = log.effective_deltas_vectorized(0.0, civ)
        high_income = civ.income == 2
        low_income = civ.income == 0
        assert deltas[high_income, Force.DESIRE].mean() > 0.14
        assert np.allclose(deltas[low_income, Force.DESIRE], 0.0)

    def test_stacking_events(self, civ):
        log = EventLog()
        log.append(WorldEvent.create(timestamp=0.0, force_deltas={"fear": 0.1}))
        log.append(WorldEvent.create(timestamp=0.0, force_deltas={"fear": 0.05}))
        deltas = log.effective_deltas_vectorized(0.0, civ)
        assert np.allclose(deltas[:, Force.FEAR], 0.15)


class TestEngineIntegration:
    def test_event_log_shifts_output(self, civ):
        q = QUESTIONS[0]
        r_base = run_question(q, civ)

        log = EventLog()
        log.append(WorldEvent.create(
            timestamp=0.0,
            force_deltas={"fear": 0.3, "identity": -0.2},
            decay_half_life=100.0,
        ))
        r_shifted = run_question(q, civ, event_log=log, t=0.0)
        assert r_shifted.yes_pct != r_base.yes_pct

    def test_no_event_log_unchanged(self, civ):
        q = QUESTIONS[0]
        r1 = run_question(q, civ)
        r2 = run_question(q, civ, event_log=None)
        assert r1.yes_pct == r2.yes_pct

    def test_empty_event_log_unchanged(self, civ):
        q = QUESTIONS[0]
        r1 = run_question(q, civ)
        log = EventLog()
        r2 = run_question(q, civ, event_log=log, t=0.0)
        assert r1.yes_pct == r2.yes_pct
