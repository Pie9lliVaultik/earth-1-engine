"""Phase 0.3 — recompute the 40 GOQA country targets from the official
WVS-7 v6.0 microdata (design weights W_WEIGHT, the registered
yes-coding rule) and compare with data/benchmark/goqa_ground_truth.json.
Runs where the microdata is (prime: /opt/earth1/rawdata)."""
import hashlib, json, os, re, sys
import duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.environ.get("WVS7_CSV", "/opt/earth1/rawdata/WVS_Cross-National_Wave_7_csv_v6_0.csv")
GT = json.load(open(os.path.join(ROOT, "data/benchmark/goqa_ground_truth.json")))
h = hashlib.sha256()
with open(RAW, "rb") as f:
    for c in iter(lambda: f.read(1 << 22), b""): h.update(c)
print("microdata sha256", h.hexdigest())
con = duckdb.connect()
con.execute(f"CREATE VIEW w AS SELECT * FROM read_csv('{RAW}', header=true, strict_mode=false, ignore_errors=true, max_line_size=10000000, null_padding=true)")
def rule(mx):
    if mx <= 2: return "CASE WHEN {c} = 1 THEN 1.0 ELSE 0.0 END"
    if mx <= 5: return "CASE WHEN {c} IN (1,2) THEN 1.0 ELSE 0.0 END"
    if mx == 10: return "CASE WHEN {c} BETWEEN 6 AND 10 THEN 1.0 ELSE 0.0 END"
    return None
worst = 0.0; rows = 0; bad = []
for q in GT:
    c = q["id"]
    mx = con.execute(f"SELECT max({c}) FROM w WHERE {c} >= 0").fetchone()[0]
    expr = rule(int(mx)).format(c=c)
    res = con.execute(f"SELECT B_COUNTRY_ALPHA, SUM(W_WEIGHT*{expr})/SUM(W_WEIGHT), count(*) FROM w WHERE {c} IS NOT NULL AND {c} >= 0 AND W_WEIGHT > 0 GROUP BY 1").fetchall()
    mine = {r[0]: float(r[1]) for r in res}
    for iso3, v in q["countries"].items():
        if iso3 in mine:
            d = abs(mine[iso3] - v["yes"]); worst = max(worst, d); rows += 1
            if d > 0.005: bad.append((c, iso3, round(v["yes"], 4), round(mine[iso3], 4)))
print(f"cells compared {rows}; max |recomputed - file| = {worst:.5f}; mismatches >0.5pp: {len(bad)}")
for b in bad[:10]: print("  ", b)
json.dump({"microdata_sha256": h.hexdigest(), "cells": rows, "max_abs_diff": worst, "mismatches_gt_0p5pp": bad}, open(os.path.join(ROOT, "data/benchmark/goqa_ground_truth_verification.json"), "w"), indent=1)
print("GROUND_TRUTH", "VERIFIED" if not bad else "MISMATCH")
