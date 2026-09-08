#!/usr/bin/env python3
"""AUDIT ITEM 5 verification — Experience Loop v0.2 scorer / filter-arm gates.

Situation established by inspection (see JSON output "provenance"):
  * The registered scorer (scripts/exploop/run_v0.py, stage_score) NOW includes
    the filter arm: commits ac6d35d (2026-08-31 17:28:53 +0200) and 25b956b
    (2026-08-31 17:29:15 +0200) added the filter arm to the scored-arms list,
    compute G1c (filter vs exp) and G7' (placebo vs exp) with the SAME paired
    method as G1, and fold both into the v0.2 verdict formula.  The working
    tree is clean; the "owed" patch is already paid in-repo.
  * The per-arm inputs stage_score needs (per-seed arm files + truth streams
    under the run's output root, default /opt/earth1-data/exploop_v02/) do NOT
    exist on this machine — /opt/earth1-data is absent entirely (it is the
    "prime" host per multiple ops/alive reports).  So the scoring stage cannot
    be re-run here, and the filter-arm gates G1c/G7' cannot be recomputed.
  * Therefore: verify what IS recomputable from data/cycles/v02_report.json
    alone, against the published audit row (ops/alive/CALIBRATION_CYCLES.md
    line 32).

Checks performed here:
  A. Structural: the stored report has NO G1c / G7prime keys and NO filter
     curve -> confirms it was emitted by the PRE-patch scorer (workaround note
     on the record is accurate).
  B. Verbatim gate cross-checks: report values vs the published row
     (G1, G1b, G8, G2, G3, G4).
  C. Wilcoxon p-value structure: paired sign-rank p-values must be integer
     multiples of 2^-16 for n=16 paired worlds; the G1 p equals the minimum
     attainable two-sided value (all 16 differences one sign), consistent with
     the published "positive in 16/16 WS worlds" claim for the same battery.
  D. Late-window curve consistency: exp late-mean must reproduce the published
     0.216; log-ratios of late-window curve means must sit near the published
     paired mean-log gates (Jensen-level agreement expected, not equality,
     because the gates are per-seed paired means of logs while the report
     stores cross-seed mean curves).
  E. Filter-arm arithmetic of the published row itself: 1.04/0.216 ratio and
     its log vs the published +1.51 paired estimate (consistency of the
     published numbers with the stored exp curve; the filter side is NOT in
     the report — that is exactly the audit gap).
  F. Naive vs naive_forced curves must be identical before the repeat-shock
     cycles and diverge (forced <= naive) only at the repeat-shock cycles.
  G. Missing-artifact inventory: exact per-arm/stream paths stage_score would
     open, none of which exist locally.

Sources:
  R  = /Users/pietronovelli/Documents/GitHub/earth-1-engine/data/cycles/v02_report.json
  S  = /Users/pietronovelli/Documents/GitHub/earth-1-engine/scripts/exploop/run_v0.py
  C  = /Users/pietronovelli/Documents/GitHub/earth-1-engine/ops/alive/CALIBRATION_CYCLES.md (line 32)
Published row values below are transcribed verbatim from C line 32.
"""
import json
import math
import os

ENG = "/Users/pietronovelli/Documents/GitHub/earth-1-engine"
REPORT = os.path.join(ENG, "data/cycles/v02_report.json")
OUTJSON = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "learning_scorer_check.json")

# ---- published values, verbatim from ops/alive/CALIBRATION_CYCLES.md:32 ----
PUB = {
    "G1c_mean_log": 1.51, "G1c_ci": [1.21, 1.81], "G1c_p": 3e-5,
    "G1c_positive_worlds": "16/16",
    "exp_late": 0.216, "filter_late": 1.04, "ratio": 4.8,
    "G1_mean_log": 2.16,            # "+2.16 p<1e-4"
    "G1b_mean_log": 0.55, "G1b_ci": [0.32, 0.77], "G1b_p": 2e-4,
    "G8_mean_log": 0.59, "G8_p": 1e-4,
    "G7prime_mean_log": 2.08, "G7prime_p": 3e-5,
    "G2_cover": 0.963,
    "G3_u_err": [0.006, 0.034],
    "G4": "4/4",
}

