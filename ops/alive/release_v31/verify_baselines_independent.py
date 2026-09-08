#!/usr/bin/env python3
"""Independent adversarial re-verification of baselines_agreement.py claims.
Written from scratch; does not import or reuse the audited script."""
import numpy as np
import pandas as pd

CSV = "/Users/pietronovelli/Documents/GitHub/earth-1-engine/data/cycles/distance2026/cells.csv"
df = pd.read_csv(CSV)

print("rows:", len(df))
print("estates:", df.estate.value_counts().to_dict())

# --- coverage of survey-noise columns per estate
for est in df.estate.unique():
    sub = df[df.estate == est]
    print(est, "n_survey notna:", int(sub.n_survey.notna().sum()),
          "se95 notna:", int(sub.se95_pp.notna().sum()),
          "within_noise notna:", int(sub.within_noise.notna().sum()))

# --- headline sets
na = df[df.abstained == 0]
print("non-abstained:", len(na))
ns = na[na.within_noise.notna()]
print("noise set:", len(ns), "estates in noise set:", sorted(ns.estate.unique()))
# any WVS non-abstained cells missing within_noise?
wvs_na = na[na.estate.isin(["wvs_heldout", "wvs_extended"])]
print("wvs non-abstained:", len(wvs_na), "of which within_noise NaN:",
      int(wvs_na.within_noise.isna().sum()))

# --- Earth-1 headline from recorded columns
print("E1 agree recorded: %.6f" % na.modal_agree.mean())
print("E1 within recorded: %.6f" % ns.within_noise.mean())

# --- rule checks (independent formulations)
side_ok = ((df.model > 0.5) == (df.human > 0.5)).astype(int) == df.modal_agree.astype(int)
print("agree rule mismatches over all rows:", int((~side_ok).sum()))
# boundary sanity: any human exactly 0.5?
print("human==0.5 exactly:", int((df.human == 0.5).sum()), "model==0.5:", int((df.model == 0.5).sum()))

d = df[df.within_noise.notna()].copy()
err_pp = (d.model - d.human).abs() * 100
rule_wn = (err_pp <= d.se95_pp).astype(int)
mism = d[rule_wn != d.within_noise.astype(int)]
print("wn rule defined cells:", len(d), "mismatches:", len(mism))
print("mismatch noise_dist values:", mism.noise_dist.tolist())
print("mismatch abstained values:", mism.abstained.tolist())

# recomputed headline via rule
print("E1 agree via rule: %.6f" % ((na.model > 0.5) == (na.human > 0.5)).mean())
print("E1 within via rule: %.6f" % (((ns.model - ns.human).abs() * 100) <= ns.se95_pp).mean())

# --- per-item constancy of the three MAE columns
for c in ["mrsp_mae_pp", "naive_mae_pp", "region_mae_pp"]:
    nun = df.groupby(["estate", "item"])[c].nunique(dropna=False)
    print(c, "items:", len(nun), "max nunique per item:", int(nun.max()))

# --- LOO reconstructions (own implementation via merge of sums)
s = df.groupby(["estate", "item"]).human.agg(["sum", "count"]).rename(
    columns={"sum": "s_it", "count": "n_it"})
df2 = df.merge(s, on=["estate", "item"], how="left")
df2["naive_pred"] = (df2.s_it - df2.human) / (df2.n_it - 1)

sr = df.groupby(["estate", "item", "region"]).human.agg(["sum", "count"]).rename(
    columns={"sum": "s_r", "count": "n_r"})
df2 = df2.merge(sr, on=["estate", "item", "region"], how="left")
loo_r = (df2.s_r - df2.human) / (df2.n_r - 1)
singleton = df2.n_r == 1
print("singleton-region cells:", int(singleton.sum()))
df2["region_pred"] = np.where(singleton, df2.naive_pred, loo_r)

def item_val(pred, rec_col, cellmask=None, label=""):
    dd = df2 if cellmask is None else df2[cellmask]
    e = (dd[pred] - dd.human).abs() * 100
    item_mae = e.groupby([dd.estate, dd.item]).mean()
    rec = df2.groupby(["estate", "item"])[rec_col].first()
    disc = (item_mae - rec).abs().dropna()
    print(f"{label}: items={len(disc)} within.005={float((disc<=0.0051).mean()):.4f} "
          f"within.01={float((disc<=0.01).mean()):.4f} mean={disc.mean():.6f} max={disc.max():.6f}")
    return disc

item_val("naive_pred", "naive_mae_pp", None, "naive LOO all-cells")
item_val("region_pred", "region_mae_pp", None, "region LOO+fallback all-cells")
# alternative cell sets for the recorded aggregate
item_val("naive_pred", "naive_mae_pp", df2.abstained == 0, "naive LOO non-abstained-only")
item_val("region_pred", "region_mae_pp", df2.abstained == 0, "region LOO non-abst-only")

# --- rejected variants: do they really fail?
df2["naive_nonloo"] = df2.s_it / df2.n_it
item_val("naive_nonloo", "naive_mae_pp", None, "naive NON-LOO (incl self)")
df2["region_nonloo"] = df2.s_r / df2.n_r
item_val("region_nonloo", "region_mae_pp", None, "region NON-LOO (incl self)")
df2["region_nofb"] = np.where(singleton, np.nan, loo_r)
e = (df2.region_nofb - df2.human).abs() * 100
im = e.groupby([df2.estate, df2.item]).mean()
rec = df2.groupby(["estate", "item"]).region_mae_pp.first()
disc = (im - rec).abs().dropna()
print(f"region LOO NO-fallback (drop singleton cells): items={len(disc)} "
      f"within.01={float((disc<=0.01).mean()):.4f} max={disc.max():.6f}")

# --- baseline table rows on identical headline sets
na2 = df2[df2.abstained == 0]
ns2 = na2[na2.within_noise.notna()]
for p in ["naive_pred", "region_pred"]:
    a = ((na2[p] > 0.5) == (na2.human > 0.5)).mean()
    w = (((ns2[p] - ns2.human).abs() * 100) <= ns2.se95_pp).mean()
    print(f"{p}: agree={a:.6f} within={w:.6f}")

# --- pooled MAE on non-abstained cells
for p, lab in [("model", "earth1"), ("naive_pred", "naive"), ("region_pred", "region")]:
    print(f"pooled MAE {lab}: {((na2[p]-na2.human).abs()*100).mean():.4f}")
print("pooled MAE mrsp (cell-weighted recorded):", round(na2.mrsp_mae_pp.mean(), 4))

# --- does any per-cell MrsP prediction column exist?
print("columns:", list(df.columns))
