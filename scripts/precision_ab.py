"""The pre-registered f32-vs-f64 equivalence study — 0.7.

Runs the matched quadruples of PRECISION_EQUIVALENCE_PROTOCOL_0_7.md:

    (control_i^64, scenario_i^64, control_i^32, scenario_i^32)  i=1..8
    + the float16-control degradation arm                       i=1..3

on the frozen day-1142 snapshot, seeds 710000+i shared across all
members of quadruple i, the frozen +0.20 FEAR scenario, 30 days,
observables recorded at days 3/15/30. One forked process per member;
precision applied AT LOAD, before the scenario perturbation — exactly
how a certified f32 ensemble would run.

    EARTH1_ENSEMBLE_SNAPSHOT=... EARTH1_AB_WORKERS=38 \
    python3 scripts/precision_ab.py
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

N_PAIRS = 8
N_CONTROL_PAIRS = 3            # float16-control arm
SEED_BASE = 710000
FEAR_SHOCK = 0.20
DAYS = 30
HORIZONS = (3, 15, 30)

SNAPSHOT = Path(os.environ["EARTH1_ENSEMBLE_SNAPSHOT"])
WORKERS = int(os.environ.get("EARTH1_AB_WORKERS", "38"))
OUT = Path(os.environ.get("EARTH1_AB_OUT",
                          str(ROOT / "data" / "precision_ab_0_7")))

BASE = None
TARGET = None


def _target_country(w):
    from earth1.genesis import GENESIS_COUNTRIES
    counts = np.bincount(w.civ.country[w.health.alive])
    idx = int(counts.argmax())
    e = GENESIS_COUNTRIES[idx]
    return idx, (e["name"] if isinstance(e, dict) else str(e))


def run_member(task):
    import copy
    pair, precision, kind = task
    from earth1.alive import live_one_day
    from earth1.observables import collect
    from earth1.precision import apply_precision, world_precision
    from earth1.types import Force

    w = copy.deepcopy(BASE) if precision != "float64" else BASE
    # (f64 members mutate their forked COW view directly; converted
    # members deepcopy first so conversion never leaks into the shared
    # parent pages seen by a member forked later in the same process —
    # maxtasksperchild=1 makes this belt-and-braces, not load-bearing)
    apply_precision(w, precision)

    if kind == "scenario":
        mask = w.health.alive & (w.civ.country == TARGET[0])
        fcol = w.civ.forces[:, Force.FEAR]
        fcol[mask] = np.clip(fcol[mask] + FEAR_SHOCK, 0.0, 1.0)

    rng = np.random.default_rng(SEED_BASE + pair)
    cum = {}
    snaps = {}
    t0 = time.monotonic()
    for d in range(1, DAYS + 1):
        st = live_one_day(w, rng)
        for k in ("deaths", "births", "disease_deaths",
                  "rehomed_migrants", "rehomed_workers", "cascades_fired",
                  "firms_failed", "ties_strengthened", "ties_weakened",
                  "ties_pruned", "ties_rewired"):
            cum[k] = cum.get(k, 0) + int(st.get(k, 0) or 0)
        if d in HORIZONS:
            snaps[str(d)] = collect(w, dict(cum))
    return {"pair": pair, "precision": precision, "kind": kind,
            "seed": SEED_BASE + pair,
            "world_precision": world_precision(w),
            "wall_s": round(time.monotonic() - t0, 1),
            "horizons": snaps}


def main():
    global BASE, TARGET
    from earth1 import persistence
    from earth1.alive import CANONICAL_DAY
    from earth1.manifest import Manifest

    t_job = time.monotonic()
    stamp = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())
    run_dir = OUT / f"run_{stamp}"
    man = Manifest(
        run_dir, experiment="precision_equivalence_0_7",
        snapshot_dir=SNAPSHOT,
        config={"CANONICAL_DAY": dict(CANONICAL_DAY), "pairs": N_PAIRS,
                "control_pairs": N_CONTROL_PAIRS, "days": DAYS,
                "horizons": list(HORIZONS), "seed_base": SEED_BASE,
                "fear_shock": FEAR_SHOCK,
                "precisions": ["float64", "float32", "float16-control"]},
        seeds={"member": f"{SEED_BASE}+i shared across quadruple"},
        workers=WORKERS, threads_per_worker=1)

    print(f"loading f64 baseline from {SNAPSHOT}", flush=True)
    legacy = SNAPSHOT / "adj.npz"
    BASE, _r, info = persistence.load_world(
        SNAPSHOT / "world.pkl",
        adj_path=(legacy if legacy.exists() else None))
    TARGET = _target_country(BASE)
    print(f"  day {BASE.day}, target={TARGET[1]}", flush=True)

    tasks = [(i, p, k)
             for i in range(1, N_PAIRS + 1)
             for p in ("float64", "float32")
             for k in ("control", "scenario")]
    tasks += [(i, "float16-control", k)
              for i in range(1, N_CONTROL_PAIRS + 1)
              for k in ("control", "scenario")]

    results = []
    ctx = mp.get_context("fork")
    with ctx.Pool(processes=WORKERS, maxtasksperchild=1) as pool:
        for r in pool.imap_unordered(run_member, tasks):
            results.append(r)
            print(f"  [{len(results):2d}/{len(tasks)}] pair "
                  f"{r['pair']} {r['precision']:15s} {r['kind']:8s} "
                  f"{r['wall_s']:7.1f}s", flush=True)

    results.sort(key=lambda r: (r["pair"], r["precision"], r["kind"]))
    (run_dir / "members.json").write_text(json.dumps(results, indent=1))
    man.add_artifact(run_dir / "members.json")
    man.data["wall_clock_total_s"] = round(time.monotonic() - t_job, 1)
    man.close()
    print(f"\nSTUDY COMPLETE {round((time.monotonic()-t_job)/60,1)} min "
          f"-> {run_dir}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
