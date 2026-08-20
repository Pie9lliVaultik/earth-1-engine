"""V3 ensemble-consistency study — 0.7 (founder Ruling A).

Four independent ensembles from the frozen day-1142 snapshot
(PRECISION_EQUIVALENCE_PROTOCOL_0_7_V3.md): f64 reference A, f64
known-answer B, f32 candidate X, f16 degraded control C. No pairing
across arms — the comparison is distributional. Fresh seeds per arm.

    EARTH1_ENSEMBLE_SNAPSHOT=... EARTH1_AB_WORKERS=40 \
    python3 scripts/precision_ab_v3.py
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

#        arm  precision           seed_base  pairs
ARMS = (("A", "float64",          730000,    10),
        ("B", "float64",          731000,    10),
        ("X", "float32",          732000,    10),
        ("C", "float16-control",  733000,     3))
FEAR_SHOCK = -0.20
DAYS = 30
HORIZONS = (3, 15, 30)

SNAPSHOT = Path(os.environ["EARTH1_ENSEMBLE_SNAPSHOT"])
WORKERS = int(os.environ.get("EARTH1_AB_WORKERS", "40"))
OUT = Path(os.environ.get("EARTH1_AB_OUT",
                          str(ROOT / "data" / "precision_ab_0_7_v3")))

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
    arm, precision, seed, kind = task
    from earth1.alive import live_one_day
    from earth1.observables import collect
    from earth1.precision import apply_precision, world_precision
    from earth1.types import Force

    w = copy.deepcopy(BASE) if precision != "float64" else BASE
    apply_precision(w, precision)

    if kind == "scenario":
        mask = w.health.alive & (w.civ.country == TARGET[0])
        fcol = w.civ.forces[:, Force.FEAR]
        fcol[mask] = np.clip(fcol[mask] + FEAR_SHOCK, 0.0, 1.0)

    rng = np.random.default_rng(seed)
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
    return {"arm": arm, "precision": precision, "seed": seed,
            "kind": kind, "world_precision": world_precision(w),
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
        run_dir, experiment="precision_ensemble_consistency_v3",
        snapshot_dir=SNAPSHOT,
        config={"CANONICAL_DAY": dict(CANONICAL_DAY),
                "arms": [list(a) for a in ARMS], "days": DAYS,
                "horizons": list(HORIZONS), "fear_shock": FEAR_SHOCK},
        seeds={a[0]: f"{a[2]}+i, i=1..{a[3]}, shared within pair"
               for a in ARMS},
        workers=WORKERS, threads_per_worker=1)

    print(f"loading f64 baseline from {SNAPSHOT}", flush=True)
    legacy = SNAPSHOT / "adj.npz"
    BASE, _r, info = persistence.load_world(
        SNAPSHOT / "world.pkl",
        adj_path=(legacy if legacy.exists() else None))
    TARGET = _target_country(BASE)
    print(f"  day {BASE.day}, target={TARGET[1]}", flush=True)

    tasks = [(arm, prec, base + i, kind)
             for arm, prec, base, n in ARMS
             for i in range(1, n + 1)
             for kind in ("control", "scenario")]

    results = []
    ctx = mp.get_context("fork")
    with ctx.Pool(processes=WORKERS, maxtasksperchild=1) as pool:
        for r in pool.imap_unordered(run_member, tasks):
            results.append(r)
            print(f"  [{len(results):2d}/{len(tasks)}] {r['arm']} "
                  f"seed {r['seed']} {r['kind']:8s} "
                  f"{r['wall_s']:7.1f}s", flush=True)

    results.sort(key=lambda r: (r["arm"], r["seed"], r["kind"]))
    (run_dir / "members.json").write_text(json.dumps(results, indent=1))
    man.add_artifact(run_dir / "members.json")
    man.data["wall_clock_total_s"] = round(time.monotonic() - t_job, 1)
    man.close()
    print(f"\nV3 STUDY COMPLETE {round((time.monotonic()-t_job)/60,1)} "
          f"min -> {run_dir}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
