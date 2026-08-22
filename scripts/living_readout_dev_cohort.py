"""0.4 DEV DIAGNOSTIC, stage 2 — the COHORT instrument.

DEV ONLY, no holdout. Stage 1 (national) showed living-26 worse than
legacy-18 at national aggregation (+0.85pp) — the expected MRP-theory
outcome if within-unit signal exists but washes out in country means.
This stage measures where the 0.4 thesis actually lives: do lived-state
features differentiate COHORTS within countries, in the directions real
people differ?

Truth: data/wvs_w7_cohort_by_country.csv — 8 questions x 65 countries x
4 age buckets, weighted WVS-7 aggregates (median cell n=352).

Protocol: same 200k/seed-42 world lived 60 canonical days; features
aggregated per (country, age-bucket-group) cell; country-held-out CV
(5 folds x 3 seeds — cells never leak across the country split);
identical machinery for every arm.

Metrics per arm: cohort MAE (pp) · gradient direction (sign of
old-vs-young difference per question x held-out country, chance 50%) ·
calibration slope · within-country R^2 (variance of country-demeaned
truth explained by country-demeaned predictions — the number that
cannot be faked by country stereotypes, which demean to zero).
"""
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from earth1.alive import birth_world, live_one_day
from earth1.benchmark_questions import ISO3_TO_ISO2
from earth1.calibration import (LIVING_FEATURES, _build_features,
                                living_features)
from earth1.genesis import GENESIS_COUNTRY_CODES
from earth1.rng import logit, sigmoid

POP, SEED, DAYS = 200_000, 42, 60
RIDGE, FOLDS, CV_SEEDS = 1.0, 5, (42, 7, 13)
BUCKETS = {"18_29": (0,), "30_44": (1,), "45_59": (2,), "60_plus": (3, 4)}
FAMILIES = {
    "deprivation": ["deprivation"], "employment": ["unemployed", "spells"],
    "hunger": ["hunger"], "mental_health": ["mental"],
    "addiction": ["addiction"], "isolation": ["relationship"],
    "hope": ["hope"],
}


def cell_features(X, civ, country_idx, bucket_ids):
    m = (civ.country == country_idx) & np.isin(civ.age_bucket, bucket_ids)
    return X[m].mean(axis=0) if m.sum() >= 20 else None


