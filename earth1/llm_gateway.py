"""LLM Gateway — free-text question to structured force weights.

The LLM sets the weights; the math decides the vote.  (Law 1)
The LLM may not narrate an uncomputed cause.         (Law 2)

Calls Claude via tool_use to produce a structured Question with
baseline, weights[8], domain classification, and premise check.
Falls back to OpenAI if OPENAI_API_KEY is set and Anthropic is not.
"""
from __future__ import annotations

import json
import os
from typing import Optional

import numpy as np

from earth1.types import Question, Force, NUM_FORCES

FORCE_NAMES_LOWER = [f.name.lower() for f in Force]

SYSTEM_PROMPT = """\
You are the weight-estimation layer of Earth-1, a civilization engine that models
8 billion synthetic humans.  You receive a question posed to the world population
and must estimate the force weights that drive opinion on it.

THE EIGHT FORCES (indices 0-7):
  0. fear        — threat salience, loss aversion, panic
  1. desire      — aspiration, want, hope for gain
  2. economics   — material self-interest, cost-benefit
  3. collective  — social conformity, herd pressure, institutions
  4. identity    — who-I-am alignment, moral/religious/political identity
  5. culture     — inherited norms, traditions, cultural memory
  6. experience  — lived experience, personal history, age-accumulated
  7. temperament — personality traits (openness, risk appetite, empathy)

HOW WEIGHTS WORK:
  Each agent's stance = sigmoid(baseline + (agent_forces - population_means) @ weights)
  - baseline: logit-space prior. 0 = 50/50. Positive = lean-yes. Range [-3, 3].
  - weights: signed floats, typically [-4, 4]. Positive = "more of this force → more yes".
    Negative = "more of this force → more no".  Magnitude = strength of influence.

EXAMPLES OF WELL-CALIBRATED QUESTIONS:
  "Do people support same-sex marriage?"
    baseline=0.35, fear=0, desire=0, economics=0, collective=-1.2,
    identity=3.4, culture=-2.2, experience=-1.6, temperament=0
    domain=belief_causal, lens=culture

  "Is your money safe at your bank right now?"
    baseline=2.1, fear=-3.6, desire=0, economics=1.1, collective=2.4,
    identity=0, culture=0, experience=0, temperament=-1.0
    domain=belief_causal, lens=finance

  "Should immigration be more restricted?"
    baseline=-0.1, fear=2.8, desire=0, economics=1.4, collective=0,
    identity=-2.6, culture=1.8, experience=0, temperament=0
    domain=belief_causal, lens=policy

DOMAIN CLASSIFICATION:
  - "belief_causal": opinion is shaped by internal beliefs, values, identity, or social forces.
    Most political, social, cultural, economic questions are belief-causal.
  - "outcome_forecast": the question asks about an EXTERNAL OUTCOME the population
    does not cause but forms collective beliefs/expectations about — elections
    resolving, recessions, wars starting, asteroid impacts, rate decisions.
    The engine reports the CIVILIZATION'S collective probability of the outcome,
    never a claim about physical ground truth. Estimate weights for the belief.
  - "external_substrate": the answer is a factual measurement with no meaningful
    collective-belief layer (arithmetic, a physical constant, tomorrow's exact
    temperature reading). The engine CANNOT answer these.

PREMISE CHECK:
  Before estimating weights, determine if the question is:
  1. belief_causal → estimate weights normally
  2. outcome_forecast → estimate weights normally; the answer is interpreted
     as collective expectation, not truth
  3. external_substrate → set premise_valid=false, explain why belief is not the cause
  4. incoherent/unanswerable → set premise_valid=false, explain

COUNTRY SCOPING:
  The engine models 194 countries — every UN member state plus major
  territories, each identified by its ISO 3166-1 alpha-2 code (US, IT,
  NG, JP, ...).  If the question targets a specific country (e.g. "What
  do Italians think about..."), set country_scope to that ISO2 code.
  If it asks about "the world" or "people" generically, set
  country_scope to "global".

TEMPORAL CONTEXT:
  If the question references a specific event, time period, or condition
  (e.g. "After the 2024 election...", "During COVID..."), extract it as
  temporal_context.  This does NOT change the weights — it is metadata for
  the narration layer.  If no temporal framing, set to empty string.

BINARY REFRAMING:
  The engine needs a yes/no question.  If the input is open-ended
  ("What do people think about X?"), reframe it as a binary:
  "Do people support/approve/favor X?"  Return the reframed version
  in binary_question.  If already binary, return as-is.

YOUR TASK: Given the user's question, call the `estimate_weights` tool with your
best estimates.  Think carefully about which forces ACTUALLY drive opinion, their
directions (positive/negative), and their relative magnitudes.  Most questions are
driven by 2-4 forces — leave the rest at 0.  The baseline reflects the global prior
lean: how would the average person answer if all forces were at the mean?"""

