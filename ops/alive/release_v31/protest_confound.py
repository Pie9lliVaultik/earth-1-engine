#!/usr/bin/env python3
"""AUDIT ITEM 2: wealth-confound re-score of the protest-onset register.

Question: the quiet controls in RETRODICTION v1 are all rich stable states,
so the pooled null-arm Spearman rho=0.552 (p=0.0052) may be a wealth proxy.
Re-score with income group controlled.

Data sources
------------
1. Register table (country, outcome class, P(onset) scenario arm, P(onset)
   null arm): transcribed verbatim from
   /Users/pietronovelli/Documents/GitHub/earth-1-engine/ops/alive/RETRODICTION_v1.md
   lines 14-37 (12 WAVE positives, 12 quiet controls).
2. Income group per ISO2: the engine repo's own country table
   (earth1/census.py, CENSUS_TARGETS[*]["income"]) — the same tier map the
   C2+ substrate pooling uses. Imported live below and additionally
   hard-copied into EXPECTED_INCOME_REPO with an equality assertion, so the
   JSON output lists the map in full for checking. This map matches the
   World Bank FY2020/21-era classification (event window ~2019-2022).
3. Robustness variant: World Bank income group, FY2011 classification,
   transcribed from analyst knowledge (based on 2009 GNI per capita, Atlas
   method). Boundary cases flagged in the JSON.

Methods (in order of strength)
------------------------------
M1. Partial Spearman of (null-arm P(onset), outcome) controlling for income
    group (ordinal LIC=1..HIC=4), with permutation p-values: 10,000
    Monte-Carlo label shuffles WITHIN income strata, plus EXACT enumeration
    of the full within-stratum permutation group (which is tiny: only
    strata containing both classes contribute distinct assignments).
M2. Within-stratum comparison: per-stratum means/n for positives vs
    controls; exact stratified Mann-Whitney (enumeration) — informative
    strata only.
M3. Blunt check: Spearman of null-arm P(onset) against income group alone,
    and Spearman(outcome, income) = the size of the confound itself.

Small-n honesty: exact n per stratum reported; the permutation-group size
is reported so no p-value is claimed below its attainable granularity.
"""
import itertools
import json
import sys

import numpy as np
from scipy import stats

OUT = ("/private/tmp/claude-501/-Users-pietronovelli-Documents-GitHub-vaultik-x/"
       "e30708db-e208-4f7c-aad1-c0be9c88f760/scratchpad/audit_v31/"
       "protest_confound.json")

# ---------------------------------------------------------------- register
# RETRODICTION_v1.md lines 14-37, verbatim.
REGISTER = [
    # iso2, outcome(1=WAVE,0=quiet), p_scenario, p_null
    ("IR", 1, 0.875, 1.000),
    ("LK", 1, 0.125, 0.375),
    ("KZ", 1, 0.125, 0.500),
    ("CL", 1, 0.875, 0.750),
    ("CO", 1, 0.625, 0.875),
    ("FR", 1, 0.000, 0.000),
    ("NG", 1, 0.000, 0.000),
    ("KE", 1, 0.000, 0.375),
    ("BD", 1, 0.000, 0.000),
    ("PE", 1, 0.375, 0.875),
    ("EC", 1, 0.000, 0.250),
    ("IQ", 1, 0.000, 0.000),
    ("CH", 0, 0.000, 0.000),
    ("PT", 0, 0.000, 0.000),
    ("UY", 0, 0.250, 0.125),
    ("JP", 0, 0.000, 0.125),
    ("SG", 0, 0.125, 0.125),
    ("NO", 0, 0.000, 0.000),
    ("DK", 0, 0.000, 0.000),
    ("NZ", 0, 0.000, 0.000),
    ("CA", 0, 0.000, 0.000),
    ("AU", 0, 0.000, 0.000),
    ("IE", 0, 0.000, 0.000),
    ("FI", 0, 0.000, 0.000),
]
ISO = [r[0] for r in REGISTER]
outcome = np.array([r[1] for r in REGISTER], float)
p_scen = np.array([r[2] for r in REGISTER], float)
p_null = np.array([r[3] for r in REGISTER], float)

