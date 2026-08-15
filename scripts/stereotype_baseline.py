#!/usr/bin/env python3
"""Country-stereotype baseline for the GOQA benchmark (standing battery).

The strongest cheap competitor: predict country c on question q as
  pred[c,q] = global_mean_excluding_c(q) + country_offset_excluding_q(c)
where the offset is c's mean residual vs the global mean across the
OTHER 39 questions. Strictly leakage-free: y[c,q] itself is never used.

No engine involved — this is the bar any manifold must clear to claim
it adds information beyond "which countries answer high/low in general."
Appends to data/benchmark/goqa_results.json next to the engine entries.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
GOQA = ROOT / "data" / "benchmark" / "goqa_ground_truth.json"
OUT = ROOT / "data" / "benchmark" / "goqa_results.json"


def main():
    rows = json.loads(GOQA.read_text())
    questions = [r["id"] for r in rows]
    countries = sorted({c for r in rows for c in r["countries"]})
    q_idx = {q: i for i, q in enumerate(questions)}
    c_idx = {c: i for i, c in enumerate(countries)}

    y = np.full((len(countries), len(questions)), np.nan)
    for r in rows:
        for c, d in r["countries"].items():
            y[c_idx[c], q_idx[r["id"]]] = d["yes"]

    errs_stereo, errs_naive = [], []
    for qi in range(len(questions)):
        for ci in range(len(countries)):
            if np.isnan(y[ci, qi]):
                continue
            others_c = np.delete(y[:, qi], ci)
            qmean = float(np.nanmean(others_c))          # naive, no c
            row = np.delete(y[ci, :], qi)                 # c's other questions
            col_means = np.delete(np.nanmean(y, axis=0), qi)
            offset = float(np.nanmean(row - col_means))   # c's tendency, no q
            pred = np.clip(qmean + offset, 0.0, 1.0)
            errs_stereo.append(abs(pred - y[ci, qi]))
            errs_naive.append(abs(qmean - y[ci, qi]))

    mae_s = float(np.mean(errs_stereo))
    mae_n = float(np.mean(errs_naive))
    print(f"country-stereotype MAE: {mae_s:.4f}  ({len(errs_stereo)} pairs)")
    print(f"naive (global mean)   : {mae_n:.4f}")

    history = json.loads(OUT.read_text()) if OUT.exists() else []
    history.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "baseline": "country-stereotype",
        "stereotype_mae": round(mae_s, 4),
        "naive_mae": round(mae_n, 4),
        "n_pairs": len(errs_stereo),
        "note": "leakage-free lookup: global-mean-excl-c + offset-excl-q",
    })
    OUT.write_text(json.dumps(history, indent=2))
    print(f"recorded -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
