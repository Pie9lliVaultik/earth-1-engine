"""DISTANCE FROM HUMANS — 2026-09-02 (founder order: one thing —
how far Earth-1 is from what real people actually said and did).

Computed from the frozen 200k x 3-seed LOO predictions (sb1_items_*),
named-entity abstention ON, cell-level survey n from the confirm
frames. Pew/GOQA carry no per-cell sample size, so their within-noise
and noise-unit columns read n/a — never an invented n.
Writes ops/alive/DISTANCE_FROM_HUMANS_2026-09-02.md + CSVs.
"""
import csv
import json
import math
import os
import sys
from collections import defaultdict

import statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "ops", "alive")
CSVD = os.path.join(ROOT, "data", "cycles", "distance2026")
os.makedirs(CSVD, exist_ok=True)

from earth1.genesis import GENESIS_COUNTRIES  # noqa: E402
CINFO = {c["iso2"]: c for c in GENESIS_COUNTRIES}

TAGS = json.load(open(os.path.join(
    ROOT, "data/concordance/named_entity_tags.json")))["tags"]
NS = {}
for fn, est in (("confirm_targets_v2.json", "wvs_heldout"),
                ("confirm_targets_v3.json", "wvs_extended")):
    ct = json.load(open(os.path.join(ROOT, "data/benchmark_a", fn)))
    NS[est] = {(it, iso): v["n"] for it, tg in ct["targets"].items()
               for iso, v in tg.items()}

cells = []
items_rows = []
for est in ("wvs_heldout", "wvs_extended", "goqa_dev"):
    d = json.load(open(os.path.join(ROOT, f"data/cycles/sb1_items_{est}.json")))
    for r in d["items"]:
        abstained = r["item"] in TAGS
        item_nd = []
        for iso, hum in r["country_truth"].items():
            err = r["country_e1_signed_err_pp"][iso] / 100.0
            model = hum + err
            n = NS.get(est, {}).get((r["item"], iso))
            se = (1.96 * math.sqrt(max(hum * (1 - hum), 1e-9) / n)
                  if n else None)
            nd = (abs(err) / se) if (se and se > 1e-9) else None
            cells.append({
                "estate": est, "item": r["item"], "family": r["family"],
                "country": iso, "region": CINFO.get(iso, {}).get("region"),
                "human": round(hum, 4), "model": round(model, 4),
                "signed_err_pp": round(err * 100, 2),
                "modal_agree": int((model > 0.5) == (hum > 0.5)),
                "n_survey": n,
                "se95_pp": round(se * 100, 2) if se else None,
                "within_noise": (int(abs(err) <= se) if se else None),
                "noise_dist": round(nd, 2) if nd is not None else None,
                "abstained": int(abstained),
                "mrsp_mae_pp": r["mrsp_mae_pp"],
                "naive_mae_pp": r["naive_mae_pp"],
                "region_mae_pp": r["region_mae_pp"]})
            if nd is not None:
                item_nd.append(nd)
        items_rows.append({
            "estate": est, "item": r["item"], "family": r["family"],
            "text": (r["text"] or "")[:140], "n_countries": r["n_countries"],
            "mae_pp": r["earth1_mae_pp"], "abstained": int(abstained),
            "median_noise_dist": (round(st.median(item_nd), 2)
                                  if item_nd else None)})

live = [c for c in cells if not c["abstained"]]
n_abst = sum(c["abstained"] for c in cells)


def pct(xs):
    return round(100 * sum(xs) / len(xs), 1) if xs else None


def roll(rows):
    ma = pct([c["modal_agree"] for c in rows])
    wn_rows = [c["within_noise"] for c in rows if c["within_noise"] is not None]
    wn = pct(wn_rows)
    nds = [c["noise_dist"] for c in rows if c["noise_dist"] is not None]
    med = round(st.median(nds), 2) if nds else None
    mae = round(st.mean(abs(c["signed_err_pp"]) for c in rows), 2)
    sgn = round(st.mean(c["signed_err_pp"] for c in rows), 2)
    hist = None
    if nds:
        hist = {"<=1": pct([n <= 1 for n in nds]),
                "1-2": pct([1 < n <= 2 for n in nds]),
                "2-4": pct([2 < n <= 4 for n in nds]),
                ">4": pct([n > 4 for n in nds])}
    return {"n_cells": len(rows), "majority_agree_pct": ma,
            "within_noise_pct": wn, "median_noise_dist": med,
            "mae_pp": mae, "signed_err_pp": sgn, "noise_hist": hist,
            "n_with_noise": len(nds)}


