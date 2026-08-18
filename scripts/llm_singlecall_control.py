"""Single-call control for the LLM standoff (advisor hardening #1).

Objection to close: "66 countries in one response degrades later
answers." Control: ONE country per call, 5 questions x 10 countries
(pre-specified below: first 5 questions in file order; 5 Western +
5 non-Western countries), same model, same parse path. If single-call
MAE on these 50 cells matches the batched MAE on the same cells, the
batched protocol stands.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.llm_standoff import ask  # same request/parse path

MODEL = "claude-sonnet-5"
COUNTRIES = ["USA", "DEU", "SWE", "AUS", "ITA",   # Western
             "NGA", "IDN", "BRA", "PAK", "THA"]   # non-Western


def main() -> None:
    gt = json.load(open("data/benchmark/goqa_ground_truth.json"))[:5]
    batched = json.load(
        open("data/llm_standoff_cache_claude-sonnet-5.json"))
    single, errs_s, errs_b = {}, [], []
    for q in gt:
        single[q["id"]] = {}
        for cc in COUNTRIES:
            if cc not in q["countries"]:
                continue
            pred = ask(MODEL, q["text"], [cc])  # ONE country per call
            if cc in pred:
                single[q["id"]][cc] = pred[cc]
                truth = q["countries"][cc]["yes"]
                errs_s.append(abs(pred[cc] / 100.0 - truth))
                if cc in batched.get(q["id"], {}):
                    errs_b.append(abs(batched[q["id"]][cc] / 100.0 - truth))
        print(f"{q['id']}: {len(single[q['id']])} single-call cells",
              flush=True)
    import numpy as np
    out = {"model": MODEL, "countries": COUNTRIES,
           "n_cells": len(errs_s),
           "mae_singlecall": float(np.mean(errs_s)),
           "mae_batched_same_cells": float(np.mean(errs_b)),
           "predictions": single}
    json.dump(out, open("data/llm_singlecall_control.json", "w"), indent=1)
    print(f"SINGLECALL-CONTROL: single {out['mae_singlecall']:.4f} vs "
          f"batched {out['mae_batched_same_cells']:.4f} on "
          f"{out['n_cells']} cells", flush=True)


if __name__ == "__main__":
    main()