# ------------------------------------------------------------- income maps
# Hard copy of the engine repo's tier map for the 24 register countries
# (earth1/census.py CENSUS_TARGETS[*]["income"]); asserted against the live
# import below.
EXPECTED_INCOME_REPO = {
    "IR": "LMIC", "LK": "LMIC", "KZ": "UMIC", "CL": "HIC", "CO": "UMIC",
    "FR": "HIC", "NG": "LMIC", "KE": "LMIC", "BD": "LMIC", "PE": "UMIC",
    "EC": "UMIC", "IQ": "UMIC", "CH": "HIC", "PT": "HIC", "UY": "HIC",
    "JP": "HIC", "SG": "HIC", "NO": "HIC", "DK": "HIC", "NZ": "HIC",
    "CA": "HIC", "AU": "HIC", "IE": "HIC", "FI": "HIC",
}
sys.path.insert(0, "/Users/pietronovelli/Documents/GitHub/earth-1-engine")
from earth1.census import CENSUS_TARGETS  # noqa: E402  (read-only import)

live_map = {c["iso2"]: c["income"] for c in CENSUS_TARGETS}
income_repo = {iso: live_map[iso] for iso in ISO}
assert income_repo == EXPECTED_INCOME_REPO, "repo tier map drifted"

# World Bank FY2011 classification (2009 GNI p.c., Atlas), transcribed.
# Boundary notes: EC 2009 GNI ~ $3,940 vs LMIC/UMIC cut $3,945 -> LMIC
# (WB FY2011 list had Ecuador LMIC; it moved to UMIC shortly after).
# IQ was LMIC in FY2011 (UMIC from ~FY2013). CL, UY were UMIC (HIC from
# FY2013). IR was UMIC in FY2011 (dropped to LMIC ~FY2020). KE, BD were LIC
# (LMIC from FY2015/16).
INCOME_FY2011 = {
    "IR": "UMIC", "LK": "LMIC", "KZ": "UMIC", "CL": "UMIC", "CO": "UMIC",
    "FR": "HIC", "NG": "LMIC", "KE": "LIC", "BD": "LIC", "PE": "UMIC",
    "EC": "LMIC", "IQ": "LMIC", "CH": "HIC", "PT": "HIC", "UY": "UMIC",
    "JP": "HIC", "SG": "HIC", "NO": "HIC", "DK": "HIC", "NZ": "HIC",
    "CA": "HIC", "AU": "HIC", "IE": "HIC", "FI": "HIC",
}
ORD = {"LIC": 1, "LMIC": 2, "UMIC": 3, "HIC": 4}

RNG_SEED = 20260908
N_PERM = 10_000


# ------------------------------------------------------------------ helpers
def spearman(x, y):
    r, p = stats.spearmanr(x, y)
    return float(r), float(p)


def partial_spearman(x, y, z):
    """Partial Spearman rho of (x, y) controlling z: Pearson on ranks via
    the standard partial-correlation formula (tie-aware ranks)."""
    rx, ry, rz = (stats.rankdata(v) for v in (x, y, z))
    rxy = np.corrcoef(rx, ry)[0, 1]
    rxz = np.corrcoef(rx, rz)[0, 1]
    ryz = np.corrcoef(ry, rz)[0, 1]
    return float((rxy - rxz * ryz) /
                 np.sqrt((1 - rxz ** 2) * (1 - ryz ** 2)))


def strata_indices(inc_ord):
    return {v: np.where(inc_ord == v)[0] for v in sorted(set(inc_ord))}


