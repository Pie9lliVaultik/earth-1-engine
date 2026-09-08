"""Regression tests for review M02a/b/d — the config stamp verifies
loaded state and all frozen degrees of freedom; birth honours the
substrate flag. Fresh subprocesses are used where import order matters."""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FREEZE = {}
for _line in open(os.path.join(ROOT, "scripts", "env", "freeze09.env")):
    _line = _line.strip()
    if _line.startswith("export ") and "=" in _line:
        k, v = _line[len("export "):].split("=", 1)
        FREEZE[k.strip()] = v.strip()


def _run(py, env=None):
    e = {k: v for k, v in os.environ.items()
         if not k.startswith("EARTH1_")}
    e.update(env or {})
    e["PYTHONPATH"] = ROOT
    r = subprocess.run([sys.executable, "-c", py], capture_output=True,
                       text=True, env=e, cwd=ROOT)
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_env_file_is_source_of_truth():
    from earth1 import configstamp
    assert configstamp._SOURCE == "freeze09.env"
    assert set(FREEZE) == set(configstamp.FREEZE_09)  # all 11 covered
    assert len(configstamp.FREEZE_09) == 11


def test_import_then_env_fails_loaded_mismatch():
    # review M02a: modules imported under defaults, env set AFTER.
    out = _run(
        "import earth1.life, earth1.health\n"
        "import os\n"
        + "".join("os.environ[%r]=%r\n" % (k, v) for k, v in FREEZE.items())
        + "from earth1.configstamp import stamp\n"
        "import json; print(json.dumps(stamp()))\n")
    s = json.loads(out)
    assert s["is_freeze_09"] is False
    assert "hardship_mode" in (s["loaded_mismatch"] or [])
    assert "mortality_mode" in (s["loaded_mismatch"] or [])


def test_env_then_import_passes():
    out = _run(
        "from earth1.configstamp import stamp\n"
        "import json; print(json.dumps(stamp()))\n", env=FREEZE)
    s = json.loads(out)
    assert s["is_freeze_09"] is True, s
    assert s["mismatch"] is None and s["loaded_mismatch"] is None


def test_coefficient_drift_fails():
    # review M02b: a wrong numerical coefficient must fail the stamp.
    env = dict(FREEZE)
    env["EARTH1_WEATHER_SCALE"] = "1.0"   # 49x the frozen value
    out = _run(
        "from earth1.configstamp import stamp\n"
        "import json; print(json.dumps(stamp()))\n", env=env)
    s = json.loads(out)
    assert s["is_freeze_09"] is False
    assert "EARTH1_WEATHER_SCALE" in (s["mismatch"] or {})


def test_float_tolerance_not_string_equality():
    env = dict(FREEZE)
    env["EARTH1_LAYOFF_GAIN"] = "0.00280000000000"   # same number
    out = _run(
        "from earth1.configstamp import stamp\n"
        "import json; print(json.dumps(stamp()))\n", env=env)
    assert json.loads(out)["is_freeze_09"] is True


def test_assert_refuses_on_loaded_mismatch():
    out = _run(
        "import earth1.life\n"
        "import os\n"
        + "".join("os.environ[%r]=%r\n" % (k, v) for k, v in FREEZE.items())
        + "from earth1.configstamp import assert_freeze09\n"
        "try:\n"
        "    assert_freeze09(); print('PASSED')\n"
        "except SystemExit as e:\n"
        "    print('REFUSED')\n")
    assert "REFUSED" in out


def test_substrate_flag_defaults_birth(tmp_path):
    # review M02d: flag set -> default birth is the candidate substrate.
    py = ("from earth1.genesis import genesis\n"
          "c = genesis(2000, seed=7, min_per_country=5)\n"
          "print('sex' if getattr(c, 'sex', None) is not None"
          " else 'incumbent')\n")
    assert _run(py, env=FREEZE).strip() == "sex"
    no_flag = {k: v for k, v in FREEZE.items()
               if k != "EARTH1_SUBSTRATE_FLAG"}
    no_flag["EARTH1_INCOME_CALIBRATION"] = "off"   # keyed to substrate
    assert _run(py, env=no_flag).strip() == "incumbent"
