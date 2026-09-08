#!/usr/bin/env python3
"""
AUDIT ITEM 1 — baseline rows for the paper's 83.5% majority-agreement /
14.2% within-survey-noise headline.

Input : /Users/pietronovelli/Documents/GitHub/earth-1-engine/data/cycles/distance2026/cells.csv
Output: baselines_agreement.json (next to this script)

Steps:
 1. Reproduce Earth-1's headline numbers from the recorded columns
    (modal_agree, within_noise) and independently from rule-based recomputation.
 2. Reconstruct baseline PREDICTIONS:
      naive  = leave-one-country-out (LOO) mean of `human` across countries
               within the same (estate, item)
      region = LOO mean of `human` within (estate, item, region);
               cells whose region has only 1 country fall back to the naive
               (LOO grand-mean) prediction
    Validate each against the recorded per-item naive_mae_pp / region_mae_pp
    (those columns are constant per (estate, item) — item-level aggregates,
    stored to 2 decimals).
 3. Apply Earth-1's exact agreement / within-noise rules to the baseline
    predictions on the identical cell sets used for the headline.
 4. Pooled MAE cross-check per method.

MrsP predictions are NOT reconstructable: cells.csv carries only the per-item
mrsp_mae_pp aggregate, no per-cell MrsP prediction or error.
"""
import json
import numpy as np
import pandas as pd

CSV = "/Users/pietronovelli/Documents/GitHub/earth-1-engine/data/cycles/distance2026/cells.csv"
OUT = "/private/tmp/claude-501/-Users-pietronovelli-Documents-GitHub-vaultik-x/e30708db-e208-4f7c-aad1-c0be9c88f760/scratchpad/audit_v31/baselines_agreement.json"

df = pd.read_csv(CSV)
assert len(df) == 23974, len(df)

# ---------------------------------------------------------------- rules
# Majority-agreement rule, inferred: side(x) = (x > 0.5). Verified below to
# reproduce the recorded modal_agree on 100.0% of all 23,974 cells.
def same_side(pred, human):
    return ((pred > 0.5) == (human > 0.5)).astype(float)

# Within-noise rule, inferred: |pred - human| (in pp) <= se95_pp.
# Verified below to reproduce recorded within_noise on 99.95% of the 12,977
# cells where it is defined (6 mismatches, all sitting exactly at
# noise_dist == 1.0, i.e. boundary cells decided by the unrounded se95 that
# the CSV stores rounded).
def within_noise(pred, human, se95):
    return ((pred - human).abs() * 100 <= se95).astype(float)

rule_check_agree = float(
    (same_side(df.model, df.human) == df.modal_agree).mean()
)
wn_def = df[df.within_noise.notna()]
rule_check_wn = float(
    (within_noise(wn_def.model, wn_def.human, wn_def.se95_pp) == wn_def.within_noise).mean()
)

# ---------------------------------------------------------------- headline sets
# Agreement set: non-abstained cells (all three estates).
agree_set = df[df.abstained == 0]
# Within-noise set: non-abstained cells where within_noise is defined
# (wvs_heldout + wvs_extended only; goqa_dev has no n_survey/se95_pp).
noise_set = agree_set[agree_set.within_noise.notna()]

earth1_agree_recorded = float(agree_set.modal_agree.mean())
earth1_wn_recorded = float(noise_set.within_noise.mean())
earth1_agree_rule = float(same_side(agree_set.model, agree_set.human).mean())
earth1_wn_rule = float(within_noise(noise_set.model, noise_set.human, noise_set.se95_pp).mean())

# ---------------------------------------------------------------- baselines
g = df.groupby(["estate", "item"])["human"]
n_item = g.transform("count")
m_item = g.transform("mean")
df["naive_pred"] = (m_item * n_item - df.human) / (n_item - 1)  # LOO grand mean

gr = df.groupby(["estate", "item", "region"])["human"]
n_reg = gr.transform("count")
m_reg = gr.transform("mean")
loo_reg = np.where(n_reg > 1, (m_reg * n_reg - df.human) / (n_reg - 1), np.nan)
n_singleton = int(np.isnan(loo_reg).sum())
df["region_pred"] = np.where(np.isnan(loo_reg), df["naive_pred"], loo_reg)

# ---- validation vs recorded per-item MAE columns (stored to 2 decimals)
def validate(pred_col, rec_col):
    err = (df[pred_col] - df.human).abs() * 100
    item_mae = err.groupby([df.estate, df.item]).mean()
    rec = df.groupby(["estate", "item"])[rec_col].first()
    disc = (item_mae - rec).abs()
    return {
        "n_items": int(len(disc)),
        "match_rate_within_rounding_0p0051pp": float((disc <= 0.0051).mean()),
        "match_rate_within_0p01pp": float((disc <= 0.01).mean()),
        "mean_abs_discrepancy_pp": float(disc.mean()),
        "max_abs_discrepancy_pp": float(disc.max()),
    }