def within_stratum_perms_exact(y, inc_ord):
    """Enumerate ALL distinct equally-likely within-stratum label
    assignments. Only strata containing both classes generate more than one
    assignment. Returns a generator of outcome vectors and the group size."""
    strata = strata_indices(inc_ord)
    per_stratum = []
    for v, idx in strata.items():
        k = int(y[idx].sum())
        per_stratum.append((idx, list(itertools.combinations(range(len(idx)), k))))
    size = int(np.prod([len(c) for _, c in per_stratum]))

    def gen():
        for combo in itertools.product(*[c for _, c in per_stratum]):
            yv = np.zeros_like(y)
            for (idx, _), pos in zip(per_stratum, combo):
                yv[idx[list(pos)]] = 1.0
            yield yv
    return gen, size


def perm_pvalues_partial(x, y, z, n_mc, seed):
    """Permutation p for partial Spearman: within-stratum shuffles.
    Returns observed rho, Monte-Carlo p (one/two-sided), exact p
    (enumeration), and the exact group size."""
    obs = partial_spearman(x, y, z)
    strata = strata_indices(z)
    rng = np.random.default_rng(seed)
    cnt_ge = 0
    cnt_abs = 0
    for _ in range(n_mc):
        yp = y.copy()
        for idx in strata.values():
            yp[idx] = rng.permutation(yp[idx])
        r = partial_spearman(x, yp, z)
        cnt_ge += r >= obs - 1e-12
        cnt_abs += abs(r) >= abs(obs) - 1e-12
    p_mc_one = (cnt_ge + 1) / (n_mc + 1)
    p_mc_two = (cnt_abs + 1) / (n_mc + 1)

    gen, size = within_stratum_perms_exact(y, z)
    ge = 0
    ab = 0
    for yv in gen():
        r = partial_spearman(x, yv, z)
        ge += r >= obs - 1e-12
        ab += abs(r) >= abs(obs) - 1e-12
    return dict(rho_partial=obs,
                p_perm_mc_one_sided=float(p_mc_one),
                p_perm_mc_two_sided=float(p_mc_two),
                n_mc=n_mc,
                p_exact_one_sided=ge / size,
                p_exact_two_sided=ab / size,
                exact_group_size=size)


def stratified_exact_tests(x, y, z):
    """Per-stratum descriptives + exact stratified Mann-Whitney.
    The stratified statistic = sum over strata of the positives' rank-sum
    (within-stratum ranks, tie-averaged); its null distribution comes from
    exact enumeration of the within-stratum permutation group. Strata with
    a single class contribute a constant and are labeled uninformative."""
    strata = strata_indices(z)
    per = {}
    for v, idx in strata.items():
        pos, ctl = x[idx][y[idx] == 1], x[idx][y[idx] == 0]
        per[int(v)] = dict(
            n_pos=int(len(pos)), n_ctl=int(len(ctl)),
            mean_pos=float(pos.mean()) if len(pos) else None,
            mean_ctl=float(ctl.mean()) if len(ctl) else None,
            informative=bool(len(pos) and len(ctl)),
        )

    def stat(yv):
        s = 0.0
        for idx in strata.values():
            ranks = stats.rankdata(x[idx])
            s += ranks[yv[idx] == 1].sum()
        return s

    def stat_meandiff(yv):
        s = 0.0
        for idx in strata.values():
            p_, c_ = x[idx][yv[idx] == 1], x[idx][yv[idx] == 0]
            if len(p_) and len(c_):
                s += p_.mean() - c_.mean()
        return s

    obs_w, obs_d = stat(y), stat_meandiff(y)
    gen, size = within_stratum_perms_exact(y, z)
    ge_w = 0
    ge_d = 0
    for yv in gen():
        ge_w += stat(yv) >= obs_w - 1e-12
        ge_d += stat_meandiff(yv) >= obs_d - 1e-12
    return dict(per_stratum=per,
                stratified_ranksum_obs=float(obs_w),
                p_exact_one_sided_ranksum=ge_w / size,
                stratified_meandiff_obs=float(obs_d),
                p_exact_one_sided_meandiff=ge_d / size,
                exact_group_size=size)


