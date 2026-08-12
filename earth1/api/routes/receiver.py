"""API routes for the Field Receiver (Builds 0-3).

Noise profiling, relevance maps, field state, and falsification.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import List, Optional

from earth1.api.schemas import (
    NoiseProfileSchema, ForceRelevanceSchema,
    FieldShiftRequest, FieldShiftSchema,
    FalsificationRequest, FalsificationReportSchema,
    FieldShiftRunRequest, RunResultSchema,
)
from earth1.api.deps import get_civ
from earth1.questions import question_by_id, QUESTIONS
from earth1.receiver import (
    profile_noise, compute_relevance, build_relevance_matrix,
    ReceiverState, aggregate_activations, compute_field_shift,
    run_with_receiver, ForceActivation, GeoScope, Scale,
    run_falsification,
)
from earth1.types import NUM_FORCES

import numpy as np
from datetime import datetime

router = APIRouter(prefix="/receiver", tags=["receiver"])


@router.get("/noise/{question_id}", response_model=NoiseProfileSchema)
def noise_profile(question_id: str, n_seeds: int = 5):
    q = question_by_id(question_id)
    if not q or q.domain != "belief_causal":
        raise HTTPException(400, f"Unknown or non-causal question: {question_id}")
    civ = get_civ()
    profile = profile_noise(q, civ, n_seeds=n_seeds)
    return {
        "question_id": profile.question_id,
        "baseline_yes_pct": profile.baseline_yes_pct,
        "seed_std": profile.seed_std,
        "epsilon_sensitivity": profile.epsilon_sensitivity,
        "layer_sensitivity": profile.layer_sensitivity,
        "minimum_detectable_effect": profile.minimum_detectable_effect,
        "compression_zone": profile.compression_zone,
    }


@router.get("/relevance/{question_id}", response_model=ForceRelevanceSchema)
def relevance(question_id: str):
    q = question_by_id(question_id)
    if not q:
        raise HTTPException(400, f"Unknown question: {question_id}")
    rel = compute_relevance(q)
    return {
        "question_id": rel.question_id,
        "relevance": {f: float(rel.relevance[i]) for i, f in enumerate(
            ["fear", "desire", "economics", "collective", "identity", "culture", "experience", "temperament"]
        )},
        "temporal_sensitivity": rel.temporal_sensitivity,
        "dominant_forces": rel.dominant_forces,
        "irrelevant_forces": rel.irrelevant_forces,
    }


@router.get("/relevance-matrix")
def relevance_matrix():
    matrix = build_relevance_matrix()
    return {
        qid: {
            "relevance": {f: float(rel.relevance[i]) for i, f in enumerate(
                ["fear", "desire", "economics", "collective", "identity", "culture", "experience", "temperament"]
            )},
            "temporal_sensitivity": rel.temporal_sensitivity,
            "dominant_forces": rel.dominant_forces,
        }
        for qid, rel in matrix.items()
    }


@router.post("/field-shift", response_model=FieldShiftSchema)
def field_shift(req: FieldShiftRequest):
    q = question_by_id(req.question_id)
    if not q or q.domain != "belief_causal":
        raise HTTPException(400, f"Unknown or non-causal question: {req.question_id}")

    forces = np.array(req.forces)
    confidence = np.array(req.confidence) if req.confidence else np.ones(NUM_FORCES)

    if forces.shape != (NUM_FORCES,) or confidence.shape != (NUM_FORCES,):
        raise HTTPException(400, f"forces and confidence must be arrays of length {NUM_FORCES}")

    state = ReceiverState(forces=forces, confidence=confidence, n_sources=1)
    shift = compute_field_shift(state, q, gain=req.gain)

    return {
        "question_id": req.question_id,
        "field_shift": {f: float(shift[i]) for i, f in enumerate(
            ["fear", "desire", "economics", "collective", "identity", "culture", "experience", "temperament"]
        )},
        "magnitude": float(np.linalg.norm(shift)),
        "gain": req.gain,
    }


@router.post("/run", response_model=RunResultSchema)
def run_with_field(req: FieldShiftRunRequest):
    q = question_by_id(req.question_id)
    if not q or q.domain != "belief_causal":
        raise HTTPException(400, f"Unknown or non-causal question: {req.question_id}")

    civ = get_civ()

    forces = np.array(req.forces)
    confidence = np.array(req.confidence) if req.confidence else np.ones(NUM_FORCES)
    state = ReceiverState(forces=forces, confidence=confidence, n_sources=1)

    r = run_with_receiver(q, civ, state, gain=req.gain, epsilon=req.epsilon, layers=req.layers)

    return {
        "question_id": r.question.id,
        "question_text": r.question.text,
        "n": r.n,
        "yes_pct": r.yes_pct,
        "frac_yes": r.frac_yes,
        "regime": r.regime,
        "final_distribution": r.final_distribution.tolist() if hasattr(r.final_distribution, 'tolist') else list(r.final_distribution),
        "distribution_by_layer": [d.tolist() if hasattr(d, 'tolist') else list(d) for d in r.distribution_by_layer],
        "force_anatomy": {f: float(r.force_anatomy[i]) for i, f in enumerate(
            ["fear", "desire", "economics", "collective", "identity", "culture", "experience", "temperament"]
        )},
        "dominant": r.dominant.name.lower(),
        "conviction": r.conviction,
        "fragility": r.fragility,
        "camps": {
            k: {"size": c.size, "mean_stance": c.mean_stance, "dominant": c.dominant.name.lower(),
                "contrib": {f: float(c.contrib[i]) for i, f in enumerate(
                    ["fear", "desire", "economics", "collective", "identity", "culture", "experience", "temperament"]
                )}} if c else None
            for k, c in r.camps.items()
        },
        "params": r.params,
    }
