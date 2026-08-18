"""THE DISCRIMINATING TEST — mechanism or knob?

Thresholds pre-stated in data/polar_interaction_prereg.json
(DISCRIMINATING_TEST_SPEC) before this file existed:
  Arm A  cross-country extreme mass, STYLE-CORRECTED, held-out
         countries: Pearson r >= 0.40
  Arm B  question bimodality ordering: Spearman >= 0.74 (n=8, p<0.05)
  Arm C  ERS-robustness of the metric: refit on style-corrected
         densities; parameters barely move => W1 was correcting for
         style on its own

The operator has 6 free parameters. Fitting reproduces a measured
shape by construction; only these unfitted quantities discriminate.
Env: PD_POP (default 50000), PD_ROUNDS (default 20).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.benchmark import ISO3_TO_ISO2
from earth1.calibration import calibrate_single, _get_country_index
from earth1.engine import run_question
from earth1.genesis import genesis
from earth1.polar import polar_settle
from earth1.types import Question

POP = int(os.environ.get("PD_POP", "50000"))
ROUNDS = int(os.environ.get("PD_ROUNDS", "20"))
MIN_AGENTS = 40
EDGES = np.linspace(0.0, 1.0, 11)
GRID = [(0.20, 0.01, 0.10, 0.60, 0.05), (0.20, 0.05, 0.20, 0.60, 0.05),
        (0.20, 0.10, 0.30, 0.50, 0.10), (0.20, 0.20, 0.40, 0.50, 0.15),
        (0.10, 0.20, 0.50, 0.40, 0.20), (0.20, 0.30, 0.60, 0.40, 0.25),
        (0.30, 0.30, 0.70, 0.35, 0.30), (0.20, 0.50, 0.80, 0.30, 0.35)]


def w1(p, q):
    return float(np.abs(np.cumsum(p) - np.cumsum(q)).sum() / (len(p) - 1))


def hist_from(v):
    h, _ = np.histogram(np.clip(v, 0, 1), bins=EDGES)
    t = h.sum()
    return h / t if t > 0 else np.full(10, 0.1)


def is_train(cc):
    return int(hashlib.sha256(
        f"polar-split-2026-08-18|{cc}".encode()).hexdigest()[:8], 16) % 3 != 0


def main() -> None:
    civ = genesis(POP, 42)
    c2i, _ = _get_country_index(civ)
    gt = {q["id"]: q for q in
          json.load(open("data/benchmark/goqa_ground_truth.json"))}
    raw = json.load(open("data/cell_densities.json"))
    corr = json.load(open("data/cell_densities_ers.json"))

    base = {}
    for qcode in raw:
        if qcode not in gt:
            continue
        q = gt[qcode]
        ct = {ISO3_TO_ISO2[c]: d["yes"] for c, d in q["countries"].items()
              if c in ISO3_TO_ISO2}
        g = q["global_yes_popweighted"]
        w = calibrate_single(civ, g, ct)
        if np.any(w):
            base[qcode] = run_question(
                Question(id=qcode, text=q["text"], domain="belief_causal",
                         baseline=g, weights=w, lens="wvs"),
                civ, layers=0).settled_stances

    def cells_of(dens):
        out = []
        for qcode, cs in dens.items():
            if qcode not in base:
                continue
            for key, cell in cs.items():
                cc, a, e = key.split("|")
                if cc not in c2i:
                    continue
                a, e = int(a), int(e)
                m = ((civ.country == c2i[cc]) & (civ.education == e)
                     & ((civ.age_bucket == a) if a < 3
                        else (civ.age_bucket >= 3)))
                if m.sum() >= MIN_AGENTS:
                    out.append((qcode, cc, m, np.array(cell["hist"])))
        return out

    cells_raw, cells_corr = cells_of(raw), cells_of(corr)

    def fit_on(cells, tag):
        best, best_w1 = None, 1e9
        for cfg in GRID:
            st = {q: polar_settle(s, civ.adj, seed=42, rounds=ROUNDS,
                                  hub_fraction=cfg[0], fire_rate=cfg[1],
                                  attraction=cfg[2], repulsion_threshold=cfg[3],
                                  repulsion_strength=cfg[4])
                  for q, s in base.items()}
            errs = [w1(hist_from(st[qc][m]), obs)
                    for qc, cc, m, obs in cells if is_train(cc)]
            v = float(np.mean(errs))
            if v < best_w1:
                best_w1, best, best_st = v, cfg, st
        print(f"  {tag}: selected {best} (train W1 {best_w1:.4f})", flush=True)
        return best, best_st

    cfg_raw, st_raw = fit_on(cells_raw, "fit on RAW")
    cfg_cor, st_cor = fit_on(cells_corr, "fit on STYLE-CORRECTED")
    arm_c = (cfg_raw == cfg_cor) or abs(cfg_raw[2] - cfg_cor[2]) <= 0.1

    # Arm A: per-country extreme mass, style-corrected, HELD-OUT only
    pred_c, obs_c = {}, {}
    for qc, cc, m, obs in cells_corr:
        if is_train(cc):
            continue
        hp = hist_from(st_cor[qc][m])
        pred_c.setdefault(cc, []).append(hp[0] + hp[-1])
        obs_c.setdefault(cc, []).append(obs[0] + obs[-1])
    ccs = [c for c in pred_c if len(pred_c[c]) >= 3]
    pv = np.array([np.mean(pred_c[c]) for c in ccs])
    ov = np.array([np.mean(obs_c[c]) for c in ccs])
    r_a = float(np.corrcoef(pv, ov)[0, 1]) if len(ccs) >= 4 else float("nan")

    # Arm B: per-question bimodality ordering (held-out countries)
    pred_q, obs_q = {}, {}
    for qc, cc, m, obs in cells_corr:
        if is_train(cc):
            continue
        hp = hist_from(st_cor[qc][m])
        pred_q.setdefault(qc, []).append(hp[0] + hp[-1])
        obs_q.setdefault(qc, []).append(obs[0] + obs[-1])
    qs = sorted(pred_q)
    rho = float(spearmanr([np.mean(pred_q[q]) for q in qs],
                          [np.mean(obs_q[q]) for q in qs]).statistic)

    out = {"pop": POP, "n_free_parameters": 6,
           "cfg_fit_raw": cfg_raw, "cfg_fit_corrected": cfg_cor,
           "arm_A_cross_country_r": r_a, "arm_A_n_countries": len(ccs),
           "arm_A_threshold": 0.40, "arm_A_pass": bool(r_a >= 0.40),
           "arm_B_question_spearman": rho, "arm_B_n_questions": len(qs),
           "arm_B_threshold": 0.74, "arm_B_pass": bool(rho >= 0.74),
           "arm_C_metric_ers_robust": bool(arm_c)}
    json.dump(out, open("data/polar_discriminate.json", "w"), indent=1)
    print(f"  ARM A cross-country r {r_a:+.3f} (n={len(ccs)}, need >=0.40) "
          f"-> {'PASS' if out['arm_A_pass'] else 'FAIL'}", flush=True)
    print(f"  ARM B question Spearman {rho:+.3f} (n={len(qs)}, need >=0.74) "
          f"-> {'PASS' if out['arm_B_pass'] else 'FAIL'}", flush=True)
    print(f"  ARM C metric ERS-robust: {arm_c} "
          f"(raw {cfg_raw} vs corrected {cfg_cor})", flush=True)
    verdict = ("MECHANISM" if out["arm_A_pass"] and out["arm_B_pass"]
               else "PARTIAL" if out["arm_A_pass"] or out["arm_B_pass"]
               else "KNOB — shape-matching only")
    print(f"DISCRIMINATE-VERDICT: {verdict}", flush=True)


if __name__ == "__main__":
    main()
