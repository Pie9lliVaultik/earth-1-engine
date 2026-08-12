"""Tests for Build 26 — source adapter wiring into the tick loop."""
import sys
sys.path.insert(0, ".")

from datetime import datetime
import numpy as np

from earth1.receiver import (
    ReceiverConfig, SourceConfig, sense_sources, activations_to_events,
    ForceActivation, GeoScope, Scale, GDELTAdapter, FREDAdapter,
    ACLEDAdapter, GoogleTrendsAdapter,
)
from earth1.event_log import EventLog, WorldEvent
from earth1.tick import WorldState, world_tick, run_world
from earth1.questions import QUESTIONS
from earth1.types import Force, NUM_FORCES


class TestReceiverConfig:
    def test_default_has_four_sources(self):
        config = ReceiverConfig.default()
        assert len(config.sources) == 4
        ids = {s.source_id for s in config.sources}
        assert ids == {"gdelt", "acled", "fred", "google_trends"}

    def test_offline_has_no_sources(self):
        config = ReceiverConfig.offline()
        assert len(config.sources) == 0

    def test_source_config_fields(self):
        sc = SourceConfig("gdelt", poll_interval_ticks=1, gain=0.1, decay_half_life=3.0)
        assert sc.enabled is True
        assert sc.poll_interval_ticks == 1


class TestActivationsToEvents:
    def test_empty_activations(self):
        config = ReceiverConfig.default()
        events = activations_to_events([], t=0.0, config=config)
        assert events == []

    def test_global_activation_produces_star_region(self):
        forces = np.zeros(NUM_FORCES)
        forces[Force.FEAR] = 0.5
        conf = np.zeros(NUM_FORCES)
        conf[Force.FEAR] = 0.8

        act = ForceActivation(
            source_id="gdelt", timestamp=datetime.utcnow(),
            scope=GeoScope.global_scope(),
            forces=forces, confidence=conf,
        )
        config = ReceiverConfig.default()
        events = activations_to_events([act], t=10.0, config=config)

        assert len(events) >= 1
        ev = events[0]
        assert ev.region_pattern == "*"
        assert ev.source == "receiver:gdelt"
        assert ev.timestamp == 10.0
        assert "fear" in ev.force_deltas

    def test_country_activation_produces_country_region(self):
        forces = np.zeros(NUM_FORCES)
        forces[Force.ECONOMICS] = 0.3
        conf = np.ones(NUM_FORCES)

        act = ForceActivation(
            source_id="fred", timestamp=datetime.utcnow(),
            scope=GeoScope.national("US"),
            forces=forces, confidence=conf,
        )
        config = ReceiverConfig.default()
        events = activations_to_events([act], t=5.0, config=config)

        assert len(events) >= 1
        assert events[0].region_pattern == "US-*"

    def test_zero_magnitude_produces_no_events(self):
        forces = np.zeros(NUM_FORCES)
        conf = np.ones(NUM_FORCES)

        act = ForceActivation(
            source_id="gdelt", timestamp=datetime.utcnow(),
            scope=GeoScope.global_scope(),
            forces=forces, confidence=conf,
        )
        config = ReceiverConfig.default()
        events = activations_to_events([act], t=0.0, config=config)
        assert events == []

    def test_gain_scales_deltas(self):
        forces = np.zeros(NUM_FORCES)
        forces[Force.FEAR] = 1.0
        conf = np.ones(NUM_FORCES)

        act = ForceActivation(
            source_id="gdelt", timestamp=datetime.utcnow(),
            scope=GeoScope.global_scope(),
            forces=forces, confidence=conf,
        )

        config_low = ReceiverConfig(sources=[
            SourceConfig("gdelt", gain=0.05, decay_half_life=3.0),
        ])
        config_high = ReceiverConfig(sources=[
            SourceConfig("gdelt", gain=0.2, decay_half_life=3.0),
        ])

        events_low = activations_to_events([act], t=0.0, config=config_low)
        events_high = activations_to_events([act], t=0.0, config=config_high)

        assert abs(events_low[0].force_deltas["fear"]) < abs(events_high[0].force_deltas["fear"])


class TestSenseSources:
    def test_offline_config_returns_empty(self):
        config = ReceiverConfig.offline()
        activations = sense_sources(config, tick=0)
        assert activations == []

    def test_poll_interval_respects_cadence(self):
        config = ReceiverConfig(sources=[
            SourceConfig("gdelt", poll_interval_ticks=5, gain=0.1),
        ])
        # Tick 0 should poll (0 % 5 == 0)
        # Tick 1 should not (1 % 5 != 0)
        # Tick 5 should poll (5 % 5 == 0)
        # (actual fetch may fail without network, but the cadence gate should work)
        # We can't test the actual fetch without network, so this is a structural test


