"""Narration layer — post-computation LLM explains "why."

Law 2: The LLM may not narrate an uncomputed cause.

The narration receives ONLY the computed force anatomy, camp structure,
conviction, fragility, and country splits.  It may reference these
numbers but must not invent causes the engine did not compute.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

import numpy as np

from earth1.types import RunResult, CohortCell, Force, FORCE_NAMES

# §19.3: a cause below this normalized-anatomy magnitude was not computed
# to matter — the narration may not assert it. Enforced in code, not prompt.
CAUSE_MIN = 0.05

_ALL_FORCE_NAMES = frozenset(f.name.lower() for f in Force)


def allowed_causes(result: RunResult) -> set:
    """Forces the narration is permitted to cite: |anatomy| >= CAUSE_MIN."""
    return {
        Force(i).name.lower()
        for i in range(len(result.force_anatomy))
        if abs(float(result.force_anatomy[i])) >= CAUSE_MIN
    }


def render_deterministic(result: RunResult) -> dict:
    """Narration as a pure rendering of the decomposition (§19.3 fallback).

    No LLM, no invention possible: causes are the computed anatomy values
    at or above CAUSE_MIN, sorted by magnitude. Used when the LLM narration
    violates the honesty guard, or when no LLM is available.
    """
    anatomy = result.force_anatomy
    causes = sorted(
        ((Force(i).name.lower(), float(anatomy[i]))
         for i in range(len(anatomy))
         if abs(float(anatomy[i])) >= CAUSE_MIN),
        key=lambda kv: -abs(kv[1]),
    )
    cause_txt = ", ".join(f"{n} ({v:+.2f})" for n, v in causes) or "no single force"
    narration = (
        f"The population answers {result.yes_pct:.0%} yes "
        f"(conviction {result.conviction:.2f}, fragility {result.fragility:.2f}). "
        f"Computed drivers: {cause_txt}."
    )
    return {
        "narration": narration,
        "headline": f"{result.yes_pct:.0%} yes — {result.dominant.name.lower()} driven",
        "cited_forces": [n for n, _ in causes],
        "honesty_guard": "deterministic",
    }


def enforce_honesty_guard(narr: dict, result: RunResult) -> dict:
    """Law 2, mechanically: every cited or mentioned force must be a
    computed cause. A violation withholds the LLM text entirely and
    falls back to the deterministic rendering — no cause, not said."""
    allowed = allowed_causes(result)
    cited = {str(c).lower() for c in narr.get("cited_forces", [])}
    text = (str(narr.get("narration", "")) + " " + str(narr.get("headline", ""))).lower()
    mentioned = {n for n in _ALL_FORCE_NAMES if n in text}
    violations = (cited | mentioned) - allowed
    if violations:
        guarded = render_deterministic(result)
        guarded["honesty_guard"] = f"withheld_uncomputed_causes:{sorted(violations)}"
        return guarded
    narr["honesty_guard"] = "pass"
    return narr


NARRATION_PROMPT = """\
You are the narration layer of Earth-1, a civilization engine.
You have been given the COMPUTED results of a population simulation.
Your job is to explain WHY the result came out the way it did.

LAW 2 — ABSOLUTE CONSTRAINT:
  You may ONLY cite causes that appear in the computed data below.
  You may NOT invent, speculate, or add causes the engine did not compute.
  Every claim must reference a specific number from the data.

Write 2-4 sentences.  Be specific.  Use the force names and numbers.
Start with the headline result, then explain the dominant forces, then
note any interesting splits (country, camp).

