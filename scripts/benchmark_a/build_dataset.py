"""Benchmark A Phase 2.1 — build the calibration dataset from the
FROZEN rules (BENCHMARK_A_PREREG_v1.md §1). Runs on prime (microdata).
Writes data/benchmark_a/targets_v1.json (+ manifest) and
/opt/earth1-data/benchmark_a/joint_vectors.npz (respondent-level binary
vectors per country, with weights — never committed)."""
import hashlib, json, os, re, sys
import duckdb, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from earth1.benchmark_questions import ISO3_TO_ISO2
from earth1.genesis import GENESIS_COUNTRY_CODES
DB = "/opt/earth1-data/benchmark_a/wvs7.duckdb"
OUT = os.path.join(ROOT, "data", "benchmark_a"); os.makedirs(OUT, exist_ok=True)
OUTD = "/opt/earth1-data/benchmark_a"
GT = json.load(open(os.path.join(ROOT, "data/benchmark/goqa_ground_truth.json")))
NEW = json.load(open(os.path.join(ROOT, "data/benchmark/benchmark_a_new_questions_v1.json")))["items"]
RULES = json.load(open(os.path.join(ROOT, "data/benchmark/goqa_gt_rule_diagnosis.json")))
con = duckdb.connect(DB, read_only=True)
MIN_N, MIN_CELL = 100, 50
SPECIAL = {"Q65": "=1", "Q222": "bottom3"}   # frozen scale rules for the two irreproducible items


def expr_for(c, rule, mx):
    if rule == "=1": return f"CASE WHEN {c}=1 THEN 1 ELSE 0 END"
    if rule == "=2": return f"CASE WHEN {c}=2 THEN 1 ELSE 0 END"
    if rule == "top2": return f"CASE WHEN {c} IN (1,2) THEN 1 ELSE 0 END"
    if rule == "top3": return f"CASE WHEN {c} IN (1,2,3) THEN 1 ELSE 0 END"
    if rule == "bottom2": return f"CASE WHEN {c} IN ({mx-1},{mx}) THEN 1 ELSE 0 END"
    if rule == "bottom3": return f"CASE WHEN {c} >= {mx-2} THEN 1 ELSE 0 END"
    m = re.fullmatch(r"(>=|<=)(\d+)", rule)
    if m: return f"CASE WHEN {c} {m.group(1)} {m.group(2)} THEN 1 ELSE 0 END"
    raise ValueError(rule)


def default_rule(mx):
    return "=1" if mx <= 2 else ("top2" if mx <= 5 else ">=6")


items = {}
for q in GT:
    c = q["id"]; mx = RULES[c]["scale"][1]
    items[c] = {"text": q["text"], "rule": SPECIAL.get(c, RULES[c]["best_rule"]), "scale_max": mx, "set": "goqa"}
for c, text in NEW.items():
    mn, mx = con.execute(f"SELECT min({c}), max({c}) FROM wvs WHERE {c} >= 0").fetchone()
    items[c] = {"text": text, "rule": default_rule(int(mx)), "scale_max": int(mx), "set": "new"}
targets = {}; cohorts = {}; manifest = {"items": {}, "countries": {}}
genesis = set(GENESIS_COUNTRY_CODES)
for c, it in items.items():
    e = expr_for(c, it["rule"], it["scale_max"])
    rows = con.execute(f"""SELECT B_COUNTRY_ALPHA, SUM(W_WEIGHT*({e}))/SUM(W_WEIGHT), count(*), SUM(W_WEIGHT)
        FROM wvs WHERE {c} IS NOT NULL AND {c}>=0 AND W_WEIGHT>0 GROUP BY 1""").fetchall()
    t = {}
    for iso3, share, n, sw in rows:
        iso2 = ISO3_TO_ISO2.get(iso3)
        if iso2 in genesis and n >= MIN_N:
            t[iso2] = {"yes": round(float(share), 6), "n": int(n)}
    targets[c] = t
    # cohort cells: age bands from Q262
    rows = con.execute(f"""SELECT B_COUNTRY_ALPHA, CASE WHEN Q262<30 THEN '18-29' WHEN Q262<50 THEN '30-49' ELSE '50+' END b,
        SUM(W_WEIGHT*({e}))/SUM(W_WEIGHT), count(*) FROM wvs WHERE {c} IS NOT NULL AND {c}>=0 AND W_WEIGHT>0 AND Q262>=18 GROUP BY 1,2""").fetchall()
    cc = {}
    for iso3, band, share, n in rows:
        iso2 = ISO3_TO_ISO2.get(iso3)
        if iso2 in genesis and n >= MIN_CELL and iso2 in t:
            cc.setdefault(iso2, {})[band] = {"yes": round(float(share), 6), "n": int(n)}
    cohorts[c] = cc
    manifest["items"][c] = {"rule": it["rule"], "scale_max": it["scale_max"], "set": it["set"], "n_countries": len(t), "n_cohort_cells": sum(len(v) for v in cc.values())}
# joint vectors: 8 GOQA items with widest coverage
cov = sorted([c for c in items if items[c]["set"] == "goqa"], key=lambda c: (-len(targets[c]), int(c[1:])))
joint_items = cov[:8]
exprs = ", ".join(expr_for(c, items[c]["rule"], items[c]["scale_max"]) + f" AS {c}_b" for c in joint_items)
cond = " AND ".join(f"{c} IS NOT NULL AND {c}>=0" for c in joint_items)
rows = con.execute(f"SELECT B_COUNTRY_ALPHA, W_WEIGHT, {exprs} FROM wvs WHERE {cond} AND W_WEIGHT>0").fetchall()
by = {}
for r in rows:
    iso2 = ISO3_TO_ISO2.get(r[0])
    if iso2 in genesis:
        by.setdefault(iso2, []).append(r[1:])
npz = {}
for iso2, rr in by.items():
    a = np.array(rr, float); npz[f"{iso2}_w"] = a[:, 0]; npz[f"{iso2}_x"] = a[:, 1:].astype(np.int8)
np.savez_compressed(os.path.join(OUTD, "joint_vectors_v1.npz"), **npz)
manifest["joint_items"] = joint_items; manifest["joint_countries"] = {k: len(v) for k, v in by.items()}
manifest["countries"] = sorted({iso for t in targets.values() for iso in t})
out = {"prereg": "ops/alive/BENCHMARK_A_PREREG_v1.md", "items": items, "targets": targets, "cohorts": cohorts, "manifest": manifest}
p = os.path.join(OUT, "targets_v1.json"); json.dump(out, open(p, "w"), indent=1, sort_keys=True)
print("targets sha256", hashlib.sha256(open(p, "rb").read()).hexdigest())
print("items", len(items), "countries", len(manifest["countries"]), "cohort cells", sum(v["n_cohort_cells"] for v in manifest["items"].values()), "joint items", joint_items, "joint countries", len(by))
