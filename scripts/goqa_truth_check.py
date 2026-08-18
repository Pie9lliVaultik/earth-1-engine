"""Re-score GOQA under the polarity-corrected ground truth (VNF v2
audit: Q222/Q65 binarization errors found in our v1-derived truth).
Prints both so the revision is a diff, not a replacement."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.genesis import genesis
from earth1.benchmark import run_goqa_benchmark

os.environ.setdefault("EARTH1_PINNED_FOLDS", "data/cv_folds.json")


def main() -> None:
    civ = genesis(int(os.environ.get("GTC_POP", "200000")), 42)
    out = {}
    for name, path in (("v1", "data/benchmark/goqa_ground_truth_v1_archived.json"),
                       ("corrected",
                        "data/benchmark/goqa_ground_truth_corrected.json")):
        gt = json.load(open(path))
        r = run_goqa_benchmark(civ, gt, cv_seed=42)
        out[name] = {"cv": r.engine_cv_mae, "naive": r.naive_cv_mae,
                     "wins": r.engine_wins}
        print(f"TRUTH-{name}: CV {r.engine_cv_mae:.4f} "
              f"naive {r.naive_cv_mae:.4f} wins {r.engine_wins}/40",
              flush=True)
    json.dump(out, open("data/goqa_truth_check.json", "w"), indent=1)
    print("TRUTH-CHECK-DONE", flush=True)


if __name__ == "__main__":
    main()
