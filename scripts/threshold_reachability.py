"""Threshold reachability check (eleventh review, verification #1).

Are the phase-transition trigger levels (fear > 0.7, economics < 0.3,
etc.) reachable by ANY national force mean at genesis? Measures the
per-country force-mean envelope at 200K and compares against every
registered threshold rule. Measurement only — no physics change.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.genesis import genesis, GENESIS_COUNTRIES
from earth1.types import Force

POP = int(os.environ.get("REACH_POP", "200000"))
SEED = 42


def main() -> None:
    civ = genesis(POP, SEED)
    means = []
    for c in range(len(GENESIS_COUNTRIES)):
        mask = civ.country == c
        if mask.sum() >= 50:
            means.append(civ.forces[mask].mean(axis=0))
    m = np.array(means)
    mx, mn = m.max(axis=0), m.min(axis=0)

    print(f"national force-mean envelope over {len(means)} countries "
          f"(pop {POP}):")
    for f in Force:
        print(f"  {f.name:12s} min {mn[int(f)]:.3f}  max {mx[int(f)]:.3f}")

    # registered trigger conditions (thresholds.py)
    checks = {
        "identity_collapse (fear>0.7 & collective>0.6)":
            mx[int(Force.FEAR)] > 0.7 and mx[int(Force.COLLECTIVE)] > 0.6,
        "panic_cascade (economics<0.3 & fear>0.5)":
            mn[int(Force.ECONOMICS)] < 0.3 and mx[int(Force.FEAR)] > 0.5,
        "fear>0.7 alone": mx[int(Force.FEAR)] > 0.7,
        "economics<0.3 alone": mn[int(Force.ECONOMICS)] < 0.3,
    }
    reachable = {k: bool(v) for k, v in checks.items()}
    for k, v in reachable.items():
        print(f"  {'REACHABLE  ' if v else 'UNREACHABLE'} {k}")

    out = {"pop": POP, "seed": SEED, "n_countries": len(means),
           "force_mean_max": {f.name: float(mx[int(f)]) for f in Force},
           "force_mean_min": {f.name: float(mn[int(f)]) for f in Force},
           "reachable_at_genesis": reachable}
    with open("data/threshold_reachability.json", "w") as f:
        json.dump(out, f, indent=1)
    print("REACHABILITY-DONE", flush=True)


if __name__ == "__main__":
    main()
