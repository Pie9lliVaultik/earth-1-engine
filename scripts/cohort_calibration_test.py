"""RIGHT-NUMBERS TEST: does calibrating on real cohort cells fix the
engine's cohort structure — without breaking the country headline?

Same ridge estimator as production, richer fitting targets: country
means (GOQA) PLUS within-country age-bucket cells (official microdata,
data/wvs_w7_cohort_by_country.csv). Held-out scoring: LOO-country on
BOTH metrics (country MAE + cohort bucket MAE + gradient direction).

Compare: country-only calibration (status quo) vs country+cohort
calibration. If cohort MAE collapses and country MAE holds, this is
the first measured IMPROVEMENT of the distribution era.
Env: CCT_POP (default 200000).
"""
from __future__ import annotations

import csv
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.benchmark_questions import ISO3_TO_ISO2
from earth1.calibration import _build_features, _get_country_index
from earth1.genesis import genesis
from earth1.rng import logit, sigmoid
from earth1.types import Question  # noqa: F401 (parity with prod imports)

POP = int(os.environ.get("CCT_POP", "200000"))
BUCKETS = ["18_29", "30_44", "45_59", "60_plus"]
MIN_AGENTS = 30
LAM = 0.1  # production ridge strength


def fit(groups, targets, bl, n_feat, lam=LAM):
    X = np.array([g for g in groups])
    y = np.array([logit(np.array([t]))[0] - bl for t in targets])
    return np.linalg.solve(X.T @ X + lam * np.eye(n_feat), X.T @ y)


def main() -> None:
    civ = genesis(POP, 42)
    code_to_idx, _ = _get_country_index(civ)
    feats = _build_features(civ, extended=True)
    n_feat = feats.shape[1]
    gt = {q["id"]: q for q in
          json.load(open("data/benchmark/goqa_ground_truth.json"))}
    cells = {}
    for r in csv.DictReader(open("data/wvs_w7_cohort_by_country.csv")):
        iso2 = ISO3_TO_ISO2.get(r["country"])
        if iso2:
            cells.setdefault(r["qcode"], {}).setdefault(
                iso2, {})[r["age_bucket"]] = float(r["yes_weighted"])

    def group_mean(mask):
        return feats[mask].mean(axis=0) if mask.sum() >= MIN_AGENTS else None

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
        # precompute masks
        cmasks = {cc: civ.country == code_to_idx[cc]
                  for cc in set(list(ct) + list(by_cc)) if cc in code_to_idx}
        bmasks = {}
        for cc, cm in cmasks.items():
            for i, b in enumerate(BUCKETS):
                bm = cm & ((civ.age_bucket == i) if i < 3
                           else (civ.age_bucket >= 3))
                if bm.sum() >= MIN_AGENTS:
                    bmasks[(cc, b)] = bm
        # LOO over countries that have cohort truth
        for held in [cc for cc in by_cc if cc in cmasks
                     and len(by_cc[cc]) == 4]:
            # training targets
            tr_groups, tr_targets = [], []
            for cc, t in ct.items():
                if cc == held or cc not in cmasks:
                    continue
                gm = group_mean(cmasks[cc])
                if gm is not None:
                    tr_groups.append(gm), tr_targets.append(t)
            cty_groups = list(tr_groups)
            cty_targets = list(tr_targets)
            coh_groups = list(tr_groups)
            coh_targets = list(tr_targets)
            for (cc, b), bm in bmasks.items():
                if cc == held or cc not in by_cc or b not in by_cc[cc]:
                    continue
                coh_groups.append(group_mean(bm))
                coh_targets.append(by_cc[cc][b])
            for name, G, T in (("country_only", cty_groups, cty_targets),
                               ("with_cohorts", coh_groups, coh_targets)):
                if len(G) < 4:
                    continue
                w = fit(G, T, bl, n_feat)
                r = res[name]
                # held-out country-level
                p_cty = float(sigmoid(bl + feats[cmasks[held]] @ w).mean())
                if held in ct:
                    r["cty"].append(abs(p_cty - ct[held]))
                # held-out cohort-level
                eng = {}
                for b in BUCKETS:
                    if (held, b) in bmasks:
                        eng[b] = float(sigmoid(
                            bl + feats[bmasks[(held, b)]] @ w).mean())
                if len(eng) == 4:
                    for b in BUCKETS:
                        r["coh"].append(abs(eng[b] - by_cc[held][b]))
                    og = np.sign(by_cc[held]["18_29"] - by_cc[held]["60_plus"])
                    eg = np.sign(eng["18_29"] - eng["60_plus"])
                    if og != 0:
                        r["gn"] += 1
                        r["gh"] += int(og == eg)

    out = {}
    for name, r in res.items():
        out[name] = {"country_mae": float(np.mean(r["cty"])),
                     "cohort_mae": float(np.mean(r["coh"])),
                     "gradient_acc": r["gh"] / r["gn"] if r["gn"] else None,
                     "n_gradient": r["gn"]}
        o = out[name]
        print(f"{name:14s} country-MAE {o['country_mae']:.4f} | "
              f"cohort-MAE {o['cohort_mae']:.4f} | gradient "
              f"{r['gh']}/{r['gn']}", flush=True)
    json.dump(out, open("data/cohort_calibration_test.json", "w"), indent=1)
    d = (out["country_only"]["cohort_mae"]
         - out["with_cohorts"]["cohort_mae"]) * 100
    print(f"RIGHT-NUMBERS-VERDICT: cohort-MAE improvement {d:+.2f}pp "
          f"from cohort-informed calibration", flush=True)


if __name__ == "__main__":
    main()
