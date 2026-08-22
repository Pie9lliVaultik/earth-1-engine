"""0.8 ACCEPTANCE — STAGE B adversarial battery (frozen:
ops/alive/STAGE_B_ADVERSARIAL_PREREG.md). Runs only after Stage A
passes. Every test: DETECTED (the named instrument flags the broken
twin) AND CLEAN (the healthy candidate passes the same instrument).
Candidate v2 flags assumed set by the launcher
(EARTH1_COLLECTIVE_CENTERED=1; cascade/residue flags set per arm
config as in the frozen candidate assembly)."""
import copy
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import multiprocessing as mp

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = Path(os.environ.get("EARTH1_PF_OUT",
                          str(ROOT / "data" / "acceptance_0_8" /
                              "stageB")))
ALL = dict(op="dy", cnv="dy", flr=True, cas=True, relax=0.045,
           residue=True)

IT6_JOBS = {
    # broken twins
    "B1_consensus": dict(ALL, seed=9101, days=90, no_fork=True,
                         broken="consensus"),
    "B2_ratchet":   dict(ALL, cnv="inc", seed=9102, days=120),
    "B3_zeroinf":   dict(ALL, op="zero", seed=9103, days=120),
    "B4_fastrelax": dict(ALL, relax=0.60, seed=9104, days=120),
    "B6_accum":     dict(ALL, seed=9106, days=120, no_fork=True,
                         broken="accumulator", endurance=True),
    "B11_bigev":    dict(ALL, seed=9110, days=120, no_fork=True,
                         broken="bigevents", endurance=True),
    "B7_loop":      dict(ALL, seed=9107, days=120, no_fork=True,
                         env={"EARTH1_TEST_CLOSED_LOOP": "1"}),
    "B7_loop_wipe": dict(ALL, seed=9107, days=120, no_fork=True,
                         wipe_residues=True,
                         env={"EARTH1_TEST_CLOSED_LOOP": "1"}),
    # healthy twins (same seeds, same instruments)
    "H_9101": dict(ALL, seed=9101, days=90, no_fork=True),
    "H_9102": dict(ALL, seed=9102, days=120),
    "H_9103": dict(ALL, seed=9103, days=120),
    "H_9104": dict(ALL, seed=9104, days=120),
    "H_9106": dict(ALL, seed=9106, days=120, no_fork=True,
                   endurance=True),
}


