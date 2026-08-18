"""T2 — MOVEMENT vs PERSISTENCE on 456 real GSS transitions.

Prereg: data/gss_ruler_prereg.json (four tests + scope caveat, both
registered before any run). Ruler: data/gss_truth.json — GSS
1972-2024 real weighted respondents, never used in any calibration.

The mechanism under test is the one Earth-1 has actually validated:
GENERATIONAL COMPOSITION. For each consecutive-year pair (Y1, Y2):

  1. fit the engine's weights to the OBSERVED Y1 cohort structure
     (age x education cells at Y1) — Y2 never enters the fit
  2. age the population forward by (Y2 - Y1) years with the
     generational tick (births at the young-cohort mean, aging along
     the trait gradients)
  3. read the new national share
  4. score the PREDICTED CHANGE against the OBSERVED CHANGE

Baselines:
  PERSISTENCE   predicted change = 0            (the honest null)
  DRIFT         predicted change = the variable's own historical mean
                annual drift, computed on OTHER year-pairs only
                (leave-one-transition-out — a hard, fair baseline)

Reported: movement MAE, sign accuracy, correlation with observed
change. Every number states its ruler.
Env: GM_POP (default 50000), GM_MAX_GAP (default 6 years).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.calibration import _build_features, _get_country_index
from earth1.generational import generational_tick
from earth1.genesis import genesis
from earth1.rng import logit, sigmoid
from earth1.tick import _make_mutable

POP = int(os.environ.get("GM_POP", "50000"))
MAX_GAP = int(os.environ.get("GM_MAX_GAP", "6"))
AGE_TAGS = ["18_29", "30_44", "45_59", "60_plus"]
MIN_AGENTS = 30
LAM = 1.0


def cell_masks(civ, us):
    out = {}
    for i, tag in enumerate(AGE_TAGS):
        for e in range(3):
            m = (us & (civ.education == e)
                 & ((civ.age_bucket == i) if i < 3 else (civ.age_bucket >= 3)))
            if m.sum() >= MIN_AGENTS:
                out[f"{tag}|{e}"] = m
    return out


def main() -> None:
    truth = json.load(open("data/gss_truth.json"))
    civ = _make_mutable(genesis(POP, 42))
    c2i, _ = _get_country_index(civ)
    us = civ.country == c2i["US"]
    feats = _build_features(civ, extended=True)
    masks = cell_masks(civ, us)
    print(f"US agents {int(us.sum()):,} in {len(masks)} cohort cells",
          flush=True)

    rows = []
    for var, rec in truth.items():
        years = sorted(int(y) for y in rec["national"])
        cells = rec["cells"]
        # historical mean annual drift, for the DRIFT baseline
        for a, b in zip(years, years[1:]):
            gap = b - a
            if gap < 1 or gap > MAX_GAP:
                continue
            y1 = rec["national"][str(a)]["share"]
            y2 = rec["national"][str(b)]["share"]
            # fit weights on Y1 cohort cells only
            X, yv = [], []
            for key, m in masks.items():
                tag, e = key.split("|")
                ck = f"{a}|{tag}|{e}"
                if ck in cells:
                    X.append(feats[m].mean(axis=0))
                    yv.append(cells[ck]["share"])
            if len(yv) < 6:
                continue
            bl = logit(np.array([y1]))[0]
            X = np.array(X)
            yy = np.array([logit(np.array([v]))[0] - bl for v in yv])
            w = np.linalg.solve(X.T @ X + LAM * np.eye(X.shape[1]), X.T @ yy)
            pred_y1 = float(sigmoid(bl + feats[us] @ w).mean())
            # age the population forward by the gap
            civ2 = _make_mutable(genesis(POP, 42))
            rng = np.random.default_rng(42)
            for _ in range(int(gap) * 4):
                generational_tick(civ2, rng, dt_days=91.3)
            f2 = _build_features(civ2, extended=True)
            us2 = civ2.country == c2i["US"]
            pred_y2 = float(sigmoid(bl + f2[us2] @ w).mean())
            rows.append({"var": var, "y1": a, "y2": b, "gap": gap,
                         "obs_change": y2 - y1,
                         "eng_change": pred_y2 - pred_y1})
        # leave-one-out drift baseline per variable
    obs = np.array([r["obs_change"] for r in rows])
    eng = np.array([r["eng_change"] for r in rows])
    drift = []
    for i, r in enumerate(rows):
        same = [x for j, x in enumerate(rows)
                if x["var"] == r["var"] and j != i]
        rate = (np.mean([x["obs_change"] / x["gap"] for x in same])
                if same else 0.0)
        drift.append(rate * r["gap"])
    drift = np.array(drift)

    out = {"ruler": "GSS 1972-2024 verified microdata (US only — grades "
                    "MECHANISM, not scope)",
           "pop": POP, "n_transitions": len(rows),
           "persistence_mae": float(np.abs(obs).mean()),
           "engine_mae": float(np.abs(eng - obs).mean()),
           "drift_baseline_mae": float(np.abs(drift - obs).mean()),
           "engine_sign_acc": float(np.mean(np.sign(eng) == np.sign(obs))),
           "drift_sign_acc": float(np.mean(np.sign(drift) == np.sign(obs))),
           "engine_corr": float(np.corrcoef(eng, obs)[0, 1]),
           "drift_corr": float(np.corrcoef(drift, obs)[0, 1]),
           "mean_abs_observed_change": float(np.abs(obs).mean())}
    json.dump(out, open("data/gss_movement_test.json", "w"), indent=1)
    print(f"  transitions scored: {out['n_transitions']}", flush=True)
    print(f"  PERSISTENCE   MAE {out['persistence_mae']:.4f}", flush=True)
    print(f"  ENGINE        MAE {out['engine_mae']:.4f} | sign "
          f"{out['engine_sign_acc']:.2f} | corr {out['engine_corr']:+.3f}",
          flush=True)
    print(f"  DRIFT (LOO)   MAE {out['drift_baseline_mae']:.4f} | sign "
          f"{out['drift_sign_acc']:.2f} | corr {out['drift_corr']:+.3f}",
          flush=True)
    d = 100 * (out["persistence_mae"] - out["engine_mae"])
    print(f"GSS-T2-VERDICT: engine vs persistence {d:+.2f}pp "
          f"[VERIFIED RULER, US-only: grades mechanism not scope]",
          flush=True)


if __name__ == "__main__":
    main()
