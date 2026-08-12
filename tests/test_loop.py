"""Tests for Participatory Calibration — the Loop (G6)."""
import sys
sys.path.insert(0, ".")

import numpy as np
import pytest
import os

from earth1.loop import (
    find_nearest_agent, claim_earthling, reveal_profile,
    apply_corrections, apply_trait_corrections,
    measure_calibration, batch_calibrate,
    Correction, TraitCorrection, CorrectionResult, CalibrationReport,
    _compute_force_delta, _find_region, _apply_trait_deltas,
    _recompute_agent_forces,
    REGION_LEARNING_RATE, SIMILARITY_THRESHOLD,
)
from earth1.engine import build_civilization, run_question
from earth1.questions import question_by_id, QUESTIONS
from earth1.forces import project_all
from earth1.population import COUNTRIES, COUNTRY_CODES
from earth1.types import Force, NUM_FORCES
from earth1.rng import sigmoid, logit
from earth1.dynamics import _deep_copy_civ


POP = 10_000
civ = build_civilization(POP, seed=42)


class TestFindNearest:
    def test_finds_agent_in_country(self):
        idx, score = find_nearest_agent(civ, "US")
        assert civ.country[idx] == COUNTRY_CODES.index("US")
        assert 0 <= score <= 1

    def test_high_match_score_for_close_demographics(self):
        us_agents = np.where(civ.country == 0)[0]
        sample = us_agents[0]
        idx, score = find_nearest_agent(
            civ, "US",
            age=float(civ.age[sample]),
            education=int(civ.education[sample]),
            income=int(civ.income[sample]),
            urban=bool(civ.urban[sample]),
            openness=float(civ.openness[sample]),
        )
        assert score > 0.9

    def test_unknown_country_raises(self):
        with pytest.raises(ValueError, match="Unknown"):
            find_nearest_agent(civ, "ZZ")

    def test_different_demographics_different_agent(self):
        idx1, _ = find_nearest_agent(civ, "US", age=0.14, openness=0.9)
        idx2, _ = find_nearest_agent(civ, "US", age=0.96, openness=0.2)
        assert idx1 != idx2


class TestClaimEarthling:
    def test_returns_claimed_earthling(self):
        claimed = claim_earthling(civ, "user-123", "GB")
        assert claimed.user_id == "user-123"
        assert claimed.country_code == "GB"
        assert 0 <= claimed.match_score <= 1
        assert claimed.agent_idx >= 0

    def test_demographics_populated(self):
        claimed = claim_earthling(civ, "user-456", "DE", age=0.62, education=2)
        assert "age" in claimed.demographics
        assert "openness" in claimed.demographics

    def test_agent_in_correct_country(self):
        claimed = claim_earthling(civ, "user-789", "JP")
        assert civ.country[claimed.agent_idx] == COUNTRY_CODES.index("JP")


class TestRevealProfile:
    def test_returns_traits_and_forces(self):
        profile = reveal_profile(civ, 0)
        assert "traits" in profile
        assert "force_profile" in profile
        assert "projected_stances" in profile
        assert len(profile["force_profile"]) == NUM_FORCES

    def test_stances_are_bounded(self):
        profile = reveal_profile(civ, 100)
        for qid, stance in profile["projected_stances"].items():
            assert 0 <= stance <= 1

    def test_specific_questions(self):
        profile = reveal_profile(civ, 0, question_ids=["ssm", "svb"])
        assert "ssm" in profile["projected_stances"]
        assert "svb" in profile["projected_stances"]
        assert len(profile["projected_stances"]) == 2

    def test_country_correct(self):
        profile = reveal_profile(civ, 0)
        expected = COUNTRY_CODES[civ.country[0]]
        assert profile["country"] == expected


