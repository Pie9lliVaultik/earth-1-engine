"""Review M07b/c/d regression suite — multiverse adapter correctness.

Reproduces the external review's probes (review_probes.py + verify
probe_m07.py) as stubs: no worlds are birthed, answer() is patched
where a Verdict is needed, and every disk write is redirected to a
temp _ROOT. The repo's registered data/question_classes.json must be
byte-identical after every test (asserted via sha256, session-wide).

M07a (binary readout semantics) is deliberately NOT tested for change:
it is founder-gated; the formula carries a NOTE and stays as registered.
"""
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from earth1.adapters import multiverse as mv  # noqa: E402

REPO_QC = ROOT / "data" / "question_classes.json"


def _sha(p) -> str:
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


@pytest.fixture(scope="session", autouse=True)
def repo_registry_is_never_written():
    """review M07d: the registered file is read-only at request time."""
    before = _sha(REPO_QC)
    yield
    assert _sha(REPO_QC) == before, (
        "a test wrote the repo's registered question_classes.json")


@pytest.fixture
def qc_env(tmp_path):
    """Temp _ROOT holding a copy of the registered registry; the module
    cache is cleared on the way in and out so no test leaks classes."""
    os.makedirs(tmp_path / "data")
    shutil.copy(REPO_QC, tmp_path / "data" / "question_classes.json")
    saved_root = mv._ROOT
    mv._ROOT, mv._CLASSES = str(tmp_path), None
    yield (str(tmp_path / "data" / "question_classes.json"),
           str(tmp_path / "data" / "question_classes_auto.json"))
    mv._ROOT, mv._CLASSES = saved_root, None


# ═══ M07c — 2-fork conditional key rule mirrors answer() ═════════════

def test_reviewer_contract_stub_passes(qc_env):
    """The reviewer's exact contract stub (review_probes.py): a 2-fork
    conditional against a binary-shaped Verdict must not KeyError."""
    with patch.object(mv, "answer") as ma:
        ma.return_value = SimpleNamespace(
            abstain=False,
            force_signature={"YES": {"fear": 0.1}, "NO": {"fear": -0.1}})
        out = mv._conditional_door(
            {"question_id": "review",
             "text": "what happens if a crisis occurs",
             "outcomes": ["occurs", "does not occur"],
             "class": "market_cascade"}, None, 42, 1)
    assert [f["fork"] for f in out["forks"]] == ["occurs", "does not occur"]
    # the forks were read under answer()'s own binary keys
    assert out["forks"][0]["force_delta"] == {"fear": 0.1}
    assert out["forks"][1]["force_delta"] == {"fear": -0.1}
    spec = ma.call_args[0][0]
    assert spec["outcomes"] == ["occurs", "does not occur"]


def test_three_fork_conditional_keeps_o_keys_and_restores_cache(qc_env):
    """k>2 forks still key O{i}; the derived forces are visible to
    answer() at call time but the cached template is restored (M07d —
    the verify probe's d_cache_mutation check)."""
    seen = {}

    def fake_answer(spec, base_world, seed, horizon_days):
        tpl = mv.classes()[spec["class"]]
        seen["forces_keys"] = sorted(tpl["injector"]["forces"].keys())
        return SimpleNamespace(
            abstain=False,
            force_signature={f"O{i}": {"fear": 0.1, "desire": 0.2}
                             for i in range(3)})

    before = sorted(
        mv.classes()["market_cascade"]["injector"]["forces"].keys())
    with patch.object(mv, "answer", side_effect=fake_answer):
        out = mv._conditional_door(
            {"question_id": "review-3", "text": "what happens if it spreads",
             "outcomes": ["a", "b", "c"], "class": "market_cascade"},
            None, 1, 1)
    assert {"O0", "O1", "O2"} <= set(seen["forces_keys"])
    after = sorted(
        mv.classes()["market_cascade"]["injector"]["forces"].keys())
    assert before == after == ["NO", "YES"]
    assert len(out["forks"]) == 3


def test_cache_restored_even_when_answer_raises(qc_env):
    with patch.object(mv, "answer", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError):
            mv._conditional_door(
                {"question_id": "review-x", "text": "what happens if x",
                 "outcomes": ["a", "b", "c"], "class": "market_cascade"},
                None, 1, 1)
    assert sorted(mv.classes()["market_cascade"]["injector"]["forces"]
                  .keys()) == ["NO", "YES"]


