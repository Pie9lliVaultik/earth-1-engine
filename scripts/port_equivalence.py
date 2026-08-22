"""PROGRAM 2 — port-equivalence harness (frozen battery:
ops/alive/CANONICALIZATION_PROGRAM.md). Self-contained: runs in the
PINNED pre-port checkout (--mode lab, assembling lab candidate
76a574c exactly as the it6 "ALL" arm did) or in the ported checkout
(--mode canon, flagless live_one_day). Both modes write identical
fingerprint files; --compare checks them bitwise (tolerance 0).

  python scripts/port_equivalence.py --mode lab   --n 20000 --seed 8890 --days 10 --every 1 --out D
  python scripts/port_equivalence.py --mode canon --n 20000 --seed 8890 --days 10 --every 1 --out D
  python scripts/port_equivalence.py --compare D_lab D_canon
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _h(a) -> str:
    a = np.ascontiguousarray(np.asarray(a))
    return hashlib.sha256(a.tobytes()).hexdigest()[:24] + f":{a.dtype}:{a.shape}"


def fingerprint(w, effective_fn):
    civ, life, fl = w.civ, w.life, w.flourishing
    from earth1.persistence import world_hash
    arrays = {
        "forces": civ.forces, "alpha": civ.alpha, "openness": civ.openness,
        "effective": np.asarray(effective_fn(w)),
        "alive": w.health.alive,
        "life.deprivation": life.deprivation, "life.wealth": life.wealth,
        "life.employed": life.employed, "life.firm": life.firm,
        "life.wage": life.wage, "life.firm_health": life.firm_health,
        "life.political": life.political, "life.social_need": life.social_need,
        "life.addiction": life.addiction, "life.mental": life.mental,
        "life.relationship": life.relationship, "life.spells": life.spells,
        "fl.hope": fl.hope, "fl.hunger": fl.hunger, "fl.thirst": fl.thirst,
        "fl.curiosity": fl.curiosity, "fl.belonging": fl.belonging,
        "fl.meaning": fl.meaning, "fl.satisfaction": fl.satisfaction,
        "adj.indptr": civ.adj.indptr, "adj.indices": civ.adj.indices,
        "adj.data": civ.adj.data,
    }
    res = getattr(w.chronicle, "cascade_residues", None) or []
    lf = getattr(w.chronicle, "cascade_last_fired", None) or {}
    return {
        "day": int(w.day),
        "hashes": {k: _h(v) for k, v in arrays.items()},
        "world_hash": world_hash(w),
        "chronicle_events": [(m.id, round(float(m.salience), 12),
                              int(m.scope.sum()) if m.scope is not None
                              else -1) for m in w.chronicle.events],
        "cascade_last_fired": sorted([[k[0], int(k[1]), int(v)]
                                      for k, v in lf.items()]),
        "cascade_residues": sorted([[r["rule"], int(r["loc"]),
                                     int(r["day"]), float(r["h"]),
                                     _h(r["effects"])] for r in res]),
        "n_alive": int(w.health.alive.sum()),
    }, arrays


def run(mode, n, seed, days, every, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    import earth1.alive as am
    if mode == "lab":
        # ===== lab candidate 76a574c, assembled exactly as it6 "ALL" =====
        os.environ["EARTH1_CASCADE_COOLDOWN"] = "1"
        os.environ["EARTH1_DECAY_RESIDUE"] = "1"
        os.environ["EARTH1_COLLECTIVE_CENTERED"] = "1"
        import earth1.contagion as cont
        import earth1.feed as feedmod
        import earth1.flourishing as flmod
        import earth1.life as lifemod
        import earth1.conviction_lab as clab
        import earth1.field_lab as flab
        from earth1.types import Force
        w = am.birth_world(n, seed)
        clab.ALPHA0 = w.civ.alpha.copy()
        flab.FLOUR_REF[0] = w.flourishing
        flab.AROUSAL = np.array(
            [feedmod.AROUSAL_WEIGHT[Force(k)] for k in range(8)])
        flab.DRIVE_ACC[0] = np.zeros(n)
        flab.ENC_COUNT[0] = np.zeros(n, dtype=np.int64)
        am.propagate = flab.make_dyadic_propagate_v6(3, 0.05)
        feedmod.feed_tick = flab.make_dyadic_feed_v6(0.05)
        cont.CONTAGION_GAIN = 0.0
        lifemod.life_force_target = flab.flourishing_level_map(
            lifemod.life_force_target)
        flmod.flourishing_tick = flab.flourishing_writes_disabled(
            flmod.flourishing_tick)

        def conv(forces, alpha, adj):
            n_enc = np.maximum(flab.ENC_COUNT[0], 1)
            drive = flab.DRIVE_ACC[0] / n_enc
            drive[flab.ENC_COUNT[0] == 0] = 0.0
            a = np.clip(alpha, 0.02, 0.98)
            o = np.clip(1 / (1 + np.exp(-(np.log(a / (1 - a))
                                          + 0.003 * drive))), 0.02, 1.0)
            flab.DRIVE_ACC[0][:] = 0.0
            flab.ENC_COUNT[0][:] = 0
            return o
        am.update_conviction = conv

        def tick(w, rng, d):
            flab._DAY[0] = d
            return am.live_one_day(w, rng, relax=0.045)
    else:
        # ===== canonical port: flagless =====
        for k in list(os.environ):
            if k.startswith("EARTH1_"):
                del os.environ[k]
        w = am.birth_world(n, seed)

        def tick(w, rng, d):
            return am.live_one_day(w, rng)
    eff = am.effective_forces
    rng = np.random.default_rng(seed)
    fp0, _ = fingerprint(w, eff)
    (out / "day0000.json").write_text(json.dumps(fp0))
    for d in range(1, days + 1):
        tick(w, rng, d)
        if d % every == 0 or d == days:
            fp, arrays = fingerprint(w, eff)
            (out / f"day{d:04d}.json").write_text(json.dumps(fp))
            if d == days:
                np.savez_compressed(out / "final_arrays.npz",
                                    forces=arrays["forces"],
                                    alpha=arrays["alpha"],
                                    effective=arrays["effective"])
    (out / "meta.json").write_text(json.dumps(
        {"mode": mode, "n": n, "seed": seed, "days": days,
         "physics_version": getattr(am, "PHYSICS_VERSION", "lab-76a574c"),
         "commit": os.popen("git rev-parse --short HEAD").read().strip()}))
    print(f"{mode}: {days} days dumped to {out}")


def compare(a, b):
    a, b = Path(a), Path(b)
    files = sorted(p.name for p in a.glob("day*.json"))
    bad = 0
    for fn in files:
        fa = json.loads((a / fn).read_text())
        fb = json.loads((b / fn).read_text())
        diffs = [k for k in fa["hashes"] if fa["hashes"][k]
                 != fb["hashes"].get(k)]
        for key in ("world_hash", "chronicle_events",
                    "cascade_last_fired", "cascade_residues", "n_alive"):
            if fa[key] != fb[key]:
                diffs.append(key)
        if diffs:
            bad += 1
            print(f"  {fn}: DIFF {diffs}")
            if "forces" in diffs and (a / "final_arrays.npz").exists() \
                    and fn == files[-1]:
                A = np.load(a / "final_arrays.npz")
                B = np.load(b / "final_arrays.npz")
                print("   max|Δforces| =", float(np.abs(
                    A["forces"] - B["forces"]).max()))
    print(f"COMPARED {len(files)} checkpoints: "
          f"{'BITWISE IDENTICAL' if bad == 0 else f'{bad} DIFFER'}")
    return bad == 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["lab", "canon"])
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=8890)
    ap.add_argument("--days", type=int, default=10)
    ap.add_argument("--every", type=int, default=1)
    ap.add_argument("--out")
    ap.add_argument("--compare", nargs=2)
    a = ap.parse_args()
    if a.compare:
        sys.exit(0 if compare(*a.compare) else 1)
    run(a.mode, a.n, a.seed, a.days, a.every, a.out)
