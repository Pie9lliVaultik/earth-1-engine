"""A6 secular leg: development-driven value drift (fit + score + placebo).

Registered functional form (A6 + A6.1, data/g5_preregistration.json):
  drift_qc = beta_q . D_rate_c ,  D_rate = D / years_i * 7.0
  D_c = [dlog GDP pc PPP, d tertiary pp, d urban pp] over the country's
  OWN fieldwork interval (earth1/wvs_wave5.py alignment table).
  Sign-constrained: the Inglehart direction is IMPOSED per question
  (development up -> traditional-religious down, self-expression up);
  only magnitudes are fit. Betas fit on W5->W6 ONLY; scored on W6->W7
  with LOO-country (scoring country c uses betas fit without c).
  Placebo: shuffled-development (country D vectors permuted, fixed
  seed, same frozen pipeline). Sign accuracy REPORTED but CONTAMINATED
  (per-question W6->W7 directions were inspected before registration).

Outputs: data/secular_betas.json (frozen), data/secular_fit.json.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.wvs_paired import WVS_PAIRED
from earth1.wvs_wave5 import WAVE5, W5_YEARS, W6_YEARS, W7_YEARS

YEARS_REF = 7.0
LAMBDA_GRID = [0.1, 0.3, 1.0, 3.0, 10.0]
PLACEBO_SEED = 202608

# The Inglehart direction per question, AUTHORED FROM THEORY (frozen
# with the betas): +1 = development pushes the coded proportion UP
# (self-expression/secular-rational direction), -1 = down.
INGLEHART_SIGN = {
    "t_homosexuality": +1, "t_abortion": +1, "t_divorce": +1,
    "t_religion": -1, "t_trust": +1, "t_democracy": +1,
    "t_army_rule": -1, "t_life_sat": +1, "t_men_leaders": -1,
    "t_pride": -1, "t_two_parent": -1, "t_tech_good": +1,
    "t_death_penalty": -1, "t_environment": +1, "t_hard_work": -1,
}


def _wdi():
    return json.load(open("data/wdi_tide.json"))


def _val(series: dict, cc: str, year: int):
    """Value at year, else nearest within 3y, else None."""
    d = series.get(cc)
    if not d:
        return None
    for dy in (0, 1, -1, 2, -2, 3, -3):
        v = d.get(str(year + dy))
        if v is not None:
            return float(v)
    return None


def dev_vector(wdi, cc: str, y0: int, y1: int):
    """D_rate: per-7y development change [dlogGDP, dtertiary, durban]."""
    g0, g1 = _val(wdi["gdp_pcap_ppp"], cc, y0), _val(wdi["gdp_pcap_ppp"], cc, y1)
    t0, t1 = _val(wdi["tertiary_enroll"], cc, y0), _val(wdi["tertiary_enroll"], cc, y1)
    u0, u1 = _val(wdi["urban_share"], cc, y0), _val(wdi["urban_share"], cc, y1)
    if None in (g0, g1, t0, t1, u0, u1) or g0 <= 0 or g1 <= 0:
        return None
    years = max(1.0, float(y1 - y0))
    D = np.array([np.log(g1) - np.log(g0),
                  (t1 - t0) / 100.0,
                  (u1 - u0) / 100.0])
    return D / years * YEARS_REF


def _fit_beta(X: np.ndarray, y: np.ndarray, sign: int, lam: float):
    """Ridge with the sign constraint: beta = sign * b, b >= 0.
    Solve ridge on sign-flipped X, then clip negatives to zero
    (projected solution — the registered 'only magnitudes are fit')."""
    Xs = X * sign
    b = np.linalg.solve(Xs.T @ Xs + lam * np.eye(3), Xs.T @ y)
    return sign * np.maximum(b, 0.0)


def _lambda_by_training_loo(X, y, sign):
    best, err = LAMBDA_GRID[0], np.inf
    n = len(y)
    if n < 4:
        return 1.0
    for lam in LAMBDA_GRID:
        e = []
        for i in range(n):
            k = np.arange(n) != i
            beta = _fit_beta(X[k], y[k], sign, lam)
            e.append((y[i] - X[i] @ beta) ** 2)
        m = float(np.mean(e))
        if m < err:
            best, err = lam, m
    return best


def main() -> None:
    wdi = _wdi()
    rngp = np.random.default_rng(PLACEBO_SEED)

    # ---- training data: W5->W6 deltas + D_rate over W5->W6 interval
    train = {}   # qid -> (countries, X rows, y)
    for pq in WVS_PAIRED:
        w5 = WAVE5[pq.id]
        rows, ys, ccs = [], [], []
        for cc, v5 in w5.items():
            if cc not in pq.wave6 or cc not in W5_YEARS:
                continue
            D = dev_vector(wdi, cc, W5_YEARS[cc], W6_YEARS[cc])
            if D is None:
                continue
            rows.append(D)
            ys.append(pq.wave6[cc] - v5)
            ccs.append(cc)
        if len(ys) >= 6:
            train[pq.id] = (ccs, np.array(rows), np.array(ys))

    # placebo permutation of country identity (fixed, one draw,
    # applied to the SCORING-era D vectors)
    all_countries = sorted({c for pq in WVS_PAIRED
                            for c in pq.overlapping_countries})
    perm = dict(zip(all_countries,
                    rngp.permutation(np.array(all_countries))))

    betas, lambdas = {}, {}
    for qid, (ccs, X, y) in train.items():
        sign = INGLEHART_SIGN[qid]
        lam = _lambda_by_training_loo(X, y, sign)
        lambdas[qid] = lam
        betas[qid] = _fit_beta(X, y, sign, lam).tolist()

    # ---- score W6->W7, LOO-country (refit without the scored country)
    mae_e, mae_n, mae_p, signs_ok, n_sign = [], [], [], 0, 0
    per_q = {}
    for pq in WVS_PAIRED:
        if pq.id not in train:
            continue
        ccs, X, y = train[pq.id]
        sgn = INGLEHART_SIGN[pq.id]
        qe, qn = [], []
        for cc in pq.overlapping_countries:
            if cc not in W6_YEARS or cc not in W7_YEARS:
                continue
            obs = pq.wave7[cc] - pq.wave6[cc]
            D7 = dev_vector(wdi, cc, W6_YEARS[cc], W7_YEARS[cc])
            if D7 is None:
                continue
            # LOO: refit without cc if cc was in training
            if cc in ccs:
                k = np.array([c != cc for c in ccs])
                beta = _fit_beta(X[k], y[k], sgn, lambdas[pq.id])
            else:
                beta = np.array(betas[pq.id])
            yrs = max(1.0, float(W7_YEARS[cc] - W6_YEARS[cc]))
            pred = float(beta @ D7) * yrs / YEARS_REF
            # placebo: same beta, permuted country's development
            pcc = perm[cc]
            D7p = (dev_vector(wdi, pcc, W6_YEARS[cc], W7_YEARS[cc])
                   if pcc in W6_YEARS else None)
            predp = (float(beta @ D7p) * yrs / YEARS_REF
                     if D7p is not None else 0.0)
            mae_e.append(abs(pred - obs))
            mae_n.append(abs(obs))
            mae_p.append(abs(predp - obs))
            qe.append(abs(pred - obs)), qn.append(abs(obs))
            if abs(obs) >= 0.02:
                n_sign += 1
                if np.sign(pred) == np.sign(obs) and pred != 0:
                    signs_ok += 1
        if qe:
            per_q[pq.id] = {"mae_engine": float(np.mean(qe)),
                            "mae_nochange": float(np.mean(qn)),
                            "n": len(qe)}

    out_betas = {"registered_under": "A6+A6.1", "years_ref": YEARS_REF,
                 "inglehart_signs": INGLEHART_SIGN, "lambdas": lambdas,
                 "betas": betas,
                 "training": "W5->W6 only, 3y-nearest WDI matching",
                 "placebo_seed": PLACEBO_SEED}
    json.dump(out_betas, open("data/secular_betas.json", "w"), indent=1)

    res = {"n_pairs": len(mae_e),
           "mae_engine": float(np.mean(mae_e)),
           "mae_nochange": float(np.mean(mae_n)),
           "mae_placebo": float(np.mean(mae_p)),
           "sign_accuracy_CONTAMINATED": (signs_ok / n_sign
                                          if n_sign else None),
           "n_sign_pairs": n_sign,
           "per_question": per_q}
    json.dump(res, open("data/secular_fit.json", "w"), indent=1)
    beats_nochange = res["mae_engine"] < res["mae_nochange"]
    beats_placebo = res["mae_engine"] < res["mae_placebo"]
    print(f"SECULAR-VERDICT: engine {res['mae_engine']:.4f} vs "
          f"no-change {res['mae_nochange']:.4f} vs placebo "
          f"{res['mae_placebo']:.4f} | n={res['n_pairs']} | "
          f"sign(CONTAM) {res['sign_accuracy_CONTAMINATED']} | "
          f"beats no-change: {beats_nochange} | beats placebo: "
          f"{beats_placebo}", flush=True)


if __name__ == "__main__":
    main()
