"""Event generation — the model generates events that feed back into itself.

Detection rules scan population state + recent history for emergent phenomena
and inject new events into the event log. This closes the loop: the system
feeds on its own output."""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

from earth1.types import Civilization, RunResult, Force, NUM_FORCES
from earth1.event_log import EventLog, WorldEvent
from earth1.genesis import GENESIS_COUNTRIES


def _bimodality(stances: np.ndarray) -> float:
    """Bimodality coefficient: (skewness^2 + 1) / kurtosis. Higher = more bimodal."""
    if len(stances) < 10:
        return 0.0
    mean = np.mean(stances)
    std = np.std(stances)
    if std < 1e-10:
        return 0.0
    centered = stances - mean
    skew = float(np.mean(centered**3) / std**3)
    kurt = float(np.mean(centered**4) / std**4)
    if kurt < 1e-10:
        return 0.0
    return (skew**2 + 1) / kurt


def _regional_means(civ: Civilization) -> Dict[int, np.ndarray]:
    """Compute per-country force means."""
    means = {}
    for ci in range(len(GENESIS_COUNTRIES)):
        mask = civ.country == ci
        if mask.sum() < 10:
            continue
        means[ci] = civ.forces[mask].mean(axis=0)
    return means


def detect_polarization(
    civ: Civilization,
    recent_results: List[Dict[str, RunResult]],
    threshold: float = 0.18,
    t: float = 0.0,
) -> List[WorldEvent]:
    """Detect bimodality surges — two camps pulling apart."""
    events = []
    if not recent_results:
        return events

    latest = recent_results[-1]
    # authoritative world time (audit round 7: len(history) with a
    # 30-entry cap timestamped day-500 events at ~day 30)
    t = max(t, len(recent_results) * 1.0)

    for qid, r in latest.items():
        if r.fragility > 0.6 and r.conviction < 0.4:
            # per-AGENT stances — the old [yes_pct, 1-yes_pct] input had
            # n=2 < 10, so this detector could never fire (audit finding)
            if r.settled_stances is None:
                continue
            bim = _bimodality(r.settled_stances)
            if bim > threshold:
                events.append(WorldEvent.create(
                    timestamp=t,
                    force_deltas={"fear": 0.03, "collective": 0.02},
                    region_pattern="*",
                    decay_half_life=15.0,
                    source=f"emergent:polarization:{qid}",
                ))
    return events


def detect_consensus(
    civ: Civilization,
    recent_results: List[Dict[str, RunResult]],
    event_log: Optional[EventLog] = None,
    t: float = 0.0,
    threshold: float = 0.80,
) -> List[WorldEvent]:
    """Detect when >threshold of a region converges on a topic."""
    events = []
    if not recent_results:
        return events

    latest = recent_results[-1]
    t = max(t, len(recent_results) * 1.0)

    already_fired = set()
    if event_log is not None:
        for e in event_log.events():
            if e.source.startswith("emergent:consensus:"):
                already_fired.add(e.source.split(":")[-1])

    for qid, r in latest.items():
        if qid in already_fired:
            continue
        if r.yes_pct > threshold or r.yes_pct < (1 - threshold):
            events.append(WorldEvent.create(
                timestamp=t,
                force_deltas={"identity": 0.03, "collective": 0.02},
                region_pattern="*",
                decay_half_life=30.0,
                source=f"emergent:consensus:{qid}",
            ))
    return events


def detect_opinion_reversal(
    recent_results: List[Dict[str, RunResult]],
    window: int = 5,
    min_swing: float = 0.08,
    t: float = 0.0,
) -> List[WorldEvent]:
    """Detect when a question's yes_pct reverses direction significantly."""
    events = []
    if len(recent_results) < window:
        return events

    t = max(t, len(recent_results) * 1.0)
    recent = recent_results[-window:]

    all_qids = set()
    for r in recent:
        all_qids.update(r.keys())

    for qid in all_qids:
        series = []
        for r in recent:
            if qid in r:
                series.append(r[qid].yes_pct)
        if len(series) < 3:
            continue

        first_half = series[:len(series) // 2]
        second_half = series[len(series) // 2:]
        trend_1 = first_half[-1] - first_half[0]
        trend_2 = second_half[-1] - second_half[0]

        if trend_1 * trend_2 < 0 and abs(trend_2 - trend_1) > min_swing:
            events.append(WorldEvent.create(
                timestamp=t,
                force_deltas={"fear": 0.03, "identity": -0.02},
                region_pattern="*",
                decay_half_life=15.0,
                source=f"emergent:reversal:{qid}",
            ))
    return events


def detect_cascade(
    event_log: EventLog,
    t: float,
    window_ticks: float = 5.0,
    min_events: int = 3,
) -> List[WorldEvent]:
    """Detect when multiple threshold transitions fire in quick succession."""
    events = []
    recent_threshold = [
        e for e in event_log.events()
        if e.source.startswith("threshold:") and t - e.timestamp <= window_ticks
    ]

    if len(recent_threshold) >= min_events:
        regions = set()
        for e in recent_threshold:
            regions.add(e.region_pattern)

        for region in regions:
            region_events = [e for e in recent_threshold if e.region_pattern == region]
            if len(region_events) >= min_events:
                events.append(WorldEvent.create(
                    timestamp=t,
                    force_deltas={"fear": 0.08, "economics": -0.05, "collective": 0.06},
                    region_pattern=region,
                    decay_half_life=45.0,
                    source="emergent:cascade",
                ))
    return events


def detect_emergent_events(
    civ: Civilization,
    event_log: EventLog,
    t: float,
    recent_results: List[Dict[str, RunResult]],
    window: int = 10,
) -> List[WorldEvent]:
    """Scan population state + recent history for all emergent phenomena."""
    all_events = []
    all_events.extend(detect_polarization(civ, recent_results, t=t))
    all_events.extend(detect_consensus(civ, recent_results, event_log=event_log, t=t))
    all_events.extend(detect_opinion_reversal(recent_results, window=window, t=t))
    all_events.extend(detect_cascade(event_log, t))
    return all_events