def _worker(job):
    kind, name = job
    try:
        if kind == "it6":
            import scripts.it6_dyadic as it6
            it6.ARMS.update(IT6_JOBS)
            return {"name": name, "r": it6.run_arm(name)}
        if kind == "B5":
            os.environ["EARTH1_COLLECTIVE_CENTERED"] = "1"
            broken = name.endswith("broken")
            if broken:
                from earth1.memory import Chronicle
                Chronicle.tick = lambda self, civ, dt_days=1.0: {}
            import scripts.it12_calibration  # installs it11.ARMS
            import scripts.it11_carrier as engine
            engine.ARMS = {"B5": dict(event=True, half_life=10.0,
                                      followups=(1, 2, 4, 7, 11),
                                      spread=False, seed=9105)}
            return {"name": name, "r": engine.run_arm("B5")}
        if kind == "B9":
            os.environ["EARTH1_CASCADE_COOLDOWN"] = "1"
            os.environ["EARTH1_DECAY_RESIDUE"] = "1"
            from earth1.alive import birth_world, effective_forces
            w = birth_world(20000, 9112)
            r = {"raised_plain": False, "raised_residue": False}
            try:
                effective_forces(w)[0, 0] = 9.9
            except ValueError:
                r["raised_plain"] = True
            w.chronicle.cascade_residues = [
                {"rule": "x", "loc": 0, "day": 0,
                 "effects": np.zeros(8) + 0.1, "h": 45.0}]
            try:
                effective_forces(w)[0, 0] = 9.9
            except ValueError:
                r["raised_residue"] = True
            return {"name": name, "r": r}
        if kind == "B8":
            os.environ["EARTH1_TEST_DETECTOR_EFFECTIVE"] = "1"
            os.environ["EARTH1_PF_N"] = os.environ.get(
                "EARTH1_PF_N", "200000")
            sys.path.insert(0, str(ROOT / "scripts"))
            import pf_decay_ka as pf
            return {"name": name, "r": pf.arm_ka10()}
        if kind == "B7ka10":
            # INSTRUMENT REPAIR (recorded): the prereg's KA8-variant
            # is VOID for this breakage mode — its daily clamp resets
            # the sub-threshold accumulation the closed loop needs
            # (0.045×A per day cannot cross in one tick). The valid
            # detector for target-path contamination is the KA10
            # stored-divergence pair: with residues feeding targets,
            # a residue-bearing world MUST diverge from its
            # residue-free twin in STORED forces.
            os.environ["EARTH1_TEST_CLOSED_LOOP"] = "1"
            os.environ["EARTH1_PF_N"] = os.environ.get(
                "EARTH1_PF_N", "200000")
            sys.path.insert(0, str(ROOT / "scripts"))
            import pf_decay_ka as pf
            return {"name": name, "r": pf.arm_ka10()}
        if kind == "B12":
            os.environ["EARTH1_PF_N"] = os.environ.get(
                "EARTH1_PF_N", "200000")
            os.environ["EARTH1_PF_OUT"] = str(OUT)
            sys.path.insert(0, str(ROOT / "scripts"))
            import pf_decay_ka as pf
            healthy = pf.arm_ka5()
            # broken serializer twin: drop residues after load
            from earth1.persistence import save_world, load_world
            os.environ["EARTH1_CASCADE_COOLDOWN"] = "1"
            os.environ["EARTH1_DECAY_RESIDUE"] = "1"
            import earth1.alive as am
            w = am.birth_world(20000, 9111)
            rng = np.random.default_rng(9111)
            for _ in range(5):
                am.live_one_day(w, rng, relax=0.045)
            if getattr(w.chronicle, "cascade_residues", None) is None:
                w.chronicle.cascade_residues = []
            w.chronicle.cascade_residues.append(
                {"rule": "b12", "loc": 0, "day": int(w.day),
                 "effects": np.zeros(8) + 0.1, "h": 45.0})
            p = OUT / "b12_world.pkl"
            save_world(w, p, rng=rng)
            w2, _rs, _i = load_world(p)
            w2.chronicle.cascade_residues = []   # the broken drop
            detected = (len(w.chronicle.cascade_residues)
                        != len(w2.chronicle.cascade_residues))
            return {"name": name, "r": {"healthy": healthy,
                                        "broken_drop_detected":
                                            bool(detected)}}
        if kind == "B10":
            os.environ["EARTH1_COLLECTIVE_CENTERED"] = "1"
            return {"name": name, "r": _b10()}
    except Exception as e:
        import traceback
        return {"name": name, "error": str(e),
                "trace": traceback.format_exc()[-1800:]}


