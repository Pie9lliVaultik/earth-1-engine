"""Historical signal replay — exogenous forcing for the living world.

Phase 5.6 (bible v2 §14, §21): the G5 three-run arc proved endogenous
dynamics alone cannot track history (63.7% sign accuracy on broken
physics -> 39.7% half-fixed -> 44.3% correct). Secular drift requires
exogenous signal. This module replays cached GDELT monthly tone/volume
history (fetched once by scripts/fetch_gdelt_history.py) through the
SAME adapter force-mapping and gain path the live receiver uses —
history enters the world exactly the way today's news does.

Replay honesty rules:
  - The adapter's Welford baselines are warmed on a first pass over the
    whole period (a climatology), so month one isn't artificially novel.
  - Geography can be shuffled (country labels permuted) to build the
    inline §14 placebo control: the real assignment must beat the
    shuffled one, or the signal is noise, not information.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

import numpy as np

from earth1.receiver import (
    GDELTAdapter, GeoScope, ReceiverConfig, activations_to_events,
)


def load_history(path) -> Dict[str, Dict[str, Dict[str, float]]]:
    import json
    from pathlib import Path
    return json.loads(Path(path).read_text())


def shuffle_history_geography(
    history: Dict, rng: np.random.Generator,
) -> Dict:
    """Permute country labels — every series survives, attached to the
    wrong country. The §14 placebo control for replay."""
    codes = sorted(history)
    permuted = list(rng.permutation(codes))
    return {new: history[old] for new, old in zip(permuted, codes)}


def build_replay_events(
    history: Dict,
    config: Optional[ReceiverConfig] = None,
    warmup: bool = True,
) -> Dict[int, List]:
    """Convert cached history into per-month WorldEvent lists.

    Returns {month_index: [WorldEvent, ...]} with month 0 = the earliest
    month present. Events carry the adapter's force mapping (tone z ->
    fear/economics, volume z -> collective) scaled by the receiver gain.
    """
    config = config or ReceiverConfig.default()
    adapter = GDELTAdapter()

    months = sorted({m for c in history.values() for m in c.get("tone", {})})
    if not months:
        return {}

    def _values(cc: str, m: str):
        tone = history[cc].get("tone", {}).get(m)
        vol = history[cc].get("vol", {}).get(m)
        if tone is None or vol is None:
            return None
        return tone, vol, max(0.0, -tone)

    def _pass(generate: bool) -> Dict[int, List]:
        out: Dict[int, List] = {}
        for mi, m in enumerate(months):
            acts = []
            ts = datetime(int(m[:4]), int(m[5:7]), 15)
            for cc in sorted(history):
                vals = _values(cc, m)
                if vals is None:
                    continue
                tone, vol, conflict = vals
                act = adapter.from_values(
                    tone=tone, event_count=vol, conflict_intensity=conflict,
                    scope=GeoScope.national(cc), timestamp=ts,
                )
                if generate:
                    acts.append(act)
            if generate and acts:
                # t is stamped by the caller at injection time; month
                # index is the key, timestamps inside events are set then
                out[mi] = acts
        return out

    if warmup:
        _pass(generate=False)      # climatology: baselines learn "normal"
    activations_by_month = _pass(generate=True)

    events_by_month: Dict[int, List] = {}
    for mi, acts in activations_by_month.items():
        evs = activations_to_events(acts, t=float(mi * 30), config=config)
        if evs:
            events_by_month[mi] = evs
    return events_by_month
