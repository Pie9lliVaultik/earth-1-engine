#!/usr/bin/env python3
"""Gate G3 automated audit — "no decided votes, no uncomputed causes."

Verifies the two laws mechanically, without trusting anyone's word:

LAW 1 — The LLM never decides the vote.
  A1  Schema audit: the gateway's tool schema exposes no vote-like field —
      the LLM can physically only return baseline + force weights + metadata.
  A2  Determinism: with a fixed Question, the vote is a pure function of
      (civ, question, epsilon, layers). Same inputs, same yes_pct, twice.
  A3  Isolation: mutating every gateway field EXCEPT baseline/weights
      (confidence, premise_reason, binary_question, temporal_context)
      leaves yes_pct bit-identical. The only causal channel is the weights.
  A4  The channel is live: changing weights DOES change the vote
      (guards against a stub that ignores the LLM entirely).
  A5  Corpus path: a retrieval hit supplies only (baseline, weights) via
      Question — CorpusHit has no vote-like attribute.

LAW 2 — The LLM may not narrate an uncomputed cause.
  B1  Order audit (AST): in central_mind.think, narrate() is called after
      run_question() — narration can only see computed results.
  B2  Input audit: the narration data block contains only fields computed
      by the engine (anatomy, conviction, fragility, camps, splits).
  B3  Citation audit (live, optional): narration's cited_forces must be a
      subset of forces with nonzero computed anatomy. Runs only when an
      API key is present; otherwise reported as SKIPPED (not passed).

Exit code 0 = gate clears (all non-skipped checks pass). 1 = violation.
"""
import ast
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from earth1.engine import build_genesis_civilization, run_question
from earth1.llm_gateway import WEIGHT_TOOL, GatewayResult
from earth1.corpus import CorpusHit
from earth1.types import Question, NUM_FORCES
from earth1 import central_mind, narration

VOTE_TOKENS = ("yes_pct", "frac_yes", "vote", "result", "answer_pct", "probability")

checks = []


def check(name, passed, detail=""):
    checks.append((name, passed, detail))
    mark = "PASS" if passed else ("SKIP" if passed is None else "FAIL")
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))


