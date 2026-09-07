"""EQUILIBRATED SCALE TEST — does the freeze-0.9 anchor board hold at scale?

Runs to 180 days (the age the board was measured at) with censuses at
checkpoints, at two scales, so scale invariance is tested at EVERY
world-age and the equilibrated board is checked against real anchors.

REFUSES TO RUN on anything but freeze-0.9 physics — a 2026-09-02 run
without the exports silently used engine defaults (cliff/legacy/off)
and burned 46 hours producing numbers comparable to nothing.

usage: equilibrate.py <pop> <tag>     (source scripts/env/freeze09.env first)
"""
import json
import os
import resource
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import numpy as np

from earth1.configstamp import assert_freeze09
STAMP = assert_freeze09()          # hard gate, before anything is born

try:
    open("/proc/self/oom_score_adj", "w").write("500")
except Exception:
    pass

from earth1.alive import birth_world, live_one_day
from earth1.deathwatch import DeathWatch
from earth1.poverty import anchors, poverty_profile

POP, TAG = int(sys.argv[1]), sys.argv[2]
DAYS = int(os.environ.get("EQ_DAYS", "180"))
CHECK = {5, 15, 30, 60, 90, 120, 180}
SEED = 20260902
OUT = "/opt/earth1-data/equilibrate_%s.json" % TAG

A = anchors()["anchors"]
REAL = {"median": A["pip_world_median_daily_2021ppp"]["value"],
        "pov830": A["poverty_830_2021ppp"]["value"] / 100.0}
BOARD_200K = {"median": 9.605, "pov830": 0.4588, "pov300": 0.1680,
              "cdr_yr": 0.00727, "mean_age_death": 68.99}

t0 = time.time()
w = birth_world(POP, SEED, substrate="c2plus_v1")
print("[%s] BORN %d in %.0fs | physics %s" % (TAG, w.civ.n, time.time() - t0,
                                              STAMP["loaded"]), flush=True)
rng = np.random.default_rng(SEED)
watch = DeathWatch(w)
rows = []
for d in range(1, DAYS + 1):
    live_one_day(w, rng)
    watch.observe(w)
    if d in CHECK:
        p = poverty_profile(w)
        row = {"day": d,
               "median": round(p["median_welfare_ppp"], 3),
               "pov830": round(p["poverty_830_2021ppp_headcount"], 4),
               "pov420": round(p["poverty_420_2021ppp_headcount"], 4),
               "pov300": round(p["poverty_300_2021ppp_headcount"], 4),
               "deaths_cum": watch.n,
               "cdr_yr": round(watch.n / POP * (365.0 / d), 5),
               "mean_age_death": (round(watch.mean_age_at_death, 2)
                                  if watch.n else None),
               "alive": int(w.health.alive.sum()),
               "elapsed_s": round(time.time() - t0)}
        rows.append(row)
        json.dump({"pop": POP, "tag": TAG, "config": STAMP,
                   "real_anchors": REAL, "board_200k_180d": BOARD_200K,
                   "peak_rss_gb": round(resource.getrusage(
                       resource.RUSAGE_SELF).ru_maxrss / 1e6, 1),
                   "checkpoints": rows}, open(OUT, "w"), indent=1)
        print("[%s] day %3d  med %5.2f  pov830 %.4f  cdr %.5f  ageD %s  (%.0fs)"
              % (TAG, d, row["median"], row["pov830"], row["cdr_yr"],
                 row["mean_age_death"], row["elapsed_s"]), flush=True)
print("[%s] EQUILIBRATE COMPLETE" % TAG, flush=True)
