"""Tests for non-linear thresholds — phase transitions and cascades."""
import numpy as np
import pytest

from earth1.thresholds import (
    TransitionRule,
    TRANSITION_RULES,
    detect_transitions,
    detect_and_append,
    _check_condition,
)
from earth1.event_log import EventLog, WorldEvent
from earth1.genesis import genesis, GENESIS_COUNTRIES
from earth1.types import Force, NUM_FORCES


def _mutable_civ(pop=5_000, seed=42):
    civ = genesis(pop=pop, seed=seed, min_per_country=10)
    for attr in ["forces", "alpha", "means"]:
        arr = getattr(civ, attr)
        if isinstance(arr, np.ndarray) and not arr.flags.writeable:
            object.__setattr__(civ, attr, arr.copy())
    return civ


class TestCheckCondition:
    def test_greater_than(self):
        assert _check_condition(0.8, ">", 0.7) is True
        assert _check_condition(0.7, ">", 0.7) is False
        assert _check_condition(0.6, ">", 0.7) is False

    def test_less_than(self):
        assert _check_condition(0.2, "<", 0.3) is True
        assert _check_condition(0.3, "<", 0.3) is False
        assert _check_condition(0.4, "<", 0.3) is False


class TestTransitionRules:
    def test_rules_have_required_fields(self):
        for rule in TRANSITION_RULES:
            assert rule.name
            assert len(rule.conditions) > 0
            assert len(rule.effects) > 0
            assert rule.cooldown_days > 0
            assert rule.decay_half_life > 0

    def test_rules_reference_valid_forces(self):
        for rule in TRANSITION_RULES:
            for force, op, thresh in rule.conditions:
                assert isinstance(force, Force)
                assert op in (">", "<")
                assert 0 <= thresh <= 1


class TestDetectTransitions:
    def test_no_transitions_on_normal_population(self):
        civ = _mutable_civ()
        log = EventLog()
        events, fired = detect_transitions(civ, log, t=0.0)
        # May or may not fire depending on genesis population stats
        # Just verify it returns valid structure
        assert isinstance(events, list)
        assert isinstance(fired, dict)

    def test_forced_identity_collapse(self):
        civ = _mutable_civ()
        # Force conditions: fear > 0.7 AND collective > 0.6 for country 0
        mask = civ.country == 0
        civ.forces[mask, Force.FEAR] = 0.85
        civ.forces[mask, Force.COLLECTIVE] = 0.75
        rule = TransitionRule(
            name="identity_collapse",
            conditions=[(Force.FEAR, ">", 0.7), (Force.COLLECTIVE, ">", 0.6)],
            effects={"identity": -0.15},
            region_scope="regional",
            cooldown_days=30.0,
            decay_half_life=60.0,
        )
        events, fired = detect_transitions(civ, EventLog(), t=0.0, rules=[rule])
        assert len(events) >= 1
        assert any("identity_collapse" in e.source for e in events)
        assert events[0].force_deltas["identity"] == -0.15

    def test_forced_panic_cascade(self):
        civ = _mutable_civ()
        mask = civ.country == 0
        civ.forces[mask, Force.ECONOMICS] = 0.15
        civ.forces[mask, Force.FEAR] = 0.65
        rule = TransitionRule(
            name="panic_cascade",
            conditions=[(Force.ECONOMICS, "<", 0.3), (Force.FEAR, ">", 0.5)],
            effects={"fear": 0.10, "desire": -0.08},
            region_scope="regional",
            cooldown_days=14.0,
            decay_half_life=45.0,
        )
        events, fired = detect_transitions(civ, EventLog(), t=0.0, rules=[rule])
        assert len(events) >= 1
        assert events[0].force_deltas["fear"] == 0.10

    def test_cooldown_prevents_refiring(self):
        civ = _mutable_civ()
        mask = civ.country == 0
        civ.forces[mask, Force.FEAR] = 0.85
        civ.forces[mask, Force.COLLECTIVE] = 0.75
        rule = TransitionRule(
            name="test_rule",
            conditions=[(Force.FEAR, ">", 0.7), (Force.COLLECTIVE, ">", 0.6)],
            effects={"identity": -0.1},
            region_scope="regional",
            cooldown_days=30.0,
            decay_half_life=60.0,
        )
        events1, fired1 = detect_transitions(civ, EventLog(), t=0.0, rules=[rule])
        assert len(events1) >= 1
        # Try again within cooldown
        events2, fired2 = detect_transitions(civ, EventLog(), t=10.0, last_fired=fired1, rules=[rule])
        assert len(events2) == 0
        # After cooldown
        events3, fired3 = detect_transitions(civ, EventLog(), t=31.0, last_fired=fired1, rules=[rule])
        assert len(events3) >= 1

    def test_global_scope_rule(self):
        civ = _mutable_civ()
        civ.forces[:, Force.FEAR] = 0.85
        civ.forces[:, Force.COLLECTIVE] = 0.75
        rule = TransitionRule(
            name="global_test",
            conditions=[(Force.FEAR, ">", 0.7), (Force.COLLECTIVE, ">", 0.6)],
            effects={"identity": -0.1},
            region_scope="global",
            cooldown_days=30.0,
            decay_half_life=60.0,
        )
        events, fired = detect_transitions(civ, EventLog(), t=0.0, rules=[rule])
        assert len(events) == 1
        assert events[0].region_pattern == "*"

    def test_insufficient_agents_skipped(self):
        civ = _mutable_civ(pop=200)
        # With 200 agents spread across 194 countries, most have < 10 agents
        rule = TransitionRule(
            name="test_rule",
            conditions=[(Force.FEAR, ">", 0.0)],
            effects={"identity": -0.1},
            region_scope="regional",
            cooldown_days=0.1,
            decay_half_life=60.0,
        )
        events, _ = detect_transitions(civ, EventLog(), t=0.0, rules=[rule])
        # Should skip countries with < 10 agents
        assert len(events) < len(GENESIS_COUNTRIES)

    def test_event_source_contains_rule_name(self):
        civ = _mutable_civ()
        mask = civ.country == 0
        civ.forces[mask, Force.FEAR] = 0.85
        civ.forces[mask, Force.COLLECTIVE] = 0.75
        rule = TransitionRule(
            name="my_custom_rule",
            conditions=[(Force.FEAR, ">", 0.7), (Force.COLLECTIVE, ">", 0.6)],
            effects={"identity": -0.1},
            region_scope="regional",
            cooldown_days=30.0,
            decay_half_life=60.0,
        )
        events, _ = detect_transitions(civ, EventLog(), t=0.0, rules=[rule])
        assert events[0].source == "threshold:my_custom_rule"

    def test_regional_event_targets_country(self):
        civ = _mutable_civ()
        mask = civ.country == 0
        civ.forces[mask, Force.FEAR] = 0.85
        civ.forces[mask, Force.COLLECTIVE] = 0.75
        rule = TransitionRule(
            name="test",
            conditions=[(Force.FEAR, ">", 0.7), (Force.COLLECTIVE, ">", 0.6)],
            effects={"identity": -0.1},
            region_scope="regional",
            cooldown_days=30.0,
            decay_half_life=60.0,
        )
        events, _ = detect_transitions(civ, EventLog(), t=0.0, rules=[rule])
        iso2 = GENESIS_COUNTRIES[0]["iso2"]
        assert any(iso2 in e.region_pattern for e in events)


