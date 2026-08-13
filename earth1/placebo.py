"""Placebo harness — §14 guardrail for the grounding stack.

Every source must beat a shuffled-geography placebo before it is wired
into the living world.  The test runs the actual engine: per-country
predictions under real-geography signals vs. shuffled-geography signals.
A source passes only when real geography produces a statistically
different per-country prediction pattern than random geography — meaning
the source's geographic structure actually changes what the model says
about each country.

A source that fails this test adds noise, not information.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
from scipy import stats as sp_stats

from earth1.types import Civilization, Question, Force, NUM_FORCES
from earth1.receiver import (
    ForceActivation, GeoScope, ReceiverState,
    aggregate_activations, compute_country_field_shift,
    compute_relevance, get_adapter, _init_default_adapters,
)
from earth1.engine import run_question


@dataclass
class SourcePlaceboResult:
    """Outcome of the §14 placebo test for one source."""
    source_id: str
    n_questions: int
    n_countries: int
    n_permutations: int
    real_dispersion: float
    placebo_mean_dispersion: float
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
    proportional to magnitudes[i], with random signs per force.
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


def _per_country_yes_pct(
    civ: Civilization,
    question: Question,
    activations: List[ForceActivation],
    countries: List[str],
    country_indices: Dict[str, np.ndarray],
    gain: float = 0.1,
) -> np.ndarray:
    """Run the question through the actual engine with receiver shifts,
    then extract per-country yes_pct from the settled stances."""
    ref_time = activations[0].timestamp if activations else None
    state = aggregate_activations(activations, now=ref_time)
    relevance = compute_relevance(question)

    shift = np.zeros((civ.n, NUM_FORCES))
    for cc, idx in country_indices.items():
        cc_shift = compute_country_field_shift(state, question, cc, relevance, gain)
        shift[idx] = cc_shift

    r = run_question(question, civ, field_shift=shift)

    pcts = np.zeros(len(countries))
    for i, cc in enumerate(countries):
        if cc in country_indices:
            idx = country_indices[cc]
            if hasattr(r, 'settled_stances') and r.settled_stances is not None:
                pcts[i] = float(r.settled_stances[idx].mean())
            else:
                pcts[i] = r.yes_pct
        else:
            pcts[i] = r.yes_pct
    return pcts


def _build_country_indices(
    civ: Civilization,
    countries: List[str],
) -> Dict[str, np.ndarray]:
    """Map ISO2 country codes to agent index arrays in the civ."""
    from earth1.genesis import GENESIS_COUNTRY_CODES
    code_to_idx = {code: i for i, code in enumerate(GENESIS_COUNTRY_CODES)}
    out = {}
    for cc in countries:
        if cc in code_to_idx:
            cidx = code_to_idx[cc]
            mask = np.where(civ.country == cidx)[0]
            if len(mask) > 0:
                out[cc] = mask
    return out


def _intended_effects(
    activations: List[ForceActivation],
    question: Question,
    countries: List[str],
    country_indices: Dict[str, np.ndarray],
    gain: float = 0.1,
) -> np.ndarray:
    """Compute the intended per-country effect: shift_for_country · weights.

    This is the force-projected scalar shift each country SHOULD
    experience given its geographic signal.  It is the same regardless
    of whether geography is shuffled — it describes what was MEANT for
    each country, not what it actually received.
    """
    ref_time = activations[0].timestamp if activations else None
    state = aggregate_activations(activations, now=ref_time)
    relevance = compute_relevance(question)
    effects = np.zeros(len(countries))
    for i, cc in enumerate(countries):
        if cc in country_indices:
            shift = compute_country_field_shift(state, question, cc, relevance, gain)
            effects[i] = float(shift @ question.weights)
    return effects


def _coherence(
    intended: np.ndarray,
    deviations: np.ndarray,
) -> float:
    """Cosine similarity between intended per-country effects and
    observed per-country deviations from baseline.

    High coherence means the right countries deviate in the right
    direction.  Under shuffled geography, the wrong countries receive
    the wrong signals, so the deviation pattern decouples from what
    was intended — coherence drops.
    """
    n_int = np.linalg.norm(intended)
    n_dev = np.linalg.norm(deviations)
    if n_int < 1e-12 or n_dev < 1e-12:
        return 0.0
    return float(np.dot(intended, deviations) / (n_int * n_dev))


def placebo_test_source(
    source_id: str,
    civ: Civilization,
    questions: List[Question],
    countries: Optional[List[str]] = None,
    n_perms: int = 100,
    seed: int = 42,
    gain: float = 0.1,
) -> SourcePlaceboResult:
    """§14 placebo test for one source, run through the actual engine.

    1. Compute baseline per-country predictions (no receiver).
    2. Compute intended per-country effects from the REAL assignment.
    3. Compute per-country predictions with REAL geography signals.
    4. Shuffle geography n_perms times, compute per-country predictions.
    5. Metric: cosine coherence between intended effects and observed
       per-country deviations.  Under correct geography the right
       countries deviate in the right direction; under shuffled
       geography the pattern decouples.  Source passes if real coherence
       exceeds the 95th percentile of the placebo distribution.
    """
    rng = np.random.default_rng(seed)

    if countries is None:
        countries = ["US", "CN", "IN", "BR", "NG", "DE", "JP", "MX",
                     "RU", "GB", "FR", "ID", "TR", "EG", "PK"]

    country_indices = _build_country_indices(civ, countries)
    active_countries = [cc for cc in countries if cc in country_indices]
    if len(active_countries) < 3:
        return SourcePlaceboResult(
            source_id=source_id, n_questions=len(questions),
            n_countries=len(active_countries), n_permutations=0,
            real_dispersion=0.0, placebo_mean_dispersion=0.0,
            placebo_95th=0.0, p_value=1.0, passes=False, per_question=[],
        )

    n_c = len(active_countries)
    intended_mags = rng.uniform(0.3, 1.0, size=n_c)
    real_acts = _synthetic_activations(source_id, active_countries, intended_mags, rng)

    per_question = []
    real_coherences = []
    placebo_coherences_all = []

    for q in questions:
        baseline_pcts = _per_country_yes_pct(
            civ, q, [], active_countries, country_indices, gain,
        )
        intended = _intended_effects(
            real_acts, q, active_countries, country_indices, gain,
        )

        real_pcts = _per_country_yes_pct(
            civ, q, real_acts, active_countries, country_indices, gain,
        )
        real_devs = real_pcts - baseline_pcts
        real_coh = _coherence(intended, real_devs)
        real_coherences.append(real_coh)

        q_placebo_cohs = []
        for _ in range(n_perms):
            shuffled = _shuffle_geography(real_acts, rng)
            placebo_pcts = _per_country_yes_pct(
                civ, q, shuffled, active_countries, country_indices, gain,
            )
            placebo_devs = placebo_pcts - baseline_pcts
            p_coh = _coherence(intended, placebo_devs)
            q_placebo_cohs.append(p_coh)

        placebo_coherences_all.extend(q_placebo_cohs)
        per_question.append({
            "question_id": q.id,
            "real_coherence": round(real_coh, 6),
            "placebo_mean": round(float(np.mean(q_placebo_cohs)), 6),
            "placebo_95th": round(float(np.percentile(q_placebo_cohs, 95)), 6),
        })

    real_mean = float(np.mean(real_coherences))
    placebo_mean = float(np.mean(placebo_coherences_all))
    placebo_95th = float(np.percentile(placebo_coherences_all, 95))
    p_value = float(np.mean([1.0 if p >= real_mean else 0.0
                             for p in placebo_coherences_all]))

    passes = real_mean > placebo_95th and p_value < 0.05

    return SourcePlaceboResult(
        source_id=source_id,
        n_questions=len(questions),
        n_countries=n_c,
        n_permutations=n_perms,
        real_dispersion=round(real_mean, 6),
        placebo_mean_dispersion=round(placebo_mean, 6),
        placebo_95th=round(placebo_95th, 6),
        p_value=round(p_value, 4),
        passes=passes,
        per_question=per_question,
    )


def run_placebo_gate(
    civ: Civilization,
    questions: List[Question],
    source_ids: Optional[List[str]] = None,
    countries: Optional[List[str]] = None,
    n_perms: int = 100,
    seed: int = 42,
) -> PlaceboPassport:
    """Run the §14 gate for all sources. Returns a passport."""
    _init_default_adapters()
    if source_ids is None:
        source_ids = ["gdelt", "acled", "fred"]

    results = {}
    for sid in source_ids:
        results[sid] = placebo_test_source(
            sid, civ, questions, countries, n_perms, seed,
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
            f"coherence={r.real_dispersion:.4f}  "
            f"placebo_95={r.placebo_95th:.4f}  "
            f"p={r.p_value:.3f}"
        )
    lines.append("-" * 40)
    lines.append(f"Gate: {'ALL PASS' if passport.all_pass else 'BLOCKED'}")
    return "\n".join(lines)
