"""Founder ruling 2026-09-08: emergence experiment — ruling 3, first
step (external review M07a): binary readout SEMANTICS.

The 2-outcome readout d_NO/(d_YES+d_NO) is served under its honest name
— a normalized branch-displacement ratio (branch consistency), not a
calibrated event probability. This suite pins the three guarantees of
that step:

  1. the binary answer payload carries the additive `semantics` /
     `semantics_note` fields next to p_model;
  2. every computed value is byte-identical to the pre-change serving —
     verbatim pass-through at the stub level, and an end-to-end p_model
     against an expectation CAPTURED PRE-CHANGE (2026-09-08, fresh
     scrubbed process, so the frozen-env shell cannot skew it);
  3. ops/alive/SEMANTICS_BINARY_READOUT.md exists and names the three
     ruling options (KEEP+relabel / CALIBRATE / REDESIGN).

Like test_review_multiverse.py, stub tests redirect the module _ROOT to
a temp dir so no request-time write (uncalibrated_questions.jsonl,
class overlay) can touch the repo's committed data files.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from earth1.adapters import multiverse as mv  # noqa: E402

SEM_DOC = ROOT / "ops" / "alive" / "SEMANTICS_BINARY_READOUT.md"
EXPECTED_NOTE = ("normalized branch-displacement ratio; not a calibrated "
                 "event probability (see SEMANTICS_BINARY_READOUT.md)")


@pytest.fixture
def qc_env(tmp_path):
    """Temp _ROOT with a copy of the registered registry (cache cleared
    both ways) — request-time appends land in tmp, never in the repo."""
    os.makedirs(tmp_path / "data")
    shutil.copy(ROOT / "data" / "question_classes.json",
                tmp_path / "data" / "question_classes.json")
    saved_root = mv._ROOT
    mv._ROOT, mv._CLASSES = str(tmp_path), None
    yield str(tmp_path)
    mv._ROOT, mv._CLASSES = saved_root, None


def _binary_verdict(**over):
    base = dict(
        question_class="market_cascade", abstain=False,
        p_model=0.30199999999999999,
        p_by_outcome={"YES": 0.30199999999999999, "NO": 0.698},
        abstain_reason=None, force_signature={"YES": {"fear": 0.3}},
        conviction_index=0.41, branch_hashes={"NULL": "aa", "YES": "bb"},
        distances={"YES": 0.052145081169563567, "NO": 0.017381697133461459},
        noise_floor=0.01645, outcomes=["YES", "NO"])
    base.update(over)
    return SimpleNamespace(**base)


def _ask(v):
    world = SimpleNamespace(day=12.0, civ=SimpleNamespace(n=100))
    with patch.object(mv, "answer", return_value=v):
        return mv.ask({"question_id": "qsem",
                       "text": "will the market crash by 2027",
                       "class": "market_cascade"}, world, 1, 1)


# ═══ 1. the payload carries the semantics fields ═════════════════════

def test_binary_payload_carries_semantics_fields(qc_env):
    payload = _ask(_binary_verdict())
    assert payload["door"] == "forecast"
    assert payload["semantics"] == "branch_consistency"
    assert payload["semantics_note"] == EXPECTED_NOTE
    assert "SEMANTICS_BINARY_READOUT.md" in payload["semantics_note"]
    assert "p_model" in payload  # the fields sit next to the number


def test_abstaining_binary_payload_is_still_labeled(qc_env):
    """The label describes the readout construction, so a 2-outcome
    abstain (p_model None) is labeled too."""
    payload = _ask(_binary_verdict(
        abstain=True, p_model=None, p_by_outcome=None,
        abstain_reason="all branch deltas below class noise floor"))
    assert payload["p_model"] is None
    assert payload["semantics"] == "branch_consistency"
    assert payload["semantics_note"] == EXPECTED_NOTE


def test_multi_outcome_payload_not_labeled_with_binary_semantics(qc_env):
    """The note states the BINARY formula's semantics; the k>2 softmax
    path is a different registered readout and must not carry it."""
    payload = _ask(_binary_verdict(
        outcomes=["a", "b", "c"], p_model=0.5,
        p_by_outcome={"a": 0.5, "b": 0.3, "c": 0.2},
        distances={"O0": 0.1, "O1": 0.2, "O2": 0.3}))
    assert "semantics" not in payload
    assert "semantics_note" not in payload


# ═══ 2. computed values byte-identical to pre-change serving ═════════

def test_payload_values_pass_through_verbatim(qc_env):
    """Pre-change, ask() served the Verdict's numbers verbatim; the
    additive fields must not perturb a single computed value."""
    v = _binary_verdict()
    payload = _ask(v)
    assert payload["p_model"] == 0.30199999999999999
    assert payload["p_model"] is v.p_model            # untouched object
    assert payload["p_by_outcome"] is v.p_by_outcome
    assert payload["distances"] is v.distances
    assert payload["noise_floor"] == 0.01645
    assert payload["conviction_index"] == 0.41
    assert payload["branch_hashes"] is v.branch_hashes


# Captured PRE-CHANGE (2026-09-08, before the semantics fields landed):
# birth_world(2000, 42, substrate="c2plus_v1"), class market_cascade,
# outcomes YES/NO, country None, seed 7, horizon 8 days, in a process
# whose env carries no EARTH1_* export (the scrubbed default physics —
# the freeze09-sourced shell yields a different, equally frozen value,
# which is why the subprocess scrubs rather than inherits).
PRECHANGE = {"p_model": 0.25000003678733956,
             "d_YES": 0.052145081169563567,
             "d_NO": 0.017381697133461459}

_SUBPROC_SRC = r"""
import copy, json, os, shutil, sys, tempfile
sys.path.insert(0, {root!r})
from earth1.alive import birth_world
from earth1.adapters import multiverse as mv
tmp = tempfile.mkdtemp()
os.makedirs(os.path.join(tmp, "data"))
shutil.copy(os.path.join({root!r}, "data", "question_classes.json"),
            os.path.join(tmp, "data", "question_classes.json"))
