"""SB1 feature worlds: candidate flags, 200k x 180d, per-country
living-feature means + agent counts. usage: run_features.py <seed>"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

def main(seed):
    from earth1.alive import birth_world, live_one_day
    from earth1.calibration import living_features
    from earth1.genesis import GENESIS_COUNTRY_CODES
    w = birth_world(200_000, seed, substrate="c2plus_v1")
    rng = np.random.default_rng(seed)
    for _ in range(180):
        live_one_day(w, rng)
    X = living_features(w)
    civ, alive = w.civ, w.health.alive
    out = {}
    for ci, iso2 in enumerate(GENESIS_COUNTRY_CODES):
        m = alive & (civ.country == ci)
        if m.sum() >= 30:
            out[iso2] = {"n": int(m.sum()),
                         "f": [round(float(v), 6) for v in X[m].mean(0)]}
    d = os.environ.get("SB_OUT", "/opt/earth1-data/scoreboard")
    os.makedirs(d, exist_ok=True)
    json.dump(out, open(os.path.join(d, f"features_{seed}.json"), "w"))
    print("FEATURES DONE", seed, len(out), "countries")

if __name__ == "__main__":
    main(int(sys.argv[1]))
