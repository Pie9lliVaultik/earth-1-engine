"""C2 step 1: US joint distribution cells from WVS7 microdata.
age x education x religiosity, weighted, with per-cell answers —
the real within-country structure genesis v3 must reproduce."""
from __future__ import annotations

import json

import duckdb
import numpy as np

RAW = "/tmp/WVS_Cross-National_Wave_7_csv_v6_0.csv"

con = duckdb.connect()
con.execute(f"""CREATE VIEW w AS SELECT * FROM read_csv('{RAW}',
  header=true, delim=',', quote='"', escape='"', strict_mode=false,
  ignore_errors=true, max_line_size=10000000, null_padding=true)""")

rows = con.execute("""
SELECT CASE WHEN Q262 BETWEEN 18 AND 29 THEN 0
            WHEN Q262 BETWEEN 30 AND 44 THEN 1
            WHEN Q262 BETWEEN 45 AND 59 THEN 2
            WHEN Q262 >= 60 THEN 3 END AS age_b,
       CASE WHEN Q275 <= 2 THEN 0 WHEN Q275 <= 5 THEN 1 ELSE 2 END AS edu,
       CASE WHEN Q164 >= 6 THEN 1 ELSE 0 END AS relig,
       SUM(W_WEIGHT) AS n,
       SUM(CASE WHEN Q57 = 1 THEN W_WEIGHT ELSE 0 END)
         / SUM(W_WEIGHT) AS trust,
       SUM(CASE WHEN Q182 >= 6 THEN W_WEIGHT ELSE 0 END)
         / SUM(W_WEIGHT) AS homosex,
       SUM(CASE WHEN Q184 >= 6 THEN W_WEIGHT ELSE 0 END)
         / SUM(W_WEIGHT) AS abortion
FROM w
WHERE B_COUNTRY_ALPHA = 'USA' AND Q262 >= 18 AND Q164 >= 0
  AND Q275 >= 0 AND W_WEIGHT > 0
GROUP BY age_b, edu, relig
HAVING SUM(W_WEIGHT) >= 30 AND age_b IS NOT NULL
ORDER BY age_b, edu, relig""").fetchall()

out = [{"age_b": r[0], "edu": r[1], "relig": r[2], "n": round(r[3], 1),
        "trust": round(r[4], 4), "homosex": round(r[5], 4),
        "abortion": round(r[6], 4)} for r in rows]
json.dump(out, open("data/us_joint_cells.json", "w"), indent=1)

tr = [r for r in out if r["relig"] == 1]
nr = [r for r in out if r["relig"] == 0]
h_r = np.average([r["homosex"] for r in tr], weights=[r["n"] for r in tr])
h_s = np.average([r["homosex"] for r in nr], weights=[r["n"] for r in nr])
print(f"US-JOINT: {len(out)} cells | homosexuality justifiable: "
      f"religious {h_r:.3f} vs secular {h_s:.3f} | "
      f"within-US spread across cells "
      f"{max(r['homosex'] for r in out) - min(r['homosex'] for r in out):.3f}")
