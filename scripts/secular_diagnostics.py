"""DIAGNOSTICS for the A6 negative (2026-08-18). Investigation only —
no criterion changes, nothing here re-scores the registered verdict.

Questions:
 D1 coverage      — which countries/pairs dropped, are WDI values sane?
 D2 magnitudes    — do predictions move at all vs observed deltas?
 D3 zero-betas    — how many questions were clipped to zero by the sign
                    constraint (training data fighting Inglehart)?
 D4 global-drift  — is the dev term acting as a per-question constant
                    (everyone grows) rather than differentiating
                    countries? Compare vs a global-mean-drift baseline.
 D5 sign flip     — unconstrained ridge (diagnostic): does the data
                    want the OPPOSITE of the Inglehart signs?
 D6 trend check   — do (estimated) W5->W6 deltas correlate with
                    observed W6->W7 deltas at all? If ~0, the training
                    era itself carries no signal (data-quality prime
                    suspect).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.wvs_paired import WVS_PAIRED
from earth1.wvs_wave5 import WAVE5, W5_YEARS, W6_YEARS, W7_YEARS
from scripts.fit_secular import (dev_vector, _wdi, _fit_beta,
                                 INGLEHART_SIGN, YEARS_REF)


def main() -> None:
    wdi = _wdi()

    # D1 — coverage + sanity
    dropped = []
    sane = {}
    for cc in sorted(W6_YEARS):
        D = dev_vector(wdi, cc, W6_YEARS[cc], W7_YEARS.get(cc, W6_YEARS[cc] + 7))
        if D is None:
            dropped.append(cc)
        else:
            sane[cc] = [round(float(x), 4) for x in D]
    print(f"D1 coverage: {len(sane)}/{len(W6_YEARS)} countries have W6->W7 "
          f"dev vectors; dropped: {dropped}")
    for cc in ("US", "IN", "NG", "DE"):
        print(f"   {cc}: D_rate(W6->W7) = {sane.get(cc)}")

    # D2/D4/D6 — magnitudes, global drift, trend correlation
    preds, obss, w56, w67 = [], [], [], []
    betas = json.load(open("data/secular_betas.json"))["betas"]
    for pq in WVS_PAIRED:
        if pq.id not in betas:
            continue
        b = np.array(betas[pq.id])
        for cc in pq.overlapping_countries:
            if cc not in W6_YEARS or cc not in W7_YEARS:
                continue
            D7 = dev_vector(wdi, cc, W6_YEARS[cc], W7_YEARS[cc])
            if D7 is None:
                continue
            yrs = max(1.0, float(W7_YEARS[cc] - W6_YEARS[cc]))
            preds.append(float(b @ D7) * yrs / YEARS_REF)
            obss.append(pq.wave7[cc] - pq.wave6[cc])
            if cc in WAVE5.get(pq.id, {}):
                w56.append(pq.wave6[cc] - WAVE5[pq.id][cc])
                w67.append(pq.wave7[cc] - pq.wave6[cc])
    preds, obss = np.array(preds), np.array(obss)
    print(f"D2 magnitudes: mean|pred| {np.abs(preds).mean():.4f} vs "
          f"mean|obs| {np.abs(obss).mean():.4f} | "
          f"corr(pred,obs) {np.corrcoef(preds, obss)[0,1]:.3f}")

    # D3 — zero-clipped questions
    nz = {q: int(np.count_nonzero(b)) for q, b in betas.items()}
    zeroed = [q for q, k in nz.items() if k == 0]
    print(f"D3 sign-clipped-to-zero questions: {len(zeroed)}/{len(betas)} "
          f"{zeroed}")

    # D4 — global-drift baseline: per-question constant = training mean
    mae_gd, mae_nc = [], []
    for pq in WVS_PAIRED:
        if pq.id not in WAVE5:
            continue
        tr = [pq.wave6[c] - WAVE5[pq.id][c] for c in WAVE5[pq.id]
              if c in pq.wave6]
        if not tr:
            continue
        gd = float(np.mean(tr))  # W5->W6 global mean drift, per 7y-ish
        for cc in pq.overlapping_countries:
            obs = pq.wave7[cc] - pq.wave6[cc]
            mae_gd.append(abs(gd - obs))
            mae_nc.append(abs(obs))
    print(f"D4 global-drift baseline (train-mean constant/question): "
          f"MAE {np.mean(mae_gd):.4f} vs no-change {np.mean(mae_nc):.4f}")

    # D5 — unconstrained ridge (DIAGNOSTIC): where does the data point?
    flips = []
    for pq in WVS_PAIRED:
        if pq.id not in WAVE5:
            continue
        rows, ys = [], []
        for cc, v5 in WAVE5[pq.id].items():
            if cc not in pq.wave6 or cc not in W5_YEARS:
                continue
            D = dev_vector(wdi, cc, W5_YEARS[cc], W6_YEARS[cc])
            if D is None:
                continue
            rows.append(D), ys.append(pq.wave6[cc] - v5)
        if len(ys) < 6:
            continue
        X, y = np.array(rows), np.array(ys)
        bu = np.linalg.solve(X.T @ X + 1.0 * np.eye(3), X.T @ y)
        dom = int(np.argmax(np.abs(bu)))
        want = np.sign(bu[dom])
        if want != 0 and want != INGLEHART_SIGN[pq.id]:
            flips.append(pq.id)
    print(f"D5 unconstrained fit disagrees with Inglehart sign on: "
          f"{len(flips)} questions {flips}")

    # D6 — does the training era predict the scoring era at all?
    w56, w67 = np.array(w56), np.array(w67)
    print(f"D6 trend: corr(W5->W6 est. delta, W6->W7 obs delta) = "
          f"{np.corrcoef(w56, w67)[0,1]:.3f} over {len(w56)} pairs")
    print("DIAGNOSTICS-DONE")


if __name__ == "__main__":
    main()
