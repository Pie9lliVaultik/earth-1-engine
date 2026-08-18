"""Live LLM standoff on the corrected 66-country GOQA (preregistered:
data/llm_standoff_prereg.json — read it before editing anything here).

One call per question, temperature 0, model returns {ISO2: yes_percent}.
Scored per cell vs corrected truth; Western/non-Western split per the
preregistered list. Resumable: per-model cache file keyed by question id.

Env: ANTHROPIC_API_KEY (from /opt/earth1/.env), LSO_MODELS, LSO_LIMIT.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PREREG = json.load(open("data/llm_standoff_prereg.json"))
WESTERN = set(PREREG["western_set"])
MODELS = os.environ.get(
    "LSO_MODELS", "claude-sonnet-5,claude-haiku-4-5-20251001").split(",")
LIMIT = int(os.environ.get("LSO_LIMIT", "0"))  # 0 = all questions


def ask(model: str, question: str, countries: list) -> dict:
    prompt = (
        "Estimate public opinion. For EACH country listed, estimate the "
        "percentage (0-100) of adults who would answer YES to the survey "
        "question below.\n\n"
        f"Question: {question}\n\n"
        f"Countries (ISO2): {', '.join(countries)}\n\n"
        "Reply with ONLY a JSON object mapping each ISO2 code to a number "
        "0-100. No prose, no markdown fences.")
    payload = {"model": model, "max_tokens": 2000,
               "messages": [{"role": "user", "content": prompt}]}
    if not model.endswith("-5"):
        payload["temperature"] = 0  # deprecated on the Claude 5 family
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                 "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                text = json.load(r)["content"][0]["text"]
            text = text.strip().strip("`").lstrip("json").strip()
            start, end = text.find("{"), text.rfind("}")
            return {k.upper(): float(v)
                    for k, v in json.loads(text[start:end + 1]).items()}
        except Exception as e:  # noqa: BLE001 — retry API/parse flakes
            if attempt == 5:
                raise
            time.sleep(2 ** attempt)
    return {}


def main() -> None:
    gt = json.load(open("data/benchmark/goqa_ground_truth.json"))
    if LIMIT:
        gt = gt[:LIMIT]
    results = {}
    for model in MODELS:
        cache_path = f"data/llm_standoff_cache_{model.replace('.', '_')}.json"
        cache = (json.load(open(cache_path))
                 if os.path.exists(cache_path) else {})
        errs, errs_w, errs_nw, per_q = [], [], [], {}
        for q in gt:
            countries = sorted(q["countries"].keys())
            if q["id"] not in cache:
                cache[q["id"]] = ask(model, q["text"], countries)
                json.dump(cache, open(cache_path, "w"))
                print(f"{model} {q['id']}: {len(cache[q['id']])} countries",
                      flush=True)
            pred = cache[q["id"]]
            qe = []
            for cc, d in q["countries"].items():
                if cc not in pred:
                    continue
                e = abs(pred[cc] / 100.0 - d["yes"])
                qe.append(e), errs.append(e)
                (errs_w if cc in WESTERN else errs_nw).append(e)
            if qe:
                per_q[q["id"]] = sum(qe) / len(qe)
        import numpy as np
        results[model] = {
            "mae": float(np.mean(errs)), "n_cells": len(errs),
            "mae_western": float(np.mean(errs_w)),
            "mae_nonwestern": float(np.mean(errs_nw)),
            "split_ratio": float(np.mean(errs_nw) / max(np.mean(errs_w), 1e-9)),
            "per_question": per_q,
        }
        r = results[model]
        print(f"LLM-STANDOFF {model}: MAE {r['mae']:.4f} "
              f"(W {r['mae_western']:.4f} / NW {r['mae_nonwestern']:.4f}, "
              f"ratio {r['split_ratio']:.2f}) n={r['n_cells']}", flush=True)
    json.dump(results, open("data/llm_standoff_results.json", "w"), indent=1)
    print("STANDOFF-DONE", flush=True)


if __name__ == "__main__":
    main()
