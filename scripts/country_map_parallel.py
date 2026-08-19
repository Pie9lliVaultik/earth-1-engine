"""Country map at N paired repeats — parallel across cores.

Each repeat is completely independent. Running them sequentially left
every core but one idle and turned a short job into a six-hour one.
"""
import json
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from earth1.alive import birth_world, live_one_day
from earth1.branch import apply
from earth1.genesis import GENESIS_COUNTRIES
from hormuz import SCENARIOS

SC = SCENARIOS[1]
NC = len(GENESIS_COUNTRIES)
POP = int(os.environ.get("CM_POP", "200000"))
DAYS = int(os.environ.get("CM_DAYS", "240"))
WARM = int(os.environ.get("CM_WARM", "60"))
REPS = int(os.environ.get("CM_REPS", "20"))


def unemp(w):
    lf = w.life.in_lf & w.health.alive
    a = np.bincount(w.civ.country, weights=lf.astype(float), minlength=NC)
    b = np.bincount(w.civ.country,
                    weights=(lf & ~w.life.employed).astype(float),
                    minlength=NC)
    return b / np.maximum(a, 1.0), a


def paired(seed):
    """Control and branch on IDENTICAL dice — the variance reduction."""
    out = {}
    for shock in (False, True):
        w = birth_world(POP, 42)
        r = np.random.default_rng(seed)
        for _ in range(WARM):
            live_one_day(w, r)
        if shock:
            apply(w, SC, r)
        for _ in range(DAYS):
            live_one_day(w, r)
        out[shock] = unemp(w)
    return out[True][0] - out[False][0], out[False][1]


def job(seed):
    d, lf = paired(seed)
    return seed, d.tolist(), lf.tolist()


def spear(a, b):
    ra = np.argsort(np.argsort(-a)).astype(float)
    rb = np.argsort(np.argsort(-b)).astype(float)
    ra -= ra.mean()
    rb -= rb.mean()
    d = np.linalg.norm(ra) * np.linalg.norm(rb)
    return float(ra @ rb / d) if d > 0 else 0.0


if __name__ == "__main__":
    seeds = [1000 + i for i in range(REPS)] + [5000 + i for i in range(REPS)]
    n_proc = min(len(seeds), max(1, (os.cpu_count() or 4) - 1))
    print(f"  {len(seeds)} paired worlds across {n_proc} processes",
          flush=True)
    with Pool(n_proc) as p:
        res = p.map(job, seeds)

    A = [np.array(d) for s, d, _ in sorted(res) if s < 5000]
    B = [np.array(d) for s, d, _ in sorted(res) if s >= 5000]
    lf = np.array(res[0][2])
    k = lf > 0

    print(f"\n  {'repeats':>8s} {'country rank corr':>19s}")
    out = []
    for n in (2, 4, 8, 12, 16, 20):
        if n > min(len(A), len(B)):
            break
        rc = spear(np.mean(A[:n], axis=0)[k], np.mean(B[:n], axis=0)[k])
        out.append({"repeats": n, "rank_corr": round(rc, 4)})
        print(f"  {n:8d} {rc:+19.3f}"
              + ("   <== WORKS" if rc >= 0.5 else ""), flush=True)
    json.dump({"pop": POP, "days": DAYS, "ladder": out},
              open("data/country_map_parallel.json", "w"), indent=1)
