"""WHAT IS THE UNIVERSE HERE? — measure its effective dimension.

Compares the intrinsic dimensionality of:
  ENGINE  — Earth-1's agent state (traits + forces), within country
            and pooled across countries
  REALITY — WVS7 respondents' own answer space (the same people the
            benchmark is built from), within country and pooled

Effective rank = exp(entropy of the normalized eigenvalue spectrum)
(participation ratio), plus the count of components needed for 90% of
variance. A container is only a universe if the object inside it
actually occupies its dimensions.
"""
from __future__ import annotations

import json
import os
import sys

import duckdb
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAW = "/tmp/WVS_Cross-National_Wave_7_csv_v6_0.csv"
POP = int(os.environ.get("UD_POP", "50000"))
# a broad, non-cherry-picked slice of WVS7 attitude items
REAL_VARS = ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q27", "Q29",
             "Q30", "Q31", "Q32", "Q33", "Q34", "Q35", "Q36", "Q46", "Q47",
             "Q48", "Q49", "Q50", "Q57", "Q58", "Q59", "Q60", "Q61", "Q62",
             "Q106", "Q107", "Q108", "Q109", "Q110", "Q111", "Q112",
             "Q164", "Q170", "Q171", "Q173", "Q176", "Q177", "Q178",
             "Q179", "Q180", "Q181", "Q182", "Q183", "Q184", "Q185",
             "Q186", "Q189", "Q192", "Q195", "Q199", "Q209", "Q222",
             "Q235", "Q240", "Q250", "Q252"]


def eff_rank(X: np.ndarray) -> tuple:
    X = X - X.mean(axis=0, keepdims=True)
    sd = X.std(axis=0)
    X = X[:, sd > 1e-9] / sd[sd > 1e-9]
    if X.shape[1] < 2 or X.shape[0] < 10:
        return (0.0, 0, 0)
    ev = np.linalg.svd(X, compute_uv=False) ** 2
    ev = ev / ev.sum()
    ent = -(ev * np.log(np.maximum(ev, 1e-15))).sum()
    n90 = int(np.searchsorted(np.cumsum(ev), 0.90) + 1)
    return (float(np.exp(ent)), n90, X.shape[1])


def main() -> None:
    from earth1.genesis import genesis
    from earth1.calibration import _get_country_index

    civ = genesis(POP, 42)
    c2i, _ = _get_country_index(civ)
    traits = [n for n in ("openness", "empathy", "risk_appetite", "doubt",
                          "desire_intensity", "conscientiousness",
                          "agreeableness", "extraversion", "neuroticism",
                          "individualism", "power_distance",
                          "uncertainty_avoidance", "long_term_orientation",
                          "economic_field", "culture_offset")
              if getattr(civ, n, None) is not None]
    E = np.column_stack([getattr(civ, n) for n in traits]
                        + [civ.forces[:, i] for i in range(8)])
    er_pool = eff_rank(E)
    per_c = []
    for cc in ("US", "DE", "BR", "IN", "NG", "JP"):
        if cc in c2i:
            m = civ.country == c2i[cc]
            if m.sum() > 200:
                per_c.append(eff_rank(E[m])[0])
    print(f"ENGINE  pooled eff-rank {er_pool[0]:.2f} of {er_pool[2]} dims "
          f"(90% var in {er_pool[1]}) | within-country mean "
          f"{np.mean(per_c):.2f}", flush=True)

    con = duckdb.connect()
    con.execute(f"""CREATE VIEW w AS SELECT * FROM read_csv('{RAW}',
      header=true, delim=',', quote='"', escape='"', strict_mode=false,
      ignore_errors=true, max_line_size=10000000, null_padding=true)""")
    cols = []
    for v in REAL_VARS:
        try:
            con.execute(f"SELECT {v} FROM w LIMIT 1").fetchall()
            cols.append(v)
        except Exception:
            continue
    sel = ", ".join(f"CASE WHEN {c} >= 0 THEN {c} END AS {c}" for c in cols)
    rows = con.execute(
        f"SELECT B_COUNTRY_ALPHA, {sel} FROM w WHERE W_WEIGHT > 0").fetchall()
    arr = np.array([[np.nan if v is None else float(v) for v in r[1:]]
                    for r in rows])
    ccs = np.array([r[0] for r in rows])
    keep = ~np.isnan(arr).any(axis=1)
    A, C = arr[keep], ccs[keep]
    rr_pool = eff_rank(A)
    per_r = []
    for cc in ("USA", "DEU", "BRA", "IND", "NGA", "JPN"):
        m = C == cc
        if m.sum() > 200:
            per_r.append(eff_rank(A[m])[0])
    print(f"REALITY pooled eff-rank {rr_pool[0]:.2f} of {rr_pool[2]} dims "
          f"(90% var in {rr_pool[1]}) | within-country mean "
          f"{np.mean(per_r):.2f} | n={len(A)} respondents", flush=True)

    out = {"engine": {"eff_rank_pooled": er_pool[0], "n90": er_pool[1],
                      "dims": er_pool[2],
                      "eff_rank_within_country": float(np.mean(per_c))},
           "reality": {"eff_rank_pooled": rr_pool[0], "n90": rr_pool[1],
                       "dims": rr_pool[2],
                       "eff_rank_within_country": float(np.mean(per_r)),
                       "n_respondents": int(len(A))}}
    json.dump(out, open("data/universe_dimension.json", "w"), indent=1)
    print(f"UNIVERSE-VERDICT: engine within-country eff-rank "
          f"{np.mean(per_c):.2f} vs reality {np.mean(per_r):.2f} — "
          f"ratio {np.mean(per_c)/max(np.mean(per_r),1e-9):.2f}", flush=True)


if __name__ == "__main__":
    main()
