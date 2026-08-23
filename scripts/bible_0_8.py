"""Bible 0.8 — butterfly + FSLE on the registered Epoch-2 snapshot,
canonical configuration only (ops/alive/BIBLE_0_8_REMEASUREMENT.md).
    python scripts/bible_0_8.py butterfly <snapshot_dir> [days]
    python scripts/bible_0_8.py placebo   <snapshot_dir> [days]
    python scripts/bible_0_8.py fsle      <snapshot_dir> <trial_index> [days]
"""
import json, os, sys, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from earth1 import persistence
from earth1.alive import live_one_day, CANONICAL_DAY as STEP, PHYSICS_VERSION
from earth1.chaos import entropy, lyapunov_from
OUT = Path(os.environ.get("EARTH1_B08_OUT", str(ROOT / "data" / "bible_0_8"))); OUT.mkdir(parents=True, exist_ok=True)
R = 2.0


def pair(snap):
    wA, rsA, _ = persistence.load_world(Path(snap) / "world.pkl")
    wB, rsB, _ = persistence.load_world(Path(snap) / "world.pkl")
    return wA, persistence.rng_from_state(rsA), wB, persistence.rng_from_state(rsB)


def perturb(w, pick=None):
    cand = np.flatnonzero(w.life.employed)
    who = int(cand[len(cand) // 2]) if pick is None else int(cand[pick % len(cand)])
    w.life.employed[who] = False; w.life.firm[who] = -1
    w.life.tenure[who] = 0.0; w.life.spells[who] += 1
    return who


def evolve(wA, rA, wB, rB, days, tag):
    div, frac, ent = [], [], []
    t0 = time.time()
    for d in range(days):
        live_one_day(wA, rA, **STEP); live_one_day(wB, rB, **STEP)
        df = np.abs(wA.civ.forces - wB.civ.forces)
        div.append(float(np.linalg.norm(df))); frac.append(float((df.max(axis=1) > 1e-12).mean())); ent.append(entropy(wA.civ.forces))
        if d % 5 == 0:
            print(f"  {tag} day {d+1:4d} div {div[-1]:.4e} reach {frac[-1]:.4%} ent {ent[-1]:.4f} ({(time.time()-t0)/(d+1):.0f}s/d)", flush=True)
    return div, frac, ent


mode, snap = sys.argv[1], sys.argv[2]
meta = {"physics_version": PHYSICS_VERSION, "config": dict(STEP), "snapshot": snap,
        "snapshot_sha256": json.loads((Path(snap) / "state.json").read_text()).get("sha256")}
if mode in ("butterfly", "placebo"):
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    wA, rA, wB, rB = pair(snap)
    who = perturb(wB) if mode == "butterfly" else None
    div, frac, ent = evolve(wA, rA, wB, rB, days, mode)
    L = lyapunov_from(div) if mode == "butterfly" else None
    res = {**meta, "mode": mode, "days": days, "touched": who, "div": div, "reach": frac, "entropy": ent,
           "max_div": max(div), "lyapunov": (round(L, 5) if L is not None else None),
           "final_frac_world": frac[-1], "max_frac_world": max(frac), "entropy_start": ent[0], "entropy_end": ent[-1],
           "chaotic": (bool(L > 0.01 and max(frac) > 0.01) if L is not None else None),
           "placebo_exactly_zero": (max(div) == 0.0) if mode == "placebo" else None}
    (OUT / f"{mode}.json").write_text(json.dumps(res, indent=1))
    print(f"{mode.upper()} DONE", {k: res[k] for k in ("lyapunov", "max_frac_world", "final_frac_world", "entropy_start", "entropy_end", "chaotic", "placebo_exactly_zero", "max_div")})
elif mode == "fsle":
    i = int(sys.argv[3]); days = int(sys.argv[4]) if len(sys.argv) > 4 else 40
    wA, rA, wB, rB = pair(snap)
    who = perturb(wB, pick=i * 7919)
    div, frac, ent = evolve(wA, rA, wB, rB, days, f"fsle{i}")
    d = np.array(div); d0 = d[0]; hit = np.flatnonzero(d >= R * d0)
    t_double = int(hit[0]) + 1 if hit.size else None
    res = {**meta, "mode": "fsle", "trial": i, "touched": who, "days": days, "d0": float(d0), "dmax": float(d.max()),
           "t_double": t_double, "fsle_per_day": (float(np.log(R) / t_double) if t_double else 0.0), "max_reach": float(max(frac)), "div": div, "reach": frac}
    (OUT / f"fsle_{i}.json").write_text(json.dumps(res, indent=1))
    print("FSLE TRIAL DONE", {k: res[k] for k in ("trial", "touched", "d0", "dmax", "t_double", "fsle_per_day", "max_reach")})
