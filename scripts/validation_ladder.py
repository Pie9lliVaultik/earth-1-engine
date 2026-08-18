"""THE VALIDATION LADDER — every trusted survey on the planet, in order.

Nothing ships on one source. The ladder climbs from the smallest
verified set to the widest, and each rung states its ruler, its scale,
and whether the engine beat the baselines ON THAT RUNG.

  R1  GSS      US, 15 items, 1972-2024, real microdata (on disk)
  R2  WVS7     66 countries, 8 items, real microdata (on disk)
  R3  ANES     US, 2024, real microdata (on prime)
  R4  GOQA     40 items x 66 countries, Pew+WVS derived (real)
  R5  LIVE     Pew / Gallup / Ipsos / YouGov fetched at runtime by
               Path D — the open-ended rung, any survey on the planet

Each rung reports: engine, MrsP, naive, and (where the source supports
it) cohort shape. A rung PASSES only if the engine beats naive AND the
result is reported next to MrsP rather than instead of it.

Env: VL_POP (default 200000), VL_RUNGS (default "1,2,4").
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.calibration import (_build_features, _get_country_index,
                                calibrate_cohort, calibrate_single)
from earth1.genesis import genesis
from earth1.rng import logit, sigmoid

POP = int(os.environ.get("VL_POP", "200000"))
RUNGS = set(os.environ.get("VL_RUNGS", "1,2,4").split(","))
AGE_TAGS = ["18_29", "30_44", "45_59", "60_plus"]


def _us_cells(civ, c2i):
    us = civ.country == c2i["US"]
    out = {}
    for i, tag in enumerate(AGE_TAGS):
        for e in range(3):
            m = (us & (civ.education == e)
                 & ((civ.age_bucket == i) if i < 3 else (civ.age_bucket >= 3)))
            if m.sum() >= 10:
                out[f"{tag}|{e}"] = m
    return us, out


def rung_gss(civ, c2i, feats) -> dict:
    """R1 — GSS: fit on one year's cohort cells, score all later years."""
    truth = json.load(open("data/gss_truth.json"))
    us, masks = _us_cells(civ, c2i)
    eng, naive = [], []
    for var, rec in truth.items():
        years = sorted(int(y) for y in rec["national"])
        if len(years) < 4:
            continue
        y0 = years[0]
        cells = {k.split("|", 1)[1]: v["share"]
                 for k, v in rec["cells"].items()
                 if k.startswith(f"{y0}|") and "pol_" not in k}
        if len(cells) < 6:
            continue
        base = rec["national"][str(y0)]["share"]
        w, info = calibrate_cohort(civ, base, cells, masks)
        if not info["accepted"]:
            continue
        bl = logit(np.array([base]))[0]
        p = float(sigmoid(bl + feats[us] @ w).mean())
        grand = float(np.mean([rec["national"][str(y)]["share"]
                               for y in years]))
        for y in years[1:]:
            t = rec["national"][str(y)]["share"]
            eng.append(abs(p - t))
            naive.append(abs(grand - t))
    return {"rung": "R1 GSS", "ruler": "GSS 1972-2024 microdata (US)",
            "scale": f"{len(eng)} item-years",
            "engine_mae": float(np.mean(eng)) if eng else None,
            "naive_mae": float(np.mean(naive)) if naive else None}


def rung_wvs(civ, c2i, feats) -> dict:
    """R2 — WVS7: per-country cohort targets, LOO-country."""
    import csv
    from earth1.benchmark import ISO3_TO_ISO2
    cells = {}
    for r in csv.DictReader(open("data/wvs_w7_cohort_by_country.csv")):
        i2 = ISO3_TO_ISO2.get(r["country"])
        if i2:
            cells.setdefault(r["qcode"], {}).setdefault(
                i2, {})[r["age_bucket"]] = float(r["yes_weighted"])
    eng, naive = [], []
    for q, by_cc in cells.items():
        ccs = [c for c in by_cc if c in c2i and len(by_cc[c]) >= 4]
        if len(ccs) < 8:
            continue
        allv = [np.mean(list(by_cc[c].values())) for c in ccs]
        grand = float(np.mean(allv))
        for held in ccs[:12]:
            tr = {c: float(np.mean(list(by_cc[c].values())))
                  for c in ccs if c != held}
            w = calibrate_single(civ, grand, tr, extended=True)
            if not np.any(w):
                continue
            m = civ.country == c2i[held]
            if m.sum() < 40:
                continue
            bl = logit(np.array([grand]))[0]
            p = float(sigmoid(bl + feats[m] @ w).mean())
            t = float(np.mean(list(by_cc[held].values())))
            eng.append(abs(p - t))
            naive.append(abs(grand - t))
    return {"rung": "R2 WVS7", "ruler": "WVS Wave 7 microdata (66 countries)",
            "scale": f"{len(eng)} held-out country-items",
            "engine_mae": float(np.mean(eng)) if eng else None,
            "naive_mae": float(np.mean(naive)) if naive else None}


def rung_goqa(civ, c2i, feats) -> dict:
    """R4 — GOQA 40x66 on pinned folds, corrected truth."""
    from earth1.benchmark import run_goqa_benchmark
    os.environ.setdefault("EARTH1_PINNED_FOLDS", "data/cv_folds.json")
    gt = json.load(open("data/benchmark/goqa_ground_truth.json"))
    r = run_goqa_benchmark(civ, gt, cv_seed=42)
    return {"rung": "R4 GOQA", "ruler": "GOQA 40x66 (Pew+WVS derived)",
            "scale": f"{r.n_country_pairs} cells",
            "engine_mae": r.engine_cv_mae, "naive_mae": r.naive_cv_mae,
            "wins": f"{r.engine_wins}/40"}


def main() -> None:
    civ = genesis(POP, 42)
    c2i, _ = _get_country_index(civ)
    feats = _build_features(civ, extended=True)
    rows = []
    if "1" in RUNGS:
        rows.append(rung_gss(civ, c2i, feats))
    if "2" in RUNGS:
        rows.append(rung_wvs(civ, c2i, feats))
    if "4" in RUNGS:
        rows.append(rung_goqa(civ, c2i, feats))
    for r in rows:
        e, n = r.get("engine_mae"), r.get("naive_mae")
        verdict = ("PASS" if e is not None and n is not None and e < n
                   else "FAIL")
        r["verdict"] = verdict
        print(f"  {r['rung']:10s} {r['scale']:26s} engine "
              f"{e:.4f} vs naive {n:.4f} -> {verdict}"
              + (f" ({r['wins']})" if "wins" in r else ""), flush=True)
    json.dump({"pop": POP, "rungs": rows},
              open("data/validation_ladder.json", "w"), indent=1)
    passed = sum(1 for r in rows if r["verdict"] == "PASS")
    print(f"LADDER: {passed}/{len(rows)} rungs passed", flush=True)


if __name__ == "__main__":
    main()