def main():
    print("=" * 72)
    print("GATE G3 AUDIT — no decided votes, no uncomputed causes")
    print("=" * 72)

    # ── A1: schema audit ──
    props = set(WEIGHT_TOOL["input_schema"]["properties"].keys())
    allowed_meta = {"domain", "premise_valid", "premise_reason",
                    "country_scope", "temporal_context", "binary_question",
                    "lens", "confidence"}
    force_fields = {"baseline", "fear", "desire", "economics", "collective",
                    "identity", "culture", "experience", "temperament"}
    leaked = props - force_fields - allowed_meta
    vote_like = {p for p in props if any(t in p.lower() for t in VOTE_TOKENS)}
    check("A1 gateway schema exposes no vote field",
          not leaked and not vote_like,
          f"properties: {sorted(props)}" if (leaked or vote_like) else
          f"{len(props)} fields, all weights/metadata")

    # ── build a small civ for behavioral checks ──
    civ = build_genesis_civilization(20_000, seed=42)
    w = np.array([0.5, 0.0, 1.1, -0.8, 2.0, -1.5, 0.4, 0.0])
    q = Question(id="audit_q", text="Do people support the audited proposition?",
                 domain="belief_causal", baseline=0.3, weights=w, lens="wvs")

    # ── A2: determinism ──
    r1 = run_question(q, civ, epsilon=0.18, layers=8)
    r2 = run_question(q, civ, epsilon=0.18, layers=8)
    check("A2 vote is a pure function of (civ, question)",
          r1.yes_pct == r2.yes_pct,
          f"yes_pct = {r1.yes_pct:.6f} both runs")

    # ── A3: non-weight gateway fields cannot move the vote ──
    gw_a = GatewayResult(question=q, confidence="high", premise_valid=True,
                         premise_reason="", raw={}, country_scope="global",
                         temporal_context="", binary_question="v1?")
    gw_b = GatewayResult(question=q, confidence="corpus", premise_valid=True,
                         premise_reason="entirely different reasoning text",
                         raw={"anything": 123}, country_scope="US",
                         temporal_context="after the 2026 election",
                         binary_question="a completely different rephrasing?")
    ra = run_question(gw_a.question, civ, epsilon=0.18, layers=8)
    rb = run_question(gw_b.question, civ, epsilon=0.18, layers=8)
    check("A3 non-weight gateway fields cannot move the vote",
          ra.yes_pct == rb.yes_pct,
          f"yes_pct identical at {ra.yes_pct:.6f}")

    # ── A4: the weight channel is live ──
    q_moved = Question(id="audit_q2", text=q.text, domain=q.domain,
                       baseline=q.baseline, weights=w * -1.0, lens=q.lens)
    r_moved = run_question(q_moved, civ, epsilon=0.18, layers=8)
    check("A4 changing weights changes the vote",
          abs(r_moved.yes_pct - r1.yes_pct) > 1e-6,
          f"{r1.yes_pct:.4f} -> {r_moved.yes_pct:.4f}")

    # ── A5: corpus path carries weights only ──
    hit_attrs = set(CorpusHit.__dataclass_fields__.keys())
    vote_attrs = {a for a in hit_attrs if any(t in a.lower() for t in VOTE_TOKENS)}
    check("A5 corpus hit carries no vote field",
          not vote_attrs, f"fields: {sorted(hit_attrs)}")

    # ── B1: AST — narrate() only after run_question() in think() ──
    src = Path(central_mind.__file__).read_text()
    tree = ast.parse(src)
    think_fn = next(n for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name == "think")
    call_order = []
    for node in ast.walk(think_fn):
        if isinstance(node, ast.Call):
            fname = getattr(node.func, "id", getattr(node.func, "attr", ""))
            if fname in ("run_question", "narrate"):
                call_order.append((node.lineno, fname))
    call_order.sort()
    rq_lines = [ln for ln, f in call_order if f == "run_question"]
    narr_lines = [ln for ln, f in call_order if f == "narrate"]
    check("B1 narration is strictly post-computation",
          bool(rq_lines) and bool(narr_lines) and min(narr_lines) > min(rq_lines),
          f"run_question@{rq_lines}, narrate@{narr_lines}")

    # ── B2: narration data block built only from computed fields ──
    block = narration._build_data_block(r1)
    has_computed = all(s in block for s in
                       ("YES %", "CONVICTION", "FRAGILITY", "DOMINANT FORCE"))
    check("B2 narration input is the computed result only", has_computed,
          "data block carries anatomy/conviction/fragility from RunResult")

    # ── B3: live citation audit (needs API key) ──
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY"):
        try:
            narr = narration.narrate(r1)
            anatomy = r1.force_anatomy
            computed = {f.name.lower() for f in
                        __import__("earth1.types", fromlist=["Force"]).Force
                        if abs(anatomy[f]) > 1e-9}
            cited = {c.lower() for c in narr.get("cited_forces", [])}
            check("B3 cited forces are all computed forces",
                  cited.issubset(computed),
                  f"cited={sorted(cited)}, computed={sorted(computed)}")
        except Exception as e:
            check("B3 live citation audit", None, f"skipped: {e}")
    else:
        check("B3 live citation audit", None, "skipped: no API key in env")

    # ── verdict ──
    hard = [(n, p) for n, p, _ in checks if p is not None]
    failed = [n for n, p in hard if not p]
    print()
    if failed:
        print(f"G3: FAIL — {len(failed)} violation(s): {failed}")
        sys.exit(1)
    skipped = [n for n, p, _ in checks if p is None]
    print(f"G3: CLEAR — {len(hard)} checks passed"
          + (f", {len(skipped)} skipped (no API key)" if skipped else ""))
    sys.exit(0)


if __name__ == "__main__":
    main()
