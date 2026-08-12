"""Field Receiver — External State Sensing (Builds 0-3).

The receiver ingests real-world signals (GDELT, ACLED, FRED, Google Trends,
World Bank, etc.), normalizes them, infers force activations, and produces
field_shift vectors that modify Earth-1's projections.

Build 0: Engine noise measurement — minimum detectable effect (MDE)
Build 1: Question-force relevance profiles
Build 2: Source adapters, normalization, force inference, integration
Build 3: Falsification experiments (real vs placebo)

Architecture:
  Real-world APIs → raw observations → normalized features →
  force inference → question relevance → field_shift → Earth-1 agents
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from earth1.types import Civilization, Question, Force, NUM_FORCES, FORCE_KEYS
from earth1.forces import project_all
from earth1.engine import run_question
from earth1.rng import sigmoid, logit, make_rng
from earth1.questions import QUESTIONS, question_by_id


# ---------------------------------------------------------------------------
#  Build 0 — Engine Noise Measurement
# ---------------------------------------------------------------------------

@dataclass
class NoiseProfile:
    """Engine noise characteristics for a question."""
    question_id: str
    baseline_yes_pct: float
    seed_std: float
    epsilon_sensitivity: float
    layer_sensitivity: float
    minimum_detectable_effect: float
    compression_zone: bool


def measure_seed_noise(
    question: Question,
    pop: int = 100_000,
    n_seeds: int = 20,
) -> float:
    from earth1.engine import build_civilization
    results = []
    for seed in range(42, 42 + n_seeds):
        civ = build_civilization(pop, seed=seed)
        r = run_question(question, civ)
        results.append(r.yes_pct)
    return float(np.std(results))


def measure_epsilon_sensitivity(
    question: Question,
    civ: Civilization,
    epsilons: Optional[List[float]] = None,
) -> float:
    if epsilons is None:
        epsilons = [0.10, 0.14, 0.18, 0.22, 0.26]
    results = []
    for eps in epsilons:
        r = run_question(question, civ, epsilon=eps)
        results.append(r.yes_pct)
    return float(np.std(results))


def measure_layer_sensitivity(
    question: Question,
    civ: Civilization,
    layer_counts: Optional[List[int]] = None,
) -> float:
    if layer_counts is None:
        layer_counts = [4, 6, 8, 10, 12]
    results = []
    for layers in layer_counts:
        r = run_question(question, civ, layers=layers)
        results.append(r.yes_pct)
    return float(np.std(results))


def measure_field_shift_response(
    question: Question,
    civ: Civilization,
    magnitudes: Optional[List[float]] = None,
) -> List[Tuple[float, float]]:
    if magnitudes is None:
        magnitudes = [0.0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5]

    baseline = run_question(question, civ).yes_pct
    responses = []
    for mag in magnitudes:
        shift = np.zeros(NUM_FORCES)
        dom = int(np.argmax(np.abs(question.weights)))
        shift[dom] = mag * np.sign(question.weights[dom])
        r = run_question(question, civ, field_shift=shift)
        responses.append((mag, abs(r.yes_pct - baseline)))
    return responses


def profile_noise(
    question: Question,
    civ: Civilization,
    n_seeds: int = 5,
) -> NoiseProfile:
    seed_std = measure_seed_noise(question, pop=civ.n, n_seeds=n_seeds)
    eps_sens = measure_epsilon_sensitivity(question, civ)
    layer_sens = measure_layer_sensitivity(question, civ)

    noise_floor = max(seed_std, eps_sens, layer_sens)
    mde = noise_floor * 3.0

    baseline = run_question(question, civ).yes_pct
    compression = 0.45 <= baseline <= 0.55

    return NoiseProfile(
        question_id=question.id,
        baseline_yes_pct=round(baseline, 4),
        seed_std=round(seed_std, 6),
        epsilon_sensitivity=round(eps_sens, 6),
        layer_sensitivity=round(layer_sens, 6),
        minimum_detectable_effect=round(mde, 6),
        compression_zone=compression,
    )


# ---------------------------------------------------------------------------
#  Build 1 — Question-Force Relevance Profiles
# ---------------------------------------------------------------------------

@dataclass
class ForceRelevance:
    """How strongly each force's external signal should affect a question."""
    question_id: str
    relevance: np.ndarray  # (8,) — |weight| / sum(|weights|)
    temporal_sensitivity: float  # 0-1: how much real-time data matters
    dominant_forces: List[str]
    irrelevant_forces: List[str]


