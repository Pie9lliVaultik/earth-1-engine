"""MEANINGFUL CIVILIZATION OUTCOME PROBE — founder ruling post-v3.

Does Earth-1 compute a coherent causal chain from a material shock?
Canonical float64 only. Paired scenario/control branches from the
frozen day-1142 snapshot, identical seeds within a pair.

THE INTERVENTION — a recession, through existing mechanisms only:
`life.firm_health[firms of TARGET country] = 0.05` at branch day 0.
Two canonical channels respond (earth1/life.py life_tick):
  - failure hazard fail_p = RATE * (2 - health): a failure WAVE;
  - the hiring gate (firm_health > 0.25) excludes depressed firms:
    separations stop being replaced.
No new physics, no parameter changes; one recorded state edit.

ARMS
  main:    8 pairs, seeds 740001..740008, shock on the most populous
           country (India in this snapshot)
  placebo: 3 pairs, seeds 741001..741003, the SAME shock applied to
           the least-populous country's firms — the broken-path
           control: India and the world must show ~no effect, proving
           effects flow from the targeted mechanism, not from the act
           of intervening.

MEASUREMENT
  Daily causal-chain series (both arms, cohorts fixed at day 0 from
  the shared snapshot, identical indices in both arms by construction):
    HIT   = alive & in labour force & TARGET country
    COMP  = alive & in labour force & comparison country (2nd largest)
  employment, wage, wealth, deprivation, destitution, mental,
  relationship, addiction, evicted, FEAR/pole, hope proxy
  (flourishing.thirst), migration; world firms_failed/cascades.
  Full observable bundle at days 3/15/30.

Report everything as scenario - paired control. No tuning after
results (the shock magnitude was fixed by a single recorded sizing
pilot BEFORE the frozen run; pilot artifacts preserved).
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

SHOCK_HEALTH = 0.05
DAYS = 30
HORIZONS = (3, 15, 30)
ARMS = (("main", 740000, 8, "largest"),
        ("placebo", 741000, 3, "smallest"))

SNAPSHOT = Path(os.environ["EARTH1_ENSEMBLE_SNAPSHOT"])
WORKERS = int(os.environ.get("EARTH1_PROBE_WORKERS", "22"))
PAIR_OVERRIDE = os.environ.get("EARTH1_PROBE_PAIRS")   # sizing pilot
OUT = Path(os.environ.get("EARTH1_PROBE_OUT",
                          str(ROOT / "data" / "outcome_probe_0_7")))

BASE = None
GEO = None          # dict: largest/smallest/comparison country indices


def _geography(w):
    from earth1.genesis import GENESIS_COUNTRIES

    def name(i):
        e = GENESIS_COUNTRIES[i]
        return e["name"] if isinstance(e, dict) else str(e)
    counts = np.bincount(w.civ.country[w.health.alive])
    order = np.argsort(counts)[::-1]
    present = [int(c) for c in order if counts[c] > 0]
    return {"largest": (present[0], name(present[0])),
            "comparison": (present[1], name(present[1])),
            "smallest": (present[-1], name(present[-1]))}


def _cohort_stats(w, mask):
    life, civ = w.life, w.civ
    alive_m = mask & w.health.alive
    lf = alive_m & life.in_lf
    n = int(lf.sum())
    if n == 0:
        return None
    emp = lf & life.employed
    out = {
        "n_lf": n,
        "employment_rate": float(life.employed[lf].mean()),
        "wage_mean_employed": (float(life.wage[emp].mean())
                               if emp.any() else 0.0),
        "wealth_mean": float(life.wealth[alive_m].mean()),
        "deprivation_mean": float(life.deprivation[alive_m].mean()),
        "destitute_share": float((life.deprivation[alive_m]
                                  > 0.99).mean()),
        "mental_mean": float(life.mental[alive_m].mean()),
        "relationship_mean": float(life.relationship[alive_m].mean()),
        "addiction_mean": float(life.addiction[alive_m].mean()),
        "isolated_share": float((life.relationship[alive_m]
                                 < 0.25).mean()),
        "evicted_share": float(life.evicted[alive_m].mean()),
        "fear_mean": float(civ.forces[alive_m, 0].mean()),
        "pole_fear_share": float((civ.forces[alive_m, 0] > 0.5).mean()),
        "alive": int(alive_m.sum()),
    }
    if w.flourishing is not None and \
            getattr(w.flourishing, "thirst", None) is not None:
        out["thirst_mean"] = float(w.flourishing.thirst[alive_m].mean())
    return out


def run_member(task):
    arm, target_key, pair, seed, kind = task
    from earth1.alive import live_one_day
    from earth1.observables import collect

    w = BASE                        # forked COW copy — private
    tgt_idx = GEO[target_key][0]
    hit_mask = (w.health.alive & w.life.in_lf
                & (w.civ.country == GEO["largest"][0]))
    comp_mask = (w.health.alive & w.life.in_lf
                 & (w.civ.country == GEO["comparison"][0]))

    shocked_firms = 0
    if kind == "scenario":
        firms = np.flatnonzero(w.life.firm_country == tgt_idx)
        w.life.firm_health[firms] = SHOCK_HEALTH
        shocked_firms = int(firms.size)

    rng = np.random.default_rng(seed)
    cum = {}
    daily = []
    snaps = {}
    t0 = time.monotonic()
    for d in range(1, DAYS + 1):
        st = live_one_day(w, rng)
        for k in ("deaths", "births", "disease_deaths",
                  "rehomed_migrants", "rehomed_workers",
                  "cascades_fired", "firms_failed",
                  "ties_strengthened", "ties_pruned"):
            cum[k] = cum.get(k, 0) + int(st.get(k, 0) or 0)
        daily.append({
            "day": d,
            "firms_failed": int(st.get("firms_failed", 0) or 0),
            "hit": _cohort_stats(w, hit_mask),
            "comp": _cohort_stats(w, comp_mask),
        })
        if d in HORIZONS:
            snaps[str(d)] = collect(w, dict(cum))
    return {"arm": arm, "pair": pair, "seed": seed, "kind": kind,
            "target": {"key": target_key, "index": tgt_idx,
                       "name": GEO[target_key][1]},
            "shocked_firms": shocked_firms,
            "wall_s": round(time.monotonic() - t0, 1),
            "daily": daily, "horizons": snaps}


def main():
    global BASE, GEO
    from earth1 import persistence
    from earth1.alive import CANONICAL_DAY
    from earth1.manifest import Manifest
    from earth1.precision import world_precision

    t_job = time.monotonic()
    stamp = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())
    run_dir = OUT / f"run_{stamp}"

    print(f"loading f64 baseline from {SNAPSHOT}", flush=True)
    legacy = SNAPSHOT / "adj.npz"
    BASE, _r, info = persistence.load_world(
        SNAPSHOT / "world.pkl",
        adj_path=(legacy if legacy.exists() else None))
    GEO = _geography(BASE)
    assert world_precision(BASE) == "float64"
    print(f"  target={GEO['largest']}, comparison={GEO['comparison']}, "
          f"placebo-target={GEO['smallest']}", flush=True)

    arms = ARMS
    if PAIR_OVERRIDE:                       # sizing pilot: main arm only
        arms = (("pilot", 740000, int(PAIR_OVERRIDE), "largest"),)

    man = Manifest(
        run_dir, experiment="meaningful_outcome_probe_0_7",
        snapshot_dir=SNAPSHOT,
        config={"CANONICAL_DAY": dict(CANONICAL_DAY),
                "intervention": {"type": "firm_health_recession",
                                 "set_health": SHOCK_HEALTH,
                                 "mechanisms": ["failure_wave",
                                                "hiring_gate_0.25"]},
                "days": DAYS, "horizons": list(HORIZONS),
                "arms": [list(a) for a in arms],
                "precision": "float64"},
        seeds={a[0]: f"{a[1]}+i, i=1..{a[2]}" for a in arms},
        workers=WORKERS, threads_per_worker=1)

    tasks = [(arm, tkey, i, base + i, kind)
             for arm, base, n, tkey in arms
             for i in range(1, n + 1)
             for kind in ("control", "scenario")]

    results = []
    ctx = mp.get_context("fork")
    with ctx.Pool(processes=WORKERS, maxtasksperchild=1) as pool:
        for r in pool.imap_unordered(run_member, tasks):
            results.append(r)
            print(f"  [{len(results):2d}/{len(tasks)}] {r['arm']:8s} "
                  f"pair {r['pair']} {r['kind']:8s} "
                  f"shocked_firms={r['shocked_firms']:>6} "
                  f"{r['wall_s']:7.1f}s", flush=True)

    results.sort(key=lambda r: (r["arm"], r["pair"], r["kind"]))
    (run_dir / "members.json").write_text(json.dumps(results, indent=1))
    man.add_artifact(run_dir / "members.json")
    man.data["wall_clock_total_s"] = round(time.monotonic() - t_job, 1)
    man.close()
    print(f"\nPROBE COMPLETE {round((time.monotonic()-t_job)/60,1)} min "
          f"-> {run_dir}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
