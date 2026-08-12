"""Participatory Calibration — the Loop (G6).

A person claims their Earthling, sees what the model infers about someone
in their position, corrects it, and the correction updates that region
of the manifold.  RLHF from actual people, not the full protocol.

Flow:  claim → reveal → correct → update region → measure improvement

Each correction is a supervised label at a point in soul-space.
Corrections propagate to nearby agents via kernel-weighted region update:
agents in the same demographic cell with similar force profiles receive
a decayed version of the trait shift.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from earth1.types import Civilization, Question, Force, NUM_FORCES
from earth1.population import COUNTRIES, COUNTRY_CODES
from earth1.rng import sigmoid, logit
from earth1.forces import project_all
from earth1.engine import run_question


REGION_LEARNING_RATE = 0.4
SIMILARITY_THRESHOLD = 0.6


@dataclass
class ClaimedEarthling:
    agent_idx: int
    user_id: str
    country_code: str
    match_score: float
    demographics: Dict[str, float]


@dataclass
class Correction:
    question_id: str
    corrected_stance: float  # 0..1


@dataclass
class TraitCorrection:
    trait: str
    value: float


@dataclass
class CorrectionResult:
    agent_idx: int
    n_region_updated: int
    corrections_applied: int
    before_stances: Dict[str, float]
    after_stances: Dict[str, float]
    trait_deltas: Dict[str, float]


@dataclass
class CalibrationReport:
    n_corrections: int
    holdout_error_before: float
    holdout_error_after: float
    improvement: float
    improved_questions: List[str]
    cohort_improvements: Dict[str, float]


def find_nearest_agent(
    civ: Civilization,
    country_code: str,
    age: float = 0.38,
    education: int = 1,
    income: int = 1,
    urban: bool = True,
    openness: float = 0.55,
) -> Tuple[int, float]:
    if country_code not in COUNTRY_CODES:
        raise ValueError(f"Unknown country: {country_code}")

    ci = COUNTRY_CODES.index(country_code)
    country_mask = civ.country == ci

    if not country_mask.any():
        raise ValueError(f"No agents in country {country_code}")

    candidates = np.where(country_mask)[0]

    age_dist = np.abs(civ.age[candidates] - age)
    edu_dist = np.abs(civ.education[candidates] - education).astype(float) / 2.0
    inc_dist = np.abs(civ.income[candidates] - income).astype(float) / 2.0
    urb_dist = (civ.urban[candidates] != urban).astype(float)
    open_dist = np.abs(civ.openness[candidates] - openness)

    distance = (
        0.25 * age_dist
        + 0.20 * edu_dist
        + 0.15 * inc_dist
        + 0.10 * urb_dist
        + 0.30 * open_dist
    )

    best_local = int(np.argmin(distance))
    best_idx = int(candidates[best_local])
    match_score = float(1.0 - np.clip(distance[best_local], 0, 1))

    return best_idx, match_score


def claim_earthling(
    civ: Civilization,
    user_id: str,
    country_code: str,
    age: float = 0.38,
    education: int = 1,
    income: int = 1,
    urban: bool = True,
    openness: float = 0.55,
) -> ClaimedEarthling:
    agent_idx, match_score = find_nearest_agent(
        civ, country_code, age, education, income, urban, openness,
    )
    return ClaimedEarthling(
        agent_idx=agent_idx,
        user_id=user_id,
        country_code=country_code,
        match_score=match_score,
        demographics={
            "age": float(civ.age[agent_idx]),
            "education": int(civ.education[agent_idx]),
            "income": int(civ.income[agent_idx]),
            "urban": bool(civ.urban[agent_idx]),
            "openness": float(civ.openness[agent_idx]),
        },
    )


def reveal_profile(
    civ: Civilization,
    agent_idx: int,
    question_ids: Optional[List[str]] = None,
) -> Dict:
    from earth1.questions import question_by_id, QUESTIONS

    forces = civ.forces[agent_idx]
    traits = {
        "openness": float(civ.openness[agent_idx]),
        "risk_appetite": float(civ.risk_appetite[agent_idx]),
        "doubt": float(civ.doubt[agent_idx]),
        "empathy": float(civ.empathy[agent_idx]),
        "desire_intensity": float(civ.desire_intensity[agent_idx]),
        "economic_field": float(civ.economic_field[agent_idx]),
        "culture_offset": float(civ.culture_offset[agent_idx]),
        "age": float(civ.age[agent_idx]),
    }

    force_profile = {
        Force(i).name.lower(): float(forces[i]) for i in range(NUM_FORCES)
    }

    questions = question_ids or [q.id for q in QUESTIONS if q.domain == "belief_causal"]
    stances = {}
    for qid in questions:
        q = question_by_id(qid)
        if q and q.domain == "belief_causal":
            s0 = project_all(civ, q)
            stances[qid] = round(float(s0[agent_idx]), 4)

    return {
        "agent_idx": agent_idx,
        "country": COUNTRY_CODES[civ.country[agent_idx]],
        "traits": traits,
        "force_profile": force_profile,
        "projected_stances": stances,
    }


def _compute_force_delta(
    civ: Civilization,
    agent_idx: int,
    question: Question,
    corrected_stance: float,
) -> np.ndarray:
    s0 = project_all(civ, question)
    current = float(s0[agent_idx])

    delta_logit = logit(np.array([corrected_stance]))[0] - logit(np.array([current]))[0]

    w = question.weights
    w_norm_sq = float(w @ w)
    if w_norm_sq < 1e-8:
        return np.zeros(NUM_FORCES)

    delta_forces = w * delta_logit / w_norm_sq
    return delta_forces


_FORCE_TO_TRAITS = {
    Force.FEAR: [("doubt", 1.0), ("risk_appetite", -1.0), ("neuroticism", 0.3)],
    Force.DESIRE: [("desire_intensity", 1.0)],
    Force.ECONOMICS: [("economic_field", 1.0)],
    Force.COLLECTIVE: [("openness", -0.6), ("power_distance", 0.4)],
    Force.IDENTITY: [("openness", 0.5), ("individualism", 0.5)],
    Force.CULTURE: [("culture_offset", 1.0), ("long_term_orientation", 0.1)],
    Force.EXPERIENCE: [],  # age is immutable
    Force.TEMPERAMENT: [("risk_appetite", 0.7), ("extraversion", 0.3)],
}


def _apply_trait_deltas(
    civ: Civilization,
    indices: np.ndarray,
    delta_forces: np.ndarray,
    scale: float = 1.0,
) -> Dict[str, float]:
    trait_deltas: Dict[str, float] = {}

    for force_idx in range(NUM_FORCES):
        df = delta_forces[force_idx] * scale
        if abs(df) < 1e-8:
            continue

        mappings = _FORCE_TO_TRAITS[Force(force_idx)]
        n_traits = len(mappings)
        if n_traits == 0:
            continue

        per_trait = df / n_traits
        for trait_name, direction in mappings:
            delta = per_trait * direction
            arr = getattr(civ, trait_name)

            if trait_name == "culture_offset":
                arr[indices] = np.clip(arr[indices] + delta, -0.5, 0.5)
            else:
                arr[indices] = np.clip(arr[indices] + delta, 0, 1)

            trait_deltas[trait_name] = trait_deltas.get(trait_name, 0) + float(delta)

    return trait_deltas


def _recompute_agent_forces(civ: Civilization, indices: np.ndarray) -> None:
    idx = indices
    civ.forces[idx, Force.FEAR] = np.clip(
        (civ.doubt[idx] + (1.0 - civ.risk_appetite[idx]) + civ.neuroticism[idx] * 0.3) / 2.3, 0, 1)
    civ.forces[idx, Force.DESIRE] = civ.desire_intensity[idx]
    civ.forces[idx, Force.ECONOMICS] = civ.economic_field[idx]
    civ.forces[idx, Force.COLLECTIVE] = np.clip(
        (1.0 - civ.openness[idx]) * 0.6 + civ.power_distance[idx] * 0.4, 0, 1)
    civ.forces[idx, Force.IDENTITY] = np.clip(
        civ.openness[idx] * 0.5 + civ.individualism[idx] * 0.5, 0, 1)
    civ.forces[idx, Force.CULTURE] = np.clip(
        0.5 + civ.culture_offset[idx] + civ.long_term_orientation[idx] * 0.1, 0, 1)
    civ.forces[idx, Force.EXPERIENCE] = civ.age[idx]
    civ.forces[idx, Force.TEMPERAMENT] = np.clip(
        civ.risk_appetite[idx] * 0.7 + civ.extraversion[idx] * 0.3, 0, 1)

    civ.alpha[idx] = np.clip(
        0.28 + 0.5 * civ.openness[idx] - 0.12 * (1.0 - civ.openness[idx]), 0, 1)
    civ.means = civ.forces.mean(axis=0)


def _find_region(
    civ: Civilization,
    agent_idx: int,
    max_region: int = 500,
) -> np.ndarray:
    ci = civ.country[agent_idx]
    same_country = np.where(civ.country == ci)[0]

    ref_forces = civ.forces[agent_idx]
    candidate_forces = civ.forces[same_country]

    ref_norm = np.linalg.norm(ref_forces)
    cand_norms = np.linalg.norm(candidate_forces, axis=1)

    denom = ref_norm * cand_norms
    safe_denom = np.where(denom > 1e-8, denom, 1.0)
    cosine_sim = (candidate_forces @ ref_forces) / safe_denom

    age_sim = 1.0 - np.abs(civ.age[same_country] - civ.age[agent_idx])
    edu_sim = (civ.education[same_country] == civ.education[agent_idx]).astype(float)
    urban_sim = (civ.urban[same_country] == civ.urban[agent_idx]).astype(float)

    similarity = (
        0.50 * cosine_sim
        + 0.25 * age_sim
        + 0.15 * edu_sim
        + 0.10 * urban_sim
    )

    above_threshold = similarity >= SIMILARITY_THRESHOLD
    region_local = np.where(above_threshold)[0]

    if len(region_local) > max_region:
        top_k = np.argsort(-similarity[region_local])[:max_region]
        region_local = region_local[top_k]

    return same_country[region_local], similarity[region_local]


def apply_corrections(
    civ: Civilization,
    agent_idx: int,
    corrections: List[Correction],
    propagate: bool = True,
) -> CorrectionResult:
    from earth1.questions import question_by_id

    before_stances = {}
    after_stances = {}
    total_trait_deltas: Dict[str, float] = {}
    n_region = 0

    for corr in corrections:
        q = question_by_id(corr.question_id)
        if q is None:
            raise ValueError(f"Unknown question: {corr.question_id}")

        s0 = project_all(civ, q)
        before_stances[corr.question_id] = round(float(s0[agent_idx]), 4)

        delta_forces = _compute_force_delta(civ, agent_idx, q, corr.corrected_stance)

        agent_arr = np.array([agent_idx])
        deltas = _apply_trait_deltas(civ, agent_arr, delta_forces, scale=1.0)
        for k, v in deltas.items():
            total_trait_deltas[k] = total_trait_deltas.get(k, 0) + v

        _recompute_agent_forces(civ, agent_arr)

        if propagate:
            region_idx, region_sim = _find_region(civ, agent_idx)
            self_mask = region_idx != agent_idx
            region_idx = region_idx[self_mask]
            region_sim = region_sim[self_mask]

            if len(region_idx) > 0:
                weights = region_sim * REGION_LEARNING_RATE
                for i, idx in enumerate(region_idx):
                    _apply_trait_deltas(
                        civ, np.array([idx]), delta_forces, scale=float(weights[i]),
                    )
                _recompute_agent_forces(civ, region_idx)
                n_region = len(region_idx)

        s1 = project_all(civ, q)
        after_stances[corr.question_id] = round(float(s1[agent_idx]), 4)

    return CorrectionResult(
        agent_idx=agent_idx,
        n_region_updated=n_region,
        corrections_applied=len(corrections),
        before_stances=before_stances,
        after_stances=after_stances,
        trait_deltas=total_trait_deltas,
    )


def apply_trait_corrections(
    civ: Civilization,
    agent_idx: int,
    trait_corrections: List[TraitCorrection],
    propagate: bool = True,
) -> Dict:
    agent_arr = np.array([agent_idx])
    deltas = {}

    for tc in trait_corrections:
        if not hasattr(civ, tc.trait):
            raise ValueError(f"Unknown trait: {tc.trait}")
        arr = getattr(civ, tc.trait)
        old_val = float(arr[agent_idx])
        if tc.trait == "culture_offset":
            arr[agent_idx] = np.clip(tc.value, -0.5, 0.5)
        else:
            arr[agent_idx] = np.clip(tc.value, 0, 1)
        deltas[tc.trait] = float(arr[agent_idx]) - old_val

    _recompute_agent_forces(civ, agent_arr)

    n_region = 0
    if propagate:
        region_idx, region_sim = _find_region(civ, agent_idx)
        self_mask = region_idx != agent_idx
        region_idx = region_idx[self_mask]
        region_sim = region_sim[self_mask]

        if len(region_idx) > 0:
            for tc in trait_corrections:
                arr = getattr(civ, tc.trait)
                delta = deltas.get(tc.trait, 0)
                if abs(delta) < 1e-8:
                    continue
                weighted = delta * region_sim * REGION_LEARNING_RATE
                if tc.trait == "culture_offset":
                    arr[region_idx] = np.clip(arr[region_idx] + weighted, -0.5, 0.5)
                else:
                    arr[region_idx] = np.clip(arr[region_idx] + weighted, 0, 1)
            _recompute_agent_forces(civ, region_idx)
            n_region = len(region_idx)

    return {"trait_deltas": deltas, "n_region_updated": n_region}


def measure_calibration(
    civ: Civilization,
    corrections: List[Correction],
    agent_idx: int,
    holdout_question_ids: Optional[List[str]] = None,
) -> CalibrationReport:
    from earth1.questions import question_by_id, QUESTIONS
    from earth1.dynamics import _deep_copy_civ

    if holdout_question_ids is None:
        correction_qids = {c.question_id for c in corrections}
        holdout_question_ids = [
            q.id for q in QUESTIONS
            if q.domain == "belief_causal" and q.id not in correction_qids
        ]

    holdout_questions = []
    for qid in holdout_question_ids:
        q = question_by_id(qid)
        if q and q.domain == "belief_causal":
            holdout_questions.append(q)

    if not holdout_questions:
        return CalibrationReport(
            n_corrections=len(corrections),
            holdout_error_before=0.0,
            holdout_error_after=0.0,
            improvement=0.0,
            improved_questions=[],
            cohort_improvements={},
        )

    ci = civ.country[agent_idx]
    cohort_mask = civ.country == ci

    def cohort_error(c: Civilization) -> Tuple[float, Dict[str, float]]:
        errors = {}
        for q in holdout_questions:
            s = project_all(c, q)
            cohort_mean = float(s[cohort_mask].mean())
            target = sigmoid(np.array([q.baseline]))[0]
            errors[q.id] = abs(cohort_mean - target)
        return float(np.mean(list(errors.values()))), errors

    error_before, per_q_before = cohort_error(civ)

    civ_copy = _deep_copy_civ(civ)
    apply_corrections(civ_copy, agent_idx, corrections, propagate=True)

    error_after, per_q_after = cohort_error(civ_copy)

    improved = [
        qid for qid in per_q_before
        if per_q_after.get(qid, 1.0) < per_q_before[qid]
    ]

    cohort_improvements = {
        qid: round(per_q_before[qid] - per_q_after.get(qid, per_q_before[qid]), 6)
        for qid in per_q_before
    }

    return CalibrationReport(
        n_corrections=len(corrections),
        holdout_error_before=round(error_before, 6),
        holdout_error_after=round(error_after, 6),
        improvement=round(error_before - error_after, 6),
        improved_questions=improved,
        cohort_improvements=cohort_improvements,
    )


def batch_calibrate(
    civ: Civilization,
    claims: List[Dict],
) -> Dict:
    total_region = 0
    total_corrections = 0

    for claim_data in claims:
        agent_idx = claim_data["agent_idx"]
        corrections = [
            Correction(c["question_id"], c["corrected_stance"])
            for c in claim_data["corrections"]
        ]
        result = apply_corrections(civ, agent_idx, corrections, propagate=True)
        total_region += result.n_region_updated
        total_corrections += result.corrections_applied

    return {
        "n_claims": len(claims),
        "total_corrections": total_corrections,
        "total_region_updated": total_region,
    }
