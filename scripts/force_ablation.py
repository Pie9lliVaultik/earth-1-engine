"""0.8-A3/A4 — endogeny + mechanism ablation for the pinned force
field. Fresh 200k worlds, NO news, common seed across arms, 365 days.

Arms (clone-only diagnosis; production code untouched):
  baseline   CANONICAL_DAY as-is
  decay_on   the PRE-REGISTERED 0.8 A/B arm B: conviction decay 0.02
             (patched at the alive.py binding for this process only)
  beta1      propagation alignment weight beta=1.0 (the old reduced
             system's value) instead of canonical 2.0

Daily readout: per-channel mean/sd/saturation shares + alpha
mean/frac>0.9. One process per arm.
"""
import json
import os
import sys
import time
from functools import partial
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import multiprocessing as mp

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

N_AGENTS = 200_000
DAYS = int(os.environ.get("EARTH1_ABL_DAYS", "365"))
SEED = 8802
OUT = Path(os.environ.get("EARTH1_ABL_OUT",
                          str(ROOT / "data" / "force_ablation_0_8")))


def run_arm(arm):
    import earth1.alive as alive_mod
    from earth1.alive import birth_world, live_one_day
    from earth1.types import Force
    import earth1.influence as infl

    if arm == "decay_on":
        alive_mod.update_conviction = partial(
            infl.update_conviction, _experimental_decay_0_8_ab=0.02)
    step_kw = {"beta": 1.0} if arm == "beta1" else {}

    w = birth_world(N_AGENTS, SEED)
    rng = np.random.default_rng(SEED)
    days = []
    t0 = time.monotonic()
    for d in range(1, DAYS + 1):
        live_one_day(w, rng, **step_kw)
        alive = w.health.alive
        f = w.civ.forces[alive]
        a = w.civ.alpha[alive]
        days.append({
            "day": d,
            "mean": [round(float(v), 5) for v in f.mean(axis=0)],
            "sd": [round(float(v), 5) for v in f.std(axis=0)],
            "sat_hi": [round(float((f[:, c] > 0.95).mean()), 5)
                       for c in range(f.shape[1])],
            "sat_lo": [round(float((f[:, c] < 0.05).mean()), 5)
                       for c in range(f.shape[1])],
            "alpha_mean": round(float(a.mean()), 5),
            "alpha_gt09": round(float((a > 0.9).mean()), 5),
        })
    return {"arm": arm, "days": days, "n": N_AGENTS, "seed": SEED,
            "wall_s": round(time.monotonic() - t0, 1),
            "channels": [c.name for c in
                         __import__("earth1.types",
                                    fromlist=["Force"]).Force]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ctx = mp.get_context("spawn")      # separate interpreters: patches
    with ctx.Pool(processes=3) as pool:  # never cross-contaminate arms
        for r in pool.imap_unordered(run_arm,
                                     ["baseline", "decay_on", "beta1"]):
            (OUT / f"{r['arm']}.json").write_text(json.dumps(r))
            last = r["days"][-1]
            print(f"{r['arm']:9s} done {r['wall_s']:7.1f}s | day-{DAYS} "
                  f"alpha={last['alpha_mean']:.4f} "
                  f"fear={last['mean'][0]:.4f} "
                  f"sat_hi(FEAR)={last['sat_hi'][0]:.3f}", flush=True)
    print("ABLATION COMPLETE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