by_est = {e: roll([c for c in live if c["estate"] == e])
          for e in ("wvs_heldout", "wvs_extended", "goqa_dev")}
by_fam = {f: roll([c for c in live if c["family"] == f])
          for f in sorted({c["family"] for c in live})}
by_cty = {k: roll([c for c in live if c["country"] == k])
          for k in sorted({c["country"] for c in live})}
by_cty = {k: v for k, v in by_cty.items() if v["n_cells"] >= 40}
overall = roll(live)

fam_reg = defaultdict(list)
for c in live:
    if c["noise_dist"] is not None:
        fam_reg[(c["family"], c["region"])].append(c["noise_dist"])
heat = {k: round(st.median(v), 2) for k, v in fam_reg.items()
        if len(v) >= 30}

for name, rows, cols in (
        ("cells", cells, None),
        ("items", items_rows, None),
        ("countries", [{"country": k, **v, "noise_hist": json.dumps(
            v["noise_hist"])} for k, v in by_cty.items()], None),
        ("families", [{"family": k, **v, "noise_hist": json.dumps(
            v["noise_hist"])} for k, v in by_fam.items()], None)):
    p = os.path.join(CSVD, f"{name}.csv")
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

scored_items = [i for i in items_rows if not i["abstained"]]
wvs_items = [i for i in scored_items if i["median_noise_dist"] is not None]
closest = sorted(wvs_items, key=lambda i: i["median_noise_dist"])[:20]
farthest = sorted(wvs_items, key=lambda i: -i["median_noise_dist"])[:20]
cty_sorted = sorted(((k, v) for k, v in by_cty.items()
                     if v["median_noise_dist"] is not None),
                    key=lambda kv: kv[1]["median_noise_dist"])
best_fam = min(((k, v) for k, v in by_fam.items()
                if v["median_noise_dist"]), key=lambda kv: kv[1][
                    "median_noise_dist"])
worst_fam = max(((k, v) for k, v in by_fam.items()
                 if v["median_noise_dist"]), key=lambda kv: kv[1][
                     "median_noise_dist"])
regs = defaultdict(list)
for c in live:
    if c["noise_dist"] is not None:
        regs[c["region"]].append(c["noise_dist"])
reg_med = {k: round(st.median(v), 2) for k, v in regs.items()
           if len(v) >= 100}
best_reg = min(reg_med, key=reg_med.get)
worst_reg = max(reg_med, key=reg_med.get)

EV_DIRECTION_PCT = 40.0     # B-DEV flag battery, committed scoreboard
headline = [
    f"Majority agreement with humans: {overall['majority_agree_pct']}% "
    f"of {overall['n_cells']:,} scored (item,country) cells.",
    f"Within the survey's own 95% sampling noise: "
    f"{overall['within_noise_pct']}% of the {overall['n_with_noise']:,} "
    "cells where survey n is known (WVS estates).",
    f"Median distance: {overall['median_noise_dist']} noise units "
    f"(MAE {overall['mae_pp']}pp).",
    f"Best family {best_fam[0]} ({best_fam[1]['median_noise_dist']}σ), "
    f"worst {worst_fam[0]} ({worst_fam[1]['median_noise_dist']}σ); "
    f"best region {best_reg} ({reg_med[best_reg]}σ), worst {worst_reg} "
    f"({reg_med[worst_reg]}σ).",
    f"Events: {EV_DIRECTION_PCT:.0f}% of resolved-event direction calls "
    "match what happened (5-rep battery; most sub-significance — see "
    "events table); protest geography rank-corr with real onsets "
    "ρ=0.552 (p=0.005).",
]

md = ["# DISTANCE FROM HUMANS — 2026-09-02",
      "_One question: how far is Earth-1 from what real people actually "
      "said and did. Frozen 0.9 + adopted flags, 200k, 3 seeds, "
      "leave-one-country-out, named-entity abstention ON "
      f"({n_abst:,} cells abstained, excluded from both sides). "
      "Bible tiers exist and are not the subject of this report. "
      "Baselines are context columns only._", "", "## HEADLINE", ""]
