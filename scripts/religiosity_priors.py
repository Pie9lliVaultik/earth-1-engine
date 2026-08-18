"""C2 step 3: per-country P(religious | age bucket, education) from
WVS7 microdata — the first REAL joint structure genesis will carry.

Religious := Q164 (importance of God) >= 6 on the 1-10 scale, the same
coding the official seeds use. Education collapsed to genesis's 3
levels from Q275 (ISCED). Survey-weighted, min weighted N 30 per cell;
country falls back to its own marginal where a cell is thin.

Output: data/religiosity_priors.json
  {iso2: {"cells": {"<age_b>_<edu>": p}, "marginal": p, "n": w}}
"""
from __future__ import annotations

import json

import duckdb

RAW = "/tmp/WVS_Cross-National_Wave_7_csv_v6_0.csv"

con = duckdb.connect()
con.execute(f"""CREATE VIEW w AS SELECT * FROM read_csv('{RAW}',
  header=true, delim=',', quote='"', escape='"', strict_mode=false,
  ignore_errors=true, max_line_size=10000000, null_padding=true)""")

CELL_SQL = """
SELECT B_COUNTRY_ALPHA AS cc,
       CASE WHEN Q262 BETWEEN 18 AND 29 THEN 0
            WHEN Q262 BETWEEN 30 AND 44 THEN 1
            WHEN Q262 BETWEEN 45 AND 59 THEN 2
            WHEN Q262 >= 60 THEN 3 END AS age_b,
       CASE WHEN Q275 <= 2 THEN 0 WHEN Q275 <= 5 THEN 1 ELSE 2 END AS edu,
       SUM(CASE WHEN Q164 >= 6 THEN W_WEIGHT ELSE 0 END)
         / SUM(W_WEIGHT) AS p_relig,
       SUM(W_WEIGHT) AS nw
FROM w
WHERE Q164 >= 0 AND Q262 >= 18 AND Q275 >= 0 AND W_WEIGHT > 0
GROUP BY cc, age_b, edu
HAVING SUM(W_WEIGHT) >= 30 AND age_b IS NOT NULL
"""

MARGINAL_SQL = """
SELECT B_COUNTRY_ALPHA AS cc,
       SUM(CASE WHEN Q164 >= 6 THEN W_WEIGHT ELSE 0 END)
         / SUM(W_WEIGHT) AS p_relig,
       SUM(W_WEIGHT) AS nw
FROM w
WHERE Q164 >= 0 AND W_WEIGHT > 0
GROUP BY cc HAVING SUM(W_WEIGHT) >= 200
"""


def main() -> None:
    from earth1.benchmark import ISO3_TO_ISO2
    out: dict = {}
    for cc, p, nw in con.execute(MARGINAL_SQL).fetchall():
        iso2 = ISO3_TO_ISO2.get(cc)
        if iso2:
            out[iso2] = {"cells": {}, "marginal": round(p, 4),
                         "n": round(nw, 1)}
    n_cells = 0
    for cc, age_b, edu, p, nw in con.execute(CELL_SQL).fetchall():
        iso2 = ISO3_TO_ISO2.get(cc)
        if iso2 and iso2 in out:
            out[iso2]["cells"][f"{age_b}_{edu}"] = round(p, 4)
            n_cells += 1
    json.dump(out, open("data/religiosity_priors.json", "w"), indent=1)
    spread = [max(v["cells"].values()) - min(v["cells"].values())
              for v in out.values() if len(v["cells"]) >= 6]
    import numpy as np
    print(f"RELIGIOSITY-PRIORS: {len(out)} countries, {n_cells} cells | "
          f"mean within-country cell spread {np.mean(spread):.3f} | "
          f"country marginals range "
          f"{min(v['marginal'] for v in out.values()):.2f}-"
          f"{max(v['marginal'] for v in out.values()):.2f}")


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()
