"""0.8 IT3 — the propagation-operator experiment, exactly as frozen
at 4b44e93 (PROPAGATION_LAW_EXPERIMENT_0_8_IT3.md).

18 arms: P1 magnitude (3 eta x 2 layers), P2 structure (2 delta x
pole on/off), P3 scheduling (2 exposure p), C0 incumbent reference,
KA1-KA5 known-answer controls. 200k no-news worlds, 120 days,
conviction = incumbent everywhere, relax = 0.25 everywhere except
KA5 (relax=0). Per-pass contraction logged inside every operator;
IT2 homogenization panel every 10 days; day-90 paired fork measures
BOTH tau (ECONOMICS +0.15, 25% cohort) and cross-person transmission
(CULTURE +0.30 on 5k seed agents; day-30 movement of their direct
non-seed neighbors).
"""
import copy
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

N = int(os.environ.get("EARTH1_IT3_N", "200000"))
DAYS = int(os.environ.get("EARTH1_IT3_DAYS", "120"))
TAU_AT = int(os.environ.get("EARTH1_IT3_TAU_AT", "90"))
TAU_DAYS = int(os.environ.get("EARTH1_IT3_TAU_DAYS", "30"))
SEED = 8830
CH_TAU = 2                # ECONOMICS
CH_TRANS = 5              # CULTURE
OUT = Path(os.environ.get("EARTH1_IT3_OUT",
                          str(ROOT / "data" / "propagation_it3")))

# arm -> (operator kwargs, relax, randomized_graph)
ARMS = {
    "C0":       (dict(), 0.25, False),
    "P1a": (dict(eta=0.05, layers=2), 0.25, False),
    "P1b": (dict(eta=0.02, layers=2), 0.25, False),
    "P1c": (dict(eta=0.005, layers=2), 0.25, False),
    "P1d": (dict(eta=0.05, layers=1), 0.25, False),
    "P1e": (dict(eta=0.02, layers=1), 0.25, False),
    "P1f": (dict(eta=0.005, layers=1), 0.25, False),
    "P2a": (dict(gate_delta=0.3), 0.25, False),
    "P2b": (dict(gate_delta=0.5), 0.25, False),
    "P2c": (dict(gate_delta=0.3, pole_on=False), 0.25, False),
    "P2d": (dict(gate_delta=0.5, pole_on=False), 0.25, False),
    "P3a": (dict(exposure_p=0.1), 0.25, False),
    "P3b": (dict(exposure_p=0.3), 0.25, False),
    "KA1": (dict(eta=0.5, layers=4), 0.25, False),
    "KA2": (dict(eta=0.0), 0.25, False),
    "KA3": (dict(gate_delta=0.05), 0.25, False),
    "KA4": (dict(), 0.25, True),
    "KA5": (dict(), 0.0, False),
}


def panel(w, genesis_sd):
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
    ch_sd = f.std(axis=0)
    return {
        "alpha_mean": round(float(a.mean()), 4),
        "alpha_sd": round(float(a.std()), 4),
        "alpha_gt99": round(float((a > 0.99).mean()), 4),
        "alpha_floor": round(float((a < 0.05).mean()), 4),
        "one_minus_alpha_med": round(float(np.median(1.0 - a)), 4),
        "sd_ratio_genesis": round(float((ch_sd / genesis_sd).mean()), 3),
        "sat_hi": [round(float((f[:, c] > 0.95).mean()), 4)
                   for c in range(f.shape[1])],
        "sat_lo": [round(float((f[:, c] < 0.05).mean()), 4)
                   for c in range(f.shape[1])],
        "nb_dist_mean": round(float(nbdist.mean()), 4),
        "unanimous_share": round(float((agr > 0.95).mean()), 4),
    }


def contraction_summary(log):
    if not log:
        return None
    by_layer = {}
    for day, layer, vb, va in log:
        by_layer.setdefault(layer, []).append(va / vb if vb > 0 else 1.0)
    return {f"layer{k}": {"mean_ratio": round(float(np.mean(v)), 5),
                          "min_ratio": round(float(np.min(v)), 5)}
            for k, v in sorted(by_layer.items())}


def run_arm(arm):
    import earth1.alive as am
    import earth1.propagation_lab as plab
    from earth1.alive import birth_world, live_one_day

    kwargs, relax, randomize = ARMS[arm]
    w = birth_world(N, SEED)
    if randomize:
        # randomize at the by_type level — the daily recompose rebuilds
        # civ.adj from by_type, so a top-level swap would be wiped on
        # day 1 (caught by the smoke: KA4 ran bit-identical to C0)
        for i, (tname, m) in enumerate(w.fabric.by_type.items()):
            w.fabric.by_type[tname] = plab.randomized_graph(
                m, seed=911 + i)
        from earth1.rehome import _recompose_adj
        _recompose_adj(w)
    am.propagate = plab.make_operator(**kwargs)
    rng = np.random.default_rng(SEED)
    genesis_sd = w.civ.forces[w.health.alive].std(axis=0)

    panels, contractions = {}, {}
    tau, trans = None, None
    for d in range(1, DAYS + 1):
        plab._DAY[0] = d
        plab.PASS_LOG.clear()
        live_one_day(w, rng, relax=relax)
        if d % 10 == 0:
            panels[str(d)] = panel(w, genesis_sd)
            contractions[str(d)] = contraction_summary(plab.PASS_LOG)
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
            nb = np.unique(adjc[seeds].indices)
            nb = np.setdiff1d(nb, seeds)
            deltas = [float(w2.civ.forces[idx, CH_TAU].mean()
                            - w.civ.forces[idx, CH_TAU].mean())]
            t0 = float(w2.civ.forces[nb, CH_TRANS].mean()
                       - w.civ.forces[nb, CH_TRANS].mean())
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
                   "resid_d30": round(deltas[-1] / d0, 3) if d0 else None,
                   "deltas": [round(x, 5) for x in deltas]}
            trans = {"neighbor_delta_d0": round(t0, 5),
                     "neighbor_delta_d30": round(
                         float(w2.civ.forces[nb, CH_TRANS].mean()
                               - w.civ.forces[nb, CH_TRANS].mean()), 5),
                     "n_neighbors": int(nb.size)}
    return {"arm": arm, "kwargs": {k: v for k, v in kwargs.items()},
            "relax": relax, "randomized": randomize,
            "panels": panels, "contractions": contractions,
            "tau": tau, "transmission": trans}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    results = []
    ctx = mp.get_context("spawn")
    with ctx.Pool(processes=min(18, len(ARMS))) as pool:
        for r in pool.imap_unordered(run_arm, list(ARMS)):
            results.append(r)
            p = r["panels"].get(str(DAYS), {})
            print(f"  {r['arm']}: sdr {p.get('sd_ratio_genesis')} "
                  f"unan {p.get('unanimous_share')} "
                  f"alpha {p.get('alpha_mean')} "
                  f"tau {r['tau']['half_life_d'] if r['tau'] else '?'} "
                  f"trans {r['transmission']['neighbor_delta_d30'] if r['transmission'] else '?'}",
                  flush=True)
    (OUT / "arms.json").write_text(json.dumps(results, indent=1))
    print(f"\nIT3 COMPLETE {round((time.monotonic()-t0)/60,1)} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
