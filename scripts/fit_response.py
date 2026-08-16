#!/usr/bin/env python3
"""Fit the temporal response operator on the reaction-case library.

Model (deliberately minimal, 8 params + intercept-free):
    d_logit(opinion) = response . shock
where shock is the LLM-perceived force-delta vector for the case's
country and response is a global 8-vector (sign AND gain per force),
ridge-fit on case-country observations.

Validation: leave-one-CASE-out. A case's observations never touch the
parameters that predict it. Reported: per-case predicted vs measured
delta, sign accuracy, magnitude ratio.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import json
import numpy as np
from earth1.reaction_cases import REACTION_CASES
from earth1.news_perception import perceive_item
from earth1.types import NUM_FORCES, Force
from earth1.rng import logit

CACHE = ROOT / "data" / "perceived_cases.json"


def perceive_all():
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    for case in REACTION_CASES:
        for item in case.headlines:
            key = f"{case.id}|{item.country}|{item.title[:40]}"
            if key in cache:
                continue
            ev = perceive_item(item)
            cache[key] = (None if ev is None else
                          {"deltas": {str(k): v for k, v in ev.force_deltas.items()},
                           "confidence": ev.confidence,
                           "decay": ev.decay_half_life})
            CACHE.write_text(json.dumps(cache, indent=1))
            print(f"  perceived {key[:60]}")
    return cache


def build_observations(cache):
    """One observation per case-country: mean shock vector across that
    country's headlines, target = logit(post) - logit(pre)."""
    obs = []
    for case in REACTION_CASES:
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
            if cc not in case.pre or cc not in case.post:
                continue
            shock = np.mean(vecs, axis=0)
            d = float(logit(np.array([case.post[cc]]))[0]
                      - logit(np.array([case.pre[cc]]))[0])
            obs.append({"case": case.id, "country": cc,
                        "shock": shock, "d_logit": d,
                        "pre": case.pre[cc], "post": case.post[cc]})
    return obs


def ridge_fit(X, y, alpha=0.5):
    return np.linalg.solve(X.T @ X + alpha * np.eye(X.shape[1]), X.T @ y)


def main():
    print("Perceiving case headlines (cached after first run)...")
    cache = perceive_all()
    obs = build_observations(cache)
    print(f"\n{len(obs)} case-country observations "
          f"across {len({o['case'] for o in obs})} cases")

    X = np.array([o["shock"] for o in obs])
    y = np.array([o["d_logit"] for o in obs])

    # full fit (descriptive)
    r_full = ridge_fit(X, y)
    print("\nresponse operator (full fit, logit units per unit force):")
    for f in Force:
        if abs(r_full[f.value]) > 0.05:
            print(f"  {f.name.lower():12s} {r_full[f.value]:+8.2f}")

    # leave-one-CASE-out validation
    from earth1.rng import sigmoid
    print("\nleave-one-case-out validation:")
    print(f"{'case':22s} {'country':7s} {'pred_d':>8s} {'meas_d':>8s} {'sign':>5s}")
    hits, n = 0, 0
    for held in sorted({o["case"] for o in obs}):
        train = [o for o in obs if o["case"] != held]
        test = [o for o in obs if o["case"] == held]
        r = ridge_fit(np.array([o["shock"] for o in train]),
                      np.array([o["d_logit"] for o in train]))
        for o in test:
            pred_logit = float(o["shock"] @ r)
            pred_post = float(sigmoid(logit(np.array([o["pre"]]))[0] + pred_logit))
            pred_d = pred_post - o["pre"]
            meas_d = o["post"] - o["pre"]
            ok = np.sign(pred_d) == np.sign(meas_d)
            hits += int(ok); n += 1
            print(f"{held:22s} {o['country']:7s} {pred_d:>+8.4f} {meas_d:>+8.4f} "
                  f"{'OK' if ok else 'X':>5s}")
    print(f"\nLOO sign accuracy: {hits}/{n} = {hits/n:.0%}")

if __name__ == "__main__":
    main()
