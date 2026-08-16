#!/usr/bin/env python3
"""Batch-perceive cached headlines for the temporal replay (G5 run #8).

Reads data/headlines_2017_2022.json (from fetch_headlines.py), perceives
each headline via the LLM perception pipeline, and caches results in
data/perceived_headlines.json. Resumable — skips already-perceived windows.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from earth1.perceived_replay import load_headlines, perceive_all_headlines

HEADLINES_PATH = ROOT / "data" / "headlines_2017_2022.json"
CACHE_PATH = ROOT / "data" / "perceived_headlines.json"


def main():
    if not HEADLINES_PATH.exists():
        print(f"No headlines at {HEADLINES_PATH} — run fetch_headlines.py first")
        sys.exit(1)

    headlines = load_headlines(HEADLINES_PATH)
    print(f"Loaded {len(headlines)} windows, "
          f"{sum(len(v) for v in headlines.values())} total headlines")

    perceived = perceive_all_headlines(
        headlines,
        cache_path=str(CACHE_PATH),
        progress=True,
    )

    total_events = sum(len(v) for v in perceived.values())
    print(f"\nDone: {len(perceived)} windows, {total_events} perceived events")
    print(f"Cached at {CACHE_PATH}")


if __name__ == "__main__":
    main()
