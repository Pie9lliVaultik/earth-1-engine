"""Data-role registry with fail-closed reads.

Founder ruling 2026-08-26 (ops/alive/THREE_TRACK_PREREG_v1.md, Track C):
data-role discipline no longer lives in Markdown. Every registered
dataset carries a role; code declares a purpose when it reads; illegal
(role, purpose) pairs raise before a single byte is returned.

Roles:   TRAIN, VALIDATION, HOLDOUT, PROSPECTIVE, INPUT_EXPOSURE,
         EVALUATION_OUTCOME
Purposes: training, model_selection, validation, input_exposure,
          evaluation, final_scoring, audit

The registry is data/data_roles.json. Sealed entries record a sha256 at
registration; open_data verifies it on every read and refuses on
mismatch — a silently edited holdout is treated as tampering, not as
data. The feature-lineage graph (data/feature_lineage.json) is a
separate, additive record; the correlation/adjacency gate
(scripts/feature_adjacency_gate.py) is preserved independently and is
NOT replaced by lineage.
"""
from __future__ import annotations

import hashlib
import json
import os

ROLES = ("TRAIN", "VALIDATION", "HOLDOUT", "PROSPECTIVE",
         "INPUT_EXPOSURE", "EVALUATION_OUTCOME")
PURPOSES = ("training", "model_selection", "validation", "input_exposure",
            "evaluation", "final_scoring", "audit")

# Which purposes may read which role. Fail-closed: anything not listed
# here raises. "audit" is read-only inspection (hash checks, listings)
# and is legal everywhere EXCEPT sealed holdout/prospective content.
_ALLOWED = {
    "TRAIN":              {"training", "model_selection", "validation",
                           "evaluation", "audit"},
    "VALIDATION":         {"model_selection", "validation", "evaluation",
                           "audit"},
    "HOLDOUT":            {"final_scoring"},
    "PROSPECTIVE":        {"final_scoring"},
    "INPUT_EXPOSURE":     {"input_exposure", "evaluation", "audit"},
    "EVALUATION_OUTCOME": {"evaluation", "final_scoring", "audit"},
}

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(_REPO, "data", "data_roles.json")


class RoleViolation(RuntimeError):
    """An illegal (role, purpose) access. Never catch-and-continue."""


class TamperError(RuntimeError):
    """A sealed dataset's bytes no longer match its registered hash."""


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_registry(path: str = REGISTRY_PATH) -> dict:
    with open(path) as f:
        return json.load(f)


def register(name: str, path: str, role: str, *, lineage=None,
             licence: str = "", notes: str = "", seal: bool = False,
             registry_path: str = REGISTRY_PATH) -> dict:
    """Add or update a registry entry. Sealing records the sha256 now;
    any later change to the bytes makes every read fail."""
    if role not in ROLES:
        raise ValueError(f"unknown role {role!r}; roles are {ROLES}")
    reg = load_registry(registry_path) if os.path.exists(registry_path) \
        else {"entries": {}}
    entry = {
        "path": os.path.relpath(os.path.abspath(path), _REPO)
        if os.path.abspath(path).startswith(_REPO) else path,
        "role": role,
        "lineage": lineage or [],
        "licence": licence,
        "notes": notes,
    }
    if seal:
        entry["sha256"] = _sha256(path)
    reg["entries"][name] = entry
    with open(registry_path, "w") as f:
        json.dump(reg, f, indent=1, sort_keys=True)
    return entry


def _resolve(entry_path: str) -> str:
    return entry_path if os.path.isabs(entry_path) \
        else os.path.join(_REPO, entry_path)


def open_data(name: str, purpose: str, *, registry_path: str = REGISTRY_PATH):
    """The ONLY sanctioned way experiment code reads registered data.

    Returns an open binary file handle. Raises RoleViolation for an
    illegal (role, purpose) pair or an unregistered name, TamperError
    if a sealed entry's bytes have changed.
    """
    if purpose not in PURPOSES:
        raise RoleViolation(
            f"unknown purpose {purpose!r}; purposes are {PURPOSES}")
    reg = load_registry(registry_path)
    entry = reg["entries"].get(name)
    if entry is None:
        raise RoleViolation(
            f"{name!r} is not in the data-role registry; register it "
            f"with a role before reading it")
    role = entry["role"]
    if purpose not in _ALLOWED[role]:
        raise RoleViolation(
            f"{name!r} has role {role}; purpose {purpose!r} is not "
            f"permitted (allowed: {sorted(_ALLOWED[role])})")
    path = _resolve(entry["path"])
    if "sha256" in entry:
        actual = _sha256(path)
        if actual != entry["sha256"]:
            raise TamperError(
                f"{name!r} is sealed with sha256 {entry['sha256'][:12]}… "
                f"but the bytes on disk hash to {actual[:12]}…")
    return open(path, "rb")


def path_for(name: str, purpose: str, *,
             registry_path: str = REGISTRY_PATH) -> str:
    """Role-checked path lookup for readers that need a filename
    (duckdb, pandas). Same enforcement as open_data; verifies seal."""
    with open_data(name, purpose, registry_path=registry_path):
        pass
    return _resolve(load_registry(registry_path)["entries"][name]["path"])
