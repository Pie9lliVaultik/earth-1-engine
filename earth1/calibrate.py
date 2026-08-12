"""Force-signature calibration — can force anatomy predict real-world outcomes?

Hypothesis: if predictions with similar force signatures resolve similarly,
then we can build a calibration function:
    force_anatomy + engine_yes_pct → calibrated_probability

Test: leave-one-out cross-validation on resolved predictions.
If the calibrated output beats the raw engine, force signatures carry
predictive information beyond what the raw yes_pct provides.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from earth1.types import Civilization, Force, NUM_FORCES
from earth1.predictions import (
    RESOLVED_PREDICTIONS,
    ResolvedPrediction,
    run_prediction_validation,
    PredictionReport,
    PredictionResult,
)
from earth1.engine import run_question
from earth1.decompose import anatomize


@dataclass
class CalibrationResult:
    """Result of calibrating one held-out prediction."""
    id: str
    text: str
    actual_outcome: float
    raw_engine: float
    calibrated: float
    market_price: float
    raw_error: float
    calibrated_error: float
    market_error: float
    raw_brier: float
    calibrated_brier: float
    market_brier: float
    dominant_force: str
    nearest_neighbors: List[str]


@dataclass
class CalibrationReport:
    """Full leave-one-out calibration report."""
    n_predictions: int
    raw_mae: float
    calibrated_mae: float
    market_mae: float
    raw_brier: float
    calibrated_brier: float
    market_brier: float
    raw_direction: float
    calibrated_direction: float
    market_direction: float
    improvement_mae: float
    improvement_brier: float
    results: List[CalibrationResult]
    force_signal_strength: Dict[str, float]


def _force_vector(result: PredictionResult) -> np.ndarray:
    """Extract force anatomy as a vector in canonical order."""
    force_names = [f.name.lower() for f in Force]
    return np.array([result.force_anatomy.get(f, 0.0) for f in force_names])


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def calibrate_from_neighbors(
    held_out: PredictionResult,
    training: List[PredictionResult],
    predictions: List[ResolvedPrediction],
    k: int = 5,
    engine_weight: float = 0.3,
) -> Tuple[float, List[str]]:
    """Predict outcome using force-signature similarity to resolved predictions.

    Combines:
    1. Similarity-weighted average of training outcomes (force signal)
    2. Raw engine yes_pct (population signal)
    3. Dominant-force historical rate (force-type signal)

    Returns (calibrated_probability, neighbor_ids).
    """
    held_vec = _force_vector(held_out)
    pred_map = {p.id: p for p in predictions}

    similarities = []
    for t in training:
        t_vec = _force_vector(t)
        sim = _cosine_similarity(held_vec, t_vec)
        similarities.append((sim, t))

    similarities.sort(key=lambda x: -x[0])
    top_k = similarities[:k]
    neighbor_ids = [t.id for _, t in top_k]

    total_weight = sum(s for s, _ in top_k)
    if total_weight < 1e-12:
        neighbor_signal = 0.5
    else:
        neighbor_signal = sum(
            s * pred_map[t.id].actual_outcome for s, t in top_k
        ) / total_weight

    dom = held_out.dominant_force
    dom_outcomes = [pred_map[t.id].actual_outcome
                    for t in training if t.dominant_force == dom]
    if dom_outcomes:
        dom_rate = sum(dom_outcomes) / len(dom_outcomes)
    else:
        dom_rate = 0.5

    calibrated = (
        0.45 * neighbor_signal
        + engine_weight * held_out.engine_yes_pct
        + 0.25 * dom_rate
    )
    calibrated = max(0.01, min(0.99, calibrated))
    return calibrated, neighbor_ids


def run_calibration_test(
    civ: Civilization,
    report: Optional[PredictionReport] = None,
) -> CalibrationReport:
    """Leave-one-out cross-validation: does force calibration beat raw engine?"""
    if report is None:
        report = run_prediction_validation(civ)

    results_by_id = {r.id: r for r in report.results}
    pred_map = {p.id: p for p in RESOLVED_PREDICTIONS}
    all_results = report.results

    cal_results = []

    for i, held_out in enumerate(all_results):
        training = [r for j, r in enumerate(all_results) if j != i]
        pred = pred_map[held_out.id]

        calibrated, neighbors = calibrate_from_neighbors(
            held_out, training, RESOLVED_PREDICTIONS,
        )

        raw_err = abs(held_out.engine_yes_pct - pred.actual_outcome)
        cal_err = abs(calibrated - pred.actual_outcome)
        mkt_err = abs(pred.market_price - pred.actual_outcome)

        cal_results.append(CalibrationResult(
            id=held_out.id,
            text=held_out.text,
            actual_outcome=pred.actual_outcome,
            raw_engine=held_out.engine_yes_pct,
            calibrated=round(calibrated, 4),
            market_price=pred.market_price,
            raw_error=round(raw_err, 4),
            calibrated_error=round(cal_err, 4),
            market_error=round(mkt_err, 4),
            raw_brier=round((held_out.engine_yes_pct - pred.actual_outcome) ** 2, 4),
            calibrated_brier=round((calibrated - pred.actual_outcome) ** 2, 4),
            market_brier=round((pred.market_price - pred.actual_outcome) ** 2, 4),
            dominant_force=held_out.dominant_force,
            nearest_neighbors=neighbors,
        ))

    raw_mae = float(np.mean([r.raw_error for r in cal_results]))
    cal_mae = float(np.mean([r.calibrated_error for r in cal_results]))
    mkt_mae = float(np.mean([r.market_error for r in cal_results]))
    raw_brier = float(np.mean([r.raw_brier for r in cal_results]))
    cal_brier = float(np.mean([r.calibrated_brier for r in cal_results]))
    mkt_brier = float(np.mean([r.market_brier for r in cal_results]))

    n = len(cal_results)
    raw_dir = sum(1 for r in cal_results
                  if (r.raw_engine >= 0.5) == (r.actual_outcome >= 0.5)) / n
    cal_dir = sum(1 for r in cal_results
                  if (r.calibrated >= 0.5) == (r.actual_outcome >= 0.5)) / n
    mkt_dir = sum(1 for r in cal_results
                  if (r.market_price >= 0.5) == (r.actual_outcome >= 0.5)) / n

    force_names = [f.name.lower() for f in Force]
    force_signal = {}
    for fi, fname in enumerate(force_names):
        vals = [_force_vector(r)[fi] for r in all_results]
        outcomes = [pred_map[r.id].actual_outcome for r in all_results]
        if len(set(outcomes)) < 2 or np.std(vals) < 1e-8:
            force_signal[fname] = 0.0
        else:
            force_signal[fname] = round(float(abs(np.corrcoef(vals, outcomes)[0, 1])), 4)

    return CalibrationReport(
        n_predictions=n,
        raw_mae=round(raw_mae, 4),
        calibrated_mae=round(cal_mae, 4),
        market_mae=round(mkt_mae, 4),
        raw_brier=round(raw_brier, 4),
        calibrated_brier=round(cal_brier, 4),
        market_brier=round(mkt_brier, 4),
        raw_direction=round(raw_dir, 4),
        calibrated_direction=round(cal_dir, 4),
        market_direction=round(mkt_dir, 4),
        improvement_mae=round((raw_mae - cal_mae) / max(raw_mae, 1e-8), 4),
        improvement_brier=round((raw_brier - cal_brier) / max(raw_brier, 1e-8), 4),
        results=sorted(cal_results, key=lambda x: x.calibrated_error - x.raw_error),
        force_signal_strength=force_signal,
    )


def format_calibration_report(report: CalibrationReport) -> str:
    """Format calibration report as human-readable text."""
    lines = [
        "Force-Signature Calibration Test (Leave-One-Out)",
        "=" * 65,
        "",
        "  HYPOTHESIS: force anatomy predicts real-world outcomes",
        "  METHOD: for each prediction, train on the other N-1,",
        "          calibrate using force-signature similarity",
        "",
        f"  {'Metric':<24s} {'Raw Engine':>12s} {'Calibrated':>12s} {'Market':>12s}",
        f"  {'-'*60}",
        f"  {'MAE':<24s} {report.raw_mae:12.4f} {report.calibrated_mae:12.4f} {report.market_mae:12.4f}",
        f"  {'Brier Score':<24s} {report.raw_brier:12.4f} {report.calibrated_brier:12.4f} {report.market_brier:12.4f}",
        f"  {'Directional Accuracy':<24s} {report.raw_direction:11.0%} {report.calibrated_direction:11.0%} {report.market_direction:11.0%}",
        "",
    ]

    if report.improvement_brier > 0:
        lines.append(f"  RESULT: Calibration IMPROVES Brier by {report.improvement_brier:.1%}")
        lines.append(f"  RESULT: Calibration IMPROVES MAE by {report.improvement_mae:.1%}")
        lines.append("  VERDICT: Force signatures carry predictive signal.")
    elif report.improvement_brier > -0.05:
        lines.append(f"  RESULT: Calibration roughly MATCHES raw engine (Brier delta: {report.improvement_brier:.1%})")
        lines.append("  VERDICT: Inconclusive at this sample size.")
    else:
        lines.append(f"  RESULT: Calibration DEGRADES Brier by {-report.improvement_brier:.1%}")
        lines.append("  VERDICT: Insufficient data or overfitting.")

    lines.append("")
    lines.append(f"  {'ID':<24s} {'Raw':>5s} {'Cal':>5s} {'Mkt':>5s} {'Real':>5s} {'R-err':>6s} {'C-err':>6s} {'Better':>7s}")
    lines.append(f"  {'-'*68}")

    for r in report.results:
        better = "YES" if r.calibrated_error < r.raw_error - 0.01 else (
            "NO" if r.raw_error < r.calibrated_error - 0.01 else "SAME")
        lines.append(
            f"  {r.id:<24s} {r.raw_engine:5.2f} {r.calibrated:5.2f} "
            f"{r.market_price:5.2f} {r.actual_outcome:5.1f} "
            f"{r.raw_error:6.4f} {r.calibrated_error:6.4f} {better:>7s}"
        )

    lines.append("")
    lines.append("  Force-Outcome Correlation (|r|):")
    lines.append(f"  {'-'*40}")
    for fname, corr in sorted(report.force_signal_strength.items(), key=lambda x: -x[1]):
        bar = "#" * int(corr * 30)
        lines.append(f"  {fname:<14s} {corr:6.4f}  {bar}")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    from earth1.engine import build_civilization

    parser = argparse.ArgumentParser(description="Force-Signature Calibration Test")
    parser.add_argument("--pop", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print(f"Building civilization with {args.pop:,} agents...")
    civ = build_civilization(args.pop, seed=args.seed)

    print("Running prediction validation...")
    from earth1.predictions import run_prediction_validation
    report = run_prediction_validation(civ)

    print("Running leave-one-out calibration test...\n")
    cal = run_calibration_test(civ, report)
    print(format_calibration_report(cal))