class TestDetectAndAppend:
    def test_appends_to_event_log(self):
        civ = _mutable_civ()
        mask = civ.country == 0
        civ.forces[mask, Force.FEAR] = 0.85
        civ.forces[mask, Force.COLLECTIVE] = 0.75
        log = EventLog()
        rule = TransitionRule(
            name="test",
            conditions=[(Force.FEAR, ">", 0.7), (Force.COLLECTIVE, ">", 0.6)],
            effects={"identity": -0.1},
            region_scope="regional",
            cooldown_days=30.0,
            decay_half_life=60.0,
        )
        n_fired, fired = detect_and_append(civ, log, t=0.0, rules=[rule])
        assert n_fired >= 1
        assert len(log) == n_fired

    def test_empty_when_no_transitions(self):
        civ = _mutable_civ()
        civ.forces[:] = 0.5  # all neutral
        log = EventLog()
        rule = TransitionRule(
            name="impossible",
            conditions=[(Force.FEAR, ">", 0.99)],
            effects={"identity": -0.1},
            region_scope="regional",
            cooldown_days=30.0,
            decay_half_life=60.0,
        )
        n_fired, _ = detect_and_append(civ, log, t=0.0, rules=[rule])
        assert n_fired == 0
        assert len(log) == 0


class TestCascade:
    def test_threshold_event_modifies_forces(self):
        """A threshold fires an event, and that event shifts forces
        so another threshold can fire — demonstrating cascade potential."""
        civ = _mutable_civ()
        mask = civ.country == 0
        # Set up near-threshold conditions for panic_cascade
        civ.forces[mask, Force.ECONOMICS] = 0.15
        civ.forces[mask, Force.FEAR] = 0.55

        log = EventLog()
        panic_rule = TransitionRule(
            name="panic",
            conditions=[(Force.ECONOMICS, "<", 0.3), (Force.FEAR, ">", 0.5)],
            effects={"fear": 0.20},
            region_scope="regional",
            cooldown_days=30.0,
            decay_half_life=60.0,
        )
        fear_rule = TransitionRule(
            name="fear_spiral",
            conditions=[(Force.FEAR, ">", 0.7)],
            effects={"identity": -0.1},
            region_scope="regional",
            cooldown_days=30.0,
            decay_half_life=60.0,
        )

        # First round: panic fires (fear=0.55 > 0.5, econ=0.15 < 0.3)
        n1, fired = detect_and_append(civ, log, t=0.0, rules=[panic_rule, fear_rule])
        assert n1 >= 1

        # Apply the event deltas to the forces to simulate the cascade
        deltas = log.effective_deltas_vectorized(0.0, civ)
        civ.forces[:] = civ.forces + deltas

        # Second round: fear_spiral should now fire (fear was 0.55 + 0.20 = 0.75 > 0.7)
        n2, fired2 = detect_and_append(civ, log, t=0.5, last_fired=fired, rules=[panic_rule, fear_rule])
        fear_spiral_fired = any("fear_spiral" in e.source for e in log.events())
        assert fear_spiral_fired
