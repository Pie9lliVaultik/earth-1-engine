"""Gated clean structural variables from WVS7 microdata.

Post-erratum discipline: these are demographic/structural facts, NOT
opinion items — none is a GOQA question. Every one still passes
through scripts/feature_adjacency_gate.py before it may be measured.

  household_size  Q270  (people in household, /8 capped)
  children        Q274  (number of children, /5 capped)
  town_size       G_TOWNSIZE (settlement size band, /8)
  immigrant       Q263  (respondent born in country: 2 => immigrant)
  income_scale    Q288  (self-reported income decile, /10)

Conditioned on (age bucket, education), survey-weighted, min N 30.
Appends to data/joint_priors.json.
"""
from __future__ import annotations

import json
import os
import sys

import duckdb
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAW = "/tmp/WVS_Cross-National_Wave_7_csv_v6_0.csv"

VARS = {
    "household_size": ("LEAST(Q270, 8) / 8.0", "Q270 BETWEEN 1 AND 30"),
    "children": ("LEAST(Q274, 5) / 5.0", "Q274 >= 0"),
    "town_size": ("(G_TOWNSIZE - 1.0) / 7.0", "G_TOWNSIZE BETWEEN 1 AND 8"),
    "immigrant": ("CASE WHEN Q263 = 2 THEN 1.0 ELSE 0.0 END",
                  "Q263 BETWEEN 1 AND 2"),
    "income_scale": ("(Q288 - 1.0) / 9.0", "Q288 BETWEEN 1 AND 10"),
}


def main() -> None:
    from earth1.benchmark_questions import ISO3_TO_ISO2
    con = duckdb.connect()
    con.execute(f"""CREATE VIEW w AS SELECT * FROM read_csv('{RAW}',
      header=true, delim=',', quote='"', escape='"', strict_mode=false,
      ignore_errors=true, max_line_size=10000000, null_padding=true)""")
    out = (json.load(open("data/joint_priors.json"))
           if os.path.exists("data/joint_priors.json") else {})
    for var, (expr, cond) in VARS.items():
        try:
            cells = con.execute(f"""
                SELECT B_COUNTRY_ALPHA AS cc,
                       CASE WHEN Q262 BETWEEN 18 AND 29 THEN 0
                            WHEN Q262 BETWEEN 30 AND 44 THEN 1
                            WHEN Q262 BETWEEN 45 AND 59 THEN 2
                            WHEN Q262 >= 60 THEN 3 END AS age_b,
                       CASE WHEN Q275 <= 2 THEN 0 WHEN Q275 <= 5 THEN 1
                            ELSE 2 END AS edu,
                       SUM(({expr}) * W_WEIGHT) / SUM(W_WEIGHT) AS v
                FROM w WHERE {cond} AND Q262 >= 18 AND Q275 >= 0
                  AND W_WEIGHT > 0
                GROUP BY cc, age_b, edu
                HAVING SUM(W_WEIGHT) >= 30 AND age_b IS NOT NULL""").fetchall()
            marg = con.execute(f"""
                SELECT B_COUNTRY_ALPHA AS cc,
                       SUM(({expr}) * W_WEIGHT) / SUM(W_WEIGHT) AS v
                FROM w WHERE {cond} AND W_WEIGHT > 0
                GROUP BY cc HAVING SUM(W_WEIGHT) >= 200""").fetchall()
        except Exception as exc:  # column absent in this release
            print(f"  {var:15s}: SKIPPED ({str(exc)[:60]})", flush=True)
            continue
        d = {}
        for cc, v in marg:
            i2 = ISO3_TO_ISO2.get(cc)
            if i2:
                d[i2] = {"marginal": round(float(v), 4), "cells": {}}
        n = 0
        for cc, a, e, v in cells:
            i2 = ISO3_TO_ISO2.get(cc)
            if i2 and i2 in d:
                d[i2]["cells"][f"{a}_{e}"] = round(float(v), 4)
                n += 1
        if not d:
            print(f"  {var:15s}: no data", flush=True)
            continue
        out[var] = d
        sp = [max(x["cells"].values()) - min(x["cells"].values())
              for x in d.values() if len(x["cells"]) >= 6]
        print(f"  {var:15s}: {len(d)} countries, {n} cells | within-country "
              f"spread {np.mean(sp) if sp else 0:.3f}", flush=True)
    json.dump(out, open("data/joint_priors.json", "w"), indent=1)
    print(f"CLEAN-STRUCTURE: joint_priors now has {len(out)} variables",
          flush=True)


if __name__ == "__main__":
    main()
