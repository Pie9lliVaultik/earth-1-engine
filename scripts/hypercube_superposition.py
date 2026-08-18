"""THE HYPERCUBE AS PREDICTION SUBSTRATE — point agents vs superposed.

Pietro's thesis: an agent should not be a point in one cube cell; it
should occupy a SUPERPOSITION across cells, and the answer to a
question is the collapse of that superposition.

This is the first empirical test of it, on historical data, at cell
resolution (where within-country structure is the graded quantity —
data/wvs_w7_cohort_by_country.csv, real microdata).

Three readouts of the same population, same calibration, same forces:
  A HARD   — agent belongs to exactly one cell (current engine)
  B SOFT   — agent has membership weights across neighbouring cells
             (Gaussian in normalized age; superposition of demography)
  C SOFT+  — B, plus stance uncertainty: each agent contributes a
             distribution over answers (logit +/- sigma) instead of a
             point estimate, so the cell readout is a mixture rather
             than a mean of points (superposition of opinion)

Scored against real cells: bucket MAE + age-gradient direction.
Cell coordinates are age x education — both gate-clean, neither a
benchmark item.
Env: HC_POP (default 200000), HC_SIGMA (stance spread, default 0.6),
     HC_TAU (age membership width in buckets, default 0.6).
"""
from __future__ import annotations

import csv
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.benchmark import ISO3_TO_ISO2
from earth1.calibration import calibrate_single, _get_country_index
from earth1.engine import run_question
from earth1.genesis import genesis
from earth1.rng import logit, sigmoid
from earth1.types import Question

POP = int(os.environ.get("HC_POP", "200000"))
SIGMA = float(os.environ.get("HC_SIGMA", "0.6"))
TAU = float(os.environ.get("HC_TAU", "0.6"))
BUCKETS = ["18_29", "30_44", "45_59", "60_plus"]
BUCKET_CENTER = np.array([0.0, 1.0, 2.0, 3.0])
MIN_AGENTS = 30


def main() -> None:
    civ = genesis(POP, 42)
    code_to_idx, _ = _get_country_index(civ)
    gt = {q["id"]: q for q in
          json.load(open("data/benchmark/goqa_ground_truth.json"))}
    cells = {}
    for r in csv.DictReader(open("data/wvs_w7_cohort_by_country.csv")):
        i2 = ISO3_TO_ISO2.get(r["country"])
        if i2:
            cells.setdefault(r["qcode"], {}).setdefault(
                i2, {})[r["age_bucket"]] = float(r["yes_weighted"])

    # continuous age position in bucket space (0..3) for soft membership
    age_years = 18.0 + civ.age * 72.0
    pos = np.interp(age_years, [23.5, 37.0, 52.0, 68.0], [0.0, 1.0, 2.0, 3.0])

    res = {k: {"err": [], "gh": 0, "gn": 0} for k in ("hard", "soft", "soft+")}
    for qcode, by_cc in cells.items():
        if qcode not in gt:
            continue
        q = gt[qcode]
        ct = {ISO3_TO_ISO2[c]: d["yes"] for c, d in q["countries"].items()
              if c in ISO3_TO_ISO2}
        g = q["global_yes_popweighted"]
        w = calibrate_single(civ, g, ct)
        if not np.any(w):
            continue
        r = run_question(Question(id=qcode, text=q["text"],
                                  domain="belief_causal", baseline=g,
                                  weights=w, lens="wvs"), civ)
        s = np.clip(r.settled_stances, 1e-4, 1 - 1e-4)
        z = logit(s)
        for cc, obs in by_cc.items():
            if len(obs) < 4 or cc not in code_to_idx:
                continue
            cm = civ.country == code_to_idx[cc]
            if cm.sum() < MIN_AGENTS * 4:
                continue
            preds = {"hard": {}, "soft": {}, "soft+": {}}
            for i, b in enumerate(BUCKETS):
                hard_m = cm & ((civ.age_bucket == i) if i < 3
                               else (civ.age_bucket >= 3))
                if hard_m.sum() >= MIN_AGENTS:
                    preds["hard"][b] = float(s[hard_m].mean())
                # SOFT: every agent in the country contributes with a
                # membership weight — the agent is IN several cells at once
                wts = np.exp(-0.5 * ((pos[cm] - BUCKET_CENTER[i]) / TAU) ** 2)
                if wts.sum() > 1e-6:
                    preds["soft"][b] = float(
                        np.average(s[cm], weights=wts))
                    # SOFT+: each agent is a distribution over answers;
                    # E[sigmoid(z + eps)] via 5-point Gauss-Hermite
                    nodes = np.array([-2.02, -0.959, 0.0, 0.959, 2.02])
                    gw = np.array([0.0199, 0.3936, 0.9453, 0.3936, 0.0199])
                    gw = gw / gw.sum()
                    mix = np.zeros(cm.sum())
                    for nd, gwt in zip(nodes, gw):
                        mix += gwt * sigmoid(z[cm] + SIGMA * nd)
                    preds["soft+"][b] = float(np.average(mix, weights=wts))
            for k in res:
                p = preds[k]
                if len(p) == 4:
                    for b in BUCKETS:
                        res[k]["err"].append(abs(p[b] - obs[b]))
                    og = np.sign(obs["18_29"] - obs["60_plus"])
                    eg = np.sign(p["18_29"] - p["60_plus"])
                    if og != 0:
                        res[k]["gn"] += 1
                        res[k]["gh"] += int(og == eg)

    out = {"pop": POP, "sigma": SIGMA, "tau": TAU}
    for k, v in res.items():
        out[k] = {"cell_mae": float(np.mean(v["err"])) if v["err"] else None,
                  "gradient": f"{v['gh']}/{v['gn']}",
                  "gradient_acc": v["gh"] / v["gn"] if v["gn"] else None,
                  "n_cells": len(v["err"])}
        o = out[k]
        print(f"  {k:6s} cell-MAE {o['cell_mae']:.4f} | gradient "
              f"{o['gradient']} ({o['gradient_acc']:.2f}) | "
              f"{o['n_cells']} cells", flush=True)
    json.dump(out, open("data/hypercube_superposition.json", "w"), indent=1)
    d = (out["hard"]["cell_mae"] - out["soft+"]["cell_mae"]) * 100
    print(f"HYPERCUBE-VERDICT: superposition vs point agents "
          f"{d:+.2f}pp cell-MAE (positive = superposition better)",
          flush=True)


if __name__ == "__main__":
    main()
