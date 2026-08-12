"""SQLAlchemy models for foresight persistence.

Tables:
  runs         — every query to the engine (mind, freetext, timeline)
  predictions  — forward-looking claims with target dates
  outcomes     — real-world results matched against predictions
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Boolean, Integer, DateTime,
    Text, ForeignKey, Index, JSON,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def _uuid():
    return str(uuid.uuid4())


class Run(Base):
    __tablename__ = "runs"

    id = Column(String(36), primary_key=True, default=_uuid)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    run_type = Column(String(20), nullable=False)
    question_text = Column(Text, nullable=False)
    binary_question = Column(Text, default="")
    question_id = Column(String(80), default="")

    country_scope = Column(String(10), default="global")
    temporal_context = Column(Text, default="")

    yes_pct = Column(Float, nullable=False)
    frac_yes = Column(Float, nullable=False)
    dominant = Column(String(20), nullable=False)
    conviction = Column(Float, default=0.0)
    fragility = Column(Float, default=0.0)

    confidence_regime = Column(String(20), default="forward_estimate")
    confidence_similarity = Column(Float, default=0.0)

    force_anatomy = Column(JSON, default=dict)
    parameters = Column(JSON, default=dict)
    narration = Column(JSON, nullable=True)
    country_splits = Column(JSON, nullable=True)

    gateway_raw = Column(JSON, nullable=True)

    predictions = relationship("Prediction", back_populates="run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_runs_created", "created_at"),
        Index("ix_runs_question_id", "question_id"),
        Index("ix_runs_type", "run_type"),
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String(36), primary_key=True, default=_uuid)
    run_id = Column(String(36), ForeignKey("runs.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    question_text = Column(Text, nullable=False)
    country_code = Column(String(10), nullable=True)

    predicted_yes_pct = Column(Float, nullable=False)
    confidence_regime = Column(String(20), nullable=False)
    confidence_similarity = Column(Float, default=0.0)

    horizon_days = Column(Integer, nullable=False)
    target_date = Column(DateTime, nullable=False)

    status = Column(String(20), default="open")
    tags = Column(JSON, default=list)

    armed = Column(Boolean, default=False)
    armed_at = Column(DateTime, nullable=True)
    prediction_hash = Column(String(64), nullable=True)
    manifold_version_id = Column(String(36), nullable=True)
    force_anatomy = Column(JSON, default=dict)
    fragility = Column(Float, default=0.0)

    run = relationship("Run", back_populates="predictions")
    outcomes = relationship("Outcome", back_populates="prediction", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_pred_status", "status"),
        Index("ix_pred_target_date", "target_date"),
    )


class Claim(Base):
    __tablename__ = "claims"

    id = Column(String(36), primary_key=True, default=_uuid)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user_id = Column(String(120), nullable=False)
    agent_idx = Column(Integer, nullable=False)
    country_code = Column(String(10), nullable=False)
    match_score = Column(Float, nullable=False)

    demographics = Column(JSON, default=dict)
    status = Column(String(20), default="active")

    correction_records = relationship(
        "CorrectionRecord", back_populates="claim", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_claims_user", "user_id"),
        Index("ix_claims_status", "status"),
    )


class CorrectionRecord(Base):
    __tablename__ = "correction_records"

    id = Column(String(36), primary_key=True, default=_uuid)
    claim_id = Column(String(36), ForeignKey("claims.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    question_id = Column(String(80), nullable=False)
    model_stance = Column(Float, nullable=False)
    corrected_stance = Column(Float, nullable=False)
    delta = Column(Float, nullable=False)

    n_region_updated = Column(Integer, default=0)
    trait_deltas = Column(JSON, default=dict)

    consent = Column(Boolean, default=True)

    claim = relationship("Claim", back_populates="correction_records")

    __table_args__ = (
        Index("ix_corr_claim", "claim_id"),
        Index("ix_corr_question", "question_id"),
    )


class ManifoldVersion(Base):
    __tablename__ = "manifold_versions"

    id = Column(String(36), primary_key=True, default=_uuid)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    kind = Column(String(10), nullable=False)  # "frozen" | "living"
    pop_hash = Column(String(64), nullable=False)
    population = Column(Integer, nullable=False)
    seed = Column(Integer, nullable=False)
    country_count = Column(Integer, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)

    agent_snapshots = relationship(
        "AgentSnapshot", back_populates="manifold", cascade="all, delete-orphan")
    holdout_results = relationship(
        "HoldoutResult", back_populates="manifold", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_manifold_kind", "kind"),
    )


class AgentSnapshot(Base):
    __tablename__ = "agent_snapshots"

    id = Column(String(36), primary_key=True, default=_uuid)
    manifold_id = Column(String(36), ForeignKey("manifold_versions.id"), nullable=False)
    agent_idx = Column(Integer, nullable=False)
    country_code = Column(String(10), nullable=False)
    traits = Column(JSON, nullable=False)
    forces = Column(JSON, nullable=False)
    alpha = Column(Float, nullable=False)
    demographics = Column(JSON, default=dict)

    manifold = relationship("ManifoldVersion", back_populates="agent_snapshots")

    __table_args__ = (
        Index("ix_agent_manifold", "manifold_id"),
    )


class HoldoutResult(Base):
    __tablename__ = "holdout_results"

    id = Column(String(36), primary_key=True, default=_uuid)
    manifold_id = Column(String(36), ForeignKey("manifold_versions.id"), nullable=False)
    question_id = Column(String(80), nullable=False)
    yes_pct = Column(Float, nullable=False)
    dominant = Column(String(20), nullable=False)
    conviction = Column(Float, nullable=False)
    tested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    manifold = relationship("ManifoldVersion", back_populates="holdout_results")

    __table_args__ = (
        Index("ix_holdout_manifold", "manifold_id"),
        Index("ix_holdout_question", "question_id"),
    )


class Outcome(Base):
    __tablename__ = "outcomes"

    id = Column(String(36), primary_key=True, default=_uuid)
    prediction_id = Column(String(36), ForeignKey("predictions.id"), nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    actual_yes_pct = Column(Float, nullable=False)
    source = Column(Text, nullable=False)
    source_url = Column(Text, default="")
    error = Column(Float, nullable=False)

    prediction = relationship("Prediction", back_populates="outcomes")

    __table_args__ = (
        Index("ix_outcome_recorded", "recorded_at"),
    )


class ForceOutcome(Base):
    __tablename__ = "force_outcomes"

    id = Column(String(36), primary_key=True, default=_uuid)
    prediction_id = Column(String(36), ForeignKey("predictions.id"), nullable=False)
    dominant_force = Column(String(20), nullable=False)
    force_signature = Column(JSON, nullable=False)
    fragility_at_prediction = Column(Float, nullable=False)
    predicted_yes_pct = Column(Float, nullable=False)
    actual_yes_pct = Column(Float, nullable=True)
    error = Column(Float, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_fo_dominant", "dominant_force"),
        Index("ix_fo_prediction", "prediction_id"),
    )
