"""CRUD operations for foresight persistence.

All functions accept an explicit session — the caller controls the transaction.
Every function is a no-op that returns None if session is None (DB disabled).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from earth1.db.models import (
    Run, Prediction, Outcome, Claim, CorrectionRecord,
    ManifoldVersion, AgentSnapshot, HoldoutResult, ForceOutcome,
)


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


def save_claim(
    session,
    user_id: str,
    agent_idx: int,
    country_code: str,
    match_score: float,
    demographics: Optional[Dict] = None,
) -> Optional[Claim]:
    if session is None:
        return None

    claim = Claim(
        user_id=user_id,
        agent_idx=agent_idx,
        country_code=country_code,
        match_score=match_score,
        demographics=demographics or {},
    )
    session.add(claim)
    session.commit()
    session.refresh(claim)
    return claim


def save_correction_record(
    session,
    claim_id: str,
    question_id: str,
    model_stance: float,
    corrected_stance: float,
    n_region_updated: int = 0,
    trait_deltas: Optional[Dict] = None,
    consent: bool = True,
) -> Optional[CorrectionRecord]:
    if session is None:
        return None

    rec = CorrectionRecord(
        claim_id=claim_id,
        question_id=question_id,
        model_stance=model_stance,
        corrected_stance=corrected_stance,
        delta=abs(corrected_stance - model_stance),
        n_region_updated=n_region_updated,
        trait_deltas=trait_deltas or {},
        consent=consent,
    )
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec


def get_claim(session, claim_id: str) -> Optional[Claim]:
    if session is None:
        return None
    return session.query(Claim).filter_by(id=claim_id).first()


def list_claims(
    session,
    user_id: Optional[str] = None,
    status: str = "active",
    limit: int = 50,
) -> List[Claim]:
    if session is None:
        return []
    q = session.query(Claim).filter(Claim.status == status)
    if user_id:
        q = q.filter(Claim.user_id == user_id)
    return q.order_by(Claim.created_at.desc()).limit(limit).all()


def list_correction_records(
    session,
    claim_id: Optional[str] = None,
    limit: int = 100,
) -> List[CorrectionRecord]:
    if session is None:
        return []
    q = session.query(CorrectionRecord)
    if claim_id:
        q = q.filter(CorrectionRecord.claim_id == claim_id)
    return q.order_by(CorrectionRecord.created_at.desc()).limit(limit).all()


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


# --- Manifold versioning ---

def compute_pop_hash(civ) -> str:
    import hashlib
    return hashlib.sha256(civ.forces.tobytes()).hexdigest()


def save_manifold(
    session,
    civ,
    kind: str = "frozen",
    metadata: Optional[Dict] = None,
) -> Optional[ManifoldVersion]:
    if session is None:
        return None

    from earth1.engine import _is_genesis
    if _is_genesis(civ):
        from earth1.genesis import GENESIS_COUNTRIES
        country_count = len(GENESIS_COUNTRIES)
    else:
        from earth1.population import COUNTRIES
        country_count = len(COUNTRIES)
    mv = ManifoldVersion(
        kind=kind,
        pop_hash=compute_pop_hash(civ),
        population=civ.n,
        seed=civ.seed,
        country_count=country_count,
        metadata_=metadata or {},
    )
    session.add(mv)
    session.commit()
    session.refresh(mv)
    return mv


def save_agent_batch(
    session,
    manifold_id: str,
    civ,
    sample_n: int = 1000,
) -> int:
    if session is None:
        return 0

    import numpy as np
    from earth1.engine import _is_genesis
    if _is_genesis(civ):
        from earth1.genesis import GENESIS_COUNTRIES as _countries
        _code_key = "iso2"
    else:
        from earth1.population import COUNTRIES as _countries
        _code_key = "code"

    indices = np.random.default_rng(42).choice(civ.n, size=min(sample_n, civ.n), replace=False)
    indices.sort()

    snapshots = []
    for idx in indices:
        country_code = _countries[int(civ.country[idx])][_code_key]
        snap = AgentSnapshot(
            manifold_id=manifold_id,
            agent_idx=int(idx),
            country_code=country_code,
            traits={
                "openness": float(civ.openness[idx]),
                "empathy": float(civ.empathy[idx]),
                "risk_appetite": float(civ.risk_appetite[idx]),
                "doubt": float(civ.doubt[idx]),
                "desire_intensity": float(civ.desire_intensity[idx]),
                "conscientiousness": float(civ.conscientiousness[idx]),
                "agreeableness": float(civ.agreeableness[idx]),
                "extraversion": float(civ.extraversion[idx]),
                "neuroticism": float(civ.neuroticism[idx]),
            },
            forces=[float(civ.forces[idx, f]) for f in range(8)],
            alpha=float(civ.alpha[idx]),
            demographics={
                "age": float(civ.age[idx]),
                "education": int(civ.education[idx]),
                "income": int(civ.income[idx]),
                "urban": bool(civ.urban[idx]),
            },
        )
        snapshots.append(snap)

    session.add_all(snapshots)
    session.commit()
    return len(snapshots)


def get_manifold(session, manifold_id: str) -> Optional[ManifoldVersion]:
    if session is None:
        return None
    return session.query(ManifoldVersion).filter_by(id=manifold_id).first()


def list_manifolds(
    session,
    kind: Optional[str] = None,
    limit: int = 50,
) -> List[ManifoldVersion]:
    if session is None:
        return []
    q = session.query(ManifoldVersion)
    if kind:
        q = q.filter(ManifoldVersion.kind == kind)
    return q.order_by(ManifoldVersion.created_at.desc()).limit(limit).all()


def save_holdout_result(
    session,
    manifold_id: str,
    question_id: str,
    yes_pct: float,
    dominant: str,
    conviction: float,
) -> Optional[HoldoutResult]:
    if session is None:
        return None

    hr = HoldoutResult(
        manifold_id=manifold_id,
        question_id=question_id,
        yes_pct=yes_pct,
        dominant=dominant,
        conviction=conviction,
    )
    session.add(hr)
    session.commit()
    session.refresh(hr)
    return hr


# --- Standing record + Force-Outcome Atlas ---

def arm_prediction(session, prediction_id: str) -> Optional[Prediction]:
    if session is None:
        return None

    import hashlib
    pred = session.query(Prediction).filter_by(id=prediction_id).first()
    if not pred:
        raise ValueError(f"Prediction {prediction_id} not found")
    if pred.armed:
        raise ValueError(f"Prediction {prediction_id} already armed")

    content = f"{pred.question_text}|{pred.predicted_yes_pct}|{pred.horizon_days}"
    pred.prediction_hash = hashlib.sha256(content.encode()).hexdigest()
    pred.armed = True
    pred.armed_at = datetime.utcnow()
    session.commit()
    session.refresh(pred)
    return pred


def resolve_with_atlas(
    session,
    prediction_id: str,
    actual_yes_pct: float,
    source: str,
    source_url: str = "",
) -> Optional[ForceOutcome]:
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

    anatomy = pred.force_anatomy or {}
    dominant = max(anatomy, key=anatomy.get) if anatomy else "unknown"

    fo = ForceOutcome(
        prediction_id=prediction_id,
        dominant_force=dominant,
        force_signature=anatomy,
        fragility_at_prediction=pred.fragility,
        predicted_yes_pct=pred.predicted_yes_pct,
        actual_yes_pct=actual_yes_pct,
        error=error,
        resolved_at=datetime.utcnow(),
    )
    session.add(fo)
    session.commit()
    session.refresh(fo)
    return fo


def query_atlas(
    session,
    dominant_force: Optional[str] = None,
    min_fragility: Optional[float] = None,
    limit: int = 100,
) -> List[ForceOutcome]:
    if session is None:
        return []

    q = session.query(ForceOutcome)
    if dominant_force:
        q = q.filter(ForceOutcome.dominant_force == dominant_force)
    if min_fragility is not None:
        q = q.filter(ForceOutcome.fragility_at_prediction >= min_fragility)
    return q.order_by(ForceOutcome.resolved_at.desc()).limit(limit).all()
