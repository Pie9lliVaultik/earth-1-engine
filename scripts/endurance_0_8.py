"""0.8 ACCEPTANCE — STAGE A: 365-day endogenous endurance (frozen:
ops/alive/ACCEPTANCE_BATTERY_0_8.md, Stage A section = the
sub-registration; candidate executable 1ae8740 lineage).

Three fresh preregistered seeds (9001, 9002, 9003), the frozen
candidate, NO artificial news/event stream — endogenous physics
only. Continuous dual-family measurement every 10 days.

SCORED (stored family, every seed): sat_terminal < 0.20 AND
max_t sat(t) < 0.20 every channel; sdr >= 0.5; unanimity < 50%;
alpha interior; no monotone runaway (|d mean| day 100->365 < 0.15
per channel); population plausibility reported. Effective family:
measured characterization, unscored (first census).
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
                          str(ROOT / "data" / "acceptance_0_8" /
                              "stageA")))
DAYS = int(os.environ.get("EARTH1_STAGEA_DAYS", "365"))
SEEDS = tuple(int(x) for x in os.environ.get(
    "EARTH1_STAGEA_SEEDS", "9001,9002,9003").split(","))
BASE = dict(op="canon", cnv="canon", flr=False, cas=False,
            relax=0.045, days=DAYS, no_fork=True, endurance=True)
ARMS = {f"END_{s}": dict(BASE, seed=s) for s in SEEDS}


def _worker(name):
    try:
        import scripts.it6_dyadic as it6
        it6.ARMS.update(ARMS)
        return {"name": name, "r": it6.run_arm(name)}
    except Exception as e:
        import traceback
        return {"name": name, "error": str(e),
                "trace": traceback.format_exc()[-2000:]}


def _score(r):
    g = {}
    P = r["panels"]
    E = r["endurance"]
    last = str(max(int(k) for k in P))
    sats = [P[k]["sat_max"] for k in P]
    g["sat_terminal_lt_20"] = P[last]["sat_max"] < 0.20
    g["sat_max_t_lt_20"] = max(sats) < 0.20
    g["sdr_ge_05"] = P[last]["sd_ratio_genesis"] >= 0.5
    g["unanimity_lt_50"] = all(P[k]["unanimous_share"] < 0.50
                               for k in P)
    g["alpha_interior"] = (P[last]["alpha_gt99"] < 0.01
                           and P[last]["alpha_floor"] < 0.01)
    m100 = E.get("100")
    mlast = E[str(max(int(k) for k in E))]
    if m100:
        drift = [abs(a - b) for a, b in
                 zip(mlast["mean_stored"], m100["mean_stored"])]
        g["no_runaway_lt_015"] = max(drift) < 0.15
    pop0 = E[str(min(int(k) for k in E))]["alive"]
    stats = {
        "sat_stored_max_t": round(max(sats), 4),
        "sat_stored_terminal": P[last]["sat_max"],
        "sat_eff_max_t": round(max(max(v["sat_eff"]) for v in
                                   E.values()), 4),
        "sat_eff_terminal": max(mlast["sat_eff"]),
        "population_start_end": [pop0, mlast["alive"]],
        "residues_end": mlast["n_residues"],
        "fired_cum_end": mlast["fired_cum"],
        "memories_end": mlast["memories"],
        "employment_end": mlast["employment"],
        "at_bound_stored_end": mlast["at_bound_stored"],
        "overlay_clip_frac_end": mlast["overlay_clip_frac"],
        "drift_100_end_max": round(max(drift), 4) if m100 else None,
    }
    return g, stats


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    ctx = mp.get_context("spawn")
    results = {}
    with ctx.Pool(processes=len(ARMS), maxtasksperchild=1) as pool:
        for out in pool.imap_unordered(_worker, list(ARMS)):
            results[out["name"]] = out
            print(f"  done {out['name']}"
                  + (f" ERROR {out.get('error')}" if "error" in out
                     else ""), flush=True)
    V = {"errors": [n for n, o in results.items() if "error" in o],
         "seeds": {}}
    for n, o in results.items():
        if "error" in o:
            continue
        g, stats = _score(json.loads(json.dumps(o["r"])))
        V["seeds"][n] = {"gates": g, "stats": stats,
                         "pass": all(g.values())}
    V["STAGE_A"] = ("PASS" if (not V["errors"] and V["seeds"]
                               and all(s["pass"] for s in
                                       V["seeds"].values()))
                    else "FAIL")
    (OUT / "endurance.json").write_text(
        json.dumps({"verdict": V, "results": results}, indent=1,
                   default=str))
    print(json.dumps(V, indent=1, default=str))
    print(f"STAGE A {V['STAGE_A']} "
          f"{round((time.monotonic() - t0) / 60, 1)} min")


if __name__ == "__main__":
    main()