Write for a smart journalist — no jargon, no hedging, no filler."""


NARRATION_TOOL = {
    "name": "narrate",
    "description": "Return the narration for a computed simulation result.",
    "input_schema": {
        "type": "object",
        "properties": {
            "narration": {
                "type": "string",
                "description": "2-4 sentence explanation of why the result is what it is, citing only computed forces and numbers.",
            },
            "headline": {
                "type": "string",
                "description": "One-line summary suitable for a dashboard card (under 80 chars).",
            },
            "cited_forces": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of force names actually cited in the narration.",
            },
        },
        "required": ["narration", "headline", "cited_forces"],
    },
}

OPENAI_NARRATION_TOOL = {
    "type": "function",
    "function": {
        "name": NARRATION_TOOL["name"],
        "description": NARRATION_TOOL["description"],
        "parameters": NARRATION_TOOL["input_schema"],
    },
}


def _build_data_block(
    result: RunResult,
    country_splits: Optional[List[CohortCell]] = None,
    temporal_context: str = "",
) -> str:
    lines = [
        f"QUESTION: {result.question.text}",
        f"YES %: {result.yes_pct:.1%}  (fraction above 0.5: {result.frac_yes:.1%})",
        f"CONVICTION: {result.conviction:.3f}  FRAGILITY: {result.fragility:.3f}",
        f"DOMINANT FORCE: {result.dominant.name.lower()}",
        "",
        "FORCE ANATOMY (normalized contribution to the result):",
    ]
    for f in Force:
        lines.append(f"  {f.name.lower():12s}: {result.force_anatomy[f.value]:.3f}")

    if result.camps.get("yes") and result.camps.get("no"):
        yes_camp = result.camps["yes"]
        no_camp = result.camps["no"]
        lines.extend([
            "",
            f"YES CAMP: {yes_camp.size:,} agents, mean stance {yes_camp.mean_stance:.3f}, "
            f"led by {yes_camp.dominant.name.lower()}",
            f"NO CAMP:  {no_camp.size:,} agents, mean stance {no_camp.mean_stance:.3f}, "
            f"led by {no_camp.dominant.name.lower()}",
        ])

    if country_splits:
        lines.append("")
        lines.append("COUNTRY SPLITS:")
        for cell in sorted(country_splits, key=lambda c: -c.yes_pct):
            lines.append(f"  {cell.label:4s}: {cell.yes_pct:.1%} ({cell.n:,} agents, led by {cell.dominant.name.lower()})")

    if temporal_context:
        lines.extend(["", f"TEMPORAL CONTEXT: {temporal_context}"])

    return "\n".join(lines)


def narrate_anthropic(
    result: RunResult,
    country_splits: Optional[List[CohortCell]] = None,
    temporal_context: str = "",
    model: str = "claude-haiku-4-5-20251001",
) -> dict:
    import anthropic
    client = anthropic.Anthropic()

    data_block = _build_data_block(result, country_splits, temporal_context)

    resp = client.messages.create(
        model=model,
        max_tokens=512,
        system=NARRATION_PROMPT,
        tools=[NARRATION_TOOL],
        tool_choice={"type": "tool", "name": "narrate"},
        messages=[{"role": "user", "content": data_block}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "narrate":
            return block.input
    raise RuntimeError("Narration LLM did not return tool_use block")


def narrate_openai(
    result: RunResult,
    country_splits: Optional[List[CohortCell]] = None,
    temporal_context: str = "",
    model: str = "gpt-4o",
) -> dict:
    import openai
    client = openai.OpenAI()

    data_block = _build_data_block(result, country_splits, temporal_context)

    resp = client.chat.completions.create(
        model=model,
        max_tokens=512,
        messages=[
            {"role": "system", "content": NARRATION_PROMPT},
            {"role": "user", "content": data_block},
        ],
        tools=[OPENAI_NARRATION_TOOL],
        tool_choice={"type": "function", "function": {"name": "narrate"}},
    )
    tc = resp.choices[0].message.tool_calls
    if tc and tc[0].function.name == "narrate":
        return json.loads(tc[0].function.arguments)
    raise RuntimeError("Narration LLM did not return tool call")


def narrate(
    result: RunResult,
    country_splits: Optional[List[CohortCell]] = None,
    temporal_context: str = "",
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> dict:
    if provider is None:
        if os.environ.get("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        elif os.environ.get("OPENAI_API_KEY"):
            provider = "openai"
        else:
            # No LLM: narration is still available as a pure rendering
            # of the decomposition (§19.3).
            return render_deterministic(result)

    if provider == "anthropic":
        narr = narrate_anthropic(
            result, country_splits, temporal_context,
            model=model or "claude-haiku-4-5-20251001",
        )
    elif provider == "openai":
        narr = narrate_openai(
            result, country_splits, temporal_context,
            model=model or "gpt-4o",
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")

    return enforce_honesty_guard(narr, result)
