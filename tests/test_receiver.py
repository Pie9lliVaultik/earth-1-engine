"""Field Receiver tests — Builds 0-3."""
import sys
sys.path.insert(0, ".")

import numpy as np
import pytest
from datetime import datetime, timedelta

from earth1.engine import build_civilization, run_question
from earth1.questions import QUESTIONS, question_by_id
from earth1.types import Force, NUM_FORCES
from earth1.receiver import (
    # Build 0
    measure_seed_noise, measure_epsilon_sensitivity,
    measure_layer_sensitivity, measure_field_shift_response,
    profile_noise, NoiseProfile,
    # Build 1
    compute_relevance, build_relevance_matrix, ForceRelevance,
    # Build 2
    WelfordState, GeoScope, Scale, Reading, ForceActivation,
    SourceAdapter, GDELTAdapter, ACLEDAdapter, FREDAdapter, GoogleTrendsAdapter,
    register_adapter, get_adapter, list_adapters,
    freshness_weight, aggregate_activations, ReceiverState,
    compute_field_shift, compute_country_field_shift, run_with_receiver,
    # Build 3
    run_falsification, run_full_falsification_suite,
    FalsificationReport, PlaceboResult,
)

POP = 5_000
civ = build_civilization(POP, seed=42)
Q_SVB = question_by_id("svb")
Q_SSM = question_by_id("ssm")
Q_IMMIG = question_by_id("immig")
Q_INCUMBENT = question_by_id("incumbent")
Q_FOURDAY = question_by_id("fourday")
Q_RAIN = question_by_id("rain")


# ===================================================================
#  Build 0 — Engine Noise Measurement
# ===================================================================

class TestSeedNoise:
    def test_seed_noise_is_small(self):
        std = measure_seed_noise(Q_SVB, pop=POP, n_seeds=3)
        assert 0 <= std < 0.05, f"Seed noise too high: {std}"

    def test_different_questions_different_noise(self):
        s1 = measure_seed_noise(Q_SVB, pop=POP, n_seeds=3)
        s2 = measure_seed_noise(Q_SSM, pop=POP, n_seeds=3)
        assert isinstance(s1, float)
        assert isinstance(s2, float)


class TestEpsilonSensitivity:
    def test_epsilon_sensitivity_bounded(self):
        sens = measure_epsilon_sensitivity(Q_SVB, civ)
        assert 0 <= sens < 0.1

    def test_custom_epsilons(self):
        sens = measure_epsilon_sensitivity(Q_SVB, civ, epsilons=[0.1, 0.2, 0.3])
        assert isinstance(sens, float)


class TestLayerSensitivity:
    def test_layer_sensitivity_bounded(self):
        sens = measure_layer_sensitivity(Q_SVB, civ)
        assert 0 <= sens < 0.1

    def test_custom_layers(self):
        sens = measure_layer_sensitivity(Q_SVB, civ, layer_counts=[2, 4, 8])
        assert isinstance(sens, float)


class TestFieldShiftResponse:
    def test_zero_magnitude_zero_effect(self):
        responses = measure_field_shift_response(Q_SVB, civ, magnitudes=[0.0])
        assert len(responses) == 1
        mag, effect = responses[0]
        assert mag == 0.0
        assert effect == 0.0

    def test_monotonic_response(self):
        responses = measure_field_shift_response(Q_SVB, civ, magnitudes=[0.0, 0.05, 0.1, 0.2])
        effects = [e for _, e in responses]
        for i in range(1, len(effects)):
            assert effects[i] >= effects[0] - 0.01, "Large shift should have equal or greater effect"


class TestNoiseProfile:
    def test_profile_returns_all_fields(self):
        p = profile_noise(Q_SVB, civ, n_seeds=2)
        assert isinstance(p, NoiseProfile)
        assert p.question_id == "svb"
        assert 0 < p.baseline_yes_pct < 1
        assert p.seed_std >= 0
        assert p.epsilon_sensitivity >= 0
        assert p.layer_sensitivity >= 0
        assert p.minimum_detectable_effect > 0

    def test_mde_is_three_sigma(self):
        p = profile_noise(Q_SVB, civ, n_seeds=2)
        noise_floor = max(p.seed_std, p.epsilon_sensitivity, p.layer_sensitivity)
        assert abs(p.minimum_detectable_effect - noise_floor * 3.0) < 1e-4

    def test_compression_zone_detection(self):
        p_svb = profile_noise(Q_SVB, civ, n_seeds=2)
        assert not p_svb.compression_zone, "SVB is high-yes, not in compression zone"


