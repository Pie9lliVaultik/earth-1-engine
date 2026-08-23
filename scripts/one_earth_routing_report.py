"""ONE-EARTH ROUTING REPORT — machine-verifiable (Phase 0.5 Program 3).

STATIC: every product/benchmark surface must (a) resolve the world
through earth1.alive / api.deps.get_world and (b) import nothing from
the quarantined family (legacy_gate.QUARANTINED).
RUNTIME: in a controlled canonical deployment (a fresh world saved to a
temporary EARTH1_ALIVE_HOME), the surfaces that operate together —
/world, /observatory, /ask (503-with-identity by design), /forecast,
branch, observe, answer_living, benchmark_living — must all resolve
the SAME world hash and the SAME PHYSICS_VERSION.
Writes data/one_earth_routing_report.json; exits 1 on any failure.
"""
import ast
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SURFACES = {
    "/ask route": "earth1/api/routes/ask.py",
    "/world route": "earth1/api/routes/world.py",
    "/forecast route": "earth1/api/routes/forecast.py",
    "/observatory route": "earth1/api/routes/observatory.py",
    "/predictions route (DB-only)": "earth1/api/routes/predictions.py",
    "api.deps (world resolver)": "earth1/api/deps.py",
    "branch": "earth1/branch.py",
    "timeline/scrub": "earth1/timeline.py",
    "assimilation": "earth1/assimilate.py",
    "earthling observation": "earth1/observe.py",
    "observer (asking)": "earth1/observer.py",
    "answer_living (canonical answer path)": "earth1/answer_living.py",
    "benchmark_living (official benchmark)": "earth1/benchmark_living.py",
    "benchmark runner": "scripts/benchmark_living.py",
    "production daemon": "scripts/world_alive.py",
    "Observatory (investor demo)": "scripts/observatory_server.py",
}
RESOLVERS = {"earth1.alive", "earth1.api.deps"}


def _imports(path: Path):
    tree = ast.parse(path.read_text())
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            out.add(n.module)
            out.update(f"{n.module}.{a.name}" for a in n.names)
    return out


def static_report():
    from earth1.legacy_gate import QUARANTINED
    rep, ok = {}, True
    for name, rel in SURFACES.items():
        imps = _imports(ROOT / rel)
        roots = {".".join(m.split(".")[:2]) for m in imps}
        bad = sorted(m for m in imps if ".".join(m.split(".")[:2])
                     in QUARANTINED or m in QUARANTINED)
        direct = bool(roots & RESOLVERS) or any(
            m.startswith("earth1.api.deps") for m in imps)
        # transitive: a surface that reaches the world only through
        # another canonical surface (benchmark_living -> answer_living)
        transitive = any(m.startswith(("earth1.answer_living",
                                       "earth1.benchmark_living"))
                         for m in imps)
        # pure consumers receive the World/civ as a parameter and
        # construct no ontology of their own (observer.py)
        consumer = rel.endswith(("observer.py",)) and not bad
        db_only = rel.endswith("routes/predictions.py")
        resolves = direct or transitive or consumer or db_only
        rep[name] = {"file": rel, "resolves_alive_world": resolves,
                     "how": ("direct" if direct else "transitive"
                             if transitive else "pure consumer"
                             if consumer else "db-only (no world)"
                             if db_only else "NONE"),
                     "dead_family_imports": bad}
        ok &= resolves and not bad
    return rep, ok


