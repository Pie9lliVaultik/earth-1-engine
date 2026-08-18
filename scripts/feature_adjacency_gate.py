"""MANDATORY GATE — runs BEFORE any new genesis input is measured.

Origin (2026-08-18): religiosity was injected into genesis as
Q164 >= 6. Q164 IS a GOQA benchmark item. The injected feature
correlated +0.983 with its own target and >0.5 with 16 of 40 targets.
The resulting 10.59 -> 9.42pp "improvement" was the answer key, not
structure. Caught by an external reviewer AFTER it was committed —
this gate exists so the check happens BEFORE.

Rules (a candidate FAILS if any is true):
  R1  its source variable id appears as a GOQA item id
  R2  |corr| with ANY single target > MAX_SINGLE (0.50)
  R3  count of targets with |corr| > 0.35 exceeds MAX_BROAD (4)
Exit code 1 on any failure. The full table is always written to
data/feature_adjacency.json and committed with the result.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.benchmark import ISO3_TO_ISO2

MAX_SINGLE = 0.50
MAX_BROAD = 4
BROAD_LEVEL = 0.35

# candidate feature -> WVS source variable id (for R1)
SOURCES = {
    "religiosity": "Q164",
    "marital": "Q273",
    "employed": "Q279",
    "ideology": "Q240",
    "social_class": "Q287",
    "household_size": "Q270",
    "children": "Q274",
    "town_size": "G_TOWNSIZE",
    "immigrant": "Q263",
    "income_scale": "Q288",
}


def load_priors() -> dict:
    out = {}
    p = "data/religiosity_priors.json"
    if os.path.exists(p):
        out["religiosity"] = json.load(open(p))
    p = "data/joint_priors.json"
    if os.path.exists(p):
        out.update(json.load(open(p)))
    return out


def main() -> None:
    gt = json.load(open("data/benchmark/goqa_ground_truth.json"))
    target_ids = {q["id"] for q in gt}
    priors = load_priors()
    report, failed = {}, []
    for feat, pri in priors.items():
        src = SOURCES.get(feat, "?")
        corrs = {}
        for q in gt:
            xs, ys = [], []
            for iso3, d in q["countries"].items():
                i2 = ISO3_TO_ISO2.get(iso3)
                if i2 and i2 in pri:
                    xs.append(pri[i2]["marginal"])
                    ys.append(d["yes"])
            if len(xs) >= 20:
                c = float(np.corrcoef(xs, ys)[0, 1])
                if np.isfinite(c):
                    corrs[q["id"]] = round(c, 3)
        vals = list(corrs.values())
        mx = max(vals, key=abs) if vals else 0.0
        broad = sum(1 for v in vals if abs(v) > BROAD_LEVEL)
        r1 = src in target_ids
        r2 = abs(mx) > MAX_SINGLE
        r3 = broad > MAX_BROAD
        verdict = "BANNED" if (r1 or r2 or r3) else "clean"
        if verdict == "BANNED":
            failed.append(feat)
        report[feat] = {"source_var": src, "is_benchmark_item": r1,
                        "max_abs_corr": mx, "n_broad": broad,
                        "verdict": verdict, "corrs": corrs}
        print(f"  {feat:13s} src {src:5s} | max|corr| {abs(mx):.3f} "
              f"({max(corrs, key=lambda k: abs(corrs[k])) if corrs else '-'}) "
              f"| >0.35: {broad:2d} | item-on-benchmark: {r1} -> {verdict}",
              flush=True)
    json.dump({"rules": {"max_single": MAX_SINGLE, "broad_level": BROAD_LEVEL,
                         "max_broad": MAX_BROAD},
               "features": report}, open("data/feature_adjacency.json", "w"),
              indent=1)
    active = [f.strip() for f in
              os.environ.get("EARTH1_INJECT", "").split(",") if f.strip()]
    blocked = [f for f in active if f in failed]
    print(f"ADJACENCY-GATE: banned {failed or 'none'} | active set {active} "
          f"| blocked {blocked or 'none'}")
    if blocked or (failed and not active):
        sys.exit(1)


if __name__ == "__main__":
    main()