def analyse(tag, income_map, arm, x):
    inc = np.array([ORD[income_map[i]] for i in ISO], float)
    rho_xy, p_xy = spearman(x, outcome)              # pooled, unadjusted
    rho_xz, p_xz = spearman(x, inc)                  # blunt: wealth alone
    rho_yz, p_yz = spearman(outcome, inc)            # confound size
    m1 = perm_pvalues_partial(x, outcome, inc, N_PERM, RNG_SEED)
    m2 = stratified_exact_tests(x, outcome, inc)
    # supplementary: within positives only, does wealth predict the score?
    pos = outcome == 1
    rho_pos, p_pos = spearman(x[pos], inc[pos])
    return {
        "tag": tag, "arm": arm,
        "income_ordinal_coding": {k: ORD[k] for k in ORD},
        "pooled_unadjusted": {"spearman_rho": rho_xy, "p_asymptotic": p_xy},
        "M3_blunt": {
            "spearman_p_onset_vs_income": {"rho": rho_xz, "p_asymptotic": p_xz},
            "spearman_outcome_vs_income_confound": {"rho": rho_yz,
                                                    "p_asymptotic": p_yz},
        },
        "M1_partial_spearman": m1,
        "M2_stratified": m2,
        "supp_within_positives_income_vs_score": {
            "n": int(pos.sum()), "rho": rho_pos, "p_asymptotic": p_pos},
    }


results = {
    "provenance": {
        "register": "ops/alive/RETRODICTION_v1.md lines 14-37 (transcribed "
                    "verbatim into this script)",
        "pooled_claim_under_audit": "null-arm Spearman 0.552, p=0.0052; "
                                    "positives 0.417 vs controls 0.031 "
                                    "(RETRODICTION_v1.md lines 40-44)",
        "income_repo": "engine repo country table: earth1/census.py "
                       "CENSUS_TARGETS[*]['income'] (the C2+ substrate "
                       "pooling tier map); matches WB FY2020/21-era "
                       "classification",
        "income_fy2011": "World Bank income group, FY2011 classification, "
                         "transcribed (2009 GNI p.c., Atlas). Boundary "
                         "cases: EC at the LMIC/UMIC cut (kept LMIC per "
                         "the FY2011 list); IQ LMIC; CL/UY/IR UMIC; "
                         "KE/BD LIC.",
        "seed": RNG_SEED, "n_mc_permutations": N_PERM,
    },
    "register_table": [
        {"iso2": i, "outcome": int(o), "p_scenario": ps, "p_null": pn,
         "income_repo": EXPECTED_INCOME_REPO[i],
         "income_fy2011": INCOME_FY2011[i]}
        for i, o, ps, pn in REGISTER
    ],
    "primary_repo_tiers_null_arm": analyse("repo_tiers", EXPECTED_INCOME_REPO,
                                           "null", p_null),
    "robustness_fy2011_null_arm": analyse("fy2011", INCOME_FY2011,
                                          "null", p_null),
    "secondary_repo_tiers_scenario_arm": analyse("repo_tiers",
                                                 EXPECTED_INCOME_REPO,
                                                 "scenario", p_scen),
}

# sanity: reproduce the register's pooled numbers
chk = results["primary_repo_tiers_null_arm"]["pooled_unadjusted"]
results["sanity_reproduction"] = {
    "null_arm_pooled_spearman_recomputed": chk["spearman_rho"],
    "register_claims": 0.552,
    "positives_mean_p_null": float(p_null[outcome == 1].mean()),
    "controls_mean_p_null": float(p_null[outcome == 0].mean()),
}

with open(OUT, "w") as f:
    json.dump(results, f, indent=2)
print(json.dumps(results["sanity_reproduction"], indent=2))
print(json.dumps(results["primary_repo_tiers_null_arm"], indent=2))
print(json.dumps(results["robustness_fy2011_null_arm"]["M1_partial_spearman"],
                 indent=2))
print(json.dumps(results["robustness_fy2011_null_arm"]["M2_stratified"],
                 indent=2))
print(json.dumps(results["robustness_fy2011_null_arm"]["M3_blunt"], indent=2))
print("saved ->", OUT)
