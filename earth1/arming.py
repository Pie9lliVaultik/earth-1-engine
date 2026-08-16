"""Arming the standing record (bible §20.2).

Each live market question flows: perceive → rehearse → pre-commit.
Perception is retrieval-first (§19.1); when neither the corpus nor an
LLM can supply loadings, the reading is an ABSTENTION — ledgered,
counted, displayed, never scored. Every armed reading is timestamped,
hashed, and insert-only. The record cannot be backdated.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

from earth1.types import Civilization, Question, NUM_FORCES
from earth1.corpus import QuestionCorpus
from earth1.markets import LiveMarket, horizon_days
from earth1.multiverse import rehearse_question
from earth1.db import store


@dataclass
class ArmingOutcome:
    market: LiveMarket
    status: str                  # "armed" | "abstained"
    reason: str = ""
    prediction_id: str = ""
    prediction_hash: str = ""
    engine_yes_pct: float = 0.5
    price_at_arming: float = 0.5
    fragility: float = 0.0
    reading_branch: str = ""


def perceive(
    text: str,
    corpus: Optional[QuestionCorpus],
    min_sim: float = 0.85,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> Optional[Question]:
    """Retrieval-first perception for a market question. Returns None when
    no honest loading source exists — the caller must abstain."""
    if corpus is not None:
        hit = corpus.retrieve(text, min_sim=min_sim)
        if hit is not None:
            return hit.to_question(qid=f"market_{abs(hash(text)) % 10**10}")

    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY"):
        from earth1.llm_gateway import estimate
        gw = estimate(text, provider=provider, model=model)
        if gw.premise_valid:
            if corpus is not None:
                corpus.add(
                    id=f"llm_{len(corpus)}", text=gw.binary_question or text,
                    baseline=gw.question.baseline, weights=gw.question.weights,
                    domain=gw.question.domain, lens=gw.question.lens,
                    source="llm",
                )
            return gw.question
        return None
    return None


def arm_market(
    session,
    civ: Civilization,
    market: LiveMarket,
    corpus: Optional[QuestionCorpus] = None,
    k_branches: int = 4,
    attention_frac: Optional[float] = 0.35,
) -> ArmingOutcome:
    """One market through perceive → rehearse → pre-commit."""
    q = perceive(market.question, corpus)

    if q is None:
        # Abstention: ledgered (a Run row), never scored (no Prediction).
        store.save_run(
            session, run_type="armed_abstention",
            question_text=market.question, yes_pct=0.5, frac_yes=0.5,
            dominant="none", confidence_regime="abstained",
            gateway_raw={
                "market_id": market.id, "market_source": market.source,
                "price_at_arming": market.price, "market_url": market.url,
                "reason": "no honest loading source (corpus miss, no LLM)",
            },
        )
        return ArmingOutcome(
            market=market, status="abstained",
            reason="no honest loading source",
            price_at_arming=market.price,
        )

    reh = rehearse_question(q, civ, k=k_branches, attention_frac=attention_frac)
    present = reh.present

    run = store.save_run(
        session, run_type="armed_reading",
        question_text=market.question,
        binary_question=q.text, question_id=q.id,
        yes_pct=present.yes_pct, frac_yes=present.frac_yes,
        dominant=present.dominant.name.lower(),
        conviction=present.conviction, fragility=present.fragility,
        confidence_regime=present.regime,
        force_anatomy={f"f{i}": float(present.force_anatomy[i])
                       for i in range(NUM_FORCES)},
        gateway_raw={
            "market_id": market.id, "market_source": market.source,
            "price_at_arming": market.price, "market_url": market.url,
            "close_time": market.close_time,
            "reading_branch": reh.reading.id,
            "reading_contortion": reh.reading.contortion,
            "branches": [
                {"id": b.id, "yes_pct": b.yes_pct,
                 "contortion": b.contortion,
                 "weight": reh.fragility_weights[b.id]}
                for b in reh.branches
            ],
        },
    )

    pred = store.save_prediction(
        session, run_id=run.id, question_text=market.question,
        predicted_yes_pct=present.yes_pct,
        confidence_regime=present.regime,
        horizon_days=horizon_days(market),
        tags=[market.source, "standing_record",
              "scope:v1-2026-08-16"],
    )
    pred.force_anatomy = {f"f{i}": float(present.force_anatomy[i])
                          for i in range(NUM_FORCES)}
    pred.fragility = present.fragility
    session.commit()

    armed = store.arm_prediction(session, pred.id)

    return ArmingOutcome(
        market=market, status="armed",
        prediction_id=pred.id, prediction_hash=armed.prediction_hash,
        engine_yes_pct=present.yes_pct, price_at_arming=market.price,
        fragility=present.fragility, reading_branch=reh.reading.id,
    )


def arm_all(
    session,
    civ: Civilization,
    markets: List[LiveMarket],
    corpus: Optional[QuestionCorpus] = None,
    k_branches: int = 4,
) -> List[ArmingOutcome]:
    return [arm_market(session, civ, m, corpus=corpus, k_branches=k_branches)
            for m in markets]
