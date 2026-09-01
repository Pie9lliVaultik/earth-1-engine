"""Per-item benchmark report (founder order 2026-09-01: "question by
question — where we win, where we lose").

Reuses score_sb1's exact estate loaders and LOO computation so every
item row reconciles with the committed aggregate MAEs. For each item:
Earth-1 (mean over the 3 feature seeds), MrsP, naive, region-copy MAEs,
win/loss flags, and the per-country signed Earth-1 errors (seed-mean)
for drill-down.

usage: sb1_item_report.py [estate ...]   (default: all three)
writes data/cycles/sb1_items_<estate>.json + .csv
"""
import csv
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from score_sb1 import CINFO, SEEDS, census_vec, family, load_estate, loo_ridge  # noqa: E402


def main(estates):
    feats = {s: json.load(open(os.path.join(
        ROOT, f'data/cycles/features_{s}.json'))) for s in SEEDS}
    for estate in estates:
        targets, texts = load_estate(estate)
        rows = []
        for item, t in sorted(targets.items()):
            iso = sorted(set(t) & set(feats[SEEDS[0]]) & set(CINFO))
            if len(iso) < 8:
                continue
            y = np.array([t[c] for c in iso])
            grp = np.arange(len(iso))
            Xm = np.array([census_vec(c) for c in iso])
            pm = loo_ridge(Xm, y, grp)
            reg = np.array([CINFO[c]['region'] for c in iso])
            naive_err, region_err = [], []
            for k in range(len(iso)):
                tr = grp != k
                naive_err.append(abs(y[tr].mean() - y[k]))
                same = tr & (reg == reg[k])
                region_err.append(abs((y[same].mean() if same.any()
                                       else y[tr].mean()) - y[k]))
            e1_err = np.zeros(len(iso))
            e1_pred = np.zeros(len(iso))
            for s in SEEDS:
                F = feats[s]
                Xe = np.array([F[c]['f'] for c in iso])
                pe = loo_ridge(Xe, y, grp)
                e1_err += np.abs(pe - y)
                e1_pred += pe
            e1_err /= len(SEEDS)
            e1_pred /= len(SEEDS)
            e1 = float(e1_err.mean() * 100)
            mrsp = float(np.abs(pm - y).mean() * 100)
            nav = float(np.mean(naive_err) * 100)
            regcp = float(np.mean(region_err) * 100)
            best = min(("earth1", e1), ("mrsp", mrsp), ("naive", nav),
                       ("region", regcp), key=lambda kv: kv[1])[0]
            rows.append({
                "item": item, "text": texts[item],
                "family": family(texts[item]), "n_countries": len(iso),
                "earth1_mae_pp": round(e1, 2), "mrsp_mae_pp": round(mrsp, 2),
                "naive_mae_pp": round(nav, 2), "region_mae_pp": round(regcp, 2),
                "best": best,
                "e1_minus_region_pp": round(e1 - regcp, 2),
                "e1_minus_mrsp_pp": round(e1 - mrsp, 2),
                "beats_region": bool(e1 < regcp),
                "beats_mrsp": bool(e1 < mrsp),
                "beats_all": bool(best == "earth1"),
                "country_truth": {c: round(float(y[k]), 4)
                                  for k, c in enumerate(iso)},
                "country_e1_signed_err_pp": {
                    c: round(float((e1_pred[k] - y[k]) * 100), 1)
                    for k, c in enumerate(iso)},
            })
        wins_r = sum(r["beats_region"] for r in rows)
        wins_a = sum(r["beats_all"] for r in rows)
        out = {"estate": estate, "n_items": len(rows),
               "earth1_beats_region": wins_r,
               "earth1_beats_mrsp": sum(r["beats_mrsp"] for r in rows),
               "earth1_best_of_all": wins_a,
               "items": rows}
        jp = os.path.join(ROOT, f'data/cycles/sb1_items_{estate}.json')
        json.dump(out, open(jp, 'w'), indent=1)
        cp = os.path.join(ROOT, f'data/cycles/sb1_items_{estate}.csv')
        cols = ["item", "family", "n_countries", "earth1_mae_pp",
                "mrsp_mae_pp", "naive_mae_pp", "region_mae_pp", "best",
                "e1_minus_region_pp", "beats_region", "beats_all", "text"]
        with open(cp, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
            w.writeheader()
            w.writerows(rows)
        print(estate, len(rows), "items | beats region-copy:", wins_r,
              "| best-of-all:", wins_a, "->", jp)


if __name__ == "__main__":
    main(sys.argv[1:] or ["wvs_heldout", "wvs_extended", "goqa_dev"])
