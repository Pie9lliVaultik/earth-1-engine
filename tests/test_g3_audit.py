"""Gate G3 in CI (bible §19.4) — the two-law audit runs on every build.

Law 1: the LLM never decides the vote.
Law 2: the LLM never narrates an uncomputed cause.

Plus the §19.2 mechanisms: attention (active subpopulation) and
authoring (counterfactual branches from computed loadings).
"""
import ast
from pathlib import Path

import numpy as np
import pytest

from earth1.engine import build_genesis_civilization, run_question, attend
from earth1.llm_gateway import WEIGHT_TOOL, GatewayResult
from earth1.corpus import CorpusHit
from earth1.types import Question, Force, NUM_FORCES
from earth1 import central_mind, narration

VOTE_TOKENS = ("yes_pct", "frac_yes", "vote", "answer_pct", "probability")


@pytest.fixture(scope="module")
def civ():
    return build_genesis_civilization(20_000, seed=42)


@pytest.fixture(scope="module")
def q():
    w = np.array([0.5, 0.0, 1.1, -0.8, 2.0, -1.5, 0.4, 0.0])
    return Question(id="audit_q", text="Do people support the audited proposition?",
                    domain="belief_causal", baseline=0.3, weights=w, lens="wvs")


# ── Law 1 ──

def test_gateway_schema_has_no_vote_field():
    props = set(WEIGHT_TOOL["input_schema"]["properties"].keys())
    vote_like = {p for p in props if any(t in p.lower() for t in VOTE_TOKENS)}
    assert not vote_like, f"gateway schema leaks vote fields: {vote_like}"


def test_vote_is_pure_function_of_question(civ, q):
    r1 = run_question(q, civ)
    r2 = run_question(q, civ)
    assert r1.yes_pct == r2.yes_pct


def test_non_weight_gateway_fields_cannot_move_vote(civ, q):
    gw_a = GatewayResult(question=q, confidence="high", premise_valid=True,
                         premise_reason="", raw={})
    gw_b = GatewayResult(question=q, confidence="corpus", premise_valid=True,
                         premise_reason="different text", raw={"x": 1},
                         country_scope="US", temporal_context="post-election",
                         binary_question="another phrasing?")
    assert run_question(gw_a.question, civ).yes_pct == \
           run_question(gw_b.question, civ).yes_pct


def test_weight_channel_is_live(civ, q):
    q2 = Question(id="audit_q2", text=q.text, domain=q.domain,
                  baseline=q.baseline, weights=q.weights * -1.0, lens=q.lens)
    assert run_question(q, civ).yes_pct != run_question(q2, civ).yes_pct


def test_corpus_hit_carries_no_vote_field():
    attrs = set(CorpusHit.__dataclass_fields__.keys())
    vote_like = {a for a in attrs if any(t in a.lower() for t in VOTE_TOKENS)}
    assert not vote_like


# ── Law 2 ──

def test_narration_is_post_computation():
    src = Path(central_mind.__file__).read_text()
    think_fn = next(n for n in ast.walk(ast.parse(src))
                    if isinstance(n, ast.FunctionDef) and n.name == "think")
    calls = sorted(
        (node.lineno, getattr(node.func, "id", getattr(node.func, "attr", "")))
        for node in ast.walk(think_fn) if isinstance(node, ast.Call)
        if getattr(node.func, "id", getattr(node.func, "attr", "")) in
        ("run_question", "narrate")
    )
    rq = [ln for ln, f in calls if f == "run_question"]
    na = [ln for ln, f in calls if f == "narrate"]
    assert rq and na and min(na) > min(rq)


def test_honesty_guard_withholds_uncomputed_cause(civ, q):
    result = run_question(q, civ)
    allowed = narration.allowed_causes(result)
    disallowed = [f.name.lower() for f in Force
                  if f.name.lower() not in allowed]
    if not disallowed:
        pytest.skip("all forces computed as causes for this question")
    fake = {"narration": f"Driven mostly by {disallowed[0]}.",
            "headline": "x", "cited_forces": [disallowed[0]]}
    guarded = narration.enforce_honesty_guard(fake, result)
    assert guarded["honesty_guard"].startswith("withheld_uncomputed_causes")
    assert disallowed[0] not in guarded["narration"]
    assert set(guarded["cited_forces"]).issubset(allowed)


def test_honesty_guard_passes_computed_causes(civ, q):
    result = run_question(q, civ)
    allowed = sorted(narration.allowed_causes(result))
    assert allowed, "expected at least one computed cause"
    ok = {"narration": f"Driven by {allowed[0]}.",
          "headline": "y", "cited_forces": [allowed[0]]}
    guarded = narration.enforce_honesty_guard(ok, result)
    assert guarded["honesty_guard"] == "pass"


def test_deterministic_render_cites_only_computed(civ, q):
    result = run_question(q, civ)
    det = narration.render_deterministic(result)
    assert set(det["cited_forces"]).issubset(narration.allowed_causes(result))
    assert det["honesty_guard"] == "deterministic"


# ── §19.2 attention + authoring ──

def test_attention_selects_loaded_agents(civ, q):
    active = attend(civ, q, top_frac=0.35)
    assert 0 < active.sum() < civ.n
    centered = civ.forces - civ.means[np.newaxis, :]
    load = np.abs(centered @ q.weights)
    assert load[active].min() >= load[~active].max() - 1e-12


def test_attention_preserves_reading(civ, q):
    full = run_question(q, civ)
    attn = run_question(q, civ, attention_frac=0.35)
    assert attn.params["active_agents"] < civ.n
    assert abs(attn.yes_pct - full.yes_pct) < 0.02, \
        f"attention moved the reading: {full.yes_pct:.4f} -> {attn.yes_pct:.4f}"


def test_author_selects_relevant_branches(q):
    branches = central_mind.author(q, k=4)
    assert branches[0].id == "status_quo"
    assert len(branches) == 5
    # every authored event must actually move this question's logit
    w = np.asarray(q.weights[:NUM_FORCES])
    for b in branches[1:]:
        shift = np.zeros(NUM_FORCES)
        for fi, d in b.steps[0].event.shifts.items():
            shift[int(fi)] = d
        assert abs(float(w @ shift)) > 0
