"""Non-linear thresholds — phase transitions that produce cascades.

When regional force means cross defined thresholds, events are injected
into the event log. Those events modify forces, which may trigger further
thresholds, creating emergent cascading dynamics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from earth1.types import Civilization, Force, NUM_FORCES
from earth1.event_log import EventLog, WorldEvent
from earth1.genesis import GENESIS_COUNTRIES


@dataclass
class TransitionRule:
    name: str
    conditions: List[Tuple[Force, str, float]]  # (force, ">" or "<", threshold)
    effects: Dict[str, float]  # force_name -> delta
    region_scope: str  # "regional" or "global"
    cooldown_days: float
    decay_half_life: float


TRANSITION_RULES = [
    TransitionRule(
        name="identity_collapse",
        conditions=[(Force.FEAR, ">", 0.7), (Force.COLLECTIVE, ">", 0.6)],
        effects={"identity": -0.15},
        region_scope="regional",
        cooldown_days=30.0,
        decay_half_life=60.0,
    ),
    TransitionRule(
        name="panic_cascade",
        conditions=[(Force.ECONOMICS, "<", 0.3), (Force.FEAR, ">", 0.5)],
        effects={"fear": 0.10, "desire": -0.08},
        region_scope="regional",
        cooldown_days=14.0,
        decay_half_life=45.0,
    ),
    TransitionRule(
        name="polarization_lock",
        conditions=[(Force.IDENTITY, ">", 0.8), (Force.CULTURE, ">", 0.7)],
        effects={"collective": -0.12},
        region_scope="regional",
        cooldown_days=60.0,
        decay_half_life=90.0,
    ),
    TransitionRule(
        name="economic_boom",
        conditions=[(Force.ECONOMICS, ">", 0.8), (Force.FEAR, "<", 0.3)],
        effects={"desire": 0.12, "fear": -0.05},
        region_scope="regional",
        cooldown_days=30.0,
        decay_half_life=60.0,
    ),
    TransitionRule(
        name="collective_surge",
        conditions=[(Force.COLLECTIVE, ">", 0.75), (Force.FEAR, ">", 0.6)],
        effects={"identity": -0.10, "temperament": -0.08},
        region_scope="regional",
        cooldown_days=20.0,
        decay_half_life=30.0,
    ),
]


def _check_condition(mean_val: float, op: str, threshold: float) -> bool:
    if op == ">":
        return mean_val > threshold
    elif op == "<":
        return mean_val < threshold
    return False


# ── FIX 1 (2026-08-18): LOCAL THRESHOLDS ──────────────────────────────
# The construction error: a rule was evaluated against the national MEAN
# of a force. A mean cannot cross a threshold that a minority has
# crossed — averaging the 29.2% of agents already past collective_surge
# with the 70.8% below it pulls the statistic back under the bar, so the
# detector was structurally blind to precisely the phenomenon it exists
# to detect.
#
# The fix: evaluate each condition PER AGENT, then fire when enough
# agents personally satisfy the whole rule. A phase transition is
# "enough people crossed", never "the average person crossed".
#
# MIN_PARTICIPATION is an external anchor, not a tuned value: the
# committed-minority literature (Centola et al. 2018, Science) puts the
# convention-flipping fraction near 25%, and Granovetter threshold
# models put critical mass in the 10-25% band. Registered before the
# run in data/fix1_local_thresholds_prereg.json, and swept.
MIN_PARTICIPATION = 0.25


def _participation(civ: Civilization, mask: np.ndarray,
                   rule: "TransitionRule") -> float:
    """Fraction of agents in `mask` who personally satisfy every condition.

    This is the whole fix. `civ.forces` is (N, NUM_FORCES), so each
    condition becomes a per-agent boolean column and the rule is their
    AND — the same agent must satisfy all of them, which is stricter
    than the mean test it replaces, not looser.
    """
    n = int(mask.sum())
    if n == 0:
        return 0.0
    sub = civ.forces[mask]
    met = np.ones(n, dtype=bool)
    for force, op, thresh in rule.conditions:
        col = sub[:, force.value]
        met &= (col > thresh) if op == ">" else (col < thresh)
    return float(met.mean())


def detect_transitions(
    civ: Civilization,
    event_log: EventLog,
    t: float,
    last_fired: Optional[Dict[str, float]] = None,
    rules: Optional[List[TransitionRule]] = None,
    mode: str = "local",
    min_participation: float = MIN_PARTICIPATION,
) -> Tuple[List[WorldEvent], Dict[str, float]]:
    """Scan the population for threshold crossings.

    mode='local'    fire when >= min_participation of agents personally
                    satisfy every condition (FIX 1, the default)
    mode='national' fire when the force MEAN satisfies them (the old
                    behaviour, retained so it can be run head-to-head
                    rather than deleted)

    Returns (new_events, updated_last_fired).
    """
    if rules is None:
        rules = TRANSITION_RULES
    if last_fired is None:
        last_fired = {}

    fired_events = []
    updated_fired = dict(last_fired)
    n_countries = len(GENESIS_COUNTRIES)

    for rule in rules:
        if rule.region_scope == "regional":
            for ci in range(n_countries):
                country_mask = civ.country == ci
                if country_mask.sum() < 10:
                    continue

                cooldown_key = f"{rule.name}:{ci}"
                last_t = updated_fired.get(cooldown_key, -1e9)
                if t - last_t < rule.cooldown_days:
                    continue

                if mode == "local":
                    all_met = (_participation(civ, country_mask, rule)
                               >= min_participation)
                else:
                    forces_mean = civ.forces[country_mask].mean(axis=0)
                    all_met = all(
                        _check_condition(forces_mean[force.value], op, thresh)
                        for force, op, thresh in rule.conditions
                    )
                if all_met:
                    iso2 = GENESIS_COUNTRIES[ci]["iso2"]
                    event = WorldEvent.create(
                        timestamp=t,
                        force_deltas=rule.effects,
                        region_pattern=f"{iso2}-*",
                        decay_half_life=rule.decay_half_life,
                        source=f"threshold:{rule.name}",
                    )
                    fired_events.append(event)
                    updated_fired[cooldown_key] = t
        else:
            cooldown_key = rule.name
            last_t = updated_fired.get(cooldown_key, -1e9)
            if t - last_t < rule.cooldown_days:
                continue

            if mode == "local":
                all_met = (_participation(civ, np.ones(civ.n, dtype=bool),
                                          rule) >= min_participation)
            else:
                forces_mean = civ.forces.mean(axis=0)
                all_met = all(
                    _check_condition(forces_mean[force.value], op, thresh)
                    for force, op, thresh in rule.conditions
                )
            if all_met:
                event = WorldEvent.create(
                    timestamp=t,
                    force_deltas=rule.effects,
                    region_pattern="*",
                    decay_half_life=rule.decay_half_life,
                    source=f"threshold:{rule.name}",
                )
                fired_events.append(event)
                updated_fired[cooldown_key] = t

    return fired_events, updated_fired


def detect_and_append(
    civ: Civilization,
    event_log: EventLog,
    t: float,
    last_fired: Optional[Dict[str, float]] = None,
    rules: Optional[List[TransitionRule]] = None,
) -> Tuple[int, Dict[str, float]]:
    """Detect transitions and append any fired events to the log.

    Returns (n_events_fired, updated_last_fired).
    """
    events, updated_fired = detect_transitions(civ, event_log, t, last_fired, rules)
    for e in events:
        event_log.append(e)
    return len(events), updated_fired
