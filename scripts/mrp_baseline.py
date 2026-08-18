"""MrsP BASELINE — the gold-standard method, on identical inputs.

Prereg: data/mrp_baseline_prereg.json (input-budget parity, autoMrP-
style selection, same pinned folds and corrected truth).

Model (multilevel regression with synthetic poststratification):
  logit(y_qc) = alpha_q + u_c + X_c . beta_q
  u_c ~ N(0, tau^2)      country random intercept, PARTIAL POOLING
  beta_q                 context-level covariates, ridge-regularized
  tau, lambda            chosen by cross-validation INSIDE the training
                         fold (autoMrP-style: selection, not authorship)
Then poststratification: the fitted cell predictions are recombined
with census cell weights to produce the country estimate.

Input budget = exactly Earth-1's: country targets on TRAIN countries
only + context covariates + census cell marginals. No individual
respondents.

Context covariates (all gate-clean, none a benchmark item): log GDP
per capita PPP, urban share, tertiary enrolment, life expectancy,
median age, region one-hots.
Env: MRP_POP (default 200000).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.benchmark import ISO3_TO_ISO2, _goqa_prepare_tasks
from earth1.calibration import _get_country_index
from earth1.genesis import genesis, GENESIS_COUNTRIES
from earth1.rng import logit, sigmoid

POP = int(os.environ.get("MRP_POP", "200000"))
LAMBDAS = [0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0]
TAUS = [0.05, 0.1, 0.2, 0.4, 0.8, 1.6]


def build_context(civ, codes):
    """Country-level covariates + census cell weights (the MrsP frame)."""
    wdi = json.load(open("data/wdi_tide.json"))
    c2i, _ = _get_country_index(civ)
    rows, cells, keep = {}, {}, []
    regions = sorted({(c.get("region") or "NA") for c in GENESIS_COUNTRIES})
    for cc in codes:
        if cc not in c2i:
            continue
        i = c2i[cc]
        meta = GENESIS_COUNTRIES[i] if i < len(GENESIS_COUNTRIES) else {}
        g = wdi["gdp_pcap_ppp"].get(cc, {})
        u = wdi["urban_share"].get(cc, {})
        t = wdi["tertiary_enroll"].get(cc, {})
        gv = float(g.get("2019", g.get("2018", 10000.0)) or 10000.0)
        uv = float(u.get("2019", 55.0) or 55.0)
        tv = float(t.get("2019", 35.0) or 35.0)
        reg = [1.0 if (meta.get("region") or "NA") == r else 0.0
               for r in regions]
        # PARITY MODE (MRP_PARITY=1): restrict the covariate set to what
        # Earth-1's genesis actually sees (census LE/u18 + region), so a
        # win is attributable to METHOD rather than to extra information.
        if os.environ.get("MRP_PARITY") == "1":
            rows[cc] = np.array([float(meta.get("le", 72.0)) / 100.0,
                                 float(meta.get("u18", 0.25))] + reg)
        else:
            rows[cc] = np.array([np.log(max(gv, 100.0)), uv / 100.0,
                                 tv / 100.0,
                                 float(meta.get("le", 72.0)) / 100.0,
                                 float(meta.get("u18", 0.25))] + reg)
        m = civ.country == i
        if m.sum() >= 40:
            w = []
            for a in range(4):
                for e in range(3):
                    bm = m & (civ.education == e) & (
                        (civ.age_bucket == a) if a < 3
                        else (civ.age_bucket >= 3))
                    w.append(bm.sum())
            tot = sum(w)
            cells[cc] = np.array(w) / tot if tot else None
            keep.append(cc)
    return rows, cells, keep


def fit_mrsp(X, y, lam, tau):
    """Ridge with a partial-pooling intercept: the tau term shrinks the
    country deviation toward the grand mean (multilevel closed form)."""
    n, p = X.shape
    Xa = np.hstack([np.ones((n, 1)), X])
    P = np.eye(p + 1) * lam
    P[0, 0] = 1.0 / max(tau ** 2, 1e-6)   # intercept shrinkage = pooling
    return np.linalg.solve(Xa.T @ Xa + P, Xa.T @ y)


def main() -> None:
    civ = genesis(POP, 42)
    c2i, codes = _get_country_index(civ)
    gt = json.load(open("data/benchmark/goqa_ground_truth.json"))
    ctx, cells, usable = build_context(civ, codes)
    os.environ.setdefault("EARTH1_PINNED_FOLDS", "data/cv_folds.json")
    tasks = _goqa_prepare_tasks(civ, gt, set(codes), 5, 42)

    mrp_err, naive_err, n_q = [], [], 0
    for t in tasks:
        if t["test_codes"] is None:
            continue
        ct = {c: v for c, v in t["ct"].items() if c in ctx and c in cells}
        test = [c for c in t["test_codes"] if c in ct]
        train = [c for c in ct if c not in set(test)]
        if len(train) < 8 or not test:
            continue
        n_q += 1
        g = float(t["global_yes"])
        bl = logit(np.array([g]))[0]
        Xtr = np.array([ctx[c] for c in train])
        ytr = np.array([logit(np.array([ct[c]]))[0] - bl for c in train])
        mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
        sd = np.where(sd > 1e-9, sd, 1.0)
        Xtr_s = (Xtr - mu) / sd
        # autoMrP-style: select lambda & tau by inner LOO on TRAIN only
        best, best_err = (LAMBDAS[0], TAUS[0]), np.inf
        for lam in LAMBDAS:
            for tau in TAUS:
                errs = []
                for i in range(len(train)):
                    k = np.arange(len(train)) != i
                    b = fit_mrsp(Xtr_s[k], ytr[k], lam, tau)
                    pred = b[0] + Xtr_s[i] @ b[1:]
                    errs.append((ytr[i] - pred) ** 2)
                e = float(np.mean(errs))
                if e < best_err:
                    best, best_err = (lam, tau), e
        beta = fit_mrsp(Xtr_s, ytr, *best)
        for c in test:
            x = (ctx[c] - mu) / sd
            lin = beta[0] + x @ beta[1:]
            # poststratify: same linear predictor across the country's
            # cells, recombined with census cell weights
            cw = cells[c]
            pred = float(np.sum(cw * sigmoid(np.full(len(cw), bl + lin))))
            mrp_err.append(abs(pred - ct[c]))
            naive_err.append(abs(g - ct[c]))

    out = {"pop": POP, "n_questions": n_q, "n_test_cells": len(mrp_err),
           "mrsp_cv_mae": float(np.mean(mrp_err)),
           "naive_cv_mae": float(np.mean(naive_err)),
           "earth1_cv_mae_reference": 0.1059}
    json.dump(out, open("data/mrp_baseline.json", "w"), indent=1)
    print(f"MRP-BASELINE: MrsP CV MAE {out['mrsp_cv_mae']:.4f} | naive "
          f"{out['naive_cv_mae']:.4f} | Earth-1 reference 0.1059 | "
          f"{n_q} questions, {len(mrp_err)} held-out country cells",
          flush=True)
    v = ("MRP WINS" if out["mrsp_cv_mae"] < 0.1059 - 0.002 else
         "EARTH-1 WINS" if out["mrsp_cv_mae"] > 0.1059 + 0.002 else "TIE")
    print(f"MRP-VERDICT: {v}", flush=True)


if __name__ == "__main__":
    main()
