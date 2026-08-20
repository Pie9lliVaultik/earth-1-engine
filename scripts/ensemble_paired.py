"""0.7 — the frozen paired-ensemble workload, run for real.

See ops/alive/ENSEMBLE_PROTOCOL_0_7.md — the workload is frozen there;
this runner implements it and refuses to drift from it. Worker count
and threads are the only free parameters (the saturation study's job).

    EARTH1_ENSEMBLE_SNAPSHOT=/path/to/materialized/backup \
    EARTH1_ENSEMBLE_WORKERS=40 \
    python3 scripts/ensemble_paired.py

Saturation subsets (contract §6) may shrink the job — full-run
artifacts refuse to be written unless the workload matches the frozen
protocol exactly:

    EARTH1_ENSEMBLE_PAIRS=4 EARTH1_ENSEMBLE_DAYS=5 ...   # subset

The parent loads the baseline once; each member runs in its own forked
process (one process per member, copy-on-write pages privatize as the
member's world diverges). No member state outlives its process — prime
instantiates disposable worlds only.
"""
import json
import os
import resource
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS",
                      os.environ.get("EARTH1_ENSEMBLE_THREADS", "1"))

import multiprocessing as mp

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ── frozen protocol constants (ENSEMBLE_PROTOCOL_0_7.md) ─────────────
FROZEN_PAIRS = 20
FROZEN_DAYS = 30
SEED_BASE = 700000
FEAR_SHOCK = 0.20
FROZEN_SNAPSHOT_SHA = ("379212b25f5735202aa3e9dd7f18fcf397451756"
                       "df6c60d388471e41eb7cef2c")

SNAPSHOT = Path(os.environ["EARTH1_ENSEMBLE_SNAPSHOT"])
WORKERS = int(os.environ.get("EARTH1_ENSEMBLE_WORKERS", "40"))
PAIRS = int(os.environ.get("EARTH1_ENSEMBLE_PAIRS", str(FROZEN_PAIRS)))
DAYS = int(os.environ.get("EARTH1_ENSEMBLE_DAYS", str(FROZEN_DAYS)))
OUT = Path(os.environ.get("EARTH1_ENSEMBLE_OUT",
                          str(ROOT / "data" / "ensemble_0_7")))

BASE = None          # the loaded world, shared into children by fork
TARGET_COUNTRY = None


def _target_country(w):
    """Most populous country of the frozen baseline — deterministic."""
    from earth1.genesis import GENESIS_COUNTRIES
    alive = w.health.alive
    counts = np.bincount(w.civ.country[alive])
    idx = int(counts.argmax())
    entry = GENESIS_COUNTRIES[idx]
    name = entry["name"] if isinstance(entry, dict) else str(entry)
    return idx, name, int(counts[idx])