def compute_relevance(question: Question) -> ForceRelevance:
    abs_w = np.abs(question.weights)
    total = abs_w.sum()
    if total < 1e-8:
        return ForceRelevance(
            question_id=question.id,
            relevance=np.zeros(NUM_FORCES),
            temporal_sensitivity=0.0,
            dominant_forces=[],
            irrelevant_forces=[f.name.lower() for f in Force],
        )

    relevance = abs_w / total

    fast_forces = {Force.FEAR, Force.DESIRE, Force.ECONOMICS, Force.COLLECTIVE}
    temporal = sum(relevance[f.value] for f in fast_forces)

    dominant = [Force(i).name.lower() for i in range(NUM_FORCES) if relevance[i] > 0.15]
    irrelevant = [Force(i).name.lower() for i in range(NUM_FORCES) if relevance[i] < 0.05]

    return ForceRelevance(
        question_id=question.id,
        relevance=relevance,
        temporal_sensitivity=round(float(temporal), 4),
        dominant_forces=dominant,
        irrelevant_forces=irrelevant,
    )


def build_relevance_matrix() -> Dict[str, ForceRelevance]:
    return {q.id: compute_relevance(q) for q in QUESTIONS if q.domain == "belief_causal"}


# ---------------------------------------------------------------------------
#  Build 2 — Source Adapters, Normalization, Force Inference
# ---------------------------------------------------------------------------

class Scale(IntEnum):
    PLANETARY = 0
    GLOBAL_MACRO = 1
    NATIONAL = 2
    REGIONAL = 3
    CITY = 4
    HYPERLOCAL = 5
    INDIVIDUAL = 6


@dataclass
class GeoScope:
    """Geographic scope of a reading."""
    scale: Scale
    country_code: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None

    @classmethod
    def global_scope(cls) -> "GeoScope":
        return cls(scale=Scale.GLOBAL_MACRO)

    @classmethod
    def national(cls, country_code: str) -> "GeoScope":
        return cls(scale=Scale.NATIONAL, country_code=country_code)


@dataclass
class Reading:
    """A single observation from a source."""
    source_id: str
    timestamp: datetime
    scope: GeoScope
    status: str  # ok | timeout | error | rate_limited
    raw_value: float
    normalized_value: float  # z-score against running baseline
    confidence: float  # 0-1
    provenance: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ForceActivation:
    """Force-level activation from a source reading."""
    source_id: str
    timestamp: datetime
    scope: GeoScope
    forces: np.ndarray  # (8,) activation values
    confidence: np.ndarray  # (8,) per-force confidence
    provenance: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WelfordState:
    """Online mean/variance via Welford's algorithm."""
    n: int = 0
    mean: float = 0.0
    m2: float = 0.0

    def update(self, x: float) -> None:
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        delta2 = x - self.mean
        self.m2 += delta * delta2

    @property
    def variance(self) -> float:
        return self.m2 / max(self.n - 1, 1)

    @property
    def std(self) -> float:
        return float(np.sqrt(self.variance))

    def z_score(self, x: float) -> float:
        if self.n < 3 or self.std < 1e-10:
            return 0.0
        return (x - self.mean) / self.std


class SourceAdapter(ABC):
    """Base class for all source adapters (§25 contract)."""

    @property
    @abstractmethod
    def id(self) -> str: ...

    @property
    @abstractmethod
    def scale(self) -> Scale: ...

    @property
    @abstractmethod
    def cadence(self) -> str: ...

    @property
    @abstractmethod
    def target_forces(self) -> List[Force]: ...

    @abstractmethod
    def fetch(self, scope: GeoScope) -> Reading: ...

    @abstractmethod
    def to_forces(self, reading: Reading) -> ForceActivation: ...


# --- Concrete source adapters (simulated for offline testing) ---

_FRESHNESS_HALF_LIFE_HOURS = {
    "realtime": 1,
    "hourly": 6,
    "daily": 24,
    "weekly": 168,
    "monthly": 720,
    "annual": 8760,
}


def freshness_weight(reading_time: datetime, now: Optional[datetime] = None, cadence: str = "daily") -> float:
    if now is None:
        now = datetime.utcnow()
    age_hours = max(0, (now - reading_time).total_seconds() / 3600)
    hl = _FRESHNESS_HALF_LIFE_HOURS.get(cadence, 24)
    return float(2 ** (-age_hours / hl))


