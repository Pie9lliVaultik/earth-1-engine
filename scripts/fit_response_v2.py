#!/usr/bin/env python3
"""Temporal response v2: question-conditioned coupling, one fitted gain.

  d_logit = gain * (shock . response_profile(question))

Both structures are LLM-authored BLIND to outcomes (event shocks from
headlines; response profiles from question text). Sign prediction is
therefore PARAMETER-FREE: with gain > 0, sign(pred) = sign(coupling).
Only the scalar gain is fitted (LOO by case for magnitudes).
"""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
from earth1.reaction_cases import REACTION_CASES
from earth1.news_perception import perceive_question_response
from earth1.types import NUM_FORCES
from earth1.rng import logit, sigmoid

CACHE = ROOT / "data" / "perceived_cases.json"
QCACHE = ROOT / "data" / "question_profiles.json"


def main():
    cache = json.loads(CACHE.read_text())
    qcache = json.loads(QCACHE.read_text()) if QCACHE.exists() else {}

    for case in REACTION_CASES:
        if case.id not in qcache:
            prof = perceive_question_response(case.question_text)
            qcache[case.id] = list(map(float, prof))
            QCACHE.write_text(json.dumps(qcache, indent=1))
            print(f"profiled: {case.id}")

    obs = []
    for case in REACTION_CASES:
        prof = np.array(qcache[case.id])
        by_country = {}
        for item in case.headlines:
            key = f"{case.id}|{item.country}|{item.title[:40]}"
            p = cache.get(key)
            if p is None:
                continue
            v = np.zeros(NUM_FORCES)
            for k, d in p["deltas"].items():
                v[int(k)] = d
            by_country.setdefault(item.country, []).append(v)
        for cc, vecs in by_country.items():
            if cc not in case.pre:
                continue
            shock = np.mean(vecs, axis=0)
            coupling = float(shock @ prof)
            d = float(logit(np.array([case.post[cc]]))[0]
                      - logit(np.array([case.pre[cc]]))[0])
            obs.append({"case": case.id, "country": cc,
                        "coupling": coupling, "d_logit": d,
                        "pre": case.pre[cc], "post": case.post[cc]})

    print(f"\n{len(obs)} observations, sign test is PARAMETER-FREE:")
    print(f"{'case':22s} {'cc':4s} {'coupling':>9s} {'meas_d':>8s} {'sign':>5s}")
    hits = 0
    for o in obs:
        meas_d = o["post"] - o["pre"]
        ok = np.sign(o["coupling"]) == np.sign(meas_d)
        hits += int(ok)
        print(f"{o['case']:22s} {o['country']:4s} {o['coupling']:>+9.4f} "
              f"{meas_d:>+8.4f} {'OK' if ok else 'X':>5s}")
    n = len(obs)
    from scipy import stats
    p = stats.binomtest(hits, n, 0.5, alternative="greater").pvalue
    print(f"\nsign accuracy: {hits}/{n} = {hits/n:.0%}  (binomial p={p:.4f})")

    # one-parameter gain, LOO by case, magnitude check
    cases = sorted({o["case"] for o in obs})
    print("\nLOO magnitudes (gain fitted without held case):")
    for held in cases:
        train = [o for o in obs if o["case"] != held]
        c = np.array([o["coupling"] for o in train])
        d = np.array([o["d_logit"] for o in train])
        gain = float((c @ d) / (c @ c)) if c @ c > 0 else 0.0
        for o in [o for o in obs if o["case"] == held]:
            pred_post = float(sigmoid(logit(np.array([o["pre"]]))[0]
                                      + gain * o["coupling"]))
            print(f"  {held:22s} {o['country']:4s} "
                  f"pred {pred_post - o['pre']:+.4f} vs meas "
                  f"{o['post'] - o['pre']:+.4f}  (gain {gain:.1f})")

if __name__ == "__main__":
    main()
