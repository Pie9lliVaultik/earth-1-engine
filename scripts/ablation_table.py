#!/usr/bin/env python3
"""The attribution table that ends every argument about what does what.

Four tiers, same recorded configuration (200K, seed 42), leakage flags
composable: census-only / +Hofstede / +Inglehart(full) — each scored
against the same naive baseline on GOQA LOO-country CV.
"""
import importlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

goqa = json.loads((ROOT / "data/benchmark/goqa_ground_truth.json").read_text())
os.environ.setdefault("EARTH1_GOQA_WORKERS", "40")

TIERS = [
    ("census_only",      {"EARTH1_NO_HOFSTEDE": "1", "EARTH1_NO_INGLEHART": "1"}),
    ("census_hofstede",  {"EARTH1_NO_HOFSTEDE": "0", "EARTH1_NO_INGLEHART": "1"}),
    ("full_inglehart",   {"EARTH1_NO_HOFSTEDE": "0", "EARTH1_NO_INGLEHART": "0"}),
]

results = {}
for label, flags in TIERS:
    os.environ.update(flags)
    import earth1.genesis
    importlib.reload(earth1.genesis)
    civ = earth1.genesis.genesis(200_000, seed=42)
    from earth1.benchmark import run_goqa_benchmark
    r = run_goqa_benchmark(civ, goqa)
    results[label] = {"engine_cv": r.engine_cv_mae, "naive_cv": r.naive_cv_mae,
                      "wins": r.engine_wins, "n": r.n_questions}
    print(f"{label:18s} engine CV {r.engine_cv_mae:.4f}  vs naive {r.naive_cv_mae:.4f}  "
          f"wins {r.engine_wins}/{r.n_questions}")

(ROOT / "data/ablation_table.json").write_text(json.dumps(results, indent=2))
print("ABLATION-TABLE-DONE")
