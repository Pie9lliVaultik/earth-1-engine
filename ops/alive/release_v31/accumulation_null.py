#!/usr/bin/env python3
"""
AUDIT ITEM 3 — constant-accumulation null for the wealth-concentration
emergence claim (p99/p50 11.88 -> 29.48; top-1% share 0.122 -> 0.194 over
120 days, ops/alive/PAPER_EARTH1_v1.md:168).

Null: every agent keeps its job and accumulates at a constant rate
proportional to its genesis wage, with NO shocks:

    wealth_t(c) = wealth_0 + c * wage * T,   T = 120 days

for c in {0, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 20} plus the wage-only limit
(c -> infinity: the wage distribution itself). For each member: p99/p50
and top-1% share at t = 120.

Genesis source: canonical birth_world (earth1.alive:51) under the frozen
physics flags (scripts/env/freeze09.env must be exported by the caller).
Run record used for (pop, seed): ops/alive/audit/EMERGENCE_AUDIT_collective.md:5
("canonical birth_world/live_one_day, world seed 42 / rng seed 7", M3 = 120 d,
pop 6,000). Match check: genesis wealth p99/p50 must land near 11.88 and
genesis top-1% share near 0.122; candidate list below is scanned in order
and the closest match is used.

READ-ONLY: the world is constructed in memory and never ticked; nothing is
written into the engine tree.
"""
import json
import os
import sys

import numpy as np

REPO = "/Users/pietronovelli/Documents/GitHub/earth-1-engine"
OUT = ("/private/tmp/claude-501/-Users-pietronovelli-Documents-GitHub-vaultik-x/"
       "e30708db-e208-4f7c-aad1-c0be9c88f760/scratchpad/audit_v31/"
       "accumulation_null.json")

sys.path.insert(0, REPO)

# Guard: the frozen physics flags must be in the environment (sourced by
# the caller from scripts/env/freeze09.env). Check a sentinel.
REQUIRED_FLAGS = ["EARTH1_HARDSHIP_MODE", "EARTH1_INCOME_CALIBRATION",
                  "EARTH1_MORTALITY_MODE"]
missing = [f for f in REQUIRED_FLAGS if f not in os.environ]
if missing:
    raise SystemExit(f"freeze09.env not sourced; missing {missing}")

T_DAYS = 120.0
C_GRID = [0.0, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 20.0]
MEASURED = {"genesis_p99_p50": 11.88, "day120_p99_p50": 29.48,
            "genesis_top1": 0.122, "day120_top1": 0.194}

# Candidate (pop, seed) pairs, in order of evidentiary strength:
#  - (6000, 42): the audit's own canonical 120-day run
#    (ops/alive/audit/EMERGENCE_AUDIT_collective.md:5).
#  - (200000, 424242): the genesis reference world named in
#    ops/alive/audit/EMERGENCE_AUDIT_material.md:42.
#  - (20000, 42), (200000, 42): plausible defaults (seed default is 42,
#    earth1/alive.py:51).
CANDIDATES = [(6000, 42), (200000, 424242), (20000, 42), (200000, 42)]
MATCH_TOL_REL = 0.02   # 2% relative tolerance on genesis p99/p50


def p99_p50(x):
    p99 = float(np.percentile(x, 99))
    p50 = float(np.percentile(x, 50))
    return p99 / p50 if p50 != 0 else float("inf")


def top1_share(x):
    """Share of total held by the top 1% of agents (by the same variable)."""
    x = np.asarray(x, dtype=np.float64)
    k = max(1, int(np.ceil(0.01 * x.size)))
    idx = np.argsort(x)[::-1][:k]
    tot = float(x.sum())
    return float(x[idx].sum()) / tot if tot != 0 else float("nan")


def w_p99_p50(x, w):
    """Census-weighted variant (weights from earth1.genesis.census_weights)."""
    order = np.argsort(x)
    xs, ws = x[order], w[order]
    cw = np.cumsum(ws) / ws.sum()
    p50 = float(xs[np.searchsorted(cw, 0.50)])
    p99 = float(xs[np.searchsorted(cw, 0.99)])
    return p99 / p50 if p50 != 0 else float("inf")


def w_top1_share(x, w):
    order = np.argsort(x)[::-1]
    xs, ws = x[order], w[order]
    cw = np.cumsum(ws) / ws.sum()
    k = int(np.searchsorted(cw, 0.01)) + 1
    tot = float((xs * ws).sum())
    return float((xs[:k] * ws[:k]).sum()) / tot if tot != 0 else float("nan")


def stats_pair(x, w):
    return {
        "p99_p50": round(p99_p50(x), 4),
        "top1_share": round(top1_share(x), 6),
        "p99_p50_census_weighted": round(w_p99_p50(x, w), 4),
        "top1_share_census_weighted": round(w_top1_share(x, w), 6),
    }


