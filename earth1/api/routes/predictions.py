"""Prediction tracking API — store, resolve, and measure accuracy."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from earth1.api.deps import get_db
from earth1.db import is_enabled
from earth1.db.store import (
    list_runs, get_run,
    save_prediction, list_predictions, get_prediction,
    record_outcome, prediction_accuracy, expire_predictions,
)

router = APIRouter(prefix="/predictions", tags=["predictions"])


class PredictionCreate(BaseModel):
    run_id: str
    horizon_days: int = 90
    country_code: Optional[str] = None
    tags: Optional[List[str]] = None


class OutcomeCreate(BaseModel):
    actual_yes_pct: float
    source: str
    source_url: str = ""


class RunSummary(BaseModel):
    id: str
    created_at: str
    run_type: str
    question_text: str
    yes_pct: float
    dominant: str
    confidence_regime: str


class PredictionSummary(BaseModel):
    id: str
    run_id: str
    created_at: str
    question_text: str
    predicted_yes_pct: float
    confidence_regime: str
    country_code: Optional[str]
    horizon_days: int
    target_date: str
    status: str
    tags: List[str]


class OutcomeSummary(BaseModel):
    id: str
    prediction_id: str
    recorded_at: str
    actual_yes_pct: float
    source: str
    error: float


def _check_enabled():
    if not is_enabled():
        raise HTTPException(
            503,
            "Database not configured. Set DATABASE_URL to enable persistence.",
        )


@router.get("/status")
def status():
    return {"enabled": is_enabled()}


@router.get("/runs", response_model=List[RunSummary])
def runs(run_type: str = None, limit: int = 50, offset: int = 0, db=Depends(get_db)):
    _check_enabled()
    rows = list_runs(db, run_type=run_type, limit=limit, offset=offset)
    return [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "run_type": r.run_type,
            "question_text": r.question_text,
            "yes_pct": r.yes_pct,
            "dominant": r.dominant,
            "confidence_regime": r.confidence_regime,
        }
        for r in rows
    ]


@router.get("/runs/{run_id}")
def run_detail(run_id: str, db=Depends(get_db)):
    _check_enabled()
    r = get_run(db, run_id)
    if not r:
        raise HTTPException(404, "Run not found")
    return {
        "id": r.id,
        "created_at": r.created_at.isoformat(),
        "run_type": r.run_type,
        "question_text": r.question_text,
        "binary_question": r.binary_question,
        "question_id": r.question_id,
        "country_scope": r.country_scope,
        "temporal_context": r.temporal_context,
        "yes_pct": r.yes_pct,
        "frac_yes": r.frac_yes,
        "dominant": r.dominant,
        "conviction": r.conviction,
        "fragility": r.fragility,
        "confidence_regime": r.confidence_regime,
        "confidence_similarity": r.confidence_similarity,
        "force_anatomy": r.force_anatomy,
        "parameters": r.parameters,
        "narration": r.narration,
        "country_splits": r.country_splits,
        "predictions": [
            {
                "id": p.id,
                "predicted_yes_pct": p.predicted_yes_pct,
                "horizon_days": p.horizon_days,
                "target_date": p.target_date.isoformat(),
                "status": p.status,
            }
            for p in r.predictions
        ],
    }


@router.post("/create", response_model=PredictionSummary)
def create_prediction(req: PredictionCreate, db=Depends(get_db)):
    _check_enabled()
    run = get_run(db, req.run_id)
    if not run:
        raise HTTPException(404, "Run not found")

    pred = save_prediction(
        db,
        run_id=req.run_id,
        question_text=run.question_text,
        predicted_yes_pct=run.yes_pct,
        confidence_regime=run.confidence_regime,
        confidence_similarity=run.confidence_similarity,
        horizon_days=req.horizon_days,
        country_code=req.country_code,
        tags=req.tags,
    )
    return {
        "id": pred.id,
        "run_id": pred.run_id,
        "created_at": pred.created_at.isoformat(),
        "question_text": pred.question_text,
        "predicted_yes_pct": pred.predicted_yes_pct,
        "confidence_regime": pred.confidence_regime,
        "country_code": pred.country_code,
        "horizon_days": pred.horizon_days,
        "target_date": pred.target_date.isoformat(),
        "status": pred.status,
        "tags": pred.tags,
    }


@router.get("/list", response_model=List[PredictionSummary])
def list_preds(status: str = None, limit: int = 50, offset: int = 0, db=Depends(get_db)):
    _check_enabled()
    rows = list_predictions(db, status=status, limit=limit, offset=offset)
    return [
        {
            "id": p.id,
            "run_id": p.run_id,
            "created_at": p.created_at.isoformat(),
            "question_text": p.question_text,
            "predicted_yes_pct": p.predicted_yes_pct,
            "confidence_regime": p.confidence_regime,
            "country_code": p.country_code,
            "horizon_days": p.horizon_days,
            "target_date": p.target_date.isoformat(),
            "status": p.status,
            "tags": p.tags,
        }
        for p in rows
    ]


@router.post("/{prediction_id}/resolve", response_model=OutcomeSummary)
def resolve(prediction_id: str, req: OutcomeCreate, db=Depends(get_db)):
    _check_enabled()
    try:
        outcome = record_outcome(
            db,
            prediction_id=prediction_id,
            actual_yes_pct=req.actual_yes_pct,
            source=req.source,
            source_url=req.source_url,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {
        "id": outcome.id,
        "prediction_id": outcome.prediction_id,
        "recorded_at": outcome.recorded_at.isoformat(),
        "actual_yes_pct": outcome.actual_yes_pct,
        "source": outcome.source,
        "error": outcome.error,
    }


@router.get("/accuracy")
def accuracy(limit: int = 100, db=Depends(get_db)):
    return prediction_accuracy(db, limit=limit)


@router.post("/expire")
def expire(db=Depends(get_db)):
    _check_enabled()
    n = expire_predictions(db)
    return {"expired": n}
