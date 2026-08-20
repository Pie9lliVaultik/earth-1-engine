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
    "live_one_day", "birth_world",
)

LAUNCH_DIRS = (
    Path.home() / "Library" / "LaunchAgents",
    Path("/Library/LaunchAgents"),
    Path("/Library/LaunchDaemons"),
)


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


def assert_single_writer(extra_dirs=None) -> None:
    offenders = scan_launch_dirs(extra_dirs=extra_dirs)
    if offenders:
        raise RuntimeError(
            "single_writer_world VIOLATED — this machine is configured "
            "to run an Earth-1 world without a human in the loop:\n  "
            + "\n  ".join(offenders)
            + "\nThe production daemon is the only persistent writer. "
              "Remove the job; archive it as evidence if it matters.")


if __name__ == "__main__":
    bad = scan_launch_dirs()
    if bad:
        print("VIOLATIONS:")
        for b in bad:
            print(" ", b)
        raise SystemExit(1)
    print("single_writer_world: this machine cannot silently become "
          "another Earth")
