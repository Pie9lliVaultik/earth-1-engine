from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional
import numpy as np


class Force(IntEnum):
    FEAR = 0
    DESIRE = 1
    ECONOMICS = 2
    COLLECTIVE = 3
    IDENTITY = 4
    CULTURE = 5
    EXPERIENCE = 6
    TEMPERAMENT = 7

FORCE_KEYS = list(Force)
FORCE_NAMES = {f: f.name.lower() for f in Force}
NUM_FORCES = len(Force)

PERISHABILITY_HALF_LIFE = {
    Force.FEAR: 14,
    Force.DESIRE: 60,
    Force.ECONOMICS: 400,
    Force.COLLECTIVE: 900,
    Force.TEMPERAMENT: 500,
    Force.EXPERIENCE: 4000,
    Force.IDENTITY: 5000,
    Force.CULTURE: 9000,
}


@dataclass
class Civilization:
    """Struct-of-arrays population + precomputed graph and means."""
    n: int
    seed: int
    # demographics (N,)
    country: np.ndarray       # int index into COUNTRIES
    region: np.ndarray        # int index per country
    age_bucket: np.ndarray    # int 0..4
    age: np.ndarray           # float 0..1
    education: np.ndarray     # int 0=low 1=mid 2=high
    income: np.ndarray        # int 0=low 1=mid 2=high
    urban: np.ndarray         # bool
    # traits (N,)
    openness: np.ndarray
    empathy: np.ndarray
    risk_appetite: np.ndarray
    doubt: np.ndarray
    desire_intensity: np.ndarray
    economic_field: np.ndarray
    culture_offset: np.ndarray
    # Big Five (beyond openness)
    conscientiousness: np.ndarray
    agreeableness: np.ndarray
    extraversion: np.ndarray
    neuroticism: np.ndarray
    # Hofstede-derived per-agent
    power_distance: np.ndarray
    individualism: np.ndarray
    uncertainty_avoidance: np.ndarray
    long_term_orientation: np.ndarray
    # the eight force source terms (N, 8)
    forces: np.ndarray
    # conviction / residual strength (N,)
    alpha: np.ndarray
    # population means per force (8,)
    means: np.ndarray
    # social graph — scipy sparse CSR (N, N)
    adj: object  # scipy.sparse.csr_matrix


@dataclass
class Question:
    id: str
    text: str
    domain: str  # "belief_causal" | "external_substrate"
    baseline: float
    weights: np.ndarray  # (8,) float
    lens: str = ""
    note: str = ""
    # temporal response profile (8,): how agreement RESPONDS to force
    # rises — different physics (and different signs) than the
    # cross-sectional weights. None = no temporal path (legacy behavior).
    response_profile: "Optional[np.ndarray]" = None


@dataclass
class CampAnatomy:
    size: int
    mean_stance: float
    dominant: Force
    contrib: np.ndarray  # (8,)


@dataclass
class RunResult:
    question: Question
    n: int
    yes_pct: float
    frac_yes: float
    regime: str
    distribution_by_layer: List[np.ndarray]
    final_distribution: np.ndarray
    force_anatomy: np.ndarray  # (8,) normalized
    dominant: Force
    conviction: float
    fragility: float
    camps: Dict[str, CampAnatomy]
    params: Dict[str, float]
    abstained: Optional[str] = None
    settled_stances: Optional[np.ndarray] = None
    # census-weighted world read (genesis civs only): corrects the
    # min-per-country floor's small-country overrepresentation
    yes_pct_weighted: Optional[float] = None


@dataclass
class CohortCell:
    key: str
    label: str
    n: int
    yes_pct: float
    dominant: Force


@dataclass
class Branch:
    id: str
    label: str
    yes_pct: float
    dominant: Force
    fragility: float
    contortion: float
    force_anatomy: np.ndarray
