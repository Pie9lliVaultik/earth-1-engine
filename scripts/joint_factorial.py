"""0.8 Iteration 2 — the joint conviction × relax factorial.

Runs JOINT_LAW_EXPERIMENT_0_8_IT2.md exactly: 30 cells, 200k
no-news worlds, 120 days with the homogenization panel every 10
days, then a paired 30-day tau fork at day 90. One process per cell
(spawn-isolated: conviction patches never cross arms).
"""
import copy
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

N = int(os.environ.get("EARTH1_JF_N", "200000"))
DAYS = int(os.environ.get("EARTH1_JF_DAYS", "120"))
TAU_AT = int(os.environ.get("EARTH1_JF_TAU_AT", "90"))
TAU_DAYS = int(os.environ.get("EARTH1_JF_TAU_DAYS", "30"))
SEED = 8820
CH = 2                                  # ECONOMICS shock channel

CONVICTION = {
    "A0": None,                          # incumbent
    "A1": ("c1", 0.06, 0.02), "A2": ("c1", 0.06, 0.05),
    "A3": ("c2", 0.06, 0.02), "A4": ("c2", 0.06, 0.05),
    "A5": ("c3", 0.10, 0.0),
}
RELAX = {"B0": 0.25, "B1": 0.129, "B2": 0.067, "B3": 0.045,
         "B4": 0.010}
OUT = Path(os.environ.get("EARTH1_JF_OUT",
                          str(ROOT / "data" / "joint_factorial_0_8")))


def panel(w, genesis_sd):
    from earth1.influence import propagate  # noqa: F401 (doc anchor)
    civ = w.civ
    alive = w.health.alive
    f = civ.forces[alive]
    a = civ.alpha[alive]
    adj = civ.adj
    deg = np.maximum(np.asarray(adj.sum(axis=1)).ravel(), 1.0)
    nbmean = np.asarray(adj @ civ.forces) / deg[:, None]
    nbdist = np.abs(civ.forces - nbmean).mean(axis=1)[alive]
    pole = (civ.forces > 0.5).astype(np.float64)
    nb_pole = np.asarray(adj @ pole) / deg[:, None]
    agr = (1.0 - np.abs(nb_pole - pole).mean(axis=1))[alive]
    from earth1.life import life_force_target
    tgt = life_force_target(civ, w.life)
    pull = np.abs(tgt - civ.forces).mean(axis=1)[alive]
    country = civ.country[alive]
    ch_sd = f.std(axis=0)
    within = []
    means = []
    for c in np.unique(country):
        m = country == c
        if m.sum() >= 50:
            within.append(f[m].std(axis=0).mean())
            means.append(f[m].mean(axis=0))
    return {
        "alpha_mean": round(float(a.mean()), 4),
        "alpha_sd": round(float(a.std()), 4),
        "alpha_gt99": round(float((a > 0.99).mean()), 4),
        "alpha_floor": round(float((a < 0.05).mean()), 4),
        "one_minus_alpha_med": round(float(np.median(1.0 - a)), 4),
        "ch_sd": [round(float(v), 4) for v in ch_sd],
        "sd_ratio_genesis": round(float((ch_sd / genesis_sd).mean()), 3),
        "sat_hi": [round(float((f[:, c] > 0.95).mean()), 4)
                   for c in range(f.shape[1])],
        "sat_lo": [round(float((f[:, c] < 0.05).mean()), 4)
                   for c in range(f.shape[1])],
        "nb_dist_mean": round(float(nbdist.mean()), 4),
        "unanimous_share": round(float((agr > 0.95).mean()), 4),
        "push_potential": round(float(nbdist.mean()), 4),
        "pull_potential": round(float(pull.mean()), 4),
        "within_country_sd": round(float(np.mean(within)), 4),
        "between_country_sd": round(float(np.std(np.array(means),
                                                 axis=0).mean()), 4),
    }


def run_cell(task):
    akey, bkey = task
    import earth1.alive as am
    import earth1.lab_archive.conviction_lab as lab
    from earth1.alive import birth_world, live_one_day

    conv = CONVICTION[akey]
    relax = RELAX[bkey]
    w = birth_world(N, SEED)
    lab.ALPHA0 = w.civ.alpha.copy()
    if conv is not None:
        law, gain, lam = conv
        am.update_conviction = partial(lab.LAWS[law], gain=gain,
                                      lam=lam)
    rng = np.random.default_rng(SEED)
    genesis_sd = w.civ.forces[w.health.alive].std(axis=0)

    panels = {}
    tau = None
    for d in range(1, DAYS + 1):
        live_one_day(w, rng, relax=relax)
        if d % 10 == 0:
            panels[str(d)] = panel(w, genesis_sd)
        if d == TAU_AT:
            rng_state = rng.bit_generator.state
            w2 = copy.deepcopy(w)
            rng2 = np.random.default_rng()
            rng2.bit_generator.state = rng_state
            idx = np.random.default_rng(99).choice(
                np.flatnonzero(w.health.alive), size=N // 4,
                replace=False)
            col = w2.civ.forces[:, CH]
            col[idx] = np.clip(col[idx] + 0.15, 0.0, 1.0)
            deltas = [float(w2.civ.forces[idx, CH].mean()
                            - w.civ.forces[idx, CH].mean())]
            for _ in range(TAU_DAYS):
                live_one_day(w, rng, relax=relax)
                live_one_day(w2, rng2, relax=relax)
                deltas.append(float(w2.civ.forces[idx, CH].mean()
                                    - w.civ.forces[idx, CH].mean()))
            d0 = deltas[0]
            half = None
            for i in range(1, len(deltas)):
                if abs(deltas[i]) <= abs(d0) / 2:
                    half = i
                    break
            tau = {"half_life_d": half,
                   "resid_d30": round(deltas[-1] / d0, 3) if d0 else None,
                   "deltas": [round(x, 5) for x in deltas]}
            # continue the UNSHOCKED world to DAYS for the panel
    return {"cell": f"{akey}x{bkey}", "conviction": akey,
            "relax": relax, "panels": panels, "tau": tau}


def main():
    tasks = [(a, b) for a in CONVICTION for b in RELAX]
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    results = []
    ctx = mp.get_context("spawn")
    with ctx.Pool(processes=min(30, len(tasks))) as pool:
        for r in pool.imap_unordered(run_cell, tasks):
            results.append(r)
            p = r["panels"].get(str(DAYS), {})
            print(f"  {r['cell']}: alpha {p.get('alpha_mean')} "
                  f"sd_ratio {p.get('sd_ratio_genesis')} "
                  f"unanimous {p.get('unanimous_share')} "
                  f"tau {r['tau']['half_life_d'] if r['tau'] else None}",
                  flush=True)
    (OUT / "cells.json").write_text(json.dumps(results, indent=1))
    print(f"\nFACTORIAL COMPLETE {round((time.monotonic()-t0)/60,1)} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
