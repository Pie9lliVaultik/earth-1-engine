"""0.8 IT5 JOINT PROGRAM — causal arms + variants + KA controls, as
frozen at IT5_BC_REGISTRATION.md (05b0cc6).

Fix components (independently attachable, spawn-isolated per arm):
  OP   dyadic operator family (propagate+feed dyadic; contagion
       ambient gain=0), default F1(k=3, mu=0.05)
  FLR  flourishing level-map conversion (or writes-disabled variant)
  CNV  C3 log-odds conviction at IT5-B gain (default 0.003)
Fix arms run at relax=0.045 (earned persistence region); incumbent
components run at their production forms; incumbent-relax arms 0.25.
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

N = int(os.environ.get("EARTH1_IT5_N", "200000"))
DAYS = int(os.environ.get("EARTH1_IT5_DAYS", "120"))
TAU_AT = int(os.environ.get("EARTH1_IT5_TAU_AT", "90"))
TAU_DAYS = int(os.environ.get("EARTH1_IT5_TAU_DAYS", "30"))
ALPHA_SNAP = (60, 90)
SEED = 8860
CH_TAU = 2
CH_TRANS = 5

# arm -> dict(op=None|(k,mu,gate), flr=None|"level"|"off",
#             cnv=None|gain, relax=float, extra=None|str)
ARMS = {
    "incumbent":  dict(op=None, flr=None, cnv=None, relax=0.25),
    "flr_only":   dict(op=None, flr="level", cnv=None, relax=0.25),
    "op_only":    dict(op=(3, 0.05, None), flr=None, cnv=None,
                       relax=0.045),
    "cnv_only":   dict(op=None, flr=None, cnv=0.003, relax=0.25),
    "flr_op":     dict(op=(3, 0.05, None), flr="level", cnv=None,
                       relax=0.045),
    "flr_cnv":    dict(op=None, flr="level", cnv=0.003, relax=0.25),
    "op_cnv":     dict(op=(3, 0.05, None), flr=None, cnv=0.003,
                       relax=0.045),
    "all3":       dict(op=(3, 0.05, None), flr="level", cnv=0.003,
                       relax=0.045),
    "all3_k1m15": dict(op=(1, 0.15, None), flr="level", cnv=0.003,
                       relax=0.045),
    "all3_k3m15": dict(op=(3, 0.15, None), flr="level", cnv=0.003,
                       relax=0.045),
    "all3_gate":  dict(op=(3, 0.05, 0.5), flr="level", cnv=0.003,
                       relax=0.045),
    "all3_g009":  dict(op=(3, 0.05, None), flr="level", cnv=0.009,
                       relax=0.045),
    "all3_g001":  dict(op=(3, 0.05, None), flr="level", cnv=0.001,
                       relax=0.045),
    "flr_off_all": dict(op=(3, 0.05, None), flr="off", cnv=0.003,
                        relax=0.045),
    "KA_zero":    dict(op=(0, 0.0, None), flr="level", cnv=0.003,
                       relax=0.045),
    "KA_instant": dict(op=(10, 0.9, None), flr="level", cnv=0.003,
                       relax=0.045),
    "KA_pull":    dict(op=(3, 0.05, None), flr="level", cnv=0.003,
                       relax=0.60),
    "KA_frozen":  dict(op=(3, 0.05, None), flr="level", cnv=0.003,
                       relax=0.005),
    "KA_ratchet": dict(op=(3, 0.05, None), flr="level", cnv=None,
                       relax=0.045),
    "KA_cnv0":    dict(op=(3, 0.05, None), flr="level", cnv=0.0,
                       relax=0.045),
    "KA_degtgt":  dict(op=(3, 0.05, None), flr="level", cnv=0.003,
                       relax=0.045, extra="degenerate_target"),
    "KA_fastmix": dict(op=(3, 0.05, None), flr="level", cnv=0.003,
                       relax=0.045, extra="fastmix"),
}
OUT = Path(os.environ.get("EARTH1_IT5_OUT",
                          str(ROOT / "data" / "joint_it5")))


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
        "sat_by_ch": [round(float(max((f[:, c] > 0.95).mean(),
                                      (f[:, c] < 0.05).mean())), 3)
                      for c in range(f.shape[1])],
        "unanimous_share": round(float((agr > 0.95).mean()), 4),
    }


def run_arm(name):
    import earth1.alive as am
    import earth1.contagion as cont
    import earth1.feed as feedmod
    import earth1.flourishing as flmod
    import earth1.life as lifemod
    import earth1.lab_archive.conviction_lab as clab
    import earth1.lab_archive.field_lab as flab
    from earth1.alive import birth_world, live_one_day
    from earth1.types import Force

    cfg = ARMS[name]
    w = birth_world(N, SEED)
    clab.ALPHA0 = w.civ.alpha.copy()
    flab.FLOUR_REF[0] = w.flourishing
    flab.AROUSAL = np.array(
        [feedmod.AROUSAL_WEIGHT[Force(k)] for k in range(8)])

    if cfg.get("extra") == "fastmix":
        import earth1.lab_archive.propagation_lab as plab
        for i, (tname, m) in enumerate(w.fabric.by_type.items()):
            w.fabric.by_type[tname] = plab.randomized_graph(
                m, seed=911 + i)
        from earth1.rehome import _recompose_adj
        _recompose_adj(w)

    if cfg["op"] is not None:
        k, mu, gate = cfg["op"]
        am.propagate = flab.make_dyadic_propagate(k=k, mu=mu, gate=gate)
        feedmod.feed_tick = flab.make_dyadic_feed(mu=mu, gate=gate)
        cont.CONTAGION_GAIN = 0.0
    if cfg["flr"] == "level":
        lifemod.life_force_target = flab.flourishing_level_map(
            lifemod.life_force_target)
        flmod.flourishing_tick = flab.flourishing_writes_disabled(
            flmod.flourishing_tick)
    elif cfg["flr"] == "off":
        flmod.flourishing_tick = flab.flourishing_writes_disabled(
            flmod.flourishing_tick)
    if cfg["cnv"] is not None:
        am.update_conviction = partial(clab.c3_logodds_symmetric,
                                      gain=cfg["cnv"])
    if cfg.get("extra") == "degenerate_target":
        orig = lifemod.life_force_target
        def deg_target(civ, life, _o=orig):
            t = _o(civ, life)
            t[:] = 0.9
            return t
        lifemod.life_force_target = deg_target

    relax = cfg["relax"]
    rng = np.random.default_rng(SEED)
    genesis_sd = w.civ.forces[w.health.alive].std(axis=0)
    panels, alpha_snaps = {}, {}
    tau = trans = None
    for d in range(1, DAYS + 1):
        flab._DAY[0] = d
        live_one_day(w, rng, relax=relax)
        if d in ALPHA_SNAP:
            alpha_snaps[d] = w.civ.alpha.copy()
        if d % 10 == 0:
            panels[str(d)] = panel(w, genesis_sd)
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
                flab._DAY[0] += 1
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
            trans = {"ring1_d30": round(float(
                w2.civ.forces[ring1, CH_TRANS].mean()
                - w.civ.forces[ring1, CH_TRANS].mean()), 5),
                "ring2_d30": round(float(
                    w2.civ.forces[ring2, CH_TRANS].mean()
                    - w.civ.forces[ring2, CH_TRANS].mean()), 5)}
    a60, a90 = alpha_snaps[ALPHA_SNAP[0]], alpha_snaps[ALPHA_SNAP[1]]
    alive = w.health.alive
    return {"arm": name, "cfg": {k: str(v) for k, v in cfg.items()},
            "panels": panels, "tau": tau, "transmission": trans,
            "softening_frac": round(float(
                (a90[alive] < a60[alive] - 1e-6).mean()), 4)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    results = []
    ctx = mp.get_context("spawn")
    with ctx.Pool(processes=min(22, len(ARMS))) as pool:
        for r in pool.imap_unordered(run_arm, list(ARMS)):
            results.append(r)
            p = r["panels"].get(str(DAYS), {})
            print(f"  [{len(results):2d}/{len(ARMS)}] {r['arm']:12s} "
                  f"tau {r['tau']['half_life_d'] if r['tau'] else '?'} "
                  f"r1 {r['transmission']['ring1_d30'] if r['transmission'] else '?'} "
                  f"r2 {r['transmission']['ring2_d30'] if r['transmission'] else '?'} "
                  f"a {p.get('alpha_mean')} soft {r['softening_frac']} "
                  f"sdr {p.get('sd_ratio_genesis')} "
                  f"sat {p.get('sat_max')}", flush=True)
    (OUT / "arms.json").write_text(json.dumps(results, indent=1))
    print(f"\nIT5 JOINT COMPLETE {round((time.monotonic()-t0)/60,1)} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
