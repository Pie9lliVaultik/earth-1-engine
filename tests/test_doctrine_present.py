"""The no-dead-end-results doctrine must exist, in every required place.

Founder instruction, 2026-08-19: put it in three places "so it cannot
quietly disappear" — CLAUDE.md as an execution rule, BIBLE.md as
scientific operating doctrine, and every benchmark plan as the required
miss-resolution protocol.

Three copies cannot be maintained by intention alone; that is precisely
the defect class this repository keeps rediscovering (a hand-maintained
list nobody is forced to look at). So the copies are checked here, and
deleting or weakening one fails CI.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

CANONICAL = ROOT / "BIBLE.md"
EXECUTION_RULE = ROOT / "CLAUDE.md"
BENCHMARK_PLANS = [
    ROOT / "EXPERIMENT_PLAN.md",
    ROOT / "POST_FREEZE_PROGRAM.md",
    ROOT / "EARTH1_MASTER_PLAN.md",
]

# The sentence the founder asked to be impossible to misinterpret.
THE_SENTENCE = 'Do not stop at "the model failed." Your job starts there.'

WORKFLOW_STAGES = ["MISS", "VERIFY", "DIAGNOSE", "RESEARCH", "IMPLEMENT",
                   "CALIBRATE", "ABLATE", "RETEST", "PASS", "FREEZE"]

# The load-bearing clause of each of the ten numbered obligations.
TEN_POINTS = [
    "Never hide, soften, delete, or rewrite a bad result",
    "Verify the instrument first",
    "Explain causally why",
    "Research before inventing",
    "Do not",                      # ...assume where established research exists
    "smallest defensible correction",
    "sensitivity",
    "TRAIN/DEV",
    "Never tune on the final holdout",
    "untouched external holdout",
]


def _text(p):
    """Whitespace-normalised text.

    The doctrine is hard-wrapped differently in each document, so a raw
    substring search would fail on line breaks rather than on missing
    content. Normalising means this test checks what the doctrine SAYS,
    not how it happens to be wrapped.
    """
    assert p.exists(), f"{p.name} is missing entirely"
    return re.sub(r"\s+", " ", p.read_text())


@pytest.mark.parametrize("path", [CANONICAL, EXECUTION_RULE] + BENCHMARK_PLANS,
                         ids=lambda p: p.name)
def test_doctrine_is_present(path):
    """Every required document carries the doctrine."""
    t = _text(path)
    assert THE_SENTENCE in t, (
        f"{path.name} has lost the sentence that must be impossible to "
        f"misinterpret: {THE_SENTENCE!r}")


@pytest.mark.parametrize("path", [CANONICAL, EXECUTION_RULE] + BENCHMARK_PLANS,
                         ids=lambda p: p.name)
def test_workflow_is_stated_in_order(path):
    """MISS -> ... -> FREEZE, complete and in sequence."""
    t = _text(path)
    # BIBLE.md legitimately contains an older nine-step workflow too
    # (the v4.1 miss protocol), so match the CANONICAL ten-stage block
    # specifically rather than the first thing starting with MISS.
    blocks = re.findall(r"MISS →[^|]*?FREEZE", t)
    assert blocks, f"{path.name} does not state the workflow as a sequence"
    canonical = [b for b in blocks
                 if all(s in b for s in WORKFLOW_STAGES)]
    assert canonical, (
        f"{path.name} has no block containing all ten stages; "
        f"found {len(blocks)} partial workflow(s)")
    seq = canonical[0]
    idx = [seq.find(s) for s in WORKFLOW_STAGES]
    assert idx == sorted(idx), f"{path.name} states the workflow out of order"


@pytest.mark.parametrize("path", [CANONICAL, EXECUTION_RULE],
                         ids=lambda p: p.name)
def test_all_ten_obligations_survive(path):
    """None of the ten numbered points may be quietly dropped."""
    t = _text(path)
    missing = [i + 1 for i, clause in enumerate(TEN_POINTS)
               if clause not in t]
    assert not missing, f"{path.name} lost obligation(s) {missing}"


def test_canonical_declares_itself_canonical():
    """Three copies need a tie-breaker, or drift becomes an argument."""
    t = _text(CANONICAL)
    assert "PART XI.A" in t
    assert "canonical" in t.lower()


def test_execution_rule_points_at_the_canonical_copy():
    t = _text(EXECUTION_RULE)
    assert "BIBLE.md" in t and "canonical" in t.lower()


@pytest.mark.parametrize("path", BENCHMARK_PLANS, ids=lambda p: p.name)
def test_benchmark_plans_bind_their_thresholds_to_the_protocol(path):
    """A tier in a plan must say what happens when it is missed."""
    t = _text(path)
    assert "MISS-RESOLUTION PROTOCOL" in t
    assert "XI.A" in t, f"{path.name} does not cite the canonical doctrine"


def test_the_terminal_exception_is_stated_everywhere():
    """The one legitimate way to stop must not be lost either.

    Without it the doctrine reads as 'never accept a negative result',
    which would license exactly the dishonesty it exists to prevent.
    """
    for p in [CANONICAL, EXECUTION_RULE] + BENCHMARK_PLANS:
        t = _text(p)
        assert "hypothesis" in t and "false" in t, (
            f"{p.name} has lost the terminal exception — the doctrine "
            f"must never read as 'manufacture a pass'")
