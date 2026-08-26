"""Benchmark B runner (BENCHMARK_B_PREREG_v1.md @29fa296).
Stages: warm | arm <name> <repeat> | score. One process per (arm,repeat).
Arms: control365 control540 covid_2020 gfc_2008 arab_spring_2011 placebo.
"""
import copy, json, os, subprocess, sys, time
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from earth1.alive import birth_world, live_one_day, PHYSICS_VERSION
from earth1.backtest import REGISTRY, ranking_check, score
from earth1.branch import Scenario, apply
from earth1.consequences import snapshot, compare
from earth1 import persistence
OUT = "/opt/earth1-data/benchmark_b"; os.makedirs(OUT, exist_ok=True)
POP, WARM, REPEATS, SEED_BASE = 200_000, 90, 5, 977 * 13
EV = {e.id: e for e in REGISTRY}
HORIZON = {"covid_2020": 365, "gfc_2008": 540, "arab_spring_2011": 540, "placebo": 365,
           "control365": 365, "control540": 540}
PLACEBO = Scenario(id="placebo", label="zero scenario", forces={}, countries=None,
                   firm_damage=0.0, trade_shock=0.0, persists_days=365)


def stamp():
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    return {"commit": sha, "physics_version": PHYSICS_VERSION, "pop": POP, "warm": WARM,
            "repeats": REPEATS, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def run_warm():
    w = birth_world(POP, 42); rng = np.random.default_rng(42)
    for _ in range(WARM):
        live_one_day(w, rng)
    persistence.save_world(w, os.path.join(OUT, "warm.pkl"), rng=rng)
    json.dump({**stamp(), "world_hash": persistence.world_hash(w)}, open(os.path.join(OUT, "warm_meta.json"), "w"), indent=1)
    print("WARM SAVED", persistence.world_hash(w)[:16])


def run_arm(arm, rep):
    w, _rs, _ = persistence.load_world(os.path.join(OUT, "warm.pkl"))
    rng = np.random.default_rng(SEED_BASE + rep)          # CRN across arms
    days = HORIZON[arm]
    sc = None if arm.startswith("control") else (PLACEBO if arm == "placebo" else EV[arm].scenario)
    if sc is not None:
        apply(w, sc, rng)
    path = []
    from earth1.genesis import census_weights
    cw = census_weights(w.civ)
    for d in range(days):
        live_one_day(w, rng)
        lf = w.life.in_lf & w.health.alive
        path.append(float(cw[(~w.life.employed) & lf].sum()))
    snap = snapshot(w)
    rep_out = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in snap.items()}
    json.dump({"arm": arm, "repeat": rep, "days": days, "snapshot": rep_out, "jobless_path_tail": path[-30:],
               **stamp()}, open(os.path.join(OUT, f"{arm}_r{rep}.json"), "w"), indent=1)
    # keep the world for compare() (protest_risk needs w) — save small marker instead; compare rerun in score via saved snapshot only
    if arm == "arab_spring_2011":
        from earth1.consequences import protest_risk
        json.dump({"protest_risk": protest_risk(w).tolist()}, open(os.path.join(OUT, f"{arm}_r{rep}_protest.json"), "w"))
    print("ARM DONE", arm, rep)


def _snap(arm, rep):
    d = json.load(open(os.path.join(OUT, f"{arm}_r{rep}.json")))
    return {k: (np.array(v) if isinstance(v, list) else v) for k, v in d["snapshot"].items()}


class _WStub:
    pass


