"""THE cohort feature set — single shared module (founder ruling
2026-08-27): the 20k cycle runner transfers to the canonical A-v2 task
only while their feature sets match (validated: blind copy floor 10.09
vs harness 10.08). Every feature addition lands HERE and nowhere else;
scripts/calibrate/cycle.py imports this now and scripts/benchmark_a/
run_v2.py must be wired to it at its next run (until then its
country-level features remain the frozen v2 set, which this module
reproduces at cell level via earth1.calibration.living_features).
"""
import numpy as np

BANDS = (("18-29", 18, 30), ("30-49", 30, 50), ("50+", 50, 121))


def cell_features(w, min_agents: int = 25) -> dict:
    """(iso2, band) -> feature vector: living_features means per cell,
    plus substrate demographic composition (sex/education/income
    shares) when the world carries them. Additions beyond this list
    require a named calibration cycle."""
    from earth1.calibration import living_features
    from earth1.genesis import GENESIS_COUNTRY_CODES
    X = living_features(w)
    civ, alive = w.civ, w.health.alive
    years = 18.0 + np.asarray(civ.age) * 72.0
    sex = getattr(civ, "sex", None)
    out = {}
    for iso2, ci in ((c, i) for i, c in enumerate(GENESIS_COUNTRY_CODES)):
        cm = alive & (civ.country == ci)
        if not cm.any():
            continue
        for bname, lo, hi in BANDS:
            m = cm & (years >= lo) & (years < hi)
            if m.sum() < min_agents:
                continue
            base = X[m].mean(0)
            demo = [float((civ.education[m] == 2).mean()),
                    float((civ.education[m] == 0).mean()),
                    float((civ.income[m] == 2).mean()),
                    float((civ.income[m] == 0).mean()),
                    float(np.asarray(civ.urban)[m].mean()),
                    float((np.asarray(sex)[m] == 1).mean())
                    if sex is not None else 0.5]
            out[(iso2, bname)] = np.concatenate([base, demo])
    return out
