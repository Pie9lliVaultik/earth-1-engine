"""IS THE COUNTRY MAP NOISE-LIMITED OR GENUINELY CHAOTIC?

The registered threshold said a noise floor below 0.0 means country
consequences are genuinely chaotic and no quantity of agents will
stabilise them. But that reading assumed the weighting was already
correct, and it was not — census weights were never applied, and fixing
them moved the floor from -0.433 to -0.721. So two explanations survive
and they demand opposite responses:

  SAMPLE-LIMITED     per-country estimates are too noisy at this size.
                     The floor should RISE as agents per country rise,
                     and the country map is reachable with more compute.
  GENUINELY CHAOTIC  country-level trajectories diverge no matter how
                     many agents carry them. The floor stays FLAT, and
                     the honest product refuses the map entirely.

One measurement separates them: run the identical noise-floor
diagnostic at several population sizes and look at the SLOPE. Nothing
else changes — same scenario, same days, same seeds, same diagnostic.

This is the test that decides whether the country map is worth any
further engineering, and it can return either answer.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from earth1.alive import birth_world, live_one_day
from earth1.branch import run
from hormuz import SCENARIOS, geography_divergence

DAYS = int(os.environ.get("NS_DAYS", "45"))
WARM = int(os.environ.get("NS_WARM", "45"))
SIZES = [int(x) for x in
         os.environ.get("NS_SIZES", "50000,200000,600000").split(",")]
SC = SCENARIOS[1]          # the escalation branch, the strongest signal


def floor_at(pop: int):
    """The noise floor at this population: same scenario, different dice."""
    w = birth_world(pop, 42)
    rng = np.random.default_rng(11)
    for _ in range(WARM):
        live_one_day(w, rng)
    a = run(w, [SC], days=DAYS, repeats=2, seed=101)
    b = run(w, [SC], days=DAYS, repeats=2, seed=907)
    merged = {"branches": {"a": a["branches"][SC.id],
                           "b": b["branches"][SC.id]}}
    g = geography_divergence(merged)
    return (g.get("mean_rank_correlation", 0.0),
            g.get("mean_set_overlap", 0.0))


def main() -> None:
    print("\n  Same scenario, different dice, at increasing size.")
    print("  If the floor RISES with agents it is sample-limited and the")
    print("  country map is reachable. If it stays FLAT, country")
    print("  consequences are genuinely chaotic and the map is refused.\n")
    print(f"  {'agents':>9s} {'per country':>12s} {'rank corr':>10s} "
          f"{'overlap':>8s}")
    rows = []
    for pop in SIZES:
        rc, so = floor_at(pop)
        rows.append({"pop": pop, "per_country": round(pop / 194, 1),
                     "rank_correlation": rc, "set_overlap": so})
        print(f"  {pop:9,d} {pop / 194:12.0f} {rc:+10.3f} {so:8.2f}",
              flush=True)

    slope = rows[-1]["rank_correlation"] - rows[0]["rank_correlation"]
    verdict = ("SAMPLE-LIMITED — the floor rises with agents, so the "
               "country map is reachable with more compute"
               if slope > 0.25 else
               "GENUINELY CHAOTIC — more agents do not stabilise country "
               "consequences. Refuse the map, ship global aggregates.")
    json.dump({"rows": rows, "slope": slope, "verdict": verdict,
               "days": DAYS, "scenario": SC.id},
              open("data/noise_vs_scale.json", "w"), indent=1)
    print(f"\n  floor moved {slope:+.3f} from smallest to largest")
    print(f"\n  VERDICT: {verdict}\n")


if __name__ == "__main__":
    main()
