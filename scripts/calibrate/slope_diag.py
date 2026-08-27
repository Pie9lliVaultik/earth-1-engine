"""c005 — SLOPE DIAGNOSTIC (no fix): is the cohort under-modulation one
shared shrinkage or per-axis physics?

Per axis: regress MODEL cohort deviations (LOO-predicted cell value
minus its own predicted within-country mean) on WVS cohort deviations
(target cell minus true national). Slope ~equal and <<1 across axes =
global shrinkage (readout gain/λ/blend); slopes differing by axis =
physics, and the age coefficient is the first named change.
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from calibrate.decompose import CELLS  # noqa: E402


def main():
    from earth1.alive import birth_world, live_one_day
    from earth1.calibration import living_features
    from earth1.genesis import GENESIS_COUNTRY_CODES
    ax = json.load(open(os.path.join(
        ROOT, "data/benchmark_a/axis_targets_v1.json")))["axes"]
    seeds = [int(x) for x in os.environ.get(
        "EARTH1_POOL_SEEDS", "4242").split(",")]
    iso_of = {i: c for i, c in enumerate(GENESIS_COUNTRY_CODES)}
    per_axis_sums = {axis: {} for axis in CELLS}
    for sd_ in seeds:
        w = birth_world(20_000, sd_, substrate="c2plus_v1")
        rng = np.random.default_rng(sd_)
        for _ in range(180):
            live_one_day(w, rng)
        X = living_features(w)
        civ, alive = w.civ, w.health.alive
        yrs = 18.0 + np.asarray(civ.age) * 72.0
        for axis, fn in CELLS.items():
            labels = fn(civ, yrs)
            for ci in np.unique(civ.country[alive]):
                cm = alive & (civ.country == ci)
                for cell in np.unique(labels[cm]):
                    m = cm & (labels == cell)
                    if m.sum() >= int(os.environ.get("EARTH1_MIN_CELL", "25")):
                        k = (iso_of[ci], str(cell))
                        agg = per_axis_sums[axis].setdefault(
                            k, [np.zeros(X.shape[1]), 0])
                        agg[0] += X[m].sum(0)
                        agg[1] += int(m.sum())
        print(f"  world {sd_} pooled", flush=True)
    out = {}
    for axis, fn in CELLS.items():
        feats = {k: v[0] / v[1] for k, v in per_axis_sums[axis].items()
                 if v[1] >= 25 * len(seeds)}
        dev_w, dev_m, wts = [], [], []
        for item, cc in ax[axis].items():
            cells = [(c2, cell, d["yes"], d["n"]) for c2, cs in cc.items()
                     for cell, d in cs.items() if (c2, cell) in feats]
            countries = sorted({c[0] for c in cells})
            if len(countries) < 10:
                continue
            nat = {}
            for c2 in countries:
                mine = [(y, n) for cc2, _, y, n in cells if cc2 == c2]
                nat[c2] = sum(y * n for y, n in mine) / sum(n for _, n in mine)
            Xa = np.array([feats[(c2, cell)] for c2, cell, _, _ in cells])
            ya = np.array([y for _, _, y, _ in cells]).clip(1e-3, 1 - 1e-3)
            na = np.array([n for _, _, _, n in cells], dtype=float)
            la = np.log(ya / (1 - ya))
            grp = np.array([countries.index(c2) for c2, _, _, _ in cells])
            mu, sd = Xa.mean(0), np.maximum(Xa.std(0), 1e-9)
            Z = (Xa - mu) / sd
            for gi, c2 in enumerate(countries):
                te, tr = grp == gi, grp != gi
                A_ = Z[tr].T @ Z[tr] + 1.0 * np.eye(Z.shape[1])
                b = np.linalg.solve(A_, Z[tr].T @ (la[tr] - la[tr].mean()))
                p = 1 / (1 + np.exp(-(Z[te] @ b + la[tr].mean())))
                nte = na[te]
                pnat = float((p * nte).sum() / nte.sum())
                for pk, yk, nk in zip(p, ya[te], nte):
                    dev_m.append(pk - pnat)
                    dev_w.append(yk - nat[c2])
                    wts.append(nk)
        dw, dm, wt = map(np.array, (dev_w, dev_m, wts))
        slope = float((wt * dw * dm).sum() / (wt * dw * dw).sum())
        r = float(np.corrcoef(dw, dm)[0, 1])
        out[axis] = {"slope": round(slope, 3), "r": round(r, 3),
                     "wvs_dev_sd_pp": round(float(np.sqrt(
                         (wt * dw * dw).sum() / wt.sum())) * 100, 2),
                     "model_dev_sd_pp": round(float(np.sqrt(
                         (wt * dm * dm).sum() / wt.sum())) * 100, 2),
                     "n": len(dw)}
    json.dump(out, open(os.path.join(
        ROOT, "data/cycles/c005_slope_diag.json"), "w"), indent=1)
    print(f"{'axis':8s} {'slope':>7s} {'r':>6s} {'wvs sd':>7s} {'model sd':>9s} {'n':>6s}")
    for k, v in sorted(out.items(), key=lambda kv: kv[1]["slope"]):
        print(f"{k:8s} {v['slope']:7.3f} {v['r']:6.3f} {v['wvs_dev_sd_pp']:7.2f} "
              f"{v['model_dev_sd_pp']:9.2f} {v['n']:6d}")


if __name__ == "__main__":
    main()
