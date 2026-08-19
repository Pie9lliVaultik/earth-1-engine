"""0.4 paired within-country delta: err_legacy - err_living per
(country, question, cell), same folds, same seeds - country identity
cannot get credit. Positive mean = living helps. DEV ONLY."""
import csv, json, os, subprocess, sys, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from earth1.alive import birth_world, live_one_day
from earth1.benchmark import ISO3_TO_ISO2
from earth1.calibration import _build_features, living_features
from earth1.genesis import GENESIS_COUNTRY_CODES
from earth1.rng import logit, sigmoid

POP, SEED, DAYS, RIDGE, FOLDS = 200_000, 42, 60, 1.0, 5
CV_SEEDS = (42, 7, 13)
BUCKETS = {"18_29": (0,), "30_44": (1,), "45_59": (2,), "60_plus": (3, 4)}

w = birth_world(POP, SEED); rng = np.random.default_rng(SEED)
for _ in range(DAYS): live_one_day(w, rng)
civ = w.civ
X = {"legacy": _build_features(civ, extended=True),
     "living": living_features(w)}
c2i = {c: i for i, c in enumerate(GENESIS_COUNTRY_CODES)}
cells = []
truth = {}
for r in csv.DictReader(open(ROOT/"data/wvs_w7_cohort_by_country.csv")):
    ci = c2i.get(ISO3_TO_ISO2.get(r["country"]))
    if ci is None: continue
    m = (civ.country == ci) & np.isin(civ.age_bucket, BUCKETS[r["age_bucket"]])
    if m.sum() < 20: continue
    cells.append((r["qcode"], ci, r["age_bucket"],
                  float(r["yes_weighted"]),
                  {k: Xk[m].mean(axis=0) for k, Xk in X.items()}))

def preds(arm):
    out = {}
    qs = sorted({c[0] for c in cells}); cs = sorted({c[1] for c in cells})
    for seed in CV_SEEDS:
        order = np.random.default_rng(seed).permutation(len(cs))
        for f in range(FOLDS):
            test_c = {cs[i] for i in order[f::FOLDS]}
            for q in qs:
                tr = [(y, fe[arm]) for (qq, ci, b, y, fe) in cells
                      if qq == q and ci not in test_c]
                te = [(qq, ci, b, y, fe[arm]) for (qq, ci, b, y, fe)
                      in cells if qq == q and ci in test_c]
                if len(tr) < 30 or not te: continue
                Xt = np.array([f2 for _, f2 in tr])
                yt = logit(np.clip(np.array([y for y, _ in tr]), .02, .98))
                mu, sd = Xt.mean(0), Xt.std(0)+1e-9
                A = ((Xt-mu)/sd).T @ ((Xt-mu)/sd) + RIDGE*np.eye(Xt.shape[1])
                b0 = yt.mean()
                wgt = np.linalg.solve(A, ((Xt-mu)/sd).T @ (yt-b0))
                for (qq, ci, b, y, fe) in te:
                    p = float(sigmoid(b0 + ((fe-mu)/sd) @ wgt))
                    out.setdefault((seed, qq, ci, b), []).append((y, p))
    return out

pl, pv = preds("legacy"), preds("living")
deltas, per_seed = [], {}
for k in pl:
    if k in pv:
        y, a = pl[k][0]; _, b = pv[k][0]
        d = abs(y-a) - abs(y-b)          # >0: living closer
        deltas.append(d); per_seed.setdefault(k[0], []).append(d)
d = np.array(deltas)*100
seed_means = [float(np.mean(v))*100 for v in per_seed.values()]
res = {"paired_cells": len(d),
       "mean_delta_pp": round(float(d.mean()), 4),
       "median_delta_pp": round(float(np.median(d)), 4),
       "living_wins_pct": round(100*float((d > 0).mean()), 1),
       "seed_means_pp": [round(x, 4) for x in seed_means],
       "provenance": {"host": os.uname().nodename,
           "commit": subprocess.run(["git","rev-parse","HEAD"],
               capture_output=True,text=True,cwd=ROOT).stdout.strip(),
           "protocol": {"pop":POP,"seed":SEED,"days":DAYS,
                        "folds":FOLDS,"cv_seeds":list(CV_SEEDS)},
           "wall_clock": time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}}
(ROOT/"data/living_readout_paired_delta.json").write_text(
    json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
