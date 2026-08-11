"""Tests for the temporal simulator."""
import sys
sys.path.insert(0, ".")

import numpy as np
import pytest

from earth1.temporal import (
    simulate, simulate_country, compare_scenarios,
    Shock, Timeline, TimePoint, _decay_weights, _HALF_LIVES,
)
from earth1.engine import build_civilization
from earth1.questions import question_by_id
from earth1.types import Force, NUM_FORCES, PERISHABILITY_HALF_LIFE


POP = 10_000
civ = build_civilization(POP, seed=42)


class TestDecayWeights:
    def test_no_decay_at_t0(self):
        w = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
        decayed = _decay_weights(w, 0.0, [])
        np.testing.assert_array_almost_equal(decayed, w)

    def test_fear_decays_fastest(self):
        w = np.ones(NUM_FORCES)
        t = 30.0
        decayed = _decay_weights(w, t, [])
        fear_idx = Force.FEAR.value
        culture_idx = Force.CULTURE.value
        assert decayed[fear_idx] < decayed[culture_idx]

    def test_half_life_correct(self):
        w = np.zeros(NUM_FORCES)
        w[Force.FEAR.value] = 1.0
        hl = PERISHABILITY_HALF_LIFE[Force.FEAR]
        decayed = _decay_weights(w, float(hl), [])
        assert abs(decayed[Force.FEAR.value] - 0.5) < 1e-6

    def test_identity_barely_decays_in_month(self):
        w = np.zeros(NUM_FORCES)
        w[Force.IDENTITY.value] = 1.0
        decayed = _decay_weights(w, 30.0, [])
        assert decayed[Force.IDENTITY.value] > 0.99

    def test_shock_adds_at_injection(self):
        w = np.ones(NUM_FORCES)
        shock = Shock(day=10, label="crisis", shifts={Force.FEAR.value: 2.0})
        decayed = _decay_weights(w, 10.0, [shock])
        no_shock = _decay_weights(w, 10.0, [])
        assert decayed[Force.FEAR.value] > no_shock[Force.FEAR.value]

    def test_shock_decays_after_injection(self):
        w = np.zeros(NUM_FORCES)
        shock = Shock(day=0, label="crisis", shifts={Force.FEAR.value: 2.0})
        at_0 = _decay_weights(w, 0.0, [shock])
        at_30 = _decay_weights(w, 30.0, [shock])
        assert at_0[Force.FEAR.value] > at_30[Force.FEAR.value]

    def test_shock_before_time_not_applied(self):
        w = np.zeros(NUM_FORCES)
        shock = Shock(day=100, label="future", shifts={Force.FEAR.value: 2.0})
        decayed = _decay_weights(w, 50.0, [shock])
        assert decayed[Force.FEAR.value] == 0.0

    def test_multiple_shocks_stack(self):
        w = np.zeros(NUM_FORCES)
        s1 = Shock(day=0, label="a", shifts={Force.FEAR.value: 1.0})
        s2 = Shock(day=0, label="b", shifts={Force.FEAR.value: 1.0})
        one = _decay_weights(w, 0.0, [s1])
        two = _decay_weights(w, 0.0, [s1, s2])
        assert abs(two[Force.FEAR.value] - 2 * one[Force.FEAR.value]) < 1e-6


class TestSimulate:
    def test_returns_timeline(self):
        q = question_by_id("ssm")
        tl = simulate(q, civ, duration_days=90, step_days=30)
        assert isinstance(tl, Timeline)
        assert len(tl.time_points) >= 4

    def test_first_timepoint_is_day_0(self):
        q = question_by_id("ssm")
        tl = simulate(q, civ, duration_days=60, step_days=30)
        assert tl.time_points[0].day == 0

    def test_yes_pct_bounded(self):
        q = question_by_id("ssm")
        tl = simulate(q, civ, duration_days=360, step_days=30)
        for tp in tl.time_points:
            assert 0 <= tp.yes_pct <= 1

    def test_fear_weight_decays_over_time(self):
        q = question_by_id("svb")
        tl = simulate(q, civ, duration_days=360, step_days=30)
        w0 = abs(tl.time_points[0].effective_weights[Force.FEAR.value])
        w360 = abs(tl.time_points[-1].effective_weights[Force.FEAR.value])
        assert w360 < w0 * 0.01

    def test_identity_driven_holds_steady(self):
        q = question_by_id("ssm")
        tl = simulate(q, civ, duration_days=90, step_days=30)
        day0 = tl.time_points[0].yes_pct
        day90 = tl.time_points[-1].yes_pct
        assert abs(day0 - day90) < 0.05

    def test_weight_trajectories_populated(self):
        q = question_by_id("ssm")
        tl = simulate(q, civ, duration_days=90, step_days=30)
        assert "identity" in tl.weight_trajectories
        assert len(tl.weight_trajectories["identity"]) == len(tl.time_points)

    def test_shock_changes_trajectory(self):
        q = question_by_id("ssm")
        no_shock = simulate(q, civ, duration_days=120, step_days=30)
        shock = Shock(day=30, label="moral panic", shifts={Force.FEAR.value: 3.0})
        with_shock = simulate(q, civ, duration_days=120, step_days=30, shocks=[shock])

        tp_no = {tp.day: tp.yes_pct for tp in no_shock.time_points}
        tp_yes = {tp.day: tp.yes_pct for tp in with_shock.time_points}
        assert tp_no[60] != tp_yes[60]

    def test_dominant_transition_detected(self):
        q = question_by_id("svb")
        tl = simulate(q, civ, duration_days=720, step_days=30)
        if tl.dominant_transitions:
            t = tl.dominant_transitions[0]
            assert "day" in t
            assert "from" in t
            assert "to" in t


class TestShock:
    def test_from_forces(self):
        s = Shock.from_forces(30, "crisis", fear=2.0, economics=-1.0)
        assert s.day == 30
        assert s.shifts[Force.FEAR.value] == 2.0
        assert s.shifts[Force.ECONOMICS.value] == -1.0


class TestSimulateCountry:
    def test_returns_all_countries(self):
        q = question_by_id("ssm")
        series = simulate_country(q, civ, duration_days=60, step_days=30)
        assert len(series) == 9

    def test_each_country_has_time_series(self):
        q = question_by_id("ssm")
        series = simulate_country(q, civ, duration_days=90, step_days=30)
        for code, points in series.items():
            assert len(points) >= 3
            assert all("day" in p and "yes_pct" in p for p in points)


class TestCompareScenarios:
    def test_returns_baseline_plus_scenarios(self):
        q = question_by_id("svb")
        scenarios = [
            {"label": "bank_run", "shocks": [
                Shock(day=0, label="bank collapse", shifts={Force.FEAR.value: 3.0}),
            ]},
        ]
        results = compare_scenarios(q, civ, scenarios, duration_days=90, step_days=30)
        assert "baseline" in results
        assert "bank_run" in results

    def test_scenario_diverges_from_baseline(self):
        q = question_by_id("svb")
        scenarios = [
            {"label": "panic", "shocks": [
                Shock(day=0, label="panic", shifts={Force.FEAR.value: 4.0}),
            ]},
        ]
        results = compare_scenarios(q, civ, scenarios, duration_days=90, step_days=30)
        base_final = results["baseline"].time_points[-1].yes_pct
        panic_final = results["panic"].time_points[-1].yes_pct
        assert base_final != panic_final


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
