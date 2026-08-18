"""C2 measurement: does the religiosity field (real WVS7 joint
structure) improve within-country cell prediction and the headline?

Run twice: with and without EARTH1_RELIGIOSITY=1. Reports
  (a) US age x edu x religiosity cell MAE / spread / correlation
      against data/us_joint_cells.json (real microdata cells)
  (b) GOQA country-level CV MAE (must not regress)
Env: C2_POP (default 200000).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.benchmark import ISO3_TO_ISO2, run_goqa_benchmark
from earth1.calibration import calibrate_single, _get_country_index
from earth1.engine import run_question
from earth1.genesis import genesis
from earth1.types import Question

POP = int(os.environ.get("C2_POP", "200000"))
FLAG = os.environ.get("EARTH1_RELIGIOSITY") == "1"
QMAP = {"Q182": "homosex", "Q184": "abortion", "Q57": "trust"}


def main() -> None:
    civ = genesis(POP, 42)
    code_to_idx, _ = _get_country_index(civ)
    gt = {q["id"]: q for q in
          json.load(open("data/benchmark/goqa_ground_truth.json"))}
    real = json.load(open("data/us_joint_cells.json"))
    us = civ.country == code_to_idx["US"]
    has_rel = getattr(civ, "religiosity", None) is not None

    rows = []
    for qcode, field in QMAP.items():
        q = gt[qcode]
        ct = {ISO3_TO_ISO2[c]: d["yes"] for c, d in q["countries"].items()
              if c in ISO3_TO_ISO2}
        w = calibrate_single(civ, q["global_yes_popweighted"], ct)
        s = run_question(Question(id=qcode, text=q["text"],
                                  domain="belief_causal",
                                  baseline=q["global_yes_popweighted"],
                                  weights=w, lens="wvs"), civ).settled_stances
        eng, obs = [], []
        for r in real:
            a, e, rel = r["age_b"], r["edu"], r["relig"]
            m = us & ((civ.age_bucket == a) if a < 3 else (civ.age_bucket >= 3))
            m = m & (civ.education == e)
            if has_rel:
                m = m & (civ.religiosity == rel)
            elif rel == 1:
                continue  # no religiosity dimension: score each cell once
            if m.sum() < 20:
                continue
            eng.append(float(s[m].mean()))
            obs.append(r[field])
        if len(eng) >= 4:
            eng, obs = np.array(eng), np.array(obs)
            rows.append({"q": qcode, "n_cells": len(eng),
                         "mae": float(np.abs(eng - obs).mean()),
                         "eng_spread": float(eng.max() - eng.min()),
                         "real_spread": float(obs.max() - obs.min()),
                         "corr": float(np.corrcoef(eng, obs)[0, 1])})
            print(f"  {qcode}: {len(eng)} cells | MAE {rows[-1]['mae']:.3f} | "
                  f"spread eng {rows[-1]['eng_spread']:.3f} vs real "
                  f"{rows[-1]['real_spread']:.3f} | corr "
                  f"{rows[-1]['corr']:.3f}", flush=True)

    goqa = run_goqa_benchmark(
        civ, json.load(open("data/benchmark/goqa_ground_truth.json")),
        cv_seed=42)
    out = {"religiosity_flag": FLAG, "pop": POP, "cells": rows,
           "goqa_cv_mae": goqa.engine_cv_mae,
           "goqa_naive": goqa.naive_cv_mae, "goqa_wins": goqa.engine_wins}
    tag = "on" if FLAG else "off"
    json.dump(out, open(f"data/c2_measure_{tag}.json", "w"), indent=1)
    print(f"C2-MEASURE[relig={tag}]: cell-MAE "
          f"{np.mean([r['mae'] for r in rows]):.4f} | mean corr "
          f"{np.mean([r['corr'] for r in rows]):.3f} | GOQA CV "
          f"{goqa.engine_cv_mae:.4f} (naive {goqa.naive_cv_mae:.4f}, "
          f"{goqa.engine_wins}/40)", flush=True)


if __name__ == "__main__":
    main()