# ---- experiment shape, from the runner script (full-run branch) ----
# run_v0.py:35-43 -> v0.2: 20 worlds, last 4 misspecified => 16 WS; 24 cycles;
# late window = second half of cycles (run_v0.py:379).
N_WORLDS, N_MIS, N_CYCLES = 20, 4, 24
N_WS = N_WORLDS - N_MIS
LATE = slice(N_CYCLES // 2, N_CYCLES)
REPEAT_SHOCK_CYCLES = (16, 17)   # run_v0.py:46 (second pair; first pair 8,9)
SEED_BASE = 9201                 # run_v0.py:35 (v0.2 branch)
OUT_ROOT = "/opt/earth1-data/exploop_v02"   # run_v0.py:29-32 default for v0.2
ARMS = ("frozen", "exp", "placebo", "filter")

rep = json.load(open(REPORT))
res = {"report_file": REPORT, "published_row":
       os.path.join(ENG, "ops/alive/CALIBRATION_CYCLES.md") + ":32"}

# ---------- A. structural ----------
keys = list(rep.keys())
res["A_structure"] = {
    "report_keys": keys,
    "has_G1c_key": any("G1c" in k for k in keys),
    "has_G7prime_key": any("G7prime" in k for k in keys),
    "curves_ws_arms": sorted(rep["curves_ws"].keys()),
    "has_filter_curve": "filter" in rep["curves_ws"],
    "conclusion": ("report emitted by PRE-patch scorer (no G1c/G7prime keys, "
                   "no filter curve) — matches the audit note"),
}

# ---------- B. verbatim gate cross-checks ----------
def close(a, b, tol):
    return abs(a - b) <= tol

g1 = rep["G1_frozen_minus_exp"]
g1b = rep["G1b_naive_minus_exp"]
g8 = rep["G8_shock_cycles_naive_minus_exp"]
g7 = rep["G7_frozen_minus_placebo"]
res["B_verbatim"] = {
    "G1_mean_log": {"report": g1["mean_log"], "published": PUB["G1_mean_log"],
                    "match_2dp": close(g1["mean_log"], PUB["G1_mean_log"], 0.005)},
    "G1_p": {"report": g1["p_wilcoxon"], "published_bound": "p<1e-4",
             "match": g1["p_wilcoxon"] < 1e-4},
    "G1b_mean_log": {"report": g1b["mean_log"], "published": PUB["G1b_mean_log"],
                     "match_2dp": close(g1b["mean_log"], PUB["G1b_mean_log"], 0.005)},
    "G1b_ci": {"report": g1b["ci"], "published": PUB["G1b_ci"],
               "match_2dp": all(close(a, b, 0.005)
                                for a, b in zip(g1b["ci"], PUB["G1b_ci"]))},
    "G1b_p": {"report": g1b["p_wilcoxon"], "published": PUB["G1b_p"],
              "match_1sf": close(g1b["p_wilcoxon"], PUB["G1b_p"], 0.5e-4)},
    "G8_mean_log": {"report": g8["mean_log"], "published": PUB["G8_mean_log"],
                    "match_2dp": close(g8["mean_log"], PUB["G8_mean_log"], 0.005)},
    "G8_p": {"report": g8["p_wilcoxon"], "published": PUB["G8_p"],
             "match_1sf": close(g8["p_wilcoxon"], PUB["G8_p"], 0.5e-4)},
    "G2_cover": {"report": rep["G2_cover90_late"], "published": PUB["G2_cover"],
                 "match_3dp": close(rep["G2_cover90_late"], PUB["G2_cover"], 0.0005)},
    "G3_u_err": {"report": rep["G3_recovery"]["mean_abs_u_err"],
                 "published": PUB["G3_u_err"],
                 "match": all(close(a, b, 0.0005) for a, b in
                              zip(rep["G3_recovery"]["mean_abs_u_err"],
                                  PUB["G3_u_err"]))},
    "G4": {"report": rep["G4_no_false_learning_mis"]["mis_coverage"],
           "published": PUB["G4"],
           "match": sum(rep["G4_no_false_learning_mis"]["mis_coverage"]) == 4
                    and len(rep["G4_no_false_learning_mis"]["mis_coverage"]) == 4},
    "G7_null_as_respecified": {"report_mean_log": g7["mean_log"],
                               "report_p": g7["p_wilcoxon"],
                               "ci_spans_zero": g7["ci"][0] < 0 < g7["ci"][1]},
    "verdict_flag": rep["EXPERIENTIAL_LEARNING_DEMONSTRATED"],
}

# ---------- C. Wilcoxon p structure (n=16 paired worlds) ----------
def p_struct(p):
    m = p * (2 ** 16)
    return {"p": p, "p_times_2pow16": m,
            "integer_multiple_of_2pow-16": close(m, round(m), 1e-9),
            "is_min_two_sided_n16": close(p, 2.0 / 2 ** 16, 1e-12)}

res["C_wilcoxon_structure"] = {
    "n_ws_worlds": N_WS,
    "G1": p_struct(g1["p_wilcoxon"]),
    "G1b": p_struct(g1b["p_wilcoxon"]),
    "G8": p_struct(g8["p_wilcoxon"]),
    "note": ("min two-sided sign-rank p for n=16 is 2/2^16 = 3.0517578125e-05;"
             " G1 attains it => all 16 paired differences one sign. The"
             " published G1c p=3e-5 equals the same minimum, consistent with"
             " the published 'positive in 16/16 WS worlds'."),
}

# ---------- D. late-window curve consistency ----------
cw = rep["curves_ws"]
late_mean = {a: sum(cw[a][LATE]) / len(cw[a][LATE]) for a in cw}
def logratio(hi, lo):
    return math.log(late_mean[hi] / late_mean[lo])

res["D_late_window"] = {
    "cycles": f"{N_CYCLES//2}..{N_CYCLES-1}",
    "late_means": late_mean,
    "exp_late_vs_published": {
        "computed": late_mean["exp"], "published": PUB["exp_late"],
        "match_3dp": close(late_mean["exp"], PUB["exp_late"], 0.0005)},
    "log_ratio_frozen_exp": {"computed": logratio("frozen", "exp"),
                             "paired_gate_G1": g1["mean_log"],
                             "abs_gap": abs(logratio("frozen", "exp") - g1["mean_log"])},
    "log_ratio_placebo_exp": {"computed": logratio("placebo", "exp"),
                              "published_paired_G7prime": PUB["G7prime_mean_log"],
                              "abs_gap": abs(logratio("placebo", "exp")
                                             - PUB["G7prime_mean_log"])},
    "log_ratio_naive_exp": {"computed": logratio("naive", "exp"),
                            "paired_gate_G1b": g1b["mean_log"],
                            "abs_gap": abs(logratio("naive", "exp") - g1b["mean_log"])},
    "note": ("gates are per-seed paired means of log-CRPS differences; report"
             " stores cross-seed mean curves, so log-of-means only ballparks"
             " the paired estimates (Jensen gap expected, same sign/scale)"),
}

# ---------- E. filter-arm arithmetic of the published row ----------
impl_ratio = PUB["filter_late"] / late_mean["exp"]
res["E_filter_row_arithmetic"] = {
    "published_filter_late": PUB["filter_late"],
    "computed_exp_late": late_mean["exp"],
    "implied_ratio": impl_ratio,
    "published_ratio": PUB["ratio"],
    "ratio_match_1dp": close(impl_ratio, PUB["ratio"], 0.05),
    "log_implied_ratio": math.log(impl_ratio),
    "published_paired_G1c": PUB["G1c_mean_log"],
    "within_published_ci": PUB["G1c_ci"][0] <= math.log(impl_ratio) <= PUB["G1c_ci"][1],
    "note": ("filter late-mean 1.04 comes from the published row, NOT from the"
             " report file (no filter curve stored) — this is the exact"
             " unverifiable-locally piece"),
}

# ---------- F. naive vs naive_forced divergence pattern ----------
nv, nf = cw["naive"], cw["naive_forced"]
diff_cycles = [c for c in range(N_CYCLES) if nv[c] != nf[c]]
res["F_naive_forced_pattern"] = {
    "cycles_differing": diff_cycles,
    "expected_repeat_shock_cycles_among_them": list(REPEAT_SHOCK_CYCLES),
    "forced_leq_naive_at_repeat_shocks": all(nf[c] <= nv[c]
                                             for c in REPEAT_SHOCK_CYCLES),
    "identical_before_first_repeat_shock": nv[:16] == nf[:16],
}

# ---------- G. missing-artifact inventory ----------
missing = []
for s in range(SEED_BASE, SEED_BASE + N_WORLDS):
    for a in ARMS:
        p = os.path.join(OUT_ROOT, "arms", f"{s}_{a}.json")
        if not os.path.exists(p) and not os.path.exists(
                p.replace(".json", ".orig.json")):
            missing.append(p)
    sp = os.path.join(OUT_ROOT, "streams", f"{s}.json")
    if not os.path.exists(sp):
        missing.append(sp)
res["G_missing_artifacts"] = {
    "out_root": OUT_ROOT,
    "out_root_exists": os.path.isdir(OUT_ROOT),
    "n_required_files_missing": len(missing),
    "n_required_files_total": N_WORLDS * len(ARMS) + N_WORLDS,
    "first_missing_examples": missing[:3],
    "rescore_feasible_locally": len(missing) == 0,
}

# ---------- provenance of the scorer patch ----------
res["provenance"] = {
    "scorer": os.path.join(ENG, "scripts/exploop/run_v0.py"),
    "patch_commits": {
        "ac6d35d": "2026-08-31 17:28:53 +0200 — scorer includes filter arm "
                   "(G1c) + re-specified G7prime + v0.2 verdict formula",
        "25b956b": "2026-08-31 17:29:15 +0200 — crps dict built from full "
                   "arms list (filter included)"},
    "report_mtime_before_patch": "v02_report.json written 2026-08-31 16:40 "
                                 "(pre-patch scorer output)",
    "working_tree": "clean for the scorer file (patch is committed, not "
                    "pending)",
}

# ---------- overall ----------
checks = [
    res["A_structure"]["has_G1c_key"] is False,
    res["A_structure"]["has_filter_curve"] is False,
    res["B_verbatim"]["G1_mean_log"]["match_2dp"],
    res["B_verbatim"]["G1b_mean_log"]["match_2dp"],
    res["B_verbatim"]["G1b_ci"]["match_2dp"],
    res["B_verbatim"]["G8_mean_log"]["match_2dp"],
    res["B_verbatim"]["G2_cover"]["match_3dp"],
    res["B_verbatim"]["G3_u_err"]["match"],
    res["B_verbatim"]["G4"]["match"],
    res["C_wilcoxon_structure"]["G1"]["is_min_two_sided_n16"],
    res["D_late_window"]["exp_late_vs_published"]["match_3dp"],
    res["E_filter_row_arithmetic"]["ratio_match_1dp"],
    res["E_filter_row_arithmetic"]["within_published_ci"],
    res["F_naive_forced_pattern"]["forced_leq_naive_at_repeat_shocks"],
    res["F_naive_forced_pattern"]["identical_before_first_repeat_shock"],
]
res["overall"] = {
    "n_checks": len(checks), "n_pass": sum(checks),
    "all_consistency_checks_pass": all(checks),
    "gates_reproduced_exactly": False,
    "why_not": ("G1c/G7' need the per-seed filter/exp/placebo arm files under "
                f"{OUT_ROOT} (prime host); absent on this machine"),
}

json.dump(res, open(OUTJSON, "w"), indent=1)
print(json.dumps(res["overall"], indent=1))
print(json.dumps(res["D_late_window"]["exp_late_vs_published"], indent=1))
print(json.dumps(res["E_filter_row_arithmetic"], indent=1))
print(json.dumps(res["C_wilcoxon_structure"]["G1"], indent=1))
print(json.dumps(res["G_missing_artifacts"], indent=1))