def main():
    from earth1.alive import birth_world
    from earth1.genesis import census_weights

    candidates_out = []
    chosen = None
    for pop, seed in CANDIDATES:
        # substrate comes from the frozen flag set (freeze09.env exports
        # EARTH1_SUBSTRATE_FLAG); genesis refuses a mismatched substrate.
        w = birth_world(pop, seed,
                        substrate=os.environ["EARTH1_SUBSTRATE_FLAG"])
        # constructed, never ticked
        wage = np.asarray(w.life.wage, dtype=np.float64)
        wealth0 = np.asarray(w.life.wealth, dtype=np.float64)
        cw = np.asarray(census_weights(w.civ), dtype=np.float64)
        g = {
            "pop": pop, "seed": seed,
            "genesis_wealth": stats_pair(wealth0, cw),
            "genesis_wage": stats_pair(wage, cw),
        }
        rel = abs(g["genesis_wealth"]["p99_p50"] - MEASURED["genesis_p99_p50"]) \
            / MEASURED["genesis_p99_p50"]
        g["match_rel_error_p99_p50_unweighted"] = round(rel, 4)
        rel_w = abs(g["genesis_wealth"]["p99_p50_census_weighted"]
                    - MEASURED["genesis_p99_p50"]) / MEASURED["genesis_p99_p50"]
        g["match_rel_error_p99_p50_weighted"] = round(rel_w, 4)
        candidates_out.append(g)
        print(f"candidate pop={pop} seed={seed}: "
              f"wealth p99/p50={g['genesis_wealth']['p99_p50']} "
              f"(weighted {g['genesis_wealth']['p99_p50_census_weighted']}), "
              f"top1={g['genesis_wealth']['top1_share']} "
              f"(weighted {g['genesis_wealth']['top1_share_census_weighted']})")
        if min(rel, rel_w) <= MATCH_TOL_REL and chosen is None:
            chosen = (pop, seed, wage, wealth0, cw,
                      "weighted" if rel_w < rel else "unweighted")
            break   # first (strongest-evidence) match wins

    result = {
        "measured_claim": MEASURED,
        "measured_claim_source": "ops/alive/PAPER_EARTH1_v1.md:168",
        "run_record_source": "ops/alive/audit/EMERGENCE_AUDIT_collective.md:5",
        "t_days": T_DAYS,
        "candidates": candidates_out,
    }

    if chosen is None:
        result["match"] = None
        result["verdict"] = ("NO GENESIS MATCH: no candidate (pop, seed) "
                             "reproduces genesis wealth p99/p50 = 11.88 "
                             f"within {MATCH_TOL_REL:.0%}; null family not "
                             "computed against an unmatched genesis.")
        with open(OUT, "w") as f:
            json.dump(result, f, indent=2)
        print(result["verdict"])
        return

    pop, seed, wage, wealth0, cw, mode = chosen
    result["match"] = {"pop": pop, "seed": seed, "stat_mode": mode}

    # ---- the null family -------------------------------------------------
    family = []
    for c in C_GRID:
        wt = wealth0 + c * wage * T_DAYS
        row = {"c": c, **stats_pair(wt, cw)}
        family.append(row)
    wage_only = {"c": "inf (wage-only limit)", **stats_pair(wage, cw)}
    family.append(wage_only)
    result["null_family"] = family

    # Supplementary (not part of the registered family, not used for the
    # verdict): surplus-proportional accumulation, wealth0 + c*max(wage-1,0)*T
    # — closer to the engine's actual employed-agent flow shape.
    surplus = np.maximum(wage - 1.0, 0.0)
    result["supplementary_surplus_variant"] = [
        {"c": c, **stats_pair(wealth0 + c * surplus * T_DAYS, cw)}
        for c in C_GRID
    ] + [{"c": "inf (surplus-only limit)", **stats_pair(surplus, cw)}]

    # ---- verdict ---------------------------------------------------------
    key = "p99_p50" if mode == "unweighted" else "p99_p50_census_weighted"
    key_t1 = "top1_share" if mode == "unweighted" \
        else "top1_share_census_weighted"
    ratios = [row[key] for row in family]
    top1s = [row[key_t1] for row in family]
    meas_r, meas_t = MEASURED["day120_p99_p50"], MEASURED["day120_top1"]
    inside_r = min(ratios) <= meas_r <= max(ratios)
    inside_t = min(top1s) <= meas_t <= max(top1s)
    result["verdict_inputs"] = {
        "null_p99_p50_min": min(ratios), "null_p99_p50_max": max(ratios),
        "null_top1_min": min(top1s), "null_top1_max": max(top1s),
        "measured_p99_p50": meas_r, "measured_top1": meas_t,
        "measured_p99_p50_inside_null_range": inside_r,
        "measured_top1_inside_null_range": inside_t,
    }
    # Nearest family member to the measured endpoint, per statistic
    near_r = min(family, key=lambda r: abs(r[key] - meas_r))
    near_t = min(family, key=lambda r: abs(r[key_t1] - meas_t))
    result["verdict_inputs"]["nearest_null_by_p99_p50"] = near_r
    result["verdict_inputs"]["nearest_null_by_top1"] = near_t

    if inside_r or inside_t:
        result["verdict"] = (
            "NULL REPRODUCES: the measured day-120 concentration falls inside "
            "the constant-accumulation null family's range on at least one "
            "statistic; the emergence claim does not survive this null.")
    else:
        above = meas_r > max(ratios) and meas_t > max(top1s)
        below = meas_r < min(ratios) and meas_t < min(top1s)
        side = "ABOVE" if above else ("BELOW" if below else "MIXED")
        result["verdict"] = (
            f"OUTSIDE NULL ({side}): the measured day-120 concentration falls "
            "outside the entire constant-accumulation null family on both "
            "statistics; the claim survives this null.")

    with open(OUT, "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result["verdict_inputs"], indent=2))
    print(result["verdict"])


if __name__ == "__main__":
    main()
