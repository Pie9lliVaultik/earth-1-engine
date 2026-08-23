"""Probe 2 — transmission equilibrium, measured with full encounter
bookkeeping (founder spec). all3 base configuration; arms vary the
two levers the first-principles model predicts (source persistence
via relax; effective seed density via clustered seeding) plus a
no-pull attribution control. The registered 0.006 floor is NOT
touched; this probe explains the observed value from mechanism.

Arms:
  ref        random seeds, relax 0.045   (must reproduce ~0.0018)
  slow       random seeds, relax 0.02    (source persists longer)
  cluster    one-locality seeds, 0.045   (s_eff up for ring-1)
  cluster_sl one-locality seeds, 0.02
  nopull     random seeds, relax 0.045 grow, relax=0 during the
             30-day fork ONLY (attribution control, not a candidate)
"""
import copy
import json
import os
import sys
from functools import partial
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import multiprocessing as mp

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

N = int(os.environ.get("EARTH1_TP_N", "200000"))
GROW = int(os.environ.get("EARTH1_TP_GROW", "60"))
FORK = int(os.environ.get("EARTH1_TP_FORK", "30"))
SEED = 8870
CH = 5                       # CULTURE
ARMS = {
    "ref":        dict(relax=0.045, cluster=False, fork_relax=None),
    "slow":       dict(relax=0.02, cluster=False, fork_relax=None),
    "cluster":    dict(relax=0.045, cluster=True, fork_relax=None),
    "cluster_sl": dict(relax=0.02, cluster=True, fork_relax=None),
    "nopull":     dict(relax=0.045, cluster=False, fork_relax=0.0),
}
OUT = Path(os.environ.get("EARTH1_TP_OUT",
                          str(ROOT / "data" / "transmission_probe")))

ENC = {}          # per-day encounter bookkeeping


def make_instrumented_propagate(k, mu, seeded_mask_holder):
    import earth1.lab_archive.field_lab as flab

    def op(forces, alpha, adj, beta=1.0, layers=None,
           susceptibility=None, **kw):
        f = forces.copy()
        csr = adj if hasattr(adj, "indptr") else adj.tocsr()
        rng = np.random.default_rng(920_000 + flab._DAY[0])
        seeded = seeded_mask_holder[0]
        for _ in range(k):
            partner, has = flab._sample_partners(csr, rng)
            move = flab.dyadic_move(f, partner, has, mu,
                                    susceptibility)
            if seeded is not None:
                hit = has & seeded[np.clip(partner, 0, f.shape[0] - 1)]
                d = ENC.setdefault(int(flab._DAY[0]),
                                   {"enc_with_seed": 0,
                                    "dose_from_seed": 0.0})
                d["enc_with_seed"] += int(hit.sum())
                d["dose_from_seed"] += float(
                    np.abs(move[hit]).sum())
            f = np.clip(f + move, 0, 1)
        return f
    return op


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
    seeded_holder = [None]
    am.propagate = make_instrumented_propagate(3, 0.05, seeded_holder)
    feedmod.feed_tick = flab.make_dyadic_feed(mu=0.05)
    cont.CONTAGION_GAIN = 0.0
    lifemod.life_force_target = flab.flourishing_level_map(
        lifemod.life_force_target)
    flmod.flourishing_tick = flab.flourishing_writes_disabled(
        flmod.flourishing_tick)
    am.update_conviction = partial(clab.c3_logodds_symmetric,
                                  gain=0.003)

    rng = np.random.default_rng(SEED)
    for d in range(1, GROW + 1):
        flab._DAY[0] = d
        live_one_day(w, rng, relax=cfg["relax"])

    gr = np.random.default_rng(99)
    alive_idx = np.flatnonzero(w.health.alive)
    if cfg["cluster"]:
        loc = (w.civ.country.astype(np.int64) * 1000
               + w.civ.region.astype(np.int64) * 2
               + w.civ.urban.astype(np.int64))
        vals, counts = np.unique(loc[alive_idx], return_counts=True)
        big = vals[np.argmax(counts)]
        cand = alive_idx[loc[alive_idx] == big]
        seeds = cand[:min(5000, cand.size)]
    else:
        seeds = gr.choice(alive_idx,
                          size=min(5000, alive_idx.size // 8),
                          replace=False)
    seeded = np.zeros(N, dtype=bool)
    seeded[seeds] = True

    rng_state = rng.bit_generator.state
    w2 = copy.deepcopy(w)
    rng2 = np.random.default_rng()
    rng2.bit_generator.state = rng_state
    colt = w2.civ.forces[:, CH]
    colt[seeds] = np.clip(colt[seeds] + 0.30, 0.0, 1.0)
    adjc = w.civ.adj.tocsr()
    ring1 = np.setdiff1d(np.unique(adjc[seeds].indices), seeds)
    ring2 = np.setdiff1d(np.unique(adjc[ring1].indices),
                         np.union1d(seeds, ring1))
    ring3 = np.setdiff1d(np.unique(adjc[ring2].indices),
                         np.union1d(np.union1d(seeds, ring1), ring2))
    n_seed_nb = np.asarray(
        (adjc[ring1][:, seeds] != 0).sum(axis=1)).ravel()

    fork_relax = cfg["fork_relax"] if cfg["fork_relax"] is not None \
        else cfg["relax"]
    ENC.clear()
    seeded_holder[0] = seeded
    series = []
    for d in range(1, FORK + 1):
        flab._DAY[0] = GROW + d
        live_one_day(w, rng, relax=fork_relax)
        live_one_day(w2, rng2, relax=fork_relax)
        series.append({
            "day": d,
            "seed_delta": round(float(w2.civ.forces[seeds, CH].mean()
                                      - w.civ.forces[seeds, CH].mean()), 5),
            "ring1": round(float(w2.civ.forces[ring1, CH].mean()
                                 - w.civ.forces[ring1, CH].mean()), 5),
            "ring2": round(float(w2.civ.forces[ring2, CH].mean()
                                 - w.civ.forces[ring2, CH].mean()), 5),
            "ring3": round(float(w2.civ.forces[ring3, CH].mean()
                                 - w.civ.forces[ring3, CH].mean()), 5),
        })
    total_enc = sum(v["enc_with_seed"] for v in ENC.values())
    total_dose = sum(v["dose_from_seed"] for v in ENC.values())
    return {"arm": name, "cfg": cfg, "series": series,
            "n_ring1": int(ring1.size),
            "mean_seeded_neighbors_ring1": round(float(
                n_seed_nb.mean()), 3),
            "encounters_with_seed_total": total_enc,
            "dose_from_seed_total": round(total_dose, 2),
            "p_encounter_seed_per_day": round(
                total_enc / max(1, FORK) / max(1, ring1.size), 4)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    ctx = mp.get_context("spawn")
    with ctx.Pool(processes=len(ARMS)) as pool:
        for r in pool.imap_unordered(run_arm, list(ARMS)):
            results.append(r)
            last = r["series"][-1]
            print(f"  {r['arm']:10s} seed_d30 {last['seed_delta']:+.4f} "
                  f"r1 {last['ring1']:+.5f} r2 {last['ring2']:+.5f} "
                  f"r3 {last['ring3']:+.5f} "
                  f"nbseed {r['mean_seeded_neighbors_ring1']} "
                  f"pEnc {r['p_encounter_seed_per_day']}", flush=True)
    (OUT / "probe.json").write_text(json.dumps(results, indent=1))
    print("TRANSMISSION PROBE COMPLETE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
