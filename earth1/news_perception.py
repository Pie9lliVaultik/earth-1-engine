"""LLM news perception — force events from read news (Phase 5.8).

The evidence trail that leads here: news coverage STATISTICS carry no
decade-scale value-change signal — tone failed its placebo control
(G5 run #6) and theme salience failed its pre-specified pooled test
(data/benchmark/phase57_verdict.md). Meaning must be read, not counted.
vivid-node-forge proved the semantic kernel works (an LLM reading a
story routes its meaning to the right opinions) but did it per-AGENT,
unvalidated, at 26.4pp GOQA. This module does it per-ITEM, through the
validated engine, behind the same controls that killed the cheap
signals:

  one LLM call per news item  ->  force events (country scope, force
  deltas, decay, confidence)  ->  the event log  ->  the engine

Discipline:
  - Perception authors CAUSES only; it never touches stances or agents.
  - Output magnitudes are clipped; low-confidence perceptions dropped.
  - Events are tagged source="perception:llm" — auditable end to end.
  - Validation is external: shuffle/placebo controls and measured event
    reactions score the channel; perception cannot grade itself.
  - No key, no silent fallback: without an LLM key the channel is OFF.
    The deterministic stub exists for pipeline tests ONLY and is never
    a production signal source.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np

from earth1.types import Force, NUM_FORCES

_MAX_DELTA = 0.25          # hard clip on any single perceived force delta
_MIN_CONFIDENCE = 0.3      # perceptions below this are dropped
_DEFAULT_DECAY = 14.0      # days; perception may override within bounds
_DECAY_BOUNDS = (2.0, 90.0)


@dataclass
class NewsItem:
    title: str
    country: str               # ISO2 the coverage concerns
    date: str                  # YYYY-MM-DD
    url: str = ""
    snippet: str = ""


@dataclass
class PerceivedEvent:
    """One news item's causal reading — the LLM's output, validated."""
    item: NewsItem
    force_deltas: Dict[int, float]      # Force.value -> delta
    confidence: float
    decay_half_life: float
    rationale: str = ""
    # ISO2 of the population this news CONCERNS (may differ from the
    # publisher's country — GDELT sourcecountry is the outlet's home),
    # or "GLOBAL". Defaults to the item's country for pre-scope callers.
    scope: str = ""

    def clipped(self) -> "PerceivedEvent":
        deltas = {int(k): float(np.clip(v, -_MAX_DELTA, _MAX_DELTA))
                  for k, v in self.force_deltas.items()
                  if abs(v) > 1e-4 and 0 <= int(k) < NUM_FORCES}
        decay = float(np.clip(self.decay_half_life, *_DECAY_BOUNDS))
        return PerceivedEvent(self.item, deltas, float(self.confidence),
                              decay, self.rationale,
                              self.scope or self.item.country)


PERCEPTION_TOOL = {
    "name": "author_force_event",
    "description": "Translate one news item into force-field deltas.",
    "input_schema": {
        "type": "object",
        "properties": {
            "force_deltas": {
                "type": "object",
                "description": "Force name -> delta in [-0.25, 0.25]. "
                               "Only forces this news plausibly moves.",
                "properties": {f.name.lower(): {"type": "number"}
                               for f in Force},
            },
            "confidence": {"type": "number",
                           "description": "0-1: how clearly this item "
                                          "maps to force changes"},
            "decay_half_life_days": {"type": "number"},
            "concerns": {"type": "string",
                         "description": "ISO2 code of the country this news "
                                        "actually CONCERNS (the population "
                                        "whose forces it moves), 'GLOBAL' "
                                        "for worldwide events, or 'NONE' if "
                                        "it concerns no clear population. "
                                        "May differ from the publisher's "
                                        "country."},
            "rationale": {"type": "string"},
        },
        "required": ["force_deltas", "confidence", "concerns"],
    },
}

PERCEPTION_SYSTEM = """You translate ONE news item into Earth-1 force-field deltas for the country it concerns.

The eight forces: fear (threat/insecurity), desire (aspiration/consumption), economics (material conditions), collective (in-group cohesion/conformity), identity (self-definition/expression), culture (tradition/norms), experience (lived events), temperament (risk mood).

