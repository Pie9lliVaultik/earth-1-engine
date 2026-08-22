"""DOES INTERACTION CREATE THE MISSING SHAPE?

Measured 2026-08-18: real within-cell densities are BIMODAL (61.5% of
mass at the scale extremes); Earth-1's readout is unimodal-narrow.
Individual-only prediction cannot produce bimodality — but
bounded-confidence interaction on a social graph is the canonical
mechanism that does (clustering / polarization).

Earth-1 HAS this machinery (diffusion.py, epsilon=0.18, 8 layers) and
it already runs inside run_question — so the question is not whether to
add it but whether its PARAMETERS are anywhere near the values that
reproduce observed shape. Swept here against the distributional ruler:

  layers  0 (no interaction) .. 24 (heavy)
  epsilon 0.05 (tight: talks only to near-identical -> clusters)
          .. 0.5 (loose: everyone averages -> consensus)

Reported per configuration: Wasserstein-1 vs real cell densities,
predicted extreme mass (bimodality) vs observed, and cross-cell spread.
Nothing is adopted here — this is measurement.
Env: IST_POP (default 50000).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.benchmark_questions import ISO3_TO_ISO2
from earth1.calibration import calibrate_single, _get_country_index
from earth1.engine import run_question
from earth1.genesis import genesis
from earth1.types import Question

POP = int(os.environ.get("IST_POP", "50000"))
MIN_AGENTS = 40
EDGES = np.linspace(0.0, 1.0, 11)
CONFIGS = [(0, 0.18), (4, 0.18), (8, 0.18), (16, 0.18), (24, 0.18),
           (8, 0.05), (8, 0.10), (16, 0.05), (24, 0.05), (8, 0.35),
           (8, 0.50)]


def w1(p, q):
    return float(np.abs(np.cumsum(p) - np.cumsum(q)).sum() / (len(p) - 1))


def hist_from(v):
    h, _ = np.histogram(np.clip(v, 0, 1), bins=EDGES)
    t = h.sum()
    return h / t if t > 0 else np.full(10, 0.1)


def main() -> None:
    civ = genesis(POP, 42)
    c2i, _ = _get_country_index(civ)
    gt = {q["id"]: q for q in
          json.load(open("data/benchmark/goqa_ground_truth.json"))}
    dens = json.load(open("data/cell_densities.json"))

    # precompute calibration once per question (interaction must not be
    # allowed to change the fit — only the readout)
    qs = []
    for qcode in dens:
        if qcode not in gt:
            continue
        q = gt[qcode]
        ct = {ISO3_TO_ISO2[c]: d["yes"] for c, d in q["countries"].items()
              if c in ISO3_TO_ISO2}
        g = q["global_yes_popweighted"]
        w = calibrate_single(civ, g, ct)
        if np.any(w):
            qs.append((qcode, Question(id=qcode, text=q["text"],
                                       domain="belief_causal", baseline=g,
                                       weights=w, lens="wvs")))

    obs_ext = []
    rows = []
    for layers, eps in CONFIGS:
        errs, exts, spreads = [], [], []
        for qcode, qobj in qs:
            s = run_question(qobj, civ, epsilon=eps,
                             layers=layers).settled_stances
            per_country = {}
            for key, cell in dens[qcode].items():
                cc, a, e = key.split("|")
                if cc not in c2i:
                    continue
                a, e = int(a), int(e)
                m = ((civ.country == c2i[cc]) & (civ.education == e)
                     & ((civ.age_bucket == a) if a < 3
                        else (civ.age_bucket >= 3)))
                if m.sum() < MIN_AGENTS:
                    continue
                obs = np.array(cell["hist"])
                hp = hist_from(s[m])
                errs.append(w1(hp, obs))
                exts.append(hp[0] + hp[-1])
                per_country.setdefault(cc, []).append(float(s[m].mean()))
                if len(rows) == 0:
                    obs_ext.append(obs[0] + obs[-1])
            for v in per_country.values():
                if len(v) >= 3:
                    spreads.append(max(v) - min(v))
        rows.append({"layers": layers, "epsilon": eps,
                     "w1": float(np.mean(errs)),
                     "extreme_mass": float(np.mean(exts)),
                     "cross_cell_spread": float(np.mean(spreads))
                     if spreads else 0.0, "n": len(errs)})
        r = rows[-1]
        print(f"  layers {layers:2d} eps {eps:.2f} | W1 {r['w1']:.4f} | "
              f"extreme mass {r['extreme_mass']:.3f} | cell spread "
              f"{r['cross_cell_spread']:.4f}", flush=True)

    out = {"pop": POP, "observed_extreme_mass": float(np.mean(obs_ext)),
           "configs": rows}
    json.dump(out, open("data/interaction_shape_test.json", "w"), indent=1)
    best = min(rows, key=lambda r: r["w1"])
    base = next(r for r in rows if r["layers"] == 0)
    print(f"INTERACTION-VERDICT: observed extreme mass "
          f"{out['observed_extreme_mass']:.3f} | no-interaction "
          f"{base['extreme_mass']:.3f} (W1 {base['w1']:.4f}) | best "
          f"layers={best['layers']} eps={best['epsilon']} "
          f"(W1 {best['w1']:.4f}, extreme {best['extreme_mass']:.3f}) | "
          f"interaction delta {100*(base['w1']-best['w1']):+.2f}pp",
          flush=True)


if __name__ == "__main__":
    main()
