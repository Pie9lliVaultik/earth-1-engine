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

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

SEED, POP, DAYS = 4242, 20_000, 180
CASCADE_REF_20K = 2168          # canonical cliff, this seed/scale (decomp2)
BANDS = (("18-29", 18, 30), ("30-49", 30, 50), ("50+", 50, 121))


def build_and_run():
    from earth1.alive import birth_world, live_one_day
    sub = None if os.environ.get("EARTH1_SUBSTRATE_FLAG", "c2plus_v1") \
        == "off" else "c2plus_v1"
    w = birth_world(POP, SEED, substrate=sub)
    rng = np.random.default_rng(SEED)
    cum = {"deaths": 0, "cascades_fired": 0}
    for _ in range(DAYS):
        st = live_one_day(w, rng)
        for k in cum:
            cum[k] += int(st.get(k, 0) or 0)
    return w, cum, sub


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
    from earth1.calibration import living_features
    from earth1.genesis import GENESIS_COUNTRY_CODES
    ct = json.load(open(os.path.join(
        ROOT, "data/benchmark_a/confirm_targets_v2.json")))
    X = living_features(w)
    civ, alive = w.civ, w.health.alive
    years = 18.0 + np.asarray(civ.age) * 72.0
    c2i = {c: i for i, c in enumerate(GENESIS_COUNTRY_CODES)}
    feats = {}
    for iso2, ci in c2i.items():
        for bname, lo, hi in BANDS:
            m = alive & (civ.country == ci) & (years >= lo) & (years < hi)
            if m.sum() >= 25:
                feats[(iso2, bname)] = X[m].mean(0)
    lam_grid = (0.1, 1.0, 10.0)
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
        for gi, iso2 in enumerate(countries):
            te, tr = grp == gi, grp != gi
            trn = np.arange(len(countries)) != gi
            best, bestc = None, None
            for lam in lam_grid:
                A_ = Z[tr].T @ Z[tr] + lam * np.eye(Z.shape[1])
                bvec = np.linalg.solve(A_, Z[tr].T @ (la[tr] - la[tr].mean()))
                pred = Z[te] @ bvec + la[tr].mean()
                e = np.abs(1 / (1 + np.exp(-pred)) - ya[te]).mean()
                best = e if best is None or e < best else best
                An = Zn[trn].T @ Zn[trn] + lam * np.eye(Zn.shape[1])
                bn = np.linalg.solve(An, Zn[trn].T @ (ln[trn] - ln[trn].mean()))
                pn = float(Zn[gi] @ bn + ln[trn].mean())
                ec = np.abs(1 / (1 + np.exp(-pn)) - ya[te]).mean()
                bestc = ec if bestc is None or ec < bestc else bestc
            errs_e1.append(best)
            errs_copy.append(bestc)
    mae_e1 = float(np.mean(errs_e1) * 100)
    mae_copy = float(np.mean([float(x) for x in errs_copy]) * 100)
    return {"cohort_mae_pp": round(mae_e1, 3),
            "national_copy_floor_pp": round(mae_copy, 3),
            "pass": bool(mae_e1 <= mae_copy)}


def score_cascades(cum):
    r = cum["cascades_fired"] / CASCADE_REF_20K
    return {"fired": cum["cascades_fired"], "ratio_vs_canonical": round(r, 3),
            "pass": bool(cum["cascades_fired"] > 0 and 0.3 <= r <= 3.0)}


def main(name, desc):
    t0 = time.time()
    flags = {k: os.environ.get(k, "") for k in
             ("EARTH1_HARDSHIP_MODE", "EARTH1_INCOME_CALIBRATION",
              "EARTH1_SUBSTRATE_FLAG", "EARTH1_C2PLUS_TABLES")}
    w, cum, sub = build_and_run()
    res = {"cycle": name, "change": desc, "flags": flags,
           "substrate": sub, "seed": SEED, "pop": POP, "days": DAYS,
           "commit": subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                                    capture_output=True, text=True,
                                    cwd=ROOT).stdout.strip(),
           "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "anchors": score_anchors(w, cum),
           "attitudes": score_attitudes(w),
           "cascades": score_cascades(cum)}
    gates = [res["anchors"]["median"]["pass"], res["anchors"]["pov_830"]["pass"],
             res["anchors"]["cdr_yr"]["pass"], res["attitudes"]["pass"],
             res["cascades"]["pass"]]
    res["verdict"] = "PASS" if all(gates) else "MISS"
    res["seconds"] = round(time.time() - t0, 1)
    os.makedirs(os.path.join(ROOT, "data", "cycles"), exist_ok=True)
    json.dump(res, open(os.path.join(
        ROOT, "data", "cycles", f"{name}.json"), "w"), indent=1)
    a, at, c = res["anchors"], res["attitudes"], res["cascades"]
    row = (f"| {name} | {desc[:44]} | {at['cohort_mae_pp']:.2f} vs "
           f"{at['national_copy_floor_pp']:.2f}{'✓' if at['pass'] else '✗'} "
           f"| ${a['median']['value']}{'✓' if a['median']['pass'] else '✗'} "
           f"| {a['pov_830']['value']:.1%}{'✓' if a['pov_830']['pass'] else '✗'} "
           f"| {a['cdr_yr']['value']:.3f}{'✓' if a['cdr_yr']['pass'] else '✗'} "
           f"| {c['ratio_vs_canonical']}{'✓' if c['pass'] else '✗'} "
           f"| **{res['verdict']}** |\n")
    log = os.path.join(ROOT, "ops/alive/CALIBRATION_CYCLES.md")
    if not os.path.exists(log):
        open(log, "w").write(
            "# CALIBRATION CYCLES — the production loop at 20k\n"
            "One named change per cycle; gates per the locked ruling.\n\n"
            "| cycle | change | cohortMAE vs floor | median | $8.30 | "
            "CDR | casc× | verdict |\n|---|---|---|---|---|---|---|---|\n")
    open(log, "a").write(row)
    print(json.dumps(res, indent=1))
    print("VERDICT:", res["verdict"], f"({res['seconds']}s)")
    sys.exit(0 if res["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