class GDELTAdapter(SourceAdapter):
    """GDELT Global Knowledge Graph — narrative/conflict signals."""

    @property
    def id(self) -> str:
        return "gdelt"

    @property
    def scale(self) -> Scale:
        return Scale.GLOBAL_MACRO

    @property
    def cadence(self) -> str:
        return "daily"

    @property
    def target_forces(self) -> List[Force]:
        return [Force.FEAR, Force.COLLECTIVE, Force.ECONOMICS]

    def __init__(self):
        self._baselines: Dict[str, WelfordState] = {}

    def fetch(self, scope: GeoScope) -> Reading:
        import urllib.request
        import json as _json

        key = scope.country_code or "global"
        if key not in self._baselines:
            self._baselines[key] = WelfordState()

        query = scope.country_code or "world"
        url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={query}&mode=tonechart&format=json&timespan=1d"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Earth1-Engine/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = _json.loads(resp.read().decode())

            if isinstance(data, list) and len(data) > 0:
                tone_vals = [float(d.get("tone", 0)) for d in data if "tone" in d]
                avg_tone = sum(tone_vals) / max(len(tone_vals), 1)
                n_articles = len(data)
            else:
                avg_tone = 0.0
                n_articles = 0

            return Reading(
                source_id=self.id, timestamp=datetime.utcnow(), scope=scope,
                status="ok", raw_value=avg_tone, normalized_value=avg_tone / 10.0,
                confidence=min(1.0, n_articles / 100.0),
            )
        except Exception:
            return Reading(
                source_id=self.id, timestamp=datetime.utcnow(), scope=scope,
                status="error", raw_value=0.0, normalized_value=0.0, confidence=0.0,
            )

    def to_forces(self, reading: Reading) -> ForceActivation:
        if reading.status == "error":
            return ForceActivation(
                source_id=self.id, timestamp=reading.timestamp, scope=reading.scope,
                forces=np.zeros(NUM_FORCES), confidence=np.zeros(NUM_FORCES),
            )
        return self.from_values(
            tone=reading.raw_value, event_count=reading.confidence * 100,
            conflict_intensity=max(0, -reading.raw_value),
            scope=reading.scope, timestamp=reading.timestamp,
        )

    def from_values(
        self,
        tone: float,
        event_count: float,
        conflict_intensity: float,
        scope: Optional[GeoScope] = None,
        timestamp: Optional[datetime] = None,
    ) -> ForceActivation:
        if scope is None:
            scope = GeoScope.global_scope()
        if timestamp is None:
            timestamp = datetime.utcnow()

        key = scope.country_code or "global"
        for metric_name, val in [("tone", tone), ("events", event_count), ("conflict", conflict_intensity)]:
            bk = f"{key}_{metric_name}"
            if bk not in self._baselines:
                self._baselines[bk] = WelfordState()
            self._baselines[bk].update(val)

        tone_z = self._baselines.get(f"{key}_tone", WelfordState()).z_score(tone)
        events_z = self._baselines.get(f"{key}_events", WelfordState()).z_score(event_count)
        conflict_z = self._baselines.get(f"{key}_conflict", WelfordState()).z_score(conflict_intensity)

        forces = np.zeros(NUM_FORCES)
        forces[Force.FEAR] = np.clip(-tone_z * 0.3 + conflict_z * 0.4, -1, 1)
        forces[Force.COLLECTIVE] = np.clip(events_z * 0.2, -1, 1)
        forces[Force.ECONOMICS] = np.clip(-tone_z * 0.15 + events_z * 0.1, -1, 1)

        n_obs = min(
            self._baselines.get(f"{key}_tone", WelfordState()).n,
            self._baselines.get(f"{key}_events", WelfordState()).n,
            self._baselines.get(f"{key}_conflict", WelfordState()).n,
        )
        base_conf = min(1.0, n_obs / 30.0)
        confidence = np.zeros(NUM_FORCES)
        for f in self.target_forces:
            confidence[f.value] = base_conf

        return ForceActivation(
            source_id=self.id, timestamp=timestamp, scope=scope,
            forces=forces, confidence=confidence,
            provenance={"tone": tone, "event_count": event_count, "conflict": conflict_intensity},
        )


