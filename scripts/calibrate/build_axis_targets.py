"""Build per-axis cohort DEV targets from WVS-7 microdata (prime).

Decomposition cycle (founder ruling): split the cohort miss by axis —
age band, education (Q275R), sex (Q260), income tercile (Q288R), and
age×edu — to name the axis that carries the error. Same item set and
rules as confirm_targets_v2 (consumed-as-DEV). WVS is DEV-cleared.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from earth1.benchmark_questions import ISO3_TO_ISO2  # noqa: E402
from earth1.dataroles import path_for  # noqa: E402

AXES = {
    "age": "CASE WHEN Q262<30 THEN 'a18-29' WHEN Q262<50 THEN 'a30-49' ELSE 'a50+' END",
    "edu": "CASE WHEN Q275R=1 THEN 'e_low' WHEN Q275R=2 THEN 'e_mid' ELSE 'e_high' END",
    "sex": "CASE WHEN Q260=1 THEN 's_m' ELSE 's_f' END",
    "income": "CASE WHEN Q288R=1 THEN 'i_low' WHEN Q288R=2 THEN 'i_mid' ELSE 'i_high' END",
    "age_edu": "(CASE WHEN Q262<30 THEN 'a18-29' WHEN Q262<50 THEN 'a30-49' ELSE 'a50+' END) || 'x' || (CASE WHEN Q275R=1 THEN 'e_low' WHEN Q275R=2 THEN 'e_mid' ELSE 'e_high' END)",
}
GUARDS = {"age": "Q262>=18", "edu": "Q275R IN (1,2,3)", "sex": "Q260 IN (1,2)",
          "income": "Q288R IN (1,2,3)",
          "age_edu": "Q262>=18 AND Q275R IN (1,2,3)"}


def main():
    import duckdb
    ct = json.load(open(os.path.join(
        ROOT, "data/benchmark_a/confirm_targets_v2.json")))
    con = duckdb.connect(path_for("wvs7_microdata", "training"),
                         read_only=True)
    exprs = {"=1": "{c}=1", "top2": "{c} IN (1,2)", ">=6": "{c}>=6"}
    out = {ax: {} for ax in AXES}
    for c, meta in ct["items"].items():
        e = f"CASE WHEN {exprs[meta['rule']].format(c=c)} THEN 1 ELSE 0 END"
        for ax, expr in AXES.items():
            rows = con.execute(
                f"SELECT B_COUNTRY_ALPHA, {expr}, "
                f"SUM(W_WEIGHT*({e}))/SUM(W_WEIGHT), count(*) FROM wvs "
                f"WHERE {c} IS NOT NULL AND {c}>=0 AND W_WEIGHT>0 "
                f"AND {GUARDS[ax]} GROUP BY 1,2").fetchall()
            cc = {}
            for iso3, cell, share, n in rows:
                iso2 = ISO3_TO_ISO2.get(iso3)
                if iso2 and n >= 50:
                    cc.setdefault(iso2, {})[cell] = {
                        "yes": round(float(share), 6), "n": int(n)}
            if cc:
                out[ax][c] = cc
    p = os.path.join(ROOT, "data/benchmark_a/axis_targets_v1.json")
    json.dump({"axes": out, "items": len(ct["items"]),
               "source": "wvs7.duckdb via confirm_targets_v2 rules"},
              open(p, "w"))
    for ax in AXES:
        print(ax, len(out[ax]), "items")
    print("WROTE", p)


if __name__ == "__main__":
    main()
