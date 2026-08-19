"""Semantic invariants for the 0.0e provenance gate.

The invariant: a world that cannot prove what code it is does not start.

Standing Rule 1 — the instrument is verified on a known answer first
(`test_clean_record_passes`), so a green result here means something.
Standing Rule 2 — every control can fail: each check below is exercised
in both directions, and `test_unknown_git_is_a_violation` pins the
decision that UNKNOWN counts as FAILED. A check that could not run has
not passed.
"""
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, ".")

from earth1 import provenance
from earth1.provenance import ProvenanceError

SHA = "a" * 40
OTHER = "b" * 40


def _clean(**over):
    """A record that passes every invariant. The known answer."""
    rec = {
        "code_commit": SHA,
        "intended_commit": SHA,
        "commit_matches": True,
        "dirty_worktree": False,
        "dirty_paths": [],
        "dirty_count": 0,
        "service_in_repo": True,
        "service_repo_sha256": "f" * 64,
        "service_installed_sha256": "f" * 64,
        "service_matches": True,
        "config_hash": "0" * 64,
        "schema_version": provenance.SCHEMA_VERSION,
        "snapshot_version": 1,
        "population": 2000,
        "world_day": 7,
        "allow_dirty": False,
    }
    rec.update(over)
    return rec


# ── the instrument, verified on a known answer ──────────────────────

def test_clean_record_passes():
    assert provenance.violations(_clean()) == []
    assert provenance.enforce(_clean(), strict=True) == []


# ── each invariant, exercised in the failing direction ──────────────

def test_dirty_worktree_is_a_violation():
    rec = _clean(dirty_worktree=True, dirty_count=2,
                 dirty_paths=["earth1/alive.py", "earth1/health.py"])
    bad = provenance.violations(rec)
    assert any("dirty" in v for v in bad)
    with pytest.raises(ProvenanceError, match="cannot prove"):
        provenance.enforce(rec, strict=True)


def test_commit_mismatch_is_a_violation():
    """The exact 2026-08-19 finding: box on 14401ea, branch 133 ahead."""
    rec = _clean(code_commit=SHA, intended_commit=OTHER, commit_matches=False)
    assert any("!=" in v for v in provenance.violations(rec))
    with pytest.raises(ProvenanceError):
        provenance.enforce(rec, strict=True)


def test_undeclared_intent_is_a_violation():
    rec = _clean(intended_commit=None, commit_matches=None)
    assert any("EARTH1_EXPECT_COMMIT" in v for v in provenance.violations(rec))


def test_service_not_in_source_control_is_a_violation():
    """The other half of the finding: no unit file in git at all."""
    rec = _clean(service_in_repo=False)
    assert any("source control" in v for v in provenance.violations(rec))


def test_installed_service_drift_is_a_violation():
    rec = _clean(service_installed_sha256="e" * 64, service_matches=False)
    assert any("differs" in v for v in provenance.violations(rec))


def test_unknown_git_is_a_violation():
    """UNKNOWN is FAILED. A check that could not run has not passed."""
    rec = _clean(code_commit=None, dirty_worktree=None, dirty_paths=None,
                 dirty_count=None)
    bad = provenance.violations(rec)
    assert any("unknown" in v for v in bad)
    with pytest.raises(ProvenanceError):
        provenance.enforce(rec, strict=True)


# ── the override is a downgrade, never a silencer ───────────────────

def test_allow_dirty_downgrades_but_still_reports():
    rec = _clean(dirty_worktree=True, dirty_count=1,
                 dirty_paths=["earth1/alive.py"], allow_dirty=True)
    bad = provenance.enforce(rec, strict=True)
    assert bad, "override must still return the violations for journaling"


def test_non_strict_downgrades():
    rec = _clean(dirty_worktree=True, dirty_count=1, dirty_paths=["x.py"])
    assert provenance.enforce(rec, strict=False)


# ── helpers ─────────────────────────────────────────────────────────

def test_config_hash_is_order_independent():
    a = provenance.config_hash({"beta": 2.0, "relax": 0.25})
    b = provenance.config_hash({"relax": 0.25, "beta": 2.0})
    assert a == b
    assert a != provenance.config_hash({"beta": 1.0, "relax": 0.25})


def test_sha256_file_returns_none_when_absent(tmp_path):
    assert provenance.sha256_file(tmp_path / "nope") is None


def test_git_helpers_on_a_real_tree(tmp_path):
    """git_commit/git_dirty must actually work, not just return None."""
    r = tmp_path / "repo"
    r.mkdir()
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
           "PATH": "/usr/bin:/bin:/usr/local/bin"}
    def git(*a):
        subprocess.run(("git", "-C", str(r)) + a, check=True,
                       capture_output=True, env=env)
    git("init", "-q")
    (r / "f.txt").write_text("one")
    git("add", "-A")
    git("commit", "-qm", "first")

    sha = provenance.git_commit(r)
    assert sha and len(sha) == 40
    assert provenance.git_dirty(r) == []          # clean, and provably so

    (r / "f.txt").write_text("two")
    assert provenance.git_dirty(r) == ["f.txt"]   # and it can fail

    # regression: porcelain encodes state in the first TWO columns, so
    # an unstaged change is " M f.txt" with a LEADING SPACE. Stripping
    # it shifted every unstaged path by one character (-> ".txt") and
    # would have under-reported a dirty tree as a differently-named one.
    (r / "g.txt").write_text("new")               # untracked  -> "?? "
    git("add", "g.txt")                           # staged     -> "A  "
    dirty = provenance.git_dirty(r)
    assert sorted(dirty) == ["f.txt", "g.txt"], dirty


def test_git_helpers_outside_a_repo_return_none(tmp_path):
    assert provenance.git_commit(tmp_path) is None
    assert provenance.git_dirty(tmp_path) is None


def test_record_shape_on_this_repo():
    """The record must carry every field the founder's ruling names."""
    rec = provenance.record(Path(__file__).resolve().parents[1],
                            config={"beta": 2.0}, population=10, world_day=3)
    for k in ("code_commit", "dirty_worktree", "config_hash",
              "schema_version", "snapshot_version", "population",
              "world_day", "service_in_repo", "host"):
        assert k in rec, f"missing journal field: {k}"
    assert rec["service_in_repo"] is True, \
        "ops/alive/earth1-alive.service must be in source control"
