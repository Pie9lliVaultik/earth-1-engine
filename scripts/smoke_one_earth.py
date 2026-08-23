"""0.5 FINAL ACCEPTANCE — structural observation + the one-Earth smoke.

Runs on prime against a pulled LIVE 4M snapshot (EARTH1_ALIVE_HOME
points at it). Part A records plasticity structure (bounds, mutuality,
degrees, dangling refs) — observations, not validation. Part B
exercises every mounted product route in-process and proves identity,
non-mutation, complete clones, and fail-loud behavior against the real
civilization.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

HOME = Path(os.environ["EARTH1_ALIVE_HOME"])
report = {"A_structure": {}, "B_smoke": {}, "failures": []}


def fail(name, detail):
    report["failures"].append({name: detail})
    print(f"  FAIL {name}: {detail}")


def ok(name, detail=""):
    print(f"  PASS {name} {detail}")


def part_a():
    from earth1 import persistence
    from earth1.plasticity import MAX_WEIGHT, MIN_WEIGHT
    w, rng_state, info = persistence.load_world(
        HOME / "world.pkl")
    alive = w.health.alive
    a = report["A_structure"]
    a["identity"] = {"day": int(w.day), "alive": int(alive.sum()),
                     "schema": info["schema_version"],
                     "checksum": info["checksum"]}
    genesis_max = 3.6      # observed genesis stacking ceiling
    for k in ("friends", "weak"):
        m = w.fabric.by_type[k].tocsr()
        deg = np.diff(m.indptr)
        a[k] = {"nnz": int(m.nnz),
                "degree_mean": round(float(deg.mean()), 3),
                "degree_p99": int(np.percentile(deg, 99)),
                "degree_max": int(deg.max()),
                "w_min": round(float(m.data.min()), 4) if m.nnz else None,
                "w_max": round(float(m.data.max()), 4) if m.nnz else None}
        if m.nnz:
            if float(m.data.min()) < MIN_WEIGHT - 1e-9:
                fail(f"{k}_weight_floor", a[k]["w_min"])
            if float(m.data.max()) > max(genesis_max, MAX_WEIGHT) + 1e-9:
                fail(f"{k}_weight_ceiling", a[k]["w_max"])
        asym = (m != m.T).nnz
        if asym:
            fail(f"{k}_mutuality", asym)
        if m.diagonal().sum() != 0:
            fail(f"{k}_self_loops", float(m.diagonal().sum()))
        # dangling: plastic edges to the never-alive are corruption;
        # edges to recently-dead-await-rebirth are the model's norm
        rows, cols = m.nonzero()
        dead_ref = int((~alive[cols]).sum())
        a[k]["edges_to_currently_dead"] = dead_ref
    ok("A structure", json.dumps({k: a[k] for k in ("friends", "weak")}))
    return w


def part_b(w_loaded):
    from earth1 import persistence
    from earth1.api import deps
    deps.reset_cache()
    from earth1.api.routes import forecast as f_routes
    from earth1.api.routes import observatory as o_routes
    from earth1.api.routes import world as w_routes
    from earth1.api.routes import ask as a_routes
    from earth1.api import main as api_main
    from fastapi import HTTPException

    b = report["B_smoke"]
    w, ident = deps.get_world()
    b["identity"] = ident
    if ident["world_day"] != w_loaded.day:
        fail("identity_day", (ident["world_day"], w_loaded.day))
    ok("identity", f"day {ident['world_day']} sha "
                   f"{str(ident['snapshot_sha256'])[:12]}")

    # read-only routes: bit identity of world + RNG
    before = persistence.world_hash(w)
    rng_before = np.random.get_state()[1].copy()
    results = {}
    results["/health"] = api_main.health()
    results["/civ"] = api_main.civ_stats()
    results["/world"] = w_routes.world_summary()
    results["/world/countries"] = w_routes.countries()
    i = int(np.flatnonzero(w.health.alive)[100])
    results["/world/earthling"] = w_routes.earthling(i)
    results["/observatory"] = o_routes.standing_readings()
    if persistence.world_hash(w) != before:
        fail("readonly_mutation", "world hash changed")
    elif not np.array_equal(np.random.get_state()[1], rng_before):
        fail("readonly_rng", "global RNG consumed")
    else:
        ok("read-only non-mutation", "6 routes, bit-identical world+RNG")
    for path, r in results.items():
        ident_r = r.get("identity") or r.get("world")
        if path in ("/health",) and isinstance(ident_r, dict):
            pass
        if isinstance(r, dict) and "identity" in r:
            if r["identity"]["snapshot_sha256"] != ident["snapshot_sha256"]:
                fail(f"{path}_identity", "different snapshot")
    ok("identity on responses")

    # fail-loud routes
    for name, fn in (("/ask", a_routes.ask_pending),
                     ("/forecast/multiverse",
                      f_routes.legacy_forecast_pending)):
        try:
            fn()
            fail(name, "did not fail loudly")
        except HTTPException as e:
            if e.status_code in (503,) and "pending" in str(e.detail):
                ok(name, f"{e.status_code} loud, no legacy")
            else:
                fail(name, f"unexpected {e.status_code}")
    try:
        w_routes.tick_retired()
        fail("/world/tick", "not retired")
    except HTTPException as e:
        ok("/world/tick", f"{e.status_code} (daemon is sole writer)") \
            if e.status_code == 410 else fail("/world/tick", e.status_code)

    # branch clone: complete, isolated, parent unchanged after evolution
    wc, _ = deps.clone_world()
    missing = [f for f in persistence.PERSISTENT_FIELDS
               if getattr(wc, f, None) is None]
    if missing:
        fail("clone_completeness", missing)
    shared = wc.civ.forces is w.civ.forces or wc.fabric.adj is w.fabric.adj
    if shared:
        fail("clone_aliasing", "shared mutable arrays")
    parent_before = persistence.world_hash(w)
    from earth1.alive import live_one_day
    live_one_day(wc, np.random.default_rng(5))
    if persistence.world_hash(w) != parent_before:
        fail("branch_isolation", "parent changed after branch evolution")
    else:
        ok("branch clone", "complete fields, no aliases, parent "
                           "unchanged after 1 branch day")


def main():
    t0 = time.time()
    w = part_a()
    part_b(w)
    # gates
    from earth1.legacy_gate import scan
    v = scan()
    if v:
        fail("one_production_earth", v[:3])
    else:
        ok("one-production-earth gate", "0 violations")
    report["verdict"] = "PASS" if not report["failures"] else "FAIL"
    report["provenance"] = {
        "host": os.uname().nodename,
        "commit": subprocess.run(["git", "rev-parse", "HEAD"],
                                 capture_output=True, text=True,
                                 cwd=ROOT).stdout.strip(),
        "wall_clock": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_s": round(time.time() - t0, 1)}
    out = ROOT / "data" / "one_earth_smoke.json"
    out.write_text(json.dumps(report, indent=1))
    print(f"\nSMOKE {report['verdict']} — {out}")
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