val_naive = validate("naive_pred", "naive_mae_pp")
val_region = validate("region_pred", "region_mae_pp")

# ---- rejected variants (for the record): non-LOO grand mean and non-LOO /
# no-fallback region variants, tested during development, matched the recorded
# columns for <1% / <50% of items respectively; the LOO definitions above are
# the ones that match the record.

# Re-slice the headline cell sets now that prediction columns exist.
agree_set = df[df.abstained == 0]
noise_set = agree_set[agree_set.within_noise.notna()]

# ---------------------------------------------------------------- baseline rows
def rows_for(pred):
    a = float(same_side(agree_set[pred], agree_set.human).mean())
    w = float(within_noise(noise_set[pred], noise_set.human, noise_set.se95_pp).mean())
    return a, w

naive_agree, naive_wn = rows_for("naive_pred")
region_agree, region_wn = rows_for("region_pred")

# ---------------------------------------------------------------- pooled MAE
def pooled_mae(pred):
    return float(((agree_set[pred] - agree_set.human).abs() * 100).mean())

pooled = {
    "earth1_model_pp": pooled_mae("model"),
    "naive_reconstructed_pp": pooled_mae("naive_pred"),
    "region_reconstructed_pp": pooled_mae("region_pred"),
    # recorded per-item columns, pooled two ways
    "recorded_item_columns_cell_weighted_pp": {
        "mrsp": float(agree_set.mrsp_mae_pp.mean()),
        "naive": float(agree_set.naive_mae_pp.mean()),
        "region": float(agree_set.region_mae_pp.mean()),
    },
    "recorded_item_columns_unweighted_item_mean_pp": {
        "mrsp": float(df.groupby(["estate", "item"]).mrsp_mae_pp.first().mean()),
        "naive": float(df.groupby(["estate", "item"]).naive_mae_pp.first().mean()),
        "region": float(df.groupby(["estate", "item"]).region_mae_pp.first().mean()),
    },
    "note": ("Pooled over cells (or items) of all three estates combined; NOT "
             "comparable 1:1 to per-frame lineage numbers (11.84/12.80/9.70) "
             "which are computed per-frame."),
}

result = {
    "source_csv": CSV,
    "n_rows_total": int(len(df)),
    "cell_sets": {
        "agreement_set": {
            "definition": "abstained == 0 (all three estates)",
            "n": int(len(agree_set)),
        },
        "within_noise_set": {
            "definition": "abstained == 0 AND within_noise defined (wvs_heldout + wvs_extended; goqa_dev has no survey-noise columns)",
            "n": int(len(noise_set)),
        },
    },
    "rules_inferred": {
        "majority_agreement": "(pred > 0.5) == (human > 0.5); reproduces recorded modal_agree",
        "majority_rule_match_rate_all_cells": rule_check_agree,
        "within_noise": "|pred - human| in pp <= se95_pp; reproduces recorded within_noise",
        "within_noise_rule_match_rate": rule_check_wn,
        "within_noise_mismatches": "6 of 12,977, all at noise_dist == 1.0 exactly (boundary cells decided by unrounded se95)",
    },
    "earth1_headline_reproduction": {
        "majority_agreement_recorded_column": earth1_agree_recorded,
        "majority_agreement_recomputed_rule": earth1_agree_rule,
        "within_noise_recorded_column": earth1_wn_recorded,
        "within_noise_recomputed_rule": earth1_wn_rule,
    },
    "baseline_reconstruction": {
        "naive": {
            "definition": "leave-one-country-out mean of `human` across countries within (estate, item)",
            "validation_vs_recorded_naive_mae_pp": val_naive,
        },
        "region": {
            "definition": "leave-one-country-out mean of `human` within (estate, item, region); singleton-region cells (n=1 country in region) fall back to the naive LOO grand mean",
            "n_singleton_region_cells": n_singleton,
            "validation_vs_recorded_region_mae_pp": val_region,
        },
        "mrsp": "NOT reconstructable from cells.csv: only the per-item mrsp_mae_pp aggregate is stored; no per-cell MrsP prediction or error exists in this file.",
    },
    "table_rows": {
        "earth1": {"majority_agreement": earth1_agree_recorded, "within_noise_share": earth1_wn_recorded},
        "naive_grand_mean_LOO": {"majority_agreement": naive_agree, "within_noise_share": naive_wn},
        "region_copy_LOO": {"majority_agreement": region_agree, "within_noise_share": region_wn},
        "mrsp": {"majority_agreement": None, "within_noise_share": None,
                 "reason": "predictions not in cells.csv (only item-level MAE aggregate)"},
    },
    "pooled_mae_crosscheck": pooled,
}

with open(OUT, "w") as f:
    json.dump(result, f, indent=2)

print(json.dumps(result["table_rows"], indent=2))
print(json.dumps(result["earth1_headline_reproduction"], indent=2))
print(json.dumps(result["pooled_mae_crosscheck"], indent=2))
