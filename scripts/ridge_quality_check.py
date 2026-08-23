"""Ridge quality check (eleventh review point 3) — measurement only.

The review's charge: in-sample 10.17 ≈ CV 10.24 with 18 params on ~60
observations is the signature of accidental massive shrinkage
(alpha=0.1 on unstandardized ~0.05-magnitude features). Either honest
tuning grows the margin, or hidden fragility surfaces.

Three fitting regimes on IDENTICAL folds (same _goqa_prepare_tasks
RandomState draw as the production benchmark):

  V0  production replica: alpha=0.1, unstandardized, no intercept
      (sanity anchor — must reproduce the published CV number)
  V1  standardized columns + intercept, alpha=0.1
  V2  standardized + intercept + nested alpha (inner LOO on train fold)

No production code touched. Env: RQC_POP (default 200000).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.genesis import genesis
from earth1.legacy_benchmark import _goqa_prepare_tasks
from earth1.calibration import _build_features, _get_country_index
from earth1.rng import logit, sigmoid

POP = int(os.environ.get("RQC_POP", "200000"))
SEED = 42
# extended past 30 after the 200K run pegged 31/40 questions at the old
# grid max — production's effective standardized-space alpha is ~0.1/sd^2
# with sd~0.05, i.e. ~40+, outside the original grid entirely
ALPHA_GRID = [0.01, 0.1, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0, 3000.0]


def _fit(X, y, alpha, standardize):
    """Ridge fit. Returns (w, b, mu, sd) in the internal space used by
    _predict. Unstandardized regime: no intercept, raw solve (exact
    production replica of calibrate_single)."""
    n_feat = X.shape[1]
    if not standardize:
        XtX = X.T @ X + alpha * np.eye(n_feat)
        return np.linalg.solve(XtX, X.T @ y), 0.0, None, None
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd = np.where(sd > 1e-9, sd, 1.0)
    Xs = (X - mu) / sd
    yb = y.mean()
    XtX = Xs.T @ Xs + alpha * np.eye(n_feat)
    w = np.linalg.solve(XtX, Xs.T @ (y - yb))
    return w, yb, mu, sd


def _predict(feats_mask, baseline_logit, w, b, mu, sd):
    """Agent-level prediction, matching production's sigmoid-then-mean."""
    x = feats_mask if mu is None else (feats_mask - mu) / sd
    return float(sigmoid(baseline_logit + b + x @ w).mean())


def _nested_alpha(X, y):
    """Inner LOO over the train fold picks alpha."""
    best, best_err = ALPHA_GRID[0], np.inf
    n = len(y)
    for a in ALPHA_GRID:
        errs = []
        for i in range(n):
            keep = np.arange(n) != i
            w, b, mu, sd = _fit(X[keep], y[keep], a, True)
            x = (X[i] - mu) / sd
            errs.append((y[i] - (b + x @ w)) ** 2)
        e = float(np.mean(errs))
        if e < best_err:
            best, best_err = a, e
    return best


def main() -> None:
    civ = genesis(POP, SEED)
    goqa = json.load(open("data/benchmark/goqa_ground_truth.json"))
    code_to_idx, country_codes = _get_country_index(civ)
    features = _build_features(civ, extended=True)
    tasks = _goqa_prepare_tasks(civ, goqa, set(country_codes), 5, 42)

    cv = {"V0": [], "V1": [], "V2": []}
    cv_naive = []
    alphas_chosen = []
    for task in tasks:
        if task["test_codes"] is None:
            continue
        ct, test_codes = task["ct"], set(task["test_codes"])
        baseline = float(task["global_yes"])
        bl = logit(np.array([baseline]))[0]
        rows, ys, codes = [], [], []
        for code, target in ct.items():
            if code not in code_to_idx:
                continue
            mask = civ.country == code_to_idx[code]
            if mask.sum() < 10:
                continue
            rows.append(features[mask].mean(axis=0))
            ys.append(logit(np.array([target]))[0] - bl)
            codes.append(code)
        X, y = np.array(rows), np.array(ys)
        tr = np.array([c not in test_codes for c in codes])
        if tr.sum() < 3 or (~tr).sum() == 0:
            continue
        fits = {
            "V0": _fit(X[tr], y[tr], 0.1, False),
            "V1": _fit(X[tr], y[tr], 0.1, True),
        }
        a_star = _nested_alpha(X[tr], y[tr])
        alphas_chosen.append(a_star)
        fits["V2"] = _fit(X[tr], y[tr], a_star, True)
        for code in ct:
            if code not in test_codes or code not in code_to_idx:
                continue
            mask = civ.country == code_to_idx[code]
            if mask.sum() < 10:
                continue
            for v, (w, b, mu, sd) in fits.items():
                p = _predict(features[mask], bl, w, b, mu, sd)
                cv[v].append(abs(p - ct[code]))
            cv_naive.append(abs(baseline - ct[code]))

    out = {
        "pop": POP, "seed": SEED,
        "n_cv_pairs": len(cv_naive),
        "cv_mae": {v: float(np.mean(e)) for v, e in cv.items()},
        "cv_mae_naive": float(np.mean(cv_naive)),
        "alpha_histogram": {str(a): alphas_chosen.count(a)
                            for a in ALPHA_GRID},
    }
    with open("data/ridge_quality.json", "w") as f:
        json.dump(out, f, indent=1)
    m = out["cv_mae"]
    print(f"RIDGE-QUALITY: V0(replica) {m['V0']:.4f} | "
          f"V1(std) {m['V1']:.4f} | V2(std+alphaCV) {m['V2']:.4f} | "
          f"naive {out['cv_mae_naive']:.4f} | pairs {len(cv_naive)}",
          flush=True)


if __name__ == "__main__":
    main()
