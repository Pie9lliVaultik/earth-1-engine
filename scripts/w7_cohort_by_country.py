"""Within-country cohort seeds from raw W7 microdata (micro-test lesson:
pooled age gradients are composition-dominated; the instrument must
score country x age). Rules parsed from the official seeds file's own
notes column — no re-authoring. Min weighted N per cell: 150.
"""
from __future__ import annotations

import csv
import re

import duckdb

RAW = "/tmp/WVS_Cross-National_Wave_7_csv_v6_0.csv"
QCODES = ["Q57", "Q65", "Q71", "Q164", "Q180", "Q182", "Q184", "Q185"]

rules = {}
for r in csv.DictReader(open("data/wvs_wave7_seeds_official.csv")):
    m = re.search(r"wvs_code=(Q\d+);rule=([\w=-]+)", r["notes"])
    if m and m.group(1) in QCODES:
        rules[m.group(1)] = m.group(2)


def predicate(col: str, rule: str) -> str:
    if rule == "binary_yes=1":
        return f"({col} = 1)"
    if rule == "top2of4":
        return f"({col} IN (1,2))"
    if rule == "6-10of10":
        return f"({col} >= 6)"
    raise ValueError(rule)


con = duckdb.connect()
con.execute(
    f"CREATE VIEW w AS SELECT * FROM read_csv('{RAW}', header=true, "
    f"ignore_errors=true)")
out = open("data/wvs_w7_cohort_by_country.csv", "w")
out.write("qcode,country,age_bucket,yes_weighted,n_weighted\n")
n_cells = 0
for q, rule in rules.items():
    pred = predicate(q, rule)
    rows = con.execute(f"""
        SELECT B_COUNTRY_ALPHA AS cc,
               CASE WHEN Q262 BETWEEN 18 AND 29 THEN '18_29'
                    WHEN Q262 BETWEEN 30 AND 44 THEN '30_44'
                    WHEN Q262 BETWEEN 45 AND 59 THEN '45_59'
                    WHEN Q262 >= 60 THEN '60_plus' END AS bucket,
               SUM(CASE WHEN {pred} THEN W_WEIGHT ELSE 0 END) /
                   SUM(W_WEIGHT) AS yes_share,
               SUM(W_WEIGHT) AS nw
        FROM w
        WHERE {q} >= 0 AND Q262 >= 18 AND W_WEIGHT > 0
        GROUP BY cc, bucket
        HAVING SUM(W_WEIGHT) >= 150 AND bucket IS NOT NULL
    """).fetchall()
    for cc, bucket, ys, nw in rows:
        out.write(f"{q},{cc},{bucket},{ys:.5f},{nw:.1f}\n")
        n_cells += 1
out.close()
print(f"W7-COHORT-BY-COUNTRY: {n_cells} cells across {len(rules)} questions")