# ═══ M07b — binary tier must not key on temperature_fitted ═══════════

def test_binary_tier_ignores_temperature_fitted(qc_env):
    """The verify probe showed p_model identical at T=1 and T=99 with
    temperature_fitted=True, yet _tier said CALIBRATED. Binary tiers
    now key on binary_calibrated, which the binary path consumes."""
    mv.classes()["market_cascade"]["temperature_fitted"] = True
    assert mv._tier("market_cascade", False, 2) == "UNCALIBRATED"
    assert mv._tier("market_cascade", False, 3) == "CALIBRATED"
    assert mv._tier("market_cascade", True, 2) == "ABSTAIN"


def test_binary_tier_keys_on_binary_calibrated_marker(qc_env):
    mv.classes()["market_cascade"]["binary_calibrated"] = True
    assert mv._tier("market_cascade", False, 2) == "CALIBRATED"
    # the marker says nothing about the softmax path
    assert mv._tier("market_cascade", False, 3) == "UNCALIBRATED"
    # default absent -> UNCALIBRATED
    assert mv._tier("policy", False, 2) == "UNCALIBRATED"
    assert mv._tier("policy", False, 3) == "UNCALIBRATED"


def test_ask_binary_payload_stays_uncalibrated_despite_fitted_temp(qc_env):
    mv.classes()["market_cascade"]["temperature_fitted"] = True  # the trap
    v = SimpleNamespace(
        question_class="market_cascade", abstain=False, p_model=0.6,
        p_by_outcome={"YES": 0.6, "NO": 0.4}, abstain_reason=None,
        force_signature={}, conviction_index=None, branch_hashes={},
        distances={}, noise_floor=0.0, outcomes=["YES", "NO"])
    world = SimpleNamespace(day=12.0, civ=SimpleNamespace(n=100))
    with patch.object(mv, "answer", return_value=v):
        payload = mv.ask({"question_id": "qb",
                          "text": "will the market crash by 2027",
                          "class": "market_cascade"}, world, 1, 1)
    assert payload["door"] == "forecast"
    assert payload["calibration_tier"] == "UNCALIBRATED"


# ═══ M07d — overlay registration; registered file byte-identical ═════

def test_auto_class_goes_to_overlay_only(qc_env):
    reg_path, overlay_path = qc_env
    before = _sha(reg_path)
    got = mv._ensure_class("probe_brand_new_class",
                           "will grain prices spike after the drought")
    assert got == "probe_brand_new_class"
    assert _sha(reg_path) == before          # byte-identical
    ov = json.load(open(overlay_path))
    ent = ov["classes"]["probe_brand_new_class"]
    assert ent["status"] == "provisional_auto"
    assert ent["owner"] == "auto"
    assert "YES" in ent["injector"]["forces"]
    assert "NO" in ent["injector"]["forces"]
    # overlay is loaded after the registered file
    assert "probe_brand_new_class" in mv.classes()
    # and never merged back into the registered one
    reg = json.load(open(reg_path))["classes"]
    assert "probe_brand_new_class" not in reg


def test_registered_class_wins_over_overlay(qc_env):
    reg_path, overlay_path = qc_env
    json.dump({"classes": {"market_cascade": {"noise_floor": 999.0}}},
              open(overlay_path, "w"))
    mv._CLASSES = None
    assert mv.classes()["market_cascade"]["noise_floor"] != 999.0


def test_full_request_leaves_registered_file_byte_identical(qc_env):
    """End-to-end request with an UNKNOWN class: registration happens,
    but only the overlay is created — the sha of the registered file is
    unchanged (the verify probe's d_disk_write, inverted)."""
    reg_path, overlay_path = qc_env
    before = _sha(reg_path)
    with patch.object(mv, "answer") as ma:
        ma.return_value = SimpleNamespace(
            abstain=False,
            force_signature={"YES": {"fear": 0.1}, "NO": {"fear": -0.1}})
        mv._conditional_door(
            {"question_id": "review-new",
             "text": "what happens if the harbor closes",
             "outcomes": ["closes", "stays open"],
             "class": "never_seen_class_m07d"}, None, 7, 1)
    assert _sha(reg_path) == before
    assert "never_seen_class_m07d" in json.load(
        open(overlay_path))["classes"]
    assert "never_seen_class_m07d" not in json.load(
        open(reg_path))["classes"]
