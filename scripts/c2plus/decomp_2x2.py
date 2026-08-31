"""2x2 DEV decomposition (founder ruling 2026-08-27).

Two changes landed together — population substrate and hardship physics
— so nothing may be attributed until they are separated. Cells:
  incumbent/cliff (canonical reference) | incumbent/gradient
  C2+v2/cliff                           | C2+v2/gradient
Yields delta_C2, delta_gradient, delta_interaction on every scored
observable. usage: decomp_2x2.py <substrate:incumbent|c2plus> <mode:cliff|gradient>
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

OUT = os.environ.get("DECOMP_OUT", "/opt/earth1-data/c2plus/decomp")
POP = int(os.environ.get("DECOMP_POP", "20000"))
DAYS = int(os.environ.get("DECOMP_DAYS", "180"))
SEED = 4242


def main(substrate, mode):
    os.environ["EARTH1_HARDSHIP_MODE"] = mode
    from earth1.alive import birth_world, live_one_day
    from earth1.genesis import census_weights
    from earth1.observables import collect
    from earth1.poverty import mortality_structure, poverty_profile

    os.makedirs(OUT, exist_ok=True)
    sub = None if substrate == "incumbent" else "c2plus_v1"
    w = birth_world(POP, SEED, substrate=sub)
    rng = np.random.default_rng(SEED)
    cum = {k: 0 for k in ("deaths", "births", "disease_deaths",
                          "cascades_fired", "firms_failed",
                          "starved_or_parched", "war_deaths",
                          "weather_deaths", "gm_deaths")}
    dead_ages = []
    by_cause = {}
    # INSTRUMENT FIX (2026-08-31): dead slots are REBORN within the
    # same tick, so prev_alive & ~alive missed ~95% of deaths (per-run
    # capture was ~30 of ~780 at 200k; every prior age-at-death figure
    # from this script carried ±3.5yr noise, not the claimed ±1).
    # Detection now uses person_id turnover; ages from the PRE-tick
    # snapshot; cause_of_death read post-tick is the dead occupant's
    # (rebirth does not rewrite it before the next death).
    prev_alive = w.health.alive.copy()
    prev_pid = w.civ.person_id.copy()
    prev_age = w.civ.age.copy()
    for _ in range(DAYS):
        st = live_one_day(w, rng)
        for k in cum:
            cum[k] += int(st.get(k, 0) or 0)
        died = prev_alive & (~w.health.alive
                             | (w.civ.person_id != prev_pid))
        if died.any():
            ages_d = 18.0 + prev_age[died] * 72.0
            dead_ages.extend(ages_d.tolist())
            cod = w.health.cause_of_death[died]
            for a_, c_ in zip(ages_d.tolist(), cod.tolist()):
                by_cause.setdefault(int(c_), []).append(a_)
        prev_alive = w.health.alive.copy()
        prev_pid = w.civ.person_id.copy()
        prev_age = w.civ.age.copy()
    o = collect(w, cum)
    a = w.health.alive
    cw = census_weights(w.civ)[a]
    tot = cw.sum()
    dep = w.life.deprivation[a]
    rec = {
        "substrate": substrate, "mode": mode, "pop": POP, "days": DAYS,
        "poverty": poverty_profile(w),
        "mortality_structure": mortality_structure(np.array(dead_ages)),
        "crude_death_rate_yr": cum["deaths"] / POP * (365.0 / DAYS),
        "reference_crude_death_rate_yr": 0.0076,
        "deaths": cum["deaths"], "starved": cum["starved_or_parched"],
        "disease_deaths": cum["disease_deaths"], "war_deaths": cum["war_deaths"],
        "weather_deaths": cum["weather_deaths"],
        "gm_deaths": cum["gm_deaths"],
        "deaths_by_cause": {str(k): {"n": len(v),
                                     "mean_age": round(sum(v)/len(v), 1)}
                            for k, v in by_cause.items()},
        "births": cum["births"], "cascades": cum["cascades_fired"],
        "firms_failed": cum["firms_failed"],
        "employment_rate": o["employment_rate"],
        "wealth_mean": o["wealth_mean"],
        "dep_mean": float((cw * dep).sum() / tot),
        "dep_gt_half": float(cw[dep > 0.5].sum() / tot),
        "dep_gt_99": float(cw[dep > 0.99].sum() / tot),
        "force_mean": o["force_mean"], "force_sd": o["force_sd"],
        "alive_end": int(a.sum()),
    }
    json.dump(rec, open(os.path.join(OUT, f"{substrate}_{mode}.json"), "w"),
              indent=1)
    print("CELL DONE", substrate, mode, flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
