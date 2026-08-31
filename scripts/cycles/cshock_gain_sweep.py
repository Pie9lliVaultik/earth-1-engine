"""c-SHOCK LAYOFF_GAIN calibration sweep (prereg ops/alive/cycles/cshock.md).

usage: cshock_gain_sweep.py <seed> <arm: covid|gfc|null> [pop]
Wrapper exports EARTH1_DISTRESS_LAYOFFS / EARTH1_LAYOFF_GAIN /
EARTH1_HARDSHIP_MODE before python starts; the run records what the
physics actually loaded (tripwire). Unemployment rate is census-weighted
share of the living labour force, the WB SL.UEM.TOTL.ZS frame.
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

WARM, WINDOW, EVERY = 90, 365, 5


def main(seed, arm, pop):
    from earth1 import life as life_mod
    from earth1.alive import birth_world, live_one_day
    from earth1.backtest import REGISTRY
    from earth1.branch import apply, null_branch
    from earth1.genesis import census_weights
    ev = {e.id: e for e in REGISTRY}
    w = birth_world(pop, seed, substrate="c2plus_v1")
    rng = np.random.default_rng(977 * 13 + seed)
    for _ in range(WARM):
        live_one_day(w, rng)
    cw = census_weights(w.civ)

    def urate():
        alive = w.health.alive
        lf = w.life.in_lf & alive
        denom = float(cw[lf].sum())
        return float(cw[(~w.life.employed) & lf].sum()) / max(denom, 1e-9)

    sc = {"covid": lambda: ev["covid_2020"].scenario,
          "gfc": lambda: ev["gfc_2008"].scenario,
          "null": null_branch}[arm]()
    pre_u = urate()
    apply(w, sc, rng)
    path = []
    for d in range(WINDOW):
        live_one_day(w, rng)
        if (d + 1) % EVERY == 0:
            path.append({"day": d + 1, "u": urate()})
    out = os.environ.get("CSHOCK_GAIN_OUT", "/opt/earth1-data/cshock_gain")
    os.makedirs(out, exist_ok=True)
    tag = (f"{arm}_{life_mod.DISTRESS_LAYOFFS}_g{life_mod.LAYOFF_GAIN:g}"
           f"_{pop}_{seed}")
    json.dump({"seed": seed, "arm": arm, "pop": pop,
               "flag": life_mod.DISTRESS_LAYOFFS,
               "gain": life_mod.LAYOFF_GAIN,
               "hardship_mode": life_mod.HARDSHIP_MODE,
               "pre_u": pre_u, "path": path, "final_u": path[-1]["u"],
               "distress_layoffs": int(getattr(w.life, "distress_layoffs", 0)),
               "dep_mean": float(w.life.deprivation[w.health.alive].mean()),
               "destitute": float((w.life.deprivation[w.health.alive]
                                   > 0.99).mean())},
              open(os.path.join(out, f"{tag}.json"), "w"), indent=1)
    print("GAIN-SWEEP DONE", tag, "u", round(pre_u, 4), "->",
          round(path[-1]["u"], 4))


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2],
         int(sys.argv[3]) if len(sys.argv) > 3 else 20000)
