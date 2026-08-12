#!/usr/bin/env python3
"""Seed the retrieval corpus with calibrated GOQA questions (bible §19.1).

For every GlobalOpinionQA question with >=3 mapped countries, solve the
force weights against per-country survey targets (same ridge protocol as
the benchmark run) and store (text, baseline, weights) in the corpus.

Then measure the novelty frontier: leave-one-out hit rate at min_sim=0.85
and the weight-cosine between the query's own solved weights and the
retrieved neighbour's — i.e. when retrieval fires, how good are the
loadings it supplies?
"""
import sys, json, time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from earth1.engine import build_genesis_civilization
from earth1.genesis import GENESIS_COUNTRY_CODES
from earth1.calibration import calibrate_single
from earth1.corpus import QuestionCorpus
from earth1.rng import logit

GOQA_PATH = "/tmp/goqa_parsed.json"
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "corpus" / "goqa_seed"

NAME_TO_ISO2 = {
    "Albania":"AL","Andorra":"AD","Angola":"AO","Argentina":"AR","Armenia":"AM",
    "Australia":"AU","Austria":"AT","Azerbaijan":"AZ","Bangladesh":"BD","Belarus":"BY",
    "Belgium":"BE","Bolivia":"BO","Bosnia Herzegovina":"BA","Brazil":"BR",
    "Britain":"GB","Bulgaria":"BG","Burkina Faso":"BF","Canada":"CA","Chile":"CL",
    "China":"CN","Colombia":"CO","Croatia":"HR","Cyprus":"CY","Czech Rep.":"CZ",
    "Czechia":"CZ","Denmark":"DK","Ecuador":"EC","Egypt":"EG","El Salvador":"SV",
    "Estonia":"EE","Ethiopia":"ET","Finland":"FI","France":"FR","Georgia":"GE",
    "Germany":"DE","Ghana":"GH","Great Britain":"GB","Greece":"GR","Guatemala":"GT",
    "Honduras":"HN","Hong Kong SAR":"HK","Hungary":"HU","Iceland":"IS","India":"IN",
    "Indonesia":"ID","Iran":"IR","Iraq":"IQ","Israel":"IL","Italy":"IT",
    "Ivory Coast":"CI","Japan":"JP","Jordan":"JO","Kazakhstan":"KZ","Kenya":"KE",
    "Kuwait":"KW","Kyrgyzstan":"KG","Latvia":"LV","Lebanon":"LB","Libya":"LY",
    "Lithuania":"LT","Macau SAR":"MO","Malaysia":"MY","Maldives":"MV","Mali":"ML",
    "Mexico":"MX","Mongolia":"MN","Montenegro":"ME","Morocco":"MA","Myanmar":"MM",
    "Netherlands":"NL","New Zealand":"NZ","Nicaragua":"NI","Nigeria":"NG",
    "North Macedonia":"MK","Northern Ireland":"GB","Norway":"NO","Pakistan":"PK",
    "Palest. ter.":"PS","Palestine":"PS","Peru":"PE","Philippines":"PH","Poland":"PL",
    "Portugal":"PT","Puerto Rico":"PR","Romania":"RO","Russia":"RU","S. Africa":"ZA",
    "S. Korea":"KR","Senegal":"SN","Serbia":"RS","Singapore":"SG","Slovakia":"SK",
    "Slovenia":"SI","South Korea":"KR","Spain":"ES","Sweden":"SE","Switzerland":"CH",
    "Taiwan":"TW","Taiwan ROC":"TW","Tajikistan":"TJ","Tanzania":"TZ","Thailand":"TH",
    "Tunisia":"TN","Turkey":"TR","Türkiye":"TR","Uganda":"UG","Ukraine":"UA",
    "United States":"US","Uruguay":"UY","Uzbekistan":"UZ","Venezuela":"VE",
    "Vietnam":"VN","Zimbabwe":"ZW","Colombia ":"CO","Czech Republic":"CZ",
    "South Africa":"ZA","United Kingdom":"GB","U.S.":"US","U.K.":"GB",
}
SKIP_SUFFIXES = ["(Non-national sample)", "(Current national sample)", "(Old national sample)"]


def dist_to_scalar(dist):
    n = len(dist)
    e = np.asarray(dist, dtype=np.float64).copy()
    s = e.sum()
    if s > 0:
        e /= s
    return float(np.dot(e, np.linspace(0, 1, n)))


def main():
    t0 = time.time()
    civ = build_genesis_civilization(200_000, seed=42)
    code_to_idx = {c: i for i, c in enumerate(GENESIS_COUNTRY_CODES)}
    country_masks = {}
    for iso2 in set(GENESIS_COUNTRY_CODES):
        mask = civ.country == code_to_idx[iso2]
        if mask.sum() >= 50:
            country_masks[iso2] = mask
    print(f"Civ: {civ.n:,} agents ({time.time()-t0:.0f}s)")

    with open(GOQA_PATH) as f:
        questions = json.load(f)

    ids, texts, baselines, weight_rows = [], [], [], []
    for qi, q in enumerate(questions):
        targets = {}
        for cname, dist in q["selections"].items():
            if any(cname.endswith(s) for s in SKIP_SUFFIXES):
                continue
            iso2 = NAME_TO_ISO2.get(cname)
            if iso2 and iso2 in country_masks:
                targets[iso2] = dist_to_scalar(dist)
        if len(targets) < 3:
            continue

        total_a = sum(int(country_masks[c].sum()) for c in targets)
        bl = float(np.clip(
            sum(v * int(country_masks[c].sum()) for c, v in targets.items()) / total_a,
            0.02, 0.98))
        w = calibrate_single(civ, bl, targets, ridge_alpha=0.1)
        ids.append(f"goqa_{qi}")
        texts.append(q["question"])
        baselines.append(logit(np.array([bl]))[0])
        weight_rows.append(w)

        if (qi + 1) % 500 == 0:
            print(f"  [{qi+1}/{len(questions)}] solved={len(ids)}")

    corpus = QuestionCorpus()
    corpus.build(
        ids=ids, texts=texts,
        baselines=np.array(baselines), weights=np.stack(weight_rows),
        sources=["goqa_w7_calibrated"] * len(ids),
    )
    corpus.save(OUT_PATH)
    print(f"Corpus: {len(corpus)} solved questions -> {OUT_PATH}.npz/.json "
          f"({time.time()-t0:.0f}s)")

    # ── Novelty-frontier evaluation (leave-one-out) ──
    hits, sims, wcos = 0, [], []
    rng = np.random.default_rng(7)
    sample = rng.choice(len(corpus), size=min(500, len(corpus)), replace=False)
    for i in sample:
        hit = corpus.nearest(corpus.texts[i], min_sim=0.85, exclude_id=corpus.ids[i])
        if hit is None:
            continue
        hits += 1
        sims.append(hit.similarity)
        a, b = corpus.weights[i], hit.weights
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na > 0 and nb > 0:
            wcos.append(float(a @ b / (na * nb)))

    print()
    print(f"LOO retrieval @0.85 over {len(sample)} queries:")
    print(f"  hit rate:          {hits/len(sample):.1%}")
    if sims:
        print(f"  mean similarity:   {np.mean(sims):.3f}")
        print(f"  weight cosine:     {np.mean(wcos):.3f}  "
              f"(retrieved loadings vs query's own solved loadings)")
    print("\nDONE")


if __name__ == "__main__":
    main()
