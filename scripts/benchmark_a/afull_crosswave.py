"""A-FULL-1 task (v) — cross-wave deltas (WVS-6 -> WVS-7; Pew wave-pair).

Protocol (campaign A-FULL-1, measurement only): score Earth-1's implied
W6->W7 delta against a no-change baseline and a linear-trend baseline on
overlapping items/countries; metrics = sign agreement % + delta MAE (pp).
Pew wave-pair likewise IF a second Pew wave is on disk.

WHAT IS AND IS NOT WELL-DEFINED (design decisions, resolved 2026-08-31):

1. EARTH-1 ARM: NOT_RUN. The A-FULL-1 candidate engine (earth1.alive
   birth_world + live_one_day, substrate c2plus_v1, frozen A-v2 harness
   scripts/benchmark_a/run_v2.py) has no wave-6-conditioned initial
   state: worlds are born from genesis calibrated to current-era
   targets, and the per-item ridge readouts are fit against WVS-7-era
   country targets with wave-7 MRP anchors. An "implied W6->W7 delta"
   is therefore undefined for the candidate without either (a) a
   wave-6-conditioned genesis, which does not exist, or (b) reusing
   wave-7-fitted readouts at both endpoints, which leaks the wave-7
   truth into the prediction. Per campaign instruction, NOT_RUN is
   preferred over inventing an unregistered protocol. (A legacy G5
   TEMPORAL harness, earth1/g5.py, implements calibrate-on-W6 /
   evolve / re-predict on the pre-"alive" physics stack
   (earth1.tick.world_tick); it is not the A-FULL-1 candidate
   substrate, so running it would not measure this campaign's
   configuration and it is not run here.)

2. WVS OBSERVED DELTAS + BASELINES: computed. The only W6/W7 paired
   data on disk is earth1/wvs_paired.py — 15 questions, per-country
   aggregates hand-compiled from published findings, with an explicit
   must-verify provenance caveat (no WVS-6 microdata exists on either
   box; the prime duckdb is wave-7 only). Baselines are well-defined
   on that data and are computed here, clearly caveated:
     - no_change: predicted delta = 0 for every (question, country).
       Its sign agreement is degenerate by construction (sign(0) never
       matches a nonzero observed sign); reported as 0% with a note.
     - linear_trend_w5: per (question, country) with WVS-5 coverage
       (earth1/wvs_wave5.py), rate-normalised by fieldwork years:
       pred = (W6-W5)/(y6-y5) * (y7-y6), clamped so W6+pred stays in
       [0,1]. W5 covers 26 of the 37 W6/W7 countries.
   Estate status is BASELINES_ONLY (not RUN): no model arm, and the
   ground truth carries the provenance caveat.

3. PEW ESTATE: NOT_RUN, verified at runtime — no second Pew wave is on
   disk (data/goqa_full.json carries no wave/year metadata so it cannot
   be split into waves; data_roles.json entry pew2019_judge is
   PENDING_FETCH and role HOLDOUT, i.e. untouchable even if fetched).

The script performs NO network access, NO simulation, and never opens
data/goqa_judge_split.json or any HOLDOUT/PROSPECTIVE artifact. It
exits 0 on NOT_RUN estates; nonzero only on selftest failure or an
unwritable output path.

Usage (on prime, inside /opt/earth1, or locally from the repo):
    EARTH1_AFULL_OUT=/path/to/out .venv/bin/python \
        scripts/benchmark_a/afull_crosswave.py            # writes crosswave.json
    python scripts/benchmark_a/afull_crosswave.py --selftest
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import numpy as np  # noqa: E402

from earth1.benchmark_a.scoring import (  # noqa: E402
    bootstrap_ci,
    delta_mae_pp,
    paired_bootstrap_diff_ci,
)

# Sign threshold matches the 0.5pp "no direction to get right" convention
# of earth1.benchmark_a.scoring.gradient_direction_pct.
SIGN_THRESHOLD = 0.005

PROVENANCE_CAVEAT = (
    "W5/W6/W7 values are best-effort estimates hand-compiled from published "
    "WVS aggregate findings (earth1/wvs_paired.py, earth1/wvs_wave5.py); they "
    "MUST be verified against the official database at worldvaluessurvey.org "
    "before any result built on them is published externally. No WVS-6 "
    "microdata exists on disk."
)

EARTH1_NOT_RUN_REASON = (
    "Engine has no wave-6 initial condition; implied delta undefined. The "
    "A-FULL-1 candidate (earth1.alive birth_world + live_one_day, substrate "
    "c2plus_v1, frozen A-v2 harness run_v2.py) is born from genesis "
    "calibrated to current-era targets and its ridge readouts are fit on "
    "WVS-7 targets with wave-7 MRP anchors; a W6->W7 delta would require "
    "either a nonexistent wave-6-conditioned genesis or reusing wave-7-fitted "
    "readouts at both endpoints (leaks wave-7 truth). NOT_RUN preferred over "
    "an unregistered protocol. Legacy earth1/g5.py TEMPORAL harness targets "
    "the pre-'alive' physics stack and is not the candidate; not run."
)


# ── metric primitives ───────────────────────────────────────────────


def sign_agreement_pct(pred_delta, true_delta, threshold: float = SIGN_THRESHOLD):
    """Share (%) of pairs whose predicted delta sign equals the observed
    delta sign, among pairs with |observed delta| >= threshold.
    Returns (pct_or_None, n_decided, n_excluded)."""
    p = np.asarray(pred_delta, float)
    t = np.asarray(true_delta, float)
    m = np.abs(t) >= threshold
    n_decided = int(m.sum())
    n_excluded = int(t.size - n_decided)
    if n_decided == 0:
        return None, 0, n_excluded
    pct = float(np.mean(np.sign(p[m]) == np.sign(t[m])) * 100.0)
    return pct, n_decided, n_excluded


def linear_trend_delta(w5: float, w6: float, y5: int, y6: int, y7: int):
    """A6.1-style rate-normalised linear extrapolation of the W6->W7 delta
    from the observed W5->W6 change; clamps so the implied W7 level stays
    in [0,1]. Returns (pred_delta, clamped: bool)."""
    if y6 <= y5 or y7 <= y6:
        raise ValueError("fieldwork years must be strictly increasing")
    rate = (w6 - w5) / float(y6 - y5)
    raw = rate * float(y7 - y6)
    lvl = min(1.0, max(0.0, w6 + raw))
    pred = lvl - w6
    return float(pred), bool(abs(pred - raw) > 1e-12)


def _nan_to_none(x):
    if x is None:
        return None
    x = float(x)
    return None if (x != x) else x


def score_arm(pred, true):
    """delta MAE (pp) with bootstrap CI over per-pair absolute errors, plus
    sign agreement. pred/true are aligned lists of deltas (proportions)."""
    pred = np.asarray(pred, float)
    true = np.asarray(true, float)
    abs_err_pp = np.abs(pred - true) * 100.0
    mean, lo, hi = bootstrap_ci(abs_err_pp, n_boot=2000, seed=0)
    sa, n_dec, n_exc = sign_agreement_pct(pred, true)
    return {
        "n_pairs": int(true.size),
        "delta_mae_pp": _nan_to_none(delta_mae_pp(pred, true)),
        "delta_mae_pp_ci95": [_nan_to_none(lo), _nan_to_none(hi)],
        "sign_agreement_pct": _nan_to_none(sa),
        "sign_n_decided": n_dec,
        "sign_n_excluded_below_threshold": n_exc,
    }


# ── WVS estate ──────────────────────────────────────────────────────


def observed_wvs_pairs():
    """[(qid, iso2, w6, w7, delta)] over every overlapping (question,
    country) pair in earth1/wvs_paired.py."""
    from earth1.wvs_paired import WVS_PAIRED

    out = []
    for q in WVS_PAIRED:
        for c in q.overlapping_countries:
            out.append((q.id, c, float(q.wave6[c]), float(q.wave7[c]),
                        float(q.wave7[c]) - float(q.wave6[c])))
    return out


def _wvs6_microdata_on_disk():
    """Runtime check: is any WVS-6 microdata file on disk? (Expected: no.)"""
    checked = []
    pats = [
        str(REPO / "data" / "**" / "*[Ww][Vv][Ss]*6*"),
        "/opt/earth1-data/**/*[Ww][Vv][Ss]*6*",
    ]
    hits = []
    for p in pats:
        checked.append(p)
        try:
            hits += [h for h in glob.glob(p, recursive=True)
                     if Path(h).is_file() and "wave7" not in h and "w7" not in h]
        except OSError:
            pass
    return sorted(set(hits)), checked


def build_wvs_estate():
    from earth1 import wvs_paired, wvs_wave5
    from earth1.wvs_wave5 import W5_YEARS, W6_YEARS, W7_YEARS, WAVE5

    pairs = observed_wvs_pairs()
    true_all = [d for (_, _, _, _, d) in pairs]

    # no-change baseline over the full overlap
    no_change = score_arm(np.zeros(len(pairs)), true_all)
    no_change["note"] = (
        "predicts zero delta for every pair; sign agreement is degenerate "
        "by construction (sign(0) never matches a nonzero observed sign)"
    )

    # linear-trend baseline over the W5-covered subset
    lt_idx, lt_pred, n_clamped = [], [], 0
    for i, (qid, c, w6, _w7, _d) in enumerate(pairs):
        w5 = WAVE5.get(qid, {}).get(c)
        if w5 is None or c not in W5_YEARS or c not in W6_YEARS or c not in W7_YEARS:
            continue
        pred, clamped = linear_trend_delta(w5, w6, W5_YEARS[c], W6_YEARS[c], W7_YEARS[c])
        lt_idx.append(i)
        lt_pred.append(pred)
        n_clamped += int(clamped)
    lt_true = [pairs[i][4] for i in lt_idx]
    linear_trend = score_arm(lt_pred, lt_true)
    linear_trend["n_clamped_to_unit_interval"] = n_clamped
    linear_trend["note"] = (
        "pred = (W6-W5)/(y6-y5) * (y7-y6) per (question, country), fieldwork "
        "years from earth1/wvs_wave5.py; scored only on the W5-covered subset"
    )

    # head-to-head on the common (W5-covered) subset, paired bootstrap
    nc_err = np.abs(np.zeros(len(lt_idx)) - np.asarray(lt_true)) * 100.0
    lt_err = np.abs(np.asarray(lt_pred) - np.asarray(lt_true)) * 100.0
    if len(lt_idx):
        mean_diff, lo, hi = paired_bootstrap_diff_ci(nc_err, lt_err, n_boot=2000, seed=0)
    else:
        mean_diff = lo = hi = float("nan")
    head_to_head = {
        "subset": "pairs with W5 coverage",
        "n_pairs": len(lt_idx),
        "no_change_delta_mae_pp": _nan_to_none(float(nc_err.mean()) if len(lt_idx) else None),
        "linear_trend_delta_mae_pp": _nan_to_none(float(lt_err.mean()) if len(lt_idx) else None),
        "mae_diff_pp_no_change_minus_linear_trend": _nan_to_none(mean_diff),
        "mae_diff_ci95": [_nan_to_none(lo), _nan_to_none(hi)],
        "linear_trend_better_ci_excludes_0": bool(lo == lo and lo > 0),
    }

    # per-question observed summary
    per_q = {}
    for qid in sorted({p[0] for p in pairs}):
        d = np.asarray([p[4] for p in pairs if p[0] == qid])
        per_q[qid] = {
            "n_countries": int(d.size),
            "mean_delta_pp": round(float(d.mean()) * 100.0, 3),
            "mean_abs_delta_pp": round(float(np.abs(d).mean()) * 100.0, 3),
        }

    micro_hits, micro_checked = _wvs6_microdata_on_disk()
    return {
        "status": "BASELINES_ONLY",
        "status_note": (
            "observed deltas and the two registered baselines are computed; "
            "the Earth-1 arm is NOT_RUN, so no model-vs-baseline gate exists"
        ),
        "data_source": {
            "paired_module": str(Path(wvs_paired.__file__).resolve()),
            "wave5_module": str(Path(wvs_wave5.__file__).resolve()),
            "n_questions": len(per_q),
            "provenance_caveat": PROVENANCE_CAVEAT,
            "wvs6_microdata_on_disk": bool(micro_hits),
            "wvs6_microdata_hits": micro_hits,
            "wvs6_microdata_paths_checked": micro_checked,
        },
        "observed": {
            "n_pairs": len(pairs),
            "mean_abs_delta_pp": round(float(np.abs(true_all).mean()) * 100.0, 3),
            "per_question": per_q,
        },
        "arms": {
            "earth1": {"status": "NOT_RUN", "reason": EARTH1_NOT_RUN_REASON},
            "no_change": no_change,
            "linear_trend_w5": linear_trend,
        },
        "baseline_head_to_head": head_to_head,
        "gate": None,
        "publishable": False,
    }


# ── Pew estate ──────────────────────────────────────────────────────


def build_pew_estate():
    checks = {}

    roles_path = REPO / "data" / "data_roles.json"
    try:
        entry = json.load(open(roles_path))["entries"].get("pew2019_judge", {})
        checks["pew2019_judge"] = {
            "path": entry.get("path"),
            "role": entry.get("role"),
            "on_disk": bool(entry.get("path")
                            and entry.get("path") != "PENDING_FETCH"
                            and Path(entry["path"]).exists()),
        }
    except (OSError, KeyError, ValueError) as e:  # pragma: no cover
        checks["pew2019_judge"] = {"error": str(e)}

    goqa_path = REPO / "data" / "goqa_full.json"
    wave_keys = set()
    if goqa_path.exists():
        rows = json.load(open(goqa_path)).get("rows", [])
        keys = set()
        for r in rows[:50]:
            keys |= set(r.keys())
        wave_keys = {k for k in keys if any(s in k.lower() for s in ("wave", "year", "date"))}
        checks["goqa_full"] = {
            "on_disk": True,
            "row_keys_sampled": sorted(keys),
            "wave_or_year_keys": sorted(wave_keys),
        }
    else:
        checks["goqa_full"] = {"on_disk": False}

    hits = []
    for pat in (str(REPO / "data" / "**" / "*[Pp]ew*"), "/opt/earth1-data/**/*[Pp]ew*"):
        try:
            hits += [h for h in glob.glob(pat, recursive=True) if Path(h).is_file()]
        except OSError:
            pass
    checks["pew_named_files_on_disk"] = sorted(set(hits))

    reasons = []
    if not wave_keys:
        reasons.append(
            "the only Pew-frame data on disk (data/goqa_full.json via GOQA) "
            "carries no wave/year metadata, so it cannot be split into two waves"
        )
    if checks.get("pew2019_judge", {}).get("role") == "HOLDOUT":
        reasons.append(
            "data_roles.json entry pew2019_judge is role HOLDOUT "
            f"(path {checks['pew2019_judge'].get('path')}): untouchable for "
            "this measurement even if fetched"
        )
    if not checks["pew_named_files_on_disk"]:
        reasons.append("no other Pew wave file exists on disk")

    return {
        "status": "NOT_RUN",
        "reason": "no second Pew wave available on disk: " + "; ".join(reasons),
        "checks": checks,
        "arms": None,
        "gate": None,
    }


# ── artifact ────────────────────────────────────────────────────────


def build_artifact():
    return {
        "task": "v_cross_wave",
        "campaign": "A-FULL-1",
        "created": datetime.datetime.now(datetime.timezone.utc)
                   .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "script": "scripts/benchmark_a/afull_crosswave.py",
        "protocol": (
            "WVS-6 -> WVS-7 deltas on overlapping items/countries; score the "
            "Earth-1 implied delta vs no-change and linear-trend baselines: "
            "sign agreement % (|observed delta| >= 0.5pp) + delta MAE (pp). "
            "Pew wave-pair likewise if a second wave is on disk."
        ),
        "sign_threshold": SIGN_THRESHOLD,
        "estates": {
            "wvs_w6_w7": build_wvs_estate(),
            "pew_wave_pair": build_pew_estate(),
        },
        "verdict": (
            "Earth-1 arm NOT_RUN on both estates (WVS: engine has no wave-6 "
            "initial condition, implied delta undefined; Pew: no second wave "
            "on disk). WVS observed deltas and both baselines computed on the "
            "hand-compiled paired aggregates, provenance-caveated and not "
            "publishable without verification against the official WVS "
            "database. No gate is defined."
        ),
    }


# ── selftest ────────────────────────────────────────────────────────


def selftest() -> int:
    fails = []

    def check(name, cond):
        if not cond:
            fails.append(name)
            print(f"  FAIL {name}")
        else:
            print(f"  ok   {name}")

    # delta MAE
    check("delta_mae_pp basic",
          abs(delta_mae_pp([0.1, -0.1], [0.2, -0.3]) - 15.0) < 1e-9)
    check("delta_mae_pp zero", delta_mae_pp([0.2], [0.2]) == 0.0)

    # sign agreement
    sa, nd, ne = sign_agreement_pct([0.1, -0.1, 0.1], [0.2, -0.3, -0.4])
    check("sign agreement 2/3", abs(sa - 200.0 / 3.0) < 1e-9 and nd == 3 and ne == 0)
    sa, nd, ne = sign_agreement_pct([0.1, 0.1], [0.004, 0.2])
    check("threshold excludes |d|<0.5pp", nd == 1 and ne == 1 and sa == 100.0)
    sa, nd, ne = sign_agreement_pct([0.0, 0.0], [0.2, -0.2])
    check("no-change degenerate sign = 0%", sa == 0.0 and nd == 2)
    sa, nd, ne = sign_agreement_pct([0.1], [0.001])
    check("all-excluded returns None", sa is None and nd == 0 and ne == 1)

    # linear trend
    pred, clamped = linear_trend_delta(0.20, 0.30, 2006, 2011, 2018)
    check("linear trend rate-normalised",
          abs(pred - 0.14) < 1e-12 and not clamped)
    pred, clamped = linear_trend_delta(0.85, 0.95, 2006, 2011, 2018)
    check("linear trend clamps at 1.0",
          abs(pred - 0.05) < 1e-12 and clamped)
    pred, clamped = linear_trend_delta(0.30, 0.20, 2006, 2011, 2018)
    check("linear trend downward + clamp at 0.0",
          abs(pred - (-0.14)) < 1e-12 and not clamped
          and linear_trend_delta(0.30, 0.05, 2006, 2011, 2018) == (-0.05, True))

    # score_arm shape and consistency
    s = score_arm([0.0, 0.0], [0.1, -0.1])
    check("score_arm no-change MAE",
          abs(s["delta_mae_pp"] - 10.0) < 1e-9 and s["n_pairs"] == 2
          and s["sign_agreement_pct"] == 0.0)

    # estate builders (pure data, no simulation)
    wvs = build_wvs_estate()
    check("wvs status BASELINES_ONLY", wvs["status"] == "BASELINES_ONLY")
    check("wvs earth1 NOT_RUN", wvs["arms"]["earth1"]["status"] == "NOT_RUN")
    check("wvs 15 questions", wvs["data_source"]["n_questions"] == 15)
    n_pairs = wvs["observed"]["n_pairs"]
    check("wvs pair accounting",
          n_pairs == sum(q["n_countries"]
                         for q in wvs["observed"]["per_question"].values())
          and wvs["arms"]["no_change"]["n_pairs"] == n_pairs
          and 0 < wvs["arms"]["linear_trend_w5"]["n_pairs"] <= n_pairs)
    check("wvs no-change sign degenerate",
          wvs["arms"]["no_change"]["sign_agreement_pct"] == 0.0)
    check("wvs gate is null", wvs["gate"] is None)

    pew = build_pew_estate()
    check("pew NOT_RUN with reason",
          pew["status"] == "NOT_RUN" and len(pew["reason"]) > 20)

    art = build_artifact()
    try:
        blob = json.dumps(art, indent=1, allow_nan=False)
        check("artifact strict-JSON serialisable", len(blob) > 1000)
    except ValueError as e:
        check(f"artifact strict-JSON serialisable ({e})", False)

    print(f"SELFTEST {'PASS' if not fails else 'FAIL'} "
          f"({len(fails)} failure(s))")
    return 0 if not fails else 1


# ── main ────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true",
                    help="run the delta / sign-agreement math selftest and exit")
    ap.add_argument("--out", default=None,
                    help="output directory (default: $EARTH1_AFULL_OUT)")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    out_dir = args.out or os.environ.get("EARTH1_AFULL_OUT")
    if not out_dir:
        print("ERROR: set EARTH1_AFULL_OUT or pass --out <dir>", file=sys.stderr)
        return 2
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    art = build_artifact()
    out_path = out_dir / "crosswave.json"
    with open(out_path, "w") as f:
        json.dump(art, f, indent=1, allow_nan=False)
        f.write("\n")

    wvs = art["estates"]["wvs_w6_w7"]
    print(f"wrote {out_path}")
    print(f"  wvs_w6_w7      status={wvs['status']} "
          f"pairs={wvs['observed']['n_pairs']} "
          f"earth1={wvs['arms']['earth1']['status']}")
    nc, lt = wvs["arms"]["no_change"], wvs["arms"]["linear_trend_w5"]
    print(f"    no_change       delta_mae_pp={nc['delta_mae_pp']:.3f} "
          f"sign={nc['sign_agreement_pct']}% (degenerate) n={nc['n_pairs']}")
    print(f"    linear_trend_w5 delta_mae_pp={lt['delta_mae_pp']:.3f} "
          f"sign={lt['sign_agreement_pct']:.1f}% n={lt['n_pairs']}")
    print(f"  pew_wave_pair  status={art['estates']['pew_wave_pair']['status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
