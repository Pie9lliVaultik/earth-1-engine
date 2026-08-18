"""Does the ported readout beat sigmoid-mean on shape AND on levels?

Compares, on held-out cells against real WVS7 within-cell densities:
  MEAN      current readout: sigmoid(...).mean() per cell
  COUNT     counting vote: fraction of agents above the centered zero
  BORN      coherence readout R_yes^2/(R_yes^2+R_no^2)
plus, on the country level (GOQA targets), the same three.

Also reports the camp diagnostic distribution: how many questions are
'manifold_native' (population contributing) vs 'grounding_dependent'
(population decorating) — the classification Earth-1 has never had.
Env: RC_POP (default 200000).
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
from earth1.readout import (born_probability, camp_diagnostic,
                            counting_vote, resultant_length)
from earth1.rng import logit, sigmoid

POP = int(os.environ.get("RC_POP", "200000"))
MIN_AGENTS = 40
EDGES = np.linspace(0.0, 1.0, 11)


def w1(p, q):
    return float(np.abs(np.cumsum(p) - np.cumsum(q)).sum() / (len(p) - 1))


def hist_from(v):
    h, _ = np.histogram(np.clip(v, 0, 1), bins=EDGES)
    t = h.sum()
    return h / t if t > 0 else np.full(10, 0.1)


def main() -> None:
    civ = genesis(POP, 42)
    c2i, codes = _get_country_index(civ)
    feats = _build_features(civ, extended=True)
    gt = {q["id"]: q for q in
          json.load(open("data/benchmark/goqa_ground_truth.json"))}
    dens = json.load(open("data/cell_densities.json"))
    os.environ.setdefault("EARTH1_PINNED_FOLDS", "data/cv_folds.json")
    tasks = {t["id"]: t for t in _goqa_prepare_tasks(
        civ, list(gt.values()), set(codes), 5, 42)}

    w1s = {"mean": [], "count": [], "born": []}
    lvl = {"mean": [], "count": [], "born": [], "naive": []}
    regimes = {}
    for qid, t in tasks.items():
        if t["test_codes"] is None:
            continue
        ct = t["ct"]
        test = [c for c in t["test_codes"] if c in c2i]
        train = {c: v for c, v in ct.items() if c not in set(test)}
        if len(train) < 8 or not test:
            continue
        g = float(t["global_yes"])
        bl = logit(np.array([g]))[0]
        w = calibrate_single(civ, g, train, extended=True)
        if not np.any(w):
            continue
        z = bl + feats @ w
        s = sigmoid(z)
        d = camp_diagnostic(civ.forces, s)
        regimes[qid] = d["regime"]
        for c in test:
            m = civ.country == c2i[c]
            if m.sum() < MIN_AGENTS:
                continue
            lvl["mean"].append(abs(float(s[m].mean()) - ct[c]))
            # centered by the GLOBAL population mean (as the old engine
            # did), not within the country — centering per group forces
            # ~50% by construction and destroys level information
            lvl["count"].append(abs(counting_vote(
                z[m] - z.mean(), center=False) - ct[c]))
            lvl["born"].append(
                abs(born_probability(civ.forces[m], s[m]) - ct[c]))
            lvl["naive"].append(abs(g - ct[c]))
        for key, cell in dens.get(qid, {}).items():
            cc, a, e = key.split("|")
            if cc not in test or cc not in c2i:
                continue
            a, e = int(a), int(e)
            m = ((civ.country == c2i[cc]) & (civ.education == e)
                 & ((civ.age_bucket == a) if a < 3 else (civ.age_bucket >= 3)))
            if m.sum() < MIN_AGENTS:
                continue
            obs = np.array(cell["hist"])
            w1s["mean"].append(w1(hist_from(s[m]), obs))
            # counting readout as a density: each agent votes 0 or 1
            votes = (z[m] > z.mean()).astype(float)   # global centering
            w1s["count"].append(w1(hist_from(votes), obs))
            p = born_probability(civ.forces[m], s[m])
            hb = np.zeros(10)
            hb[-1], hb[0] = p, 1 - p
            w1s["born"].append(w1(hb, obs))

    out = {"pop": POP,
           "cell_w1": {k: float(np.mean(v)) for k, v in w1s.items() if v},
           "country_mae": {k: float(np.mean(v)) for k, v in lvl.items() if v},
           "n_cells": len(w1s["mean"]), "n_country": len(lvl["mean"]),
           "regimes": {r: sum(1 for x in regimes.values() if x == r)
                       for r in set(regimes.values())}}
    json.dump(out, open("data/readout_comparison.json", "w"), indent=1)
    print("  cell W1:      " + " | ".join(
        f"{k} {v:.4f}" for k, v in out["cell_w1"].items()), flush=True)
    print("  country MAE:  " + " | ".join(
        f"{k} {v:.4f}" for k, v in out["country_mae"].items()), flush=True)
    print(f"  camp regimes: {out['regimes']} (of {len(regimes)} questions)",
          flush=True)


if __name__ == "__main__":
    main()
