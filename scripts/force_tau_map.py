"""0.8-A5 — restoring-force map on the production snapshot.

Per channel and direction: inject a delta on a fixed random 100k
cohort, evolve 10 days paired with an unperturbed control (same
seed), record the cohort-mean deviation trajectory -> half-life.
Placebo (magnitude 0) must decay exactly 0 (Standing Rule 2).
"""
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import multiprocessing as mp

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SNAPSHOT = Path(os.environ["EARTH1_ENSEMBLE_SNAPSHOT"])
DAYS = 10
SEED = 8803
COHORT = 100_000
OUT = Path(os.environ.get("EARTH1_TAU_OUT",
                          str(ROOT / "data" / "force_tau_0_8")))

BASE = None
COHORT_IDX = None


def run_arm(task):
    ch, mag = task
    from earth1.alive import live_one_day
    w = BASE
    if mag != 0.0:
        col = w.civ.forces[:, ch]
        col[COHORT_IDX] = np.clip(col[COHORT_IDX] + mag, 0.0, 1.0)
    rng = np.random.default_rng(SEED)
    traj = [float(w.civ.forces[COHORT_IDX, ch].mean())]
    for _ in range(DAYS):
        live_one_day(w, rng)
        traj.append(float(w.civ.forces[COHORT_IDX, ch].mean()))
    return {"channel": int(ch), "mag": float(mag), "traj": traj}


def main():
    global BASE, COHORT_IDX
    from earth1 import persistence
    from earth1.types import Force

    t0 = time.monotonic()
    legacy = SNAPSHOT / "adj.npz"
    BASE, _r, _i = persistence.load_world(
        SNAPSHOT / "world.pkl",
        adj_path=(legacy if legacy.exists() else None))
    rng0 = np.random.default_rng(4321)
    alive_idx = np.flatnonzero(BASE.health.alive)
    COHORT_IDX = rng0.choice(alive_idx, size=COHORT, replace=False)

    tasks = ([(ch, mag) for ch in range(8)
              for mag in (0.10, -0.10, 0.20, -0.20)]
             + [(0, 0.0)]                      # placebo
             + [(ch, 0.0) for ch in range(1, 8)])   # per-channel ctrl
    results = []
    ctx = mp.get_context("fork")
    with ctx.Pool(processes=min(40, len(tasks)),
                  maxtasksperchild=1) as pool:
        for r in pool.imap_unordered(run_arm, tasks):
            results.append(r)
            print(f"  ch{r['channel']} mag{r['mag']:+.2f} done",
                  flush=True)

    ctrl = {r["channel"]: r["traj"] for r in results if r["mag"] == 0.0}
    rows = []
    for r in results:
        if r["mag"] == 0.0:
            continue
        c = ctrl[r["channel"]]
        delta = [r["traj"][i] - c[i] for i in range(len(c))]
        d0 = delta[0]
        half = None
        for i in range(1, len(delta)):
            if abs(delta[i]) <= abs(d0) / 2:
                lo, hi = abs(delta[i - 1]), abs(delta[i])
                frac = ((lo - abs(d0) / 2) / (lo - hi)) if lo != hi else 0
                half = round(i - 1 + frac, 2)
                break
        rows.append({"channel": Force(r["channel"]).name,
                     "mag": r["mag"], "d0": round(d0, 5),
                     "delta_traj": [round(x, 5) for x in delta],
                     "half_life_days": half,
                     "remaining_frac_d10": round(delta[-1] / d0, 4)
                     if d0 else None})
    placebo_max = max(abs(r["traj"][i] - ctrl[0][i])
                      for r in results if r["mag"] == 0.0
                      and r["channel"] == 0
                      for i in range(len(r["traj"])))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tau_map.json").write_text(json.dumps(
        {"rows": rows, "placebo_max_dev": placebo_max,
         "days": DAYS, "cohort": COHORT,
         "wall_min": round((time.monotonic() - t0) / 60, 1)}, indent=1))
    for row in sorted(rows, key=lambda x: (x["channel"], x["mag"])):
        print(f"{row['channel']:12s} {row['mag']:+.2f} d0={row['d0']:+.4f} "
              f"t1/2={row['half_life_days']} "
              f"left@d10={row['remaining_frac_d10']}")
    print(f"placebo max dev: {placebo_max}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
