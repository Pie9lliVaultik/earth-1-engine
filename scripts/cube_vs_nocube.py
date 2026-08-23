"""HEAD-TO-HEAD: cube (cell-resolution) vs no-cube (country-resolution).

Two models, two rulers, all four combinations — the only honest way to
compare, since each model's home turf flatters it.

NO-CUBE  (the model we have had all along): one prediction per country.
         Its cell density is that country prediction repeated for every
         cell inside the country.
CUBE     (cell-resolution readout): one prediction per
         (country, age bucket, education) cell.

Rulers:
  R1 country MAE   — cube predictions population-weighted back up to
                     the country, vs the GOQA country target
  R2 cell W1       — Wasserstein-1 vs real within-cell densities
                     (data/cell_densities.json, WVS7 individuals)
  R3 cell MAE      — mean-based cell error, for continuity with earlier
                     numbers (and to show what a mean ruler hides)

Env: CVN_POP (default 200000).
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
from earth1.rng import logit, sigmoid
from earth1.types import Question

POP = int(os.environ.get("CVN_POP", "200000"))
MIN_AGENTS = 40
EDGES = np.linspace(0.0, 1.0, 11)


def w1(p, q):
    return float(np.abs(np.cumsum(p) - np.cumsum(q)).sum() / (len(p) - 1))


def hist_from(vals):
    h, _ = np.histogram(np.clip(vals, 0, 1), bins=EDGES)
    t = h.sum()
    return h / t if t > 0 else np.full(10, 0.1)


def main() -> None:
    civ = genesis(POP, 42)
    c2i, _ = _get_country_index(civ)
    gt = {q["id"]: q for q in
          json.load(open("data/benchmark/goqa_ground_truth.json"))}
    dens = json.load(open("data/cell_densities.json"))

    r = {"cube": {"w1": [], "cell_mae": [], "cty_mae": []},
         "nocube": {"w1": [], "cell_mae": [], "cty_mae": []}}
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
        # observed country-level yes share per cell's country
        for key, cell in cells.items():
            cc, a, e = key.split("|")
            if cc not in c2i:
                continue
            a, e = int(a), int(e)
            cm = civ.country == c2i[cc]
            m = cm & (civ.education == e) & (
                (civ.age_bucket == a) if a < 3 else (civ.age_bucket >= 3))
            if m.sum() < MIN_AGENTS or cm.sum() < MIN_AGENTS:
                continue
            obs = np.array(cell["hist"])
            obs_mean = float((obs * ((np.arange(10) + 0.5) / 10)).sum())
            # CUBE: this cell's own agents
            r["cube"]["w1"].append(w1(hist_from(s_all[m]), obs))
            r["cube"]["cell_mae"].append(abs(float(s_all[m].mean()) - obs_mean))
            # NO-CUBE: the country's agents, same answer for every cell
            r["nocube"]["w1"].append(w1(hist_from(s_all[cm]), obs))
            r["nocube"]["cell_mae"].append(
                abs(float(s_all[cm].mean()) - obs_mean))
        # country ruler: cube aggregated back up vs the country target
        for cc, tgt in ct.items():
            if cc not in c2i:
                continue
            cm = civ.country == c2i[cc]
            if cm.sum() < MIN_AGENTS:
                continue
            parts, wts = [], []
            for a in range(4):
                for e in range(3):
                    m = cm & (civ.education == e) & (
                        (civ.age_bucket == a) if a < 3
                        else (civ.age_bucket >= 3))
                    if m.sum() >= MIN_AGENTS:
                        parts.append(float(s_all[m].mean()))
                        wts.append(m.sum())
            if parts:
                r["cube"]["cty_mae"].append(
                    abs(float(np.average(parts, weights=wts)) - tgt))
            r["nocube"]["cty_mae"].append(abs(float(s_all[cm].mean()) - tgt))

    out = {"pop": POP}
    for k, v in r.items():
        out[k] = {m: float(np.mean(x)) for m, x in v.items() if x}
        out[k]["n_cells"] = len(v["w1"])
        print(f"  {k:7s} cell-W1 {out[k]['w1']:.4f} | cell-MAE "
              f"{out[k]['cell_mae']:.4f} | country-MAE "
              f"{out[k]['cty_mae']:.4f} | {out[k]['n_cells']} cells",
              flush=True)
    json.dump(out, open("data/cube_vs_nocube.json", "w"), indent=1)
    dw = (out["nocube"]["w1"] - out["cube"]["w1"]) * 100
    dc = (out["nocube"]["cty_mae"] - out["cube"]["cty_mae"]) * 100
    print(f"CUBE-VS-NOCUBE: distributional {dw:+.2f}pp | country "
          f"{dc:+.2f}pp (positive = cube better)", flush=True)


if __name__ == "__main__":
    main()
