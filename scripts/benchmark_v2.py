#!/usr/bin/env python3
"""Manifold v2 benchmark — re-run the accepted Phase 0-2 GOQA numbers on
the age-fixed manifold (recalibrate-then-measure, same protocol that
produced the v1 accepted results: extended calibration, LOO-country CV).

Usage: python3 scripts/benchmark_v2.py [--pop 200000] [--seed 42]
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GOQA = ROOT / "data" / "benchmark" / "goqa_ground_truth.json"
OUT = ROOT / "data" / "benchmark" / "goqa_results.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pop", type=int, default=200_000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    from earth1.genesis import genesis
    from earth1.benchmark import run_goqa_benchmark, format_goqa

    goqa_data = json.loads(GOQA.read_text())
    print(f"Building v2 manifold: {args.pop:,} agents, seed {args.seed}...")
    civ = genesis(args.pop, args.seed)
    print("Running GOQA benchmark (40 questions x 66 countries, "
          "extended calibration + LOO-country CV)...")
    report = run_goqa_benchmark(civ, goqa_data)
    print(format_goqa(report))

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "manifold": "v2-age-fixed",
        "pop": args.pop,
        "seed": args.seed,
        "engine_mae": report.engine_mae,
        "naive_mae": report.naive_mae,
        "engine_cv_mae": report.engine_cv_mae,
        "naive_cv_mae": report.naive_cv_mae,
        "engine_wins": report.engine_wins,
        "naive_wins": report.naive_wins,
        "n_questions": report.n_questions,
        "n_country_pairs": report.n_country_pairs,
    }
    history = json.loads(OUT.read_text()) if OUT.exists() else []
    history.append(entry)
    OUT.write_text(json.dumps(history, indent=2))
    print(f"\nRecorded -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
