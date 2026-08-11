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

    run = relationship("Run", back_populates="predictions")
    outcomes = relationship("Outcome", back_populates="prediction", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_pred_status", "status"),
        Index("ix_pred_target_date", "target_date"),
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