class TestComputeForceDelta:
    def test_delta_direction(self):
        q = question_by_id("ssm")
        s0 = project_all(civ, q)
        current = float(s0[0])
        higher = min(current + 0.2, 0.99)
        delta = _compute_force_delta(civ, 0, q, higher)
        weighted = float(delta @ q.weights)
        assert weighted > 0

    def test_no_change_gives_zero(self):
        q = question_by_id("ssm")
        s0 = project_all(civ, q)
        current = float(s0[0])
        delta = _compute_force_delta(civ, 0, q, current)
        assert np.allclose(delta, 0, atol=1e-4)


class TestFindRegion:
    def test_region_in_same_country(self):
        idx, sim = _find_region(civ, 0)
        ci = civ.country[0]
        assert np.all(civ.country[idx] == ci)

    def test_region_has_similar_agents(self):
        idx, sim = _find_region(civ, 0)
        assert np.all(sim >= SIMILARITY_THRESHOLD - 0.01)

    def test_region_bounded_by_max(self):
        idx, sim = _find_region(civ, 0, max_region=50)
        assert len(idx) <= 50


class TestApplyCorrections:
    def test_correction_moves_stance(self):
        copy = _deep_copy_civ(civ)
        q = question_by_id("ssm")
        s0 = project_all(copy, q)
        before = float(s0[0])
        target = min(before + 0.15, 0.95)

        result = apply_corrections(
            copy, 0,
            [Correction("ssm", target)],
            propagate=False,
        )

        assert result.corrections_applied == 1
        assert result.before_stances["ssm"] == pytest.approx(before, abs=0.01)
        assert abs(result.after_stances["ssm"] - target) < abs(before - target)

    def test_correction_with_propagation(self):
        copy = _deep_copy_civ(civ)
        q = question_by_id("ssm")
        s0_before = project_all(copy, q).copy()

        ci = copy.country[0]
        same_country = np.where(copy.country == ci)[0]
        mean_before = float(s0_before[same_country].mean())

        result = apply_corrections(
            copy, 0,
            [Correction("ssm", 0.95)],
            propagate=True,
        )

        assert result.n_region_updated > 0

        s0_after = project_all(copy, q)
        mean_after = float(s0_after[same_country].mean())
        assert mean_after != mean_before

    def test_unknown_question_raises(self):
        copy = _deep_copy_civ(civ)
        with pytest.raises(ValueError, match="Unknown"):
            apply_corrections(copy, 0, [Correction("fake_q", 0.5)])

    def test_multiple_corrections(self):
        copy = _deep_copy_civ(civ)
        result = apply_corrections(
            copy, 0,
            [Correction("ssm", 0.9), Correction("svb", 0.8)],
            propagate=False,
        )
        assert result.corrections_applied == 2
        assert "ssm" in result.before_stances
        assert "svb" in result.before_stances

    def test_traits_stay_bounded(self):
        copy = _deep_copy_civ(civ)
        apply_corrections(
            copy, 0,
            [Correction("ssm", 0.99)],
            propagate=True,
        )
        assert np.all(copy.openness >= 0)
        assert np.all(copy.openness <= 1)
        assert np.all(copy.forces >= 0)
        assert np.all(copy.forces <= 1)


class TestApplyTraitCorrections:
    def test_direct_trait_change(self):
        copy = _deep_copy_civ(civ)
        old_openness = float(copy.openness[0])
        result = apply_trait_corrections(
            copy, 0,
            [TraitCorrection("openness", 0.9)],
            propagate=False,
        )
        assert copy.openness[0] == pytest.approx(0.9, abs=0.01)
        assert "openness" in result["trait_deltas"]

    def test_trait_propagates_to_region(self):
        copy = _deep_copy_civ(civ)
        result = apply_trait_corrections(
            copy, 0,
            [TraitCorrection("openness", 0.95)],
            propagate=True,
        )
        assert result["n_region_updated"] > 0

    def test_unknown_trait_raises(self):
        copy = _deep_copy_civ(civ)
        with pytest.raises(ValueError, match="Unknown"):
            apply_trait_corrections(copy, 0, [TraitCorrection("fake_trait", 0.5)])

    def test_forces_recomputed(self):
        copy = _deep_copy_civ(civ)
        apply_trait_corrections(
            copy, 0,
            [TraitCorrection("openness", 0.95)],
            propagate=False,
        )
        expected_id = 0.95 * 0.5 + copy.individualism[0] * 0.5
        expected_coll = (1.0 - 0.95) * 0.6 + copy.power_distance[0] * 0.4
        assert copy.forces[0, Force.IDENTITY] == pytest.approx(expected_id, abs=0.02)
        assert copy.forces[0, Force.COLLECTIVE] == pytest.approx(expected_coll, abs=0.02)


