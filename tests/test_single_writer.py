"""0.6 — the single_writer_world topology invariant.

The laptop must never again be capable of silently becoming another
Earth. Exactly one persistent writer exists: the production daemon on
the canonical host. This machine (any dev machine) may run tests and
bounded dev worlds, but nothing here may be configured to KEEP a world
alive.

History: a launchd job (com.earthling.earth1-daily) ran a third world
on the old substrate daily until 0.6 removed it — armed to resurrect at
every login even while unloaded. Its corpse is archived as evidence in
ops/legacy_archive/; reinstalling anything like it refuses release.
"""
import plistlib
import subprocess
from pathlib import Path

import pytest

from earth1.single_writer import (WORLD_RUNNER_MARKERS, scan_launch_dirs,
                                  assert_single_writer)


def test_no_world_runner_is_configured_on_this_machine():
    """The gate proper: no launchd/LaunchAgent/LaunchDaemon on this
    machine can start an Earth-1 world."""
    offenders = scan_launch_dirs()
    assert offenders == [], \
        f"world-capable launch jobs found: {offenders} — the laptop " \
        f"is armed to become another Earth"
    assert_single_writer()


def test_restored_launchd_config_is_refused(tmp_path):
    """Required failing control 1: restore the retired configuration →
    the gate must FAIL."""
    retired = (Path(__file__).resolve().parents[1]
               / "ops/legacy_archive/com.earthling.earth1-daily.plist"
                 ".retired")
    assert retired.exists(), "the archived evidence is missing"
    staged = tmp_path / "com.earthling.earth1-daily.plist"
    staged.write_bytes(retired.read_bytes())
    offenders = scan_launch_dirs(extra_dirs=[tmp_path])
    assert offenders, "the gate cannot detect the retired job"
    with pytest.raises(RuntimeError, match="single_writer_world"):
        assert_single_writer(extra_dirs=[tmp_path])


def test_second_canonical_writer_is_refused(tmp_path):
    """Required failing control 2: configure a NEW second writer (not
    the historical one) → the gate must FAIL."""
    plist = {"Label": "com.example.my-own-earth",
             "ProgramArguments": ["/usr/bin/python3",
                                  "/opt/earth1/scripts/world_alive.py"],
             "KeepAlive": True}
    p = tmp_path / "com.example.my-own-earth.plist"
    with open(p, "wb") as f:
        plistlib.dump(plist, f)
    offenders = scan_launch_dirs(extra_dirs=[tmp_path])
    assert offenders, "a fresh second-writer config was not detected"
    with pytest.raises(RuntimeError, match="single_writer_world"):
        assert_single_writer(extra_dirs=[tmp_path])


def test_dev_tooling_remains_possible():
    """Ordinary dev/test use is NOT a persistent Earth: birthing and
    ticking a world in-process must stay allowed."""
    import numpy as np
    from earth1.alive import birth_world, live_one_day
    w = birth_world(2_000, 1)
    live_one_day(w, np.random.default_rng(1))
    assert w.day == 1                      # ran, ended, nothing persists


def test_markers_cover_the_known_runners():
    for needle in ("world_alive", "world_daily", "earth1-daily"):
        assert any(needle in m for m in WORLD_RUNNER_MARKERS)
