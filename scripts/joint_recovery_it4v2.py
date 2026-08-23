"""0.8 IT4-v2 — joint field recovery, exactly as frozen
(JOINT_FIELD_RECOVERY_0_8_IT4V2.md). 48 factorial cells + 5 KA arms.
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

N = int(os.environ.get("EARTH1_IT4_N", "200000"))
DAYS = int(os.environ.get("EARTH1_IT4_DAYS", "120"))
TAU_AT = int(os.environ.get("EARTH1_IT4_TAU_AT", "90"))
TAU_DAYS = int(os.environ.get("EARTH1_IT4_TAU_DAYS", "30"))
ALPHA_SNAP = (60, 90)
SEED = 8840
CH_TAU = 2
CH_TRANS = 5
OUT = Path(os.environ.get("EARTH1_IT4_OUT",
                          str(ROOT / "data" / "joint_recovery_it4v2")))

ETAS = {"e18": 0.18, "e05": 0.05, "e02": 0.02}
RELAXES = {"r25": 0.25, "r067": 0.067, "r045": 0.045, "r01": 0.01}
CONVS = {"inc": None, "c1": ("c1", 0.06, 0.05),
         "c2": ("c2", 0.06, 0.05), "c3": ("c3", 0.10, 0.0)}

CELLS = {f"{e}_{r}_{c}": (dict(eta=ETAS[e]), RELAXES[r], CONVS[c])
         for e in ETAS for r in RELAXES for c in CONVS}
CELLS.update({
    "KAa": (dict(eta=0.0), 0.067, CONVS["c1"]),
    "KAb": (dict(eta=0.5, layers=4), 0.25, None),
    "KAc": (dict(eta=0.05), 0.60, CONVS["c1"]),
    "KAd": (dict(eta=0.02), 0.005, CONVS["c1"]),
    "KAe": (dict(eta=0.05), 0.067, ("nc3", 0.0, 0.02)),
})


def panel(w, genesis_sd):
    civ = w.civ
    alive = w.health.alive
    f = civ.forces[alive]
    a = civ.alpha[alive]
    adj = civ.adj
    deg = np.maximum(np.asarray(adj.sum(axis=1)).ravel(), 1.0)
    pole = (civ.forces > 0.5).astype(np.float64)
    nb_pole = np.asarray(adj @ pole) / deg[:, None]
    agr = (1.0 - np.abs(nb_pole - pole).mean(axis=1))[alive]
    ch_sd = f.std(axis=0)
    return {
        "alpha_mean": round(float(a.mean()), 4),
        "alpha_sd": round(float(a.std()), 4),
        "alpha_gt99": round(float((a > 0.99).mean()), 4),
        "alpha_floor": round(float((a < 0.05).mean()), 4),
        "one_minus_alpha_med": round(float(np.median(1.0 - a)), 4),
        "sd_ratio_genesis": round(float((ch_sd / genesis_sd).mean()), 3),
        "sat_max": round(float(max(
            max((f[:, c] > 0.95).mean(), (f[:, c] < 0.05).mean())
            for c in range(f.shape[1]))), 4),
        "unanimous_share": round(float((agr > 0.95).mean()), 4),
    }


def run_cell(name):
    import earth1.alive as am
    import earth1.lab_archive.propagation_lab as plab
    import earth1.lab_archive.conviction_lab as clab
    from earth1.alive import birth_world, live_one_day

    op_kwargs, relax, conv = CELLS[name]
    w = birth_world(N, SEED)
    clab.ALPHA0 = w.civ.alpha.copy()
    am.propagate = plab.make_operator(**op_kwargs)
    if conv is not None:
        law, gain, lam = conv
        am.update_conviction = partial(clab.LAWS[law], gain=gain,
                                      lam=lam)
    rng = np.random.default_rng(SEED)
    genesis_sd = w.civ.forces[w.health.alive].std(axis=0)

    panels, contractions = {}, {}
    alpha_snaps = {}
    tau = trans = None
    for d in range(1, DAYS + 1):
        plab._DAY[0] = d
        plab.PASS_LOG.clear()
        live_one_day(w, rng, relax=relax)
        if d in ALPHA_SNAP:
            alpha_snaps[d] = w.civ.alpha.copy()
        if d % 10 == 0:
            panels[str(d)] = panel(w, genesis_sd)
            log = plab.PASS_LOG
            if log:
                ratios = [va / vb for _, _, vb, va in log if vb > 0]
                contractions[str(d)] = round(float(np.mean(ratios)), 5)
        if d == TAU_AT:
            rng_state = rng.bit_generator.state
            w2 = copy.deepcopy(w)
            rng2 = np.random.default_rng()
            rng2.bit_generator.state = rng_state
            gr = np.random.default_rng(99)
            alive_idx = np.flatnonzero(w.health.alive)
            idx = gr.choice(alive_idx, size=N // 4, replace=False)
            col = w2.civ.forces[:, CH_TAU]
            col[idx] = np.clip(col[idx] + 0.15, 0.0, 1.0)
            seeds = gr.choice(alive_idx,
                              size=min(5000, alive_idx.size // 8),
                              replace=False)
            colt = w2.civ.forces[:, CH_TRANS]
            colt[seeds] = np.clip(colt[seeds] + 0.30, 0.0, 1.0)
            adjc = w.civ.adj.tocsr()
            ring1 = np.setdiff1d(np.unique(adjc[seeds].indices), seeds)
            ring2 = np.setdiff1d(np.unique(adjc[ring1].indices),
                                 np.union1d(seeds, ring1))
            deltas = [float(w2.civ.forces[idx, CH_TAU].mean()
                            - w.civ.forces[idx, CH_TAU].mean())]
            for _ in range(TAU_DAYS):
                plab._DAY[0] += 1
                live_one_day(w, rng, relax=relax)
                live_one_day(w2, rng2, relax=relax)
                deltas.append(float(w2.civ.forces[idx, CH_TAU].mean()
                                    - w.civ.forces[idx, CH_TAU].mean()))
            d0 = deltas[0]
            half = None
            for i in range(1, len(deltas)):
                if abs(deltas[i]) <= abs(d0) / 2:
                    half = i
                    break
            tau = {"half_life_d": half,
                   "resid_d30": round(deltas[-1] / d0, 3) if d0 else None}
            trans = {
                "ring1_d30": round(float(
                    w2.civ.forces[ring1, CH_TRANS].mean()
                    - w.civ.forces[ring1, CH_TRANS].mean()), 5),
                "ring2_d30": round(float(
                    w2.civ.forces[ring2, CH_TRANS].mean()
                    - w.civ.forces[ring2, CH_TRANS].mean()), 5),
            }
    a60, a90 = alpha_snaps[ALPHA_SNAP[0]], alpha_snaps[ALPHA_SNAP[1]]
    alive = w.health.alive
    softening = float((a90[alive] < a60[alive] - 1e-6).mean())
    return {"cell": name, "relax": relax,
            "panels": panels, "contractions": contractions,
            "tau": tau, "transmission": trans,
            "softening_frac": round(softening, 4)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    results = []
    ctx = mp.get_context("spawn")
    with ctx.Pool(processes=int(os.environ.get("EARTH1_IT4_WORKERS",
                                               "27"))) as pool:
        for r in pool.imap_unordered(run_cell, list(CELLS)):
            results.append(r)
            p = r["panels"].get(str(DAYS), {})
            print(f"  [{len(results):2d}/{len(CELLS)}] {r['cell']}: "
                  f"tau {r['tau']['half_life_d'] if r['tau'] else '?'} "
                  f"ring1 {r['transmission']['ring1_d30'] if r['transmission'] else '?'} "
                  f"alpha {p.get('alpha_mean')} "
                  f"soft {r['softening_frac']} "
                  f"unan {p.get('unanimous_share')}", flush=True)
    (OUT / "cells.json").write_text(json.dumps(results, indent=1))
    print(f"\nIT4V2 COMPLETE {round((time.monotonic()-t0)/60,1)} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
