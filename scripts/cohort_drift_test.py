"""Cohort inheritance bias test (eleventh review corollary).

Claim under test: parents contribute 40% of newborn traits AFTER having
slid along the age gradients, so every replacement cycle injects a
conservative bias (~ -0.0013/yr on openness) that the 3-year stationarity
tolerance (|delta| < 0.02) is too coarse to see.

Protocol: 200 simulated years of NOTHING but the generational machinery
(no world_tick, no events, no feedback) at cohort_drift=0. If the traits
are stationary under a stationary pyramid, means stay flat; a monotone
drift confirms the bias and its rate.

Measurement only — no physics change. Freeze-compliant.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.genesis import genesis
from earth1.generational import generational_tick, _INHERITED_TRAITS

POP = int(os.environ.get("DRIFT_POP", "50000"))
YEARS = int(os.environ.get("DRIFT_YEARS", "200"))
BASIS = os.environ.get("DRIFT_BASIS", "current")  # "current" (A) | "entry" (B)
SEED = 42
DT_DAYS = 30.4375  # 12 ticks per year


def _mutable(civ):
    for name in list(vars(civ)):
        v = getattr(civ, name)
        if isinstance(v, np.ndarray) and not v.flags.writeable:
            setattr(civ, name, v.copy())
    return civ


def main() -> None:
    civ = _mutable(genesis(POP, SEED))
    rng = np.random.default_rng(SEED)
    series = {t: [] for t in _INHERITED_TRAITS}
    years_axis = []
    total_deaths = 0

    for year in range(YEARS + 1):
        if year % 5 == 0:
            years_axis.append(year)
            for t in _INHERITED_TRAITS:
                series[t].append(float(getattr(civ, t).mean()))
            print(f"y{year:3d} " + " ".join(
                f"{t[:4]}={series[t][-1]:.4f}" for t in _INHERITED_TRAITS),
                flush=True)
        if year == YEARS:
            break
        for _ in range(12):
            r = generational_tick(civ, rng, dt_days=DT_DAYS,
                                  inheritance_basis=BASIS)
            total_deaths += r["deaths"]

    # per-trait linear rates (units/year): full window AND late window.
    # The late window (second half of the run) excludes the pyramid
    # equilibration transient — genesis starts from the census age
    # distribution, not the machinery's own stationary pyramid, so the
    # first decades drift for a benign, self-limiting reason. The
    # STRUCTURAL verdict is the late-window slope.
    x = np.array(years_axis, dtype=float)
    late = x >= (YEARS / 2.0)
    rates, rates_late = {}, {}
    for t in _INHERITED_TRAITS:
        y = np.array(series[t])
        rates[t] = float(np.polyfit(x, y, 1)[0])
        rates_late[t] = float(np.polyfit(x[late], y[late], 1)[0])
    # bias confirmed if |extrapolated 50y move| > 0.02 on the LATE slope
    worst = max(rates_late, key=lambda t: abs(rates_late[t]))
    worst_50y = rates_late[worst] * 50.0
    confirmed = abs(worst_50y) > 0.02

    out = {
        "pop": POP, "years": YEARS, "seed": SEED,
        "inheritance_basis": BASIS,
        "turnover_deaths": total_deaths,
        "series_years": years_axis,
        "series": series,
        "rates_per_year": rates,
        "rates_per_year_late_window": rates_late,
        "worst_trait": worst,
        "worst_50y_extrapolation_late": worst_50y,
        "bias_confirmed": confirmed,
    }
    with open(f"data/cohort_drift_{BASIS}.json", "w") as f:
        json.dump(out, f, indent=1)
    print("full-window worst: "
          + max(rates, key=lambda t: abs(rates[t]))
          + f" {rates[max(rates, key=lambda t: abs(rates[t]))]:+.5f}/yr",
          flush=True)
    print(f"COHORT-DRIFT-VERDICT[{BASIS}]: late-window worst {worst} "
          f"rate {rates_late[worst]:+.5f}/yr -> {worst_50y:+.3f}/50y — "
          + ("DRIFTS" if confirmed else "STATIONARY"),
          flush=True)


if __name__ == "__main__":
    main()
