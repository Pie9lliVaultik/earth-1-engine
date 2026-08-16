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
from earth1.genesis import (
    genesis, GENESIS_COUNTRIES, GENESIS_COUNTRY_CODES,
    genesis_country_name, genesis_country_code,
)
from earth1.forces import project_all
from earth1.diffusion import diffuse
from earth1.decompose import histogram, anatomize
from earth1.questions import SURVEY_MATCHED
from earth1.llm_gateway import estimate, GatewayResult

DEFAULT_EPSILON = 0.18
DEFAULT_LAYERS = 8

GENESIS_AGE_LABELS = ["18-29", "30-44", "45-59", "60-74", "75+"]

_civ_cache: Dict[str, Civilization] = {}


def _is_genesis(civ: Civilization) -> bool:
    return int(civ.country.max()) >= len(COUNTRIES)


def build_civilization(pop: int = 1_000_000, seed: int = 42) -> Civilization:
    key = f"{pop}:{seed}"
    if key in _civ_cache:
        return _civ_cache[key]
    civ = generate_population(pop, seed)
    _civ_cache[key] = civ
    return civ


def build_genesis_civilization(
    pop: int = 1_000_000, seed: int = 42, min_per_country: int = 500,
) -> Civilization:
    key = f"genesis:{pop}:{seed}:{min_per_country}"
    if key in _civ_cache:
        return _civ_cache[key]
    civ = genesis(pop, seed, min_per_country)
    _civ_cache[key] = civ
    return civ


def attend(
    civ: Civilization,
    q: Question,
    top_frac: float = 0.35,
) -> np.ndarray:
    """Attention (bible §19.2): select the active subpopulation.

    An agent loads on a question to the degree its centered force profile
    projects onto the question's weight direction — |centered @ weights| is
    its logit displacement from baseline. Agents with negligible displacement
    sit at the baseline stance regardless, so only the loaded top fraction
    needs diffusion. This is how the population can be huge while inference
    stays cheap.
    """
    centered = civ.forces - civ.means[np.newaxis, :]
    load = np.abs(centered @ q.weights)
    if top_frac >= 1.0:
        return np.ones(civ.n, dtype=bool)
    k = max(1, int(civ.n * top_frac))
    thresh = np.partition(load, -k)[-k]
    return load >= thresh


def run_question(
    q: Question,
    civ: Civilization,
    epsilon: float = DEFAULT_EPSILON,
    layers: int = DEFAULT_LAYERS,
    field_shift: np.ndarray | None = None,
    event_log=None,
    t: float = 0.0,
    attention_frac: float | None = None,
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

    # ONE LAW: events ride their own channel (response law); field_shift
    # keeps counterfactual/coupling semantics. Never merged.
    event_shift = None
    if event_log is not None and len(event_log) > 0:
        event_shift = event_log.effective_deltas_vectorized(t, civ)

    s0 = project_all(civ, q, field_shift=field_shift, event_shift=event_shift)
    if attention_frac is not None and attention_frac < 1.0:
        # §19.2: diffuse only the active subpopulation; inert agents hold
        # their projected (baseline-adjacent) stance.
        active = attend(civ, q, attention_frac)
        sub_adj = civ.adj[active][:, active]
        sub_snaps = diffuse(s0[active], civ.alpha[active], sub_adj, epsilon, layers)
        snaps = []
        for s in sub_snaps:
            full = s0.copy()
            full[active] = s
            snaps.append(full)
        params["attention_frac"] = attention_frac
        params["active_agents"] = int(active.sum())
    else:
        snaps = diffuse(s0, civ.alpha, civ.adj, epsilon, layers)
    settled = snaps[-1]

    anat = anatomize(civ, settled, q)
    dists = [histogram(s) for s in snaps]

    frac_yes = float((settled >= 0.5).mean())

    yes_weighted = None
    if _is_genesis(civ):
        from earth1.genesis import census_weights
        yes_weighted = float(np.average(settled, weights=census_weights(civ)))

    return RunResult(
        question=q, n=civ.n,
        yes_pct=float(settled.mean()),
        yes_pct_weighted=yes_weighted,
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
        settled_stances=settled,
    )


def run_segment(
    q: Question,
    civ: Civilization,
    split_by: str,
    epsilon: float = DEFAULT_EPSILON,
    layers: int = DEFAULT_LAYERS,
    event_log=None,
    t: float = 0.0,
) -> List[CohortCell]:
    if q.domain == "external_substrate":
        return []

    event_shift = None
    if event_log is not None and len(event_log) > 0:
        event_shift = event_log.effective_deltas_vectorized(t, civ)
    s0 = project_all(civ, q, event_shift=event_shift)
    snaps = diffuse(s0, civ.alpha, civ.adj, epsilon, layers)
    settled = snaps[-1]

    is_gen = _is_genesis(civ)
    country_list = GENESIS_COUNTRIES if is_gen else COUNTRIES
    age_labels = GENESIS_AGE_LABELS if is_gen else AGE_LABELS
    code_key = "iso2" if is_gen else "code"

    attr_map = {
        "country": civ.country,
        "age_bucket": civ.age_bucket,
        "education": civ.education,
        "income": civ.income,
    }
    label_map = {
        "country": lambda v: country_list[v][code_key],
        "age_bucket": lambda v: age_labels[v],
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
    event_log=None,
    t: float = 0.0,
) -> dict:
    # ONE LAW: the multiverse's present is the LIVING present
    present = run_question(q, civ, epsilon, layers,
                           event_log=event_log, t=t)

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
        r = run_question(q, civ, epsilon, layers, field_shift=shift,
                         event_log=event_log, t=t)
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
    event_log=None,
    t: float = 0.0,
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

    result = run_question(gw.question, civ, epsilon=epsilon, layers=layers,
                          event_log=event_log, t=t)
    return {"gateway": gw, "result": result}


def civ_breakdown(civ: Civilization) -> List[dict]:
    is_gen = _is_genesis(civ)
    country_list = GENESIS_COUNTRIES if is_gen else COUNTRIES
    code_key = "iso2" if is_gen else "code"
    counts = np.bincount(civ.country, minlength=len(country_list))
    return [
        {"code": country_list[i][code_key], "name": country_list[i]["name"], "n": int(counts[i])}
        for i in np.argsort(-counts)
        if i < len(country_list)
    ]
