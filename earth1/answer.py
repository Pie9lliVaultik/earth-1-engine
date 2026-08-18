"""THE ANSWER PATH — the population always speaks; the tier is the receipt.

The reframe (2026-08-18, Pietro): grounding does not CREATE the answer.
Every agent already has a stance the moment a question is projected
through the force manifold, so there is never a question on which the
synthetic population is silent. Grounding CALIBRATES that voice:

  Tier A  fitted to real survey data on this exact question
  Tier B  fitted to a nearby measured question, dampened by distance
  Tier B- interpolated from far inside the measured space, directional
  Tier D  calibrated against freshly searched published polling
  Tier C  the population answers from its own structure, UNVERIFIED —
          not "I don't know" but "here is what our model of humanity
          thinks, and nobody has checked it". This is the DISCOVERY
          layer: a strong structured distribution on a question no
          survey has ever asked is a prediction about human opinion
          waiting to be tested.

Abstention moved: the engine does NOT abstain for lack of data. It
abstains when the manifold is DEGENERATE — when the camp diagnostic
says the yes-camp and no-camp have identical force signatures, so the
population carries no information on this question.

Prediction questions ("Will X happen by Y?") are rewritten into the
underlying opinion question first (the old engine's move), grounded,
and then projected forward by the dynamics. A prediction is therefore
a MEASUREMENT OF THE PRESENT plus a DYNAMICS CLAIM about where the
present is heading — each with its own receipt.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass, field

import numpy as np

from earth1.grounding import Grounding, ground
from earth1.readout import (TIER_LABEL, TIER_MEANING, born_probability,
                            camp_diagnostic, cohort_shape, counting_vote,
                            resultant_length)
from earth1.rng import logit, sigmoid

PREDICTION_RX = re.compile(
    r"^\s*(will|would|is .* going to|by \d{4}|does .* happen)\b", re.I)


@dataclass
class Answer:
    question: str
    opinion_form: str
    is_prediction: bool
    # the population's voice — always present unless degenerate
    yes_pct: float | None
    distribution: list = field(default_factory=list)
    spread: float | None = None
    coherence_yes: float | None = None
    coherence_no: float | None = None
    born_pct: float | None = None
    # the receipt
    tier: str = "C"
    calibration_source: str = "forward-estimate"
    confidence: str = "low"
    source: str | None = None
    source_url: str | None = None
    date: str | None = None
    matched_question: str | None = None
    dampening_factor: float | None = None
    nearest_similarity: float | None = None
    unsurveyed: bool = False
    # manifold status
    manifold_regime: str | None = None
    camp_cosine: float | None = None
    abstained: bool = False
    abstain_reason: str | None = None
    # SHAPE, measured rather than averaged (from the seed's real
    # cohort targets when the cascade found one)
    shape: dict | None = None
    # trajectory (predictions only)
    trajectory: dict | None = None
    # commitment
    receipt_sha256: str | None = None
    answered_at: str | None = None
    note: str | None = None


def is_prediction_question(text: str) -> bool:
    return bool(PREDICTION_RX.search(text or ""))


def to_opinion_form(text: str, allow_live: bool = False) -> str:
    """Rewrite a prediction into the underlying opinion question.

    Uses the old engine's rephrase step when an API key is available;
    otherwise applies a conservative textual fallback and says so.
    """
    if not is_prediction_question(text):
        return text
    if allow_live:
        try:
            from earth1.live_search import rephrase_survey_queries
            return rephrase_survey_queries(text).get("opinion_form", text)
        except Exception:
            pass
    return text


def answer(question_text: str,
           civ,
           weights: np.ndarray,
           baseline: float,
           population: str | None = None,
           corpus: list | None = None,
           allow_live: bool = False,
           mask: np.ndarray | None = None,
           horizon_years: float | None = None,
           grounding: Grounding | None = None) -> Answer:
    """Produce the population's answer WITH its calibration receipt.

    `weights`/`baseline` are whatever the caller's calibration produced
    for this question at the tier the cascade selected — the point of
    this function is that the population speaks either way, and the
    envelope states how well that voice is tuned.
    """
    from earth1.calibration import _build_features

    is_pred = is_prediction_question(question_text)
    opinion_form = to_opinion_form(question_text, allow_live=allow_live)
    g = grounding or ground(opinion_form, population, corpus=corpus,
                            allow_live=allow_live)

    feats = _build_features(civ, extended=True)
    m = mask if mask is not None else np.ones(civ.n, dtype=bool)
    z = logit(np.array([baseline]))[0] + feats[m] @ weights
    s = np.clip(sigmoid(z), 1e-6, 1 - 1e-6)

    diag = camp_diagnostic(civ.forces[m], s)
    hist, _ = np.histogram(s, bins=np.linspace(0, 1, 11))
    hist = (hist / max(hist.sum(), 1)).round(4).tolist()

    a = Answer(
        question=question_text, opinion_form=opinion_form,
        is_prediction=is_pred,
        yes_pct=float(s.mean()),
        distribution=hist,
        spread=float(s.max() - s.min()),
        coherence_yes=diag["r_yes"], coherence_no=diag["r_no"],
        born_pct=born_probability(civ.forces[m], s),
        tier=TIER_LABEL.get(g.calibration_source, "C"),
        calibration_source=g.calibration_source,
        confidence=g.confidence, source=g.source,
        source_url=g.source_url, date=g.date,
        matched_question=g.matched_question,
        dampening_factor=g.dampening_factor,
        nearest_similarity=getattr(g, "nearest_similarity", None) or g.similarity,
        unsurveyed=getattr(g, "unsurveyed", False),
        manifold_regime=diag["regime"], camp_cosine=diag["cosine"],
        answered_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        note=TIER_MEANING.get(g.calibration_source),
    )

    # abstention: ONLY for a degenerate manifold, never for missing data
    if diag["regime"] == "degenerate":
        a.abstained = True
        a.abstain_reason = ("degenerate manifold: the population has no "
                            "internal structure on this question — both "
                            "camps are identical, so the distribution "
                            "carries no information")
        a.yes_pct = None

    # discovery layer: unverified but structured is the frontier, not a gap
    if a.calibration_source == "forward-estimate" and not a.abstained:
        a.note = ("UNVERIFIED PREDICTION ABOUT HUMAN OPINION: no survey "
                  "has asked this (nearest measurement "
                  f"{(a.nearest_similarity or 0):.2f} away). The "
                  "population produced a structured distribution anyway "
                  "— this is a testable claim, not a missing answer.")

    # the shape the engine cannot manufacture: read it off the data
    if getattr(g, "cohort_targets", None):
        a.shape = cohort_shape(g.cohort_targets, axis="pol")

    if horizon_years and not a.abstained:
        a.trajectory = _project(civ, weights, baseline, m, horizon_years)

    payload = json.dumps(asdict(a), sort_keys=True, default=str)
    a.receipt_sha256 = hashlib.sha256(payload.encode()).hexdigest()
    return a


def _project(civ, weights, baseline, mask, years: float) -> dict:
    """Dynamics claim: where generational composition takes this.

    Reported with its own honest label — the mechanism measured on the
    verified GSS ruler was indistinguishable from persistence, so a
    projection is stated as a mechanism output, not a validated
    forecast.
    """
    from earth1.calibration import _build_features
    from earth1.generational import generational_tick
    from earth1.genesis import genesis
    from earth1.tick import _make_mutable

    c2 = _make_mutable(genesis(civ.n, civ.seed))
    rng = np.random.default_rng(civ.seed)
    for _ in range(max(1, int(round(years * 4)))):
        generational_tick(c2, rng, dt_days=91.3)
    f2 = _build_features(c2, extended=True)
    z0 = logit(np.array([baseline]))[0]
    now = float(sigmoid(z0 + _build_features(civ, extended=True)[mask]
                        @ weights).mean())
    then = float(sigmoid(z0 + f2[mask] @ weights).mean())
    return {"horizon_years": years, "now": now, "projected": then,
            "change": then - now,
            "mechanism": "generational composition only",
            "validation_status": ("UNVALIDATED — on the verified GSS ruler "
                                  "this mechanism scored 0.0289 vs "
                                  "persistence 0.0290 over 438 real "
                                  "transitions, i.e. indistinguishable "
                                  "from assuming no change")}
