"""Placebo harness — §14 guardrail for the grounding stack.

Every source must beat a shuffled-geography placebo before it is wired
into the living world.  The test: synthetic country-specific signals are
routed through the receiver pipeline.  Under real geography the
resulting per-country force-field shifts must correlate with the intended
signal pattern better than under randomly shuffled geography.

A source that fails this test adds noise, not information.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy import stats as sp_stats

from earth1.types import Question, Force, NUM_FORCES
from earth1.receiver import (
    ForceActivation, GeoScope, ReceiverState,
    aggregate_activations, compute_country_field_shift,
    compute_relevance, get_adapter, _init_default_adapters,
)


@dataclass
class SourcePlaceboResult:
    """Outcome of the §14 placebo test for one source."""
    source_id: str
    n_questions: int
    n_countries: int
    n_permutations: int
    real_specificity: float
    placebo_mean: float
    placebo_95th: float
    p_value: float
    passes: bool
    per_question: List[Dict]


@dataclass
class PlaceboPassport:
    """Aggregate pass/fail for all sources — the §14 gate."""
    results: Dict[str, SourcePlaceboResult]
    all_pass: bool
    timestamp: str


def _synthetic_activations(
    source_id: str,
    countries: List[str],
    magnitudes: np.ndarray,
    rng: np.random.Generator,
    timestamp: Optional[datetime] = None,
) -> List[ForceActivation]:
    """Create synthetic activations with known per-country magnitudes.

    Each country gets a ForceActivation whose force vector magnitude is
    proportional to magnitudes[i].  This lets us measure whether the
    receiver pipeline preserves geographic specificity.
    """
    _init_default_adapters()
    adapter = get_adapter(source_id)
    if adapter is None:
        raise ValueError(f"unknown source: {source_id}")
    target_forces = adapter.target_forces
    ts = timestamp or datetime(2026, 1, 15, 12, 0, 0)

    activations = []
    for cc, mag in zip(countries, magnitudes):
        forces = np.zeros(NUM_FORCES)
        signs = rng.choice([-1.0, 1.0], size=len(target_forces))
        for j, f in enumerate(target_forces):
            forces[f.value] = float(mag) * signs[j]

        confidence = np.zeros(NUM_FORCES)
        for f in target_forces:
            confidence[f.value] = 0.8

        activations.append(ForceActivation(
            source_id=source_id,
            timestamp=ts,
            scope=GeoScope.national(cc),
            forces=forces,
            confidence=confidence,
        ))
    return activations


def _shuffle_geography(
    activations: List[ForceActivation],
    rng: np.random.Generator,
) -> List[ForceActivation]:
    """Return a copy with country codes permuted."""
    codes = [a.scope.country_code for a in activations]
    shuffled_codes = list(rng.permutation(codes))
    out = []
    for act, new_cc in zip(activations, shuffled_codes):
        out.append(ForceActivation(
            source_id=act.source_id,
            timestamp=act.timestamp,
            scope=GeoScope.national(new_cc),
            forces=act.forces.copy(),
            confidence=act.confidence.copy(),
            provenance={"placebo": "geography_shuffle"},
        ))
    return out


def _per_country_shift_magnitude(
    activations: List[ForceActivation],
    question: Question,
    countries: List[str],
    gain: float = 0.1,
) -> np.ndarray:
    """Compute |field_shift| per country for a question."""
    ref_time = activations[0].timestamp if activations else None
    state = aggregate_activations(activations, now=ref_time)
    relevance = compute_relevance(question)
    mags = np.zeros(len(countries))
    for i, cc in enumerate(countries):
        shift = compute_country_field_shift(state, question, cc, relevance, gain)
        mags[i] = float(np.linalg.norm(shift))
    return mags


def _geographic_specificity(
    intended_magnitudes: np.ndarray,
    observed_magnitudes: np.ndarray,
) -> float:
    """Spearman ρ between intended and observed per-country magnitudes.

    High ρ means the pipeline routes signals to the correct countries.
    Under shuffled geography, ρ should be near zero.
    """
    if len(intended_magnitudes) < 3:
        return 0.0
    if np.std(observed_magnitudes) < 1e-12:
        return 0.0
    rho, _ = sp_stats.spearmanr(intended_magnitudes, observed_magnitudes)
    return float(rho) if np.isfinite(rho) else 0.0


def placebo_test_source(
    source_id: str,
    questions: List[Question],
    countries: Optional[List[str]] = None,
    n_perms: int = 200,
    seed: int = 42,
    gain: float = 0.1,
) -> SourcePlaceboResult:
    """§14 placebo test for one source.

    1. Create synthetic country-specific activations with varying magnitudes.
    2. For each question, compute per-country shift magnitudes (REAL).
    3. Shuffle geography n_perms times, compute the same (PLACEBO).
    4. Source passes if mean Spearman ρ(intended, observed) under REAL
       exceeds the 95th percentile of the PLACEBO distribution.
    """
    rng = np.random.default_rng(seed)

    if countries is None:
        countries = ["US", "CN", "IN", "BR", "NG", "DE", "JP", "MX",
                     "RU", "GB", "FR", "ID", "TR", "EG", "PK"]

    n_c = len(countries)
    intended = rng.uniform(0.2, 1.0, size=n_c)
    real_acts = _synthetic_activations(source_id, countries, intended, rng)

    per_question = []
    real_rhos = []
    placebo_rhos_all = []

    for q in questions:
        real_mags = _per_country_shift_magnitude(real_acts, q, countries, gain)
        real_rho = _geographic_specificity(intended, real_mags)
        real_rhos.append(real_rho)

        q_placebo_rhos = []
        for _ in range(n_perms):
            shuffled = _shuffle_geography(real_acts, rng)
            placebo_mags = _per_country_shift_magnitude(shuffled, q, countries, gain)
            p_rho = _geographic_specificity(intended, placebo_mags)
            q_placebo_rhos.append(p_rho)

        placebo_rhos_all.extend(q_placebo_rhos)
        per_question.append({
            "question_id": q.id,
            "real_rho": round(real_rho, 4),
            "placebo_mean": round(float(np.mean(q_placebo_rhos)), 4),
            "placebo_95th": round(float(np.percentile(q_placebo_rhos, 95)), 4),
        })

    real_mean = float(np.mean(real_rhos))
    placebo_mean = float(np.mean(placebo_rhos_all))
    placebo_95th = float(np.percentile(placebo_rhos_all, 95))
    p_value = float(np.mean([1.0 if p >= real_mean else 0.0
                             for p in placebo_rhos_all]))

    passes = real_mean > placebo_95th and p_value < 0.05

    return SourcePlaceboResult(
        source_id=source_id,
        n_questions=len(questions),
        n_countries=n_c,
        n_permutations=n_perms,
        real_specificity=round(real_mean, 4),
        placebo_mean=round(placebo_mean, 4),
        placebo_95th=round(placebo_95th, 4),
        p_value=round(p_value, 4),
        passes=passes,
        per_question=per_question,
    )


def run_placebo_gate(
    questions: List[Question],
    source_ids: Optional[List[str]] = None,
    countries: Optional[List[str]] = None,
    n_perms: int = 200,
    seed: int = 42,
) -> PlaceboPassport:
    """Run the §14 gate for all sources. Returns a passport."""
    _init_default_adapters()
    if source_ids is None:
        source_ids = ["gdelt", "acled", "fred"]

    results = {}
    for sid in source_ids:
        results[sid] = placebo_test_source(
            sid, questions, countries, n_perms, seed,
        )

    return PlaceboPassport(
        results=results,
        all_pass=all(r.passes for r in results.values()),
        timestamp=datetime.utcnow().isoformat(),
    )


def print_passport(passport: PlaceboPassport) -> str:
    """Human-readable §14 gate report."""
    lines = ["§14 Placebo Gate Report", "=" * 40]
    for sid, r in passport.results.items():
        status = "PASS" if r.passes else "FAIL"
        lines.append(
            f"  {sid:20s}  {status}  "
            f"rho={r.real_specificity:.3f}  "
            f"placebo_95={r.placebo_95th:.3f}  "
            f"p={r.p_value:.3f}"
        )
    lines.append("-" * 40)
    lines.append(f"Gate: {'ALL PASS' if passport.all_pass else 'BLOCKED'}")
    return "\n".join(lines)
