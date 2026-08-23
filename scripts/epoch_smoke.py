"""Epoch smoke battery (EPOCH_POLICY.md). Runs against a COPY of a live
snapshot — never against data/alive itself. Usage:
    python scripts/epoch_smoke.py <snapshot_dir> [--days 3]
Checks: load + identity; save/reload bit-equality; timeline snapshot/
restore through the canonical serializer; same-host deterministic
replay; branch on a clone; H-CASCADE episode-state persistence; API
identity on every route; legacy-gate scan; state-corruption invariants.
"""
import copy, json, os, shutil, sys, tempfile, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SRC = Path(sys.argv[1]).resolve()
DAYS = int(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else 3
TMP = Path(tempfile.mkdtemp(prefix="earth1_epoch_smoke_"))
for f in ("world.pkl", "world.adj.npz", "world.pkl.sha256", "state.json", "EPOCH.json"):
    if (SRC / f).exists():
        shutil.copy2(SRC / f, TMP / f)
os.environ["EARTH1_ALIVE_HOME"] = str(TMP)
from earth1 import persistence
from earth1.alive import live_one_day, CANONICAL_DAY as STEP, PHYSICS_VERSION
from earth1.persistence import world_hash
R = {"snapshot": str(SRC), "physics_version": PHYSICS_VERSION, "checks": {}}
def check(name, ok, **info):
    R["checks"][name] = {"pass": bool(ok), **info}
    print(f"[{'ok' if ok else 'FAIL'}] {name} {json.dumps(info, default=str)[:300]}", flush=True)

st = json.loads((TMP / "state.json").read_text()); ep = json.loads((TMP / "EPOCH.json").read_text())
w, rs, info = persistence.load_world(TMP / "world.pkl")
h_loaded = world_hash(w)
check("load_identity", info.get("checksum") == "verified" and st["sha256"] and ep["world_uuid"] == st["world_uuid"],
      day=w.day, alive=int(w.health.alive.sum()), epoch=ep["epoch"], world_uuid=ep["world_uuid"], checksum=info.get("checksum"), rng=rs is not None)
ep_loaded = set(w.chronicle.cascade_episode_active or ()); lf_loaded = dict(w.chronicle.cascade_last_fired or {}); res_loaded = list(w.chronicle.cascade_residues or [])
check("episode_state_loaded", isinstance(w.chronicle.cascade_episode_active, set), episodes=len(ep_loaded), cooldown_entries=len(lf_loaded), residues=len(res_loaded))

# save/reload bit-equality
meta = persistence.save_world(w, TMP / "resave.pkl", rng=persistence.rng_from_state(rs))
w2, rs2, _ = persistence.load_world(TMP / "resave.pkl")
check("save_reload_bitwise", world_hash(w2) == h_loaded and set(w2.chronicle.cascade_episode_active) == ep_loaded
      and dict(w2.chronicle.cascade_last_fired) == lf_loaded and len(w2.chronicle.cascade_residues) == len(res_loaded) and rs2 == rs,
      hash=h_loaded[:16])
del w2

# deterministic replay, same host: two independent loads, DAYS days each
def replay():
    wa, ra, _ = persistence.load_world(TMP / "world.pkl"); rng = persistence.rng_from_state(ra)
    t = time.time()
    for _ in range(DAYS): live_one_day(wa, rng, **STEP)
    return wa, (time.time() - t) / DAYS
wa, spd = replay(); ha = world_hash(wa); epa = set(wa.chronicle.cascade_episode_active); fa = len(wa.chronicle.cascade_residues)
wb, _ = replay(); hb = world_hash(wb)
check("deterministic_replay", ha == hb and epa == set(wb.chronicle.cascade_episode_active), days=DAYS, sec_per_day=round(spd, 1), hash=ha[:16], episodes_after=len(epa), residues_after=fa)

# episode persistence across a save/restart boundary during evolution
persistence.save_world(wa, TMP / "mid.pkl", rng=None)
wm, _, _ = persistence.load_world(TMP / "mid.pkl")
check("episode_state_survives_restart", set(wm.chronicle.cascade_episode_active) == epa and world_hash(wm) == ha)
del wm, wb

# timeline snapshot/restore through the canonical serializer
from earth1 import timeline
timeline.HOME = TMP / "timeline"; timeline.HOME.mkdir()
timeline._save(wa, timeline.HOME / "smoke.pkl", rng=np.random.default_rng(1))
wt, rt = timeline.restore("smoke", with_rng=True)
check("timeline_snapshot_restore", world_hash(wt) == ha and rt is not None)
del wt

# branch on a clone; the source must be untouched
from earth1.branch import Scenario, run as branch_run
wc = copy.deepcopy(wa); hc0 = world_hash(wc)
out = branch_run(wc, [Scenario(id="s", label="s", forces={"fear": 0.1}, countries=None)], days=2, repeats=1)
check("branch_on_clone", hc0 == ha and world_hash(wa) == ha and out is not None)
del wc

# state-corruption invariants
F = np.asarray(wa.civ.forces)
check("state_invariants", bool(np.isfinite(F).all() and F.min() >= 0 and F.max() <= 1 and int(wa.health.alive.sum()) > 0
      and wa.civ.adj.shape[0] == wa.civ.n and all(k[0] in {"identity_collapse", "collective_surge"} for k in wa.chronicle.cascade_episode_active)),
      forces_min=float(F.min()), forces_max=float(F.max()), alive=int(wa.health.alive.sum()))

# API identity on every route (in-process, the copied home)
from fastapi.testclient import TestClient
from earth1.api.main import app
from earth1.api import deps
c = TestClient(app); ids = {}
r = c.get("/world"); ids["/world"] = r.json().get("identity", r.json())
ids["/observatory"] = c.get("/observatory/standing-readings").json()["identity"]
ids["/ask"] = c.get("/ask").json()["detail"]["identity"]
u = {k: (v.get("world_uuid"), v.get("snapshot_sha256"), v.get("physics_version"), v.get("epoch")) for k, v in ids.items()}
check("api_identity", len(set(u.values())) == 1 and list(u.values())[0] == (ep["world_uuid"], st["sha256"], PHYSICS_VERSION, ep["epoch"]), **{k: list(v) for k, v in u.items()})

from earth1.legacy_gate import scan, assert_one_production_earth
viol = scan(); assert_one_production_earth()
check("legacy_gate", not viol, violations=viol)

R["pass"] = all(v["pass"] for v in R["checks"].values())
out = ROOT / "data" / f"epoch{ep['epoch']}_smoke.json"; out.write_text(json.dumps(R, indent=1, default=str))
print("EPOCH SMOKE", "PASS" if R["pass"] else "FAIL", out)
shutil.rmtree(TMP, ignore_errors=True)
