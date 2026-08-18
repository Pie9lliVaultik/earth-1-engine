"""C2 step 5: extend the injection beyond religiosity.

Same recipe that took GOQA 10.59 -> 9.42: extract real per-country
joint distributions from WVS7 microdata and give agents the property.
Variables added here (all present in WVS7, all absent from Earth-1):
  marital  Q273 (1-2 married/partner -> 1)
  employed Q279 (1-3 full/part/self -> 1)
  ideology Q240 left-right 1-10, normalized 0-1 (mean per cell)
  social_class Q287 (1-5, upper=1 -> normalized 0-1)
Conditioned on (age bucket, education) like religiosity.
Output: data/joint_priors.json  {var: {iso2: {cells, marginal}}}
"""
from __future__ import annotations

import json

import duckdb
import numpy as np

RAW = "/tmp/WVS_Cross-National_Wave_7_csv_v6_0.csv"

VARS = {
    "marital": ("CASE WHEN Q273 IN (1,2) THEN 1.0 ELSE 0.0 END", "Q273 >= 0"),
    "employed": ("CASE WHEN Q279 IN (1,2,3) THEN 1.0 ELSE 0.0 END",
                 "Q279 >= 0"),
    "ideology": ("(Q240 - 1.0) / 9.0", "Q240 BETWEEN 1 AND 10"),
    "social_class": ("(5.0 - Q287) / 4.0", "Q287 BETWEEN 1 AND 5"),
}

con = duckdb.connect()
con.execute(f"""CREATE VIEW w AS SELECT * FROM read_csv('{RAW}',
  header=true, delim=',', quote='"', escape='"', strict_mode=false,
  ignore_errors=true, max_line_size=10000000, null_padding=true)""")


def main() -> None:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    from earth1.benchmark import ISO3_TO_ISO2

    out = {}
    for var, (expr, cond) in VARS.items():
        cells = con.execute(f"""
            SELECT B_COUNTRY_ALPHA AS cc,
                   CASE WHEN Q262 BETWEEN 18 AND 29 THEN 0
                        WHEN Q262 BETWEEN 30 AND 44 THEN 1
                        WHEN Q262 BETWEEN 45 AND 59 THEN 2
                        WHEN Q262 >= 60 THEN 3 END AS age_b,
                   CASE WHEN Q275 <= 2 THEN 0 WHEN Q275 <= 5 THEN 1
                        ELSE 2 END AS edu,
                   SUM(({expr}) * W_WEIGHT) / SUM(W_WEIGHT) AS v,
                   SUM(W_WEIGHT) AS nw
            FROM w WHERE {cond} AND Q262 >= 18 AND Q275 >= 0 AND W_WEIGHT > 0
            GROUP BY cc, age_b, edu
            HAVING SUM(W_WEIGHT) >= 30 AND age_b IS NOT NULL""").fetchall()
        marg = con.execute(f"""
            SELECT B_COUNTRY_ALPHA AS cc,
                   SUM(({expr}) * W_WEIGHT) / SUM(W_WEIGHT) AS v
            FROM w WHERE {cond} AND W_WEIGHT > 0
            GROUP BY cc HAVING SUM(W_WEIGHT) >= 200""").fetchall()
        d = {}
        for cc, v in marg:
            iso2 = ISO3_TO_ISO2.get(cc)
            if iso2:
                d[iso2] = {"marginal": round(float(v), 4), "cells": {}}
        n = 0
        for cc, a, e, v, nw in cells:
            iso2 = ISO3_TO_ISO2.get(cc)
            if iso2 and iso2 in d:
                d[iso2]["cells"][f"{a}_{e}"] = round(float(v), 4)
                n += 1
        out[var] = d
        spreads = [max(x["cells"].values()) - min(x["cells"].values())
                   for x in d.values() if len(x["cells"]) >= 6]
        print(f"  {var:13s}: {len(d)} countries, {n} cells | within-country "
              f"spread {np.mean(spreads):.3f} | marginal range "
              f"{min(x['marginal'] for x in d.values()):.2f}-"
              f"{max(x['marginal'] for x in d.values()):.2f}", flush=True)
    json.dump(out, open("data/joint_priors.json", "w"), indent=1)
    print(f"JOINT-PRIORS: {len(out)} variables written", flush=True)


if __name__ == "__main__":
    main()
