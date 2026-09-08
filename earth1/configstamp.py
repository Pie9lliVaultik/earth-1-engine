"""CONFIG STAMP — make a wrong-physics run impossible to mistake.

A run launched without the freeze-0.9 exports silently uses engine
DEFAULTS (cliff hardship, legacy mortality, income calibration off) and
produces numbers that look plausible but are not comparable to any
board. That happened on 2026-09-02 and cost a 46-hour run.

Every artifact-producing script calls stamp() and writes the result
into its output. assert_freeze09() refuses to proceed when the physics
is not the frozen candidate.

HARDENED 2026-09-08 (external review M02a/M02b, verified):
  * The frozen flag set is parsed from scripts/env/freeze09.env — the
    file the runbooks source — so the stamp can never drift from it.
    The embedded fallback below is used only if the file is absent,
    and the stamp says so.
  * stamp() now verifies the LOADED module state, not just the
    environment: modules bind several flags at import, so a process
    that imported before the exports were set used default physics
    while the old env-only check said freeze-0.9. Import-bound values
    are compared against the frozen ones (floats at rel tol 1e-9) and
    any drift fails is_freeze_09 with a named loaded_mismatch.
  * All eleven frozen degrees of freedom are covered — the four
    numerical coefficients (GM other-share, want RR, weather scale,
    layoff gain) included, where the old stamp checked seven mode
    strings only.
"""
import os

_ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "scripts", "env", "freeze09.env")

# Fallback only — scripts/env/freeze09.env is the single source of truth.
_FALLBACK = {
    "EARTH1_HARDSHIP_MODE": "gradient",
    "EARTH1_INCOME_CALIBRATION": "v1",
    "EARTH1_SUBSTRATE_FLAG": "c2plus_v1",
    "EARTH1_C2PLUS_TABLES": "c2plus_tables_v2.json",
    "EARTH1_MORTALITY_MODE": "gompertz",
    "EARTH1_GM_OTHER_SHARE": "0.21407724082954704",
    "EARTH1_WANT_MODE": "rr",
    "EARTH1_WANT_RR": "4.933765606879083",
    "EARTH1_WEATHER_SCALE": "0.020333010074315046",
    "EARTH1_DISTRESS_LAYOFFS": "on",
    "EARTH1_LAYOFF_GAIN": "0.0028",
}


def _parse_env_file():
    """freeze09.env -> {VAR: value}. review M02b: parsed, not retyped."""
    try:
        out = {}
        for line in open(_ENV_FILE):
            line = line.strip()
            if not line.startswith("export ") or "=" not in line:
                continue
            k, v = line[len("export "):].split("=", 1)
            out[k.strip()] = v.strip()
        return (out, "freeze09.env") if out else (_FALLBACK, "fallback")
    except OSError:
        return _FALLBACK, "fallback"


FREEZE_09, _SOURCE = _parse_env_file()

_REL_TOL = 1e-9


def _differs(a: str, b: str) -> bool:
    """String compare; numeric strings compare at rel tol (review M02b)."""
    if a == b:
        return False
    try:
        fa, fb = float(a), float(b)
        return abs(fa - fb) > _REL_TOL * max(abs(fa), abs(fb), 1e-300)
    except (TypeError, ValueError):
        return True


def _loaded_state():
    """What the imported modules actually bound (review M02a).

    Import-bound values are the ones the env-only check missed; the
    call-time reads (want mode/RR, weather scale) follow the env at use
    and are covered by the env comparison above.
    """
    from earth1 import health, life
    return {
        "hardship_mode": (life.HARDSHIP_MODE, "gradient"),
        "income_calibration": (life.INCOME_CALIBRATION, "v1"),
        "mortality_mode": (health.MORTALITY_MODE, "gompertz"),
        "distress_layoffs": (life.DISTRESS_LAYOFFS, "on"),
        "layoff_gain": (str(life.LAYOFF_GAIN),
                        FREEZE_09.get("EARTH1_LAYOFF_GAIN", "0.0028")),
        "gm_other_share": (str(health.GM_OTHER_SHARE),
                           FREEZE_09.get("EARTH1_GM_OTHER_SHARE",
                                         "0.21407724082954704")),
    }


def stamp() -> dict:
    """What physics is actually loaded, as the modules read it."""
    got = {k: os.environ.get(k, "(unset->default)") for k in FREEZE_09}
    mismatch = {k: got[k] for k, v in FREEZE_09.items()
                if _differs(got[k], v)}
    loaded_raw = _loaded_state()
    loaded = {k: v[0] for k, v in loaded_raw.items()}
    loaded_mismatch = sorted(
        k for k, (have, want) in loaded_raw.items()
        if _differs(str(have), str(want)))
    ok = not mismatch and not loaded_mismatch
    return {"env": got,
            "env_source": _SOURCE,
            "loaded": loaded,
            # review M02a: loaded state is part of the verdict, so an
            # import that preceded the exports can no longer pass.
            "loaded_mismatch": loaded_mismatch or None,
            "is_freeze_09": ok,
            "mismatch": mismatch or None,
            "warning": (None if ok else
                        "NOT freeze-0.9 — these numbers are not "
                        "comparable to any committed board")}


def assert_freeze09():
    s = stamp()
    if not s["is_freeze_09"]:
        raise SystemExit(
            "REFUSING TO RUN: physics is not freeze-0.9.\n"
            "  env mismatched:    %s\n"
            "  loaded mismatched: %s\n"
            "  loaded:            %s\n"
            "  fix: set -a; . scripts/env/freeze09.env; set +a "
            "(BEFORE the first earth1 import — modules bind at import)"
            % (s["mismatch"], s["loaded_mismatch"], s["loaded"]))
    return s
