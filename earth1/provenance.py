"""PROVENANCE — know exactly which civilization is running.

Phase 0.0e. No physics, no calibration. This module answers one
question before the world takes a step: is the code executing right now
the code we intended to deploy, and can we prove that later from an
artifact rather than an argument?

It exists because on 2026-08-19 the audit found the 4M-agent world
running commit 14401ea — 133 commits behind the branch it was being
developed on — with earth1/alive.py staged-but-uncommitted, and with no
service definition in source control at all. Seven of nine live files
happened to be byte-identical, so the audit survived. That was luck,
and luck is not a control.

The five invariants (founder ruling, 2026-08-19):

    running SHA == intended SHA
    worktree clean
    service definition in source control
    config recorded at startup
    state schema recorded at startup

A daemon that cannot establish these refuses to start. The operator may
override with EARTH1_ALLOW_DIRTY=1 — but the override is itself
journaled, so an accepted risk is never an invisible one.

Nothing here reads or writes world state. It is safe to call before the
world exists.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

# The World state schema (earth1/alive.py:34-49). Bump when a field is
# added, removed, or changes meaning — a snapshot written under one
# version must never be silently loaded under another. Unversioned
# snapshots (everything written before 0.0c) report as None.
SCHEMA_VERSION = 1

# Where the checked-in unit file lives, relative to the repo root, and
# where systemd installs it. Divergence between the two is a violation:
# it means the running service is not the one under review.
SERVICE_IN_REPO = "ops/alive/earth1-alive.service"
SERVICE_INSTALLED = "/etc/systemd/system/earth1-alive.service"


class ProvenanceError(RuntimeError):
    """Raised when the running world cannot prove what it is."""


def _git(root: Path, *args: str) -> Optional[str]:
    """Run a git command, or return None if git/the repo is unavailable."""
    try:
        out = subprocess.run(("git", "-C", str(root)) + args,
                             capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    # strip trailing newlines ONLY — `git status --porcelain` encodes the
    # index/worktree state in the first two columns, so a leading space
    # is data ("  M f.txt" is not the same as "M  f.txt") and .strip()
    # silently shifts every unstaged path by one character.
    return out.stdout.rstrip("\n")


def git_commit(root: Path) -> Optional[str]:
    """Full SHA of HEAD, or None outside a git tree."""
    out = _git(root, "rev-parse", "HEAD")
    return None if out is None else out.strip()


def git_dirty(root: Path) -> Optional[List[str]]:
    """Paths that differ from HEAD — staged, unstaged, or untracked.

    Returns [] for a clean tree, None if this is not a git tree at all.
    The distinction matters: 'clean' is a passed check, 'unknown' is a
    failed one.
    """
    out = _git(root, "status", "--porcelain")
    if out is None:
        return None
    paths = []
    for ln in out.splitlines():
        if not ln.strip():
            continue
        # porcelain v1: two status columns, a space, then the path.
        # Renames arrive as "R  old -> new"; the new name is what exists.
        p = ln[3:]
        if " -> " in p:
            p = p.split(" -> ", 1)[1]
        paths.append(p)
    return paths


def sha256_file(path: Path) -> Optional[str]:
    """Hex digest of a file, or None if it is not readable."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def config_hash(config: Dict[str, Any]) -> str:
    """Stable digest of a config mapping — key order never matters."""
    blob = json.dumps(config, sort_keys=True, separators=(",", ":"),
                      default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def record(root: Path, *,
           config: Dict[str, Any],
           population: Optional[int] = None,
           world_day: Optional[int] = None,
           snapshot_version: Optional[int] = None,
           intended_commit: Optional[str] = None) -> Dict[str, Any]:
    """Build the provenance record for this process.

    `intended_commit` is what deployment believed it shipped — from the
    EARTH1_EXPECT_COMMIT environment variable if not passed. When it is
    unset we cannot check running-vs-intended, and say so rather than
    pretending the check passed.
    """
    root = Path(root)
    dirty = git_dirty(root)
    intended = intended_commit or os.environ.get("EARTH1_EXPECT_COMMIT") or None
    running = git_commit(root)

    repo_service = root / SERVICE_IN_REPO
    installed_service = Path(SERVICE_INSTALLED)
    repo_hash = sha256_file(repo_service)
    installed_hash = sha256_file(installed_service)

    return {
        "code_commit": running,
        "intended_commit": intended,
        "commit_matches": (None if (running is None or intended is None)
                           else running.startswith(intended)
                           or intended.startswith(running)),
        "dirty_worktree": (None if dirty is None else bool(dirty)),
        # capped: a genuinely broken deploy should not write a novel to
        # the journal, but the count is always exact
        "dirty_paths": (None if dirty is None else sorted(dirty)[:20]),
        "dirty_count": (None if dirty is None else len(dirty)),
        "service_in_repo": repo_service.exists(),
        "service_repo_sha256": repo_hash,
        "service_installed_sha256": installed_hash,
        "service_matches": (None if (repo_hash is None
                                     or installed_hash is None)
                            else repo_hash == installed_hash),
        "config_hash": config_hash(config),
        "config": dict(config),
        "schema_version": SCHEMA_VERSION,
        "snapshot_version": snapshot_version,
        "population": population,
        "world_day": world_day,
        "allow_dirty": os.environ.get("EARTH1_ALLOW_DIRTY") == "1",
        "host": os.uname().nodename,
    }


def violations(rec: Dict[str, Any]) -> List[str]:
    """Every invariant this record fails, in plain language.

    Unknown counts as failed. A check that could not run has not passed.
    """
    bad: List[str] = []

    if rec.get("code_commit") is None:
        bad.append("running commit unknown — not a git tree, or git unavailable")
    if rec.get("dirty_worktree") is None:
        bad.append("worktree cleanliness unknown — cannot prove what is running")
    elif rec["dirty_worktree"]:
        n = rec.get("dirty_count")
        bad.append(f"worktree dirty — {n} path(s) differ from HEAD, "
                   f"e.g. {', '.join(rec.get('dirty_paths') or [])[:200]}")

    if rec.get("intended_commit") is None:
        bad.append("intended commit not declared — set EARTH1_EXPECT_COMMIT")
    elif rec.get("commit_matches") is False:
        bad.append(f"running {str(rec['code_commit'])[:12]} != "
                   f"intended {str(rec['intended_commit'])[:12]}")

    if not rec.get("service_in_repo"):
        bad.append(f"service definition not in source control "
                   f"({SERVICE_IN_REPO} missing)")
    elif rec.get("service_matches") is False:
        bad.append("installed service definition differs from the "
                   "checked-in one")

    return bad


def enforce(rec: Dict[str, Any], *, strict: bool = True) -> List[str]:
    """Refuse to run an unprovenanced world. Returns the violation list.

    strict=False downgrades to a warning — for laptop iteration, never
    for the single writer. EARTH1_ALLOW_DIRTY=1 also downgrades, and is
    recorded in the journal so the exception is auditable after the fact.
    """
    bad = violations(rec)
    if not bad:
        return []
    if not strict or rec.get("allow_dirty"):
        for v in bad:
            print(f"  PROVENANCE WARNING: {v}", flush=True)
        if rec.get("allow_dirty"):
            print("  (EARTH1_ALLOW_DIRTY=1 — override recorded in journal)",
                  flush=True)
        return bad
    raise ProvenanceError(
        "refusing to start: the world cannot prove what code it is.\n  - "
        + "\n  - ".join(bad)
        + "\n\nFix the deployment, or set EARTH1_ALLOW_DIRTY=1 to accept "
          "the risk explicitly (it will be journaled)."
    )
