"""KAs for the data-role registry (THREE_TRACK_PREREG_v1 §C1).

Standing Rule 2: each test here is built to FAIL a broken registry —
an enforcement layer that lets an illegal read through is worse than
none, because it launders the read as legal.
"""
import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from earth1.dataroles import (RoleViolation, TamperError, open_data,
                              path_for, register)


@pytest.fixture
def reg(tmp_path):
    rp = str(tmp_path / "roles.json")
    json.dump({"entries": {}}, open(rp, "w"))
    files = {}
    for name, role in [("t_train", "TRAIN"), ("t_holdout", "HOLDOUT"),
                       ("t_prosp", "PROSPECTIVE"),
                       ("t_outcome", "EVALUATION_OUTCOME")]:
        p = str(tmp_path / f"{name}.bin")
        open(p, "wb").write(f"payload-{name}".encode())
        register(name, p, role, seal=True, registry_path=rp)
        files[name] = p
    return rp, files


def test_illegal_purpose_raises(reg):
    rp, _ = reg
    with pytest.raises(RoleViolation):
        open_data("t_holdout", "training", registry_path=rp)
    with pytest.raises(RoleViolation):
        open_data("t_holdout", "model_selection", registry_path=rp)
    with pytest.raises(RoleViolation):
        open_data("t_holdout", "audit", registry_path=rp)  # sealed: no peeking
    with pytest.raises(RoleViolation):
        open_data("t_prosp", "validation", registry_path=rp)
    with pytest.raises(RoleViolation):
        open_data("t_outcome", "training", registry_path=rp)
    with pytest.raises(RoleViolation):
        open_data("t_outcome", "model_selection", registry_path=rp)


def test_unregistered_raises(reg):
    rp, _ = reg
    with pytest.raises(RoleViolation):
        open_data("never_registered", "training", registry_path=rp)


def test_unknown_purpose_raises(reg):
    rp, _ = reg
    with pytest.raises(RoleViolation):
        open_data("t_train", "just_a_peek", registry_path=rp)


def test_legal_reads_return_bytes(reg):
    rp, _ = reg
    with open_data("t_train", "training", registry_path=rp) as f:
        assert f.read() == b"payload-t_train"
    with open_data("t_holdout", "final_scoring", registry_path=rp) as f:
        assert f.read() == b"payload-t_holdout"
    with open_data("t_outcome", "evaluation", registry_path=rp) as f:
        assert f.read() == b"payload-t_outcome"


def test_tampered_seal_raises_even_for_legal_purpose(reg):
    rp, files = reg
    open(files["t_holdout"], "ab").write(b"x")
    with pytest.raises(TamperError):
        open_data("t_holdout", "final_scoring", registry_path=rp)


def test_path_for_enforces_same_rules(reg):
    rp, files = reg
    assert path_for("t_train", "training", registry_path=rp) \
        == files["t_train"]
    with pytest.raises(RoleViolation):
        path_for("t_holdout", "training", registry_path=rp)


def test_real_registry_valid_and_gss_sealed():
    """The committed registry parses, every role is legal, and the GSS
    consumed-set entry is sealed and reads clean."""
    from earth1.dataroles import REGISTRY_PATH, ROLES, load_registry
    reg = load_registry(REGISTRY_PATH)
    assert reg["entries"], "registry must not be empty"
    for name, e in reg["entries"].items():
        assert e["role"] in ROLES, name
    with open_data("gss_r1_consumed", "audit") as f:
        assert f.read(1)


def test_adjacency_gate_still_standalone():
    """Lineage adds, never replaces: the correlation gate's artifacts
    must still exist and carry rules independent of the registry."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    adj = json.load(open(os.path.join(root, "data",
                                      "feature_adjacency.json")))
    assert "rules" in adj or any("corr" in str(v).lower()
                                 for v in adj.values())
    assert os.path.exists(os.path.join(root, "scripts",
                                       "feature_adjacency_gate.py"))
