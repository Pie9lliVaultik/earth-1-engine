"""C2 step 4: religiosity injection + COHORT-LEVEL calibration targets.

Fixes the ecological fallacy measured in step 3: fitting only on
country means teaches a cross-country religiosity weight that is wrong
within countries. Here the ridge sees BOTH country means (GOQA) and
real within-country age-bucket cells (official microdata).

Held-out by country (LOO over cohort-truth countries). Reports:
  country MAE | cohort bucket MAE | age-gradient direction accuracy
for: country-only fit vs country+cohort fit, with religiosity ON.
Env: C4_POP (default 200000), EARTH1_RELIGIOSITY=1 to inject.
"""
from __future__ import annotations

import csv
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.benchmark import ISO3_TO_ISO2
from earth1.calibration import _build_features, _get_country_index
from earth1.genesis import genesis
from earth1.rng import logit, sigmoid

POP = int(os.environ.get("C4_POP", "200000"))
BUCKETS = ["18_29", "30_44", "45_59", "60_plus"]
MIN_AGENTS = 30
LAM = 0.1


def main() -> None:
    civ = genesis(POP, 42)
    code_to_idx, _ = _get_country_index(civ)
    feats = _build_features(civ, extended=True)
    n_feat = feats.shape[1]
    has_rel = getattr(civ, "religiosity", None) is not None
    gt = {q["id"]: q for q in
          json.load(open("data/benchmark/goqa_ground_truth.json"))}
    cells = {}
    for r in csv.DictReader(open("data/wvs_w7_cohort_by_country.csv")):
        iso2 = ISO3_TO_ISO2.get(r["country"])
        if iso2:
            cells.setdefault(r["qcode"], {}).setdefault(
                iso2, {})[r["age_bucket"]] = float(r["yes_weighted"])

    res = {"country_only": {"cty": [], "coh": [], "gh": 0, "gn": 0},
           "with_cohorts": {"cty": [], "coh": [], "gh": 0, "gn": 0}}
    for qcode, by_cc in cells.items():
        if qcode not in gt:
            continue
        q = gt[qcode]
        ct = {ISO3_TO_ISO2[c]: d["yes"] for c, d in q["countries"].items()
              if c in ISO3_TO_ISO2}
        g = q["global_yes_popweighted"]
        bl = logit(np.array([g]))[0]
        cmasks = {cc: civ.country == code_to_idx[cc]
                  for cc in set(list(ct) + list(by_cc)) if cc in code_to_idx}
        bmasks = {}
        for cc, cm in cmasks.items():
            for i, b in enumerate(BUCKETS):
                bm = cm & ((civ.age_bucket == i) if i < 3
                           else (civ.age_bucket >= 3))
                if bm.sum() >= MIN_AGENTS:
                    bmasks[(cc, b)] = bm
        for held in [cc for cc in by_cc
                     if cc in cmasks and len(by_cc[cc]) == 4]:
            base_g, base_t = [], []
            for cc, t in ct.items():
                if cc == held or cc not in cmasks:
                    continue
                base_g.append(feats[cmasks[cc]].mean(axis=0))
                base_t.append(t)
            coh_g, coh_t = list(base_g), list(base_t)
            for (cc, b), bm in bmasks.items():
                if cc == held or cc not in by_cc or b not in by_cc[cc]:
                    continue
                coh_g.append(feats[bm].mean(axis=0))
                coh_t.append(by_cc[cc][b])
            for name, G, T in (("country_only", base_g, base_t),
                               ("with_cohorts", coh_g, coh_t)):
                if len(G) < 4:
                    continue
                X = np.array(G)
                y = np.array([logit(np.array([t]))[0] - bl for t in T])
                w = np.linalg.solve(X.T @ X + LAM * np.eye(n_feat), X.T @ y)
                r = res[name]
                if held in ct:
                    p = float(sigmoid(bl + feats[cmasks[held]] @ w).mean())
                    r["cty"].append(abs(p - ct[held]))
                eng = {b: float(sigmoid(bl + feats[bmasks[(held, b)]] @ w).mean())
                       for b in BUCKETS if (held, b) in bmasks}
                if len(eng) == 4:
                    for b in BUCKETS:
                        r["coh"].append(abs(eng[b] - by_cc[held][b]))
                    og = np.sign(by_cc[held]["18_29"] - by_cc[held]["60_plus"])
                    eg = np.sign(eng["18_29"] - eng["60_plus"])
                    if og != 0:
                        r["gn"] += 1
                        r["gh"] += int(og == eg)

    out = {"religiosity": has_rel, "pop": POP}
    for name, r in res.items():
        out[name] = {"country_mae": float(np.mean(r["cty"])),
                     "cohort_mae": float(np.mean(r["coh"])),
                     "gradient_acc": r["gh"] / r["gn"] if r["gn"] else None,
                     "n_gradient": r["gn"]}
        o = out[name]
        print(f"  {name:14s} country {o['country_mae']:.4f} | cohort "
              f"{o['cohort_mae']:.4f} | gradient {r['gh']}/{r['gn']}",
              flush=True)
    tag = "relig" if has_rel else "norelig"
    json.dump(out, open(f"data/c2_step4_{tag}.json", "w"), indent=1)
    print(f"C2-STEP4[{tag}]: cohort-MAE "
          f"{out['country_only']['cohort_mae']:.4f} -> "
          f"{out['with_cohorts']['cohort_mae']:.4f} | gradient "
          f"{out['country_only']['gradient_acc']:.2f} -> "
          f"{out['with_cohorts']['gradient_acc']:.2f}", flush=True)


if __name__ == "__main__":
    main()
