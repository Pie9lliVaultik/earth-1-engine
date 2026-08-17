"""Predictive-value grid driver — RESUMABLE, supervisor-safe.

Runs (variant x benchmark x seed) per frozen/spec.json, appending each
completed combo to ledger.jsonl. Combos already in the ledger are
skipped, so the supervisor can kill/relaunch this process at any time
and no work is lost. Writes frozen/GRID_DONE when the grid is complete.

Parallelism: PV_WORKERS forked processes (Linux only). Each combo is a
full single-core leg; wall clock ~= combos / workers x leg time.
"""
from __future__ import annotations

import json
import os
import sys
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(__file__))

BASE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(BASE, "ledger.jsonl")
SPEC = json.load(open(os.path.join(BASE, "frozen", "spec.json")))

# smoke-run overrides (small-first rule). The REAL grid uses the frozen
# spec untouched; any override redirects the ledger so smoke results
# can never contaminate the registered ledger.
_POP = int(os.environ.get("PV_POP", SPEC["pop"]))
_YEARS = float(os.environ.get("PV_YEARS", SPEC["temporal"]["years"]))
if _POP != SPEC["pop"] or _YEARS != SPEC["temporal"]["years"]:
    LEDGER = os.path.join(BASE, "ledger_smoke.jsonl")


def _combos():
    for variant in SPEC["variants"]:
        for bench in SPEC["benchmarks"]:
            for seed in SPEC["seeds"]:
                yield {"variant": variant, "benchmark": bench, "seed": seed}


def _done_keys():
    if not os.path.exists(LEDGER):
        return set()
    keys = set()
    for line in open(LEDGER):
        try:
            r = json.loads(line)
            keys.add((r["variant"], r["benchmark"], r["seed"]))
        except (json.JSONDecodeError, KeyError):
            continue
    return keys


def run_combo(combo):
    """One grid cell. Runs in a forked worker; returns a ledger record."""
    os.environ.setdefault("OMP_NUM_THREADS", "2")
    variant = combo["variant"]
    tick_kwargs = SPEC["variants"][variant]
    rec = dict(combo)
    try:
        if combo["benchmark"] == "temporal_w6w7":
            from earth1.g5 import g5_temporal
            r = g5_temporal(pop=_POP, seed=combo["seed"],
                            years=_YEARS,
                            dt_days=SPEC["temporal"]["dt_days"],
                            tick_kwargs=tick_kwargs)
            rec.update(mae_engine=r.mae_engine, mae_nochange=r.mae_nochange,
                       sign_accuracy=r.sign_accuracy, sign_p=r.sign_p,
                       n_pairs=r.n_pairs)
        else:  # event_a3
            from earth1.g5 import g5_event_reaction
            from earth1.reaction_cases import COVID_RALLY
            r = g5_event_reaction(case=COVID_RALLY, pop=_POP,
                                  seed=combo["seed"],
                                  tick_kwargs=tick_kwargs)
            rec.update(ratio=r.ratio, sim_delta=r.sim_delta,
                       real_delta=r.real_delta, passes=r.passes)
        rec["ok"] = True
    except Exception:
        rec["ok"] = False
        rec["error"] = traceback.format_exc()[-800:]
    return rec


def main() -> None:
    done = _done_keys()
    todo = [c for c in _combos()
            if (c["variant"], c["benchmark"], c["seed"]) not in done]
    total = sum(1 for _ in _combos())
    print(f"grid: {total} combos, {len(done)} done, {len(todo)} to run",
          flush=True)
    if not todo:
        open(os.path.join(BASE, "frozen", "GRID_DONE"), "w").write("done\n")
        print("GRID-COMPLETE", flush=True)
        return

    workers = int(os.environ.get("PV_WORKERS", "20"))
    if workers > 1 and hasattr(os, "fork"):
        import multiprocessing as mp
        with mp.get_context("fork").Pool(workers) as pool:
            for rec in pool.imap_unordered(run_combo, todo):
                with open(LEDGER, "a") as f:
                    f.write(json.dumps(rec) + "\n")
                print(f"  {rec['variant']}/{rec['benchmark']}/s{rec['seed']}"
                      f" ok={rec['ok']}", flush=True)
    else:
        for combo in todo:
            rec = run_combo(combo)
            with open(LEDGER, "a") as f:
                f.write(json.dumps(rec) + "\n")
            print(f"  {rec['variant']}/{rec['benchmark']}/s{rec['seed']}"
                  f" ok={rec['ok']}", flush=True)

    if not [c for c in _combos()
            if (c["variant"], c["benchmark"], c["seed"]) not in _done_keys()]:
        open(os.path.join(BASE, "frozen", "GRID_DONE"), "w").write("done\n")
        print("GRID-COMPLETE", flush=True)


if __name__ == "__main__":
    main()
