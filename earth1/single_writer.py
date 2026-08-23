"""single_writer_world — the topology invariant. Phase 0.6.

There is exactly one persistent writer of a canonical civilization: the
production daemon on the canonical host. Any machine that carries a
boot/login-armed job capable of running an Earth-1 world loop is a
latent second (or third) Earth — the failure mode that produced the
old-substrate laptop world, which ran daily for weeks after the living
world went to production.

This module scans the platform's launch directories for jobs whose
configuration references an Earth-1 world runner. It judges
CONFIGURATION, not processes: an unloaded plist is still armed — it
resurrects at the next login, which is exactly how the third world
survived its own obsolescence.

Dev use is untouched: running a world in-process (tests, notebooks,
scripts) is not a persistent writer. The line is persistence — anything
configured to start or keep a world WITHOUT a human in the loop.
"""
from __future__ import annotations

from pathlib import Path

# strings that identify a world-running job inside a launch config
WORLD_RUNNER_MARKERS = (
    "world_alive.py", "world_daily.py", "earth1-daily", "earth1-alive",
    "live_one_day", "birth_world", "run_daily",
)

LAUNCH_DIRS = (
    Path.home() / "Library" / "LaunchAgents",
    Path("/Library/LaunchAgents"),
    Path("/Library/LaunchDaemons"),
)

# ── systemd (0.7 extension) ──────────────────────────────────────────
# The 0.6 gate scanned launchd only — and a fourth world escaped it:
# earth1-daily.timer sat ENABLED on the production box itself, ticking
# the old substrate daily (last success 2026-08-19). Its corpse is in
# ops/legacy_archive/. The gate now judges systemd unit files too.
#
# On the canonical host, exactly the units that serve THE world are
# allowed to reference a runner; the supervisor, backup, and restore
# rehearsal serve the single writer — they are not writers themselves.
# On every other machine, NO systemd unit may reference a runner.
SYSTEMD_DIRS = (Path("/etc/systemd/system"),)

SYSTEMD_ALLOWED_ON_CANONICAL = frozenset({
    "earth1-alive.service",              # THE writer
    "earth1-supervisor.service", "earth1-supervisor.timer",
    "earth1-backup.service", "earth1-backup.timer",
    "earth1-restore-rehearsal.service", "earth1-restore-rehearsal.timer",
})


def scan_systemd_units(extra_dirs=None, canonical_host=False) -> list:
    """Every systemd unit on this machine that can start a world,
    minus the allowlisted units when this IS the canonical host."""
    offenders = []
    dirs = list(SYSTEMD_DIRS) + [Path(d) for d in (extra_dirs or [])]
    for d in dirs:
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.service")) + sorted(d.glob("*.timer")):
            if canonical_host and p.name in SYSTEMD_ALLOWED_ON_CANONICAL:
                continue
            try:
                text = p.read_bytes().decode("utf-8", errors="ignore")
            except OSError:
                continue
            # the unit NAME is systemd's label — judge it too: the real
            # fourth-world unit (earth1-daily.service) carried no marker
            # in its body, only in its name
            hits = [m for m in WORLD_RUNNER_MARKERS
                    if m in text or m in p.name]
            if hits:
                offenders.append(f"{p} (matches: {', '.join(hits)})")
    return offenders


def scan_launch_dirs(extra_dirs=None) -> list:
    """Every launch config on this machine that can start a world."""
    offenders = []
    dirs = list(LAUNCH_DIRS) + [Path(d) for d in (extra_dirs or [])]
    for d in dirs:
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.plist")):
            try:
                text = p.read_bytes().decode("utf-8", errors="ignore")
            except OSError:
                continue
            hits = [m for m in WORLD_RUNNER_MARKERS if m in text]
            if hits:
                offenders.append(f"{p} (matches: {', '.join(hits)})")
    return offenders


def assert_single_writer(extra_dirs=None, systemd_extra_dirs=None,
                         canonical_host=False) -> None:
    offenders = (scan_launch_dirs(extra_dirs=extra_dirs)
                 + scan_systemd_units(extra_dirs=systemd_extra_dirs,
                                      canonical_host=canonical_host))
    if offenders:
        raise RuntimeError(
            "single_writer_world VIOLATED — this machine is configured "
            "to run an Earth-1 world without a human in the loop:\n  "
            + "\n  ".join(offenders)
            + "\nThe production daemon is the only persistent writer. "
              "Remove the job; archive it as evidence if it matters.")


if __name__ == "__main__":
    import sys
    canonical = "--canonical-writer" in sys.argv
    bad = scan_launch_dirs() + scan_systemd_units(canonical_host=canonical)
    if bad:
        print("VIOLATIONS:")
        for b in bad:
            print(" ", b)
        raise SystemExit(1)
    role = "canonical writer" if canonical else "non-writer"
    print(f"single_writer_world ({role}): this machine cannot silently "
          "become another Earth")
