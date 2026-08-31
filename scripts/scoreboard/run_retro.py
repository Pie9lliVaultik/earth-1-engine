"""RETRODICTION v1 runner: uniform-class-dose state-discrimination.
usage: run_retro.py <seed> <arm: scenario|null>"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

WARM, WINDOW = 90, 120


def main(seed, arm):
    from earth1.alive import birth_world, live_one_day
    from earth1.branch import Scenario, apply, null_branch
    from earth1.genesis import GENESIS_COUNTRY_CODES
    w = birth_world(200_000, seed, substrate="c2plus_v1")
    rng = np.random.default_rng(977 * 13 + seed)
    for _ in range(WARM):
        live_one_day(w, rng)
    sc = null_branch() if arm == "null" else Scenario(
        id="protest_class_dose", label="registered uniform protest dose",
        forces={"fear": 0.2, "economics": -0.15}, countries=None,
        firm_damage=0.1, trade_shock=0.0, persists_days=60)
    apply(w, sc, rng)
    t0 = float(w.day)
    onsets = {}
    for _ in range(WINDOW):
        live_one_day(w, rng)
    res = getattr(w.chronicle, "cascade_residues", None) or []
    for r in res:
        if r["rule"] == "collective_surge" and r["day"] >= t0:
            iso = GENESIS_COUNTRY_CODES[int(r["loc"]) // 1000]
            onsets[iso] = onsets.get(iso, 0) + 1
    d = os.environ.get("RETRO_OUT", "/opt/earth1-data/retro")
    os.makedirs(d, exist_ok=True)
    json.dump({"seed": seed, "arm": arm, "onsets": onsets},
              open(os.path.join(d, f"{arm}_{seed}.json"), "w"))
    print("RETRO DONE", arm, seed, len(onsets), "countries with onsets")


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2])