WEIGHT_TOOL = {
    "name": "estimate_weights",
    "description": "Return structured force weight estimates for a question posed to the world population.",
    "input_schema": {
        "type": "object",
        "properties": {
            "baseline": {
                "type": "number",
                "description": "Logit-space prior. 0 = 50/50. Positive = lean-yes. Range [-3, 3].",
            },
            "fear": {"type": "number", "description": "Weight for fear force. Range [-4, 4]."},
            "desire": {"type": "number", "description": "Weight for desire force."},
            "economics": {"type": "number", "description": "Weight for economics force."},
            "collective": {"type": "number", "description": "Weight for collective force."},
            "identity": {"type": "number", "description": "Weight for identity force."},
            "culture": {"type": "number", "description": "Weight for culture force."},
            "experience": {"type": "number", "description": "Weight for experience force."},
            "temperament": {"type": "number", "description": "Weight for temperament force."},
            "domain": {
                "type": "string",
                "enum": ["belief_causal", "outcome_forecast", "external_substrate"],
                "description": "Is this a belief-causal question or external substrate?",
            },
            "premise_valid": {
                "type": "boolean",
                "description": "Can the engine meaningfully answer this? False for external substrate or incoherent questions.",
            },
            "premise_reason": {
                "type": "string",
                "description": "If premise_valid is false, explain why. Empty string if valid.",
            },
            "lens": {
                "type": "string",
                "description": "Short category label: finance, policy, culture, technology, health, etc.",
            },
            "confidence": {
                "type": "string",
                "enum": ["calibrated", "transitional", "forward_estimate"],
                "description": "How close is this to calibrated survey data? Most novel questions are forward_estimate.",
            },
            "country_scope": {
                "type": "string",
                "description": "ISO-2 country code if question targets a specific country (US, GB, DE, BR, NG, IN, JP, MX, FR), or 'global' if not country-specific.",
            },
            "temporal_context": {
                "type": "string",
                "description": "Temporal framing extracted from the question (e.g. 'post-2024 US election', 'during COVID-19 pandemic'). Empty string if none.",
            },
            "binary_question": {
                "type": "string",
                "description": "The question reframed as a yes/no binary. If already binary, return as-is. If open-ended, reframe as 'Do people support/approve/favor X?'",
            },
        },
        "required": [
            "baseline", "fear", "desire", "economics", "collective",
            "identity", "culture", "experience", "temperament",
            "domain", "premise_valid", "premise_reason", "lens", "confidence",
            "country_scope", "temporal_context", "binary_question",
        ],
    },
}

OPENAI_WEIGHT_TOOL = {
    "type": "function",
    "function": {
        "name": WEIGHT_TOOL["name"],
        "description": WEIGHT_TOOL["description"],
        "parameters": WEIGHT_TOOL["input_schema"],
    },
}


