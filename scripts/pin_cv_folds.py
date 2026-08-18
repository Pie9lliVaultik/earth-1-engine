"""F2 fix: pin the GOQA CV fold partitions once, forever.

Generates data/cv_folds.json from the reference configuration (200K,
genesis seed 42) for cv_seeds 42/7/13, plus the pinned eligible
country set. Every future rung loads these via EARTH1_PINNED_FOLDS so
scale comparisons are made on IDENTICAL partitions and reported as
mean +/- spread over the three seeds.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.benchmark import _goqa_prepare_tasks
from earth1.calibration import _get_country_index
from earth1.genesis import genesis

REF_POP = int(os.environ.get("PIN_POP", "200000"))
CV_SEEDS = (42, 7, 13)


def main() -> None:
    civ = genesis(REF_POP, 42)
    code_to_idx, country_codes = _get_country_index(civ)
    gt = json.load(open("data/benchmark/goqa_ground_truth.json"))
    folds = {}
    for s in CV_SEEDS:
        tasks = _goqa_prepare_tasks(civ, gt, set(country_codes), 5, s)
        folds[str(s)] = {t["id"]: t["test_codes"] for t in tasks
                         if t["test_codes"] is not None}
    out = {"reference_pop": REF_POP, "genesis_seed": 42,
           "cv_holdout": 5, "cv_seeds": list(CV_SEEDS),
           "eligible_countries": sorted(country_codes),
           "folds": folds}
    json.dump(out, open("data/cv_folds.json", "w"), indent=1)
    n = sum(len(v) for v in folds.values())
    print(f"PINNED: {len(folds)} seeds, {n} question-folds, "
          f"{len(country_codes)} countries")


if __name__ == "__main__":
    main()
