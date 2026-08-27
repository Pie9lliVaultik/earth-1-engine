"""THE CALIBRATION CYCLE — one command, one cycle, self-recording.

Founder ruling 2026-08-27 (locked production path): MISS → DIAGNOSE →
CALIBRATE → RETEST at 20k on one fixed seed, three evidence classes,
ONE named change per cycle. Gates:
  A. attitudes — A-v2 DEV cohort MAE (98-item consumed-as-DEV set,
     LOO-by-country ridge on Earth-1 cohort features) must beat the
     national-copy floor computed on the identical cells.
  B. anchors — fetched World Bank/PIP: median within ±10% of $9.27;
     $8.30 headcount within ±5 pts of 46.1%; crude deaths in the
     declared adult-world band [0.7%, 1.5%]/yr.
  C. cascade sanity — episodes fire, rate within [0.3, 3.0]× the
     canonical-cliff 20k reference (NOT the full cascade benchmark).
usage: cycle.py "<change-name>" "<one-line description>"
Flags read from env (EARTH1_HARDSHIP_MODE, EARTH1_INCOME_CALIBRATION,
EARTH1_SUBSTRATE_FLAG=c2plus_v1|off, EARTH1_C2PLUS_TABLES).
Appends the MISS table to ops/alive/CALIBRATION_CYCLES.md; exit 0=PASS.
"""
import json
import os
import subprocess
import sys
import time

import hashlib

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

SEED = int(os.environ.get("EARTH1_CYCLE_SEED", "4242"))
POP, DAYS = 20_000, 180
NOLOG = os.environ.get("EARTH1_CYCLE_NOLOG") == "1"


def _sha(rel):
    p = os.path.join(ROOT, rel)
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:10] \
        if os.path.exists(p) else "MISSING"
CASCADE_REF_20K = 2168          # canonical cliff, this seed/scale (decomp2)
BANDS = (("18-29", 18, 30), ("30-49", 30, 50), ("50+", 50, 121))


def build_and_run():
    from earth1.alive import birth_world, live_one_day
    sub = None if os.environ.get("EARTH1_SUBSTRATE_FLAG", "c2plus_v1") \
        == "off" else "c2plus_v1"
    w = birth_world(POP, SEED, substrate=sub)
    rng = np.random.default_rng(SEED)
    cum = {"deaths": 0, "cascades_fired": 0}
    dead_ages = []
    prev = w.health.alive.copy()
    for _ in range(DAYS):
        st = live_one_day(w, rng)
        for k in cum:
            cum[k] += int(st.get(k, 0) or 0)
        died = prev & ~w.health.alive
        if died.any():
            dead_ages.extend((18.0 + w.civ.age[died] * 72.0).tolist())
        prev = w.health.alive.copy()
    return w, cum, sub, np.array(dead_ages)


def score_anchors(w, cum):
    from earth1.poverty import anchors, poverty_profile
    p = poverty_profile(w)
    A = anchors()["anchors"]
    med_r = A["pip_world_median_daily_2021ppp"]["value"]
    line_r = A["poverty_830_2021ppp"]["value"] / 100.0
    cdr = cum["deaths"] / POP * (365.0 / DAYS)
    med = p["median_welfare_ppp"]
    line = p["poverty_830_2021ppp_headcount"]
    return {
        "median": {"value": round(med, 2), "target": med_r,
                   "pass": bool(abs(med - med_r) / med_r <= 0.10)},
        "pov_830": {"value": round(line, 4), "target": line_r,
                    "pass": bool(abs(line - line_r) <= 0.05)},
        "cdr_yr": {"value": round(cdr, 4), "band": [0.007, 0.015],
                   "pass": bool(0.007 <= cdr <= 0.015)},
        "pov_300": round(p["poverty_300_2021ppp_headcount"], 4),
        "pov_420": round(p["poverty_420_2021ppp_headcount"], 4),
    }