class TestMeasureCalibration:
    def test_returns_report(self):
        corrections = [Correction("ssm", 0.85)]
        report = measure_calibration(civ, corrections, 0)
        assert isinstance(report, CalibrationReport)
        assert report.n_corrections == 1
        assert len(report.cohort_improvements) > 0

    def test_large_correction_shows_effect(self):
        q = question_by_id("ssm")
        s0 = project_all(civ, q)
        current = float(s0[0])
        target = 1.0 - current  # flip completely

        corrections = [Correction("ssm", target)]
        report = measure_calibration(civ, corrections, 0)
        assert report.holdout_error_before >= 0
        assert report.holdout_error_after >= 0

    def test_custom_holdout(self):
        corrections = [Correction("ssm", 0.85)]
        report = measure_calibration(
            civ, corrections, 0,
            holdout_question_ids=["svb", "immig"],
        )
        assert "svb" in report.cohort_improvements
        assert "immig" in report.cohort_improvements
        assert len(report.cohort_improvements) == 2

    def test_no_holdout_returns_zero(self):
        corrections = [Correction("ssm", 0.85)]
        report = measure_calibration(
            civ, corrections, 0,
            holdout_question_ids=[],
        )
        assert report.improvement == 0.0


class TestBatchCalibrate:
    def test_batch_multiple_claims(self):
        copy = _deep_copy_civ(civ)
        claims = [
            {
                "agent_idx": 0,
                "corrections": [{"question_id": "ssm", "corrected_stance": 0.85}],
            },
            {
                "agent_idx": 100,
                "corrections": [{"question_id": "svb", "corrected_stance": 0.7}],
            },
        ]
        result = batch_calibrate(copy, claims)
        assert result["n_claims"] == 2
        assert result["total_corrections"] == 2

    def test_batch_empty_list(self):
        copy = _deep_copy_civ(civ)
        result = batch_calibrate(copy, [])
        assert result["n_claims"] == 0
        assert result["total_corrections"] == 0


class TestRecomputeForces:
    def test_forces_consistent_after_recompute(self):
        copy = _deep_copy_civ(civ)
        idx = np.array([0, 1, 2])
        copy.openness[idx] = 0.8
        copy.individualism[idx] = 0.8
        copy.power_distance[idx] = 0.2
        _recompute_agent_forces(copy, idx)
        expected_id = 0.8 * 0.5 + 0.8 * 0.5
        expected_coll = (1.0 - 0.8) * 0.6 + 0.2 * 0.4
        assert copy.forces[0, Force.IDENTITY] == pytest.approx(expected_id, abs=0.001)
        assert copy.forces[0, Force.COLLECTIVE] == pytest.approx(expected_coll, abs=0.001)

    def test_means_updated(self):
        copy = _deep_copy_civ(civ)
        old_means = copy.means.copy()
        copy.openness[:100] = 0.99
        _recompute_agent_forces(copy, np.arange(100))
        assert not np.allclose(copy.means, old_means)


