"""0.8 candidate fitting — registry target T1 ONLY.

For each candidate law, grid over (gain, lam), and for each point:
grow a fresh 200k no-news world 60 days under the law, inject an
information-only force perturbation (+0.15 on a random 25% cohort,
channel ECONOMICS — chosen as the least-railed channel in every
census), evolve 30 days paired with an unshocked control (same seed),
and measure the cohort-delta half-life and day-30 residual.

T1 band (frozen): half-life 5–15 days AND residual fraction 0.2–0.6
at day 30. The battery uses the first grid point (row-major) inside
the band; if none qualifies for a law, that law FAILS fitting and
proceeds to no battery (reported per XI.A).
"""
import json
import os
import sys
import time
from functools import partial
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import multiprocessing as mp

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

N = int(os.environ.get("EARTH1_FIT_N", "200000"))
GROW_DAYS = int(os.environ.get("EARTH1_FIT_GROW", "60"))
TAU_DAYS = int(os.environ.get("EARTH1_FIT_TAU", "30"))
SEED = 8810
CH = 2                       # ECONOMICS
GRID = {
    "c1": [(g, l) for g in (0.06, 0.03) for l in (0.005, 0.01, 0.02,
                                                  0.05)],
    "c2": [(g, l) for g in (0.06, 0.03) for l in (0.005, 0.01, 0.02,
                                                  0.05)],
    "c3": [(g, 0.0) for g in (0.05, 0.10, 0.20, 0.40)],
}
OUT = Path(os.environ.get("EARTH1_FIT_OUT",
                          str(ROOT / "data" / "conviction_fit_0_8")))
if os.environ.get("EARTH1_FIT_SMOKE") == "1":
    GRID = {"c1": [(0.06, 0.02)], "c3": [(0.10, 0.0)]}


def run_point(task):
    law_name, gain, lam = task
    import earth1.alive as am
    import earth1.lab_archive.conviction_lab as lab
    from earth1.alive import birth_world, live_one_day

    w = birth_world(N, SEED)
    lab.ALPHA0 = w.civ.alpha.copy()
    am.update_conviction = partial(lab.LAWS[law_name], gain=gain,
                                  lam=lam)
    rng = np.random.default_rng(SEED)
    for _ in range(GROW_DAYS):
        live_one_day(w, rng)
    import copy
    rng_state = rng.bit_generator.state
    w2 = copy.deepcopy(w)
    rng2 = np.random.default_rng()
    rng2.bit_generator.state = rng_state

    idx = np.random.default_rng(99).choice(
        np.flatnonzero(w.health.alive), size=N // 4, replace=False)
    col = w2.civ.forces[:, CH]
    col[idx] = np.clip(col[idx] + 0.15, 0.0, 1.0)

    deltas = [float(w2.civ.forces[idx, CH].mean()
                    - w.civ.forces[idx, CH].mean())]
    for _ in range(TAU_DAYS):
        live_one_day(w, rng)
        live_one_day(w2, rng2)
        deltas.append(float(w2.civ.forces[idx, CH].mean()
                            - w.civ.forces[idx, CH].mean()))
    d0 = deltas[0]
    half = None
    for i in range(1, len(deltas)):
        if abs(deltas[i]) <= abs(d0) / 2:
            half = i
            break
    resid = deltas[-1] / d0 if d0 else None
    alpha_end = float(w.civ.alpha[w.health.alive].mean())
    return {"law": law_name, "gain": gain, "lam": lam,
            "half_life_d": half, "resid_d30": round(resid, 3),
            "alpha_d60": round(alpha_end, 4),
            "in_band": bool(half is not None and 5 <= half <= 15
                            and 0.2 <= resid <= 0.6),
            "deltas": [round(x, 5) for x in deltas]}


def main():
    tasks = [(law, g, l) for law, pts in GRID.items() for g, l in pts]
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    t0 = time.monotonic()
    ctx = mp.get_context("spawn")
    with ctx.Pool(processes=min(20, len(tasks))) as pool:
        for r in pool.imap_unordered(run_point, tasks):
            results.append(r)
            print(f"  {r['law']} g={r['gain']} l={r['lam']} "
                  f"t1/2={r['half_life_d']} resid={r['resid_d30']} "
                  f"alpha@60={r['alpha_d60']} "
                  f"{'IN BAND' if r['in_band'] else ''}", flush=True)
    (OUT / "fit_grid.json").write_text(json.dumps(results, indent=1))
    chosen = {}
    for law in GRID:
        for g, l in GRID[law]:
            hit = next((r for r in results if r["law"] == law
                        and r["gain"] == g and r["lam"] == l
                        and r["in_band"]), None)
            if hit:
                chosen[law] = {"gain": g, "lam": l}
                break
    (OUT / "chosen.json").write_text(json.dumps(chosen, indent=1))
    print(f"\nFIT COMPLETE {round((time.monotonic()-t0)/60,1)} min; "
          f"chosen: {chosen}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