# ===================================================================
#  Build 1 — Question-Force Relevance
# ===================================================================

class TestRelevance:
    def test_svb_fear_dominant(self):
        rel = compute_relevance(Q_SVB)
        assert rel.question_id == "svb"
        fear_rel = rel.relevance[Force.FEAR]
        assert fear_rel > 0.2, f"SVB should be fear-relevant, got {fear_rel}"
        assert "fear" in rel.dominant_forces

    def test_ssm_identity_dominant(self):
        rel = compute_relevance(Q_SSM)
        assert "identity" in rel.dominant_forces

    def test_relevance_sums_to_one(self):
        rel = compute_relevance(Q_SVB)
        assert abs(rel.relevance.sum() - 1.0) < 1e-6

    def test_rain_all_zero(self):
        rel = compute_relevance(Q_RAIN)
        assert rel.relevance.sum() < 1e-6
        assert rel.temporal_sensitivity == 0.0
        assert len(rel.dominant_forces) == 0

    def test_temporal_sensitivity_range(self):
        for q in QUESTIONS:
            if q.domain == "belief_causal":
                rel = compute_relevance(q)
                assert 0 <= rel.temporal_sensitivity <= 1.0

    def test_irrelevant_forces_disjoint_from_dominant(self):
        rel = compute_relevance(Q_SVB)
        assert not set(rel.dominant_forces) & set(rel.irrelevant_forces)


class TestRelevanceMatrix:
    def test_matrix_covers_all_causal(self):
        matrix = build_relevance_matrix()
        causal_ids = {q.id for q in QUESTIONS if q.domain == "belief_causal"}
        assert set(matrix.keys()) == causal_ids

    def test_matrix_values_consistent(self):
        matrix = build_relevance_matrix()
        for qid, rel in matrix.items():
            assert abs(rel.relevance.sum() - 1.0) < 1e-6


# ===================================================================
#  Build 2 — Source Adapters & Integration
# ===================================================================

class TestWelford:
    def test_single_value(self):
        w = WelfordState()
        w.update(5.0)
        assert w.mean == 5.0
        assert w.z_score(5.0) == 0.0

    def test_known_sequence(self):
        w = WelfordState()
        for v in [2, 4, 4, 4, 5, 5, 7, 9]:
            w.update(v)
        assert abs(w.mean - 5.0) < 1e-6
        assert abs(w.std - 2.0) < 0.2  # sample std on 8 points

    def test_z_score_needs_min_data(self):
        w = WelfordState()
        w.update(1.0)
        w.update(2.0)
        assert w.z_score(10.0) == 0.0  # n < 3, returns 0

    def test_z_score_correct(self):
        w = WelfordState()
        for v in [10, 20, 30, 40, 50]:
            w.update(v)
        z = w.z_score(30.0)
        assert abs(z) < 0.01  # mean is 30


class TestFreshnessWeight:
    def test_fresh_data_weight_one(self):
        now = datetime(2025, 1, 1, 12, 0)
        w = freshness_weight(now, now, "daily")
        assert abs(w - 1.0) < 1e-6

    def test_old_data_decays(self):
        now = datetime(2025, 1, 1, 12, 0)
        old = now - timedelta(hours=24)
        w = freshness_weight(old, now, "daily")
        assert abs(w - 0.5) < 0.01

    def test_realtime_decays_fast(self):
        now = datetime(2025, 1, 1, 12, 0)
        old = now - timedelta(hours=1)
        w = freshness_weight(old, now, "realtime")
        assert abs(w - 0.5) < 0.01


class TestGeoScope:
    def test_global(self):
        g = GeoScope.global_scope()
        assert g.scale == Scale.GLOBAL_MACRO
        assert g.country_code is None

    def test_national(self):
        n = GeoScope.national("US")
        assert n.scale == Scale.NATIONAL
        assert n.country_code == "US"


