"""Frozen-cell cohort scorer (founder ruling 2026-08-28).

Cells and weights are FROZEN from WVS-7 DEV
(data/frozen_cohort_cells.v1.json). The floor is physics-invariant by
construction: for a held-out country, floor(item, band) = n-weighted
mean of the OTHER countries' same-(item, band) WVS values — pure WVS,
no world input, identical for every physics configuration. The model
(LOO ridge on world cell features, country-level fallback for cells
the world populates thinly) is scored on the SAME frozen cells, so any
model-vs-model comparison across physics configs is on identical
ground. usage: frozen_score.py <label>  (flags from env)
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

BANDS = {"18-29": (18, 30), "30-49": (30, 50), "50+": (50, 121)}


def main(label):
    from earth1.alive import birth_world, live_one_day
    from earth1.calibration import living_features
    from earth1.genesis import GENESIS_COUNTRY_CODES
    fz = json.load(open(os.path.join(ROOT, "data/frozen_cohort_cells.v1.json")))
    cells = fz["cells"]
    sub = None if os.environ.get("EARTH1_SUBSTRATE_FLAG", "off") == "off" \
        else "c2plus_v1"
    w = birth_world(20_000, 4242, substrate=sub)
    rng = np.random.default_rng(4242)
    for _ in range(180):
        live_one_day(w, rng)
    X = living_features(w)
    civ, alive = w.civ, w.health.alive
    yrs = 18.0 + np.asarray(civ.age) * 72.0
    feats, cfeats = {}, {}
    fallback = 0
    for ci, iso2 in enumerate(GENESIS_COUNTRY_CODES):
        cm = alive & (civ.country == ci)
        if cm.any():
            cfeats[iso2] = X[cm].mean(0)
            for b, (lo, hi) in BANDS.items():
                m = cm & (yrs >= lo) & (yrs < hi)
                if m.sum() >= 25:
                    feats[(iso2, b)] = X[m].mean(0)
    by_item = {}
    for c in cells:
        by_item.setdefault(c["item"], []).append(c)
    errs_m, errs_f, wts = [], [], []
    lvl_m, dev_m, dev_ref = [], [], []
    for item, cl in by_item.items():
        countries = sorted({c["iso2"] for c in cl if c["iso2"] in cfeats})
        if len(countries) < 10:
            continue
        rows = [c for c in cl if c["iso2"] in cfeats]
        Xa = np.array([feats.get((c["iso2"], c["band"]),
                                 cfeats[c["iso2"]]) for c in rows])
        fallback += sum(1 for c in rows
                        if (c["iso2"], c["band"]) not in feats)
        ya = np.array([c["yes"] for c in rows]).clip(1e-3, 1 - 1e-3)
        na = np.array([c["n"] for c in rows], float)
        la = np.log(ya / (1 - ya))
        grp = np.array([countries.index(c["iso2"]) for c in rows])
        mu, sd = Xa.mean(0), np.maximum(Xa.std(0), 1e-9)
        Z = (Xa - mu) / sd
        band_arr = np.array([c["band"] for c in rows])
        for gi, iso2 in enumerate(countries):
            te, tr = grp == gi, grp != gi
            A_ = Z[tr].T @ Z[tr] + 1.0 * np.eye(Z.shape[1])
            b_ = np.linalg.solve(A_, Z[tr].T @ (la[tr] - la[tr].mean()))
            pm = 1 / (1 + np.exp(-(Z[te] @ b_ + la[tr].mean())))
            nat = float((ya[te] * na[te]).sum() / na[te].sum())
            pnat = float((pm * na[te]).sum() / na[te].sum())
            # DECOMPOSITION (frozen-cells ruling operationalized):
            # LEVEL = |predicted national − WVS national|;
            # STRUCTURE = |model deviation − WVS deviation| vs the
            # zero-deviation reference E|WVS deviation| (2.57pp).
            # Level floor (invariant, no oracle): cross-country
            # band-mean prediction, collected in errs_f.
            for k in np.flatnonzero(te):
                b = band_arr[k]
                m_tr = tr & (band_arr == b)
                fl = float((ya[m_tr] * na[m_tr]).sum() / na[m_tr].sum())
                errs_f.append(abs(fl - ya[k]) * na[k])
                wts.append(na[k])
            errs_m.extend(np.abs(pm - ya[te]) * na[te])
            lvl_m.append((abs(pnat - nat), float(na[te].sum())))
            dev_m.extend(np.abs((pm - pnat) - (ya[te] - nat)) * na[te])
            dev_ref.extend(np.abs(ya[te] - nat) * na[te])
    W = sum(wts)
    out = {"label": label,
           "flags": {k: os.environ.get(k, "") for k in
                     ("EARTH1_HARDSHIP_MODE", "EARTH1_INCOME_CALIBRATION",
                      "EARTH1_SUBSTRATE_FLAG", "EARTH1_MORTALITY_MODE",
                      "EARTH1_GM_OTHER_SHARE", "EARTH1_WANT_SCALE")},
           "model_mae_pp": round(float(sum(errs_m) / W) * 100, 3),
           "invariant_floor_mae_pp": round(float(sum(errs_f) / W) * 100, 3),
           "n_frozen_cells_scored": len(wts),
           "world_thin_cell_fallbacks": fallback,
           "level_mae_pp": round(float(sum(a * b for a, b in lvl_m)
                                       / sum(b for _, b in lvl_m)) * 100, 3),
           "structure_dev_mae_pp": round(float(sum(dev_m) / W) * 100, 3),
           "structure_zero_ref_pp": round(float(sum(dev_ref) / W) * 100, 3),
           "frozen_sha": fz["nothing_above_this_line_may_change"]}
    json.dump(out, open(os.path.join(
        ROOT, f"data/cycles/frozen_{label}.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
