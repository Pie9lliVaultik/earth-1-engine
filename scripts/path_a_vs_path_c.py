"""THE GROUNDING TEST — Path A (real cohort targets) vs Path C (authored).

Prereg: data/grounding_test_prereg.json, registered before the cascade
existed. Ruler: GSS 1972-2024 verified microdata (US only — grades
mechanism, not scope).

Arms, on GSS questions Earth-1 has never been calibrated against:
  PATH C  the engine's current behaviour — weights fitted WITHOUT this
          question's own real cohort targets (cross-question
          calibration: fit on OTHER questions' cells, apply here)
  PATH A  survey-matched — weights fitted from THIS question's real
          cohort targets at year Y1

Both are scored on LATER years (Y2...), never on the fitting year, so
neither arm sees the quantity it is graded on.

Metrics: national share MAE, cohort cell MAE, age-gradient direction.
Env: PAC_POP (default 200000).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.calibration import (_build_features, _get_country_index,
                                calibrate_cohort)
from earth1.genesis import genesis
from earth1.rng import logit, sigmoid

POP = int(os.environ.get("PAC_POP", "200000"))
AGE_TAGS = ["18_29", "30_44", "45_59", "60_plus"]


def main() -> None:
    truth = json.load(open("data/gss_truth.json"))
    civ = genesis(POP, 42)
    c2i, _ = _get_country_index(civ)
    us = civ.country == c2i["US"]
    feats = _build_features(civ, extended=True)
    masks = {}
    for i, tag in enumerate(AGE_TAGS):
        for e in range(3):
            m = (us & (civ.education == e)
                 & ((civ.age_bucket == i) if i < 3 else (civ.age_bucket >= 3)))
            if m.sum() >= 10:
                masks[f"{tag}|{e}"] = m
    print(f"US agents {int(us.sum()):,} in {len(masks)} cells", flush=True)

    res = {"path_a": {"nat": [], "cell": [], "gh": 0, "gn": 0},
           "path_c": {"nat": [], "cell": [], "gh": 0, "gn": 0}}
    for var, rec in truth.items():
        years = sorted(int(y) for y in rec["national"])
        if len(years) < 4:
            continue
        y_fit = years[0]
        fit_cells = {k.split("|", 1)[1]: v["share"]
                     for k, v in rec["cells"].items()
                     if k.startswith(f"{y_fit}|")}
        if len(fit_cells) < 6:
            continue
        base = rec["national"][str(y_fit)]["share"]
        # PATH A — this question's own real cohort targets
        w_a, info_a = calibrate_cohort(civ, base, fit_cells, masks)
        if not info_a["accepted"]:
            continue
        # PATH C — authored proxy: fit on OTHER questions' cells at
        # their own first years, i.e. the engine has never seen this
        # question's real structure
        other_cells, other_base = {}, []
        for v2, r2 in truth.items():
            if v2 == var:
                continue
            y2f = sorted(int(y) for y in r2["national"])[0]
            cc = {k.split("|", 1)[1]: val["share"]
                  for k, val in r2["cells"].items()
                  if k.startswith(f"{y2f}|")}
            if len(cc) >= 6:
                for k, val in cc.items():
                    other_cells.setdefault(k, []).append(val)
                other_base.append(r2["national"][str(y2f)]["share"])
        if not other_cells:
            continue
        pooled = {k: float(np.mean(v)) for k, v in other_cells.items()}
        w_c, info_c = calibrate_cohort(civ, float(np.mean(other_base)),
                                       pooled, masks)
        if not info_c["accepted"]:
            continue
        for y in years[1:]:
            nat = rec["national"][str(y)]["share"]
            bl = logit(np.array([base]))[0]
            cells_y = {k.split("|", 1)[1]: v["share"]
                       for k, v in rec["cells"].items()
                       if k.startswith(f"{y}|")}
            for arm, w in (("path_a", w_a), ("path_c", w_c)):
                p_nat = float(sigmoid(bl + feats[us] @ w).mean())
                res[arm]["nat"].append(abs(p_nat - nat))
                eng = {}
                for key, m in masks.items():
                    if key in cells_y:
                        pv = float(sigmoid(bl + feats[m] @ w).mean())
                        res[arm]["cell"].append(abs(pv - cells_y[key]))
                        eng[key] = pv
                yk = [k for k in eng if k.startswith("18_29")]
                ok = [k for k in eng if k.startswith("60_plus")]
                if yk and ok:
                    og = np.sign(np.mean([cells_y[k] for k in yk])
                                 - np.mean([cells_y[k] for k in ok]))
                    pg = np.sign(np.mean([eng[k] for k in yk])
                                 - np.mean([eng[k] for k in ok]))
                    if og != 0:
                        res[arm]["gn"] += 1
                        res[arm]["gh"] += int(og == pg)

    out = {"ruler": "GSS verified microdata (US only)", "pop": POP}
    for arm, r in res.items():
        out[arm] = {"national_mae": float(np.mean(r["nat"])) if r["nat"] else None,
                    "cell_mae": float(np.mean(r["cell"])) if r["cell"] else None,
                    "gradient_acc": r["gh"] / r["gn"] if r["gn"] else None,
                    "n_scored": len(r["nat"])}
        o = out[arm]
        print(f"  {arm.upper():7s} national-MAE {o['national_mae']:.4f} | "
              f"cell-MAE {o['cell_mae']:.4f} | gradient "
              f"{o['gradient_acc']:.2f} | n={o['n_scored']}", flush=True)
    json.dump(out, open("data/path_a_vs_path_c.json", "w"), indent=1)
    dn = 100 * (out["path_c"]["national_mae"] - out["path_a"]["national_mae"])
    dc = 100 * (out["path_c"]["cell_mae"] - out["path_a"]["cell_mae"])
    print(f"GROUNDING-VERDICT: Path A beats Path C by {dn:+.2f}pp national, "
          f"{dc:+.2f}pp cohort [VERIFIED RULER]", flush=True)


if __name__ == "__main__":
    main()
