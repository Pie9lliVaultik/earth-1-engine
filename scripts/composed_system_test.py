"""THE COMPOSED SYSTEM — MrsP owns levels, Earth-1 owns shape.

First test of the architecture on the distributional ruler. Three
readouts of the same held-out cells (real WVS7 within-cell densities):

  ENGINE   engine stances as-is (own level, own shape)
  MRSP     MrsP level with NO within-country structure (every agent at
           the country estimate — a spike density)
  COMPOSED engine's within-country shape, re-anchored so the country
           mean equals the MrsP estimate

Registered expectation (stated before running): COMPOSED beats both —
ENGINE because its levels are worse, MRSP because a spike cannot match
a real density. If COMPOSED does not beat ENGINE, the level error was
not what was hurting the distributional score and the composition buys
nothing on shape.

All levels are produced by MrsP fitted on TRAIN countries only; every
scored cell belongs to a held-out country.
Env: CS_POP (default 200000).
"""
from __future__ import annotations
import os as _os  # LEGACY_COMPARISON_ONLY script: explicit opt-in
_os.environ.setdefault("EARTH1_LEGACY_COMPARISON", "1")

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.legacy_benchmark import _goqa_prepare_tasks
from earth1.calibration import (_build_features, _get_country_index,
                                calibrate_single)
from earth1.genesis import genesis
from earth1.mrsp_seed import compose
from earth1.rng import logit, sigmoid
from scripts.mrp_baseline import build_context, fit_mrsp, LAMBDAS, TAUS

POP = int(os.environ.get("CS_POP", "200000"))
MIN_AGENTS = 40
EDGES = np.linspace(0.0, 1.0, 11)


def w1(p, q):
    return float(np.abs(np.cumsum(p) - np.cumsum(q)).sum() / (len(p) - 1))


def hist_from(v):
    h, _ = np.histogram(np.clip(v, 0, 1), bins=EDGES)
    t = h.sum()
    return h / t if t > 0 else np.full(10, 0.1)


def select_and_fit(X, y):
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd = np.where(sd > 1e-9, sd, 1.0)
    Xs = (X - mu) / sd
    best, be = (LAMBDAS[0], TAUS[0]), np.inf
    for lam in LAMBDAS:
        for tau in TAUS:
            e = float(np.mean([
                (y[i] - (lambda b: b[0] + Xs[i] @ b[1:])(
                    fit_mrsp(Xs[np.arange(len(y)) != i],
                             y[np.arange(len(y)) != i], lam, tau))) ** 2
                for i in range(len(y))]))
            if e < be:
                best, be = (lam, tau), e
    return fit_mrsp(Xs, y, *best), mu, sd


def main() -> None:
    civ = genesis(POP, 42)
    c2i, codes = _get_country_index(civ)
    feats = _build_features(civ, extended=True)
    gt = {q["id"]: q for q in
          json.load(open("data/benchmark/goqa_ground_truth.json"))}
    ctx, cells_w, _ = build_context(civ, codes)
    dens = json.load(open("data/cell_densities.json"))
    os.environ.setdefault("EARTH1_PINNED_FOLDS", "data/cv_folds.json")
    tasks = {t["id"]: t for t in _goqa_prepare_tasks(
        civ, list(gt.values()), set(codes), 5, 42)}

    err = {"engine": [], "mrsp": [], "composed": []}
    for qcode, cs in dens.items():
        t = tasks.get(qcode)
        if t is None or t["test_codes"] is None:
            continue
        ct = {c: v for c, v in t["ct"].items() if c in ctx}
        test = [c for c in t["test_codes"] if c in ct]
        train = [c for c in ct if c not in set(test)]
        if len(train) < 8 or not test:
            continue
        g = float(t["global_yes"])
        bl = logit(np.array([g]))[0]
        w_eng = calibrate_single(civ, g, {c: ct[c] for c in train},
                                 extended=True)
        if not np.any(w_eng):
            continue
        s_eng = sigmoid(bl + feats @ w_eng)
        y = np.array([logit(np.array([ct[c]]))[0] - bl for c in train])
        X = np.array([ctx[c] for c in train])
        beta, mu, sd = select_and_fit(X, y)
        level = {}
        for c in test:
            x = (ctx[c] - mu) / sd
            level[c] = float(sigmoid(np.array([bl + beta[0] + x @ beta[1:]]))[0])
        s_comp = compose(s_eng, civ.country, c2i, level)
        for key, cell in cs.items():
            cc, a, e = key.split("|")
            if cc not in test or cc not in c2i:
                continue
            a, e = int(a), int(e)
            m = ((civ.country == c2i[cc]) & (civ.education == e)
                 & ((civ.age_bucket == a) if a < 3 else (civ.age_bucket >= 3)))
            if m.sum() < MIN_AGENTS:
                continue
            obs = np.array(cell["hist"])
            err["engine"].append(w1(hist_from(s_eng[m]), obs))
            err["composed"].append(w1(hist_from(s_comp[m]), obs))
            err["mrsp"].append(w1(hist_from(
                np.full(m.sum(), level[cc])), obs))

    out = {"pop": POP, "n_cells": len(err["engine"]),
           **{k: float(np.mean(v)) if v else None for k, v in err.items()}}
    json.dump(out, open("data/composed_system_test.json", "w"), indent=1)
    for k in ("engine", "mrsp", "composed"):
        print(f"  {k:9s} W1 {out[k]:.4f}", flush=True)
    print(f"COMPOSED-VERDICT: vs engine {100*(out['engine']-out['composed']):+.2f}pp"
          f" | vs mrsp-alone {100*(out['mrsp']-out['composed']):+.2f}pp "
          f"({out['n_cells']} held-out cells)", flush=True)


if __name__ == "__main__":
    main()
