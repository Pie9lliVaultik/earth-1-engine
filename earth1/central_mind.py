"""Central Mind — G3 orchestrator (bible §19).

Chains four stages:
  1. Gateway   — free-text → structured Question + scope/context
  2. Engine    — forward pass (projection + diffusion)
  3. Confidence — algorithmic similarity scoring
  4. Narration  — post-computation LLM "why" (Law 2)

Returns a MindResult that bundles everything the API needs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from earth1.types import Civilization, RunResult, CohortCell, Force, NUM_FORCES
from earth1.llm_gateway import GatewayResult, estimate
from earth1.corpus import QuestionCorpus
from earth1.scenarios import EVENT_CATALOG, Event, ScenarioBranch, BranchStep
from earth1.engine import run_question, run_segment
from earth1.confidence import ConfidenceScore, score_confidence
from earth1.narration import narrate
from earth1.population import COUNTRY_CODES

# demonym -> ISO2 for cheap LLM-free scope extraction (corpus-hit path).
# Country NAMES are matched from GENESIS_COUNTRY_NAMES; this map covers
# the demonym forms questions actually use ("Italians", "the French").
_DEMONYMS = {
    "american": "US", "italian": "IT", "german": "DE", "french": "FR",
    "british": "GB", "spanish": "ES", "portuguese": "PT", "dutch": "NL",
    "brazilian": "BR", "mexican": "MX", "argentine": "AR",
    "argentinian": "AR", "chilean": "CL", "colombian": "CO",
    "peruvian": "PE", "indian": "IN", "chinese": "CN", "japanese": "JP",
    "korean": "KR", "russian": "RU", "ukrainian": "UA", "polish": "PL",
    "turkish": "TR", "egyptian": "EG", "nigerian": "NG", "kenyan": "KE",
    "ghanaian": "GH", "moroccan": "MA", "tunisian": "TN",
    "indonesian": "ID", "filipino": "PH", "thai": "TH", "malaysian": "MY",
    "vietnamese": "VN", "pakistani": "PK", "bangladeshi": "BD",
    "iranian": "IR", "iraqi": "IQ", "israeli": "IL", "saudi": "SA",
    "australian": "AU", "canadian": "CA", "swedish": "SE",
    "norwegian": "NO", "danish": "DK", "finnish": "FI", "greek": "GR",
    "romanian": "RO", "austrian": "AT", "swiss": "CH", "belgian": "BE",
}


def _extract_scope(text: str) -> str:
    """LLM-free country-scope extraction from question text: demonyms
    first, then country names. Returns ISO2 or 'global'."""
    from earth1.genesis import GENESIS_COUNTRY_NAMES
    low = text.lower()
    for demonym, iso2 in _DEMONYMS.items():
        if demonym in low:
            return iso2
    for iso2, name in GENESIS_COUNTRY_NAMES.items():
        if name.lower() in low:
            return iso2
    return "global"


@dataclass
class MindResult:
    question_text: str
    binary_question: str
    country_scope: str
    temporal_context: str
    gateway: GatewayResult
    result: RunResult
    confidence: ConfidenceScore
    narration: Optional[dict]
    country_splits: Optional[List[CohortCell]]
    abstained: bool


def author(
    question: Question,
    k: int = 4,
    day: int = 7,
    catalog: Optional[Dict[str, Event]] = None,
) -> List[ScenarioBranch]:
    """Authoring (bible §19.2): the mind authors counterfactual branches
    for the multiverse (§13).

    An event is relevant to a question to the degree its force shifts move
    the question's logit — |weights · shifts|. The top-k relevant events
    each become a branch beside the status quo. Deterministic: the catalog
    and the computed loadings choose the futures, not an LLM.
    """
    cat = catalog or EVENT_CATALOG
    w = np.asarray(question.weights[:NUM_FORCES])

    scored = []
    for e in cat.values():
        shift = np.zeros(NUM_FORCES)
        for fi, d in e.shifts.items():
            shift[int(fi)] = d
        relevance = abs(float(w @ shift))
        if relevance > 0:
            scored.append((relevance, e))
    scored.sort(key=lambda t: -t[0])

    branches = [ScenarioBranch(id="status_quo", label="Status quo", steps=[])]
    for _, e in scored[:k]:
        branches.append(ScenarioBranch(
            id=e.id, label=e.label, steps=[BranchStep(day=day, event=e)],
        ))
    return branches


def think(
    text: str,
    civ: Civilization,
    epsilon: float = 0.18,
    layers: int = 8,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    skip_narration: bool = False,
    corpus: Optional["QuestionCorpus"] = None,
    corpus_min_sim: float = 0.85,
    attention_frac: Optional[float] = None,
) -> MindResult:
    # Perception is retrieval-first (bible §19.1): a near-neighbour in the
    # corpus supplies the solved loadings and no LLM call happens. The LLM
    # fires only at the novelty frontier.
    gw = None
    if corpus is not None:
        hit = corpus.retrieve(text, min_sim=corpus_min_sim)
        if hit is not None:
            gw = GatewayResult(
                question=hit.to_question(),
                confidence="corpus",
                premise_valid=True,
                premise_reason="",
                raw={"source": "corpus", "corpus_id": hit.id,
                     "similarity": hit.similarity},
                # scope belongs to the CURRENT text, not the corpus entry —
                # a corpus hit must not silently discard "What do Italians..."
                country_scope=_extract_scope(text),
                temporal_context="",
                binary_question=hit.text,
            )
    if gw is None:
        gw = estimate(text, provider=provider, model=model)
        # Every LLM solve grows the corpus, so the LLM footprint shrinks
        # over time (§19.1). Only valid-premise solves are worth keeping.
        if corpus is not None and gw.premise_valid:
            corpus.add(
                id=f"llm_{len(corpus)}", text=gw.binary_question or text,
                baseline=gw.question.baseline, weights=gw.question.weights,
                domain=gw.question.domain, lens=gw.question.lens, source="llm",
            )

    if not gw.premise_valid:
        empty_result = RunResult(
            question=gw.question, n=civ.n, yes_pct=0.5, frac_yes=0.5,
            regime="forward-estimate",
            distribution_by_layer=[], final_distribution=np.zeros(20, dtype=int),
            force_anatomy=np.zeros(NUM_FORCES),
            dominant=Force.IDENTITY, conviction=0.0, fragility=0.0,
            camps={"yes": None, "no": None},
            params={"epsilon": epsilon, "layers": layers},
            abstained=gw.premise_reason,
        )
        empty_conf = ConfidenceScore(
            regime="forward_estimate", similarity=0.0,
            nearest_id="", nearest_text="",
            weight_cosine=0.0, keyword_overlap=0.0,
        )
        return MindResult(
            question_text=text,
            binary_question=gw.binary_question or text,
            country_scope=gw.country_scope,
            temporal_context=gw.temporal_context,
            gateway=gw,
            result=empty_result,
            confidence=empty_conf,
            narration=None,
            country_splits=None,
            abstained=True,
        )

    result = run_question(gw.question, civ, epsilon=epsilon, layers=layers,
                          attention_frac=attention_frac)
    country_splits = run_segment(gw.question, civ, "country",
                                 epsilon=epsilon, layers=layers)

    # Scope the headline: a question about Italians is answered BY the
    # Italian cohort, not by the planet with an Italian footnote. The
    # settled stances already exist for every agent; re-read them under
    # the scope mask. Force anatomy/camps stay population-wide (noted in
    # params) — scoping those needs a sub-civilization, a later step.
    scope = (gw.country_scope or "global").upper()
    if scope != "GLOBAL" and result.settled_stances is not None:
        from earth1.genesis import GENESIS_COUNTRY_CODES
        if scope in GENESIS_COUNTRY_CODES:
            mask = civ.country == GENESIS_COUNTRY_CODES.index(scope)
            if mask.sum() >= 30:
                stances = result.settled_stances[mask]
                result.yes_pct = float(stances.mean())
                result.frac_yes = float((stances > 0.5).mean())
                result.params["country_scope"] = scope
                result.params["scope_n"] = int(mask.sum())
    elif result.yes_pct_weighted is not None:
        # global questions get the census-weighted world read: the
        # min-per-country floor overrepresents small countries (at 100k
        # agents India is 11.2% of agents vs 17.9% of humanity), so the
        # raw agent mean is not what "the world" thinks
        result.params["yes_pct_unweighted"] = result.yes_pct
        result.yes_pct = result.yes_pct_weighted

    conf = score_confidence(gw.question)

    narr = None
    if not skip_narration:
        try:
            narr = narrate(
                result,
                country_splits=country_splits,
                temporal_context=gw.temporal_context,
                provider=provider,
                model=model,
            )
        except Exception:
            narr = None

    return MindResult(
        question_text=text,
        binary_question=gw.binary_question or text,
        country_scope=gw.country_scope,
        temporal_context=gw.temporal_context,
        gateway=gw,
        result=result,
        confidence=conf,
        narration=narr,
        country_splits=country_splits,
        abstained=False,
    )