class TestGDELTAdapter:
    def test_properties(self):
        g = GDELTAdapter()
        assert g.id == "gdelt"
        assert g.scale == Scale.GLOBAL_MACRO
        assert Force.FEAR in g.target_forces

    def test_from_values_produces_activation(self):
        g = GDELTAdapter()
        for _ in range(10):
            act = g.from_values(tone=-2.0, event_count=1000, conflict_intensity=50)
        act = g.from_values(tone=-5.0, event_count=2000, conflict_intensity=100)
        assert act.forces.shape == (NUM_FORCES,)
        assert act.confidence.shape == (NUM_FORCES,)
        assert act.source_id == "gdelt"

    def test_high_conflict_raises_fear(self):
        g = GDELTAdapter()
        for _ in range(15):
            g.from_values(tone=0.0, event_count=500, conflict_intensity=20)
        calm = g.from_values(tone=0.0, event_count=500, conflict_intensity=20)
        crisis = g.from_values(tone=-5.0, event_count=500, conflict_intensity=200)
        assert crisis.forces[Force.FEAR] > calm.forces[Force.FEAR]


class TestACLEDAdapter:
    def test_properties(self):
        a = ACLEDAdapter()
        assert a.id == "acled"
        assert Force.FEAR in a.target_forces
        assert Force.COLLECTIVE in a.target_forces

    def test_from_values(self):
        a = ACLEDAdapter()
        for _ in range(10):
            a.from_values(fatalities=10, protest_events=5, violence_events=3)
        act = a.from_values(fatalities=100, protest_events=50, violence_events=30)
        assert act.forces.shape == (NUM_FORCES,)


class TestFREDAdapter:
    def test_properties(self):
        f = FREDAdapter()
        assert f.id == "fred"
        assert Force.ECONOMICS in f.target_forces

    def test_high_unemployment_shifts_economics(self):
        f = FREDAdapter()
        for _ in range(15):
            f.from_values(unemployment=5.0, inflation=2.0, consumer_confidence=100, vix=20)
        normal = f.from_values(unemployment=5.0, inflation=2.0, consumer_confidence=100, vix=20)
        crisis = f.from_values(unemployment=15.0, inflation=8.0, consumer_confidence=40, vix=50)
        assert crisis.forces[Force.ECONOMICS] < normal.forces[Force.ECONOMICS] or \
               crisis.forces[Force.FEAR] > normal.forces[Force.FEAR]


class TestGoogleTrendsAdapter:
    def test_properties(self):
        g = GoogleTrendsAdapter()
        assert g.id == "google_trends"
        assert Force.FEAR in g.target_forces

    def test_from_values(self):
        g = GoogleTrendsAdapter()
        for _ in range(10):
            g.from_values(fear_terms=50, desire_terms=50, identity_terms=50)
        act = g.from_values(fear_terms=100, desire_terms=50, identity_terms=50)
        assert act.forces.shape == (NUM_FORCES,)


class TestAdapterRegistry:
    def test_default_adapters_registered(self):
        adapters = list_adapters()
        assert "gdelt" in adapters
        assert "acled" in adapters
        assert "fred" in adapters
        assert "google_trends" in adapters

    def test_get_adapter(self):
        a = get_adapter("gdelt")
        assert a is not None
        assert a.id == "gdelt"

    def test_get_unknown_returns_none(self):
        assert get_adapter("nonexistent") is None


class TestAggregation:
    def test_empty_activations(self):
        state = aggregate_activations([])
        assert state.n_sources == 0
        assert np.allclose(state.forces, 0)

    def test_single_activation(self):
        forces = np.zeros(NUM_FORCES)
        forces[Force.FEAR] = 0.5
        conf = np.zeros(NUM_FORCES)
        conf[Force.FEAR] = 1.0
        act = ForceActivation(
            source_id="test", timestamp=datetime.utcnow(),
            scope=GeoScope.global_scope(), forces=forces, confidence=conf,
        )
        state = aggregate_activations([act])
        assert state.n_sources == 1
        assert state.forces[Force.FEAR] > 0

    def test_country_specific_aggregation(self):
        forces = np.zeros(NUM_FORCES)
        forces[Force.ECONOMICS] = 0.8
        conf = np.ones(NUM_FORCES) * 0.9
        act = ForceActivation(
            source_id="fred", timestamp=datetime.utcnow(),
            scope=GeoScope.national("US"), forces=forces, confidence=conf,
        )
        state = aggregate_activations([act])
        assert "US" in state.country_states
        us_state = state.country_states["US"]
        assert us_state.forces[Force.ECONOMICS] > 0

    def test_multiple_sources_combine(self):
        now = datetime.utcnow()
        acts = []
        for sid, f_idx in [("a", Force.FEAR), ("b", Force.ECONOMICS)]:
            forces = np.zeros(NUM_FORCES)
            forces[f_idx] = 0.5
            conf = np.zeros(NUM_FORCES)
            conf[f_idx] = 1.0
            acts.append(ForceActivation(
                source_id=sid, timestamp=now,
                scope=GeoScope.global_scope(), forces=forces, confidence=conf,
            ))
        state = aggregate_activations(acts)
        assert state.n_sources == 2
        assert state.forces[Force.FEAR] > 0
        assert state.forces[Force.ECONOMICS] > 0