class TestTickWithReceiver:
    def test_tick_with_receiver_disabled(self):
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"]
        state = WorldState.create(pop=1_000, seed=42, min_per_country=3, questions=qs)
        result = world_tick(state, questions=qs, enable_receiver=False)
        assert result.tick == 1
        # No receiver events
        receiver_events = [e for e in state.event_log.events()
                          if e.source.startswith("receiver:")]
        assert len(receiver_events) == 0

    def test_tick_with_receiver_no_config(self):
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"]
        state = WorldState.create(pop=1_000, seed=42, min_per_country=3, questions=qs)
        # enable_receiver=True but no config — should not crash
        result = world_tick(state, questions=qs, enable_receiver=True)
        assert result.tick == 1

    def test_receiver_events_injected_into_event_log(self):
        """Simulate receiver by manually injecting activations as events."""
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"]
        state = WorldState.create(pop=1_000, seed=42, min_per_country=3, questions=qs)

        # Manually inject a receiver event
        event = WorldEvent.create(
            timestamp=0.0,
            force_deltas={"fear": 0.1, "economics": -0.05},
            region_pattern="*",
            decay_half_life=10.0,
            source="receiver:gdelt",
        )
        state.event_log.append(event)

        result = world_tick(state, questions=qs)
        assert result.tick == 1
        assert len(state.event_log) >= 1

    def test_receiver_events_affect_predictions(self):
        """Injecting a strong fear event should shift fear-sensitive questions."""
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"]
        state1 = WorldState.create(pop=5_000, seed=42, min_per_country=10, questions=qs)
        state2 = WorldState.create(pop=5_000, seed=42, min_per_country=10, questions=qs)

        # State 2 gets a strong fear event
        event = WorldEvent.create(
            timestamp=0.0,
            force_deltas={"fear": 0.3},
            region_pattern="*",
            decay_half_life=30.0,
            source="receiver:test",
        )
        state2.event_log.append(event)

        from earth1.engine import run_question
        fear_q = next(q for q in qs if q.id == "nuclear_risk")

        r1 = run_question(fear_q, state1.civ, event_log=state1.event_log, t=0.0)
        r2 = run_question(fear_q, state2.civ, event_log=state2.event_log, t=0.0)

        # Fear event should increase nuclear_risk yes_pct
        assert r2.yes_pct > r1.yes_pct, (
            f"Fear event should increase nuclear_risk: {r1.yes_pct:.4f} vs {r2.yes_pct:.4f}"
        )


class TestFromValuesOffline:
    """Test adapters' from_values() methods which work without network."""

    def test_gdelt_from_values(self):
        adapter = GDELTAdapter()
        for i in range(10):
            act = adapter.from_values(
                tone=-2.0 + i * 0.4, event_count=100 + i * 10,
                conflict_intensity=0.5 + i * 0.1,
            )
            assert act.forces.shape == (NUM_FORCES,)

        # After warmup, z-scores should be meaningful
        act = adapter.from_values(tone=-5.0, event_count=200, conflict_intensity=2.0)
        assert act.forces[Force.FEAR] > 0, "Negative tone + high conflict → fear should be positive"

    def test_fred_from_values(self):
        adapter = FREDAdapter()
        for i in range(15):
            act = adapter.from_values(
                unemployment=4.0 + i * 0.1, inflation=3.0 + i * 0.05,
                consumer_confidence=70 + i, vix=20 + i * 0.5,
            )
            assert act.forces.shape == (NUM_FORCES,)

        # High unemployment spike
        act = adapter.from_values(unemployment=8.0, inflation=3.0, consumer_confidence=50, vix=35)
        assert act.forces[Force.FEAR] > 0, "High VIX → fear positive"

    def test_acled_from_values(self):
        adapter = ACLEDAdapter()
        for i in range(10):
            act = adapter.from_values(
                fatalities=10 + i * 5, protest_events=20 + i * 3,
                violence_events=5 + i * 2,
            )
            assert act.forces.shape == (NUM_FORCES,)

        # Spike in violence
        act = adapter.from_values(fatalities=100, protest_events=50, violence_events=30)
        assert act.forces[Force.FEAR] > 0

    def test_google_trends_from_values(self):
        adapter = GoogleTrendsAdapter()
        for i in range(10):
            act = adapter.from_values(
                fear_terms=30 + i * 5, desire_terms=25 + i * 3,
                identity_terms=20 + i * 2,
            )
            assert act.forces.shape == (NUM_FORCES,)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
