import os as _os  # LEGACY_COMPARISON_ONLY test: explicit opt-in (tests may)
_os.environ.setdefault("EARTH1_LEGACY_COMPARISON", "1")
"""Tests for the benchmark harness."""
import sys
sys.path.insert(0, ".")

import json
import tempfile
import numpy as np
from pathlib import Path

from earth1.legacy_benchmark import (
    BENCHMARK_QUESTIONS, BenchmarkQuestion, run_benchmark,
    format_report, save_report, check_regression,
    run_benchmark_comparison, format_comparison,
)
from earth1.engine import build_civilization
from earth1.questions import _w

POP = 10_000
civ = build_civilization(POP, seed=42)


def test_benchmark_questions_valid():
    for bq in BENCHMARK_QUESTIONS:
        assert bq.weights.shape == (8,), f"{bq.id}: bad weights shape"
        assert bq.domain == "belief_causal", f"{bq.id}: benchmark must be belief_causal"
        assert len(bq.country_targets) >= 5, f"{bq.id}: need 5+ country targets"
        for code, val in bq.country_targets.items():
            assert 0 <= val <= 1, f"{bq.id}/{code}: target out of [0,1]"


def test_benchmark_ids_unique():
    ids = [bq.id for bq in BENCHMARK_QUESTIONS]
    assert len(ids) == len(set(ids)), "Duplicate benchmark question IDs"


def test_benchmark_count():
    assert len(BENCHMARK_QUESTIONS) >= 50


def test_run_benchmark():
    report = run_benchmark(civ)
    assert report.n_questions == len(BENCHMARK_QUESTIONS)
    assert report.n_country_pairs > 0
    assert report.overall_mae > 0
    assert report.duration_s > 0
    assert len(report.questions) == len(BENCHMARK_QUESTIONS)


def test_global_predictions_bounded():
    report = run_benchmark(civ)
    for q in report.questions:
        assert 0 <= q.predicted_global <= 1, f"{q.id}: prediction out of bounds"


def test_country_errors_reasonable():
    report = run_benchmark(civ)
    for q in report.questions:
        if q.country_mae is not None:
            assert q.country_mae < 0.8, f"{q.id}: country MAE suspiciously high"


def test_regime_classification():
    report = run_benchmark(civ)
    assert "anchored" in report.by_regime
    assert "partial" in report.by_regime
    assert "unanchored" in report.by_regime
    total = sum(r["count"] for r in report.by_regime.values())
    assert total <= len(BENCHMARK_QUESTIONS)


def test_format_report():
    report = run_benchmark(civ)
    text = format_report(report)
    assert "Benchmark Report" in text
    assert "OVERALL MAE" in text
    assert "Bible target" in text


def test_save_and_load_report():
    report = run_benchmark(civ)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    save_report(report, path)
    with open(path) as f:
        data = json.load(f)
    assert data["n_questions"] == report.n_questions
    assert data["overall_mae"] == report.overall_mae
    assert len(data["questions"]) == len(report.questions)
    Path(path).unlink()


def test_regression_no_baseline():
    report = run_benchmark(civ)
    result = check_regression(report, "/nonexistent/baseline.json")
    assert result["status"] == "no_baseline"


def test_regression_check():
    report = run_benchmark(civ)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        path = f.name
    save_report(report, path)
    result = check_regression(report, path, tolerance=0.01)
    assert result["status"] == "ok"
    assert result["overall_mae_delta"] == 0.0
    assert len(result["regressions"]) == 0
    Path(path).unlink()


def test_subset_benchmark():
    subset = BENCHMARK_QUESTIONS[:3]
    report = run_benchmark(civ, questions=subset)
    assert report.n_questions == 3


def test_force_dynamics_benchmark():
    subset = BENCHMARK_QUESTIONS[:5]
    report = run_benchmark(civ, questions=subset, use_force_dynamics=True)
    assert report.n_questions == 5
    for q in report.questions:
        assert 0 <= q.predicted_global <= 1, f"{q.id}: force dynamics prediction out of bounds"


def test_benchmark_comparison():
    subset = BENCHMARK_QUESTIONS[:5]
    comp = run_benchmark_comparison(civ, questions=subset)
    assert comp.scalar_report.n_questions == 5
    assert comp.force_report.n_questions == 5
    assert len(comp.per_question) == 5
    assert comp.max_divergence >= 0


def test_comparison_format():
    subset = BENCHMARK_QUESTIONS[:3]
    comp = run_benchmark_comparison(civ, questions=subset)
    text = format_comparison(comp)
    assert "Scalar vs Force Dynamics" in text
    assert "Delta" in text


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
