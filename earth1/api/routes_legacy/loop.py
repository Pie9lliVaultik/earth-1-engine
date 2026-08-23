"""API routes for the Participatory Calibration Loop (G6).

Claim → Reveal → Correct → Measure.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Optional, List

from earth1.api.schemas import (
    ClaimRequest, ClaimSchema, RevealSchema,
    CorrectRequest, CorrectionResultSchema,
    CalibrationRequest, CalibrationReportSchema,
)
from earth1.api.deps import get_civ
from earth1.loop import (
    claim_earthling, reveal_profile, apply_corrections,
    measure_calibration, Correction,
)

router = APIRouter(prefix="/loop", tags=["loop"])


@router.post("/claim", response_model=ClaimSchema)
def claim(req: ClaimRequest):
    civ = get_civ()
    try:
        claimed = claim_earthling(
            civ,
            user_id=req.user_id,
            country_code=req.country_code,
            age=req.age,
            education=req.education,
            income=req.income,
            urban=req.urban,
            openness=req.openness,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    claim_id = ""
    from earth1.db import get_session
    db = get_session()
    if db:
        from earth1.db.store import save_claim
        record = save_claim(
            db,
            user_id=req.user_id,
            agent_idx=claimed.agent_idx,
            country_code=req.country_code,
            match_score=claimed.match_score,
            demographics=claimed.demographics,
        )
        if record:
            claim_id = record.id

    return {
        "claim_id": claim_id or f"mem_{claimed.agent_idx}",
        "agent_idx": claimed.agent_idx,
        "user_id": claimed.user_id,
        "country_code": claimed.country_code,
        "match_score": claimed.match_score,
        "demographics": claimed.demographics,
    }


@router.get("/reveal/{agent_idx}", response_model=RevealSchema)
def reveal(agent_idx: int, questions: Optional[str] = None):
    civ = get_civ()
    if agent_idx < 0 or agent_idx >= civ.n:
        raise HTTPException(400, f"agent_idx out of range: {agent_idx}")

    question_ids = questions.split(",") if questions else None
    profile = reveal_profile(civ, agent_idx, question_ids)
    return profile


@router.post("/correct", response_model=CorrectionResultSchema)
def correct(req: CorrectRequest):
    civ = get_civ()
    if req.agent_idx < 0 or req.agent_idx >= civ.n:
        raise HTTPException(400, f"agent_idx out of range: {req.agent_idx}")

    corrections = [
        Correction(c.question_id, c.corrected_stance)
        for c in req.corrections
    ]

    try:
        result = apply_corrections(
            civ, req.agent_idx, corrections, propagate=req.propagate,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    from earth1.db import get_session
    db = get_session()
    if db:
        from earth1.db.store import save_correction_record
        for corr in req.corrections:
            save_correction_record(
                db,
                claim_id="",
                question_id=corr.question_id,
                model_stance=result.before_stances.get(corr.question_id, 0),
                corrected_stance=corr.corrected_stance,
                n_region_updated=result.n_region_updated,
                trait_deltas=result.trait_deltas,
            )

    return {
        "agent_idx": result.agent_idx,
        "n_region_updated": result.n_region_updated,
        "corrections_applied": result.corrections_applied,
        "before_stances": result.before_stances,
        "after_stances": result.after_stances,
        "trait_deltas": result.trait_deltas,
    }


@router.post("/calibrate", response_model=CalibrationReportSchema)
def calibrate(req: CalibrationRequest):
    civ = get_civ()
    if req.agent_idx < 0 or req.agent_idx >= civ.n:
        raise HTTPException(400, f"agent_idx out of range: {req.agent_idx}")

    corrections = [
        Correction(c.question_id, c.corrected_stance)
        for c in req.corrections
    ]

    try:
        report = measure_calibration(
            civ, corrections, req.agent_idx,
            holdout_question_ids=req.holdout_question_ids,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {
        "n_corrections": report.n_corrections,
        "holdout_error_before": report.holdout_error_before,
        "holdout_error_after": report.holdout_error_after,
        "improvement": report.improvement,
        "improved_questions": report.improved_questions,
        "cohort_improvements": report.cohort_improvements,
    }
