"""R5 LIVE — can the grounding cascade find real data on the open web?

Prereg: data/r5_live_prereg.json (registered before this ran).

This is the rung that tests the PRODUCT rather than the engine. The
seed corpus is DISABLED so Path A and Path B cannot fire; the cascade
is forced onto Path D, the live web search. The number it comes back
with is scored against WVS Wave 7 verified microdata.

Three arms on identical items:
  LIVE    Path D live retrieval
  NAIVE   grand mean of the item across all WVS7 countries
  ENGINE  Path C forward-estimate, the population's own structure

Env: R5_N (default 6 pairs), R5_POP (default 200000).
"""
from __future__ import annotations

import csv
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.benchmark_questions import ISO3_TO_ISO2
from earth1.calibration import _build_features, _get_country_index
from earth1.genesis import genesis
from earth1.live_search import live_ground
from earth1.rng import logit, sigmoid

N_PAIRS = int(os.environ.get("R5_N", "6"))
POP = int(os.environ.get("R5_POP", "200000"))

QTEXT = {
    "Q57": "Generally speaking, would you say that most people can be trusted?",
    "Q65": "How much confidence do you have in the churches?",
    "Q71": "How much confidence do you have in the government?",
    "Q164": "How important is God in your life?",
    "Q180": "Is claiming government benefits you are not entitled to justifiable?",
    "Q182": "Is homosexuality justifiable?",
    "Q184": "Is abortion justifiable?",
    "Q185": "Is divorce justifiable?",
}
# countries with the most published third-party polling, so Path D has a
# genuine chance of finding an INDEPENDENT source rather than the WVS
PREFERRED = ["USA", "GBR", "DEU", "BRA", "JPN", "CAN", "AUS", "NLD"]


def national_truth() -> dict:
    """Reconstruct WVS7 national shares as n-weighted means over buckets."""
    acc: dict = {}
    for r in csv.DictReader(open("data/wvs_w7_cohort_by_country.csv")):
        n = float(r["n_weighted"])
        acc.setdefault(r["qcode"], {}).setdefault(r["country"], [0.0, 0.0])
        a = acc[r["qcode"]][r["country"]]
        a[0] += float(r["yes_weighted"]) * n
        a[1] += n
    return {q: {c: v[0] / v[1] for c, v in by_c.items() if v[1] > 0}
            for q, by_c in acc.items()}


def main() -> None:
    truth = national_truth()
    civ = genesis(POP, 42)
    c2i, _ = _get_country_index(civ)
    feats = _build_features(civ, extended=True)

    # build the item list: preferred countries first, one item each so
    # the small run spans all 8 questions rather than 6 of one question
    pairs = []
    for q in QTEXT:
        for iso3 in PREFERRED:
            iso2 = ISO3_TO_ISO2.get(iso3)
            if iso2 and iso2 in c2i and iso3 in truth.get(q, {}):
                pairs.append((q, iso3, iso2))
                break
    pairs = pairs[:N_PAIRS]

    rows = []
    for q, iso3, iso2 in pairs:
        t = truth[q][iso3]
        grand = float(np.mean(list(truth[q].values())))

        # ENGINE: Path C, no grounding, population answers from structure.
        # The forward estimate is the population's own mean stance with
        # the item's global level as the only anchor.
        m = civ.country == c2i[iso2]
        z = logit(np.array([grand]))[0] + feats[m] @ np.zeros(feats.shape[1])
        engine = float(sigmoid(z).mean())

        # LIVE: Path D, corpus disabled by construction (live_ground
        # never reads the corpus)
        g = live_ground(QTEXT[q], population=iso2, persist=True)
        got = (g.calibration_source == "live-grounded"
               and g.national_target is not None)
        row = {"qcode": q, "question": QTEXT[q], "country": iso3,
               "truth": round(t, 4), "naive": round(grand, 4),
               "engine": round(engine, 4),
               "retrieved": bool(got),
               "live": round(float(g.national_target), 4) if got else None,
               "source": g.source, "url": g.source_url, "date": g.date,
               "note": g.note}
        rows.append(row)
        tag = (f"live {row['live']:.3f} <- {str(g.source)[:28]}" if got
               else f"NO RETRIEVAL ({str(g.note)[:40]})")
        print(f"  {q:5s} {iso3}  truth {t:.3f} | naive {grand:.3f} | "
              f"{tag}", flush=True)

    hit = [r for r in rows if r["retrieved"]]
    rate = len(hit) / max(len(rows), 1)
    out = {"prereg": "data/r5_live_prereg.json", "n_items": len(rows),
           "retrieval_rate": round(rate, 3), "rows": rows}
    if hit:
        out["live_mae"] = float(np.mean([abs(r["live"] - r["truth"])
                                         for r in hit]))
        out["naive_mae"] = float(np.mean([abs(r["naive"] - r["truth"])
                                          for r in hit]))
        out["engine_mae"] = float(np.mean([abs(r["engine"] - r["truth"])
                                           for r in hit]))
        # independent reach: did Path D find something that is NOT the WVS?
        indep = [r for r in hit
                 if "world values" not in str(r["source"]).lower()
                 and "wvs" not in str(r["source"]).lower()]
        out["independent_source_rate"] = round(len(indep) / len(hit), 3)
        if indep:
            out["live_mae_independent_only"] = float(
                np.mean([abs(r["live"] - r["truth"]) for r in indep]))
    json.dump(out, open("data/r5_live_test.json", "w"), indent=1)

    print(f"\n  retrieval rate {rate:.0%} "
          f"({len(hit)}/{len(rows)}), bar was 60%", flush=True)
    if not hit:
        print("R5 VERDICT: FAIL — nothing retrieved, no MAE to report",
              flush=True)
        return
    print(f"  LIVE   MAE {out['live_mae']:.4f}", flush=True)
    print(f"  NAIVE  MAE {out['naive_mae']:.4f}", flush=True)
    print(f"  ENGINE MAE {out['engine_mae']:.4f}", flush=True)
    print(f"  independent (non-WVS) sources: "
          f"{out['independent_source_rate']:.0%}", flush=True)
    beats = out["live_mae"] < out["naive_mae"]
    passed = beats and rate >= 0.60
    print(f"R5 VERDICT: {'PASS' if passed else 'FAIL'} — live "
          f"{'beats' if beats else 'loses to'} naive "
          f"({out['live_mae']:.4f} vs {out['naive_mae']:.4f}), "
          f"retrieval {rate:.0%}", flush=True)


if __name__ == "__main__":
    main()
