"""Benchmark harness — GOQA-style regression suite with MAE tracking.

Runs a battery of questions with known survey ground truth against the engine,
computes MAE globally and per-country, classifies accuracy by regime, and
detects regressions against a saved baseline.

Bible §17 gate: MAE ≤ 0.221 on calibrated questions.
Bible §36 regimes: calibrated (≥0.85), transitional (0.65-0.85), forward-estimate (<0.65).
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from earth1.types import Civilization, Question, Force, NUM_FORCES, FORCE_NAMES
from earth1.engine import run_question, run_segment, build_civilization
from earth1.questions import _w


@dataclass
class BenchmarkQuestion:
    """A question with known survey ground truth."""
    id: str
    text: str
    domain: str
    baseline: float
    weights: np.ndarray
    lens: str
    global_target: Optional[float] = None
    country_targets: Dict[str, float] = field(default_factory=dict)

    def to_question(self) -> Question:
        return Question(
            id=self.id, text=self.text, domain=self.domain,
            baseline=self.baseline, weights=self.weights, lens=self.lens,
        )


@dataclass
class QuestionResult:
    id: str
    text: str
    lens: str
    predicted_global: float
    target_global: Optional[float]
    global_error: Optional[float]
    dominant: str
    country_results: List[Dict]
    country_mae: Optional[float]


@dataclass
class BenchmarkReport:
    timestamp: str
    population: int
    seed: int
    n_questions: int
    n_country_pairs: int
    global_mae: Optional[float]
    country_mae: Optional[float]
    overall_mae: float
    by_regime: Dict[str, Dict]
    questions: List[QuestionResult]
    duration_s: float


# ---------------------------------------------------------------------------
# Ground truth data — real survey results from WVS Wave 7, Pew, GSS
#
# Each entry: known yes_pct (fraction supporting/agreeing) by country.
# Sources cited per question.  Countries not in survey are omitted.
# ---------------------------------------------------------------------------

BENCHMARK_QUESTIONS: List[BenchmarkQuestion] = [
    # --- 1. Same-sex marriage (WVS7 V204 "Homosexuality justifiable" + Pew 2023) ---
    BenchmarkQuestion(
        id="b_ssm", text="Do people support same-sex marriage?",
        domain="belief_causal", baseline=0.35,
        weights=_w(identity=3.4, culture=-2.2, collective=-1.2, experience=-1.6),
        lens="culture",
        global_target=0.55,
        country_targets={
            "US": 0.71, "GB": 0.77, "DE": 0.75, "FR": 0.77,
            "BR": 0.52, "MX": 0.55, "JP": 0.65,
            "IN": 0.22, "NG": 0.07,
        },
    ),
    # --- 2. Immigration restriction (Pew Global Attitudes 2018-2022) ---
    BenchmarkQuestion(
        id="b_immig", text="Should immigration be more restricted?",
        domain="belief_causal", baseline=-0.1,
        weights=_w(fear=2.8, identity=-2.6, culture=1.8, economics=1.4),
        lens="policy",
        global_target=0.48,
        country_targets={
            "US": 0.48, "GB": 0.52, "DE": 0.46, "FR": 0.56,
            "BR": 0.44, "MX": 0.38, "JP": 0.66,
            "IN": 0.42, "NG": 0.35,
        },
    ),
    # --- 3. Climate urgency (Pew 2021 "Climate as top threat") ---
    BenchmarkQuestion(
        id="b_climate", text="Is urgent climate action a priority?",
        domain="belief_causal", baseline=0.3,
        weights=_w(identity=2.4, experience=-2.0, culture=1.2, economics=-1.0),
        lens="policy",
        global_target=0.62,
        country_targets={
            "US": 0.54, "GB": 0.70, "DE": 0.71, "FR": 0.83,
            "BR": 0.72, "MX": 0.69, "JP": 0.75,
            "IN": 0.56, "NG": 0.48,
        },
    ),
    # --- 4. Trust in government (WVS7 V115 + Pew) ---
    BenchmarkQuestion(
        id="b_gov_trust", text="Do people trust their national government?",
        domain="belief_causal", baseline=-0.25,
        weights=_w(economics=2.6, identity=1.4, fear=-1.2, collective=1.0),
        lens="politics",
        global_target=0.38,
        country_targets={
            "US": 0.20, "GB": 0.35, "DE": 0.45, "FR": 0.28,
            "BR": 0.22, "MX": 0.21, "JP": 0.28,
            "IN": 0.77, "NG": 0.25,
        },
    ),
    # --- 5. Democracy best system (WVS7 V141 "democratic system good") ---
    BenchmarkQuestion(
        id="b_democracy", text="Is democracy the best system of government?",
        domain="belief_causal", baseline=1.2,
        weights=_w(identity=2.0, culture=-0.8, experience=1.4, collective=-1.0),
        lens="politics",
        global_target=0.78,
        country_targets={
            "US": 0.85, "GB": 0.87, "DE": 0.92, "FR": 0.84,
            "BR": 0.72, "MX": 0.68, "JP": 0.82,
            "IN": 0.75, "NG": 0.68,
        },
    ),
    # --- 6. Religion important in life (WVS7 V152) ---
    BenchmarkQuestion(
        id="b_religion", text="Is religion important in your daily life?",
        domain="belief_causal", baseline=0.2,
        weights=_w(identity=2.8, culture=2.4, collective=1.0, experience=0.6, temperament=-1.6),
        lens="culture",
        global_target=0.62,
        country_targets={
            "US": 0.65, "GB": 0.27, "DE": 0.25, "FR": 0.21,
            "BR": 0.86, "MX": 0.78, "JP": 0.13,
            "IN": 0.92, "NG": 0.96,
        },
    ),
    # --- 7. Gender equality progress (Pew 2019 "men have better life") ---
    BenchmarkQuestion(
        id="b_gender_eq", text="Do men generally have a better life than women in your country?",
        domain="belief_causal", baseline=0.1,
        weights=_w(identity=1.8, culture=-2.6, experience=1.2, economics=0.8, temperament=0.6),
        lens="culture",
        global_target=0.52,
        country_targets={
            "US": 0.56, "GB": 0.54, "DE": 0.52, "FR": 0.62,
            "BR": 0.58, "MX": 0.60, "JP": 0.64,
            "IN": 0.48, "NG": 0.42,
        },
    ),
    # --- 8. Technology makes life better (WVS7 V192) ---
    BenchmarkQuestion(
        id="b_tech_good", text="Does technology generally make life better?",
        domain="belief_causal", baseline=0.8,
        weights=_w(desire=1.6, economics=1.2, fear=-1.4, experience=-0.8, temperament=1.0),
        lens="technology",
        global_target=0.72,
        country_targets={
            "US": 0.72, "GB": 0.68, "DE": 0.65, "FR": 0.62,
            "BR": 0.78, "MX": 0.76, "JP": 0.63,
            "IN": 0.85, "NG": 0.82,
        },
    ),
    # --- 9. Abortion access (WVS7 V205 "abortion justifiable" + Pew) ---
    BenchmarkQuestion(
        id="b_abortion", text="Should abortion be legal in most cases?",
        domain="belief_causal", baseline=0.0,
        weights=_w(identity=3.0, culture=-2.8, experience=-1.0, collective=-0.8, temperament=0.6),
        lens="culture",
        global_target=0.52,
        country_targets={
            "US": 0.61, "GB": 0.76, "DE": 0.72, "FR": 0.80,
            "BR": 0.38, "MX": 0.48, "JP": 0.68,
            "IN": 0.36, "NG": 0.12,
        },
    ),
    # --- 10. Death penalty (WVS7 V198 + Pew) ---
    BenchmarkQuestion(
        id="b_death_penalty", text="Do people favor the death penalty for serious crimes?",
        domain="belief_causal", baseline=0.15,
        weights=_w(fear=2.2, identity=-1.8, culture=1.6, collective=1.2, temperament=-1.4),
        lens="policy",
        global_target=0.55,
        country_targets={
            "US": 0.55, "GB": 0.48, "DE": 0.32, "FR": 0.44,
            "BR": 0.57, "MX": 0.52, "JP": 0.80,
            "IN": 0.68, "NG": 0.74,
        },
    ),
    # --- 11. Economic system fairness (Pew 2019 "econ system unfair") ---
    BenchmarkQuestion(
        id="b_econ_unfair", text="Is the economic system in your country unfair to most people?",
        domain="belief_causal", baseline=0.3,
        weights=_w(economics=-2.8, identity=0.8, collective=1.4, fear=1.0, desire=-0.6),
        lens="economics",
        global_target=0.62,
        country_targets={
            "US": 0.58, "GB": 0.62, "DE": 0.48, "FR": 0.72,
            "BR": 0.76, "MX": 0.74, "JP": 0.58,
            "IN": 0.56, "NG": 0.70,
        },
    ),
    # --- 12. Children need both parents (WVS7 V47 + Pew) ---
    BenchmarkQuestion(
        id="b_two_parent", text="Do children need both a mother and father to grow up happily?",
        domain="belief_causal", baseline=0.6,
        weights=_w(culture=2.6, identity=1.6, collective=1.8, experience=0.8, temperament=-1.0),
        lens="family",
        global_target=0.68,
        country_targets={
            "US": 0.56, "GB": 0.48, "DE": 0.42, "FR": 0.38,
            "BR": 0.72, "MX": 0.74, "JP": 0.62,
            "IN": 0.88, "NG": 0.92,
        },
    ),
    # --- 13. Trust in news media (Pew 2022 + WVS7 V120) ---
    BenchmarkQuestion(
        id="b_media_trust", text="Do people trust the news media?",
        domain="belief_causal", baseline=-0.4,
        weights=_w(identity=1.6, fear=-1.2, collective=1.8, economics=0.6, temperament=-0.8),
        lens="media",
        global_target=0.38,
        country_targets={
            "US": 0.26, "GB": 0.36, "DE": 0.50, "FR": 0.30,
            "BR": 0.42, "MX": 0.38, "JP": 0.32,
            "IN": 0.52, "NG": 0.42,
        },
    ),
    # --- 14. Satisfied with life (WVS7 V23 "satisfied with life" 7+/10) ---
    BenchmarkQuestion(
        id="b_life_sat", text="Are people generally satisfied with their life?",
        domain="belief_causal", baseline=0.5,
        weights=_w(economics=2.0, desire=-1.4, fear=-1.0, experience=0.6, temperament=1.2),
        lens="wellbeing",
        global_target=0.58,
        country_targets={
            "US": 0.72, "GB": 0.68, "DE": 0.70, "FR": 0.62,
            "BR": 0.55, "MX": 0.72, "JP": 0.52,
            "IN": 0.42, "NG": 0.38,
        },
    ),
    # --- 15. China viewed favorably (Pew 2023 Global Views of China) ---
    BenchmarkQuestion(
        id="b_china_fav", text="Do people have a favorable view of China?",
        domain="belief_causal", baseline=-0.3,
        weights=_w(economics=1.8, fear=-1.4, identity=-1.0, collective=0.8, culture=0.6),
        lens="geopolitics",
        global_target=0.34,
        country_targets={
            "US": 0.15, "GB": 0.18, "DE": 0.21, "FR": 0.16,
            "BR": 0.48, "MX": 0.42, "JP": 0.09,
            "IN": 0.32, "NG": 0.72,
        },
    ),
    # --- 16. US viewed favorably (Pew 2023) ---
    BenchmarkQuestion(
        id="b_us_fav", text="Do people have a favorable view of the United States?",
        domain="belief_causal", baseline=0.4,
        weights=_w(economics=1.4, identity=0.8, culture=-0.6, collective=0.4, fear=-0.4),
        lens="geopolitics",
        global_target=0.59,
        country_targets={
            "GB": 0.69, "DE": 0.54, "FR": 0.52,
            "BR": 0.62, "MX": 0.52, "JP": 0.73,
            "IN": 0.65, "NG": 0.78,
        },
    ),
    # --- 17. Worry about nuclear weapons (Pew 2022) ---
    BenchmarkQuestion(
        id="b_nukes", text="Are people worried about the threat of nuclear weapons?",
        domain="belief_causal", baseline=0.6,
        weights=_w(fear=3.0, collective=1.2, identity=-0.6, economics=-0.4),
        lens="security",
        global_target=0.72,
        country_targets={
            "US": 0.73, "GB": 0.68, "DE": 0.70, "FR": 0.68,
            "BR": 0.62, "MX": 0.58, "JP": 0.88,
            "IN": 0.72, "NG": 0.52,
        },
    ),
    # --- 18. Nationalism — country is better than most (WVS7 V211) ---
    BenchmarkQuestion(
        id="b_natl_pride", text="Is your country better than most other countries?",
        domain="belief_causal", baseline=0.3,
        weights=_w(identity=2.8, culture=1.8, collective=0.8, experience=0.4, economics=-0.6),
        lens="identity",
        global_target=0.52,
        country_targets={
            "US": 0.68, "GB": 0.55, "DE": 0.42, "FR": 0.52,
            "BR": 0.48, "MX": 0.62, "JP": 0.55,
            "IN": 0.68, "NG": 0.72,
        },
    ),
    # --- 19. Worry about AI (Pew 2023 "concerned about AI") ---
    BenchmarkQuestion(
        id="b_ai_concern", text="Are people concerned about artificial intelligence?",
        domain="belief_causal", baseline=0.2,
        weights=_w(fear=2.6, experience=1.4, identity=-0.8, temperament=-1.2, economics=0.6),
        lens="technology",
        global_target=0.55,
        country_targets={
            "US": 0.52, "GB": 0.58, "DE": 0.62, "FR": 0.64,
            "BR": 0.48, "MX": 0.44, "JP": 0.68,
            "IN": 0.42, "NG": 0.38,
        },
    ),
    # --- 20. Wealth gap too large (Pew 2020 + WVS7) ---
    BenchmarkQuestion(
        id="b_inequality", text="Is the gap between rich and poor too large?",
        domain="belief_causal", baseline=0.8,
        weights=_w(economics=-2.4, identity=0.6, collective=1.6, desire=-0.8, fear=0.6),
        lens="economics",
        global_target=0.74,
        country_targets={
            "US": 0.65, "GB": 0.72, "DE": 0.68, "FR": 0.78,
            "BR": 0.82, "MX": 0.80, "JP": 0.72,
            "IN": 0.68, "NG": 0.76,
        },
    ),
]


def run_benchmark(
    civ: Civilization,
    questions: Optional[List[BenchmarkQuestion]] = None,
    epsilon: float = 0.18,
    layers: int = 8,
) -> BenchmarkReport:
    """Run full benchmark suite against the civilization."""
    if questions is None:
        questions = BENCHMARK_QUESTIONS

    t0 = time.time()
    results = []
    all_global_errors = []
    all_country_errors = []

    from earth1.population import COUNTRY_CODES

    for bq in questions:
        q = bq.to_question()
        r = run_question(q, civ, epsilon=epsilon, layers=layers)

        country_results = []
        country_errors = []

        if bq.country_targets:
            cells = run_segment(q, civ, "country", epsilon=epsilon, layers=layers)
            cell_map = {c.label: c.yes_pct for c in cells}

            for code, target in bq.country_targets.items():
                predicted = cell_map.get(code)
                if predicted is not None:
                    err = abs(predicted - target)
                    country_errors.append(err)
                    all_country_errors.append(err)
                    country_results.append({
                        "country": code,
                        "predicted": round(predicted, 4),
                        "target": target,
                        "error": round(err, 4),
                    })

        global_error = None
        if bq.global_target is not None:
            global_error = abs(r.yes_pct - bq.global_target)
            all_global_errors.append(global_error)

        results.append(QuestionResult(
            id=bq.id,
            text=bq.text,
            lens=bq.lens,
            predicted_global=round(r.yes_pct, 4),
            target_global=bq.global_target,
            global_error=round(global_error, 4) if global_error is not None else None,
            dominant=r.dominant.name.lower(),
            country_results=country_results,
            country_mae=round(np.mean(country_errors), 4) if country_errors else None,
        ))

    global_mae = float(np.mean(all_global_errors)) if all_global_errors else None
    country_mae = float(np.mean(all_country_errors)) if all_country_errors else None

    all_errors = all_global_errors + all_country_errors
    overall_mae = float(np.mean(all_errors)) if all_errors else 0.0

    by_regime = _classify_regimes(results)

    dt = time.time() - t0

    return BenchmarkReport(
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        population=civ.n,
        seed=civ.seed,
        n_questions=len(results),
        n_country_pairs=len(all_country_errors),
        global_mae=round(global_mae, 4) if global_mae is not None else None,
        country_mae=round(country_mae, 4) if country_mae is not None else None,
        overall_mae=round(overall_mae, 4),
        by_regime=by_regime,
        questions=results,
        duration_s=round(dt, 2),
    )


def _classify_regimes(results: List[QuestionResult]) -> Dict[str, Dict]:
    """Group results into bible §36 accuracy regimes."""
    regimes = {
        "calibrated": {"threshold": 0.85, "questions": [], "mae": None},
        "transitional": {"threshold": 0.65, "questions": [], "mae": None},
        "forward_estimate": {"threshold": 0.0, "questions": [], "mae": None},
    }

    for r in results:
        if r.country_mae is None:
            continue
        similarity = 1.0 - r.country_mae
        if similarity >= 0.85:
            regimes["calibrated"]["questions"].append(r.id)
        elif similarity >= 0.65:
            regimes["transitional"]["questions"].append(r.id)
        else:
            regimes["forward_estimate"]["questions"].append(r.id)

    for regime in regimes.values():
        ids = set(regime["questions"])
        errors = []
        for r in results:
            if r.id in ids and r.country_mae is not None:
                errors.append(r.country_mae)
        regime["count"] = len(regime["questions"])
        regime["mae"] = round(float(np.mean(errors)), 4) if errors else None

    return regimes


def format_report(report: BenchmarkReport) -> str:
    """Format benchmark report as human-readable text."""
    lines = [
        f"Earth-1 Benchmark Report",
        f"{'='*60}",
        f"  Population: {report.population:,}  |  Seed: {report.seed}",
        f"  Questions:  {report.n_questions}  |  Country pairs: {report.n_country_pairs}",
        f"  Duration:   {report.duration_s}s",
        f"",
        f"  OVERALL MAE:  {report.overall_mae:.4f}",
        f"  Global MAE:   {report.global_mae:.4f}" if report.global_mae else "",
        f"  Country MAE:  {report.country_mae:.4f}" if report.country_mae else "",
        f"  Bible target: 0.2210  {'PASS' if report.overall_mae <= 0.221 else 'FAIL'}",
        f"",
        f"  By regime (bible s36):",
    ]

    for name, regime in report.by_regime.items():
        mae_str = f"MAE={regime['mae']:.4f}" if regime['mae'] is not None else "n/a"
        lines.append(f"    {name:20s}: {regime['count']:2d} questions  {mae_str}")

    lines.append(f"\n  Per-question breakdown:")
    lines.append(f"  {'ID':<20s} {'Pred':>6s} {'Tgt':>6s} {'Err':>6s} {'C-MAE':>6s} {'Dom':<12s}")
    lines.append(f"  {'-'*62}")

    for q in sorted(report.questions, key=lambda x: -(x.country_mae or 0)):
        tgt = f"{q.target_global:.2f}" if q.target_global is not None else "  -  "
        err = f"{q.global_error:.4f}" if q.global_error is not None else "  -  "
        cmae = f"{q.country_mae:.4f}" if q.country_mae is not None else "  -  "
        lines.append(f"  {q.id:<20s} {q.predicted_global:6.2f} {tgt:>6s} {err:>6s} {cmae:>6s} {q.dominant:<12s}")

    return "\n".join(lines)


def save_report(report: BenchmarkReport, path: str | Path) -> None:
    """Save benchmark report as JSON for regression tracking."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "timestamp": report.timestamp,
        "population": report.population,
        "seed": report.seed,
        "n_questions": report.n_questions,
        "n_country_pairs": report.n_country_pairs,
        "global_mae": report.global_mae,
        "country_mae": report.country_mae,
        "overall_mae": report.overall_mae,
        "by_regime": report.by_regime,
        "duration_s": report.duration_s,
        "questions": [
            {
                "id": q.id,
                "text": q.text,
                "predicted_global": q.predicted_global,
                "target_global": q.target_global,
                "global_error": q.global_error,
                "dominant": q.dominant,
                "country_mae": q.country_mae,
                "country_results": q.country_results,
            }
            for q in report.questions
        ],
    }

    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def check_regression(
    current: BenchmarkReport,
    baseline_path: str | Path,
    tolerance: float = 0.01,
) -> Dict:
    """Compare current run against a saved baseline. Flag regressions."""
    path = Path(baseline_path)
    if not path.exists():
        return {"status": "no_baseline", "message": "No baseline to compare against."}

    with open(path) as f:
        baseline = json.load(f)

    base_mae = baseline.get("overall_mae", 0)
    diff = current.overall_mae - base_mae

    base_questions = {q["id"]: q for q in baseline.get("questions", [])}
    regressions = []
    improvements = []

    for q in current.questions:
        if q.id in base_questions:
            bq = base_questions[q.id]
            if q.country_mae is not None and bq.get("country_mae") is not None:
                delta = q.country_mae - bq["country_mae"]
                if delta > tolerance:
                    regressions.append({
                        "id": q.id, "was": bq["country_mae"],
                        "now": q.country_mae, "delta": round(delta, 4),
                    })
                elif delta < -tolerance:
                    improvements.append({
                        "id": q.id, "was": bq["country_mae"],
                        "now": q.country_mae, "delta": round(delta, 4),
                    })

    return {
        "status": "regression" if regressions else "ok",
        "overall_mae_delta": round(diff, 4),
        "baseline_mae": base_mae,
        "current_mae": current.overall_mae,
        "regressions": regressions,
        "improvements": improvements,
    }


