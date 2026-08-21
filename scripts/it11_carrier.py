"""0.8 IT11 — informational persistence carrier (frozen:
IT11_INFORMATIONAL_CARRIER.md). Base = IT6-ALL; canonical Memory
inserted at day 90; carrier and expression measured separately."""
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

N = int(os.environ.get("EARTH1_IT11_N", "200000"))
DAYS = int(os.environ.get("EARTH1_IT11_DAYS", "90"))
WINDOW = int(os.environ.get("EARTH1_IT11_WIN", "30"))
SEED = 8903
HALF_LIFE = 720.0            # production value — the only scored one
SIG_FEAR = 0.50

# arm -> dict(event, half_life, spread, rehearsal_pool, delete_after,
#             sign, seed)
D = dict
ARMS = {
    "CAND":        D(event=True),
    "KA0_cont":    D(event=False, seed=8890),
    "KA1_delete":  D(event=True, delete_after=1),
    "KA2_nodecay": D(event=True, half_life=float("inf")),
    "KA4_scope":   D(event=True, spread=False),
    "KA6_neg":     D(event=True, sign=-1.0),
    "ABL_decay":   D(event=True, spread=False),   # decay only
    "ABL_spread":  D(event=True),                 # = CAND (attribution
                                                  # vs ABL_decay)
}
OUT = Path(os.environ.get("EARTH1_IT11_OUT",
                          str(ROOT / "data" / "it11")))


def run_arm(name):
    import earth1.alive as am
    import earth1.contagion as cont
    import earth1.feed as feedmod
    import earth1.flourishing as flmod
    import earth1.life as lifemod
    import earth1.conviction_lab as clab
    import earth1.field_lab as flab
    from earth1.alive import birth_world, live_one_day
    from earth1.memory import Memory, Chronicle
    from earth1.types import Force

    cfg = dict(ARMS[name])
    seed = int(cfg.get("seed", SEED))
    os.environ["EARTH1_CASCADE_COOLDOWN"] = "1"
    w = birth_world(N, seed)
    clab.ALPHA0 = w.civ.alpha.copy()
    flab.FLOUR_REF[0] = w.flourishing
    flab.AROUSAL = np.array(
        [feedmod.AROUSAL_WEIGHT[Force(k)] for k in range(8)])
    flab.DRIVE_ACC[0] = np.zeros(N)
    flab.ENC_COUNT[0] = np.zeros(N, dtype=np.int64)
    am.propagate = flab.make_dyadic_propagate_v6(3, 0.05)
    feedmod.feed_tick = flab.make_dyadic_feed_v6(0.05)
    cont.CONTAGION_GAIN = 0.0
    lifemod.life_force_target = flab.flourishing_level_map(
        lifemod.life_force_target)
    flmod.flourishing_tick = flab.flourishing_writes_disabled(
        flmod.flourishing_tick)

    def conv(forces, alpha, adj):
        n_enc = np.maximum(flab.ENC_COUNT[0], 1)
        drive = flab.DRIVE_ACC[0] / n_enc
        drive[flab.ENC_COUNT[0] == 0] = 0.0
        a = np.clip(alpha, 0.02, 0.98)
        out = np.clip(1 / (1 + np.exp(-(np.log(a / (1 - a))
                                        + 0.003 * drive))), 0.02, 1.0)
        flab.DRIVE_ACC[0][:] = 0.0
        flab.ENC_COUNT[0][:] = 0
        return out
    am.update_conviction = conv

    if cfg.get("spread") is False:
        Chronicle.spread = lambda self, civ, rng, rate=0.06: 0

    rng = np.random.default_rng(seed)
    for d in range(1, DAYS + 1):
        flab._DAY[0] = d
        live_one_day(w, rng, relax=0.045)

    # paired fork: event world vs control world
    rng_state = rng.bit_generator.state
    w2 = copy.deepcopy(w)
    rng2 = np.random.default_rng()
    rng2.bit_generator.state = rng_state

    loc = (w.civ.country.astype(np.int64) * 1000
           + w.civ.region.astype(np.int64) * 2
           + w.civ.urban.astype(np.int64))
    alive_idx = np.flatnonzero(w.health.alive)
    vals, counts = np.unique(loc[alive_idx], return_counts=True)
    big = vals[np.argmax(counts)]
    cand = alive_idx[loc[alive_idx] == big]
    cohort = cand[:min(5000, cand.size)]
    scope = np.zeros(N, dtype=bool)
    scope[cohort] = True
    other = alive_idx[loc[alive_idx] != big][:5000]

    mem = None
    if cfg.get("event", True):
        sig = np.zeros(8)
        sig[Force.FEAR] = SIG_FEAR * cfg.get("sign", 1.0)
        mem = Memory(id="it11:canonical", label="IT11 canonical event",
                     day=float(w2.day), force_signature=sig,
                     scope=scope.copy(),
                     half_life=cfg.get("half_life", HALF_LIFE),
                     origin="scenario")
        w2.chronicle.remember(mem)

    series = []
    for d in range(1, WINDOW + 1):
        flab._DAY[0] = DAYS + d
        if cfg.get("delete_after") and d == cfg["delete_after"] + 1:
            w2.chronicle.events = [m for m in w2.chronicle.events
                                   if m.id != "it11:canonical"]
        live_one_day(w, rng, relax=0.045)
        live_one_day(w2, rng2, relax=0.045)
        mm = next((m for m in w2.chronicle.events
                   if m.id == "it11:canonical"), None)
        series.append({
            "day": d,
            "salience": round(float(mm.salience), 5) if mm else None,
            "scope_n": int(mm.scope.sum()) if mm is not None
            and mm.scope is not None else 0,
            "rehearsals": int(mm.rehearsals) if mm else None,
            "cohort_fear_delta": round(float(
                w2.civ.forces[cohort, 0].mean()
                - w.civ.forces[cohort, 0].mean()), 5),
            "other_fear_delta": round(float(
                w2.civ.forces[other, 0].mean()
                - w.civ.forces[other, 0].mean()), 5),
        })
    d5 = series[4]["cohort_fear_delta"]
    d30 = series[-1]["cohort_fear_delta"]
    return {"arm": name, "cfg": {k: str(v) for k, v in cfg.items()},
            "series": series,
            "peak_d5": d5, "d30": d30,
            "resid_vs_peak": round(d30 / d5, 3) if d5 else None,
            "carrier_d30": series[-1]["salience"],
            "sat_check": round(float(max(
                max((w2.civ.forces[w2.health.alive][:, c] > 0.95
                     ).mean(),
                    (w2.civ.forces[w2.health.alive][:, c] < 0.05
                     ).mean())
                for c in range(8))), 4)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    results = []
    ctx = mp.get_context("spawn")
    with ctx.Pool(processes=min(8, len(ARMS))) as pool:
        for r in pool.imap_unordered(_worker, list(ARMS)):
            results.append(r)
            print(f"  [{len(results)}/{len(ARMS)}] {r['arm']:12s} "
                  f"peak5 {r['peak_d5']} d30 {r['d30']} "
                  f"resid {r['resid_vs_peak']} "
                  f"carrier {r['carrier_d30']} sat {r['sat_check']}",
                  flush=True)
    (OUT / "arms.json").write_text(json.dumps(results, indent=1))
    print(f"\nIT11 COMPLETE {round((time.monotonic()-t0)/60, 1)} min")
    return 0


def _worker(name):
    import scripts.it11_carrier as me
    return me.run_arm(name)


if __name__ == "__main__":
    sys.exit(main())