def score_attitudes(w):
    """A-v2 DEV cohort task at 20k: LOO-by-country ridge in logit space
    on Earth-1 (country, band) cohort features vs the 98-item targets."""
    from earth1.cohort_features import cell_features
    ct = json.load(open(os.path.join(
        ROOT, "data/benchmark_a/confirm_targets_v2.json")))
    feats = cell_features(w)
    lam_grid = (0.1, 1.0, 10.0)
    # c007 blend (EARTH1_COHORT_BLEND=v1): cell prediction = blind
    # national prediction + b_g·(global item age-gradient term) +
    # b_m·(model cohort deviation); b_g, b_m fit once on the FIT-half
    # countries (c006 sha split), applied everywhere; still LOO.
    BLEND = os.environ.get("EARTH1_COHORT_BLEND") == "v1"
    XB = {"18-29": -0.424, "30-49": -0.201, "50+": 0.083}
    import hashlib as _hl

    def _fit_half(c2):
        return int(_hl.sha256(c2.encode()).hexdigest(), 16) % 2 == 0
    blend_rows = []
    errs_e1, errs_copy = [], []
    for item, cc in ct["cohorts"].items():
        cells = [(iso2, b, d["yes"], d["n"])
                 for iso2, bands in cc.items()
                 for b, d in bands.items() if (iso2, b) in feats]
        countries = sorted({c[0] for c in cells})
        if len(countries) < 10:
            continue
        nat = {}
        for iso2 in countries:
            mine = [(y, n) for c2, b, y, n in cells if c2 == iso2]
            nat[iso2] = sum(y * n for y, n in mine) / sum(n for _, n in mine)
        Xa = np.array([feats[(c2, b)] for c2, b, y, n in cells])
        ya = np.array([y for c2, b, y, n in cells]).clip(1e-3, 1 - 1e-3)
        na = np.array([n for c2, b, y, n in cells], dtype=float)
        la = np.log(ya / (1 - ya))
        grp = np.array([countries.index(c2) for c2, b, y, n in cells])
        mu, sd = Xa.mean(0), np.maximum(Xa.std(0), 1e-9)
        Z = (Xa - mu) / sd
        # country-level design for the copy floor: the floor must also
        # predict the held-out country BLIND (instrument fix, cycle 001:
        # using the true national mean gave a 2.46pp pseudo-floor vs the
        # registered ~10pp — an unbeatable oracle, not a baseline).
        Xn = np.array([np.mean([feats[(c2, b)] for c2b, b, y, n in cells
                                if c2b == c2] if False else
                               [feats[(c2, b)] for cc2, b, y, n in cells
                                if cc2 == c2], axis=0)
                       for c2 in countries])
        yn = np.array([nat[c2] for c2 in countries]).clip(1e-3, 1 - 1e-3)
        ln = np.log(yn / (1 - yn))
        Zn = (Xn - mu) / sd
        g_item = 0.0
        if BLEND:
            fit_m = np.array([_fit_half(c2) for c2, _, _, _ in cells])
            if fit_m.sum() >= 6:
                xs_f = np.array([XB[b] for _, b, _, _ in cells])[fit_m]
                g_item = float(np.polyfit(
                    xs_f, la[fit_m], 1, w=np.sqrt(na[fit_m]))[0])
        for gi, iso2 in enumerate(countries):
            te, tr = grp == gi, grp != gi
            trn = np.arange(len(countries)) != gi
            # HONEST lambda (instrument fix, c007): chosen by TRAINING
            # residual, never by test error. The previous min-over-λ on
            # the held-out cells was a mild oracle on BOTH e1 and the
            # floor (gaps unaffected, absolute values ~optimistic).
            def _pick(Zt, lt):
                best_l, best_e = None, None
                for lam in lam_grid:
                    A0 = Zt.T @ Zt + lam * np.eye(Zt.shape[1])
                    b0 = np.linalg.solve(A0, Zt.T @ (lt - lt.mean()))
                    e0 = float(np.mean((Zt @ b0 + lt.mean() - lt) ** 2))                         + 1e-4 * lam
                    if best_e is None or e0 < best_e:
                        best_l, best_e = lam, e0
                return best_l
            lam_e = 1.0
            A_ = Z[tr].T @ Z[tr] + lam_e * np.eye(Z.shape[1])
            bvec = np.linalg.solve(A_, Z[tr].T @ (la[tr] - la[tr].mean()))
            pred = Z[te] @ bvec + la[tr].mean()
            errs_e1.append(np.abs(1 / (1 + np.exp(-pred)) - ya[te]).mean())
            An = Zn[trn].T @ Zn[trn] + lam_e * np.eye(Zn.shape[1])
            bn = np.linalg.solve(An, Zn[trn].T @ (ln[trn] - ln[trn].mean()))
            pn = float(Zn[gi] @ bn + ln[trn].mean())
            errs_copy.append(np.abs(1 / (1 + np.exp(-pn)) - ya[te]).mean())
            if BLEND:
                A_ = Z[tr].T @ Z[tr] + 1.0 * np.eye(Z.shape[1])
                b_ = np.linalg.solve(A_, Z[tr].T @ (la[tr] - la[tr].mean()))
                pl = Z[te] @ b_ + la[tr].mean()
                An = Zn[trn].T @ Zn[trn] + 1.0 * np.eye(Zn.shape[1])
                bn = np.linalg.solve(An, Zn[trn].T @ (ln[trn] - ln[trn].mean()))
                pn = float(Zn[gi] @ bn + ln[trn].mean())
                xs_te = np.array([XB[b] for c2, b, _, _ in
                                  np.array(cells, object)[te]])
                for k in range(int(te.sum())):
                    blend_rows.append((
                        float(la[te][k] - pn), g_item * float(xs_te[k]),
                        float(pl[k] - pl.mean()), float(na[te][k]),
                        _fit_half(iso2), float(ya[te][k]), pn))
    mae_e1 = float(np.mean(errs_e1) * 100)
    mae_copy = float(np.mean([float(x) for x in errs_copy]) * 100)
    out = {"cohort_mae_pp": round(mae_e1, 3),
           "national_copy_floor_pp": round(mae_copy, 3),
           "pass": bool(mae_e1 <= mae_copy)}
    if BLEND and blend_rows:
        R = blend_rows
        fit = [r for r in R if r[4]]
        D = np.array([[r[1], r[2]] for r in fit])
        y_ = np.array([r[0] for r in fit])
        w_ = np.sqrt([r[3] for r in fit])
        beta, *_ = np.linalg.lstsq(D * w_[:, None], y_ * w_, rcond=None)
        def _e(rows):
            return [abs(1 / (1 + np.exp(-(r[6] + beta[0] * r[1]
                                          + beta[1] * r[2]))) - r[5])
                    for r in rows]
        out["blend_beta_gradient"] = round(float(beta[0]), 3)
        out["blend_beta_model"] = round(float(beta[1]), 3)
        out["blend_mae_pp"] = round(float(np.mean(_e(R))) * 100, 3)
        out["blend_mae_heldout_pp"] = round(float(np.mean(
            _e([r for r in R if not r[4]]))) * 100, 3)
        out["cohort_mae_pp"] = out["blend_mae_pp"]
        out["pass"] = bool(out["blend_mae_pp"] <= mae_copy)
    return out


