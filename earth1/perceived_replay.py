"""Perceived-headline replay — semantic forcing for the G5 temporal leg.

Phase 5.6 proved STATISTICS (tone, volume, theme salience) carry no
decade-scale signal. Phase 5.8 proved one-call-per-item LLM perception
authors force events that match hand-authored shocks. This module bridges
the two: perceive real historical headlines, build per-quarter WorldEvents,
and inject them into the temporal leg as the world evolves.

The headline source is GDELT DOC artlist, fetched once by
scripts/fetch_headlines.py, cached in data/headlines_2017_2022.json.
Each window yields ~3 headlines × 20 countries × 24 quarters.

Replay honesty:
  - Perception calls are cached and reused: the same headlines always
    produce the same force events (model temperature is 0 by default).
  - Geography can be shuffled (country labels permuted on the EVENTS,
    not the perception): same events, wrong countries.
  - The response law at prediction time is the only mechanism that maps
    these events to opinion change (§3 discovery #4).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from earth1.event_log import WorldEvent
from earth1.news_perception import NewsItem, perceive_item, PerceivedEvent
from earth1.types import Force, NUM_FORCES


def load_headlines(path) -> Dict[str, List[Dict]]:
    return json.loads(Path(path).read_text())


def _key_to_quarter_index(key: str, base_year: int = 2017) -> int:
    cc, yq = key.split("|")
    year = int(yq[:4])
    quarter = int(yq[-1])
    return (year - base_year) * 4 + (quarter - 1)


def perceive_all_headlines(
    headlines: Dict[str, List[Dict]],
    cache_path: Optional[str] = None,
    perceiver=perceive_item,
    progress: bool = False,
) -> Dict[str, List[Dict]]:
    """Perceive every headline in the cache, returning per-key perceived events.

    Returns {country|yearQn: [{force_deltas: {int: float}, confidence, decay, title}, ...]}.
    Loads/extends cache_path if provided, so partial runs are resumable.
    """
    cache: Dict[str, List[Dict]] = {}
    if cache_path:
        p = Path(cache_path)
        if p.exists():
            cache = json.loads(p.read_text())

    total = sum(len(v) for v in headlines.values())
    done = sum(len(v) for v in cache.values())
    if progress:
        print(f"perceive: {done}/{total} headlines cached")

    for key, arts in sorted(headlines.items()):
        if key in cache:
            continue
        cc = key.split("|")[0]
        perceived = []
        for art in arts:
            item = NewsItem(
                title=art["title"],
                country=cc,
                date=art.get("date", ""),
            )
            ev = perceiver(item)
            if ev is not None:
                perceived.append({
                    "title": art["title"],
                    "force_deltas": {str(k): v for k, v in ev.force_deltas.items()},
                    "confidence": ev.confidence,
                    "decay": ev.decay_half_life,
                })
        cache[key] = perceived
        if cache_path:
            Path(cache_path).write_text(json.dumps(cache, indent=1))
        if progress and len(cache) % 20 == 0:
            print(f"  perceived {len(cache)}/{len(headlines)} windows")

    return cache


def build_perceived_replay_events(
    perceived: Dict[str, List[Dict]],
    dt_days: float = 30.0,
    base_year: int = 2017,
) -> Dict[int, List[WorldEvent]]:
    """Convert perceived headlines into per-step WorldEvents.

    Each quarter maps to a step index (quarter 0 = step 0, etc.).
    Events carry the perceived force deltas, scoped to the headline's
    country, with the perceived decay half-life.
    """
    events: Dict[int, List[WorldEvent]] = {}
    for key, percs in sorted(perceived.items()):
        cc = key.split("|")[0]
        qi = _key_to_quarter_index(key, base_year)
        step = qi * 3  # quarterly → ~monthly steps (3 months per quarter)
        for p in percs:
            deltas = {Force(int(k)).name.lower(): v
                      for k, v in p["force_deltas"].items()}
            if not deltas:
                continue
            ev = WorldEvent.create(
                timestamp=float(step * dt_days),
                force_deltas=deltas,
                region_pattern=f"{cc}-*",
                decay_half_life=p.get("decay", 14.0),
                source="perception:replay",
            )
            events.setdefault(step, []).append(ev)
    return events


def shuffle_perceived_geography(
    perceived: Dict[str, List[Dict]],
    rng: np.random.Generator,
) -> Dict[str, List[Dict]]:
    """Permute country labels on perceived events (same perception,
    wrong geography). The §14 placebo control for perceived replay."""
    by_country: Dict[str, List[Tuple[str, List[Dict]]]] = {}
    for key, percs in perceived.items():
        cc = key.split("|")[0]
        by_country.setdefault(cc, []).append((key, percs))

    codes = sorted(by_country)
    permuted = list(rng.permutation(codes))
    result = {}
    for old_cc, new_cc in zip(codes, permuted):
        for key, percs in by_country[old_cc]:
            new_key = key.replace(f"{old_cc}|", f"{new_cc}|", 1)
            result[new_key] = percs
    return result
