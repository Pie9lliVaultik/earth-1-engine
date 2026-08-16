#!/usr/bin/env python3
"""G5 run #8: temporal leg under amendment A4 — perceived-headline replay
with the response law.

Pre-conditions:
  - data/headlines_2017_2022.json exists (from fetch_headlines.py)
  - data/perceived_headlines.json exists (from perceive_headlines.py)
  - data/question_profiles.json exists (from the profile authoring step)
  - A4 amendment committed in data/g5_preregistration.json BEFORE this runs

Three conditions (same seeds):
  1. Endogenous — no events (reference)
  2. Real — perceived headlines on correct countries
  3. Shuffled — same events, permuted geography (§14 control)

Pass: real beats no-change on MAE AND real beats shuffled AND
      real sign accuracy > 0.5 at p < 0.05.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from earth1.g5 import g5_temporal_perceived_replay, print_g5_report

PERCEIVED_PATH = ROOT / "data" / "perceived_headlines.json"
PROFILES_PATH = ROOT / "data" / "question_profiles.json"
RESULTS_PATH = ROOT / "data" / "g5_results.json"


def main():
    if not PERCEIVED_PATH.exists():
        print("No perceived headlines — run perceive_headlines.py first")
        sys.exit(1)
    if not PROFILES_PATH.exists():
        print("No question profiles — author them first")
        sys.exit(1)

    perceived = json.loads(PERCEIVED_PATH.read_text())
    profiles_raw = json.loads(PROFILES_PATH.read_text())

    response_profiles = {}
    for qid, values in profiles_raw.items():
        if qid.startswith("t_"):
            response_profiles[qid] = np.array(values, dtype=np.float64)

    print(f"Perceived headlines: {len(perceived)} windows, "
          f"{sum(len(v) for v in perceived.values())} events")
    print(f"Response profiles: {len(response_profiles)} WVS questions")
    print()

    result = g5_temporal_perceived_replay(
        perceived=perceived,
        response_profiles=response_profiles,
        pop=50_000,
        seed=42,
        dt_days=30.0,
        progress=True,
    )

    print("\n" + "=" * 60)
    print(f"ENDOGENOUS: MAE {result.endogenous.mae_engine:.4f} "
          f"vs no-change {result.endogenous.mae_nochange:.4f} "
          f"| sign {result.endogenous.sign_accuracy:.1%}")
    print(f"REAL:       MAE {result.real.mae_engine:.4f} "
          f"vs no-change {result.real.mae_nochange:.4f} "
          f"| sign {result.real.sign_accuracy:.1%}")
    print(f"SHUFFLED:   MAE {result.shuffled.mae_engine:.4f} "
          f"vs no-change {result.shuffled.mae_nochange:.4f} "
          f"| sign {result.shuffled.sign_accuracy:.1%}")
    print(f"\nPASS: {result.passes}")
    print("=" * 60)

    record = {
        "run": 8,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pop": 50_000,
        "seed": 42,
        "amendment": "A4",
        "leg": "temporal",
        "n_perceived_windows": len(perceived),
        "n_response_profiles": len(response_profiles),
        "endogenous": {
            "mae_engine": result.endogenous.mae_engine,
            "mae_nochange": result.endogenous.mae_nochange,
            "sign_accuracy": result.endogenous.sign_accuracy,
            "sign_p": result.endogenous.sign_p,
        },
        "real": {
            "mae_engine": result.real.mae_engine,
            "mae_nochange": result.real.mae_nochange,
            "sign_accuracy": result.real.sign_accuracy,
            "sign_p": result.real.sign_p,
        },
        "shuffled": {
            "mae_engine": result.shuffled.mae_engine,
            "mae_nochange": result.shuffled.mae_nochange,
            "sign_accuracy": result.shuffled.sign_accuracy,
            "sign_p": result.shuffled.sign_p,
        },
        "passes": result.passes,
    }

    results = json.loads(RESULTS_PATH.read_text()) if RESULTS_PATH.exists() else []
    results.append(record)
    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nAppended run #8 to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
