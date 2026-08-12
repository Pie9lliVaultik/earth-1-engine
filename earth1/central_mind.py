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
from earth1.engine import run_question, run_segment
from earth1.confidence import ConfidenceScore, score_confidence
from earth1.narration import narrate
from earth1.population import COUNTRY_CODES


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
                country_scope="global",
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

    result = run_question(gw.question, civ, epsilon=epsilon, layers=layers)

    country_splits = None
    scope = gw.country_scope
    if scope and scope != "global" and scope.upper() in COUNTRY_CODES:
        country_splits = run_segment(gw.question, civ, "country", epsilon=epsilon, layers=layers)
    else:
        country_splits = run_segment(gw.question, civ, "country", epsilon=epsilon, layers=layers)

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