def main():
    t0 = time.time()
    w = birth_world(POP, SEED)
    rng = np.random.default_rng(SEED)
    for d in range(DAYS):
        live_one_day(w, rng)
    civ = w.civ
    X_leg = _build_features(civ, extended=True)
    X_liv = living_features(w)
    n_static = X_leg.shape[1]
    names_liv = list(LIVING_FEATURES)

    code_to_idx = {c: i for i, c in enumerate(GENESIS_COUNTRY_CODES)}
    truth = {}
    for r in csv.DictReader(open(ROOT / "data/wvs_w7_cohort_by_country.csv")):
        iso2 = ISO3_TO_ISO2.get(r["country"])
        ci = code_to_idx.get(iso2)
        if ci is not None:
            truth.setdefault(r["qcode"], {}).setdefault(ci, {})[
                r["age_bucket"]] = float(r["yes_weighted"])

    # build the cell table once per feature set
    def build_cells(X):
        rows = []
        for q, per_c in truth.items():
            for ci, buckets in per_c.items():
                for bname, y in buckets.items():
                    f = cell_features(X, civ, ci, BUCKETS[bname])
                    if f is not None:
                        rows.append((q, ci, bname, y, f))
        return rows

    cells_leg = build_cells(X_leg)
    cells_liv = build_cells(X_liv)
    print(f"  cells: {len(cells_liv)} (legacy {len(cells_leg)})", flush=True)

    def run_arm(cells, label, drop_cols=None):
        qs = sorted({c[0] for c in cells})
        countries = sorted({c[1] for c in cells})
        maes, cals_p, cals_y = [], [], []
        grad_ok = grad_n = 0
        wr2_num = wr2_den = 0.0
        for seed in CV_SEEDS:
            rs = np.random.default_rng(seed)
            order = rs.permutation(len(countries))
            for f in range(FOLDS):
                test_c = {countries[i] for i in order[f::FOLDS]}
                for q in qs:
                    tr = [(y, feat) for (qq, ci, b, y, feat) in cells
                          if qq == q and ci not in test_c]
                    te = [(ci, b, y, feat) for (qq, ci, b, y, feat)
                          in cells if qq == q and ci in test_c]
                    if len(tr) < 30 or not te:
                        continue
                    Xt = np.array([f2 for _, f2 in tr])
                    yt = logit(np.clip(np.array([y for y, _ in tr]),
                                       0.02, 0.98))
                    Xs = np.array([f2 for _, _, _, f2 in te])
                    if drop_cols is not None:
                        Xt = np.delete(Xt, drop_cols, axis=1)
                        Xs = np.delete(Xs, drop_cols, axis=1)
                    mu, sd = Xt.mean(0), Xt.std(0) + 1e-9
                    Zt, Zs = (Xt - mu) / sd, (Xs - mu) / sd
                    b0 = yt.mean()
                    A = Zt.T @ Zt + RIDGE * np.eye(Zt.shape[1])
                    wgt = np.linalg.solve(A, Zt.T @ (yt - b0))
                    p = sigmoid(b0 + Zs @ wgt)
                    ys = np.array([y for _, _, y, _ in te])
                    maes.append(np.abs(p - ys).mean() * 100)
                    cals_p.extend(p.tolist()); cals_y.extend(ys.tolist())
                    # gradient: old vs young per held-out country
                    per = {}
                    for (ci, b, y, _), pi in zip(te, p):
                        per.setdefault(ci, {})[b] = (y, pi)
                    for ci, bb in per.items():
                        if "18_29" in bb and "60_plus" in bb:
                            ty = bb["60_plus"][0] - bb["18_29"][0]
                            pp = bb["60_plus"][1] - bb["18_29"][1]
                            if abs(ty) > 0.01:
                                grad_n += 1
                                grad_ok += int(np.sign(ty) == np.sign(pp))
                    # within-country R^2 on demeaned cells
                    percm = {}
                    for (ci, b, y, _), pi in zip(te, p):
                        percm.setdefault(ci, []).append((y, pi))
                    for ci, pairs in percm.items():
                        if len(pairs) >= 3:
                            ya = np.array([a for a, _ in pairs])
                            pa = np.array([b2 for _, b2 in pairs])
                            wr2_num += float((( (ya - ya.mean())
                                              - (pa - pa.mean()))**2).sum())
                            wr2_den += float(((ya - ya.mean())**2).sum())
        cal = float(np.polyfit(np.array(cals_p), np.array(cals_y), 1)[0]) \
            if len(cals_p) > 10 else float("nan")
        return {"arm": label,
                "cohort_mae_pp": round(float(np.mean(maes)), 3),
                "gradient_direction_pct": round(100 * grad_ok
                                                / max(grad_n, 1), 1),
                "gradient_n": grad_n,
                "calibration_slope": round(cal, 3),
                "within_country_r2": round(1.0 - wr2_num
                                           / max(wr2_den, 1e-9), 4)}

    naive_cells = [(q, ci, b, y, np.zeros(1)) for (q, ci, b, y, _)
                   in cells_liv]
    res = {
        "naive": run_arm(naive_cells, "naive"),
        "legacy_18": run_arm(cells_leg, "legacy_18"),
        "living_26": run_arm(cells_liv, "living_26"),
    }
    # family ablations, delta vs full living
    abl = {}
    for fam, members in FAMILIES.items():
        cols = [n_static + names_liv.index(m) for m in members]
        abl[fam] = run_arm(cells_liv, f"minus_{fam}", drop_cols=cols)
        abl[fam]["delta_mae_vs_full"] = round(
            abl[fam]["cohort_mae_pp"] - res["living_26"]["cohort_mae_pp"], 3)

    out = {"diagnostic": "0.4 dev stage 2: cohort instrument",
           "NOT_BENCHMARK_A": True, "holdout_touched": False,
           "truth": "wvs_w7_cohort_by_country.csv (8q x 65c x 4 buckets)",
           "protocol": {"pop": POP, "seed": SEED, "days": DAYS,
                        "folds": FOLDS, "cv_seeds": list(CV_SEEDS),
                        "cells": len(cells_liv)},
           "arms": res, "family_ablations": abl,
           "provenance": {"host": os.uname().nodename,
                          "commit": subprocess.run(
                              ["git", "rev-parse", "HEAD"],
                              capture_output=True, text=True,
                              cwd=ROOT).stdout.strip(),
                          "wall_clock": time.strftime(
                              "%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                          "runtime_s": round(time.time() - t0, 1)}}
    (ROOT / "data" / "living_readout_dev_cohort.json").write_text(
        json.dumps(out, indent=1))
    print(json.dumps(res, indent=1))
    print("ablation deltas (pp vs full living):",
          {k: v["delta_mae_vs_full"] for k, v in abl.items()})


if __name__ == "__main__":
    main()
