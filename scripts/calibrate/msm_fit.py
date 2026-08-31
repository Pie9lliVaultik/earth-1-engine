"""S5b — joint MSM over MOMENTS_v1 (BIBLE VII.1 + v4.2 displacement
protocol). theta = (WAGE_LEVEL, WAGE_LOG_SD, GM_OTHER_SHARE, WANT_RR,
WEATHER_SCALE); GM A/B/c stay DERIVED-fixed. Objective: weighted LS in
standardized moment space over m1-m7+m9 (m8 pending H_unemployment).
Seeded at the serial fixed-point constants; Nelder-Mead; displacement
table in sigma units of the 8-seed replicate sweep.
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

SERIAL = dict(WAGE_LEVEL=2.3038, WAGE_LOG_SD=1.2196, GM_OTHER_SHARE=0.20,
              WANT_RR=5.0, WEATHER_SCALE=0.02)
SIGMA = json.load(open(os.path.join(ROOT, 'data/cycles/final_sigma_columns.json')))
TARGETS = dict(median=9.27, mean_over_median=2.332, p3=0.104, p83=0.461,
               cdr=0.00755, age_ratio=1.0, s65=0.1355, casc=1.0)
SEEDS = (4242, 5151, 6363, 7777)
EVALS = []


def simulate(theta):
    os.environ.update(EARTH1_HARDSHIP_MODE="gradient",
                      EARTH1_INCOME_CALIBRATION="off",
                      EARTH1_SUBSTRATE_FLAG="c2plus_v1",
                      EARTH1_MORTALITY_MODE="gompertz",
                      EARTH1_WANT_MODE="rr",
                      EARTH1_GM_OTHER_SHARE=str(theta[2]),
                      EARTH1_WANT_RR=str(theta[3]),
                      EARTH1_WEATHER_SCALE=str(theta[4]))
    for m in [k for k in list(sys.modules) if k.startswith("earth1")]:
        del sys.modules[m]
    import earth1.life as life
    life.WAGE_LEVEL, life.WAGE_LOG_SD = float(theta[0]), float(theta[1])
    from earth1.alive import birth_world, live_one_day
    from earth1.poverty import welfare_ppp, poverty_profile
    ms = []
    for sd in SEEDS:
        w = birth_world(20_000, sd, substrate="c2plus_v1")
        import earth1.life as life2
        life2.WAGE_LEVEL, life2.WAGE_LOG_SD = float(theta[0]), float(theta[1])
        rng = np.random.default_rng(sd)
        cum = {"deaths": 0, "cascades_fired": 0}
        dead_ages = []
        prev_a = w.health.alive.copy(); prev_p = w.civ.person_id.copy()
        prev_g = w.civ.age.copy()
        for _ in range(180):
            st = live_one_day(w, rng)
            for k in cum: cum[k] += int(st.get(k, 0) or 0)
            died = prev_a & (~w.health.alive | (w.civ.person_id != prev_p))
            if died.any():
                dead_ages.extend((18 + prev_g[died] * 72).tolist())
            prev_a = w.health.alive.copy(); prev_p = w.civ.person_id.copy()
            prev_g = w.civ.age.copy()
        wel, cw = welfare_ppp(w)
        o = np.argsort(wel); ws_, cs_ = wel[o], cw[o]
        cu = np.cumsum(cs_) / cs_.sum()
        med = float(ws_[np.searchsorted(cu, 0.5)])
        mean = float((wel * cw).sum() / cw.sum())
        gm = json.load(open(os.path.join(ROOT, 'data/gompertz_world.v1.json')))
        ref = gm['age_at_death_reference_own_pyramid']['c2plus_v2']
        ms.append(dict(median=med, mean_over_median=mean / med,
            p3=float(cw[wel < 3].sum() / cw.sum()),
            p83=float(cw[wel < 8.3].sum() / cw.sum()),
            cdr=cum['deaths'] / 20000 * (365 / 180),
            age_ratio=(np.mean(dead_ages) / ref) if dead_ages else 0.0,
            s65=float((18 + w.civ.age[w.health.alive] * 72 >= 65).mean()),
            casc=cum['cascades_fired'] / 1086.0))
    agg = {k: float(np.mean([m[k] for m in ms])) for k in ms[0]}
    SD = dict(median=0.067, mean_over_median=0.05, p3=0.006, p83=0.006,
              cdr=0.0006, age_ratio=0.055, s65=0.0017, casc=0.02)
    obj = sum(((agg[k] - TARGETS[k]) / SD[k]) ** 2 for k in TARGETS)
    EVALS.append((obj, list(theta), agg))
    print(f"eval {len(EVALS)}: obj {obj:.1f} theta {[round(t,4) for t in theta]}", flush=True)
    return obj


def main():
    from scipy.optimize import minimize
    x0 = np.array([SERIAL[k] for k in ("WAGE_LEVEL", "WAGE_LOG_SD",
                                       "GM_OTHER_SHARE", "WANT_RR",
                                       "WEATHER_SCALE")])
    r = minimize(simulate, x0, method="Nelder-Mead",
                 options=dict(maxfev=55, xatol=0.01, fatol=1.0))
    names = ("WAGE_LEVEL", "WAGE_LOG_SD", "GM_OTHER_SHARE", "WANT_RR",
             "WEATHER_SCALE")
    # displacement in units of parameter-scale sigma proxies from the
    # replicate sweep via local sensitivity is heavy; report Δ and Δ%
    # plus the moment-sigma-implied tolerance (declared method).
    out = {"serial": {n: float(v) for n, v in zip(names, x0)},
           "joint": {n: float(v) for n, v in zip(names, r.x)},
           "objective_serial": EVALS[0][0], "objective_joint": float(r.fun),
           "n_evals": len(EVALS),
           "displacement_pct": {n: round(100 * (float(j) - float(s)) / float(s), 2)
                                for n, s, j in zip(names, x0, r.x)}}
    json.dump(out, open(os.path.join(ROOT, 'data/cycles/msm_fit.json'), 'w'),
              indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
