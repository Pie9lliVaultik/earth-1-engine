"""PF-DECAY-2 targeted regression (frozen: ops/alive/PF_DECAY_2.md).
Reruns the exact world that broke PF-DECAY-1 (seed 8905) under the
restored open-loop topology, plus the IT12 clean-isolation arm.

Gates:
R4  cascades-have-zero-in-loop-footprint: R4_on (rules on, residue
    flag on) IDENTICAL to R4c_on (rules off) on every stored-force
    metric, and IDENTICAL to R4_wipe (residues deleted daily — the
    KA10-at-scale receipt: N_fires_caused_only_by_actuation = 0 is
    evidenced, not asserted). Firing stats reported; effective-view
    saturation reported separately.
R2  engineered single firing: stored-force IT6 gates all pass; the
    pf_big fear overlay equals the analytic superposition of the
    RECORDED fire days exactly (panic is the only positive-fear
    rule).
R3  sustained trigger 60-180 (210d): cooldown cadence exact inside
    the clamp window; overlay bounded by the analytic superposition;
    stored-force health gates pass.
IT12ISO Chronicle isolation with TRANSITION_RULES empty: COMPOSITE
    normalized d30/true-peak in [0.2, 0.6]; INTRINSIC carrier
    analytic-exact. Fails => STOP (not retuned).
"""
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import multiprocessing as mp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = Path(os.environ.get("EARTH1_PF_OUT",
                          str(ROOT / "data" / "pf_decay2")))
SEED_REG = 8905
CLAMP_R2 = tuple(range(60, 63))
CLAMP_R3 = tuple(range(60, 181))
BASE = dict(op="dy", cnv="dy", flr=True, cas=True, relax=0.045,
            seed=SEED_REG)

IT6_ARMS = {
    "R2_res":  dict(BASE, residue=True, casfire=CLAMP_R2),
    "R3_res":  dict(BASE, residue=True, casfire=CLAMP_R3, days=210,
                    no_fork=True),
    "R4_on":   dict(BASE, residue=True),
    "R4_wipe": dict(BASE, residue=True, wipe_residues=True),
    "R4_off":  dict(BASE),                      # incumbent reference
    "R4c_on":  dict(BASE, residue=True, rules_off=True),
}
IT12_ISO = ("COMPOSITE", "INTRINSIC")
KEYS4 = ("panels", "tau", "transmission", "capability", "encounters",
         "softening_frac_60_90")


def _worker(job):
    kind, name = job
    try:
        if kind == "it6":
            import scripts.it6_dyadic as it6
            it6.ARMS.update(IT6_ARMS)
            return {"kind": kind, "name": name, "r": it6.run_arm(name)}
        # IT12 isolation: rules explicitly empty, no residue flag
        os.environ.pop("EARTH1_DECAY_RESIDUE", None)
        import earth1.thresholds as th
        th.TRANSITION_RULES = []
        import scripts.it12_calibration  # installs it11.ARMS
        import scripts.it11_carrier as engine
        return {"kind": kind, "name": f"ISO_{name}",
                "r": engine.run_arm(name)}
    except Exception as e:
        import traceback
        nm = name if kind == "it6" else f"ISO_{name}"
        return {"kind": kind, "name": nm, "error": str(e),
                "trace": traceback.format_exc()[-2000:]}


def _gates(r, skip_fork=False):
    g = {}
    g["sat_lt_20_all_panels"] = all(p["sat_max"] < 0.20
                                    for p in r["panels"].values())
    p_last = r["panels"][max(r["panels"], key=int)]
    g["sdr_ge_05"] = p_last["sd_ratio_genesis"] >= 0.5
    g["alpha_interior"] = (p_last["alpha_gt99"] < 0.01
                           and p_last["alpha_floor"] < 0.01)
    g["unanimity_lt_50"] = all(p["unanimous_share"] < 0.50
                               for p in r["panels"].values())
    if not skip_fork and r.get("tau"):
        g["tau_in_5_15"] = (r["tau"]["half_life_d"] is not None
                            and 5 <= r["tau"]["half_life_d"] <= 15)
    if not skip_fork and r.get("transmission"):
        t = r["transmission"]
        g["ring1_band"] = 0.006 <= t["ring1_d30"] <= 0.15
        g["ring2_min"] = t["ring2_d30"] >= 0.0005
        g["ring3_pos"] = t["ring3_d30"] > 0
    return g


