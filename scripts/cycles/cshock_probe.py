"""c-SHOCK probe: shock-transmission chain, cliff vs gradient.

Prereg: ops/alive/cycles/cshock.md (DIAGNOSE instrument). Contrast is
branch-vs-null per the null_branch() contract; the mode contrast is
between (dose - null) EFFECTS, never between raw worlds.

usage: cshock_probe.py <seed> <arm: dose|null> <pop>
EARTH1_HARDSHIP_MODE must be exported by the wrapper BEFORE python
starts (life.py reads it at import). The probe records the mode the
physics actually loaded so a silent default is unrecordable.
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

WARM, WINDOW = 90, 120
EVERY = 10


def chain_metrics(w):
    from earth1.consequences import protest_risk
    from earth1.types import Force
    alive = w.health.alive
    dep = w.life.deprivation[alive]
    f = w.civ.forces[alive]
    return {
        "dep_mean": float(dep.mean()),
        "dep_gt04": float((dep > 0.4).mean()),
        "dep_gt099": float((dep > 0.99).mean()),
        "fear_gt06": float((f[:, Force.FEAR] > 0.6).mean()),
        "coll_gt075": float((f[:, Force.COLLECTIVE] > 0.75).mean()),
        "surge_joint": float(((f[:, Force.COLLECTIVE] > 0.75)
                              & (f[:, Force.FEAR] > 0.6)).mean()),
        "protest_risk_sum": float(protest_risk(w).sum()),
        "employed": float(w.life.employed[alive].mean()),
    }


def main(seed, arm, pop):
    from earth1 import life as life_mod
    from earth1.alive import birth_world, live_one_day
    from earth1.branch import Scenario, apply, null_branch
    from earth1.genesis import GENESIS_COUNTRY_CODES
    w = birth_world(pop, seed, substrate="c2plus_v1")
    rng = np.random.default_rng(977 * 13 + seed)
    for _ in range(WARM):
        live_one_day(w, rng)
    pre = chain_metrics(w)
    sc = null_branch() if arm == "null" else Scenario(
        id="protest_class_dose", label="registered uniform protest dose",
        forces={"fear": 0.2, "economics": -0.15}, countries=None,
        firm_damage=0.1, trade_shock=0.0, persists_days=60)
    apply(w, sc, rng)
    t0 = float(w.day)
    series = []
    # v2 EVENT-TIME counting (VERIFY-2, cshock.md): terminal-residue
    # counting is expiry-biased — residues leave the active set at
    # level<0.01 (~100d at h=30), so onsets fired in the first ~20d of
    # a 120d window are invisible at end-of-window. Capture every
    # residue the tick it appears instead; keep the terminal count to
    # quantify the bias. Also log ALL rules (competing-rule dynamics)
    # and hot-locality-days (episode intensity, immune to
    # entry-counting).
    events, seen = [], set()
    hot_days = 0
    for d in range(WINDOW):
        live_one_day(w, rng)
        for r in (getattr(w.chronicle, "cascade_residues", None) or []):
            key = (r["rule"], float(r["day"]), int(r["loc"]))
            if key not in seen:
                seen.add(key)
                events.append({"rule": r["rule"], "day": float(r["day"]),
                               "loc": int(r["loc"])})
        ep = getattr(w.chronicle, "cascade_episode_active", None) or set()
        hot_days += sum(1 for k in ep if k[0] == "collective_surge")
        if (d + 1) % EVERY == 0:
            series.append({"day": d + 1, **chain_metrics(w)})
    onsets, onsets_ev = {}, {}
    for r in (getattr(w.chronicle, "cascade_residues", None) or []):
        if r["rule"] == "collective_surge" and r["day"] >= t0:
            iso = GENESIS_COUNTRY_CODES[int(r["loc"]) // 1000]
            onsets[iso] = onsets.get(iso, 0) + 1
    for e in events:
        if e["rule"] == "collective_surge" and e["day"] >= t0:
            iso = GENESIS_COUNTRY_CODES[e["loc"] // 1000]
            onsets_ev[iso] = onsets_ev.get(iso, 0) + 1
    out = os.environ.get("CSHOCK_OUT", "/opt/earth1-data/cshock")
    os.makedirs(out, exist_ok=True)
    mode = life_mod.HARDSHIP_MODE
    json.dump({"seed": seed, "arm": arm, "pop": pop, "mode": mode,
               "pre": pre, "series": series, "final": chain_metrics(w),
               "onsets": onsets, "onsets_total": int(sum(onsets.values())),
               "onsets_event": onsets_ev,
               "onsets_event_total": int(sum(onsets_ev.values())),
               "hot_locality_days": int(hot_days),
               "events": events},
              open(os.path.join(out, f"{mode}_{arm}_{pop}_{seed}.json"), "w"),
              indent=1)
    print("CSHOCK DONE", mode, arm, pop, seed,
          "onsets_terminal", sum(onsets.values()),
          "onsets_event", sum(onsets_ev.values()),
          "hot_days", hot_days)


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2], int(sys.argv[3]))
