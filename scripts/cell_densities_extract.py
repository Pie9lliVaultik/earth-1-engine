"""Real WITHIN-CELL answer DENSITIES from WVS7 microdata.

Not means — the full weighted response histogram per
(question, country, age bucket, education) cell. This is the substrate
the distributional ruler needs: real people inside one cell disagree
by a specific, measurable amount.

Questions: the 1-10 justifiability/importance scales (10 bins each),
which carry genuine within-cell shape (often bimodal).
Output: data/cell_densities.json
  {qcode: {"iso2|age_b|edu": {"hist": [10 weighted shares], "n": w}}}
"""
from __future__ import annotations

import json
import os
import sys

import duckdb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAW = "/tmp/WVS_Cross-National_Wave_7_csv_v6_0.csv"
# 1-10 scale items (GOQA-scored ones included: the DENSITY is not the
# benchmark target, which is a binarized share — this is a richer view
# of the same items, used only for the distributional instrument)
QCODES = ["Q164", "Q182", "Q184", "Q185", "Q180", "Q186", "Q179", "Q181"]
MIN_W = 40.0


def main() -> None:
    from earth1.benchmark import ISO3_TO_ISO2
    con = duckdb.connect()
    con.execute(f"""CREATE VIEW w AS SELECT * FROM read_csv('{RAW}',
      header=true, delim=',', quote='"', escape='"', strict_mode=false,
      ignore_errors=true, max_line_size=10000000, null_padding=true)""")
    out = {}
    for q in QCODES:
        try:
            rows = con.execute(f"""
                SELECT B_COUNTRY_ALPHA AS cc,
                       CASE WHEN Q262 BETWEEN 18 AND 29 THEN 0
                            WHEN Q262 BETWEEN 30 AND 44 THEN 1
                            WHEN Q262 BETWEEN 45 AND 59 THEN 2
                            WHEN Q262 >= 60 THEN 3 END AS age_b,
                       CASE WHEN Q275 <= 2 THEN 0 WHEN Q275 <= 5 THEN 1
                            ELSE 2 END AS edu,
                       {q} AS val,
                       SUM(W_WEIGHT) AS wt
                FROM w
                WHERE {q} BETWEEN 1 AND 10 AND Q262 >= 18 AND Q275 >= 0
                  AND W_WEIGHT > 0
                GROUP BY cc, age_b, edu, val""").fetchall()
        except Exception as exc:
            print(f"  {q}: skipped ({str(exc)[:50]})", flush=True)
            continue
        acc = {}
        for cc, a, e, val, wt in rows:
            i2 = ISO3_TO_ISO2.get(cc)
            if not i2 or a is None:
                continue
            k = f"{i2}|{a}|{e}"
            d = acc.setdefault(k, [0.0] * 10)
            d[int(val) - 1] += float(wt)
        cells = {}
        for k, hist in acc.items():
            tot = sum(hist)
            if tot >= MIN_W:
                cells[k] = {"hist": [round(x / tot, 5) for x in hist],
                            "n": round(tot, 1)}
        if cells:
            out[q] = cells
            import numpy as np
            # how bimodal is reality? mass in the extremes vs middle
            ext = np.mean([c["hist"][0] + c["hist"][9] for c in cells.values()])
            mid = np.mean([sum(c["hist"][4:6]) for c in cells.values()])
            print(f"  {q}: {len(cells)} cells | extreme mass {ext:.3f} vs "
                  f"middle mass {mid:.3f}", flush=True)
    json.dump(out, open("data/cell_densities.json", "w"), indent=1)
    print(f"CELL-DENSITIES: {sum(len(v) for v in out.values())} cells "
          f"across {len(out)} questions", flush=True)


if __name__ == "__main__":
    main()
