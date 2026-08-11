"""Pydantic response schemas for the API."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class CampSchema(BaseModel):
    size: int
    mean_stance: float
    dominant: str
    contrib: Dict[str, float]


class RunResultSchema(BaseModel):
    question_id: str
    question_text: str
    n: int
    yes_pct: float
    frac_yes: float
    regime: str
    final_distribution: List[int]
    distribution_by_layer: List[List[int]]
    force_anatomy: Dict[str, float]
    dominant: str
    conviction: float
    fragility: float
    camps: Dict[str, Optional[CampSchema]]
    params: Dict[str, float]
    abstained: Optional[str] = None


class CohortCellSchema(BaseModel):
    key: str
    label: str
    n: int
    yes_pct: float
    dominant: str


class BranchSchema(BaseModel):
    id: str
    label: str
    yes_pct: float
    dominant: str
    fragility: float
    contortion: float
    force_anatomy: Dict[str, float]


class MultiverseSchema(BaseModel):
    present: RunResultSchema
    branches: List[BranchSchema]


class CivStatsSchema(BaseModel):
    population: int
    seed: int
    countries: List[Dict[str, Any]]
    edges: int
    mean_degree: float


class DecayCurveSchema(BaseModel):
    months: List[int]
    actual: List[float]
    durable_baseline: List[float]
    half_life_days: int
    dominant: str


class QuestionSchema(BaseModel):
    id: str
    text: str
    domain: str
    lens: str
    note: str


class OrderEffectSchema(BaseModel):
    q1_then_q2: Dict[str, float]
    q2_then_q1: Dict[str, float]
    order_effect_q2: float
    order_effect_q1: float


class CubeAggregateSchema(BaseModel):
    n: int
    yes_pct: float
    num_cells: int


class CalibrationResultSchema(BaseModel):
    id: str
    baseline: float
    weights: Dict[str, float]
    target_pct: float
    achieved_pct: float
    error: float


class FreetextRequest(BaseModel):
    question: str
    epsilon: float = 0.18
    layers: int = 8
    provider: Optional[str] = None
    model: Optional[str] = None


class GatewaySchema(BaseModel):
    premise_valid: bool
    premise_reason: str
    confidence: str
    lens: str
    estimated_weights: Dict[str, float]
    baseline: float


class FreetextResponse(BaseModel):
    gateway: GatewaySchema
    result: RunResultSchema


class HealthSchema(BaseModel):
    status: str
    population: int
    engine: str
