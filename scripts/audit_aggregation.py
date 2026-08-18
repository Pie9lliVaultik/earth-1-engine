"""Aggregation audit — two measurements on the frozen engine.

F1: Does the agent population help the GOQA headline number, or hurt it?
    Compares mean(sigmoid(z_i)) over the full country sub-population
    against sigmoid(z_bar) — one mean agent per country, same weights.

F2: How large is CV-fold noise relative to the ladder's scale gains?
    Same rung, different CV fold seeds.

No new mechanisms; pure measurement on the frozen physics.
Usage:  python3 scripts/audit_aggregation.py [--pop 200000] [--seeds 42,43]
"""
from __future__ import annotations

import argparse
import json

import numpy as np

from earth1.benchmark import ISO3_TO_ISO2
from earth1.calibration import (_build_features, _get_country_index,
                                calibrate_single, calibrate_single_aggregated)
from earth1.genesis import genesis
from earth1.rng import logit, sigmoid

GT_PATH = "data/benchmark/goqa_ground_truth.json"


def _targets(q, code_to_idx):
    out = {}
    for iso3, dist in q["countries"].items():
        iso2 = ISO3_TO_ISO2.get(iso3)
        if iso2 and iso2 in code_to_idx:
            out[iso2] = dist["yes"]
    return out


def run(civ, gt, cv_seed, ridge_alpha=0.1, extended=True, min_agents=10,
        estimator="production"):
    if estimator == "aggregated":
        fit = lambda civ, g, tr: calibrate_single_aggregated(
            civ, g, tr, ridge_alpha=0.01, extended=extended)
    else:
        fit = lambda civ, g, tr: calibrate_single(
            civ, g, tr, ridge_alpha=ridge_alpha, extended=extended)
    code_to_idx, _ = _get_country_index(civ)
    feats = _build_features(civ, extended=extended)
    rng = np.random.RandomState(cv_seed)

    agent_err, mean_err, naive_err, jensen = [], [], [], []

    for q in gt:
        ct = _targets(q, code_to_idx)
        if len(ct) < 6:
            continue
        g = float(np.mean(list(ct.values())))
        bl = logit(np.array([g]))[0]

        codes = [c for c in ct
                 if (civ.country == code_to_idx[c]).sum() >= min_agents]
        if len(codes) < 6:
            continue
        rng.shuffle(codes)
        k = max(1, len(codes) // 3)
        test = codes[:k]
        train = {c: ct[c] for c in codes if c not in test}

        w = fit(civ, g, train)

        for c in test:
            mask = civ.country == code_to_idx[c]
            z = bl + feats[mask] @ w
            p_agents = float(sigmoid(z).mean())
            p_mean = float(sigmoid(np.array([z.mean()]))[0])
            agent_err.append(abs(p_agents - ct[c]))
            mean_err.append(abs(p_mean - ct[c]))
            naive_err.append(abs(g - ct[c]))
            jensen.append(p_agents - p_mean)

    return {
        "n_cells": len(agent_err),
        "cv_mae_agents": round(float(np.mean(agent_err)), 5),
        "cv_mae_mean_agent": round(float(np.mean(mean_err)), 5),
        "cv_mae_naive": round(float(np.mean(naive_err)), 5),
        "delta_pp": round(float((np.mean(mean_err) - np.mean(agent_err)) * 100), 3),
        "jensen_gap_mean_abs": round(float(np.abs(jensen).mean()), 5),
        "jensen_gap_p90": round(float(np.percentile(np.abs(jensen), 90)), 5),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pop", type=int, default=200000)
    ap.add_argument("--genesis-seed", type=int, default=42)
    ap.add_argument("--cv-seeds", type=str, default="42,7,13")
    ap.add_argument("--estimator", type=str, default="production")
    ap.add_argument("--out", type=str, default="data/audit_aggregation.json")
    args = ap.parse_args()

    gt = json.load(open(GT_PATH))
    civ = genesis(pop=args.pop, seed=args.genesis_seed)

    rows = []
    for s in [int(x) for x in args.cv_seeds.split(",")]:
        r = run(civ, gt, s, estimator=args.estimator)
        r["cv_seed"] = s
        rows.append(r)
        print(f"cv_seed={s:>3}  agents {r['cv_mae_agents']:.4f}  "
              f"mean-agent {r['cv_mae_mean_agent']:.4f}  "
              f"delta {r['delta_pp']:+.2f}pp  "
              f"jensen |mean| {r['jensen_gap_mean_abs']:.4f}")

    maes = [r["cv_mae_agents"] for r in rows]
    fold_spread = (max(maes) - min(maes)) * 100
    print(f"\nF1  population effect: {np.mean([r['delta_pp'] for r in rows]):+.2f}pp "
          f"(negative = agents HURT vs one mean agent)")
    print(f"F2  CV-fold spread at fixed scale: {fold_spread:.2f}pp "
          f"(compare to ladder's 0.21pp claimed scale gain)")

    payload = {
        "pop": args.pop,
        "genesis_seed": args.genesis_seed,
        "rows": rows,
        "fold_spread_pp": round(float(fold_spread), 3),
    }
    with open(args.out, "w") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
