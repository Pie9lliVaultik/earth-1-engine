"""LYAPUNOV — the largest exponent, by Benettin, on the living world."""
from __future__ import annotations
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 0.2 MIGRATION NOTE: this instrument now steps THE canonical loop
# (chaos.world_step delegates to alive.live_one_day over a full World).
# Its numbers are NOT comparable with any measured before 0.2 - the
# instrument itself changed. 0.8 re-runs every measurement from scratch.
from earth1.chaos import lyapunov_benettin
from earth1.alive import birth_world

POP = int(os.environ.get("LY_POP", "20000"))
STEPS = int(os.environ.get("LY_STEPS", "240"))

def fresh():
    return birth_world(POP, 42)

def main():
    rows = []
    settings = [("legacy (averaging kernel, dead feedback)",
                 dict(beta=0.0, residue=0.0005, critical_fraction=0.25, relax=0.0)),
                ("living world", dict(beta=2.0, residue=0.02,
                                      critical_fraction=0.12, relax=0.25))]
    print(f"  {POP:,} agents, {STEPS} steps, Benettin renormalisation\n")
    print(f"  {'configuration':46s} {'lambda/day':>11s} {'doubling':>10s}")
    for label, kw in settings:
        wA = fresh(); wB = fresh()
        r = lyapunov_benettin(wA, wB,
                              np.random.default_rng(1234),
                              np.random.default_rng(1234),
                              steps=STEPS, **kw)
        lam = r["lyapunov"]
        dbl = (np.log(2) / lam) if lam > 1e-9 else float("inf")
        rows.append({"config": label, **r, "doubling_days": dbl, **kw})
        print(f"  {label:46s} {lam:+11.4f} "
              + (f"{dbl:9.1f}d" if np.isfinite(dbl) else "        --"))
    json.dump({"pop": POP, "steps": STEPS, "rows": rows},
              open("data/lyapunov_test.json", "w"), indent=1)
    live = rows[-1]["lyapunov"]
    print(f"\nLYAPUNOV VERDICT: {'CHAOTIC' if live > 0 else 'not chaotic'} "
          f"— lambda = {live:+.4f} per day")
    if live > 0:
        print(f"  A difference of one part in a million between two "
              f"Earth-1s doubles every {np.log(2)/live:.1f} days.")

if __name__ == "__main__":
    main()
