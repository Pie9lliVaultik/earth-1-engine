import os as _os  # LEGACY_COMPARISON_ONLY script: explicit opt-in
_os.environ.setdefault("EARTH1_LEGACY_COMPARISON", "1")
#!/usr/bin/env python3
"""The decisive experiment: GOQA with and without the Inglehart channel.

Reviewer finding: Inglehart coordinates derive from WVS answers to the
very items GOQA benchmarks. If the engine's margin over naive survives
without them (census + Hofstede only), the headline claim is leakage-
clean and STRONGER. If it collapses, we learned it first.

Same recorded configuration: 200K agents, seed 42, same harness.
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

results = {}
for label, flag in [("WITH_inglehart", "0"), ("NO_inglehart", "1")]:
    os.environ["EARTH1_NO_INGLEHART"] = flag
    import earth1.genesis
    importlib.reload(earth1.genesis)
    civ = earth1.genesis.genesis(200_000, seed=42)
    from earth1.legacy_benchmark import run_goqa_benchmark
    r = run_goqa_benchmark(civ, goqa)
    results[label] = {"engine_cv": r.engine_cv_mae, "naive_cv": r.naive_cv_mae,
                      "engine_insample": r.engine_mae,
                      "wins": r.engine_wins, "n": r.n_questions}
    print(f"{label}: engine CV {r.engine_cv_mae:.4f} vs naive {r.naive_cv_mae:.4f}, "
          f"wins {r.engine_wins}/{r.n_questions}")

(ROOT / "data/leakage_test.json").write_text(json.dumps(results, indent=2))
d = results["NO_inglehart"]["engine_cv"] - results["WITH_inglehart"]["engine_cv"]
survives = results["NO_inglehart"]["engine_cv"] < results["NO_inglehart"]["naive_cv"]
print(f"LEAKAGE-VERDICT: cost {d*100:+.2f}pp — "
      f"{'CLAIM SURVIVES leakage-clean' if survives else 'CLAIM COLLAPSES without Inglehart'}")