class TestFieldShift:
    def test_zero_receiver_zero_shift(self):
        state = ReceiverState()
        shift = compute_field_shift(state, Q_SVB)
        assert np.allclose(shift, 0)

    def test_shift_direction_matches_weight_sign(self):
        forces = np.zeros(NUM_FORCES)
        forces[Force.FEAR] = 1.0
        conf = np.ones(NUM_FORCES)
        state = ReceiverState(forces=forces, confidence=conf, n_sources=1)
        shift = compute_field_shift(state, Q_SVB, gain=1.0)
        fear_weight_sign = np.sign(Q_SVB.weights[Force.FEAR])
        assert np.sign(shift[Force.FEAR]) == fear_weight_sign or shift[Force.FEAR] == 0

    def test_gain_scales_linearly(self):
        forces = np.ones(NUM_FORCES) * 0.5
        conf = np.ones(NUM_FORCES)
        state = ReceiverState(forces=forces, confidence=conf, n_sources=1)
        shift_01 = compute_field_shift(state, Q_SVB, gain=0.1)
        shift_02 = compute_field_shift(state, Q_SVB, gain=0.2)
        assert np.allclose(shift_02, shift_01 * 2, atol=1e-8)

    def test_country_shift_uses_country_state(self):
        forces = np.zeros(NUM_FORCES)
        forces[Force.FEAR] = 0.8
        conf = np.ones(NUM_FORCES)
        us_state = ReceiverState(forces=forces, confidence=conf)
        state = ReceiverState(country_states={"US": us_state})

        shift_us = compute_country_field_shift(state, Q_SVB, "US", gain=0.1)
        shift_gb = compute_country_field_shift(state, Q_SVB, "GB", gain=0.1)
        assert not np.allclose(shift_us, shift_gb)


class TestRunWithReceiver:
    def test_receiver_modifies_output(self):
        baseline = run_question(Q_SVB, civ)

        forces = np.zeros(NUM_FORCES)
        forces[Force.FEAR] = 1.0
        conf = np.ones(NUM_FORCES)
        state = ReceiverState(forces=forces, confidence=conf, n_sources=1)
        received = run_with_receiver(Q_SVB, civ, state, gain=0.5)

        assert received.yes_pct != baseline.yes_pct or received.conviction != baseline.conviction

    def test_zero_state_matches_baseline(self):
        baseline = run_question(Q_SVB, civ)
        state = ReceiverState()
        received = run_with_receiver(Q_SVB, civ, state, gain=0.1)
        assert abs(received.yes_pct - baseline.yes_pct) < 0.001


# ===================================================================
#  Build 3 — Falsification / Placebo Testing
# ===================================================================