def _overlay_prediction(fire_days, days_n, h=45.0, amp=0.10):
    """Analytic superposition of recorded panic fires at pf_big.
    Residue day = fire_day - 1 (w.day at detection)."""
    out = []
    for d in range(1, days_n + 1):
        s = 0.0
        for fd in fire_days:
            rday = fd - 1
            if d >= fd:
                f = 2.0 ** (-(d - rday) / h)
                if f >= 0.01 and amp * f >= 0.01:
                    s += amp * f
        out.append(s)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    jobs = ([("it6", n) for n in IT6_ARMS]
            + [("it12iso", n) for n in IT12_ISO])
    sel = os.environ.get("EARTH1_PF_REG_ARMS")
    if sel:
        keep = set(sel.split(","))
        jobs = [j for j in jobs if j[1] in keep or
                f"ISO_{j[1]}" in keep]
    ctx = mp.get_context("spawn")
    results = {}
    with ctx.Pool(processes=len(jobs), maxtasksperchild=1) as pool:
        for out in pool.imap_unordered(_worker, jobs):
            results[out["name"]] = out
            print(f"  done {out['name']}"
                  + (f" ERROR {out.get('error')}" if "error" in out
                     else ""), flush=True)
    ran = set(results)
    V = {"errors": [n for n, o in results.items() if "error" in o]}

    def J(n):
        return json.loads(json.dumps(results[n]["r"]))

    # R4: zero in-loop footprint + KA10-at-scale receipt
    if all(n in ran and "error" not in results[n]
           for n in ("R4_on", "R4c_on", "R4_wipe")):
        a, c, wp = J("R4_on"), J("R4c_on"), J("R4_wipe")
        same_c = {k: a[k] == c[k] for k in KEYS4}
        same_w = {k: a[k] == wp[k] for k in KEYS4}
        V["R4_identity_vs_rules_off"] = same_c
        V["R4_identity_vs_wipe"] = same_w
        V["R4_firings"] = {
            "unique_rule_loc": a["cascade_state"]["n_last_fired"],
            "active_residues_end":
                a["cascade_state"]["n_residues"],
            "wipe_unique_rule_loc":
                wp["cascade_state"]["n_last_fired"]}
        V["R4_eff_sat"] = a.get("eff_sat")
        V["R4_incumbent_sat_last"] = J("R4_off")["panels"]["120"][
            "sat_max"] if "R4_off" in ran else None
        V["R4_pass"] = (all(same_c.values()) and all(same_w.values())
                        and a["cascade_state"]["n_last_fired"] ==
                        wp["cascade_state"]["n_last_fired"]
                        and a["cascade_state"]["n_last_fired"] > 0)

    # R2: engineered firing + exact overlay conformance
    if "R2_res" in ran and "error" not in results["R2_res"]:
        r = J("R2_res")
        g = _gates(r)
        pf = r["pf"]
        g["fired_at_clamp"] = 60 in pf["big_loc_fire_days"]
        pred = _overlay_prediction(pf["big_loc_fire_days"],
                                   len(pf["series"]))
        worst = max(abs(e["fear_level"] - p)
                    for e, p in zip(pf["series"], pred))
        g["overlay_matches_analytic"] = worst < 2e-3
        V["R2_overlay_worst_err"] = round(worst, 5)
        V["R2_big_fire_days"] = pf["big_loc_fire_days"]
        V["R2_gates"] = g
        V["R2_pass"] = all(g.values())

    # R3: cadence + bounded superposition + health
    if "R3_res" in ran and "error" not in results["R3_res"]:
        r = J("R3_res")
        g = _gates(r, skip_fork=True)
        pf = r["pf"]
        fires = pf["big_loc_fire_days"]
        gaps_all = [b - a for a, b in zip(fires, fires[1:])]
        in_clamp = [f for f in fires if 60 <= f <= 180]
        gaps_clamp = [b - a for a, b in
                      zip(in_clamp, in_clamp[1:])]
        g["cooldown_honored"] = all(x >= 14 for x in gaps_all)
        g["cadence_in_clamp"] = (len(in_clamp) >= 3
                                 and all(x == 14
                                         for x in gaps_clamp))
        s = [e["fear_level"] for e in pf["series"]]
        bound = 0.10 / (1 - 2.0 ** (-14 / 45.0)) + 0.02
        g["overlay_bounded"] = max(s) <= bound
        pred = _overlay_prediction(fires, len(pf["series"]))
        worst = max(abs(a - b) for a, b in zip(s, pred))
        g["overlay_matches_analytic"] = worst < 2e-3
        V["R3_fires"] = fires
        V["R3_overlay_max"] = round(max(s), 4)
        V["R3_overlay_worst_err"] = round(worst, 5)
        V["R3_eff_sat"] = r.get("eff_sat")
        V["R3_gates"] = g
        V["R3_pass"] = all(g.values())

    # IT12 isolation
    iso = {}
    for n in IT12_ISO:
        key = f"ISO_{n}"
        if key in ran and "error" not in results[key]:
            r = J(key)
            series = r["series"]
            deltas = [e["cohort_fear_delta"] for e in series]
            peak = max(deltas)
            d30 = deltas[-1]
            entry = {"peak": round(peak, 5), "d30": round(d30, 5),
                     "resid_norm": round(d30 / peak, 3) if peak
                     else None,
                     "carrier_d30": r.get("carrier_d30")}
            if n == "COMPOSITE":
                entry["in_band"] = (peak > 0
                                    and 0.2 <= d30 / peak <= 0.6)
            if n == "INTRINSIC":
                sal10 = series[9]["salience"]
                entry["carrier_d10"] = sal10
                entry["carrier_exact"] = (
                    sal10 is not None
                    and abs(sal10 - 0.5) < 1e-3
                    and r.get("carrier_d30") is not None
                    and abs(r["carrier_d30"] - 0.125) < 1e-3)
            iso[n] = entry
    if iso:
        V["IT12ISO"] = iso
        V["IT12ISO_pass"] = (
            iso.get("COMPOSITE", {}).get("in_band", False)
            and iso.get("INTRINSIC", {}).get("carrier_exact", False))

    passes = [V.get(k) for k in ("R2_pass", "R3_pass", "R4_pass",
                                 "IT12ISO_pass")]
    V["REGRESSION"] = ("PASS" if (not V["errors"] and all(passes)
                                  and None not in passes)
                       else "FAIL")
    payload = {"verdict": V, "results": results}
    (OUT / "regression2.json").write_text(
        json.dumps(payload, indent=1, default=str))
    print(json.dumps(V, indent=1, default=str))
    print(f"PF-DECAY-2 regression {V['REGRESSION']} "
          f"{round((time.monotonic() - t0) / 60, 1)} min")


if __name__ == "__main__":
    main()
