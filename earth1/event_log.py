"""Append-only event timeline — the 'context window' of the civilization.

Events target regions and demographics, decay over time, and stack
to produce per-agent force deltas. This is Layer 1 of the layered
state model: base genesis (Layer 0) + accumulated experience (Layer 1)."""

from __future__ import annotations

import fnmatch
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from earth1.types import Civilization, Force, NUM_FORCES
from earth1.genesis import GENESIS_COUNTRIES, genesis_country_code
from earth1.regions import get_regions


_FORCE_NAME_TO_IDX = {f.name.lower(): f.value for f in Force}


@dataclass(frozen=True)
class WorldEvent:
    id: str
    timestamp: float
    region_pattern: str
    demographic_filter: dict
    force_deltas: dict
    decay_half_life: float
    source: str

    @staticmethod
    def create(
        timestamp: float,
        force_deltas: dict,
        region_pattern: str = "*",
        demographic_filter: Optional[dict] = None,
        decay_half_life: float = 30.0,
        source: str = "manual",
    ) -> WorldEvent:
        # bare ISO2 ("IT") silently matched zero agents; canonicalize
        if (len(region_pattern) == 2 and region_pattern.isalpha()
                and region_pattern.isupper()):
            region_pattern = f"{region_pattern}-*"
        return WorldEvent(
            id=str(uuid.uuid4()),
            timestamp=timestamp,
            region_pattern=region_pattern,
            demographic_filter=demographic_filter or {},
            force_deltas=_canonical_deltas(force_deltas),
            decay_half_life=decay_half_life,
            source=source,
        )


def _canonical_deltas(force_deltas: dict) -> dict:
    """Canonicalize force keys to lowercase names at construction.

    External-review finding (2026-08-16): integer enum keys silently
    produced ZERO event vectors — G5 runs #3-#6 event legs injected
    no-op shocks. Accept Force enums, ints, digit strings, and names;
    reject unknowns loudly rather than dropping them silently.
    """
    from earth1.types import Force

    out = {}
    for key, delta in force_deltas.items():
        if isinstance(key, Force):
            name = key.name.lower()
        elif isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
            name = Force(int(key)).name.lower()
        elif isinstance(key, str) and key.lower() in _FORCE_NAME_TO_IDX:
            name = key.lower()
        else:
            raise ValueError(f"unknown force key {key!r} in event deltas")
        out[name] = float(delta)
    return out


def _event_force_vector(event: WorldEvent) -> np.ndarray:
    v = np.zeros(NUM_FORCES, dtype=np.float64)
    for name, delta in event.force_deltas.items():
        idx = _FORCE_NAME_TO_IDX.get(name)
        if idx is not None:
            v[idx] = delta
    return v


def _decay_factor(t: float, event: WorldEvent) -> float:
    dt = t - event.timestamp
    if dt < 0:
        return 0.0
    if event.decay_half_life <= 0:
        return 1.0
    return 2.0 ** (-dt / event.decay_half_life)


class EventLog:

    def __init__(self):
        self._events: List[WorldEvent] = []
        self._region_codes_cache: Optional[Dict[int, List[str]]] = None

    def append(self, event: WorldEvent) -> None:
        self._events.append(event)

    def events(self) -> List[WorldEvent]:
        return list(self._events)

    def __len__(self) -> int:
        return len(self._events)

    def active_events(self, t: float, threshold: float = 0.01) -> List[WorldEvent]:
        result = []
        for e in self._events:
            factor = _decay_factor(t, e)
            if factor < threshold:
                continue
            max_delta = max(abs(v) for v in e.force_deltas.values()) if e.force_deltas else 0
            if max_delta * factor >= threshold:
                result.append(e)
        return result

    def _build_region_codes(self, civ: Civilization) -> Dict[int, List[str]]:
        if self._region_codes_cache is not None:
            return self._region_codes_cache
        cache = {}
        for ci in range(len(GENESIS_COUNTRIES)):
            iso2 = GENESIS_COUNTRIES[ci]["iso2"]
            regions = get_regions(iso2)
            codes = [r.code for r in regions]
            cache[ci] = codes
        self._region_codes_cache = cache
        return cache

    def _matches_region(self, pattern: str, country_idx: int, region_idx: int,
                        region_codes: Dict[int, List[str]]) -> bool:
        if pattern == "*":
            return True
        codes = region_codes.get(country_idx, [])
        if not codes:
            iso2 = genesis_country_code(country_idx) if country_idx < len(GENESIS_COUNTRIES) else "XX"
            return fnmatch.fnmatch(iso2, pattern) or fnmatch.fnmatch(f"{iso2}-*", pattern)
        actual_code = codes[region_idx] if region_idx < len(codes) else codes[0]
        if fnmatch.fnmatch(actual_code, pattern):
            return True
        iso2 = actual_code.split("-")[0] if "-" in actual_code else actual_code
        return fnmatch.fnmatch(f"{iso2}-*", pattern) and pattern.endswith("*")

    def _matches_demographics(self, filt: dict, civ: Civilization, idx: int) -> bool:
        if not filt:
            return True
        if "age_min" in filt and civ.age[idx] < filt["age_min"]:
            return False
        if "age_max" in filt and civ.age[idx] > filt["age_max"]:
            return False
        if "income" in filt and civ.income[idx] != filt["income"]:
            return False
        if "education" in filt and civ.education[idx] != filt["education"]:
            return False
        if "urban" in filt and bool(civ.urban[idx]) != filt["urban"]:
            return False
        return True

    def effective_deltas_vectorized(self, t: float, civ: Civilization) -> np.ndarray:
        deltas = np.zeros((civ.n, NUM_FORCES), dtype=np.float64)
        active = self.active_events(t)
        if not active:
            return deltas

        region_codes = self._build_region_codes(civ)

        for event in active:
            factor = _decay_factor(t, event)
            fv = _event_force_vector(event) * factor

            if event.region_pattern == "*" and not event.demographic_filter:
                deltas += fv[np.newaxis, :]
                continue

            if event.region_pattern != "*":
                region_mask = np.zeros(civ.n, dtype=bool)
                for ci in range(len(GENESIS_COUNTRIES)):
                    codes = region_codes.get(ci, [])
                    country_mask = civ.country == ci
                    if not country_mask.any():
                        continue
                    for ri, code in enumerate(codes):
                        if fnmatch.fnmatch(code, event.region_pattern):
                            region_mask |= (country_mask & (civ.region == ri))
                    iso2 = GENESIS_COUNTRIES[ci]["iso2"]
                    if event.region_pattern.endswith("*") and fnmatch.fnmatch(f"{iso2}-X", event.region_pattern):
                        for ri in range(len(codes)):
                            region_mask |= (country_mask & (civ.region == ri))
            else:
                region_mask = np.ones(civ.n, dtype=bool)

            if event.demographic_filter:
                demo_mask = np.ones(civ.n, dtype=bool)
                f = event.demographic_filter
                if "age_min" in f:
                    demo_mask &= civ.age >= f["age_min"]
                if "age_max" in f:
                    demo_mask &= civ.age <= f["age_max"]
                if "income" in f:
                    demo_mask &= civ.income == f["income"]
                if "education" in f:
                    demo_mask &= civ.education == f["education"]
                if "urban" in f:
                    demo_mask &= civ.urban == f["urban"]
                mask = region_mask & demo_mask
            else:
                mask = region_mask

            deltas[mask] += fv[np.newaxis, :]

        # Cap total effective deltas to prevent event accumulation runaway
        np.clip(deltas, -0.5, 0.5, out=deltas)
        return deltas
