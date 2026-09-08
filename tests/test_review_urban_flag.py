"""Review M01a — EARTH1_URBAN_AXIS_FIX flag gate (founder ruling pending).

The C2+ joint table carries the URBAN mass at axis index 0
(build_tables.py: m_urb = [urban%, 1 - urban%]), but the frozen-0.9
sampler stores urb = u.astype(bool), so civ.urban == True means RURAL
(DEFECT_URBAN_INVERSION.md; every country measures exactly 1 - census).
The fix is PREPARED behind EARTH1_URBAN_AXIS_FIX (default 'off') and
promotes only on the founder's v1.1 ruling
(ops/alive/cycles/URBAN_FIX_PREREG.md).

Asserted here:
  1. flag unset/off -> draw_c2plus is bitwise-identical to a fresh
     no-flag process (the frozen inversion, preserved exactly);
  2. flag off reproduces the original defect probe: urban share
     == 1 - census axis-0 mass (reviewer's urban_probe.py logic);
  3. flag on -> urban share matches census (JP ~0.92), only the boolean
     flips (sex/age/edu/income streams untouched).
"""
import json
import os
import subprocess
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from earth1.popsynth import _TABLE_FILE, _tables, draw_c2plus

TABLES = os.path.join(ROOT, "data", _TABLE_FILE)
pytestmark = pytest.mark.skipif(
    not os.path.exists(TABLES),
    reason="tables not built yet (prime artifact)")

N = 50_000
SEED = 42
ISO2 = ["JP", "IN"]          # two countries, exercised in ONE mixed draw


def _mixed_country():
    c = np.zeros(N, dtype=int)
    c[N // 2:] = 1
    return c


def _draw(monkeypatch, flag):
    if flag is None:
        monkeypatch.delenv("EARTH1_URBAN_AXIS_FIX", raising=False)
    else:
        monkeypatch.setenv("EARTH1_URBAN_AXIS_FIX", flag)
    return draw_c2plus(_mixed_country(), SEED, ISO2)


def _table_urban_share(iso):
    t = np.asarray(_tables()["tables"][iso], dtype=np.float64)
    return float(t[..., 0].sum() / t.sum())  # axis index 0 = urban mass


# ── 1. flag off: bitwise-equal to a fresh process that never saw the flag ──

def test_flag_off_bitwise_equal_to_fresh_no_flag_process(
        monkeypatch, tmp_path):
    out = tmp_path / "fresh.npz"
    script = (
        "import sys, numpy as np; sys.path.insert(0, %r); "
        "from earth1.popsynth import draw_c2plus; "
        "c = np.zeros(%d, dtype=int); c[%d:] = 1; "
        "s, a, e, i, u = draw_c2plus(c, %d, %r); "
        "np.savez(%r, sex=s, age_raw=a, edu=e, inc=i, urb=u)"
        % (ROOT, N, N // 2, SEED, ISO2, str(out)))
    env = {k: v for k, v in os.environ.items()
           if k != "EARTH1_URBAN_AXIS_FIX"}
    env["EARTH1_C2PLUS_TABLES"] = _TABLE_FILE   # same tables as this process
    subprocess.run([sys.executable, "-c", script], check=True, env=env,
                   cwd=ROOT)
    fresh = np.load(out)

    for flag in (None, "off"):                  # unset AND explicit 'off'
        sex, age_raw, edu, inc, urb = _draw(monkeypatch, flag)
        for name, got in (("sex", sex), ("age_raw", age_raw), ("edu", edu),
                          ("inc", inc), ("urb", urb)):
            assert got.tobytes() == fresh[name].tobytes(), \
                f"{name} not bit-identical with flag={flag!r}"


# ── 2. flag off reproduces the registered defect (reviewer's probe) ──

def test_flag_off_reproduces_inversion(monkeypatch):
    monkeypatch.delenv("EARTH1_URBAN_AXIS_FIX", raising=False)
    for iso in ("JP", "US", "IN", "NG"):
        urb = draw_c2plus(np.zeros(N, dtype=int), SEED, [iso])[-1]
        census = _table_urban_share(iso)
        assert abs(float(urb.mean()) - (1.0 - census)) < 0.01, \
            f"{iso}: frozen behaviour should be 1 - census"


# ── 3. flag on: boolean reads urban correctly; nothing else moves ──

def test_flag_on_jp_urban_share_matches_census(monkeypatch):
    monkeypatch.setenv("EARTH1_URBAN_AXIS_FIX", "on")
    urb = draw_c2plus(np.zeros(N, dtype=int), SEED, ["JP"])[-1]
    census = _table_urban_share("JP")           # 0.920 for JP
    assert abs(census - 0.920) < 0.005
    assert abs(float(urb.mean()) - census) < 0.01


def test_flag_on_flips_only_the_boolean(monkeypatch):
    off = _draw(monkeypatch, "off")
    on = _draw(monkeypatch, "on")
    for k, name in ((0, "sex"), (1, "age_raw"), (2, "edu"), (3, "inc")):
        assert on[k].tobytes() == off[k].tobytes(), \
            f"{name} must not move with the flag (same rng stream)"
    # axis has exactly two levels, so the fix is the exact complement
    assert np.array_equal(on[4], ~off[4])
