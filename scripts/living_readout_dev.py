"""0.4 DEVELOPMENT DIAGNOSTIC — legacy readout vs living-state readout.

DEV ONLY. This is not Benchmark A, touches no holdout, and moves no
acceptance threshold. The question it answers: does the living-state
readout expose genuine within-country structure, and does the added
lived state carry measurable signal on the existing clean development
instrument?

Protocol (the pinned one, data/cv_folds.json): pop 200,000, genesis
seed 42, 5-fold CV over the GOQA countries, 3 CV seeds, ridge in logit
space on country-aggregated features. Arms share folds, seeds, targets
and aggregation — they differ ONLY in the feature matrix:

  naive    grand-mean baseline (must be beatable, or nothing means much)
  legacy   _build_features(civ, extended=True)      (18 static features)
  living   living_features(w)                       (+8 lived channels)

Plus per-family ablations of the living block and a within-country
variance decomposition. Every result JSON stamps host, commit, seed and
wall-clock (Standing Rule 10).
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from earth1.alive import CANONICAL_DAY, birth_world, live_one_day
from earth1.benchmark import ISO3_TO_ISO2
from earth1.calibration import (LIVING_FEATURES, _build_features,
                                living_features)
from earth1.genesis import GENESIS_COUNTRY_CODES
from earth1.rng import logit, sigmoid

POP = 200_000
SEED = 42
DAYS = 60                 # lived state needs a lived-in world
RIDGE = 1.0
FOLDS = 5
CV_SEEDS = (42, 7, 13)

FAMILIES = {
    "material": ["deprivation", "unemployed", "spells"],
    "body_mind": ["hunger", "mental", "addiction"],
    "social": ["relationship"],
    "flourishing": ["hope"],
}


def country_matrix(X, civ, weights=None):
    """Population-mean feature vector per country index."""
    nc = len(GENESIS_COUNTRY_CODES)
    out = np.zeros((nc, X.shape[1]))
    for c in range(nc):
        m = civ.country == c
        if m.any():
            out[c] = X[m].mean(axis=0)
    return out


def ridge_cv(Xc, y, folds, seeds, lam=RIDGE):
    """Held-out predictions via ridge in logit space, pinned protocol."""
    preds = np.zeros_like(y)
    counts = np.zeros_like(y)
    n = len(y)
    ylog = logit(np.clip(y, 0.02, 0.98))
    for seed in seeds:
        rs = np.random.default_rng(seed)
        order = rs.permutation(n)
        for f in range(folds):
            test = order[f::folds]
            train = np.setdiff1d(order, test)
            Xt = Xc[train]
            mu, sd = Xt.mean(0), Xt.std(0) + 1e-9
            Zt = (Xt - mu) / sd
            Zs = (Xc[test] - mu) / sd
            b0 = ylog[train].mean()
            A = Zt.T @ Zt + lam * np.eye(Zt.shape[1])
            w = np.linalg.solve(A, Zt.T @ (ylog[train] - b0))
            preds[test] += sigmoid(b0 + Zs @ w)
            counts[test] += 1
    return preds / np.maximum(counts, 1)


def evaluate(Xc, questions, label):
    maes, cals = [], []
    for q in questions:
        idx, y = q["idx"], q["y"]
        p = ridge_cv(Xc[idx], y, FOLDS, CV_SEEDS)
        maes.append(float(np.abs(p - y).mean()) * 100)
        if np.std(p) > 1e-9:
            cals.append(float(np.polyfit(p, y, 1)[0]))
    return {"arm": label,
            "national_mae_pp": round(float(np.mean(maes)), 3),
            "mae_per_question_sd": round(float(np.std(maes)), 3),
            "calibration_slope": round(float(np.mean(cals)), 3)}


def main():
    t0 = time.time()
    print(f"  birthing {POP:,} @ seed {SEED}", flush=True)
    w = birth_world(POP, SEED)
    rng = np.random.default_rng(SEED)
    print(f"  living {DAYS} canonical days", flush=True)
    for d in range(DAYS):
        live_one_day(w, rng)
        if (d + 1) % 20 == 0:
            print(f"    day {d+1}", flush=True)

    civ = w.civ
    X_legacy = _build_features(civ, extended=True)
    X_living = living_features(w)
    n_static = X_legacy.shape[1]
    print(f"  features: legacy {X_legacy.shape}, living {X_living.shape}",
          flush=True)

    # GOQA targets onto genesis country indices
    code_to_idx = {c: i for i, c in enumerate(GENESIS_COUNTRY_CODES)}
    goqa = json.load(open(ROOT / "data/benchmark/goqa_ground_truth.json"))
    questions = []
    for q in goqa:
        idx, y = [], []
        for iso3, v in q["countries"].items():
            iso2 = ISO3_TO_ISO2.get(iso3)
            ci = code_to_idx.get(iso2)
            if ci is not None and (civ.country == ci).sum() >= 50:
                idx.append(ci)
                y.append(v["yes"])
        if len(idx) >= 40:
            questions.append({"id": q["id"], "idx": np.array(idx),
                              "y": np.array(y)})
    print(f"  {len(questions)} questions usable", flush=True)

    Cleg = country_matrix(X_legacy, civ)
    Cliv = country_matrix(X_living, civ)

    # naive = intercept-only: zero features (the beatable floor)
    naive = evaluate(np.zeros((Cleg.shape[0], 1)), questions, "naive")
    legacy = evaluate(Cleg, questions, "legacy_18")
    living = evaluate(Cliv, questions, "living_26")

    # ablations: drop each living family
    names_liv = list(LIVING_FEATURES)
    ablations = {}
    for fam, members in FAMILIES.items():
        keep = [j for j, nm in enumerate(names_liv) if nm not in members]
        Xa = np.hstack([Cliv[:, :n_static],
                        Cliv[:, n_static:][:, keep]])
        ablations[fam] = evaluate(Xa, questions, f"living_minus_{fam}")

    # within-country variance carried by the living block (agent level)
    wv = {}
    Xl = X_living[:, n_static:]
    for j, nm in enumerate(names_liv):
        col = Xl[:, j]
        gm = col.mean()
        cm = np.zeros_like(col)
        for c in np.unique(civ.country):
            m = civ.country == c
            cm[m] = col[m].mean()
        ss_within = float(((col - cm) ** 2).sum())
        ss_total = float(((col - gm) ** 2).sum()) or 1.0
        wv[nm] = round(ss_within / ss_total, 3)

    out = {
        "diagnostic": "0.4 dev-only: legacy vs living readout",
        "NOT_BENCHMARK_A": True,
        "holdout_touched": False,
        "protocol": {"pop": POP, "seed": SEED, "days_lived": DAYS,
                     "folds": FOLDS, "cv_seeds": list(CV_SEEDS),
                     "ridge_lambda": RIDGE,
                     "questions": len(questions)},
        "arms": {"naive": naive, "legacy": legacy, "living": living},
        "ablations": ablations,
        "within_country_variance_share": wv,
        "provenance": {
            "host": os.uname().nodename,
            "commit": subprocess.run(["git", "rev-parse", "HEAD"],
                                     capture_output=True, text=True,
                                     cwd=ROOT).stdout.strip(),
            "wall_clock": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                        time.gmtime()),
            "runtime_s": round(time.time() - t0, 1)},
    }
    dest = ROOT / "data" / "living_readout_dev.json"
    dest.write_text(json.dumps(out, indent=1))
    print(json.dumps({"naive": naive, "legacy": legacy, "living": living},
                     indent=1))
    print("ablations:", {k: v["national_mae_pp"]
                         for k, v in ablations.items()})
    print(f"written {dest}")


if __name__ == "__main__":
    main()