mv._ROOT, mv._CLASSES = tmp, None       # repo data files never written
w = birth_world(2000, 42, substrate="c2plus_v1")
payload = mv.ask({{"question_id": "sem-capture",
                   "text": "will the market crash by 2027",
                   "class": "market_cascade"}}, w, 7, 8)
print(json.dumps({{"p_model": payload["p_model"],
                   "d_YES": payload["distances"]["YES"],
                   "d_NO": payload["distances"]["NO"],
                   "semantics": payload.get("semantics"),
                   "semantics_note": payload.get("semantics_note")}}))
"""


def test_p_model_matches_captured_prechange_expectation():
    """End-to-end: a real tiny-world ask() serves p_model bitwise equal
    to the pre-change capture, WITH the semantics fields alongside."""
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("EARTH1_")}
    out = subprocess.run(
        [sys.executable, "-c", _SUBPROC_SRC.format(root=str(ROOT))],
        capture_output=True, text=True, env=env, timeout=600)
    assert out.returncode == 0, out.stderr[-2000:]
    got = json.loads(out.stdout.strip().splitlines()[-1])
    assert got["p_model"] == PRECHANGE["p_model"]     # bitwise
    assert got["d_YES"] == PRECHANGE["d_YES"]
    assert got["d_NO"] == PRECHANGE["d_NO"]
    # the registered formula reconstructs the served number exactly
    assert got["p_model"] == got["d_NO"] / (got["d_YES"] + got["d_NO"])
    assert got["semantics"] == "branch_consistency"
    assert got["semantics_note"] == EXPECTED_NOTE


# ═══ 3. the semantics document ═══════════════════════════════════════

def test_semantics_doc_exists_and_names_the_three_options():
    assert SEM_DOC.exists(), "ops/alive/SEMANTICS_BINARY_READOUT.md missing"
    text = SEM_DOC.read_text()
    for marker in ("Option A", "Option B", "Option C",
                   "KEEP", "CALIBRATE", "REDESIGN"):
        assert marker in text, f"doc does not name ruling option: {marker}"
    # the load-bearing semantic claims
    assert "branch_consistency" in text
    assert "d_NO / (d_YES + d_NO)" in text
    assert "not a calibrated event probability" in text
    # the redesign track's stated blocker
    assert "0 resolutions" in text