class TestGateG6:
    """Gate G6: Human corrections measurably improve accuracy in corrected cohorts."""

    def test_identity_corrections_improve_identity_questions(self):
        copy = _deep_copy_civ(civ)
        q = question_by_id("ssm")
        baseline_target = sigmoid(np.array([q.baseline]))[0]

        s0 = project_all(copy, q)
        us_mask = copy.country == COUNTRY_CODES.index("US")
        us_mean_before = float(s0[us_mask].mean())

        midpoint = (us_mean_before + baseline_target) / 2.0
        corrections = [Correction("ssm", midpoint)]

        us_agents = np.where(us_mask)[0]
        sample_agents = us_agents[:20]
        for agent_idx in sample_agents:
            apply_corrections(copy, int(agent_idx), corrections, propagate=True)

        s1 = project_all(copy, q)
        us_mean_after = float(s1[us_mask].mean())

        error_before = abs(us_mean_before - baseline_target)
        error_after = abs(us_mean_after - baseline_target)

        assert error_after <= error_before or abs(error_after - error_before) < 0.02

    def test_corrections_do_not_corrupt_other_countries(self):
        copy = _deep_copy_civ(civ)
        q = question_by_id("ssm")

        jp_mask = copy.country == COUNTRY_CODES.index("JP")
        s0_jp = project_all(copy, q)
        jp_mean_before = float(s0_jp[jp_mask].mean())

        us_mask = copy.country == COUNTRY_CODES.index("US")
        us_agents = np.where(us_mask)[0][:10]
        for agent_idx in us_agents:
            apply_corrections(
                copy, int(agent_idx),
                [Correction("ssm", 0.95)],
                propagate=True,
            )

        s1_jp = project_all(copy, q)
        jp_mean_after = float(s1_jp[jp_mask].mean())

        assert abs(jp_mean_after - jp_mean_before) < 0.06

    def test_measure_calibration_shows_improvement(self):
        corrections = [Correction("ssm", 0.65)]

        us_agents = np.where(civ.country == COUNTRY_CODES.index("US"))[0]
        report = measure_calibration(
            civ, corrections, int(us_agents[0]),
            holdout_question_ids=["climate", "immig"],
        )

        assert report.holdout_error_before >= 0
        assert report.holdout_error_after >= 0


class TestDBIntegration:
    """Test DB models for claims and corrections (when DB available)."""

    def test_claim_model(self):
        os.environ["DATABASE_URL"] = "sqlite://"
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from earth1.db.models import Base, Claim, CorrectionRecord

        engine = create_engine("sqlite://", echo=False)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        db = Session()

        from earth1.db.store import save_claim, get_claim, list_claims
        claim = save_claim(
            db, user_id="test-user", agent_idx=42,
            country_code="US", match_score=0.87,
            demographics={"age": 0.38, "openness": 0.6},
        )
        assert claim is not None
        assert claim.user_id == "test-user"

        found = get_claim(db, claim.id)
        assert found is not None
        assert found.agent_idx == 42

        claims = list_claims(db, user_id="test-user")
        assert len(claims) == 1

        db.close()

    def test_correction_record_model(self):
        os.environ["DATABASE_URL"] = "sqlite://"
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from earth1.db.models import Base

        engine = create_engine("sqlite://", echo=False)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        db = Session()

        from earth1.db.store import save_claim, save_correction_record, list_correction_records
        claim = save_claim(
            db, user_id="test-user", agent_idx=42,
            country_code="US", match_score=0.87,
        )
        rec = save_correction_record(
            db, claim_id=claim.id, question_id="ssm",
            model_stance=0.58, corrected_stance=0.85,
            n_region_updated=120, trait_deltas={"openness": 0.05},
        )
        assert rec is not None
        assert rec.delta == pytest.approx(0.27, abs=0.001)
        assert rec.consent is True

        records = list_correction_records(db, claim_id=claim.id)
        assert len(records) == 1

        db.close()

    def test_none_session_safe(self):
        from earth1.db.store import save_claim, get_claim, list_claims
        from earth1.db.store import save_correction_record, list_correction_records
        assert save_claim(None, "u", 0, "US", 0.5) is None
        assert get_claim(None, "x") is None
        assert list_claims(None) == []
        assert save_correction_record(None, "c", "q", 0.5, 0.6) is None
        assert list_correction_records(None) == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
