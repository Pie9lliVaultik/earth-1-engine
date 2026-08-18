"""EXTREME RESPONSE STYLE vs TRUE POLARIZATION.

Before any operator is fitted to reproduce 0.647 extreme mass, split
that number into (a) country-level response STYLE — how much a country
picks endpoints regardless of item — and (b) the item/cell-specific
residual, which is the only part a physics of polarization should
reproduce.

Method: per country, extreme rate across ALL 1-10 items (style
constant). Per cell, observed extreme mass. Variance of cell extreme
mass explained by the country constant = style share. Residual target
= what the mechanism must actually match, after removing style.

Also emits data/cell_densities_ers.json: cell histograms with the
country's style component divided out and renormalized, so operators
can be fitted against polarization rather than against style.
"""
from __future__ import annotations

import json
import os
import sys

import duckdb
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAW = "/tmp/WVS_Cross-National_Wave_7_csv_v6_0.csv"
ALL_ITEMS = ["Q164", "Q182", "Q184", "Q185", "Q180", "Q186", "Q179", "Q181",
             "Q176", "Q177", "Q178", "Q183", "Q189", "Q192", "Q195",
             "Q199", "Q252", "Q250", "Q235", "Q29", "Q30", "Q31", "Q32"]


def main() -> None:
    from earth1.benchmark import ISO3_TO_ISO2
    con = duckdb.connect()
    con.execute(f"""CREATE VIEW w AS SELECT * FROM read_csv('{RAW}',
      header=true, delim=',', quote='"', escape='"', strict_mode=false,
      ignore_errors=true, max_line_size=10000000, null_padding=true)""")
    ok = []
    for q in ALL_ITEMS:
        try:
            con.execute(f"SELECT {q} FROM w LIMIT 1").fetchall()
            ok.append(q)
        except Exception:
            continue
    # country-level extreme response style across ALL items
    parts = " + ".join(
        f"CASE WHEN {q} IN (1,10) THEN W_WEIGHT WHEN {q} BETWEEN 1 AND 10 "
        f"THEN 0 ELSE 0 END" for q in ok)
    denom = " + ".join(
        f"CASE WHEN {q} BETWEEN 1 AND 10 THEN W_WEIGHT ELSE 0 END"
        for q in ok)
    rows = con.execute(f"""
        SELECT B_COUNTRY_ALPHA, SUM({parts}) / NULLIF(SUM({denom}), 0)
        FROM w WHERE W_WEIGHT > 0 GROUP BY B_COUNTRY_ALPHA""").fetchall()
    style = {}
    for cc, v in rows:
        i2 = ISO3_TO_ISO2.get(cc)
        if i2 and v is not None:
            style[i2] = float(v)
    vals = np.array(list(style.values()))
    print(f"ERS across {len(ok)} items, {len(style)} countries: "
          f"mean {vals.mean():.3f} | range {vals.min():.3f}-{vals.max():.3f} "
          f"| sd {vals.std():.3f}", flush=True)

    dens = json.load(open("data/cell_densities.json"))
    obs, sty, keys = [], [], []
    for qcode, cells in dens.items():
        for key, cell in cells.items():
            cc = key.split("|")[0]
            if cc in style:
                h = np.array(cell["hist"])
                obs.append(h[0] + h[-1])
                sty.append(style[cc])
                keys.append((qcode, key))
    obs, sty = np.array(obs), np.array(sty)
    r = float(np.corrcoef(sty, obs)[0, 1])
    beta = float(np.polyfit(sty, obs, 1)[0])
    pred = np.polyval(np.polyfit(sty, obs, 1), sty)
    r2 = 1 - ((obs - pred) ** 2).sum() / ((obs - obs.mean()) ** 2).sum()
    resid_target = float(np.mean(obs - pred + obs.mean() * 0))
    print(f"cell extreme mass {obs.mean():.3f} | explained by country "
          f"style: R2 {r2:.3f} (corr {r:.3f}, slope {beta:.2f})", flush=True)
    print(f"  => STYLE component ~{r2 * obs.mean():.3f} | "
          f"POLARIZATION target ~{(1 - r2) * obs.mean():.3f} "
          f"(residual sd {float(np.std(obs - pred)):.3f})", flush=True)

    # style-corrected densities: divide endpoint mass by the country's
    # style ratio, renormalize
    ref = float(np.mean(list(style.values())))
    out = {}
    for qcode, cells in dens.items():
        out[qcode] = {}
        for key, cell in cells.items():
            cc = key.split("|")[0]
            h = np.array(cell["hist"], dtype=float)
            if cc in style and style[cc] > 1e-6:
                adj = ref / style[cc]
                h[0] *= adj
                h[-1] *= adj
                h = h / h.sum()
            out[qcode][key] = {"hist": [round(float(x), 5) for x in h],
                               "n": cell["n"]}
    json.dump(out, open("data/cell_densities_ers.json", "w"), indent=1)
    ext_corr = float(np.mean([np.array(c["hist"])[0] + np.array(c["hist"])[-1]
                              for cs in out.values() for c in cs.values()]))
    json.dump({"ers_by_country": style, "raw_extreme_mass": float(obs.mean()),
               "style_r2": r2, "style_component": float(r2 * obs.mean()),
               "polarization_target": float((1 - r2) * obs.mean()),
               "corrected_extreme_mass": ext_corr},
              open("data/ers_decomposition.json", "w"), indent=1)
    print(f"ERS-VERDICT: raw target 0.647 -> style-corrected extreme mass "
          f"{ext_corr:.3f}; style explains R2 {r2:.3f} of cross-cell "
          f"variation", flush=True)


if __name__ == "__main__":
    main()
