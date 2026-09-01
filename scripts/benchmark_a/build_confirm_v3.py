"""WVS-EXTENDED estate builder (founder challenge 2026-09-01: "the WVS
doesn't have only 141 questions").

Measured: the wvs7.duckdb holds 331 Q-columns; imported_vnf's labels file
covers 141, and that curation gap — not the WVS, not the protocol — is
why only 98 items were judged. This builder registers the UNLABELED
substantive-core items (Qnum <= 259) that pass the SAME frozen rules the
98 passed (registered binarization; >=40 genesis countries x n>=100),
excluding GOQA-overlap ids, the 8 consumed seeds, and R-suffixed recode
duplicates of a base item already present.

Output: confirm_targets_v2.json inside EARTH1_AV2_OUT (the frozen run_v2
stages read that fixed name — pointing them at a SEPARATE OUT dir keeps
the pipeline byte-identical while the estate differs; the stamp inside
the file says WVS_EXTENDED_v3). The frozen 98-item v2 estate and the
18,333 frozen cohort cells are untouched.

Question texts: PENDING_FETCH (official WVS-7 codebook) — scoring never
consumes text; texts are provenance to be filled before publication.
"""
import json
import os
import re
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

CONSUMED = {"Q10", "Q23", "Q51", "Q68", "Q86", "Q138", "Q169", "Q196"}
OUT = os.path.join(ROOT, "data", "benchmark_a")
DUCK = "/opt/earth1-data/benchmark_a/wvs7.duckdb"


def main():
    import duckdb
    import subprocess
    import time
    from earth1.benchmark_questions import ISO3_TO_ISO2
    from earth1.genesis import GENESIS_COUNTRY_CODES
    ns = {}
    exec(open(os.path.join(ROOT, "imported_vnf/scripts/wvs7_labels.py")).read(), ns)
    L = ns.get("LABELS") or ns.get("labels")
    goqa = {q["id"] for q in json.load(
        open(os.path.join(ROOT, "data/benchmark/goqa_ground_truth.json")))}
    con = duckdb.connect(DUCK, read_only=True)
    cols = [r[1] for r in con.execute("PRAGMA table_info(wvs)").fetchall()]
    qcols = [c for c in cols if re.fullmatch(r"Q\d+[A-Z]*", c)]
    base = {c for c in qcols if re.fullmatch(r"Q\d+", c)}
    cand = sorted(
        [c for c in qcols
         if c not in L and c not in goqa and c not in CONSUMED
         and int(re.match(r"Q(\d+)", c).group(1)) <= 259
         and not (re.fullmatch(r"Q\d+[A-Z]+", c)
                  and re.match(r"Q\d+", c).group(0) in base)],
        key=lambda k: (int(re.match(r"Q(\d+)", k).group(1)), k))
    genesis = set(GENESIS_COUNTRY_CODES)
    items, targets, cohorts = {}, {}, {}
    for c in cand:
        try:
            mn, mx = con.execute(
                f"SELECT min({c}), max({c}) FROM wvs WHERE {c} >= 0").fetchone()
        except Exception:
            continue
        if mx is None:
            continue
        mx = int(mx)
        if mx <= 2:
            rule, e = "=1", f"CASE WHEN {c}=1 THEN 1 ELSE 0 END"
        elif mx <= 5:
            rule, e = "top2", f"CASE WHEN {c} IN (1,2) THEN 1 ELSE 0 END"
        elif mx == 10:
            rule, e = ">=6", f"CASE WHEN {c}>=6 THEN 1 ELSE 0 END"
        else:
            continue
        rows = con.execute(
            f"SELECT B_COUNTRY_ALPHA, SUM(W_WEIGHT*({e}))/SUM(W_WEIGHT), count(*) "
            f"FROM wvs WHERE {c} IS NOT NULL AND {c}>=0 AND W_WEIGHT>0 "
            f"GROUP BY 1").fetchall()
        t = {ISO3_TO_ISO2.get(r[0]): {"yes": round(float(r[1]), 6), "n": int(r[2])}
             for r in rows
             if ISO3_TO_ISO2.get(r[0]) in genesis and r[2] >= 100}
        if len(t) < 40:
            continue
        rows = con.execute(
            f"SELECT B_COUNTRY_ALPHA, CASE WHEN Q262<30 THEN '18-29' "
            f"WHEN Q262<50 THEN '30-49' ELSE '50+' END, "
            f"SUM(W_WEIGHT*({e}))/SUM(W_WEIGHT), count(*) FROM wvs "
            f"WHERE {c} IS NOT NULL AND {c}>=0 AND W_WEIGHT>0 AND Q262>=18 "
            f"GROUP BY 1,2").fetchall()
        cc = {}
        for iso3, band, share, n in rows:
            iso2 = ISO3_TO_ISO2.get(iso3)
            if iso2 in t and n >= 50:
                cc.setdefault(iso2, {})[band] = {"yes": round(float(share), 6),
                                                 "n": int(n)}
        items[c] = {"text": "PENDING_FETCH (WVS-7 official codebook)",
                    "rule": rule, "scale_max": mx}
        targets[c] = t
        cohorts[c] = cc
    conf = sorted(items, key=lambda k: (int(re.match(r"Q(\d+)", k).group(1)), k))
    joint_items = sorted(conf, key=lambda c: (-len(targets[c]),
                                              int(re.match(r"Q(\d+)", c).group(1))))[:8]
    stride = max(1, len(conf) // 8)
    zeroshot = [conf[i] for i in range(0, len(conf), stride)][:8]
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                         text=True, cwd=ROOT).stdout.strip()
    out = {"items": items, "targets": targets, "cohorts": cohorts,
           "joint_items": joint_items, "zeroshot_items": zeroshot,
           "n_items": len(conf),
           "stamp": {"estate": "WVS_EXTENDED_v3",
                     "note": ("unlabeled substantive-core items; same frozen "
                              "rules as v2; texts PENDING_FETCH; v2 estate "
                              "and frozen cells untouched"),
                     "commit": sha,
                     "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}}
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "confirm_targets_v3.json")
    json.dump(out, open(p, "w"), indent=1, sort_keys=True)
    print("WVS_EXTENDED_v3 BUILT:", len(conf), "items ->", p)
    print("joints:", joint_items, "zeroshot:", zeroshot)


if __name__ == "__main__":
    main()