class ACLEDAdapter(SourceAdapter):
    """ACLED — Armed Conflict Location & Event Data."""

    @property
    def id(self) -> str:
        return "acled"

    @property
    def scale(self) -> Scale:
        return Scale.NATIONAL

    @property
    def cadence(self) -> str:
        return "weekly"

    @property
    def target_forces(self) -> List[Force]:
        return [Force.FEAR, Force.COLLECTIVE, Force.IDENTITY]

    def __init__(self):
        self._baselines: Dict[str, WelfordState] = {}

    def fetch(self, scope: GeoScope) -> Reading:
        import urllib.request
        import json as _json

        key = scope.country_code or "global"
        if key not in self._baselines:
            self._baselines[key] = WelfordState()

        iso3 = {"US": "United States", "CN": "China", "IN": "India",
                "GB": "United Kingdom", "BR": "Brazil", "NG": "Nigeria"}.get(key, key)
        url = (f"https://api.acleddata.com/acled/read?terms=accept"
               f"&country={iso3}&limit=100&event_date_where=>="
               + datetime.utcnow().strftime("%Y-%m-%d"))

        try:
            api_key = __import__("os").environ.get("ACLED_API_KEY", "")
            email = __import__("os").environ.get("ACLED_EMAIL", "")
            if api_key and email:
                url += f"&key={api_key}&email={email}"
            req = urllib.request.Request(url, headers={"User-Agent": "Earth1-Engine/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = _json.loads(resp.read().decode())

            events = data.get("data", [])
            fatalities = sum(int(e.get("fatalities", 0)) for e in events)
            protests = sum(1 for e in events if "protest" in e.get("event_type", "").lower())
            violence = sum(1 for e in events if "violence" in e.get("event_type", "").lower())

            return Reading(
                source_id=self.id, timestamp=datetime.utcnow(), scope=scope,
                status="ok", raw_value=float(len(events)),
                normalized_value=min(1.0, len(events) / 50.0),
                confidence=min(1.0, len(events) / 20.0),
            )
        except Exception:
            return Reading(
                source_id=self.id, timestamp=datetime.utcnow(), scope=scope,
                status="error", raw_value=0.0, normalized_value=0.0, confidence=0.0,
            )

    def to_forces(self, reading: Reading) -> ForceActivation:
        if reading.status == "error":
            return ForceActivation(
                source_id=self.id, timestamp=reading.timestamp, scope=reading.scope,
                forces=np.zeros(NUM_FORCES), confidence=np.zeros(NUM_FORCES),
            )
        return self.from_values(
            fatalities=reading.raw_value * 0.1,
            protest_events=reading.raw_value * 0.3,
            violence_events=reading.raw_value * 0.2,
            scope=reading.scope, timestamp=reading.timestamp,
        )

    def from_values(
        self,
        fatalities: float,
        protest_events: float,
        violence_events: float,
        scope: Optional[GeoScope] = None,
        timestamp: Optional[datetime] = None,
    ) -> ForceActivation:
        if scope is None:
            scope = GeoScope.national("global")
        if timestamp is None:
            timestamp = datetime.utcnow()

        key = scope.country_code or "global"
        for name, val in [("fatalities", fatalities), ("protests", protest_events), ("violence", violence_events)]:
            bk = f"{key}_{name}"
            if bk not in self._baselines:
                self._baselines[bk] = WelfordState()
            self._baselines[bk].update(val)

        fat_z = self._baselines[f"{key}_fatalities"].z_score(fatalities)
        prot_z = self._baselines[f"{key}_protests"].z_score(protest_events)
        viol_z = self._baselines[f"{key}_violence"].z_score(violence_events)

        forces = np.zeros(NUM_FORCES)
        forces[Force.FEAR] = np.clip(fat_z * 0.5 + viol_z * 0.3, -1, 1)
        forces[Force.COLLECTIVE] = np.clip(prot_z * 0.4, -1, 1)
        forces[Force.IDENTITY] = np.clip(prot_z * 0.2 - viol_z * 0.1, -1, 1)

        n_obs = min(
            self._baselines[f"{key}_fatalities"].n,
            self._baselines[f"{key}_protests"].n,
        )
        base_conf = min(1.0, n_obs / 20.0)
        confidence = np.zeros(NUM_FORCES)
        for f in self.target_forces:
            confidence[f.value] = base_conf

        return ForceActivation(
            source_id=self.id, timestamp=timestamp, scope=scope,
            forces=forces, confidence=confidence,
            provenance={"fatalities": fatalities, "protests": protest_events, "violence": violence_events},
        )


class FREDAdapter(SourceAdapter):
    """FRED / World Bank — economic indicators."""

    @property
    def id(self) -> str:
        return "fred"

    @property
    def scale(self) -> Scale:
        return Scale.NATIONAL

    @property
    def cadence(self) -> str:
        return "monthly"

    @property
    def target_forces(self) -> List[Force]:
        return [Force.ECONOMICS, Force.FEAR, Force.DESIRE]

    def __init__(self):
        self._baselines: Dict[str, WelfordState] = {}

    def fetch(self, scope: GeoScope) -> Reading:
        import urllib.request
        import json as _json
        import os

        key = scope.country_code or "US"
        if key not in self._baselines:
            self._baselines[key] = WelfordState()

        fred_key = os.environ.get("FRED_API_KEY", "")
        if not fred_key:
            return Reading(
                source_id=self.id, timestamp=datetime.utcnow(), scope=scope,
                status="error", raw_value=0.0, normalized_value=0.0, confidence=0.0,
            )

        series_ids = {"unemployment": "UNRATE", "inflation": "CPIAUCSL",
                      "consumer": "UMCSENT", "vix": "VIXCLS"}

        try:
            values = {}
            for label, series_id in series_ids.items():
                url = (f"https://api.stlouisfed.org/fred/series/observations"
                       f"?series_id={series_id}&api_key={fred_key}"
                       f"&file_type=json&sort_order=desc&limit=1")
                req = urllib.request.Request(url, headers={"User-Agent": "Earth1-Engine/1.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = _json.loads(resp.read().decode())
                obs = data.get("observations", [])
                if obs and obs[0].get("value", ".") != ".":
                    values[label] = float(obs[0]["value"])

            if not values:
                return Reading(
                    source_id=self.id, timestamp=datetime.utcnow(), scope=scope,
                    status="error", raw_value=0.0, normalized_value=0.0, confidence=0.0,
                )

            composite = (values.get("consumer", 70) - 50) / 50.0
            return Reading(
                source_id=self.id, timestamp=datetime.utcnow(), scope=scope,
                status="ok", raw_value=composite,
                normalized_value=max(-1.0, min(1.0, composite)),
                confidence=min(1.0, len(values) / 4.0),
            )
        except Exception:
            return Reading(
                source_id=self.id, timestamp=datetime.utcnow(), scope=scope,
                status="error", raw_value=0.0, normalized_value=0.0, confidence=0.0,
            )

    def to_forces(self, reading: Reading) -> ForceActivation:
        if reading.status == "error":
            return ForceActivation(
                source_id=self.id, timestamp=reading.timestamp, scope=reading.scope,
                forces=np.zeros(NUM_FORCES), confidence=np.zeros(NUM_FORCES),
            )
        return self.from_values(
            unemployment=max(0, -reading.raw_value * 5 + 5),
            inflation=max(0, reading.raw_value * 2 + 2),
            consumer_confidence=reading.raw_value * 50 + 70,
            vix=max(10, -reading.raw_value * 15 + 20),
            scope=reading.scope, timestamp=reading.timestamp,
        )

    def from_values(
        self,
        unemployment: float,
        inflation: float,
        consumer_confidence: float,
        vix: float = 20.0,
        scope: Optional[GeoScope] = None,
        timestamp: Optional[datetime] = None,
    ) -> ForceActivation:
        if scope is None:
            scope = GeoScope.national("US")
        if timestamp is None:
            timestamp = datetime.utcnow()

        key = scope.country_code or "US"
        for name, val in [("unemp", unemployment), ("infl", inflation),
                          ("consumer", consumer_confidence), ("vix", vix)]:
            bk = f"{key}_{name}"
            if bk not in self._baselines:
                self._baselines[bk] = WelfordState()
            self._baselines[bk].update(val)

        unemp_z = self._baselines[f"{key}_unemp"].z_score(unemployment)
        infl_z = self._baselines[f"{key}_infl"].z_score(inflation)
        cons_z = self._baselines[f"{key}_consumer"].z_score(consumer_confidence)
        vix_z = self._baselines[f"{key}_vix"].z_score(vix)

        forces = np.zeros(NUM_FORCES)
        forces[Force.ECONOMICS] = np.clip(-unemp_z * 0.3 - infl_z * 0.2 + cons_z * 0.3, -1, 1)
        forces[Force.FEAR] = np.clip(vix_z * 0.4 + unemp_z * 0.2, -1, 1)
        forces[Force.DESIRE] = np.clip(cons_z * 0.3 - infl_z * 0.1, -1, 1)

        n_obs = min(
            self._baselines[f"{key}_unemp"].n,
            self._baselines[f"{key}_infl"].n,
        )
        base_conf = min(1.0, n_obs / 12.0)
        confidence = np.zeros(NUM_FORCES)
        for f in self.target_forces:
            confidence[f.value] = base_conf

        return ForceActivation(
            source_id=self.id, timestamp=timestamp, scope=scope,
            forces=forces, confidence=confidence,
            provenance={"unemployment": unemployment, "inflation": inflation,
                         "consumer_confidence": consumer_confidence, "vix": vix},
        )


class GoogleTrendsAdapter(SourceAdapter):
    """Google Trends — attention/search signals."""

    @property
    def id(self) -> str:
        return "google_trends"

    @property
    def scale(self) -> Scale:
        return Scale.NATIONAL

    @property
    def cadence(self) -> str:
        return "daily"

    @property
    def target_forces(self) -> List[Force]:
        return [Force.FEAR, Force.DESIRE, Force.COLLECTIVE, Force.IDENTITY]

    def __init__(self):
        self._baselines: Dict[str, WelfordState] = {}

    def fetch(self, scope: GeoScope) -> Reading:
        key = scope.country_code or "US"
        if key not in self._baselines:
            self._baselines[key] = WelfordState()

        try:
            from pytrends.request import TrendReq
        except ImportError:
            return Reading(
                source_id=self.id, timestamp=datetime.utcnow(), scope=scope,
                status="error", raw_value=0.0, normalized_value=0.0, confidence=0.0,
            )

        try:
            pytrends = TrendReq(hl="en-US", tz=360)
            fear_kws = ["recession", "war", "pandemic"]
            desire_kws = ["investment", "opportunity", "growth"]
            identity_kws = ["nationalism", "immigration", "identity"]

            geo = key if key != "global" else ""

            pytrends.build_payload(fear_kws, cat=0, timeframe="now 7-d", geo=geo)
            fear_df = pytrends.interest_over_time()
            fear_val = float(fear_df[fear_kws].mean().mean()) if not fear_df.empty else 0.0

            pytrends.build_payload(desire_kws, cat=0, timeframe="now 7-d", geo=geo)
            desire_df = pytrends.interest_over_time()
            desire_val = float(desire_df[desire_kws].mean().mean()) if not desire_df.empty else 0.0

            pytrends.build_payload(identity_kws, cat=0, timeframe="now 7-d", geo=geo)
            identity_df = pytrends.interest_over_time()
            identity_val = float(identity_df[identity_kws].mean().mean()) if not identity_df.empty else 0.0

            composite = (fear_val + desire_val + identity_val) / 3.0
            return Reading(
                source_id=self.id, timestamp=datetime.utcnow(), scope=scope,
                status="ok", raw_value=composite,
                normalized_value=composite / 100.0,
                confidence=0.7,
            )
        except Exception:
            return Reading(
                source_id=self.id, timestamp=datetime.utcnow(), scope=scope,
                status="error", raw_value=0.0, normalized_value=0.0, confidence=0.0,
            )

    def to_forces(self, reading: Reading) -> ForceActivation:
        if reading.status == "error":
            return ForceActivation(
                source_id=self.id, timestamp=reading.timestamp, scope=reading.scope,
                forces=np.zeros(NUM_FORCES), confidence=np.zeros(NUM_FORCES),
            )
        return self.from_values(
            fear_terms=reading.raw_value,
            desire_terms=reading.raw_value * 0.8,
            identity_terms=reading.raw_value * 0.6,
            scope=reading.scope, timestamp=reading.timestamp,
        )

    def from_values(
        self,
        fear_terms: float,
        desire_terms: float,
        identity_terms: float,
        scope: Optional[GeoScope] = None,
        timestamp: Optional[datetime] = None,
    ) -> ForceActivation:
        if scope is None:
            scope = GeoScope.national("US")
        if timestamp is None:
            timestamp = datetime.utcnow()

        key = scope.country_code or "US"
        for name, val in [("fear", fear_terms), ("desire", desire_terms), ("identity", identity_terms)]:
            bk = f"{key}_{name}"
            if bk not in self._baselines:
                self._baselines[bk] = WelfordState()
            self._baselines[bk].update(val)

        fear_z = self._baselines[f"{key}_fear"].z_score(fear_terms)
        des_z = self._baselines[f"{key}_desire"].z_score(desire_terms)
        id_z = self._baselines[f"{key}_identity"].z_score(identity_terms)

        forces = np.zeros(NUM_FORCES)
        forces[Force.FEAR] = np.clip(fear_z * 0.4, -1, 1)
        forces[Force.DESIRE] = np.clip(des_z * 0.3, -1, 1)
        forces[Force.IDENTITY] = np.clip(id_z * 0.3, -1, 1)
        forces[Force.COLLECTIVE] = np.clip((fear_z + des_z) * 0.15, -1, 1)

        n_obs = min(
            self._baselines[f"{key}_fear"].n,
            self._baselines[f"{key}_desire"].n,
        )
        base_conf = min(1.0, n_obs / 14.0)
        confidence = np.zeros(NUM_FORCES)
        for f in self.target_forces:
            confidence[f.value] = base_conf

        return ForceActivation(
            source_id=self.id, timestamp=timestamp, scope=scope,
            forces=forces, confidence=confidence,
        )


# --- Source Registry ---

_ADAPTERS: Dict[str, SourceAdapter] = {}


def register_adapter(adapter: SourceAdapter) -> None:
    _ADAPTERS[adapter.id] = adapter


def get_adapter(source_id: str) -> Optional[SourceAdapter]:
    return _ADAPTERS.get(source_id)


def list_adapters() -> List[str]:
    return list(_ADAPTERS.keys())


def _init_default_adapters() -> None:
    if not _ADAPTERS:
        register_adapter(GDELTAdapter())
        register_adapter(ACLEDAdapter())
        register_adapter(FREDAdapter())
        register_adapter(GoogleTrendsAdapter())


# --- Receiver State & Orchestration ---

@dataclass
class ReceiverState:
    """Current aggregated field state from all sources."""
    forces: np.ndarray = field(default_factory=lambda: np.zeros(NUM_FORCES))
    confidence: np.ndarray = field(default_factory=lambda: np.zeros(NUM_FORCES))
    n_sources: int = 0
    last_update: Optional[datetime] = None
    activations: List[ForceActivation] = field(default_factory=list)
    country_states: Dict[str, "ReceiverState"] = field(default_factory=dict)


def aggregate_activations(
    activations: List[ForceActivation],
    now: Optional[datetime] = None,
) -> ReceiverState:
    if not activations:
        return ReceiverState()

    if now is None:
        now = datetime.utcnow()

    global_forces = np.zeros(NUM_FORCES)
    global_weights = np.zeros(NUM_FORCES)
    country_forces: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}

    for act in activations:
        adapter = get_adapter(act.source_id)
        cadence = adapter.cadence if adapter else "daily"
        fresh = freshness_weight(act.timestamp, now, cadence)

        weighted_forces = act.forces * act.confidence * fresh
        weighted_conf = act.confidence * fresh

        if act.scope.country_code and act.scope.country_code != "global":
            cc = act.scope.country_code
            if cc not in country_forces:
                country_forces[cc] = (np.zeros(NUM_FORCES), np.zeros(NUM_FORCES))
            cf, cw = country_forces[cc]
            cf += weighted_forces
            cw += weighted_conf
        else:
            global_forces += weighted_forces
            global_weights += weighted_conf

    safe_global = np.where(global_weights > 1e-8, global_weights, 1.0)
    agg_forces = global_forces / safe_global
    agg_conf = np.clip(global_weights, 0, 1)

    country_states = {}
    for cc, (cf, cw) in country_forces.items():
        combined_f = global_forces + cf
        combined_w = global_weights + cw
        safe_w = np.where(combined_w > 1e-8, combined_w, 1.0)
        country_states[cc] = ReceiverState(
            forces=combined_f / safe_w,
            confidence=np.clip(combined_w, 0, 1),
            n_sources=len([a for a in activations if a.scope.country_code == cc]),
            last_update=now,
        )

    return ReceiverState(
        forces=agg_forces,
        confidence=agg_conf,
        n_sources=len(activations),
        last_update=now,
        activations=activations,
        country_states=country_states,
    )


# --- Question-Relevance Gate (§25) ---

def compute_field_shift(
    receiver_state: ReceiverState,
    question: Question,
    relevance: Optional[ForceRelevance] = None,
    gain: float = 0.1,
) -> np.ndarray:
    """Compute the field_shift vector for a question given receiver state.

    Δs = Σ_f  F_f · R_{q,f} · D_{q,f} · C_f · gain

    F = observed field activation
    R = |weight| relevance (normalized)
    D = sign(weight) direction
    C = source confidence
    """
    if relevance is None:
        relevance = compute_relevance(question)

    F = receiver_state.forces
    R = relevance.relevance
    D = np.sign(question.weights)
    C = receiver_state.confidence

    shift = F * R * D * C * gain
    return shift


def compute_country_field_shift(
    receiver_state: ReceiverState,
    question: Question,
    country_code: str,
    relevance: Optional[ForceRelevance] = None,
    gain: float = 0.1,
) -> np.ndarray:
    if country_code in receiver_state.country_states:
        state = receiver_state.country_states[country_code]
    else:
        state = receiver_state

    return compute_field_shift(state, question, relevance, gain)


def run_with_receiver(
    question: Question,
    civ: Civilization,
    receiver_state: ReceiverState,
    gain: float = 0.1,
    epsilon: float = 0.18,
    layers: int = 8,
):
    shift = compute_field_shift(receiver_state, question, gain=gain)
    return run_question(question, civ, epsilon=epsilon, layers=layers, field_shift=shift)


# ---------------------------------------------------------------------------
#  Build 3 — Falsification / Placebo Testing
# ---------------------------------------------------------------------------

@dataclass
class PlaceboResult:
    """Result of a single experimental condition."""
    condition: str
    yes_pct: float
    dominant: str
    conviction: float
    fragility: float
    field_shift_magnitude: float


@dataclass
class FalsificationReport:
    """Complete falsification experiment results."""
    question_id: str
    conditions: Dict[str, PlaceboResult]
    real_vs_off_delta: float
    time_placebo_delta: float
    country_placebo_delta: float
    sign_placebo_delta: float
    real_signal_exceeds_placebo: bool
    signal_to_noise: float


def _run_condition(
    question: Question,
    civ: Civilization,
    field_shift: Optional[np.ndarray],
    condition_name: str,
) -> PlaceboResult:
    r = run_question(question, civ, field_shift=field_shift)
    mag = float(np.linalg.norm(field_shift)) if field_shift is not None else 0.0
    return PlaceboResult(
        condition=condition_name,
        yes_pct=r.yes_pct,
        dominant=r.dominant.name.lower(),
        conviction=r.conviction,
        fragility=r.fragility,
        field_shift_magnitude=round(mag, 6),
    )


def run_falsification(
    question: Question,
    civ: Civilization,
    real_activations: List[ForceActivation],
    rng_seed: int = 42,
) -> FalsificationReport:
    """Run a full falsification experiment: OFF, REAL, TIME_PLACEBO,
    COUNTRY_PLACEBO, SIGN_PLACEBO."""

    _init_default_adapters()
    rng = make_rng(rng_seed)
    relevance = compute_relevance(question)

    # Condition 1: OFF (no receiver)
    off = _run_condition(question, civ, None, "OFF")

    # Condition 2: REAL (actual signals)
    real_state = aggregate_activations(real_activations)
    real_shift = compute_field_shift(real_state, question, relevance)
    real = _run_condition(question, civ, real_shift, "REAL")

    # Condition 3: TIME_PLACEBO (shuffle timestamps)
    time_shuffled = []
    for act in real_activations:
        shuffled = ForceActivation(
            source_id=act.source_id,
            timestamp=act.timestamp - timedelta(days=int(rng.integers(30, 365))),
            scope=act.scope,
            forces=act.forces,
            confidence=act.confidence * 0.5,
            provenance={"placebo": "time_shuffle"},
        )
        time_shuffled.append(shuffled)
    time_state = aggregate_activations(time_shuffled)
    time_shift = compute_field_shift(time_state, question, relevance)
    time_placebo = _run_condition(question, civ, time_shift, "TIME_PLACEBO")

    # Condition 4: COUNTRY_PLACEBO (wrong country data)
    country_shuffled = []
    country_codes = ["US", "GB", "DE", "BR", "NG", "IN", "JP", "MX", "FR"]
    for act in real_activations:
        wrong_country = country_codes[int(rng.integers(0, len(country_codes)))]
        shuffled_scope = GeoScope(
            scale=act.scope.scale,
            country_code=wrong_country,
            region=act.scope.region,
        )
        shuffled = ForceActivation(
            source_id=act.source_id,
            timestamp=act.timestamp,
            scope=shuffled_scope,
            forces=act.forces,
            confidence=act.confidence,
            provenance={"placebo": "country_shuffle"},
        )
        country_shuffled.append(shuffled)
    country_state = aggregate_activations(country_shuffled)
    country_shift = compute_field_shift(country_state, question, relevance)
    country_placebo = _run_condition(question, civ, country_shift, "COUNTRY_PLACEBO")

    # Condition 5: SIGN_PLACEBO (flip force direction)
    sign_shift = -real_shift
    sign_placebo = _run_condition(question, civ, sign_shift, "SIGN_PLACEBO")

    # Analysis
    real_delta = abs(real.yes_pct - off.yes_pct)
    time_delta = abs(time_placebo.yes_pct - off.yes_pct)
    country_delta = abs(country_placebo.yes_pct - off.yes_pct)
    sign_delta = abs(sign_placebo.yes_pct - off.yes_pct)

    max_placebo = max(time_delta, country_delta, 1e-8)
    signal_to_noise = real_delta / max_placebo

    exceeds = real_delta > max(time_delta, country_delta) * 1.5

    return FalsificationReport(
        question_id=question.id,
        conditions={
            "OFF": off,
            "REAL": real,
            "TIME_PLACEBO": time_placebo,
            "COUNTRY_PLACEBO": country_placebo,
            "SIGN_PLACEBO": sign_placebo,
        },
        real_vs_off_delta=round(real_delta, 6),
        time_placebo_delta=round(time_delta, 6),
        country_placebo_delta=round(country_delta, 6),
        sign_placebo_delta=round(sign_delta, 6),
        real_signal_exceeds_placebo=exceeds,
        signal_to_noise=round(signal_to_noise, 4),
    )


def run_full_falsification_suite(
    civ: Civilization,
    real_activations: List[ForceActivation],
    question_ids: Optional[List[str]] = None,
) -> List[FalsificationReport]:
    if question_ids is None:
        question_ids = [q.id for q in QUESTIONS if q.domain == "belief_causal"]

    reports = []
    for qid in question_ids:
        q = question_by_id(qid)
        if q and q.domain == "belief_causal":
            report = run_falsification(q, civ, real_activations)
            reports.append(report)
    return reports


# --- Initialize on import ---
_init_default_adapters()