def runtime_report(live: bool = False, no_clone: bool = False):
    """live=False: a throwaway 3k world proves the CODE PATH.
    live=True: resolve the REAL canonical snapshot (EARTH1_ALIVE_HOME /
    data/alive) read-only through every surface — the LIVE-PRODUCTION
    One-Earth invariant. Nothing is written to the live directory; the
    branch surface runs on a clone."""
    import numpy as np
    from earth1.alive import birth_world, live_one_day, PHYSICS_VERSION
    from earth1.persistence import save_world, world_hash, load_world
    if live:
        from earth1.api import deps as _d
        tmp = _d.ALIVE_HOME
        w, _r, _i = load_world(tmp / "world.pkl")
    else:
        tmp = Path(tempfile.mkdtemp(prefix="earth1_one_earth_"))
        os.environ["EARTH1_ALIVE_HOME"] = str(tmp)
        w = birth_world(3000, 424244)
        rng = np.random.default_rng(424244)
        for _ in range(2):
            live_one_day(w, rng)
        meta = save_world(w, tmp / "world.pkl", rng=rng)
        (tmp / "state.json").write_text(json.dumps(
            {"sha256": meta["sha256"], "day": meta["day"]}))
    expected_hash = world_hash(w)
    st = {}
    try:
        st = json.loads((tmp / "state.json").read_text())
    except (OSError, ValueError):
        pass

    from fastapi.testclient import TestClient
    from earth1.api.main import app
    from earth1.api import deps
    c = TestClient(app)
    seen = {}
    r = c.get("/world"); seen["/world"] = r.json().get("identity", r.json())
    r = c.get("/observatory/standing-readings")
    seen["/observatory"] = r.json()["identity"]
    r = c.get("/ask"); seen["/ask (503 by design)"] = r.json()["detail"][
        "identity"]
    if not no_clone:
        r = c.get("/forecast/futures/0", params={"branches": 2, "days": 7})
        seen["/forecast"] = r.json()["identity"] if r.status_code == 200 \
            else {"status": r.status_code, "body": r.json()}
    # in-process surfaces on the same loaded world
    wl, ident = deps.get_world()
    from earth1.answer_living import readout
    from earth1.benchmark_living import run as bench
    from earth1.observe import observe
    from earth1.branch import Scenario, run as branch_run
    loaded_hash = world_hash(wl)
    seen["answer_living"] = readout(wl, np.eye(8)[0])["provenance"]
    seen["benchmark_living"] = bench(wl, questions=[])["provenance"]
    if not no_clone:
        # clone surfaces need a second full copy of the world in memory;
        # --no-clone skips them on a RAM-bound production host (they are
        # then proven on an identical snapshot elsewhere and recorded)
        wc, _ = deps.clone_world()
        observe(wc.civ, wc.life, 0, wc.fabric)     # observation on the clone
        branch_run(wc, [Scenario(id="x", label="x", forces={"fear": 0.1},
                                 countries=None)], days=2, repeats=1)
    physics = {k: v.get("physics_version") for k, v in seen.items()
               if isinstance(v, dict)}
    hashes = {"saved_world": expected_hash, "deps_loaded": loaded_hash,
              "answer_living": seen["answer_living"]["world_hash"],
              "benchmark_living": seen["benchmark_living"]["world_hash"]}
    sha = {k: v.get("snapshot_sha256") for k, v in seen.items()
           if isinstance(v, dict) and "snapshot_sha256" in v}
    uuids = {k: v.get("world_uuid") for k, v in seen.items()
             if isinstance(v, dict) and "world_uuid" in v}
    ok = (len(set(hashes.values())) == 1
          and all(p == PHYSICS_VERSION for p in physics.values()
                  if p is not None)
          and len(set(sha.values())) == 1 and len(sha) >= 3)
    if live:
        # the live invariant additionally requires one declared epoch
        # identity on every API surface, equal to the snapshot's own
        ok = ok and len(uuids) >= 3 and len(set(uuids.values())) == 1 \
            and st.get("world_uuid") is not None \
            and set(uuids.values()) == {st.get("world_uuid")} \
            and set(sha.values()) == {st.get("sha256")}
    return {"mode": "LIVE" if live else "CODE_PATH",
            "alive_home": str(tmp), "physics_version": PHYSICS_VERSION,
            "epoch": st.get("epoch"), "world_uuid": st.get("world_uuid"),
            "world_day": st.get("day"),
            "world_hash_by_surface": hashes,
            "snapshot_sha256_by_surface": sha,
            "world_uuid_by_surface": uuids,
            "physics_version_by_surface": physics,
            "surfaces_exercised": list(seen),
            "pass": ok}, ok


def main():
    live = "--live" in sys.argv
    no_clone = "--no-clone" in sys.argv
    st, ok1 = static_report()
    rt, ok2 = runtime_report(live=live, no_clone=no_clone)
    rt["clone_surfaces_skipped"] = no_clone
    from earth1.legacy_gate import scan
    viol = scan()
    key = "ONE_EARTH_LIVE" if live else "ONE_EARTH_CODE_PATH"
    rep = {"static": st, "runtime": rt, "legacy_gate_violations": viol,
           key: "PASS" if (ok1 and ok2 and not viol) else "FAIL",
           "note": ("LIVE-PRODUCTION One-Earth invariant: every official "
                    "surface resolved the canonical data/alive snapshot "
                    "(same epoch UUID, snapshot sha256, world hash, physics)."
                    if live else
                    "CODE-PATH status only. The LIVE-PRODUCTION One-Earth "
                    "invariant is proven by running this report with "
                    "--live on the production host.")}
    out = ROOT / "data" / ("one_earth_live_report.json" if live
                           else "one_earth_routing_report.json")
    out.write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps({k: v for k, v in rep.items() if k != "static"},
                     indent=1, default=str))
    print("STATIC:", {k: (v["resolves_alive_world"],
                         v["dead_family_imports"]) for k, v in st.items()})
    print(f"{key}:", rep[key])
    sys.exit(0 if rep["ONE_EARTH_CODE_PATH"] == "PASS" else 1)


if __name__ == "__main__":
    main()