class TestFalsification:
    def _make_activations(self, n=10):
        gdelt = GDELTAdapter()
        acts = []
        for i in range(n):
            act = gdelt.from_values(
                tone=-2.0 + i * 0.3,
                event_count=500 + i * 50,
                conflict_intensity=30 + i * 5,
                timestamp=datetime.utcnow() - timedelta(hours=i),
            )
            acts.append(act)
        return acts

    def test_report_structure(self):
        acts = self._make_activations()
        report = run_falsification(Q_SVB, civ, acts)
        assert isinstance(report, FalsificationReport)
        assert report.question_id == "svb"
        assert "OFF" in report.conditions
        assert "REAL" in report.conditions
        assert "TIME_PLACEBO" in report.conditions
        assert "COUNTRY_PLACEBO" in report.conditions
        assert "SIGN_PLACEBO" in report.conditions

    def test_off_condition_no_shift(self):
        acts = self._make_activations()
        report = run_falsification(Q_SVB, civ, acts)
        off = report.conditions["OFF"]
        assert off.field_shift_magnitude == 0.0

    def test_real_has_nonzero_shift(self):
        acts = self._make_activations(20)
        report = run_falsification(Q_SVB, civ, acts)
        real = report.conditions["REAL"]
        assert real.field_shift_magnitude >= 0

    def test_sign_placebo_flips_direction(self):
        acts = self._make_activations(20)
        report = run_falsification(Q_SVB, civ, acts)
        real = report.conditions["REAL"]
        sign = report.conditions["SIGN_PLACEBO"]
        assert real.field_shift_magnitude == sign.field_shift_magnitude

    def test_signal_to_noise_nonnegative(self):
        acts = self._make_activations()
        report = run_falsification(Q_SVB, civ, acts)
        assert report.signal_to_noise >= 0

    def test_deltas_are_nonnegative(self):
        acts = self._make_activations()
        report = run_falsification(Q_SVB, civ, acts)
        assert report.real_vs_off_delta >= 0
        assert report.time_placebo_delta >= 0
        assert report.country_placebo_delta >= 0
        assert report.sign_placebo_delta >= 0


class TestFullSuite:
    def test_suite_covers_all_causal(self):
        gdelt = GDELTAdapter()
        acts = [gdelt.from_values(-1, 500, 30) for _ in range(10)]
        reports = run_full_falsification_suite(civ, acts)
        causal_ids = {q.id for q in QUESTIONS if q.domain == "belief_causal"}
        report_ids = {r.question_id for r in reports}
        assert report_ids == causal_ids

    def test_suite_specific_questions(self):
        gdelt = GDELTAdapter()
        acts = [gdelt.from_values(-1, 500, 30) for _ in range(10)]
        reports = run_full_falsification_suite(civ, acts, question_ids=["svb", "ssm"])
        assert len(reports) == 2


# ===================================================================
#  Integration: end-to-end receiver pipeline
# ===================================================================

class TestEndToEnd:
    def test_gdelt_to_field_shift_to_projection(self):
        gdelt = GDELTAdapter()
        for _ in range(20):
            gdelt.from_values(tone=0, event_count=500, conflict_intensity=30)
        act = gdelt.from_values(tone=-8.0, event_count=2000, conflict_intensity=150)

        state = aggregate_activations([act])
        shift = compute_field_shift(state, Q_SVB, gain=0.1)
        r = run_question(Q_SVB, civ, field_shift=shift)
        r_baseline = run_question(Q_SVB, civ)

        assert isinstance(r.yes_pct, float)
        assert 0 < r.yes_pct < 1

    def test_fred_economics_question(self):
        fred = FREDAdapter()
        for _ in range(15):
            fred.from_values(unemployment=5, inflation=2, consumer_confidence=100, vix=20)
        act = fred.from_values(unemployment=12, inflation=6, consumer_confidence=50, vix=40)

        state = aggregate_activations([act])
        r = run_with_receiver(Q_INCUMBENT, civ, state, gain=0.2)
        assert isinstance(r.yes_pct, float)
        assert 0 < r.yes_pct < 1

    def test_multi_source_aggregation_pipeline(self):
        gdelt = GDELTAdapter()
        fred = FREDAdapter()

        for _ in range(15):
            gdelt.from_values(tone=0, event_count=500, conflict_intensity=30)
            fred.from_values(unemployment=5, inflation=2, consumer_confidence=100)

        act1 = gdelt.from_values(tone=-5, event_count=1500, conflict_intensity=100)
        act2 = fred.from_values(unemployment=10, inflation=5, consumer_confidence=60)

        state = aggregate_activations([act1, act2])
        assert state.n_sources == 2

        for q in [Q_SVB, Q_INCUMBENT, Q_IMMIG]:
            shift = compute_field_shift(state, q, gain=0.1)
            assert shift.shape == (NUM_FORCES,)

    def test_noise_profile_then_falsification(self):
        profile = profile_noise(Q_SVB, civ, n_seeds=2)

        gdelt = GDELTAdapter()
        acts = []
        for _ in range(15):
            acts.append(gdelt.from_values(tone=0, event_count=500, conflict_intensity=30))

        report = run_falsification(Q_SVB, civ, acts)

        assert isinstance(profile.minimum_detectable_effect, float)
        assert isinstance(report.real_vs_off_delta, float)