def run_member(task):
    """One ensemble member, in its own forked process. BASE arrived by
    fork; mutating it here privatizes only this process's pages."""
    pair, kind = task
    from earth1 import persistence
    from earth1.alive import live_one_day
    from earth1.types import Force

    w = BASE                       # this process's COW copy — private
    tgt_idx, tgt_name, _ = TARGET_COUNTRY
    if kind == "scenario":
        mask = w.health.alive & (w.civ.country == tgt_idx)
        f = w.civ.forces[:, Force.FEAR]
        f[mask] = np.clip(f[mask] + FEAR_SHOCK, 0.0, 1.0)

    seed = SEED_BASE + pair
    rng = np.random.default_rng(seed)
    per_day = []
    deaths = 0
    t0 = time.monotonic()
    for _ in range(DAYS):
        td = time.monotonic()
        st = live_one_day(w, rng)
        per_day.append(round(time.monotonic() - td, 2))
        deaths += int(st.get("deaths", 0))
    wall = time.monotonic() - t0

    alive = w.health.alive
    life = w.life
    emp = float(life.employed[alive & life.in_lf].mean()) \
        if (alive & life.in_lf).any() else None
    tmask = alive & (w.civ.country == tgt_idx)
    return {
        "pair": pair, "kind": kind, "seed": seed, "days": DAYS,
        "world_hash": persistence.world_hash(w),
        "day_end": int(w.day),
        "alive_end": int(alive.sum()),
        "deaths_total": deaths,
        "employment_rate": round(emp, 5) if emp is not None else None,
        "mean_fear_target": round(
            float(w.civ.forces[tmask, Force.FEAR].mean()), 5),
        "wall_s": round(wall, 1),
        "per_day_s": per_day,
        "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main():
    global BASE, TARGET_COUNTRY
    from earth1 import persistence
    from earth1.alive import CANONICAL_DAY
    from earth1.manifest import Manifest, snapshot_identity

    t_job = time.monotonic()
    ident = snapshot_identity(SNAPSHOT)
    is_frozen_run = (PAIRS == FROZEN_PAIRS and DAYS == FROZEN_DAYS
                     and ident.get("world_pkl_sha256")
                     == FROZEN_SNAPSHOT_SHA)

    stamp = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())
    run_dir = OUT / (f"run_{stamp}_p{PAIRS}d{DAYS}w{WORKERS}"
                     + ("" if is_frozen_run else "_SUBSET"))
    man = Manifest(
        run_dir, experiment="paired_ensemble_0_7",
        snapshot_dir=SNAPSHOT,
        config={"CANONICAL_DAY": dict(CANONICAL_DAY), "pairs": PAIRS,
                "days": DAYS, "seed_base": SEED_BASE,
                "fear_shock": FEAR_SHOCK,
                "frozen_workload": is_frozen_run},
        seeds={"member": f"{SEED_BASE}+i, shared within pair"},
        workers=WORKERS,
        threads_per_worker=int(os.environ["OMP_NUM_THREADS"]))

    print(f"loading baseline from {SNAPSHOT}", flush=True)
    t0 = time.monotonic()
    legacy = SNAPSHOT / "adj.npz"
    BASE, _rng, info = persistence.load_world(
        SNAPSHOT / "world.pkl",
        adj_path=(legacy if legacy.exists() else None))
    load_s = time.monotonic() - t0
    TARGET_COUNTRY = _target_country(BASE)
    print(f"  day {BASE.day}, alive {int(BASE.health.alive.sum()):,}, "
          f"schema v{info['schema_version']}, load {load_s:.0f}s; "
          f"target={TARGET_COUNTRY[1]} ({TARGET_COUNTRY[2]:,} alive)",
          flush=True)

    tasks = [(i, kind) for i in range(1, PAIRS + 1)
             for kind in ("control", "scenario")]
    load_samples = []
    results = []
    ctx = mp.get_context("fork")
    t1 = time.monotonic()
    with ctx.Pool(processes=WORKERS, maxtasksperchild=1) as pool:
        for r in pool.imap_unordered(run_member, tasks):
            results.append(r)
            load_samples.append(
                {"t": round(time.monotonic() - t1, 1),
                 "loadavg": os.getloadavg()[0],
                 "done": len(results)})
            print(f"  [{len(results):2d}/{len(tasks)}] pair {r['pair']:2d}"
                  f" {r['kind']:8s} {r['wall_s']:7.1f}s "
                  f"alive {r['alive_end']:,}", flush=True)
    compute_s = time.monotonic() - t1

    results.sort(key=lambda r: (r["pair"], r["kind"]))
    deltas = []
    by = {(r["pair"], r["kind"]): r for r in results}
    for i in range(1, PAIRS + 1):
        c, s = by.get((i, "control")), by.get((i, "scenario"))
        if c and s:
            deltas.append({
                "pair": i,
                "d_alive": s["alive_end"] - c["alive_end"],
                "d_deaths": s["deaths_total"] - c["deaths_total"],
                "d_employment": (round(s["employment_rate"]
                                       - c["employment_rate"], 5)
                                 if c["employment_rate"] is not None
                                 else None),
                "d_fear_target": round(s["mean_fear_target"]
                                       - c["mean_fear_target"], 5),
            })

    wall_total = time.monotonic() - t_job
    member_walls = [r["wall_s"] for r in results]
    summary = {
        "frozen_workload": is_frozen_run,
        "pairs": PAIRS, "days": DAYS, "workers": WORKERS,
        "threads_per_worker": int(os.environ["OMP_NUM_THREADS"]),
        "target_country": {"index": TARGET_COUNTRY[0],
                           "name": TARGET_COUNTRY[1],
                           "alive": TARGET_COUNTRY[2]},
        "wall_clock_total_s": round(wall_total, 1),
        "under_30_min": wall_total < 1800,
        "phase_s": {"load": round(load_s, 1),
                    "compute": round(compute_s, 1),
                    "orchestration": round(
                        wall_total - load_s - compute_s, 1)},
        "member_wall_s": {"min": min(member_walls),
                          "mean": round(float(np.mean(member_walls)), 1),
                          "max": max(member_walls)},
        "sum_cpu_proxy_s": round(sum(member_walls), 1),
        "world_days_per_wall_s": round(PAIRS * 2 * DAYS / wall_total, 2),
        "peak_member_rss_gb": round(
            max(r["max_rss_kb"] for r in results) / 1e6, 1),
        "loadavg_samples": load_samples[::4],
    }

    (run_dir / "results.json").write_text(json.dumps(results, indent=1))
    (run_dir / "pair_deltas.json").write_text(json.dumps(deltas, indent=1))
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=1))
    for f in ("results.json", "pair_deltas.json", "summary.json"):
        man.add_artifact(run_dir / f)
    man.close()

    verdict = "UNDER" if summary["under_30_min"] else "OVER"
    print(f"\nENSEMBLE {'FROZEN' if is_frozen_run else 'SUBSET'} run: "
          f"{wall_total/60:.1f} min — {verdict} the 30-min bar\n"
          f"  {run_dir}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
