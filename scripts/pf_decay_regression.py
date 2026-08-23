"""PF-DECAY-1 targeted regression (frozen: ops/alive/PF_DECAY_1.md).
Runs ONLY after the full KA battery passes. One question: does
restoring the correct TransitionRule contract break the candidate
architecture about to be frozen? No tuning of any kind.

R1  Chronicle isolation — IT12 arms (COMPOSITE/INTRINSIC/KA1_delete)
    rerun with the residue flag ON, seed 8904: must be UNCHANGED vs
    data/it12/arms.json (Memory.half_life != decay_half_life as
    mechanisms).
R2  cascade-event stress — engineered panic firing (clamp days
    60-62) on IT6-ALL @8905, residue ON, all frozen IT6 gates; the
    instant-write reference arm runs for comparison only.
R3  repeated-trigger stress — clamp days 60-180, 210-day horizon:
    fire cadence every cooldown, residue envelope must plateau at
    the bounded superposition, never ratchet; world health gates.
R4  no-trigger control — IT6-ALL @8905 residue ON vs OFF, no
    engineered events: identical worlds.
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
                          str(ROOT / "data" / "pf_decay")))
SEED_REG = 8905
CLAMP_R2 = tuple(range(60, 63))
CLAMP_R3 = tuple(range(60, 181))

IT6_ARMS = {
    "R2_res":  dict(op="dy", cnv="dy", flr=True, cas=True, relax=0.045,
                    seed=SEED_REG, residue=True, casfire=CLAMP_R2),
    "R2_inst": dict(op="dy", cnv="dy", flr=True, cas=True, relax=0.045,
                    seed=SEED_REG, casfire=CLAMP_R2),
    "R3_res":  dict(op="dy", cnv="dy", flr=True, cas=True, relax=0.045,
                    seed=SEED_REG, residue=True, casfire=CLAMP_R3,
                    days=210, no_fork=True),
    "R4_on":   dict(op="dy", cnv="dy", flr=True, cas=True, relax=0.045,
                    seed=SEED_REG, residue=True),
    "R4_off":  dict(op="dy", cnv="dy", flr=True, cas=True, relax=0.045,
                    seed=SEED_REG),
    # clean identity control: firing impossible => worlds MUST match
    "R4c_on":  dict(op="dy", cnv="dy", flr=True, cas=True, relax=0.045,
                    seed=SEED_REG, residue=True, rules_off=True),
    "R4c_off": dict(op="dy", cnv="dy", flr=True, cas=True, relax=0.045,
                    seed=SEED_REG, rules_off=True),
}
R1_ARMS = ("COMPOSITE", "INTRINSIC", "KA1_delete")


def _worker(job):
    kind, name = job
    try:
        if kind == "it6":
            import scripts.it6_dyadic as it6
            it6.ARMS.update(IT6_ARMS)
            return {"kind": kind, "name": name, "r": it6.run_arm(name)}
        os.environ["EARTH1_DECAY_RESIDUE"] = "1"
        import scripts.it12_calibration  # installs it11.ARMS
        import scripts.it11_carrier as engine
        return {"kind": kind, "name": name, "r": engine.run_arm(name)}
    except Exception as e:
        import traceback
        return {"kind": kind, "name": name, "error": str(e),
                "trace": traceback.format_exc()[-2000:]}


def _it6_gates(r):
    """The frozen IT6 health gates, mechanical."""
    g = {}
    p_last = r["panels"][max(r["panels"], key=int)]
    g["sat_lt_20"] = all(p["sat_max"] < 0.20
                         for p in r["panels"].values())
    g["sdr_ge_05"] = p_last["sd_ratio_genesis"] >= 0.5
    g["alpha_interior"] = (p_last["alpha_gt99"] < 0.01
                           and p_last["alpha_floor"] < 0.01)
    g["unanimity_lt_50"] = all(p["unanimous_share"] < 0.50
                               for p in r["panels"].values())
    if r.get("tau"):
        g["tau_in_5_15"] = (r["tau"]["half_life_d"] is not None
                            and 5 <= r["tau"]["half_life_d"] <= 15)
    if r.get("transmission"):
        t = r["transmission"]
        g["ring1_band"] = 0.006 <= t["ring1_d30"] <= 0.15
        g["ring2_min"] = t["ring2_d30"] >= 0.0005
        g["ring3_pos"] = t["ring3_d30"] > 0
    return g


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    jobs = ([("it6", n) for n in IT6_ARMS]
            + [("it12", n) for n in R1_ARMS])
    sel = os.environ.get("EARTH1_PF_REG_ARMS")
    if sel:
        keep = set(sel.split(","))
        jobs = [j for j in jobs if j[1] in keep]
    ctx = mp.get_context("spawn")
    results = {}
    with ctx.Pool(processes=len(jobs), maxtasksperchild=1) as pool:
        for out in pool.imap_unordered(_worker, jobs):
            results[out["name"]] = out
            print(f"  done {out['name']}"
                  + (f" ERROR {out.get('error')}" if "error" in out
                     else ""), flush=True)

    verdict = {"errors": [n for n, o in results.items()
                          if "error" in o]}

    ran = set(results)

    # R1: unchanged vs IT12 recorded
    rec12 = {x["arm"]: x for x in
             json.load(open(ROOT / "data" / "it12" / "arms.json"))}
    r1 = {}
    for n in [x for x in R1_ARMS if x in ran]:
        if "error" in results[n]:
            r1[n] = "ERROR"
            continue
        got = json.loads(json.dumps(results[n]["r"]))
        same = got["series"] == rec12[n]["series"]
        r1[n] = {"series_unchanged": bool(same),
                 "d30": got["d30"], "rec_d30": rec12[n]["d30"]}
    verdict["R1"] = r1
    if r1:
        verdict["R1_pass"] = all(isinstance(v, dict)
                                 and v["series_unchanged"]
                                 for v in r1.values())

    # R2: gates on the residue arm; firing + decay conformance
    if "R2_res" in ran and "error" not in results["R2_res"]:
        r = results["R2_res"]["r"]
        g = _it6_gates(r)
        pf = r["pf"]
        g["fired_at_clamp"] = 60 in pf["fire_days"]
        g["one_big_loc_firing"] = pf["big_loc_fire_days"] == [60]
        s = {e["day"]: e["fear_level"] for e in pf["series"]}
        if s.get(60):
            ratio = (s.get(120, 0.0) / s[60]) if s[60] else None
            analytic = 2.0 ** (-(120 - 60) / 45.0)
            g["decay_matches_analytic"] = (
                ratio is not None and abs(ratio - analytic) < 0.02)
            verdict["R2_decay"] = {"ratio_d120_d60": ratio,
                                   "analytic": analytic}
        verdict["R2_gates"] = g
        verdict["R2_pass"] = all(g.values())

    # R3: cadence + plateau + health
    if "R3_res" in ran and "error" not in results["R3_res"]:
        r = results["R3_res"]["r"]
        g = _it6_gates(r)
        g.pop("tau_in_5_15", None)      # no fork in R3
        pf = r["pf"]
        fires = pf["big_loc_fire_days"]
        gaps = [b - a for a, b in zip(fires, fires[1:])]
        g["cadence_cooldown"] = (len(fires) >= 3
                                 and all(x == 14 for x in gaps))
        s = [e["fear_level"] for e in pf["series"]]
        w1 = max(s[120:150]) if len(s) > 150 else None
        w2 = max(s[150:180]) if len(s) > 180 else None
        bound = 0.10 / (1 - 2.0 ** (-14 / 45.0)) + 0.01
        g["envelope_plateau"] = (w1 is not None and w2 is not None
                                 and w2 <= w1 * 1.05)
        g["envelope_bounded"] = max(s) <= bound
        verdict["R3_envelope"] = {"win_120_150": w1, "win_150_180": w2,
                                  "max": max(s), "analytic_bound":
                                  round(bound, 4),
                                  "fire_days": fires}
        verdict["R3_gates"] = g
        verdict["R3_pass"] = all(g.values())

    # R4: identical worlds
    KEYS4 = ("panels", "tau", "transmission", "capability",
             "encounters", "softening_frac_60_90")

    def _pair(on, off):
        a = json.loads(json.dumps(results[on]["r"]))
        b = json.loads(json.dumps(results[off]["r"]))
        return a, {k: a[k] == b[k] for k in KEYS4}

    if all(n in ran and "error" not in results[n]
           for n in ("R4c_on", "R4c_off")):
        a, same = _pair("R4c_on", "R4c_off")
        verdict["R4c"] = {"identical": same}
        # firing impossible => identity is a HARD gate
        verdict["R4_pass"] = all(same.values())
    if all(n in ran and "error" not in results[n]
           for n in ("R4_on", "R4_off")):
        a, same = _pair("R4_on", "R4_off")
        fired = a["cascade_state"]["n_last_fired"]
        verdict["R4"] = {"identical": same,
                         "residues_on_arm":
                         a["cascade_state"]["n_residues"],
                         "fired_localities_on_arm": fired}
        if fired == 0:
            # genuinely no-trigger => identity also required here
            verdict["R4_pass"] = (verdict.get("R4_pass", True)
                                  and all(same.values()))
        # fired > 0: natural firings mean the pair legitimately
        # differs (instant write vs decaying level) — reported as
        # diagnostic, not an identity gate

    passes = [verdict.get(k) for k in
              ("R1_pass", "R2_pass", "R3_pass", "R4_pass")]
    verdict["REGRESSION"] = ("PASS" if (not verdict["errors"]
                                        and all(passes)) else "FAIL")
    payload = {"verdict": verdict,
               "results": {n: o for n, o in results.items()}}
    (OUT / "regression.json").write_text(json.dumps(payload, indent=1))
    print(json.dumps(verdict, indent=1))
    print(f"PF-DECAY-1 regression {verdict['REGRESSION']} "
          f"{round((time.monotonic() - t0) / 60, 1)} min")


if __name__ == "__main__":
    main()