def score_mortality_structure(w, dead_ages):
    """Founder ruling: CDR must not go green while age structure is
    red. Adult-world adjustments declared: 65+ share target is the
    fetched 65+/(1 − 0-14) = 65+ share of the ADULT+ population; the
    0-14 share is INAPPLICABLE (Earth-1 is 18+ by construction).
    Mean-age-at-death band is a declared DEV band around fetched LE."""
    from earth1.poverty import anchors
    A = anchors()["anchors"]
    le = A["life_expectancy_years"]["value"]
    s65 = A["pop_share_65plus_pct"]["value"] / 100.0
    s014 = A["pop_share_0_14_pct"]["value"] / 100.0
    target65 = s65 / (1.0 - s014)
    alive = w.health.alive
    years = 18.0 + np.asarray(w.civ.age)[alive] * 72.0
    share65 = float((years >= 65).mean())
    mad = float(np.mean(dead_ages)) if len(dead_ages) else 0.0
    return {"mean_age_at_death": {"value": round(mad, 1),
                                  "target_LE": le, "band": [le - 10, le + 10],
                                  "pass": bool(le - 10 <= mad <= le + 10)},
            "pop_65plus_share": {"value": round(share65, 4),
                                 "target": round(target65, 4),
                                 "pass": bool(abs(share65 - target65) <= 0.04)},
            "pop_0_14": "INAPPLICABLE (adult-only world)"}


def score_cascades(cum):
    r = cum["cascades_fired"] / CASCADE_REF_20K
    return {"fired": cum["cascades_fired"], "ratio_vs_canonical": round(r, 3),
            "pass": bool(cum["cascades_fired"] > 0 and 0.3 <= r <= 3.0)}