def run_score():
    from earth1.benchmark_a import scoring as SC
    res = {"stamp": stamp(), "events": {}, "gates": {}}
    scale_note = "census-weighted people, already scaled by census_weights"
    ctrl = {365: [_snap("control365", r) for r in range(REPEATS)], 540: [_snap("control540", r) for r in range(REPEATS)]}
    effects = {}
    for ev in ("covid_2020", "gfc_2008", "arab_spring_2011", "placebo"):
        days = HORIZON[ev]; per_rep = []
        for r in range(REPEATS):
            b = _snap(ev, r); c = ctrl[days][r]
            eff = {
                "jobs_lost": float(np.maximum((b["jobless_by_country"] - c["jobless_by_country"]), 0).sum()),
                "jobs_net": float((b["jobless_by_country"] - c["jobless_by_country"]).sum()),
                "destitution": float(b["destitute"] - c["destitute"]),
                "excess_deaths": float(b["dead"] - c["dead"]),
                "displaced": float(b["migrants"] - c["migrants"]),
                "hope_change": float(b.get("mean_hope", 0) - c.get("mean_hope", 0)),
                "gov_at_risk": float(np.sum((b["legitimacy"] < 0.25) & ((c["legitimacy"] - b["legitimacy"]) > 0.02))),
                "jobs_vector": (b["jobless_by_country"] - c["jobless_by_country"]).tolist(),
            }
            per_rep.append(eff)
        effects[ev] = per_rep
        agg = {k: SC.bootstrap_ci([p[k] for p in per_rep]) for k in per_rep[0] if k != "jobs_vector"}
        res["events"][ev] = {"per_repeat": [{k: v for k, v in p.items() if k != "jobs_vector"} for p in per_rep], "ci": agg}
    # direction
    dirs = {"covid_2020": {"jobs": ("jobs_lost", "+"), "poverty": ("destitution", "+"), "hope": ("hope_change", "-"), "deaths": ("excess_deaths", "+")},
            "gfc_2008": {"jobs": ("jobs_lost", "+"), "poverty": ("destitution", "+"), "hope": ("hope_change", "-")},
            "arab_spring_2011": {"govs": ("gov_at_risk", "+"), "displacement": ("displaced", "+"), "poverty": ("destitution", "+")}}
    dir_rows = []
    for ev, fam in dirs.items():
        got = {}
        for name, (k, sgn) in fam.items():
            med = float(np.median([p[k] for p in effects[ev]]))
            got[name] = bool(med > 0 if sgn == "+" else med < 0)
        res["events"][ev]["direction"] = got
        dir_rows += list(got.values())
    dir_pct = 100 * np.mean(dir_rows)
    res["gates"]["direction"] = {"pct": float(dir_pct), "per_event": {ev: 100 * np.mean(list(res["events"][ev]["direction"].values())) for ev in dirs},
                                 "ACCEPT_75": bool(dir_pct >= 75), "GOOD_85": bool(dir_pct >= 85)}
    # magnitude vs LOO-exposure baseline (jobs; displacement for arab)
    workers = {365: float(np.mean([c["workers_by_country"].sum() for c in ctrl[365]])), 540: float(np.mean([c["workers_by_country"].sum() for c in ctrl[540]]))}
    anchors = {"covid_2020": ("jobs_lost", 2.55e8, EV["covid_2020"].scenario.firm_damage),
               "gfc_2008": ("jobs_lost", 3.0e7, EV["gfc_2008"].scenario.firm_damage),
               "arab_spring_2011": ("displaced", 3.0e6, EV["arab_spring_2011"].scenario.firm_damage)}
    def exposure(ev):
        sc = EV[ev].scenario; days = HORIZON[ev]
        n = workers[days]
        if sc.countries is not None:
            # exposed share by country membership of the workforce
            c0 = ctrl[days][0]
            from earth1.genesis import GENESIS_COUNTRY_CODES as CODES
            idx = [CODES.index(x) for x in sc.countries if x in CODES]
            n = float(np.mean([c["workers_by_country"][idx].sum() for c in ctrl[days]]))
        return anchors[ev][2] * n * (days / 365.0)
    errs_e1, errs_base = {}, {}
    for ev, (k, rec, _) in anchors.items():
        others = [o for o in anchors if o != ev]
        ks = [anchors[o][1] / exposure(o) for o in others]
        k_loo = float(np.exp(np.mean(np.log(ks))))
        base_pred = k_loo * exposure(ev)
        e1_pred = float(np.median([p[k] for p in effects[ev]]))
        errs_e1[ev] = abs(np.log10(max(e1_pred, 1.0)) - np.log10(rec))
        errs_base[ev] = abs(np.log10(max(base_pred, 1.0)) - np.log10(rec))
        res["events"][ev]["magnitude"] = {"anchor": rec, "e1": e1_pred, "loo_exposure_baseline": base_pred,
                                          "e1_log10_err": errs_e1[ev], "baseline_log10_err": errs_base[ev]}
    res["gates"]["magnitude"] = {"e1_median_log10_err": float(np.median(list(errs_e1.values()))),
                                 "baseline_median_log10_err": float(np.median(list(errs_base.values()))),
                                 "pass": bool(np.median(list(errs_e1.values())) < np.median(list(errs_base.values())))}
    # proportionality + discrimination
    means = {ev: float(np.mean([p["jobs_lost"] for p in effects[ev]])) for ev in dirs}
    sds = {ev: float(np.std([p["jobs_lost"] for p in effects[ev]])) for ev in dirs}
    order = sorted(dirs, key=lambda e: -means[e])
    pooled_sd = float(np.mean(list(sds.values())))
    gaps = [means[order[i]] - means[order[i + 1]] for i in range(len(order) - 1)]
    res["gates"]["proportionality"] = {"expected": ["covid_2020", "gfc_2008", "arab_spring_2011"], "got": order,
                                       "order_correct": order == ["covid_2020", "gfc_2008", "arab_spring_2011"],
                                       "min_gap_over_2sd": bool(min(gaps) > 2 * pooled_sd), "gaps": gaps, "pooled_sd": pooled_sd,
                                       "pass": bool(order == ["covid_2020", "gfc_2008", "arab_spring_2011"] and min(gaps) > 2 * pooled_sd)}
    # placebo
    pl = effects["placebo"]; small = min(abs(means[e]) for e in dirs)
    pl_ok = []
    for k in ("jobs_lost", "destitution", "excess_deaths", "displaced"):
        ci = SC.bootstrap_ci([p[k] for p in pl]); med = abs(float(np.median([p[k] for p in pl])))
        pl_ok.append((ci[1] <= 0 <= ci[2]) or med < 0.05 * small)
        res["events"]["placebo"].setdefault("gate_detail", {})[k] = {"ci": ci, "median": med, "threshold": 0.05 * small}
    res["gates"]["placebo"] = {"pass": bool(all(pl_ok))}
    # coverage (leave-one-repeat-out, 80% nominal)
    hits = tot = 0
    for ev in dirs:
        for k in ("jobs_lost", "destitution"):
            v = np.array([p[k] for p in effects[ev]])
            for i in range(len(v)):
                rest = np.delete(v, i)
                lo, hi = np.quantile(rest, 0.10), np.quantile(rest, 0.90)
                hits += int(lo <= v[i] <= hi); tot += 1
    cov = 100 * hits / tot
    res["gates"]["coverage"] = {"empirical_pct": float(cov), "pass": bool(70 <= cov <= 90)}
    # geography eligibility
    geo = {}
    from scipy.stats import spearmanr
    for ev in dirs:
        V = np.array([p_full for p_full in ([e["jobs_vector"] for e in effects[ev]])])
        rhos = [float(spearmanr(V[i], V[j]).statistic) for i in range(len(V)) for j in range(i + 1, len(V))]
        geo[ev] = {"median_repeat_spearman": float(np.median(rhos)), "eligible": bool(np.median(rhos) >= 0.5)}
    res["gates"]["geography"] = {**geo, "claimed": {ev: g["eligible"] for ev, g in geo.items()}}
    n_pass = sum(bool(res["gates"][g].get("pass", res["gates"][g].get("ACCEPT_75"))) for g in ("direction", "magnitude", "proportionality", "placebo", "coverage"))
    res["overall"] = {"gates_passed": n_pass, "of": 5,
                      "PASS": bool(res["gates"]["direction"]["ACCEPT_75"] and res["gates"]["magnitude"]["pass"] and res["gates"]["proportionality"]["pass"] and res["gates"]["placebo"]["pass"])}
    json.dump(res, open(os.path.join(OUT, "scoreboard_b.json"), "w"), indent=1)
    print(json.dumps({"direction": res["gates"]["direction"], "magnitude": res["gates"]["magnitude"]["pass"], "proportionality": res["gates"]["proportionality"]["pass"], "placebo": res["gates"]["placebo"]["pass"], "coverage": res["gates"]["coverage"], "overall": res["overall"]}, indent=1))


if __name__ == "__main__":
    a = sys.argv[1]
    if a == "warm": run_warm()
    elif a == "arm": run_arm(sys.argv[2], int(sys.argv[3]))
    elif a == "score": run_score()
