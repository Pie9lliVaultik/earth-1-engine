"""0.4 CLOSURE RUN — three questions, frozen protocol, then the decision.

Nothing about the estimator, features, folds, seeds or protocol
changes here. The three already-defined closure questions:

  1. SEED STABILITY   hybrid_hier - legacy_hier per frozen seed; the
                      beneficial sign must hold on all three.
  2. HYBRID ABLATIONS the eight lived families ablated inside the
                      hybrid configuration (the arm we would ship).
  3. PERMUTATION      shuffle the living block within-country (bucket
                      correspondence destroyed, marginals and country
                      identity preserved, fixed seeds); the hybrid
                      advantage must vanish or materially collapse.

Cells come from the frozen cache written by the Iteration-2/3 run
(same 730-day admissible world). Estimator code is imported from the
frozen script — not re-implemented — so drift is impossible.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import importlib
it2 = importlib.import_module("scripts.living_readout_iter2")
from earth1.calibration import LIVING_FEATURES
from earth1.rng import logit, sigmoid

FOLDS, CV_SEEDS = it2.FOLDS, it2.CV_SEEDS
ridge_fit, ridge_pred, pick_lam = it2.ridge_fit, it2.ridge_pred, it2.pick_lam
N_STATIC = 18
NAMES_LIV = list(LIVING_FEATURES)
FAMILIES = it2.FAMILIES


def load_cells():
    z = np.load(ROOT / "data" / "iter2_cells_cache.npz", allow_pickle=True)
    return [{"q": str(q), "c": int(c), "b": str(b), "y": float(y),
             "leg": lg, "liv": lv}
            for q, c, b, y, lg, lv in zip(z["q"], z["c"], z["b"], z["y"],
                                          z["leg"], z["liv"])]


def run_hier(cells, fkey, within_key, drop=None):
    """The hierarchical arm, verbatim logic from the frozen script,
    returning per-(seed,q,c,b) predictions for paired analysis."""
    wkey = within_key

    def feats(cell):
        v = cell[fkey]
        return np.delete(v, drop) if drop is not None else v

    def wfeats(cell):
        v = cell[wkey]
        return np.delete(v, drop) if drop is not None else v

    qs = sorted({c["q"] for c in cells})
    countries = sorted({c["c"] for c in cells})
    maes = []
    pair = {}
    for seed in CV_SEEDS:
        rs = np.random.default_rng(seed)
        order = rs.permutation(len(countries))
        for f in range(FOLDS):
            test_c = {countries[i] for i in order[f::FOLDS]}
            for q in qs:
                tr = [c for c in cells if c["q"] == q
                      and c["c"] not in test_c]
                te = [c for c in cells if c["q"] == q and c["c"] in test_c]
                if len(tr) < 30 or not te:
                    continue
                cmap = {}
                for c in tr:
                    cmap.setdefault(c["c"], []).append(c)
                Xb = np.array([np.mean([feats(c) for c in v], 0)
                               for v in cmap.values()])
                yb = np.array([logit(np.clip(
                    np.mean([c["y"] for c in v]), .02, .98))
                    for v in cmap.values()])
                lam_b = pick_lam(Xb, yb, np.random.default_rng(seed*7+f))
                mb = ridge_fit(Xb, yb, lam_b)
                Xw, yw = [], []
                for v in cmap.values():
                    fm = np.mean([wfeats(c) for c in v], 0)
                    ym = np.mean([logit(np.clip(c["y"], .02, .98))
                                  for c in v])
                    for c in v:
                        Xw.append(wfeats(c) - fm)
                        yw.append(logit(np.clip(c["y"], .02, .98)) - ym)
                Xw, yw = np.array(Xw), np.array(yw)
                lam_w = pick_lam(Xw, yw, np.random.default_rng(seed*13+f))
                mw = ridge_fit(Xw, yw, lam_w)
                te_map = {}
                for c in te:
                    te_map.setdefault(c["c"], []).append(c)
                for ci2, v in te_map.items():
                    fm = np.mean([feats(c) for c in v], 0)
                    wm = np.mean([wfeats(c) for c in v], 0)
                    base = ridge_pred(mb, fm[None, :])[0]
                    for c in v:
                        dev = ridge_pred(mw,
                                         (wfeats(c) - wm)[None, :])[0]
                        p = float(sigmoid(base + dev))
                        maes.append(abs(p - c["y"]) * 100)
                        pair[(seed, q, c["c"], c["b"])] = (c["y"], p)
    return round(float(np.mean(maes)), 3), pair


def per_seed_delta(pa, pb):
    out = {}
    for seed in CV_SEEDS:
        ks = [k for k in pa if k[0] == seed and k in pb]
        d = np.array([abs(pa[k][0] - pa[k][1]) - abs(pb[k][0] - pb[k][1])
                      for k in ks]) * 100
        out[seed] = {"n": len(d), "mean_pp": round(float(d.mean()), 4),
                     "b_wins_pct": round(100 * float((d > 0).mean()), 1)}
    return out


def main():
    t0 = time.time()
    cells = load_cells()
    print(f"  cells: {len(cells)} (frozen cache)", flush=True)

    mae_leg, p_leg = run_hier(cells, "leg", "leg")
    mae_hyb, p_hyb = run_hier(cells, "leg", "liv")
    print(f"  legacy_hier {mae_leg} | hybrid_hier {mae_hyb}", flush=True)

    # 1 — seed stability
    seeds = per_seed_delta(p_leg, p_hyb)
    print("  per-seed Δ:", seeds, flush=True)

    # 2 — hybrid ablations
    abl = {}
    for fam, members in FAMILIES.items():
        cols = [N_STATIC + NAMES_LIV.index(m) for m in members]
        m_a, _ = run_hier(cells, "leg", "liv", drop=cols)
        abl[fam] = round(m_a - mae_hyb, 3)      # positive = channel helps
        print(f"  ablate {fam}: dL={abl[fam]:+.3f}", flush=True)

    # 3 — permutation control: within each country, permute the living
    # block across its cells (fixed seeds); bucket correspondence dies,
    # marginals and country identity survive
    perm_deltas = []
    for pseed in (101, 202, 303, 404, 505):
        prs = np.random.default_rng(pseed)
        perm_cells = []
        by_country = {}
        for c in cells:
            by_country.setdefault(c["c"], []).append(c)
        for ci, group in by_country.items():
            livs = [c["liv"][N_STATIC:] for c in group]
            perm = prs.permutation(len(livs))
            for c, j in zip(group, perm):
                pc = dict(c)
                pc["liv"] = np.concatenate([c["liv"][:N_STATIC],
                                            livs[j]])
                perm_cells.append(pc)
        m_p, p_p = run_hier(perm_cells, "leg", "liv")
        ks = set(p_leg) & set(p_p)
        d = np.array([abs(p_leg[k][0] - p_leg[k][1])
                      - abs(p_p[k][0] - p_p[k][1]) for k in ks]) * 100
        perm_deltas.append(round(float(d.mean()), 4))
        print(f"  perm {pseed}: mae {m_p}, Δ vs legacy {d.mean():+.4f}",
              flush=True)

    real_delta = float(np.mean([v["mean_pp"] for v in seeds.values()]))
    out = {"closure": "0.4 decision run", "frozen_protocol": True,
           "arms": {"legacy_hier_mae": mae_leg, "hybrid_hier_mae": mae_hyb},
           "q1_seed_stability": {str(k): v for k, v in seeds.items()},
           "q1_all_seeds_beneficial": all(v["mean_pp"] > 0
                                          for v in seeds.values()),
           "q2_hybrid_ablations_deltaL_positive_helps": abl,
           "q2_earning_families": sorted(k for k, v in abl.items()
                                         if v > 0),
           "q3_permutation_deltas_pp": perm_deltas,
           "q3_real_delta_pp": round(real_delta, 4),
           "q3_advantage_collapses": all(pd < real_delta * 0.5
                                         for pd in perm_deltas),
           "provenance": {"host": os.uname().nodename,
                          "commit": subprocess.run(
                              ["git", "rev-parse", "HEAD"],
                              capture_output=True, text=True,
                              cwd=ROOT).stdout.strip(),
                          "wall_clock": time.strftime(
                              "%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                          "runtime_s": round(time.time() - t0, 1)}}
    (ROOT / "data" / "living_readout_closure.json").write_text(
        json.dumps(out, indent=1))
    print(json.dumps(out, indent=1)[:1200])
    print("DONE-CLOSURE")


if __name__ == "__main__":
    main()
