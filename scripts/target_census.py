"""0.8 IT5-A — target-map census + writer attribution. NO repairs.

Part 1 (static): characterize life_force_target's lived-state -> target
mapping on (a) the production snapshot, (b) a genesis world, and
(c) three synthetic known-answer lived states (constant, healthy
heterogeneous, pole-biased) that the instrument must classify
correctly. Sensitivities via input perturbation.

Part 2 (dynamic): fresh 200k world, eta=0 (social operator OFF),
60 days. Each day, compare actual force movement against the pure
relax prediction f + r*(t - f); the residual is the net contribution
of every OTHER writer (contagion, feed, weather, memory, war,
flourishing, feedback...) per channel — this attributes KA2's
IDENTITY railing to its actual author.
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CH = ["FEAR", "DESIRE", "ECONOMICS", "COLLECTIVE", "IDENTITY",
      "CULTURE", "EXPERIENCE", "TEMPERAMENT"]
OUT = Path(os.environ.get("EARTH1_TC_OUT",
                          str(ROOT / "data" / "target_census_0_8")))

INPUTS = ("deprivation", "wealth", "employed", "spells", "mental",
          "addiction", "political", "social_need", "relationship",
          "n_events")


def target_stats(t, alive):
    x = t[alive]
    return {CH[c]: {
        "mean": round(float(x[:, c].mean()), 4),
        "sd": round(float(x[:, c].std()), 4),
        "q10": round(float(np.percentile(x[:, c], 10)), 4),
        "q90": round(float(np.percentile(x[:, c], 90)), 4),
        "mass_lo": round(float((x[:, c] < 0.05).mean()), 4),
        "mass_hi": round(float((x[:, c] > 0.95).mean()), 4),
    } for c in range(len(CH))}


def identical_fraction(t, alive):
    x = np.round(t[alive], 3)
    _, counts = np.unique(x, axis=0, return_counts=True)
    return round(float(counts.max() / x.shape[0]), 4)


def sensitivities(w):
    from earth1.life import life_force_target
    base = life_force_target(w.civ, w.life)
    out = {}
    for name in INPUTS:
        arr = getattr(w.life, name, None)
        if arr is None:
            continue
        orig = arr.copy()
        if arr.dtype == bool:
            setattr(w.life, name, ~orig)
        else:
            hi = np.clip(orig.astype(np.float64) + 0.2, 0, None)
            setattr(w.life, name, hi.astype(orig.dtype))
        t2 = life_force_target(w.civ, w.life)
        setattr(w.life, name, orig)
        d = (t2 - base).mean(axis=0)
        out[name] = {CH[c]: round(float(d[c]), 4)
                     for c in range(len(CH)) if abs(d[c]) > 1e-4}
    return out


def synthetic_arms(w):
    """Known-answer lived states, applied to a copy's life arrays."""
    import copy
    from earth1.life import life_force_target
    res = {}
    for arm in ("constant", "heterogeneous", "pole_biased"):
        w2 = copy.deepcopy(w)
        life = w2.life
        n = w2.civ.n
        rng = np.random.default_rng(5)
        if arm == "constant":
            vals = dict(deprivation=0.3, wealth=45.0, mental=0.6,
                        addiction=0.05, political=0.3, social_need=0.3,
                        relationship=0.5)
        elif arm == "heterogeneous":
            vals = dict(deprivation=rng.uniform(0, 1, n),
                        wealth=rng.uniform(0, 180, n),
                        mental=rng.uniform(0, 1, n),
                        addiction=rng.uniform(0, 0.4, n),
                        political=rng.uniform(0, 1, n),
                        social_need=rng.uniform(0, 1, n),
                        relationship=rng.uniform(0, 1, n))
        else:
            vals = dict(deprivation=1.0, wealth=0.0, mental=0.0,
                        addiction=0.0, political=0.0, social_need=1.0,
                        relationship=0.0)
        for k, v in vals.items():
            arr = getattr(life, k, None)
            if arr is not None:
                arr[:] = v
        t = life_force_target(w2.civ, w2.life)
        alive = w2.health.alive
        res[arm] = {"stats": target_stats(t, alive),
                    "identical_frac": identical_fraction(t, alive)}
    return res


def dynamic_attribution(days=60, n=200_000, relax=0.25):
    import earth1.alive as am
    import earth1.lab_archive.propagation_lab as plab
    from earth1.alive import birth_world, live_one_day
    from earth1.life import life_force_target

    am.propagate = plab.make_operator(eta=0.0)
    w = birth_world(n, 8850)
    rng = np.random.default_rng(8850)
    rows = []
    for d in range(1, days + 1):
        f0 = w.civ.forces.copy()
        t = life_force_target(w.civ, w.life)
        pred = f0 + relax * (t - f0)
        live_one_day(w, rng, relax=relax)
        f1 = w.civ.forces
        resid = (f1 - pred).mean(axis=0)
        tmean = t.mean(axis=0)
        if d % 5 == 0 or d == 1:
            rows.append({"day": d,
                         "target_mean": [round(float(v), 4)
                                         for v in tmean],
                         "force_mean": [round(float(v), 4)
                                        for v in f1.mean(axis=0)],
                         "nonrelax_residual": [round(float(v), 5)
                                               for v in resid]})
    return rows


def main():
    from earth1 import persistence
    from earth1.alive import birth_world
    from earth1.life import life_force_target

    OUT.mkdir(parents=True, exist_ok=True)
    report = {}

    snap = os.environ.get("EARTH1_ENSEMBLE_SNAPSHOT")
    if snap:
        d = Path(snap)
        adj = d / "adj.npz"
        w, _r, _i = persistence.load_world(
            d / "world.pkl", adj_path=(adj if adj.exists() else None))
        t = life_force_target(w.civ, w.life)
        report["production"] = {
            "stats": target_stats(t, w.health.alive),
            "identical_frac": identical_fraction(t, w.health.alive)}
        del w

    g = birth_world(200_000, 8801)
    tg = life_force_target(g.civ, g.life)
    report["genesis"] = {"stats": target_stats(tg, g.health.alive),
                         "identical_frac": identical_fraction(
                             tg, g.health.alive)}
    report["sensitivities"] = sensitivities(g)
    report["synthetic"] = synthetic_arms(g)
    print("static census done; running eta=0 writer attribution "
          "(60 days)...", flush=True)
    report["dynamic_eta0"] = dynamic_attribution()

    (OUT / "census.json").write_text(json.dumps(report, indent=1))
    for row in report["dynamic_eta0"][-3:]:
        print("day", row["day"])
        for c in range(8):
            print(f"   {CH[c]:12s} target {row['target_mean'][c]:6.3f} "
                  f"force {row['force_mean'][c]:6.3f} "
                  f"nonrelax_resid {row['nonrelax_residual'][c]:+8.5f}")
    print(f"-> {OUT/'census.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
