#!/usr/bin/env python3
"""AUDIT ITEM 15: split opinion results by substrate provenance class.

Classes:
  survey_measured : country ISO2 in population_frame.v1.json joint_provenance.survey_measured (63 codes)
  tier_fallback   : any other country appearing in cells.csv

Evaluation set: non-abstained cells (abstained == 0) of
  data/cycles/distance2026/cells.csv

Per class we compute:
  - cell count
  - majority agreement           = mean(modal_agree)
  - within-noise share           = mean(within_noise) over cells where n_survey is known
  - median noise_dist            (over cells where noise_dist is known)
  - Earth-1 MAE (pp)             = mean |model - human| * 100
  - naive baseline MAE (pp)      : prediction = leave-one-out mean of 'human' over
                                   same (estate, item), pooled over non-abstained cells
  - region-copy baseline MAE (pp): prediction = leave-one-out mean of 'human' over
                                   same (estate, item, region); singleton groups fall
                                   back to the naive (estate,item) LOO mean
  - earth1_minus_regioncopy_mae_gap_pp

Output: provenance_split.json next to this script.
"""
import csv
import json
import statistics
from collections import defaultdict

CELLS = "/Users/pietronovelli/Documents/GitHub/earth-1-engine/data/cycles/distance2026/cells.csv"
FRAME = "/Users/pietronovelli/Documents/GitHub/earth-1-engine/data/population_frame.v1.json"
OUT = "/private/tmp/claude-501/-Users-pietronovelli-Documents-GitHub-vaultik-x/e30708db-e208-4f7c-aad1-c0be9c88f760/scratchpad/audit_v31/provenance_split.json"

frame = json.load(open(FRAME))
jp = frame["joint_provenance"]
survey_measured = set(jp["survey_measured"])
assert len(survey_measured) == 63, f"expected 63 survey-measured codes, got {len(survey_measured)}"
assert jp["n_survey_measured"] == 63
n_tier_fallback_frame = jp["n_tier_fallback"]

rows = list(csv.DictReader(open(CELLS)))
cells = [r for r in rows if r["abstained"] == "0"]  # non-abstained evaluation set

def f(x):
    x = x.strip()
    return float(x) if x else None

# ---- leave-one-out baseline pools over non-abstained cells ----
naive_pool = defaultdict(lambda: [0.0, 0])        # (estate,item) -> [sum, n]
region_pool = defaultdict(lambda: [0.0, 0])       # (estate,item,region) -> [sum, n]
for r in cells:
    h = float(r["human"])
    naive_pool[(r["estate"], r["item"])][0] += h
    naive_pool[(r["estate"], r["item"])][1] += 1
    region_pool[(r["estate"], r["item"], r["region"])][0] += h
    region_pool[(r["estate"], r["item"], r["region"])][1] += 1

singleton_region_fallbacks = 0
per_class = defaultdict(lambda: {
    "abs_err_model": [], "abs_err_naive": [], "abs_err_region": [],
    "modal_agree": [], "within_noise": [], "noise_dist": [],
    "countries": set(), "n_survey_known": 0,
})

for r in cells:
    cls = "survey_measured" if r["country"] in survey_measured else "tier_fallback"
    d = per_class[cls]
    h = float(r["human"]); m = float(r["model"])
    d["abs_err_model"].append(abs(m - h))
    d["modal_agree"].append(float(r["modal_agree"]))
    d["countries"].add(r["country"])

    ns = f(r["n_survey"])
    if ns is not None:
        d["n_survey_known"] += 1
        wn = f(r["within_noise"])
        if wn is not None:
            d["within_noise"].append(wn)
    nd = f(r["noise_dist"])
    if nd is not None:
        d["noise_dist"].append(nd)

    # naive LOO
    s, n = naive_pool[(r["estate"], r["item"])]
    naive_pred = (s - h) / (n - 1) if n > 1 else None
    if naive_pred is not None:
        d["abs_err_naive"].append(abs(naive_pred - h))

    # region-copy LOO, singleton -> naive LOO fallback
    s2, n2 = region_pool[(r["estate"], r["item"], r["region"])]
    if n2 > 1:
        region_pred = (s2 - h) / (n2 - 1)
    else:
        region_pred = naive_pred
        singleton_region_fallbacks += 1
    if region_pred is not None:
        d["abs_err_region"].append(abs(region_pred - h))

result = {
    "source_cells_csv": CELLS,
    "source_frame_json": FRAME,
    "eval_set": "non-abstained cells (abstained==0)",
    "n_rows_total": len(rows),
    "n_cells_nonabstained": len(cells),
    "n_survey_measured_codes_in_frame": len(survey_measured),
    "n_tier_fallback_codes_in_frame": n_tier_fallback_frame,
    "singleton_region_fallbacks_to_naive": singleton_region_fallbacks,
    "baseline_note": ("naive = LOO mean of human over same (estate,item); "
                      "region_copy = LOO mean over same (estate,item,region), "
                      "singleton region groups fall back to naive LOO; "
                      "pools restricted to non-abstained cells"),
    "classes": {},
}

