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


class ConfidenceSchema(BaseModel):
    regime: str
    similarity: float
    nearest_id: str
    nearest_text: str
    weight_cosine: float
    keyword_overlap: float


class NarrationSchema(BaseModel):
    narration: str
    headline: str
    cited_forces: List[str]


class MindRequest(BaseModel):
    question: str
    epsilon: float = 0.18
    layers: int = 8
    provider: Optional[str] = None
    model: Optional[str] = None
    skip_narration: bool = False


class MindResponse(BaseModel):
    question_text: str
    binary_question: str
    country_scope: str
    temporal_context: str
    gateway: GatewaySchema
    result: RunResultSchema
    confidence: ConfidenceSchema
    narration: Optional[NarrationSchema] = None
    country_splits: Optional[List[CohortCellSchema]] = None
    abstained: bool


class ShockSchema(BaseModel):
    day: int
    label: str
    shifts: Dict[str, float]


class TimePointSchema(BaseModel):
    day: int
    yes_pct: float
    frac_yes: float
    dominant: str
    force_anatomy: Dict[str, float]
    conviction: float
    fragility: float
    effective_weights: Dict[str, float]
    active_shocks: List[str]


class TimelineSchema(BaseModel):
    question_id: str
    question_text: str
    duration_days: int
    step_days: int
    time_points: List[TimePointSchema]
    shocks: List[ShockSchema]
    weight_trajectories: Dict[str, List[float]]
    dominant_transitions: List[Dict[str, Any]]


class TimelineRequest(BaseModel):
    question_id: str
    duration_days: int = 720
    step_days: int = 30
    epsilon: float = 0.18
    layers: int = 8
    shocks: Optional[List[ShockSchema]] = None


class ScenarioRequest(BaseModel):
    question_id: str
    duration_days: int = 720
    step_days: int = 30
    epsilon: float = 0.18
    layers: int = 8
    scenarios: List[Dict[str, Any]]


class EventSchema(BaseModel):
    id: str
    label: str
    shifts: Dict[str, float]
    tags: List[str]


class BranchStepSchema(BaseModel):
    day: int
    event_id: str


class ScenarioBranchInput(BaseModel):
    id: str
    label: str
    steps: List[BranchStepSchema]


class TreeRequest(BaseModel):
    question_id: str
    branches: List[ScenarioBranchInput]
    duration_days: int = 720
    step_days: int = 30
    epsilon: float = 0.18
    layers: int = 8
    include_baseline: bool = True


class TreeAnalysisSchema(BaseModel):
    max_divergence: float
    max_divergence_day: int
    max_divergence_pair: List[str]
    converges: bool
    convergence_day: Optional[int]
    branch_rankings: List[Dict[str, Any]]


class ScenarioTreeSchema(BaseModel):
    question_id: str
    question_text: str
    branches: Dict[str, Any]
    timelines: Dict[str, TimelineSchema]
    analysis: TreeAnalysisSchema


class EvolveRequest(BaseModel):
    years: int = 10
    seed: Optional[int] = None
    question_id: Optional[str] = None


class EvolveStatsSchema(BaseModel):
    year: int
    deaths: int
    births: int
    migrants: int
    pop_by_country: Dict[str, int]
    mean_age: float
    mean_openness: float
    mean_education: float
    urbanization_rate: float


class OpinionDriftPoint(BaseModel):
    year: int
    yes_pct: float
    dominant: str
    conviction: float
    fragility: float


class EvolveResponse(BaseModel):
    years_evolved: int
    stats: List[EvolveStatsSchema]
    opinion_drift: Optional[List[OpinionDriftPoint]] = None


class HealthSchema(BaseModel):
    status: str
    population: int
    engine: str
