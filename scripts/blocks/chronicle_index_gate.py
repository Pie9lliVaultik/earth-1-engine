"""Chronicle-index bitwise gate (founder 2026-09-02): 20k news-laden
world, same seed, flag-off vs flag-on — world hashes must be IDENTICAL
at day 30 and day 90, plus wall-clock ratio reported."""
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)


def run(flag):
    os.environ["EARTH1_CHRONICLE_INDEX"] = flag
    from earth1 import persistence
    from earth1.alive import live_one_day
    from earth1.historical import birth_at
    w, _ = birth_at("2010-12-16", 20000, 4242, warm_days=90)
    rng = np.random.default_rng(777)
    hashes = {}
    t0 = time.time()
    for d in range(1, 91):
        live_one_day(w, rng)
        if d in (30, 90):
            hashes[d] = persistence.world_hash(w)
    return hashes, time.time() - t0


off, t_off = run("off")
on, t_on = run("v1")
ok = off == on
print("day30 off", off[30][:16], "on", on[30][:16], "EQ", off[30] == on[30])
print("day90 off", off[90][:16], "on", on[90][:16], "EQ", off[90] == on[90])
print("wall: off %.1fs on %.1fs speedup %.1fx" % (t_off, t_on, t_off / max(t_on, 1e-9)))
print("GATE", "PASS" if ok else "FAIL")
