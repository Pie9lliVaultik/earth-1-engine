"""HYBRID: does Earth-1's agent structure add anything ON TOP of MrsP?

Prereg: data/hybrid_test_prereg.json — registered expectation is NO
GAIN, and a positive result must be checked for smuggled target
information before it is believed.

Arms (identical pinned folds, identical nesting — hyperparameters
selected by inner LOO inside train only):
  A  MrsP alone            context covariates
  B  MrsP + engine         context covariates + Earth-1's country
                           prediction as one extra covariate
  C  engine alone          the standing 10.59pp path, for reference

LEAK GUARD (mandatory, from the prereg): the engine covariate for a
held-out country is produced by calibration fitted on TRAIN countries
only — the held-out country's target never enters its own predictor.
Env: HY_POP (default 200000).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.benchmark import _goqa_prepare_tasks
from earth1.calibration import (_build_features, _get_country_index,
                                calibrate_single)
from earth1.genesis import genesis
from earth1.rng import logit, sigmoid
from scripts.mrp_baseline import build_context, fit_mrsp, LAMBDAS, TAUS

POP = int(os.environ.get("HY_POP", "200000"))


def select_and_fit(X, y):
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd = np.where(sd > 1e-9, sd, 1.0)
    Xs = (X - mu) / sd
    best, best_err = (LAMBDAS[0], TAUS[0]), np.inf
    for lam in LAMBDAS:
        for tau in TAUS:
            errs = []
            for i in range(len(y)):
                k = np.arange(len(y)) != i
                b = fit_mrsp(Xs[k], y[k], lam, tau)
                errs.append((y[i] - (b[0] + Xs[i] @ b[1:])) ** 2)
            e = float(np.mean(errs))
            if e < best_err:
                best, best_err = (lam, tau), e
    return fit_mrsp(Xs, y, *best), mu, sd


def main() -> None:
    civ = genesis(POP, 42)
    c2i, codes = _get_country_index(civ)
    feats = _build_features(civ, extended=True)
    gt = json.load(open("data/benchmark/goqa_ground_truth.json"))
    ctx, cells, _ = build_context(civ, codes)
    os.environ.setdefault("EARTH1_PINNED_FOLDS", "data/cv_folds.json")
    tasks = _goqa_prepare_tasks(civ, gt, set(codes), 5, 42)

    err = {"mrsp": [], "hybrid": [], "engine": [], "naive": []}
    for t in tasks:
        if t["test_codes"] is None:
            continue
        ct = {c: v for c, v in t["ct"].items() if c in ctx and c in cells}
        test = [c for c in t["test_codes"] if c in ct]
        train = [c for c in ct if c not in set(test)]
        if len(train) < 8 or not test:
            continue
        g = float(t["global_yes"])
        bl = logit(np.array([g]))[0]
        # LEAK GUARD: engine weights fitted on TRAIN countries only
        w_eng = calibrate_single(civ, g, {c: ct[c] for c in train},
                                 extended=True)
        if not np.any(w_eng):
            continue
        # engine covariate must be OUT-OF-SAMPLE for every row it is
        # fitted against, else beta is learned on an optimistic version
        # of the predictor and applied to a pessimistic one at test.
        # Train rows: leave-one-country-out within train. Test rows:
        # the train-fitted weights (already out-of-sample).
        eng_pred = {}
        for c in train:
            sub = {k: ct[k] for k in train if k != c}
            w_loo = calibrate_single(civ, g, sub, extended=True)
            m = civ.country == c2i[c]
            eng_pred[c] = float(sigmoid(bl + feats[m] @ w_loo).mean()
                                ) if np.any(w_loo) else g
        for c in test:
            m = civ.country == c2i[c]
            eng_pred[c] = float(sigmoid(bl + feats[m] @ w_eng).mean())
        y = np.array([logit(np.array([ct[c]]))[0] - bl for c in train])
        Xa = np.array([ctx[c] for c in train])
        Xb = np.array([np.concatenate([ctx[c], [logit(
            np.array([min(max(eng_pred[c], 1e-3), 1 - 1e-3)]))[0] - bl]])
            for c in train])
        ba, mua, sda = select_and_fit(Xa, y)
        bb, mub, sdb = select_and_fit(Xb, y)
        for c in test:
            xa = (ctx[c] - mua) / sda
            pa = float(sigmoid(np.array([bl + ba[0] + xa @ ba[1:]]))[0])
            xb_raw = np.concatenate([ctx[c], [logit(np.array(
                [min(max(eng_pred[c], 1e-3), 1 - 1e-3)]))[0] - bl]])
            xb = (xb_raw - mub) / sdb
            pb = float(sigmoid(np.array([bl + bb[0] + xb @ bb[1:]]))[0])
            err["mrsp"].append(abs(pa - ct[c]))
            err["hybrid"].append(abs(pb - ct[c]))
            err["engine"].append(abs(eng_pred[c] - ct[c]))
            err["naive"].append(abs(g - ct[c]))

    out = {"pop": POP, "n": len(err["mrsp"]),
           **{k: float(np.mean(v)) for k, v in err.items()}}
    json.dump(out, open("data/hybrid_mrp_engine.json", "w"), indent=1)
    for k in ("mrsp", "hybrid", "engine", "naive"):
        print(f"  {k:7s} CV MAE {out[k]:.4f}", flush=True)
    d = (out["mrsp"] - out["hybrid"]) * 100
    print(f"HYBRID-VERDICT: engine covariate on top of MrsP {d:+.2f}pp "
          f"(positive = agents add something), n={out['n']}", flush=True)


if __name__ == "__main__":
    main()
