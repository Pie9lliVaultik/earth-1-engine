"""CONFIG STAMP — make a wrong-physics run impossible to mistake.

A run launched without the freeze-0.9 exports silently uses engine
DEFAULTS (cliff hardship, legacy mortality, income calibration off) and
produces numbers that look plausible but are not comparable to any
board. That happened on 2026-09-02 and cost a 46-hour run.

Every artifact-producing script calls stamp() and writes the result
into its output. assert_freeze09() refuses to proceed when the physics
is not the frozen candidate.
"""
import os

FREEZE_09 = {
    "EARTH1_HARDSHIP_MODE": "gradient",
    "EARTH1_INCOME_CALIBRATION": "v1",
    "EARTH1_SUBSTRATE_FLAG": "c2plus_v1",
    "EARTH1_C2PLUS_TABLES": "c2plus_tables_v2.json",
    "EARTH1_MORTALITY_MODE": "gompertz",
    "EARTH1_WANT_MODE": "rr",
    "EARTH1_DISTRESS_LAYOFFS": "on",
}


def stamp() -> dict:
    """What physics is actually loaded, as the modules read it."""
    from earth1 import health, life
    got = {k: os.environ.get(k, "(unset->default)") for k in FREEZE_09}
    mismatch = {k: got[k] for k, v in FREEZE_09.items() if got[k] != v}
    return {"env": got,
            "loaded": {"hardship_mode": life.HARDSHIP_MODE,
                       "income_calibration": life.INCOME_CALIBRATION,
                       "mortality_mode": health.MORTALITY_MODE,
                       "distress_layoffs": life.DISTRESS_LAYOFFS},
            "is_freeze_09": not mismatch,
            "mismatch": mismatch or None,
            "warning": (None if not mismatch else
                        "NOT freeze-0.9 — these numbers are not "
                        "comparable to any committed board")}


def assert_freeze09():
    s = stamp()
    if not s["is_freeze_09"]:
        raise SystemExit(
            "REFUSING TO RUN: physics is not freeze-0.9.\n"
            "  mismatched: %s\n"
            "  loaded:     %s\n"
            "  fix: set -a; . scripts/env/freeze09.env; set +a"
            % (s["mismatch"], s["loaded"]))
    return s
