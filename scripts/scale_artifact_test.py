"""Is 100% reach a small-world artifact of 103 agents per country?

Pietro, 2026-08-18: "the 100% reach at 20,000 agents may partly be a
small-world artifact."

Same perturbation, same physics, four population sizes. If reach stays
pinned at 100% as agents-per-country grows, propagation is genuinely
global. If it falls, the earlier number was counting a village.
"""
from __future__ import annotations
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 0.2 MIGRATION NOTE: this instrument now steps THE canonical loop
# (chaos.world_step delegates to alive.live_one_day over a full World).
# Its numbers are NOT comparable with any measured before 0.2 - the
# instrument itself changed. 0.8 re-runs every measurement from scratch.
from earth1.chaos import world_step
from earth1.alive import birth_world
LIVING = dict(beta=2.0, residue=0.02, critical_fraction=0.12, relax=0.25)
DAYS = int(os.environ.get("SA_DAYS", "30"))

def one(pop):
    def fresh():
        return birth_world(pop, 42)
    wA = fresh(); wB = fresh()
    cA, lA, cB, lB = wA.civ, wA.life, wB.civ, wB.life
    rA = np.random.default_rng(1234); rB = np.random.default_rng(1234)
    cand = np.flatnonzero(lB.employed); who = int(cand[len(cand)//2])
    lB.employed[who] = False; lB.firm[who] = -1
    lB.tenure[who] = 0.0; lB.spells[who] += 1
    home = int(cA.country[who])
    curve = []
    for d in range(DAYS):
        world_step(wA, rA, **LIVING); world_step(wB, rB, **LIVING)
        diff = np.abs(cA.forces - cB.forces).max(axis=1) > 1e-12
        curve.append(float(diff.mean()))
    hm = cA.country == home
    return {"pop": pop, "agents_per_country": round(pop / 194, 1),
            "reach_day1": round(curve[0], 4), "reach_day5": round(curve[4], 4),
            "max_reach": round(max(curve), 4),
            "final_reach": round(curve[-1], 4),
            "reach_in_home_country": round(
                float((np.abs(cA.forces-cB.forces).max(axis=1) > 1e-12)[hm].mean()), 4),
            "curve": [round(c, 5) for c in curve]}

def main():
    print(f"  {'pop':>9s} {'per country':>12s} {'day1':>8s} {'day5':>8s} "
          f"{'max':>8s} {'final':>8s} {'home ctry':>10s}")
    rows = []
    for pop in (20_000, 60_000, 200_000, 600_000):
        r = one(pop); rows.append(r)
        print(f"  {r['pop']:9,d} {r['agents_per_country']:12.1f} "
              f"{r['reach_day1']:7.1%} {r['reach_day5']:7.1%} "
              f"{r['max_reach']:7.1%} {r['final_reach']:7.1%} "
              f"{r['reach_in_home_country']:9.1%}", flush=True)
    json.dump({"days": DAYS, "rows": rows},
              open("data/scale_artifact_test.json", "w"), indent=1)
    a, b = rows[0]["max_reach"], rows[-1]["max_reach"]
    print(f"\nSCALE VERDICT: max reach {a:.1%} at 20K -> {b:.1%} at 600K")
    print("  " + ("reach is scale-dependent: the 20K number was a village"
                  if b < a * 0.75 else
                  "reach holds as the world grows: propagation is genuinely global"))

if __name__ == "__main__":
    main()
