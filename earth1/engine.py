"""The orchestrator — one forward pass, five stages.

  1. Input/population  2. Embedding (traits)  3. Projection + diffusion
  4. Latent read       5. Narration (API layer)
"""
from __future__ import annotations
from typing import Dict, List, Optional
import numpy as np

from earth1.types import (
    Civilization, Question, RunResult, CohortCell, Branch,
    Force, FORCE_KEYS, NUM_FORCES, PERISHABILITY_HALF_LIFE,
)
from earth1.population import generate_population, COUNTRIES, AGE_LABELS
from earth1.forces import project_all
from earth1.diffusion import diffuse
from earth1.decompose import histogram, anatomize
from earth1.questions import SURVEY_MATCHED
from earth1.llm_gateway import estimate, GatewayResult

DEFAULT_EPSILON = 0.18
DEFAULT_LAYERS = 8

_civ_cache: Dict[str, Civilization] = {}


def build_civilization(pop: int = 1_000_000, seed: int = 42) -> Civilization:
    key = f"{pop}:{seed}"
    if key in _civ_cache:
        return _civ_cache[key]
    civ = generate_population(pop, seed)
    _civ_cache[key] = civ
    return civ


def run_question(
    q: Question,
    civ: Civilization,
    epsilon: float = DEFAULT_EPSILON,
    layers: int = DEFAULT_LAYERS,
    field_shift: np.ndarray | None = None,
) -> RunResult:
    params = {"epsilon": epsilon, "layers": layers}

    if q.domain == "external_substrate":
        return RunResult(
            question=q, n=civ.n, yes_pct=0.5, frac_yes=0.5,
            regime="forward-estimate",
            distribution_by_layer=[], final_distribution=np.zeros(20, dtype=int),
            force_anatomy=np.zeros(NUM_FORCES),
            dominant=Force.IDENTITY, conviction=0.0, fragility=0.0,
            camps={"yes": None, "no": None}, params=params,
            abstained="Out of the belief-causal domain — belief is not the cause.",
        )

    s0 = project_all(civ, q, field_shift)
    snaps = diffuse(s0, civ.alpha, civ.adj, epsilon, layers)
    settled = snaps[-1]

    anat = anatomize(civ, settled, q)
    dists = [histogram(s) for s in snaps]

    frac_yes = float((settled >= 0.5).mean())

    return RunResult(
        question=q, n=civ.n,
        yes_pct=float(settled.mean()),
        frac_yes=frac_yes,
        regime="survey-matched" if q.id in SURVEY_MATCHED else "forward-estimate",
        distribution_by_layer=dists,
        final_distribution=dists[-1],
        force_anatomy=anat["force_anatomy"],
        dominant=anat["dominant"],
        conviction=anat["conviction"],
        fragility=anat["fragility"],
        camps=anat["camps"],
        params=params,
    )


def run_segment(
    q: Question,
    civ: Civilization,
    split_by: str,
    epsilon: float = DEFAULT_EPSILON,
    layers: int = DEFAULT_LAYERS,
) -> List[CohortCell]:
    if q.domain == "external_substrate":
        return []

    s0 = project_all(civ, q)
    snaps = diffuse(s0, civ.alpha, civ.adj, epsilon, layers)
    settled = snaps[-1]

    attr_map = {
        "country": civ.country,
        "age_bucket": civ.age_bucket,
        "education": civ.education,
        "income": civ.income,
    }
    label_map = {
        "country": lambda v: COUNTRIES[v]["code"],
        "age_bucket": lambda v: AGE_LABELS[v],
        "education": lambda v: ["low", "mid", "high"][v],
        "income": lambda v: ["low", "mid", "high"][v],
    }

    vals = attr_map[split_by]
    labeler = label_map[split_by]
    unique_vals = np.unique(vals)

    centered = civ.forces - civ.means[np.newaxis, :]
    abs_contrib = np.abs(centered * q.weights[np.newaxis, :])

    cells = []
    for v in unique_vals:
        mask = vals == v
        n = int(mask.sum())
        if n == 0:
            continue
        yes_pct = float(settled[mask].mean())
        c = abs_contrib[mask].sum(axis=0)
        dom = Force(int(np.argmax(c)))
        cells.append(CohortCell(
            key=str(v), label=labeler(v), n=n, yes_pct=yes_pct, dominant=dom,
        ))

    if split_by == "age_bucket":
        order = {l: i for i, l in enumerate(AGE_LABELS)}
        cells.sort(key=lambda c: order.get(c.label, 99))
    else:
        cells.sort(key=lambda c: -c.yes_pct)

    return cells


def run_multiverse(
    q: Question,
    civ: Civilization,
    epsilon: float = DEFAULT_EPSILON,
    layers: int = DEFAULT_LAYERS,
) -> dict:
    present = run_question(q, civ, epsilon, layers)

    branch_defs = [
        {"id": "A", "label": "It happened (shock)",
         "shift": {Force.FEAR: 0.14, Force.ECONOMICS: -0.08, Force.COLLECTIVE: 0.06}},
        {"id": "B", "label": "It didn't (calm holds)",
         "shift": {Force.DESIRE: 0.1, Force.FEAR: -0.08, Force.IDENTITY: 0.05}},
    ]

    branches = []
    for bd in branch_defs:
        shift = np.zeros(NUM_FORCES)
        for f, v in bd["shift"].items():
            shift[f.value] = v
        r = run_question(q, civ, epsilon, layers, field_shift=shift)
        contortion = float(np.linalg.norm(r.force_anatomy - present.force_anatomy))
        branches.append(Branch(
            id=bd["id"], label=bd["label"],
            yes_pct=r.yes_pct, dominant=r.dominant,
            fragility=r.fragility, contortion=contortion,
            force_anatomy=r.force_anatomy,
        ))

    branches.sort(key=lambda b: b.contortion)
    return {"present": present, "branches": branches}


def run_freetext(
    text: str,
    civ: Civilization,
    epsilon: float = DEFAULT_EPSILON,
    layers: int = DEFAULT_LAYERS,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> dict:
    """Full pipeline: free-text → LLM weight estimation → engine forward pass → result.

    Returns dict with 'gateway' (LLM estimation metadata) and 'result' (RunResult).
    If premise is invalid, returns an abstained RunResult with the reason.
    """
    gw = estimate(text, provider=provider, model=model)

    if not gw.premise_valid:
        result = RunResult(
            question=gw.question, n=civ.n, yes_pct=0.5, frac_yes=0.5,
            regime="forward-estimate",
            distribution_by_layer=[], final_distribution=np.zeros(20, dtype=int),
            force_anatomy=np.zeros(NUM_FORCES),
            dominant=Force.IDENTITY, conviction=0.0, fragility=0.0,
            camps={"yes": None, "no": None},
            params={"epsilon": epsilon, "layers": layers},
            abstained=gw.premise_reason,
        )
        return {"gateway": gw, "result": result}

    result = run_question(gw.question, civ, epsilon=epsilon, layers=layers)
    return {"gateway": gw, "result": result}


def civ_breakdown(civ: Civilization) -> List[dict]:
    counts = np.bincount(civ.country, minlength=len(COUNTRIES))
    return [
        {"code": COUNTRIES[i]["code"], "name": COUNTRIES[i]["name"], "n": int(counts[i])}
        for i in np.argsort(-counts)
    ]
