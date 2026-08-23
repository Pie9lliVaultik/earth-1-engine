"""Cohort instrument v2 — WITHIN-COUNTRY age gradients (the design the
micro-test demanded). Engine per-(question, country, age-bucket)
readouts vs official microdata cells (data/wvs_w7_cohort_by_country.csv,
survey-weighted, min-N 150).

Metrics per (question, country):
  - bucket MAE vs the country-flat baseline (country's own bucket mean
    — the 'no age knowledge' null)
  - age-gradient direction (young minus old), engine vs observed

Registered prediction (POST_FREEZE_PROGRAM step 1): the frozen engine
fails — authored age structure, not learned differentiation.
Env: CI2_POP (default 200000 — need agents per country x bucket cell).
"""
from __future__ import annotations

import csv
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

POP = int(os.environ.get("CI2_POP", "200000"))
BUCKETS = ["18_29", "30_44", "45_59", "60_plus"]
MIN_AGENTS = 30


def main() -> None:
    civ = genesis(POP, 42)
    code_to_idx, _ = _get_country_index(civ)
    gt = {q["id"]: q for q in
          json.load(open("data/benchmark/goqa_ground_truth.json"))}

    cells = {}
    for r in csv.DictReader(open("data/wvs_w7_cohort_by_country.csv")):
        iso2 = ISO3_TO_ISO2.get(r["country"])
        if iso2:
            cells.setdefault(r["qcode"], {}).setdefault(
                iso2, {})[r["age_bucket"]] = float(r["yes_weighted"])

    eng_mae, flat_mae, grad_hits, grad_n = [], [], 0, 0
    per_pair = []
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
        res = run_question(Question(id=qcode, text=q["text"],
                                    domain="belief_causal", baseline=g,
                                    weights=w, lens="wvs"), civ)
        s = res.settled_stances
        for cc, obs in by_cc.items():
            if len(obs) < 4 or cc not in code_to_idx:
                continue
            cmask = civ.country == code_to_idx[cc]
            eng = {}
            for i, b in enumerate(BUCKETS):
                bmask = cmask & ((civ.age_bucket == i) if i < 3 else
                                 (civ.age_bucket >= 3))
                if bmask.sum() < MIN_AGENTS:
                    break
                eng[b] = float(s[bmask].mean())
            if len(eng) < 4:
                continue
            flat = float(np.mean([obs[b] for b in BUCKETS]))
            for b in BUCKETS:
                eng_mae.append(abs(eng[b] - obs[b]))
                flat_mae.append(abs(flat - obs[b]))
            og = np.sign(obs["18_29"] - obs["60_plus"])
            eg = np.sign(eng["18_29"] - eng["60_plus"])
            if og != 0:
                grad_n += 1
                grad_hits += int(og == eg)
            per_pair.append({"q": qcode, "cc": cc,
                             "obs_grad": round(obs["18_29"] - obs["60_plus"], 3),
                             "eng_grad": round(eng["18_29"] - eng["60_plus"], 3)})

    out = {"pop": POP, "n_cells": len(eng_mae),
           "n_pairs": len(per_pair),
           "engine_bucket_mae": float(np.mean(eng_mae)),
           "flat_baseline_mae": float(np.mean(flat_mae)),
           "gradient_direction_acc": grad_hits / grad_n if grad_n else None,
           "n_gradient_pairs": grad_n,
           "per_pair": per_pair}
    json.dump(out, open("data/cohort_instrument_v2.json", "w"), indent=1)
    print(f"COHORT-V2: {len(per_pair)} (q,country) pairs, {len(eng_mae)} "
          f"cells | engine bucket-MAE {out['engine_bucket_mae']:.4f} vs "
          f"flat {out['flat_baseline_mae']:.4f} | gradient direction "
          f"{grad_hits}/{grad_n}", flush=True)


if __name__ == "__main__":
    main()