class GatewayResult:
    __slots__ = (
        "question", "confidence", "premise_valid", "premise_reason",
        "country_scope", "temporal_context", "binary_question", "raw",
    )

    def __init__(
        self,
        question: Question,
        confidence: str,
        premise_valid: bool,
        premise_reason: str,
        raw: dict,
        country_scope: str = "global",
        temporal_context: str = "",
        binary_question: str = "",
    ):
        self.question = question
        self.confidence = confidence
        self.premise_valid = premise_valid
        self.premise_reason = premise_reason
        self.country_scope = country_scope
        self.temporal_context = temporal_context
        self.binary_question = binary_question
        self.raw = raw


def _parse_tool_input(data: dict, text: str) -> GatewayResult:
    weights = np.array([
        float(data.get("fear", 0)),
        float(data.get("desire", 0)),
        float(data.get("economics", 0)),
        float(data.get("collective", 0)),
        float(data.get("identity", 0)),
        float(data.get("culture", 0)),
        float(data.get("experience", 0)),
        float(data.get("temperament", 0)),
    ], dtype=np.float64)

    domain = data.get("domain", "belief_causal")
    premise_valid = data.get("premise_valid", True)
    premise_reason = data.get("premise_reason", "")

    if not premise_valid:
        weights = np.zeros(NUM_FORCES)

    qid = _slug(text)

    q = Question(
        id=qid,
        text=text,
        domain=domain,
        baseline=float(data.get("baseline", 0)),
        weights=weights,
        lens=data.get("lens", ""),
        note=f"LLM-estimated ({data.get('confidence', 'forward_estimate')})",
    )

    # ONE LAW: a novelty-frontier question gets its temporal response
    # profile authored blind alongside the cross-sectional weights —
    # otherwise it would be event-inert in the living world.
    if premise_valid:
        try:
            from earth1.news_perception import perceive_question_response
            q.response_profile = perceive_question_response(text)
        except Exception:
            q.response_profile = None   # authoring failure = honest inert

    country_scope = data.get("country_scope", "global")
    temporal_context = data.get("temporal_context", "")
    binary_question = data.get("binary_question", text)

    return GatewayResult(
        question=q,
        confidence=data.get("confidence", "forward_estimate"),
        premise_valid=premise_valid,
        premise_reason=premise_reason,
        country_scope=country_scope,
        temporal_context=temporal_context,
        binary_question=binary_question,
        raw=data,
    )


def _slug(text: str) -> str:
    slug = text.lower().strip().rstrip("?").replace(" ", "_")
    slug = "".join(c for c in slug if c.isalnum() or c == "_")
    return slug[:60] or "freetext"


def estimate_anthropic(text: str, model: str = "claude-haiku-4-5-20251001") -> GatewayResult:
    import anthropic
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=[WEIGHT_TOOL],
        tool_choice={"type": "tool", "name": "estimate_weights"},
        messages=[{"role": "user", "content": text}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "estimate_weights":
            return _parse_tool_input(block.input, text)
    raise RuntimeError("LLM did not return tool_use block")


def estimate_openai(text: str, model: str = "gpt-4o") -> GatewayResult:
    import openai
    client = openai.OpenAI()
    resp = client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        tools=[OPENAI_WEIGHT_TOOL],
        tool_choice={"type": "function", "function": {"name": "estimate_weights"}},
    )
    tc = resp.choices[0].message.tool_calls
    if tc and tc[0].function.name == "estimate_weights":
        data = json.loads(tc[0].function.arguments)
        return _parse_tool_input(data, text)
    raise RuntimeError("LLM did not return tool call")


def estimate(
    text: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> GatewayResult:
    """Estimate force weights for a free-text question.

    Provider auto-detected from env: ANTHROPIC_API_KEY → Claude, OPENAI_API_KEY → OpenAI.
    """
    if provider is None:
        if os.environ.get("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        elif os.environ.get("OPENAI_API_KEY"):
            provider = "openai"
        else:
            raise RuntimeError(
                "No LLM API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."
            )

    if provider == "anthropic":
        return estimate_anthropic(text, model=model or "claude-haiku-4-5-20251001")
    elif provider == "openai":
        return estimate_openai(text, model=model or "gpt-4o")
    else:
        raise ValueError(f"Unknown provider: {provider}")
