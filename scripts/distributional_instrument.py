"""THE DISTRIBUTIONAL INSTRUMENT — Wasserstein-1 on real cell densities.

Prereg: data/distributional_instrument_prereg.json (written first).
Substrate: data/cell_densities.json — 4,728 real within-cell response
histograms from WVS7 individual answers.

Readouts scored (same population, same calibration, same forces):
  HARD     point stances -> histogram (current engine)
  SOFT+    each agent is a distribution over answers, width = sigma
  COLLAPSE each agent COLLAPSES to a discrete answer under the question
           (Bernoulli on its stance, then placed at the scale extremes
           it implies) — the readout Pietro's superposition concept
           predicts: measurement yields a definite answer, so the cell
           density is a mixture of definite answers, not of smears
  BORN     coherence readout recovered from the old TS engine:
           P = R_yes^2 / (R_yes^2 + R_no^2) with R = mean resultant
           length of each camp's normalized force vectors; placed as a
           two-point density at the extremes

Also reported: observed vs predicted EXTREME MASS (bimodality), the
statistic a smoother cannot fake.
Env: DI_POP (default 200000), DI_SIGMA_GRID.
"""
from __future__ import annotations

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

POP = int(os.environ.get("DI_POP", "200000"))
SIGMA_GRID = [float(x) for x in
              os.environ.get("DI_SIGMA_GRID", "0,0.5,1.0,1.5,2.0,3.0").split(",")]
MIN_AGENTS = 40
EDGES = np.linspace(0.0, 1.0, 11)      # 10 bins matching the 1-10 scale
CENTERS = (EDGES[:-1] + EDGES[1:]) / 2


def w1(p: np.ndarray, q: np.ndarray) -> float:
    """Wasserstein-1 between two histograms on a uniform 1-D grid."""
    return float(np.abs(np.cumsum(p) - np.cumsum(q)).sum() / (len(p) - 1))


def hist_from(vals: np.ndarray, wts=None) -> np.ndarray:
    h, _ = np.histogram(np.clip(vals, 0, 1), bins=EDGES, weights=wts)
    t = h.sum()
    return h / t if t > 0 else np.full(len(CENTERS), 1.0 / len(CENTERS))


def main() -> None:
    civ = genesis(POP, 42)
    c2i, _ = _get_country_index(civ)
    gt = {q["id"]: q for q in
          json.load(open("data/benchmark/goqa_ground_truth.json"))}
    dens = json.load(open("data/cell_densities.json"))
    fnorm = civ.forces / np.maximum(
        np.linalg.norm(civ.forces, axis=1, keepdims=True), 1e-9)

    scores = {k: [] for k in ["hard", "collapse", "born"]}
    scores.update({f"soft{s}": [] for s in SIGMA_GRID})
    ext_obs, ext_pred = {k: [] for k in scores}, []
    rng = np.random.default_rng(7)
    nodes = np.array([-2.02, -0.959, 0.0, 0.959, 2.02])
    gwt = np.array([0.0199, 0.3936, 0.9453, 0.3936, 0.0199])
    gwt /= gwt.sum()

    for qcode, cells in dens.items():
        if qcode not in gt:
            continue
        q = gt[qcode]
        ct = {ISO3_TO_ISO2[c]: d["yes"] for c, d in q["countries"].items()
              if c in ISO3_TO_ISO2}
        g = q["global_yes_popweighted"]
        w = calibrate_single(civ, g, ct)
        if not np.any(w):
            continue
        s_all = np.clip(run_question(
            Question(id=qcode, text=q["text"], domain="belief_causal",
                     baseline=g, weights=w, lens="wvs"),
            civ).settled_stances, 1e-4, 1 - 1e-4)
        z_all = logit(s_all)
        for key, cell in cells.items():
            cc, a, e = key.split("|")
            if cc not in c2i:
                continue
            a, e = int(a), int(e)
            m = ((civ.country == c2i[cc])
                 & (civ.education == e)
                 & ((civ.age_bucket == a) if a < 3 else (civ.age_bucket >= 3)))
            if m.sum() < MIN_AGENTS:
                continue
            obs = np.array(cell["hist"])
            s, z = s_all[m], z_all[m]
            # HARD
            scores["hard"].append(w1(hist_from(s), obs))
            # SOFT+ at each sigma
            for sg in SIGMA_GRID:
                if sg == 0:
                    hp = hist_from(s)
                else:
                    parts = [gw * hist_from(sigmoid(z + sg * nd))
                             for nd, gw in zip(nodes, gwt)]
                    hp = np.sum(parts, axis=0)
                    hp = hp / hp.sum()
                scores[f"soft{sg}"].append(w1(hp, obs))
            # COLLAPSE: measurement yields a definite answer
            draws = (rng.random(m.sum()) < s).astype(float)
            hp_c = hist_from(draws)
            scores["collapse"].append(w1(hp_c, obs))
            ext_pred.append(hp_c[0] + hp_c[-1])
            # BORN: camp coherence -> two-point density
            yes_m, no_m = s >= 0.5, s < 0.5
            if yes_m.sum() > 2 and no_m.sum() > 2:
                r_y = float(np.linalg.norm(fnorm[m][yes_m].mean(axis=0)))
                r_n = float(np.linalg.norm(fnorm[m][no_m].mean(axis=0)))
                p_born = r_y ** 2 / max(r_y ** 2 + r_n ** 2, 1e-9)
            else:
                p_born = float(s.mean())
            hp_b = np.zeros(len(CENTERS))
            hp_b[-1], hp_b[0] = p_born, 1 - p_born
            scores["born"].append(w1(hp_b, obs))
            ext_obs["hard"].append(obs[0] + obs[-1])

    out = {"pop": POP, "n_cells": len(scores["hard"]),
           "observed_extreme_mass": float(np.mean(ext_obs["hard"])),
           "collapse_extreme_mass": float(np.mean(ext_pred))}
    for k, v in scores.items():
        if v:
            out[k] = float(np.mean(v))
    for k in sorted(out):
        if isinstance(out[k], float) and k not in (
                "observed_extreme_mass", "collapse_extreme_mass"):
            print(f"  {k:10s} W1 {out[k]:.4f}", flush=True)
    print(f"  extreme mass: observed {out['observed_extreme_mass']:.3f} | "
          f"collapse readout {out['collapse_extreme_mass']:.3f}", flush=True)
    json.dump(out, open("data/distributional_instrument.json", "w"), indent=1)
    best = min((k for k in out if k.startswith(("hard", "soft", "collapse",
                                                "born"))), key=lambda k: out[k])
    print(f"DISTRIBUTIONAL-VERDICT: best readout = {best} "
          f"(W1 {out[best]:.4f} vs hard {out['hard']:.4f}, "
          f"{out['n_cells']} cells)", flush=True)


if __name__ == "__main__":
    main()