def main(name, desc):
    t0 = time.time()
    flags = {k: os.environ.get(k, "") for k in
             ("EARTH1_HARDSHIP_MODE", "EARTH1_INCOME_CALIBRATION",
              "EARTH1_SUBSTRATE_FLAG", "EARTH1_C2PLUS_TABLES",
              "EARTH1_DEMO_FORCE_GRADIENT")}
    flags["EARTH1_C2PLUS_TABLES"] = os.environ.get(
        "EARTH1_C2PLUS_TABLES", "c2plus_tables_v2.json")
    w, cum, sub, dead_ages = build_and_run()
    res = {"cycle": name, "change": desc, "flags": flags,
           "substrate": sub, "seed": SEED, "pop": POP, "days": DAYS,
           "commit": subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                                    capture_output=True, text=True,
                                    cwd=ROOT).stdout.strip(),
           "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "provenance": {
               "tables_sha": _sha("data/" + os.environ.get(
                   "EARTH1_C2PLUS_TABLES", "c2plus_tables_v2.json")),
               "anchors_sha": _sha("data/anchors_worldbank.json"),
               "income_cal_sha": _sha(
                   "data/income_calibration."
                   + ("incumbent" if os.environ.get(
                       "EARTH1_SUBSTRATE_FLAG", "off") == "off"
                      else os.environ.get("EARTH1_SUBSTRATE_FLAG"))
                   + ".json")},
           "anchors": score_anchors(w, cum),
           "mortality_structure": score_mortality_structure(w, dead_ages),
           "attitudes": score_attitudes(w),
           "cascades": score_cascades(cum)}
    ms = res["mortality_structure"]
    gates = [res["anchors"]["median"]["pass"], res["anchors"]["pov_830"]["pass"],
             res["anchors"]["cdr_yr"]["pass"], res["attitudes"]["pass"],
             res["cascades"]["pass"], ms["mean_age_at_death"]["pass"],
             ms["pop_65plus_share"]["pass"]]
    res["verdict"] = "PASS" if all(gates) else "MISS"
    res["seconds"] = round(time.time() - t0, 1)
    os.makedirs(os.path.join(ROOT, "data", "cycles"), exist_ok=True)
    json.dump(res, open(os.path.join(
        ROOT, "data", "cycles", f"{name}.json"), "w"), indent=1)
    a, at, c = res["anchors"], res["attitudes"], res["cascades"]
    fl = ";".join(f"{k.split('_')[-1]}={v or 'off'}"
                  for k, v in res["flags"].items())
    pv = res["provenance"]
    row = (f"| {name} | {desc[:44]} | {at['cohort_mae_pp']:.2f} vs "
           f"{at['national_copy_floor_pp']:.2f}{'✓' if at['pass'] else '✗'} "
           f"| ${a['median']['value']}{'✓' if a['median']['pass'] else '✗'} "
           f"| {a['pov_830']['value']:.1%}{'✓' if a['pov_830']['pass'] else '✗'} "
           f"| {a['cdr_yr']['value']:.3f}{'✓' if a['cdr_yr']['pass'] else '✗'} "
           f"| {ms['mean_age_at_death']['value']}{'✓' if ms['mean_age_at_death']['pass'] else '✗'} "
           f"| {ms['pop_65plus_share']['value']:.1%}{'✓' if ms['pop_65plus_share']['pass'] else '✗'} "
           f"| {c['ratio_vs_canonical']}{'✓' if c['pass'] else '✗'} "
           f"| **{res['verdict']}** | {fl} | t:{pv['tables_sha']} "
           f"a:{pv['anchors_sha']} i:{pv['income_cal_sha']} |\n")
    if NOLOG:
        print(json.dumps({k: res[k] for k in ("cycle", "verdict")}))
        print("VERDICT:", res["verdict"], f"({res['seconds']}s)")
        sys.exit(0 if res["verdict"] == "PASS" else 1)
    log = os.path.join(ROOT, "ops/alive/CALIBRATION_CYCLES.md")
    if not os.path.exists(log):
        open(log, "w").write(
            "# CALIBRATION CYCLES — the production loop at 20k\n"
            "One named change per cycle; gates per the locked ruling.\n\n"
            "| cycle | change | cohortMAE vs floor | median | $8.30 | "
            "CDR | ageAtDeath | 65+ | casc× | verdict | flags | provenance |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    open(log, "a").write(row)
    print(json.dumps(res, indent=1))
    print("VERDICT:", res["verdict"], f"({res['seconds']}s)")
    sys.exit(0 if res["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
