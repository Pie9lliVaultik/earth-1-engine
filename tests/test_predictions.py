import os as _os  # LEGACY_COMPARISON_ONLY test: explicit opt-in (tests may)
_os.environ.setdefault("EARTH1_LEGACY_COMPARISON", "1")
"""Tests for Build 27 — Prediction market validation."""
import sys
sys.path.insert(0, ".")

import numpy as np
import pytest

from earth1.legacy_predictions import (
    RESOLVED_PREDICTIONS,
    ResolvedPrediction,
    PredictionResult,
    PredictionReport,
    run_prediction_validation,
    format_prediction_report,
)
from earth1.types import Civilization, Force, NUM_FORCES
from earth1.engine import build_civilization
from earth1.questions import _w

POP = 5_000

@pytest.fixture(scope="module")
def civ():
    return build_civilization(POP, seed=42)


@pytest.fixture(scope="module")
def report(civ):
    return run_prediction_validation(civ)


class TestResolvedPredictions:
    def test_prediction_count(self):
        assert len(RESOLVED_PREDICTIONS) >= 20

    def test_ids_unique(self):
        ids = [p.id for p in RESOLVED_PREDICTIONS]
        assert len(ids) == len(set(ids))

    def test_all_have_outcomes(self):
        for p in RESOLVED_PREDICTIONS:
            assert p.actual_outcome in (0.0, 1.0), f"{p.id} has non-binary outcome"

    def test_all_have_market_prices(self):
        for p in RESOLVED_PREDICTIONS:
            assert 0.0 <= p.market_price <= 1.0, f"{p.id} market price out of range"

    def test_all_have_weights(self):
        for p in RESOLVED_PREDICTIONS:
            assert p.weights.shape == (NUM_FORCES,), f"{p.id} bad weight shape"
            assert np.any(p.weights != 0), f"{p.id} has zero weights"

    def test_to_question(self):
        q = RESOLVED_PREDICTIONS[0].to_question()
        assert q.id == RESOLVED_PREDICTIONS[0].id
        assert q.text == RESOLVED_PREDICTIONS[0].text


class TestPredictionValidation:
    def test_report_fields(self, report):
        assert report.n_predictions == len(RESOLVED_PREDICTIONS)
        assert report.population == 5_000
        assert report.engine_mae >= 0
        assert report.market_mae >= 0
        assert report.engine_brier >= 0
        assert report.market_brier >= 0
        assert report.engine_wins + report.market_wins + report.ties == report.n_predictions

    def test_results_count(self, report):
        assert len(report.results) == len(RESOLVED_PREDICTIONS)

    def test_engine_predictions_in_range(self, report):
        for r in report.results:
            assert 0.0 <= r.engine_yes_pct <= 1.0, f"{r.id} engine out of range"

    def test_errors_non_negative(self, report):
        for r in report.results:
            assert r.engine_error >= 0
            assert r.market_error >= 0

    def test_force_anatomy_present(self, report):
        for r in report.results:
            assert len(r.force_anatomy) == NUM_FORCES
            total = sum(r.force_anatomy.values())
            assert abs(total - 1.0) < 0.01, f"{r.id} anatomy doesn't sum to 1"

    def test_dominant_force_valid(self, report):
        force_names = {f.name.lower() for f in Force}
        for r in report.results:
            assert r.dominant_force in force_names, f"{r.id} invalid dominant"

    def test_conviction_in_range(self, report):
        for r in report.results:
            assert 0.0 <= r.conviction <= 1.0

    def test_fragility_in_range(self, report):
        for r in report.results:
            assert 0.0 <= r.fragility <= 1.0

    def test_camps_present(self, report):
        for r in report.results:
            assert "yes" in r.camps
            assert "no" in r.camps
            assert r.camps["yes"]["size"] + r.camps["no"]["size"] == POP

    def test_brier_score_bounded(self, report):
        assert report.engine_brier <= 1.0
        assert report.market_brier <= 1.0

    def test_engine_mae_reasonable(self, report):
        assert report.engine_mae < 0.6, f"Engine MAE {report.engine_mae} too high"


class TestForceAnalysis:
    def test_force_analysis_keys(self, report):
        force_names = {f.name.lower() for f in Force}
        assert set(report.force_analysis.keys()) == force_names

    def test_force_analysis_fields(self, report):
        for fname, stats in report.force_analysis.items():
            assert "mean_contribution" in stats
            assert "when_correct" in stats
            assert "when_wrong" in stats


class TestReportFormatting:
    def test_format_produces_string(self, report):
        text = format_prediction_report(report)
        assert isinstance(text, str)
        assert "Earth-1 Prediction Market Validation" in text

    def test_format_includes_metrics(self, report):
        text = format_prediction_report(report)
        assert "ENGINE MAE" in text
        assert "MARKET MAE" in text
        assert "Brier" in text

    def test_format_includes_all_predictions(self, report):
        text = format_prediction_report(report)
        for pred in RESOLVED_PREDICTIONS:
            assert pred.id in text


class TestSubsetValidation:
    def test_single_prediction(self, civ):
        subset = [RESOLVED_PREDICTIONS[0]]
        report = run_prediction_validation(civ, predictions=subset)
        assert report.n_predictions == 1
        assert len(report.results) == 1

    def test_custom_epsilon(self, civ):
        subset = RESOLVED_PREDICTIONS[:3]
        r1 = run_prediction_validation(civ, predictions=subset, epsilon=0.1)
        r2 = run_prediction_validation(civ, predictions=subset, epsilon=0.3)
        assert r1.engine_mae != r2.engine_mae or r1.engine_mae == 0.0


class TestDirectionalSanity:
    """Verify the engine's direction makes sense on easy questions."""

    def test_strong_no_outcomes(self, report):
        """Questions with actual_outcome=0 and low market price should have low engine yes_pct."""
        easy_nos = [r for r in report.results
                    if r.actual_outcome == 0.0 and r.market_price < 0.10]
        if easy_nos:
            avg_engine = np.mean([r.engine_yes_pct for r in easy_nos])
            assert avg_engine < 0.75, (
                f"Easy NO questions average engine yes_pct={avg_engine:.3f}, should be < 0.75"
            )

    def test_strong_yes_outcomes(self, report):
        """Questions with actual_outcome=1 and high market price should have higher engine yes_pct."""
        easy_yeses = [r for r in report.results
                      if r.actual_outcome == 1.0 and r.market_price > 0.80]
        if easy_yeses:
            avg_engine = np.mean([r.engine_yes_pct for r in easy_yeses])
            assert avg_engine > 0.3, (
                f"Easy YES questions average engine yes_pct={avg_engine:.3f}, should be > 0.3"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
