"""Phase 2A dose-response harness (PHASE_2A_FORCING_IDENTIFIABILITY.md §4).
Development-only. Drives UNCHANGED physics inputs (firm_health, cost,
memory) on schedules; no module is modified. Usage: arm <A1..A8> <rep>."""
import json, os, subprocess, sys, time
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from earth1.alive import live_one_day, PHYSICS_VERSION
from earth1.backtest import REGISTRY
from earth1.branch import apply
from earth1 import persistence
from earth1.types import Force
OUT = "/opt/earth1-data/benchmark_b"
DAYS, SEED_BASE = 180, 977 * 13
COVID = next(e for e in REGISTRY if e.id == "covid_2020").scenario
import copy as _copy


def cov(fd=None, trade=None):
    sc = _copy.deepcopy(COVID)
    if fd is not None: sc.firm_damage = fd
    if trade is not None: sc.trade_shock = trade
    return sc


ARMS = {
    "A1": {"oneshot": cov(fd=0.10)}, "A2": {"oneshot": cov()}, "A3": {"oneshot": cov(fd=0.70)},
    "A4": {"oneshot": cov(fd=0.0), "daily_fd": (0.35 / 90, 90)},
    "A5": {"oneshot": cov(fd=0.0), "daily_fd": (0.70 / 180, 180)},
    "A6": {"oneshot": cov(), "trade_revert_day": 90},
    "A7": {"oneshot": cov(fd=0.0, trade=0.0)},
    "A8": {"oneshot": cov()},
}


def main(arm, rep):
    spec = ARMS[arm]
    w, _rs, _ = persistence.load_world(os.path.join(OUT, "warm.pkl"))
    rng = np.random.default_rng(SEED_BASE + rep)
    from earth1.genesis import census_weights
    cw = census_weights(w.civ)
    cost0 = w.life.cost.copy()
    apply(w, spec["oneshot"], rng)
    jl, dest, fear, hope, wealth, fired = [], [], [], [], [], []
    for d in range(DAYS):
        if "daily_fd" in spec:
            per, until = spec["daily_fd"]
            if d < until:
                w.life.firm_health[:] = np.clip(w.life.firm_health - per, 0, 1)
        if spec.get("trade_revert_day") == d:
            w.life.cost[:] = cost0
        st = live_one_day(w, rng)
        alive = w.health.alive; lf = w.life.in_lf & alive
        jl.append(float(cw[(~w.life.employed) & lf].sum()))
        dest.append(float(cw[(w.life.deprivation > 0.99) & alive].sum()))
        fear.append(float(np.average(w.civ.forces[alive, Force.FEAR], weights=cw[alive])))
        hope.append(float(np.average(w.flourishing.hope[alive], weights=cw[alive])))
        wealth.append(float(np.median(w.life.wealth[alive])))
        fired.append(int(st.get("cascades_fired", 0)))
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    json.dump({"arm": arm, "rep": rep, "days": DAYS, "jobless_path": jl, "destitute_path": dest,
               "fear_path": fear[::5], "hope_path": hope[::5], "wealth_path": wealth[::5],
               "cascades": int(np.sum(fired)), "dead_end": float(cw[~w.health.alive].sum()),
               "sat_stored_end": float(np.mean((w.civ.forces[w.health.alive] > 0.98) | (w.civ.forces[w.health.alive] < 0.02))),
               "commit": sha, "physics_version": PHYSICS_VERSION},
              open(os.path.join(OUT, f"dose_{arm}_r{rep}.json"), "w"))
    print("DOSE ARM DONE", arm, rep)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
