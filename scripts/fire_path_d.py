"""FIRE PATH D — the first time this engine looks at the world.

One question, one cascade run with live grounding enabled. The
question is deliberately one that MISSES the 794-seed corpus, so the
cascade must fall through A and B and actually search.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.grounding import ground, load_corpus
from earth1.readout import TIER_LABEL, TIER_MEANING

QUESTION = os.environ.get(
    "PD_QUESTION",
    "Do you support a universal basic income, where the government "
    "provides every adult with a regular payment regardless of work?")
POPULATION = os.environ.get("PD_POP", "US")


def main() -> None:
    corpus = load_corpus()
    print(f"corpus: {len(corpus)} seeds", flush=True)
    print(f"question: {QUESTION}", flush=True)

    dry = ground(QUESTION, POPULATION, corpus=corpus, allow_live=False)
    print(f"  without live grounding -> {dry.calibration_source} "
          f"({dry.confidence}), best corpus sim "
          f"{(dry.similarity or 0):.2f}", flush=True)

    print("  firing Path D (web search)...", flush=True)
    live = ground(QUESTION, POPULATION, corpus=corpus, allow_live=True)
    out = {
        "question": QUESTION,
        "population": POPULATION,
        "without_live": {"calibration_source": dry.calibration_source,
                         "confidence": dry.confidence},
        "with_live": {
            "calibration_source": live.calibration_source,
            "tier": TIER_LABEL.get(live.calibration_source),
            "tier_meaning": TIER_MEANING.get(live.calibration_source),
            "confidence": live.confidence,
            "national_target": live.national_target,
            "source": live.source,
            "source_url": live.source_url,
            "date": live.date,
            "matched_question": live.matched_question,
            "seed_id": live.seed_id,
            "note": live.note,
        },
    }
    json.dump(out, open("data/path_d_first_fire.json", "w"), indent=1)
    w = out["with_live"]
    print(f"  PATH D RESULT: {w['calibration_source']} (tier {w['tier']}, "
          f"{w['confidence']})", flush=True)
    print(f"    target   : {w['national_target']}", flush=True)
    print(f"    source   : {w['source']}", flush=True)
    print(f"    url      : {w['source_url']}", flush=True)
    print(f"    date     : {w['date']}", flush=True)
    print(f"    as asked : {w['matched_question']}", flush=True)
    print(f"    note     : {w['note']}", flush=True)


if __name__ == "__main__":
    main()