Rules:
- concerns: the country whose POPULATION this news moves — NOT the country whose outlet published it. A Lagos paper covering a US election concerns US (or GLOBAL if it moves everyone). Foreign wire stories with no local impact on any clear population -> NONE.
- Output deltas ONLY for forces this item plausibly moves; magnitudes in [-0.25, 0.25]; typical news is 0.02-0.10, only major national events exceed 0.15.
- confidence reflects how clearly the item maps to forces (routine sports/weather -> low; coups, crashes, landmark rulings -> high).
- decay_half_life_days: how long the reaction persists (celebrity story ~2, policy change ~30-90).
- You author CAUSES in the force field. You never predict opinions."""


def perceive_item(
    item: NewsItem,
    model: str = "claude-haiku-4-5-20251001",
) -> Optional[PerceivedEvent]:
    """The one-call-per-item LLM boundary. Returns None (channel off)
    when no ANTHROPIC_API_KEY is configured — never a silent fallback."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    import anthropic
    client = anthropic.Anthropic()
    text = (f"Country: {item.country}\nDate: {item.date}\n"
            f"Headline: {item.title}\n"
            + (f"Snippet: {item.snippet}" if item.snippet else ""))
    resp = client.messages.create(
        model=model, max_tokens=512,
        system=PERCEPTION_SYSTEM,
        tools=[PERCEPTION_TOOL],
        tool_choice={"type": "tool", "name": "author_force_event"},
        messages=[{"role": "user", "content": text}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "author_force_event":
            return _parse_perception(item, block.input)
    return None


def _parse_perception(item: NewsItem, data: dict) -> Optional[PerceivedEvent]:
    name_to_val = {f.name.lower(): f.value for f in Force}
    deltas = {}
    for name, v in (data.get("force_deltas") or {}).items():
        if name in name_to_val:
            try:
                deltas[name_to_val[name]] = float(v)
            except (TypeError, ValueError):
                continue
    conf = float(data.get("confidence", 0.0))
    decay = float(data.get("decay_half_life_days", _DEFAULT_DECAY))
    scope = str(data.get("concerns", "")).strip().upper()
    if scope == "NONE":
        return None       # concerns no clear population — abstain
    if scope != "GLOBAL" and len(scope) != 2:
        scope = item.country   # malformed -> publisher country fallback
    ev = PerceivedEvent(item, deltas, conf, decay,
                        str(data.get("rationale", "")), scope).clipped()
    if ev.confidence < _MIN_CONFIDENCE or not ev.force_deltas:
        return None
    return ev


def perceive_item_stub(item: NewsItem) -> Optional[PerceivedEvent]:
    """Deterministic keyword stub — pipeline tests ONLY. Tagged as stub
    in the rationale so it can never be mistaken for perception."""
    kw = {
        "war": {Force.FEAR.value: 0.12, Force.COLLECTIVE.value: 0.06},
        "attack": {Force.FEAR.value: 0.10},
        "election": {Force.COLLECTIVE.value: 0.05, Force.IDENTITY.value: 0.04},
        "economy": {Force.ECONOMICS.value: -0.06, Force.FEAR.value: 0.04},
        "crisis": {Force.FEAR.value: 0.08, Force.ECONOMICS.value: -0.05},
        "pandemic": {Force.FEAR.value: 0.15, Force.COLLECTIVE.value: 0.08},
    }
    low = item.title.lower()
    for k, deltas in kw.items():
        if k in low:
            return PerceivedEvent(item, dict(deltas), 0.6, _DEFAULT_DECAY,
                                  rationale="STUB").clipped()
    return None


def events_from_news(
    items: List[NewsItem],
    t: float,
    gain: float = 1.0,
    perceiver=perceive_item,
) -> List:
    """Perceive a batch of items and emit WorldEvents for the event log.

    gain scales all deltas (receiver-config style). Items the perceiver
    declines (None) are skipped — abstention is ledgered by the caller.
    """
    from earth1.event_log import WorldEvent

    force_names = [f.name.lower() for f in Force]
    events = []
    for item in items:
        ev = perceiver(item)
        if ev is None:
            continue
        deltas = {force_names[i]: float(v * gain)
                  for i, v in ev.force_deltas.items()}
        events.append(WorldEvent.create(
            timestamp=t,
            force_deltas=deltas,
            region_pattern=f"{item.country}-*",
            decay_half_life=ev.decay_half_life,
            source=("perception:stub" if ev.rationale == "STUB"
                    else "perception:llm"),
        ))
    return events


# ── question response profiles (temporal coupling, v2) ─────────────────

RESPONSE_TOOL = {
    "name": "author_response_profile",
    "description": "How agreement with a survey question RESPONDS to force rises.",
    "input_schema": {
        "type": "object",
        "properties": {
            "response": {
                "type": "object",
                "description": "Force name -> signed sensitivity in [-1,1]: "
                               "if this force RISES, does agreement rise (+) "
                               "or fall (-)? 0 = no response.",
                "properties": {f.name.lower(): {"type": "number"}
                               for f in Force},
            },
            "rationale": {"type": "string"},
        },
        "required": ["response"],
    },
}

RESPONSE_SYSTEM = """You author the TEMPORAL response profile of one survey question in Earth-1's force framework.

The eight forces: fear (threat/insecurity), desire (aspiration), economics (material conditions), collective (in-group cohesion), identity (self-expression), culture (tradition), experience (lived events), temperament (risk mood).

Question: if a force RISES in a society, does agreement with the survey question rise (+) or fall (-)? This is about SHORT-RUN reaction to events, not cross-country levels — e.g. a fear spike RAISES support for protective institutions (rally effect) even though chronically fearful societies trust less.

Output signed sensitivities in [-1,1] only for forces with a real mechanism; 0 otherwise. You author structure; you never predict opinion values."""


def perceive_question_response(
    question_text: str,
    model: str = "claude-haiku-4-5-20251001",
) -> Optional[np.ndarray]:
    """LLM authors the question's signed force-response profile —
    blind to any outcome data. None when the channel is off (no key)."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    import anthropic
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model, max_tokens=512,
        system=RESPONSE_SYSTEM,
        tools=[RESPONSE_TOOL],
        tool_choice={"type": "tool", "name": "author_response_profile"},
        messages=[{"role": "user", "content": question_text}],
    )
    name_to_val = {f.name.lower(): f.value for f in Force}
    for block in resp.content:
        if block.type == "tool_use" and block.name == "author_response_profile":
            out = np.zeros(NUM_FORCES)
            for name, v in (block.input.get("response") or {}).items():
                if name in name_to_val:
                    try:
                        out[name_to_val[name]] = float(np.clip(float(v), -1, 1))
                    except (TypeError, ValueError):
                        continue
            return out
    return None