def run_cli():
    """CLI entry point for running benchmarks."""
    import argparse
    parser = argparse.ArgumentParser(description="Earth-1 Benchmark Suite")
    parser.add_argument("--pop", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--save", type=str, default=None, help="Save JSON report to path")
    parser.add_argument("--baseline", type=str, default=None, help="Compare against baseline JSON")
    args = parser.parse_args()

    print(f"Building civilization ({args.pop:,} agents, seed={args.seed})...")
    civ = build_civilization(args.pop, args.seed)

    print(f"Running {len(BENCHMARK_QUESTIONS)} benchmark questions...")
    report = run_benchmark(civ)

    print(format_report(report))

    if args.save:
        save_report(report, args.save)
        print(f"\nReport saved to {args.save}")

    if args.baseline:
        regression = check_regression(report, args.baseline)
        print(f"\nRegression check: {regression['status']}")
        if regression.get("regressions"):
            for r in regression["regressions"]:
                print(f"  REGRESSION: {r['id']} ({r['was']:.4f} -> {r['now']:.4f}, +{r['delta']:.4f})")
        if regression.get("improvements"):
            for r in regression["improvements"]:
                print(f"  IMPROVED:   {r['id']} ({r['was']:.4f} -> {r['now']:.4f}, {r['delta']:.4f})")


if __name__ == "__main__":
    run_cli()
