"""0.4 XI.A ITERATION 2 — four arms, temporal admissibility first.

DEV ONLY. No holdout. Iteration 1 (b0c00a4) is immutable.

A. ADMISSIBILITY. Targets are WVS-7 (fieldwork 2017-2022). The
   production world is INADMISSIBLE for scoring: it has ingested GDELT
   news from 2026 — information after every target's cutoff. The scored
   state is a fresh world that reads NO news (event-level information
   content = genesis priors only; prior-vintage caveat recorded, R16),
   evolved 730 canonical days so lived state is mature and age-graded
   under 0.0a. The machine-readable admissibility table is written into
   the result.

B. FOUR ARMS — same folds, seeds, truth, state; hyperparameters chosen
   inside training folds only:
     1 legacy-18 + flat ridge        3 legacy-18 + hierarchical
     2 living-26 + flat ridge        4 living-26 + hierarchical
   Hierarchical = country-level ridge (between) + separately-shrunk
   ridge on country-DEMEANED features predicting country-DEMEANED
   targets (within), lambda_b and lambda_w selected by inner CV on the
   training countries. Arms 3 and 4 share the identical estimator and
   tuning procedure — the Earth-1 question is 4 vs 3.

C. The within level is scored directly: y_cqk - ybar_cq versus the
   predicted deviation. Country identity cannot get credit.
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
from earth1.benchmark import ISO3_TO_ISO2
from earth1.calibration import (LIVING_FEATURES, _build_features,
                                living_features)
from earth1.genesis import GENESIS_COUNTRY_CODES
from earth1.rng import logit, sigmoid

POP, SEED, DAYS = 200_000, 42, 730
FOLDS, CV_SEEDS = 5, (42, 7, 13)
LAM_GRID = (0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0)
BUCKETS = {"18_29": (0,), "30_44": (1,), "45_59": (2,), "60_plus": (3, 4)}
FAMILIES = {"deprivation": ["deprivation"], "unemployed": ["unemployed"],
            "spells": ["spells"], "hunger": ["hunger"],
            "mental": ["mental"], "addiction": ["addiction"],
            "isolation": ["relationship"], "hope": ["hope"]}

ADMISSIBILITY = {
    "targets": "WVS-7 cohort aggregates, fieldwork 2017-2022",
    "rule": "t_feature_state <= t_prediction_cutoff",
    "candidates": {
        "production_day590_world": {
            "admissible": False,
            "reason": "ingests GDELT news from 2026 via signal_bus -> "
                      "memory -> life; post-cutoff event information",
            "use": "unscored structural diagnostics only"},
        "fresh_no_news_world_730d": {
            "admissible": True,
            "reason": "no news ingestion on the research path; "
                      "event-level information = genesis priors only. "
                      "CAVEAT (recorded, R16): genesis statistical "
                      "priors are curated tables of mixed vintage - "
                      "founder-gated transcription pending; no "
                      "event-level post-cutoff information",
            "use": "SCORED (this run)"}},
    "chosen": "fresh_no_news_world_730d"}


def ridge_fit(X, y, lam):
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Z = (X - mu) / sd
    b0 = y.mean()
    w = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]),
                        Z.T @ (y - b0))
    return mu, sd, b0, w


def ridge_pred(model, X):
    mu, sd, b0, w = model
    return b0 + ((X - mu) / sd) @ w


def pick_lam(X, y, rs):
    """Inner 3-fold CV on TRAINING data only."""
    n = len(y)
    if n < 12:
        return 1.0
    order = rs.permutation(n)
    best, best_err = 1.0, np.inf
    for lam in LAM_GRID:
        errs = []
        for f in range(3):
            te = order[f::3]
            tr = np.setdiff1d(order, te)
            m = ridge_fit(X[tr], y[tr], lam)
            errs.append(float(np.abs(ridge_pred(m, X[te]) - y[te]).mean()))
        e = float(np.mean(errs))
        if e < best_err:
            best, best_err = lam, e
    return best


def main():
    t0 = time.time()
    print(f"  world: {POP:,} @ {SEED}, {DAYS} no-news days", flush=True)
    w = birth_world(POP, SEED)
    rng = np.random.default_rng(SEED)
    for d in range(DAYS):
        live_one_day(w, rng)
        if (d + 1) % 100 == 0:
            print(f"    day {d+1}  ({time.time()-t0:.0f}s)", flush=True)
    civ = w.civ

    X = {"legacy": _build_features(civ, extended=True),
         "living": living_features(w)}
    n_static = X["legacy"].shape[1]
    names_liv = list(LIVING_FEATURES)

    c2i = {c: i for i, c in enumerate(GENESIS_COUNTRY_CODES)}
    cells = []
    for r in csv.DictReader(open(ROOT / "data/wvs_w7_cohort_by_country.csv")):
        ci = c2i.get(ISO3_TO_ISO2.get(r["country"]))
        if ci is None:
            continue
        m = (civ.country == ci) & np.isin(civ.age_bucket,
                                          BUCKETS[r["age_bucket"]])
        if m.sum() < 20:
            continue
        cells.append({"q": r["qcode"], "c": ci, "b": r["age_bucket"],
                      "y": float(r["yes_weighted"]),
                      "leg": X["legacy"][m].mean(axis=0),
                      "liv": X["living"][m].mean(axis=0)})
    print(f"  cells: {len(cells)}", flush=True)

    def run_arm(fkey, estimator, drop=None):
        def feats(cell):
            v = cell[fkey]
            return np.delete(v, drop) if drop is not None else v
        qs = sorted({c["q"] for c in cells})
        countries = sorted({c["c"] for c in cells})
        maes, nat_maes = [], []
        cal_p, cal_y = [], []
        grad_ok = grad_n = 0
        wnum = wden = 0.0
        pair = {}
        for seed in CV_SEEDS:
            rs = np.random.default_rng(seed)
            order = rs.permutation(len(countries))
            for f in range(FOLDS):
                test_c = {countries[i] for i in order[f::FOLDS]}
                for q in qs:
                    tr = [c for c in cells if c["q"] == q
                          and c["c"] not in test_c]
                    te = [c for c in cells if c["q"] == q
                          and c["c"] in test_c]
                    if len(tr) < 30 or not te:
                        continue
                    Xt = np.array([feats(c) for c in tr])
                    yt = logit(np.clip(np.array([c["y"] for c in tr]),
                                       .02, .98))
                    Xs = np.array([feats(c) for c in te])
                    ys = np.array([c["y"] for c in te])
                    if estimator == "flat":
                        m = ridge_fit(Xt, yt, 1.0)
                        p = sigmoid(ridge_pred(m, Xs))
                    else:
                        # hierarchical: between on country means,
                        # within on demeaned; lambdas from inner CV
                        cs_tr = sorted({c["c"] for c in tr})
                        cmap = {}
                        for c in tr:
                            cmap.setdefault(c["c"], []).append(c)
                        Xb = np.array([np.mean([feats(c) for c in v], 0)
                                       for v in cmap.values()])
                        yb = np.array([logit(np.clip(
                            np.mean([c["y"] for c in v]), .02, .98))
                            for v in cmap.values()])
                        lam_b = pick_lam(Xb, yb, np.random.default_rng(
                            seed * 7 + f))
                        mb = ridge_fit(Xb, yb, lam_b)
                        # within: demeaned features -> demeaned logit
                        Xw, yw = [], []
                        for v in cmap.values():
                            fm = np.mean([feats(c) for c in v], 0)
                            ym = np.mean([logit(np.clip(c["y"], .02, .98))
                                          for c in v])
                            for c in v:
                                Xw.append(feats(c) - fm)
                                yw.append(logit(np.clip(c["y"], .02, .98))
                                          - ym)
                        Xw, yw = np.array(Xw), np.array(yw)
                        lam_w = pick_lam(Xw, yw, np.random.default_rng(
                            seed * 13 + f))
                        mw = ridge_fit(Xw, yw, lam_w)
                        # predict: country mean part + within part
                        te_map = {}
                        for c in te:
                            te_map.setdefault(c["c"], []).append(c)
                        p = np.zeros(len(te))
                        for ci2, v in te_map.items():
                            fm = np.mean([feats(c) for c in v], 0)
                            base = ridge_pred(mb, fm[None, :])[0]
                            for c in v:
                                j = te.index(c)
                                dev = ridge_pred(
                                    mw, (feats(c) - fm)[None, :])[0]
                                p[j] = sigmoid(base + dev)
                    maes.append(float(np.abs(p - ys).mean()) * 100)
                    cal_p.extend(p.tolist()); cal_y.extend(ys.tolist())
                    per = {}
                    for c, pi in zip(te, p):
                        per.setdefault(c["c"], {})[c["b"]] = (c["y"], pi)
                        pair[(seed, q, c["c"], c["b"])] = (c["y"], pi)
                    for ci2, bb in per.items():
                        if "18_29" in bb and "60_plus" in bb:
                            ty = bb["60_plus"][0] - bb["18_29"][0]
                            pp2 = bb["60_plus"][1] - bb["18_29"][1]
                            if abs(ty) > 0.01:
                                grad_n += 1
                                grad_ok += int(np.sign(ty) == np.sign(pp2))
                        ya = np.array([v[0] for v in bb.values()])
                        pa = np.array([v[1] for v in bb.values()])
                        if len(ya) >= 3:
                            wnum += float((((ya - ya.mean())
                                            - (pa - pa.mean()))**2).sum())
                            wden += float(((ya - ya.mean())**2).sum())
                    # national: population of cells per held-out country
                    for ci2, bb in per.items():
                        ya = np.mean([v[0] for v in bb.values()])
                        pa = np.mean([v[1] for v in bb.values()])
                        nat_maes.append(abs(ya - pa) * 100)
        cal = float(np.polyfit(np.array(cal_p), np.array(cal_y), 1)[0])
        return {"cohort_mae_pp": round(float(np.mean(maes)), 3),
                "cohort_mae_sd": round(float(np.std(maes)), 3),
                "national_mae_pp": round(float(np.mean(nat_maes)), 3),
                "gradient_pct": round(100 * grad_ok / max(grad_n, 1), 1),
                "calibration": round(cal, 3),
                "within_r2": round(1 - wnum / max(wden, 1e-9), 4)}, pair

    arms, pairs = {}, {}
    for label, fkey, est in (("legacy_flat", "leg", "flat"),
                             ("living_flat", "liv", "flat"),
                             ("legacy_hier", "leg", "hier"),
                             ("living_hier", "liv", "hier")):
        arms[label], pairs[label] = run_arm(fkey, est)
        print(f"  {label}: {arms[label]}", flush=True)

    def paired_delta(a, b):
        ks = set(pairs[a]) & set(pairs[b])
        d = np.array([abs(pairs[a][k][0] - pairs[a][k][1])
                      - abs(pairs[b][k][0] - pairs[b][k][1])
                      for k in ks]) * 100
        return {"n": len(d), "mean_pp": round(float(d.mean()), 4),
                "b_wins_pct": round(100 * float((d > 0).mean()), 1)}

    deltas = {"living_vs_legacy_flat": paired_delta("legacy_flat",
                                                    "living_flat"),
              "living_vs_legacy_hier": paired_delta("legacy_hier",
                                                    "living_hier"),
              "hier_vs_flat_legacy": paired_delta("legacy_flat",
                                                  "legacy_hier")}

    abl = {}
    for fam, members in FAMILIES.items():
        cols = [n_static + names_liv.index(m) for m in members]
        r, _ = run_arm("liv", "hier", drop=cols)
        abl[fam] = {"cohort_mae_pp": r["cohort_mae_pp"],
                    "delta_L": round(r["cohort_mae_pp"]
                                     - arms["living_hier"]["cohort_mae_pp"],
                                     3)}   # positive = channel helps
        print(f"  ablate {fam}: dL={abl[fam]['delta_L']}", flush=True)

    out = {"iteration": 2, "NOT_BENCHMARK_A": True,
           "holdout_touched": False,
           "iteration1_immutable": "b0c00a4",
           "admissibility": ADMISSIBILITY,
           "protocol": {"pop": POP, "seed": SEED, "days": DAYS,
                        "folds": FOLDS, "cv_seeds": list(CV_SEEDS),
                        "lambda_grid": list(LAM_GRID),
                        "cells": len(cells)},
           "arms": arms, "paired_deltas": deltas,
           "family_ablations_deltaL_positive_helps": abl,
           "provenance": {"host": os.uname().nodename,
                          "commit": subprocess.run(
                              ["git", "rev-parse", "HEAD"],
                              capture_output=True, text=True,
                              cwd=ROOT).stdout.strip(),
                          "wall_clock": time.strftime(
                              "%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                          "runtime_s": round(time.time() - t0, 1)}}
    (ROOT / "data" / "living_readout_iter2.json").write_text(
        json.dumps(out, indent=1))
    print(json.dumps({"arms": arms, "paired": deltas}, indent=1))
    print("DONE-ITER2")


if __name__ == "__main__":
    main()