for cls, d in sorted(per_class.items()):
    mae_model = 100 * statistics.fmean(d["abs_err_model"])
    mae_naive = 100 * statistics.fmean(d["abs_err_naive"])
    mae_region = 100 * statistics.fmean(d["abs_err_region"])
    result["classes"][cls] = {
        "n_cells": len(d["abs_err_model"]),
        "n_countries": len(d["countries"]),
        "majority_agreement": round(statistics.fmean(d["modal_agree"]), 4),
        "n_cells_with_n_survey": d["n_survey_known"],
        "within_noise_share_where_n_survey_known": (
            round(statistics.fmean(d["within_noise"]), 4) if d["within_noise"] else None),
        "median_noise_dist": (
            round(statistics.median(d["noise_dist"]), 3) if d["noise_dist"] else None),
        "mae_pp_earth1": round(mae_model, 3),
        "mae_pp_naive": round(mae_naive, 3),
        "mae_pp_region_copy": round(mae_region, 3),
        "earth1_minus_regioncopy_mae_gap_pp": round(mae_model - mae_region, 3),
        "earth1_minus_naive_mae_gap_pp": round(mae_model - mae_naive, 3),
    }

# ---- abstention rate per class (over all rows, not just non-abstained) ----
for cls, pred in (("survey_measured", lambda c: c in survey_measured),
                  ("tier_fallback", lambda c: c not in survey_measured)):
    sub = [r for r in rows if pred(r["country"])]
    ab = sum(1 for r in sub if r["abstained"] == "1")
    result["classes"][cls]["n_rows_incl_abstained"] = len(sub)
    result["classes"][cls]["abstention_rate"] = round(ab / len(sub), 4)

# ---- estate-matched comparison: all tier-fallback cells are goqa_dev, so also
#      report survey-measured restricted to goqa_dev to remove the estate confound ----
def summarize(subset):
    mae_m = 100 * statistics.fmean(abs(float(r["model"]) - float(r["human"])) for r in subset)
    errs_n, errs_r = [], []
    for r in subset:
        h = float(r["human"])
        s, n = naive_pool[(r["estate"], r["item"])]
        np_ = (s - h) / (n - 1) if n > 1 else None
        if np_ is not None:
            errs_n.append(abs(np_ - h))
        s2, n2 = region_pool[(r["estate"], r["item"], r["region"])]
        rp = (s2 - h) / (n2 - 1) if n2 > 1 else np_
        if rp is not None:
            errs_r.append(abs(rp - h))
    mae_n = 100 * statistics.fmean(errs_n)
    mae_r = 100 * statistics.fmean(errs_r)
    return {
        "n_cells": len(subset),
        "n_countries": len(set(r["country"] for r in subset)),
        "majority_agreement": round(statistics.fmean(float(r["modal_agree"]) for r in subset), 4),
        "mae_pp_earth1": round(mae_m, 3),
        "mae_pp_naive": round(mae_n, 3),
        "mae_pp_region_copy": round(mae_r, 3),
        "earth1_minus_regioncopy_mae_gap_pp": round(mae_m - mae_r, 3),
        "earth1_minus_naive_mae_gap_pp": round(mae_m - mae_n, 3),
    }

result["estate_note"] = ("all non-abstained tier_fallback cells belong to the goqa_dev estate; "
                         "survey_measured spans wvs_heldout, wvs_extended and goqa_dev, so the "
                         "estate-matched block compares like with like")
result["estate_matched_goqa_dev"] = {
    "survey_measured": summarize([r for r in cells if r["estate"] == "goqa_dev"
                                  and r["country"] in survey_measured]),
    "tier_fallback": summarize([r for r in cells if r["estate"] == "goqa_dev"
                                and r["country"] not in survey_measured]),
}

# cross-check: recorded aggregate columns in the csv (constant per file section) vs reconstruction
rec = {k: statistics.fmean(float(r[k]) for r in cells) for k in
       ("mrsp_mae_pp", "naive_mae_pp", "region_mae_pp")}
all_model = 100 * statistics.fmean(abs(float(r["model"]) - float(r["human"])) for r in cells)
result["crosscheck"] = {
    "recorded_columns_mean_over_nonabstained": {k: round(v, 3) for k, v in rec.items()},
    "reconstructed_overall_earth1_mae_pp": round(all_model, 3),
}

with open(OUT, "w") as fh:
    json.dump(result, fh, indent=2)
print(json.dumps(result, indent=2))
