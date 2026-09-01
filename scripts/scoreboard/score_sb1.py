"""SB1 scorer: country-level MAE on never-calibrated estates.

Estates: goqa_dev (GAS/Pew-frame, concordance targets), wvs_heldout
(national values reconstructed n-weighted from confirm_targets_v2
cohorts). Per item, leave-one-country-out. Predictors:
  earth1   ridge on 200k candidate-world living-feature country means
  mrsp     ridge on census covariates only (med_age, urban, income
           one-hot, le, tfr) — census-covariate MRP, registered tonight
  naive    train-country grand mean
  region   mean of same-region train countries (census 'region' field)
Seeds: features_{4242,5151,6363}. Outputs per-estate JSON.
"""
import json
import os
import sys
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from earth1.genesis import GENESIS_COUNTRIES  # noqa: E402

SEEDS = (4242, 5151, 6363)
CINFO = {c['iso2']: c for c in GENESIS_COUNTRIES}
INC = {"HIC": 0, "UMIC": 1, "LMIC": 2, "LIC": 3}


def census_vec(iso2):
    c = CINFO[iso2]
    one = [0.0] * 4
    one[INC.get(c['income'], 2)] = 1.0
    return [c['med_age'], c['urban'], c['le'], c['tfr']] + one


def load_estate(name):
    if name == 'goqa_dev':
        items = json.load(open(os.path.join(
            ROOT, 'data/concordance/goqa_dev.json')))['items']
        return {it['qid']: it['targets'] for it in items}, \
               {it['qid']: it['question'] for it in items}
    if name in ('wvs_heldout', 'wvs_extended'):
        # wvs_extended: the 131 unlabeled substantive-core items registered
        # 2026-09-01 (build_confirm_v3.py) — same rules, same reconstruction
        # as wvs_heldout, provably unspent by TRAIN (never labeled).
        fn = ('confirm_targets_v2.json' if name == 'wvs_heldout'
              else 'confirm_targets_v3.json')
        ct = json.load(open(os.path.join(ROOT, 'data/benchmark_a', fn)))
        out, txt = {}, {}
        for item, cc in ct['cohorts'].items():
            t = {}
            for c2, bands in cc.items():
                n = sum(b['n'] for b in bands.values())
                t[c2] = round(sum(b['yes'] * b['n']
                                  for b in bands.values()) / n, 6)
            out[item] = t
            txt[item] = ct['items'][item]['text']
        return out, txt
    raise ValueError(name)


def loo_ridge(X, y, grp, lam=1.0):
    mu, sd = X.mean(0), np.maximum(X.std(0), 1e-9)
    Z = (X - mu) / sd
    la = np.log(np.clip(y, 1e-3, 1 - 1e-3) / (1 - np.clip(y, 1e-3, 1 - 1e-3)))
    pred = np.zeros(len(y))
    for g in np.unique(grp):
        te, tr = grp == g, grp != g
        A = Z[tr].T @ Z[tr] + lam * np.eye(Z.shape[1])
        b = np.linalg.solve(A, Z[tr].T @ (la[tr] - la[tr].mean()))
        pred[te] = 1 / (1 + np.exp(-(Z[te] @ b + la[tr].mean())))
    return pred


def family(text):
    import re
    t = text.lower()
    for fam, pat in (("democracy/governance", r"democr|elect|vote|govern|leader|corrupt"),
                     ("economy", r"econom|job|income|financ|trade|poverty"),
                     ("intl-relations", r"united states|china|russia|european union|nato|influence|foreign"),
                     ("religion/values", r"relig|god|moral|abortion|homosex|marriage|gender|women"),
                     ("tech/climate", r"climate|environment|internet|technolog|science"),
                     ("security", r"terror|military|war|crime|police")):
        if re.search(pat, t):
            return fam
    return "other"


def main(estates):
    fdir = os.environ.get('SB1_FEATURES_DIR', os.path.join(ROOT, 'data/cycles'))
    sfx = os.environ.get('SB1_OUT_SUFFIX', '')
    feats = {s: json.load(open(os.path.join(
        fdir, f'features_{s}.json'))) for s in SEEDS}
    for estate in estates:
        targets, texts = load_estate(estate)
        per_seed = {m: [] for m in ("earth1", "mrsp", "naive", "region")}
        cells = defaultdict(list)   # (family, region, income) -> errors
        worst = []
        for s in SEEDS:
            F = feats[s]
            errs = {m: [] for m in per_seed}
            for item, t in targets.items():
                iso = sorted(set(t) & set(F) & set(CINFO))
                if len(iso) < 8:
                    continue
                y = np.array([t[c] for c in iso])
                grp = np.arange(len(iso))
                Xe = np.array([F[c]['f'] for c in iso])
                Xm = np.array([census_vec(c) for c in iso])
                pe = loo_ridge(Xe, y, grp)
                pm = loo_ridge(Xm, y, grp)
                reg = np.array([CINFO[c]['region'] for c in iso])
                for k, c in enumerate(iso):
                    tr = grp != k
                    naive = y[tr].mean()
                    same = tr & (reg == reg[k])
                    regcp = y[same].mean() if same.any() else naive
                    errs["earth1"].append(abs(pe[k] - y[k]))
                    errs["mrsp"].append(abs(pm[k] - y[k]))
                    errs["naive"].append(abs(naive - y[k]))
                    errs["region"].append(abs(regcp - y[k]))
                    if s == SEEDS[0]:
                        fam = family(texts[item])
                        cells[(fam, CINFO[c]['region'],
                               CINFO[c]['income'])].append(abs(pe[k] - y[k]))
                        worst.append((abs(pe[k] - y[k]), c, item, fam))
            for m in per_seed:
                per_seed[m].append(float(np.mean(errs[m]) * 100))
        res = {m: {"mae_pp": round(float(np.mean(v)), 3),
                   "seed_sigma": round(float(np.std(v, ddof=1)), 3)}
               for m, v in per_seed.items()}
        e1 = res['earth1']['mae_pp']
        res['excess_vs_mrsp'] = round(e1 - res['mrsp']['mae_pp'], 3)
        res['tier'] = ("WIN" if e1 <= 3.5 else "GOOD" if e1 <= 5.0
                       else "ACCEPT" if e1 <= 7.0 else "MISS")
        res['beats_naive'] = bool(e1 < res['naive']['mae_pp'])
        res['n_items_scored'] = len({w[2] for w in worst})
        worst.sort(reverse=True)
        res['worst5'] = [{"err_pp": round(w[0] * 100, 1), "country": w[1],
                          "family": w[3]} for w in worst[:5]]
        res['best5'] = [{"err_pp": round(w[0] * 100, 2), "country": w[1],
                         "family": w[3]} for w in worst[-5:]]
        agg = sorted(((np.mean(v) * 100 * len(v), k, len(v))
                      for k, v in cells.items()), reverse=True)
        res['top3_error_cells'] = [
            {"family": k[0], "region": k[1], "income": k[2],
             "share_weighted_mae": round(s_, 1), "n": n}
            for s_, k, n in agg[:3]]
        json.dump(res, open(os.path.join(
            ROOT, f'data/cycles/sb1_{estate}{sfx}.json'), 'w'), indent=1)
        print(estate, json.dumps({k: res[k] for k in
                                  ("earth1", "mrsp", "naive", "region",
                                   "excess_vs_mrsp", "tier",
                                   "beats_naive", "n_items_scored")}))


if __name__ == "__main__":
    main(sys.argv[1:] or ["goqa_dev", "wvs_heldout"])