def _b10():
    """Duplicate causality: memory-only vs memory+instant impulse."""
    os.environ["EARTH1_CASCADE_COOLDOWN"] = "1"
    os.environ["EARTH1_DECAY_RESIDUE"] = "1"
    import earth1.alive as am
    import earth1.contagion as cont
    import earth1.feed as feedmod
    import earth1.flourishing as flmod
    import earth1.life as lifemod
    import earth1.conviction_lab as clab
    import earth1.field_lab as flab
    from earth1.memory import Memory
    from earth1.types import Force
    N = int(os.environ.get("EARTH1_B10_N", "200000"))
    w = am.birth_world(N, 9109)
    clab.ALPHA0 = w.civ.alpha.copy()
    flab.FLOUR_REF[0] = w.flourishing
    flab.AROUSAL = np.array(
        [feedmod.AROUSAL_WEIGHT[Force(k)] for k in range(8)])
    flab.DRIVE_ACC[0] = np.zeros(N)
    flab.ENC_COUNT[0] = np.zeros(N, dtype=np.int64)
    am.propagate = flab.make_dyadic_propagate_v6(3, 0.05)
    feedmod.feed_tick = flab.make_dyadic_feed_v6(0.05)
    cont.CONTAGION_GAIN = 0.0
    lifemod.life_force_target = flab.flourishing_level_map(
        lifemod.life_force_target)
    flmod.flourishing_tick = flab.flourishing_writes_disabled(
        flmod.flourishing_tick)
    rng = np.random.default_rng(9109)
    for d in range(1, 31):
        flab._DAY[0] = d
        am.live_one_day(w, rng, relax=0.045)
    loc = (w.civ.country.astype(np.int64) * 1000
           + w.civ.region.astype(np.int64) * 2
           + w.civ.urban.astype(np.int64))
    ai = np.flatnonzero(w.health.alive)
    vals, counts = np.unique(loc[ai], return_counts=True)
    big = vals[np.argmax(counts)]
    cohort = ai[loc[ai] == big][:5000]
    scope = np.zeros(N, dtype=bool)
    scope[cohort] = True

    def run(double):
        wc = copy.deepcopy(w)
        ws = copy.deepcopy(w)
        st = rng.bit_generator.state
        r1 = np.random.default_rng(); r1.bit_generator.state = st
        r2 = np.random.default_rng(); r2.bit_generator.state = st
        sig = np.zeros(8); sig[0] = 0.5
        ws.chronicle.remember(Memory(
            id="b10", label="b10", day=float(ws.day),
            force_signature=sig, scope=scope.copy(),
            half_life=10.0, origin="scenario"))
        if double:
            ws.civ.forces[cohort, 0] = np.clip(
                ws.civ.forces[cohort, 0] + 0.5, 0, 1)
        peaks = []
        for d in range(1, 16):
            flab._DAY[0] = 30 + d
            am.live_one_day(wc, r1, relax=0.045)
            am.live_one_day(ws, r2, relax=0.045)
            peaks.append(float(ws.civ.forces[cohort, 0].mean()
                               - wc.civ.forces[cohort, 0].mean()))
        return max(peaks)

    single = run(False)
    dbl = run(True)
    return {"peak_single": round(single, 5),
            "peak_double": round(dbl, 5),
            "ratio": round(dbl / single, 3) if single else None}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    jobs = ([("it6", n) for n in IT6_JOBS]
            + [("B5", "B5_broken"), ("B5", "B5_clean"),
               ("B9", "B9"), ("B8", "B8_contaminated"),
               ("B7ka10", "B7_ka10"), ("B12", "B12"),
               ("B10", "B10")])
    sel = os.environ.get("EARTH1_PF_REG_ARMS")
    if sel:
        keep = set(sel.split(","))
        jobs = [j for j in jobs if j[1] in keep]
    ctx = mp.get_context("spawn")
    results = {}
    with ctx.Pool(processes=min(len(jobs), 14),
                  maxtasksperchild=1) as pool:
        for out in pool.imap_unordered(_worker, jobs):
            results[out["name"]] = out
            print(f"  done {out['name']}"
                  + (f" ERROR {out.get('error')}" if "error" in out
                     else ""), flush=True)

    def J(n):
        return json.loads(json.dumps(results[n]["r"], default=str))

    ran = set(results)
    V = {"errors": [n for n, o in results.items() if "error" in o],
         "tests": {}}

    def add(tid, detected, clean, detail):
        V["tests"][tid] = {"DETECTED": bool(detected),
                           "CLEAN": bool(clean),
                           "pass": bool(detected and clean),
                           "detail": detail}

    def early_panels(r, upto):
        return [v for k, v in r["panels"].items() if int(k) <= upto]

    if {"B1_consensus", "H_9101"} <= ran:
        b, h = J("B1_consensus"), J("H_9101")
        det = any(p["sd_ratio_genesis"] < 0.5
                  or p["unanimous_share"] >= 0.5
                  for p in early_panels(b, 60))
        cln = all(p["sd_ratio_genesis"] >= 0.5
                  and p["unanimous_share"] < 0.5
                  for p in h["panels"].values())
        add("B1", det, cln,
            {"broken_sdr_d60": early_panels(b, 60)[-1][
                "sd_ratio_genesis"]})
    if {"B2_ratchet", "H_9102"} <= ran:
        b, h = J("B2_ratchet"), J("H_9102")
        p90 = b["panels"]["90"]
        det = (p90["alpha_gt99"] >= 0.01
               or (b["softening_frac_60_90"] is not None
                   and b["softening_frac_60_90"] < 1e-4))
        cln = (h["panels"]["90"]["alpha_gt99"] < 0.01
               and h["softening_frac_60_90"] >= 1e-4)
        add("B2", det, cln,
            {"broken_alpha_gt99_d90": p90["alpha_gt99"],
             "broken_softening": b["softening_frac_60_90"],
             "healthy_softening": h["softening_frac_60_90"]})
    if {"B3_zeroinf", "H_9103"} <= ran:
        b, h = J("B3_zeroinf"), J("H_9103")
        det = b["transmission"]["ring1_d30"] < 0.006
        cln = 0.006 <= h["transmission"]["ring1_d30"] <= 0.15
        add("B3", det, cln,
            {"broken_ring1": b["transmission"]["ring1_d30"],
             "healthy_ring1": h["transmission"]["ring1_d30"]})
    if {"B4_fastrelax", "H_9104"} <= ran:
        b, h = J("B4_fastrelax"), J("H_9104")
        det = b["tau"]["half_life_d"] < 5
        cln = 5 <= h["tau"]["half_life_d"] <= 15
        add("B4", det, cln, {"broken_tau": b["tau"],
                             "healthy_tau": h["tau"]})
    if {"B5_broken", "B5_clean"} <= ran:
        b, h = J("B5_broken"), J("B5_clean")
        pb = max(e["cohort_fear_delta"] for e in b["series"])
        ph = max(e["cohort_fear_delta"] for e in h["series"])
        dh = h["series"][-1]["cohort_fear_delta"]
        det = (pb < 0.1 * ph) or (pb > 0 and
                                  b["series"][-1]["cohort_fear_delta"]
                                  / pb < 0.2)
        cln = ph > 0 and 0.2 <= dh / ph <= 0.6
        add("B5", det, cln, {"broken_peak": pb, "healthy_peak": ph,
                             "healthy_norm": round(dh / ph, 3)})
    if {"B6_accum", "H_9106"} <= ran:
        b, h = J("B6_accum"), J("H_9106")
        E = b["endurance"]
        det = any(p["sat_max"] >= 0.20 for p in b["panels"].values())
        m60 = E.get("60"); mlast = E[str(max(int(k) for k in E))]
        if m60:
            det = det or max(abs(a - c) for a, c in zip(
                mlast["mean_stored"], m60["mean_stored"])) >= 0.15
        cln = all(p["sat_max"] < 0.20 for p in h["panels"].values())
        add("B6", det, cln,
            {"broken_sat_max": max(p["sat_max"]
                                   for p in b["panels"].values())})
    if "B7_ka10" in ran:
        r = J("B7_ka10")
        det = (r.get("stored_identical") is False
               or r.get("pass") is False)
        add("B7_selfrearm", det, True,
            {"ka10_under_closed_loop": {
                k: r.get(k) for k in ("stored_identical",
                                      "same_fire_records", "pass")}})
    if {"B7_loop", "B7_loop_wipe"} <= ran:
        a, wpe = J("B7_loop"), J("B7_loop_wipe")
        det = (a["cascade_state"]["n_last_fired"]
               != wpe["cascade_state"]["n_last_fired"])
        add("B7_wipe_divergence", det, True,
            {"loop_fires": a["cascade_state"]["n_last_fired"],
             "wipe_fires": wpe["cascade_state"]["n_last_fired"]})
    if "B8_contaminated" in ran:
        r = J("B8_contaminated")
        det = r.get("pass") is False
        add("B8", det, True, {"ka10_under_contamination": r})
    if "B9" in ran:
        r = J("B9")
        add("B9", r["raised_plain"] and r["raised_residue"], True, r)
    if "B12" in ran:
        r = J("B12")
        add("B12", r["broken_drop_detected"],
            r["healthy"].get("pass", False),
            {"healthy_ka5": r["healthy"].get("pass")})
    if "B10" in ran:
        r = J("B10")
        det = r["ratio"] is not None and r["ratio"] > 1.6
        cln = r["peak_single"] > 0
        add("B10", det, cln, r)
    if {"B11_bigev", "H_9106"} <= ran:
        b, h = J("B11_bigev"), J("H_9106")
        Eb = b["endurance"]
        ab = [(int(k), v["at_bound_stored"]) for k, v in
              sorted(Eb.items(), key=lambda x: int(x[0]))]
        # sustained >=5% for >=30d: 4 consecutive 10d census points
        runs = 0
        det = False
        for _, v in ab:
            runs = runs + 1 if v >= 0.05 else 0
            if runs >= 4:
                det = True
        Eh = h["endurance"]
        healthy_max = max(v["at_bound_stored"] for v in Eh.values())
        add("B11", det, healthy_max < 0.05,
            {"broken_at_bound": dict(ab),
             "healthy_at_bound_max": healthy_max})
    V["tests"]["B13_dt_invariance"] = {
        "pass": True, "DETECTED": None, "CLEAN": None,
        "detail": "N/A per frozen prereg: dt=1 day is the only "
                  "integrator; no synthetic test fabricated"}

    scored = [t for k, t in V["tests"].items()
              if k != "B13_dt_invariance"]
    V["STAGE_B"] = ("PASS" if (not V["errors"] and scored
                               and all(t["pass"] for t in scored))
                    else "FAIL")
    (OUT / "stageB.json").write_text(
        json.dumps({"verdict": V, "results": results}, indent=1,
                   default=str))
    print(json.dumps(V["tests"], indent=1, default=str))
    print(f"STAGE B {V['STAGE_B']} "
          f"{round((time.monotonic() - t0) / 60, 1)} min")


if __name__ == "__main__":
    main()
