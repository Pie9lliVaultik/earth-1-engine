"""CRUD operations for foresight persistence.

All functions accept an explicit session — the caller controls the transaction.
Every function is a no-op that returns None if session is None (DB disabled).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from earth1.db.models import Run, Prediction, Outcome


def save_run(
    session,
    run_type: str,
    question_text: str,
    yes_pct: float,
    frac_yes: float,
    dominant: str,
    conviction: float = 0.0,
    fragility: float = 0.0,
    binary_question: str = "",
    question_id: str = "",
    country_scope: str = "global",
    temporal_context: str = "",
    confidence_regime: str = "forward_estimate",
    confidence_similarity: float = 0.0,
    force_anatomy: Optional[Dict] = None,
    parameters: Optional[Dict] = None,
    narration: Optional[Dict] = None,
    country_splits: Optional[List] = None,
    gateway_raw: Optional[Dict] = None,
) -> Optional[Run]:
    if session is None:
        return None

    run = Run(
        run_type=run_type,
        question_text=question_text,
        binary_question=binary_question,
        question_id=question_id,
        country_scope=country_scope,
        temporal_context=temporal_context,
        yes_pct=yes_pct,
        frac_yes=frac_yes,
        dominant=dominant,
        conviction=conviction,
        fragility=fragility,
        confidence_regime=confidence_regime,
        confidence_similarity=confidence_similarity,
        force_anatomy=force_anatomy or {},
        parameters=parameters or {},
        narration=narration,
        country_splits=country_splits,
        gateway_raw=gateway_raw,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def save_prediction(
    session,
    run_id: str,
    question_text: str,
    predicted_yes_pct: float,
    confidence_regime: str,
    horizon_days: int,
    confidence_similarity: float = 0.0,
    country_code: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Optional[Prediction]:
    if session is None:
        return None

    pred = Prediction(
        run_id=run_id,
        question_text=question_text,
        country_code=country_code,
        predicted_yes_pct=predicted_yes_pct,
        confidence_regime=confidence_regime,
        confidence_similarity=confidence_similarity,
        horizon_days=horizon_days,
        target_date=datetime.utcnow() + timedelta(days=horizon_days),
        tags=tags or [],
    )
    session.add(pred)
    session.commit()
    session.refresh(pred)
    return pred


def record_outcome(
    session,
    prediction_id: str,
    actual_yes_pct: float,
    source: str,
    source_url: str = "",
) -> Optional[Outcome]:
    if session is None:
        return None

    pred = session.query(Prediction).filter_by(id=prediction_id).first()
    if not pred:
        raise ValueError(f"Prediction {prediction_id} not found")

    error = abs(actual_yes_pct - pred.predicted_yes_pct)

    outcome = Outcome(
        prediction_id=prediction_id,
        actual_yes_pct=actual_yes_pct,
        source=source,
        source_url=source_url,
        error=error,
    )
    session.add(outcome)

    pred.status = "resolved"
    session.commit()
    session.refresh(outcome)
    return outcome


def list_runs(
    session,
    run_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Run]:
    if session is None:
        return []

    q = session.query(Run)
    if run_type:
        q = q.filter(Run.run_type == run_type)
    return q.order_by(Run.created_at.desc()).offset(offset).limit(limit).all()


def get_run(session, run_id: str) -> Optional[Run]:
    if session is None:
        return None
    return session.query(Run).filter_by(id=run_id).first()


def list_predictions(
    session,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Prediction]:
    if session is None:
        return []

    q = session.query(Prediction)
    if status:
        q = q.filter(Prediction.status == status)
    return q.order_by(Prediction.target_date.asc()).offset(offset).limit(limit).all()


def get_prediction(session, prediction_id: str) -> Optional[Prediction]:
    if session is None:
        return None
    return session.query(Prediction).filter_by(id=prediction_id).first()


def prediction_accuracy(session, limit: int = 100) -> Dict:
    if session is None:
        return {"enabled": False}

    resolved = (
        session.query(Prediction)
        .filter(Prediction.status == "resolved")
        .order_by(Prediction.created_at.desc())
        .limit(limit)
        .all()
    )

    if not resolved:
        return {
            "enabled": True,
            "n_resolved": 0,
            "mean_error": None,
            "by_regime": {},
        }

    errors = []
    by_regime: Dict[str, List[float]] = {}

    for pred in resolved:
        for outcome in pred.outcomes:
            errors.append(outcome.error)
            regime = pred.confidence_regime
            if regime not in by_regime:
                by_regime[regime] = []
            by_regime[regime].append(outcome.error)

    import numpy as np
    regime_stats = {}
    for regime, errs in by_regime.items():
        regime_stats[regime] = {
            "n": len(errs),
            "mean_error": round(float(np.mean(errs)), 4),
            "max_error": round(float(np.max(errs)), 4),
        }

    return {
        "enabled": True,
        "n_resolved": len(resolved),
        "mean_error": round(float(np.mean(errors)), 4) if errors else None,
        "by_regime": regime_stats,
    }


def expire_predictions(session) -> int:
    if session is None:
        return 0

    now = datetime.utcnow()
    expired = (
        session.query(Prediction)
        .filter(Prediction.status == "open")
        .filter(Prediction.target_date < now)
        .all()
    )
    for pred in expired:
        pred.status = "expired"
    session.commit()
    return len(expired)
