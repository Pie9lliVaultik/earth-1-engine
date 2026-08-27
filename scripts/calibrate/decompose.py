"""c004 — DECOMPOSITION CYCLE (no fix): split the cohort miss by axis.

For each axis (age, edu, sex, income, age×edu): LOO-by-country ridge on
Earth-1 (country, cell) features vs WVS axis targets, against the
blind national-copy floor on the identical cells. The axis with the
largest model-minus-floor gap names the next physics lever.
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

CELLS = {
    "age": lambda civ, yrs: np.where(yrs < 30, "a18-29",
                                     np.where(yrs < 50, "a30-49", "a50+")),
    "edu": lambda civ, yrs: np.array(["e_low", "e_mid", "e_high"])[civ.education],
    "sex": lambda civ, yrs: np.array(["s_m", "s_f"])[np.asarray(civ.sex)],
    "income": lambda civ, yrs: np.array(["i_low", "i_mid", "i_high"])[civ.income],
}
CELLS["age_edu"] = lambda civ, yrs: np.char.add(
    np.char.add(CELLS["age"](civ, yrs).astype(str), "x"),
    CELLS["edu"](civ, yrs).astype(str))


def main():
    from earth1.alive import birth_world, live_one_day
    from earth1.calibration import living_features
    from earth1.genesis import GENESIS_COUNTRY_CODES
    ax = json.load(open(os.path.join(
        ROOT, "data/benchmark_a/axis_targets_v1.json")))["axes"]
    w = birth_world(20_000, 4242, substrate="c2plus_v1")
    rng = np.random.default_rng(4242)
    for _ in range(180):
        live_one_day(w, rng)
    X = living_features(w)
    civ, alive = w.civ, w.health.alive
    yrs = 18.0 + np.asarray(civ.age) * 72.0
    iso_of = {i: c for i, c in enumerate(GENESIS_COUNTRY_CODES)}
    report = {}
    for axis, fn in CELLS.items():
        labels = fn(civ, yrs)
        feats = {}
        for ci in np.unique(civ.country[alive]):
            cm = alive & (civ.country == ci)
            for cell in np.unique(labels[cm]):
                m = cm & (labels == cell)
                if m.sum() >= 25:
                    feats[(iso_of[ci], str(cell))] = X[m].mean(0)
        errs_m, errs_f = [], []
        for item, cc in ax[axis].items():
            cells = [(c2, cell, d["yes"], d["n"]) for c2, cells_ in cc.items()
                     for cell, d in cells_.items() if (c2, cell) in feats]
            countries = sorted({c[0] for c in cells})
            if len(countries) < 10:
                continue
            nat = {}
            for c2 in countries:
                mine = [(y, n) for cc2, _, y, n in cells if cc2 == c2]
                nat[c2] = sum(y * n for y, n in mine) / sum(n for _, n in mine)
            Xa = np.array([feats[(c2, cell)] for c2, cell, y, n in cells])
            ya = np.array([y for _, _, y, n in cells]).clip(1e-3, 1 - 1e-3)
            la = np.log(ya / (1 - ya))
            grp = np.array([countries.index(c2) for c2, _, _, _ in cells])
            mu, sd = Xa.mean(0), np.maximum(Xa.std(0), 1e-9)
            Z = (Xa - mu) / sd
            Xn = np.array([np.mean([feats[(c2, cell)] for cc2, cell, _, _
                                    in cells if cc2 == c2], axis=0)
                           for c2 in countries])
            yn = np.array([nat[c2] for c2 in countries]).clip(1e-3, 1 - 1e-3)
            ln = np.log(yn / (1 - yn))
            Zn = (Xn - mu) / sd
            for gi, c2 in enumerate(countries):
                te, tr = grp == gi, grp != gi
                trn = np.arange(len(countries)) != gi
                bm, bf = None, None
                for lam in (0.1, 1.0, 10.0):
                    A_ = Z[tr].T @ Z[tr] + lam * np.eye(Z.shape[1])
                    b = np.linalg.solve(A_, Z[tr].T @ (la[tr] - la[tr].mean()))
                    e = np.abs(1 / (1 + np.exp(-(Z[te] @ b + la[tr].mean())))
                               - ya[te]).mean()
                    bm = e if bm is None or e < bm else bm
                    An = Zn[trn].T @ Zn[trn] + lam * np.eye(Zn.shape[1])
                    bn = np.linalg.solve(An, Zn[trn].T @ (ln[trn] - ln[trn].mean()))
                    pn = float(Zn[gi] @ bn + ln[trn].mean())
                    ef = np.abs(1 / (1 + np.exp(-pn)) - ya[te]).mean()
                    bf = ef if bf is None or ef < bf else bf
                errs_m.append(bm)
                errs_f.append(bf)
        report[axis] = {"model_mae_pp": round(float(np.mean(errs_m)) * 100, 3),
                        "floor_mae_pp": round(float(np.mean(errs_f)) * 100, 3),
                        "gap_pp": round(float(np.mean(errs_m) - np.mean(errs_f)) * 100, 3),
                        "n_cells_scored": len(errs_m)}
    json.dump(report, open(os.path.join(
        ROOT, "data/cycles/c004_decomposition.json"), "w"), indent=1)
    print(f"{'axis':8s} {'model':>8s} {'floor':>8s} {'gap':>7s} {'cells':>6s}")
    for axk, r in sorted(report.items(), key=lambda kv: -kv[1]["gap_pp"]):
        print(f"{axk:8s} {r['model_mae_pp']:8.2f} {r['floor_mae_pp']:8.2f} "
              f"{r['gap_pp']:+7.2f} {r['n_cells_scored']:6d}")


if __name__ == "__main__":
    main()