md += [f"- {h}" for h in headline]
md += ["", "## BY ESTATE", "",
       "| estate | cells | majority-agree | within-noise | median σ-dist "
       "| MAE pp | signed pp | ≤1σ / 1–2σ / 2–4σ / >4σ |", "|" + "---|" * 8]
for e, v in by_est.items():
    h = v["noise_hist"] or {}
    md.append(f"| {e} | {v['n_cells']:,} | {v['majority_agree_pct']}% | "
              f"{v['within_noise_pct'] if v['within_noise_pct'] is not None else 'n/a (no cell n)'} | "
              f"{v['median_noise_dist'] or 'n/a'} | {v['mae_pp']} | "
              f"{v['signed_err_pp']:+} | "
              + (f"{h.get('<=1')}/{h.get('1-2')}/{h.get('2-4')}/{h.get('>4')}"
                 if h else "n/a") + " |")
md += ["", "## BY FAMILY (signed direction is the finding)", "",
       "| family | cells | majority | median σ | MAE | signed pp "
       "(+ = model too high) |", "|" + "---|" * 6]
for f_, v in sorted(by_fam.items(), key=lambda kv: kv[1]["mae_pp"]):
    md.append(f"| {f_} | {v['n_cells']:,} | {v['majority_agree_pct']}% | "
              f"{v['median_noise_dist'] or 'n/a'} | {v['mae_pp']} | "
              f"{v['signed_err_pp']:+} |")
md += ["", "## COUNTRIES — 10 CLOSEST / 10 FARTHEST (median σ-dist, ≥40 cells)", ""]
for tag, seg in (("closest", cty_sorted[:10]), ("farthest", cty_sorted[-10:])):
    md.append(f"**{tag}:** " + ", ".join(
        f"{k} ({v['median_noise_dist']}σ)" for k, v in seg))
md += ["", "## ITEMS — 20 CLOSEST / 20 FARTHEST (WVS, median σ-dist)", ""]
for tag, seg in (("CLOSEST", closest), ("FARTHEST", farthest)):
    md.append(f"### {tag}")
    for i in seg:
        md.append(f"- {i['item']} ({i['median_noise_dist']}σ, "
                  f"{i['family']}, {i['n_countries']}c) {i['text'][:90]}")
md += ["", "## FAMILY × REGION (median σ-dist, ≥30 cells)", ""]
fams = sorted({k[0] for k in heat})
regions = sorted({k[1] for k in heat if k[1]})
md.append("| family \\ region | " + " | ".join(regions) + " |")
md.append("|" + "---|" * (len(regions) + 1))
for f_ in fams:
    md.append(f"| {f_} | " + " | ".join(
        str(heat.get((f_, rg), "—")) for rg in regions) + " |")
md += ["", "## EVENTS — DISTANCE FROM WHAT HAPPENED", "",
       "From the committed flag-battery t-table and RETRODICTION_v1 "
       "(events with |t|<1 are indistinguishable from no-response at 5 "
       "reps — the honest 'within its own uncertainty' analog):", "",
       "| event | observable | model direction right? | significant? |",
       "|---|---|---|---|",
       "| covid_2020 | jobs | YES | yes (t=+2.2) |",
       "| covid_2020 | poverty | YES | borderline (t=+1.3) |",
       "| covid_2020 | displacement | YES | yes (t=+3.1) |",
       "| covid_2020 | hope | NO | no (t=+0.3) |",
       "| covid_2020 | deaths | NO | no (t=+1.0; channel absent) |",
       "| gfc_2008 | jobs | YES | no (t=+0.7) |",
       "| gfc_2008 | poverty | NO | no (t=−0.5) |",
       "| gfc_2008 | hope | NO | yes-wrong-sign (t=+2.1) |",
       "| arab_spring | govs/displacement/poverty | NO | no (all |t|≤1.2) |",
       "",
       "Direction agreement: 40% of scored calls (4/10); of the "
       "SIGNIFICANT responses (|t|≥2): 2 right-signed, 1 wrong-signed. "
       "Protest geography vs real GDELT-verified onsets: Spearman "
       "ρ=0.552, p=0.005, 13× separation, placebo clean.",
       "", "_Context columns (naive / region-copy / MrsP) are in "
       "cells.csv per cell at item granularity._"]

open(os.path.join(OUT, "DISTANCE_FROM_HUMANS_2026-09-02.md"),
     "w").write("\n".join(md) + "\n")
print("HEADLINE:")
for h in headline:
    print(" ", h)
print("report + CSVs written:", CSVD)
