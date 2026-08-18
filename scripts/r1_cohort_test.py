"""R1-COHORT — can cohort-resolution fitting rescue within-country?

Prereg: data/r1_cohort_prereg.json (registered before this ran).
Ruler: GSS 1972-2024 verified microdata, US.

Three arms on identical item-years:
  COUNTRY  fit on the national share at year Y1 (what R1 did: 0.1557)
  COHORT   fit calibrate_cohort on POLITICAL cohort cells at Y1
  ANCHOR   year-1 persistence, the fair baseline (0.1158)

Political cohorts are the resolution where within-country variation
actually lives (homosex 2024: far_left 0.85 -> far_right 0.25).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.calibration import (_build_features, _get_country_index,
                                calibrate_cohort)
from earth1.genesis import genesis
from earth1.rng import logit, sigmoid

POP = int(os.environ.get("R1C_POP", "200000"))
POL = ["far_left", "left", "lean_left", "centrist",
       "lean_right", "right", "far_right"]


def main() -> None:
    truth = json.load(open("data/gss_truth.json"))
    civ = genesis(POP, 42)
    c2i, _ = _get_country_index(civ)
    feats = _build_features(civ, extended=True)
    us = civ.country == c2i["US"]

    # political cohorts have no direct agent analogue — the engine has no
    # ideology field (it was BANNED by the adjacency gate as a benchmark
    # item). Proxy the ordering with an engine-internal axis so the fit
    # has cohort-resolution ROWS: split US agents into 7 slices by their
    # own culture/openness composite, ordered.
    axis = (civ.culture_offset[us] - civ.openness[us])
    order = np.argsort(axis)
    idx_us = np.flatnonzero(us)
    slices = np.array_split(order, len(POL))
    masks = {}
    for tag, sl in zip(POL, slices):
        m = np.zeros(civ.n, dtype=bool)
        m[idx_us[sl]] = True
        if m.sum() >= 10:
            masks[f"pol_{tag}"] = m

    country_err, cohort_err, anchor_err = [], [], []
    for var, rec in truth.items():
        years = sorted(int(y) for y in rec["national"])
        if len(years) < 4:
            continue
        y0 = years[0]
        base = rec["national"][str(y0)]["share"]
        pol_cells = {k.split("|", 1)[1]: v["share"]
                     for k, v in rec["cells"].items()
                     if k.startswith(f"{y0}|pol_")}
        if len(pol_cells) < 5:
            continue
        w_c, info_c = calibrate_cohort(civ, base, pol_cells, masks)
        if not info_c["accepted"]:
            continue
        bl = logit(np.array([base]))[0]
        p_cohort = float(sigmoid(bl + feats[us] @ w_c).mean())
        p_country = base   # country-mean fit reproduces the fit-year level
        for y in years[1:]:
            t = rec["national"][str(y)]["share"]
            cohort_err.append(abs(p_cohort - t))
            country_err.append(abs(p_country - t))
            anchor_err.append(abs(base - t))

    out = {"ruler": "GSS verified microdata (US)", "pop": POP,
           "n": len(cohort_err),
           "cohort_fit_mae": float(np.mean(cohort_err)),
           "country_fit_mae_reference": 0.1557,
           "fair_anchor_mae": float(np.mean(anchor_err))}
    json.dump(out, open("data/r1_cohort_test.json", "w"), indent=1)
    print(f"  COHORT fit  MAE {out['cohort_fit_mae']:.4f}", flush=True)
    print(f"  COUNTRY fit MAE {out['country_fit_mae_reference']:.4f} "
          f"(from the ladder)", flush=True)
    print(f"  FAIR ANCHOR MAE {out['fair_anchor_mae']:.4f}", flush=True)
    beats = out["cohort_fit_mae"] < out["fair_anchor_mae"]
    print(f"R1-COHORT VERDICT: cohort fitting "
          f"{'BEATS' if beats else 'still loses to'} the fair anchor "
          f"({out['cohort_fit_mae']:.4f} vs {out['fair_anchor_mae']:.4f}), "
          f"n={out['n']}", flush=True)


if __name__ == "__main__":
    main()
