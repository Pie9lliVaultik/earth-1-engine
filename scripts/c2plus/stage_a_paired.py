"""C2+ class-2 Stage-A paired health regression (C2PLUS_CHANGE_IMPACT.md).

Incumbent vs candidate substrate, same seed + rng stream, 200k x 90d.
usage: stage_a_paired.py <arm: incumbent|c2plus> """
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from earth1.alive import birth_world, live_one_day  # noqa: E402
from earth1.observables import collect  # noqa: E402

OUT = "/opt/earth1-data/c2plus/stage_a"
CUM = ("deaths", "births", "disease_deaths", "cascades_fired",
       "firms_failed", "starved_or_parched")


def main(arm):
    os.makedirs(OUT, exist_ok=True)
    sub = None if arm == "incumbent" else "c2plus_v1"
    w = birth_world(200_000, 4242, substrate=sub)
    rng = np.random.default_rng(4242)
    cum = {k: 0 for k in CUM}
    rows = []
    for d in range(90):
        st = live_one_day(w, rng)
        for k in CUM:
            cum[k] += int(st.get(k, 0) or 0)
        o = collect(w, cum)
        rows.append({k: o[k] for k in
                     ("alive", "cum_deaths", "cum_disease_deaths",
                      "employment_rate", "destitute_share", "wealth_mean",
                      "cum_cascades", "cum_firms_failed")}
                    | {"dep_mean": o["deprivation"]["mean"],
                       "force_mean": o["force_mean"],
                       "force_sd": o["force_sd"],
                       "cum_starved": cum["starved_or_parched"]})
        if d % 15 == 0:
            print(arm, "day", d, "alive", o["alive"], flush=True)
    json.dump(rows, open(os.path.join(OUT, f"{arm}.json"), "w"))
    print("STAGE-A ARM DONE", arm)


if __name__ == "__main__":
    main(sys.argv[1])
