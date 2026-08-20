"""V3 mechanical gate — ensemble consistency (0.7, founder Ruling A).

Applies PRECISION_EQUIVALENCE_PROTOCOL_0_7_V3.md as written: per-row
margins max(1.25 sigma_A, RES), family-horizon cell aggregation,
dispersion ratios, informative-effect classification, sign/ranking
criteria on ensemble means, and the two known-answer controls (B must
pass, C must fail) that validate the instrument itself.

    python3 scripts/precision_gate_v3.py <run_dir>
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.precision_gate import SCALARS, _family, _res  # noqa: E402

HORIZONS = ("3", "15", "30")
MARGIN_K = 1.25
DISP_LO, DISP_HI = 1.0 / 6.0, 6.0
DET_TOL_REL = 1e-6


def _arm_values(members, arm, get, h, kind):
    out = []
    for m in members:
        if m["arm"] == arm and m["kind"] == kind:
            v = get(m["horizons"][h])
            out.append(v)
    return out


def _arm_deltas(members, arm, get, h):
    by = {}
    for m in members:
        if m["arm"] == arm:
            by.setdefault(m["seed"], {})[m["kind"]] = \
                get(m["horizons"][h])
    out = []
    for seed, d in sorted(by.items()):
        if d.get("control") is not None and d.get("scenario") is not None:
            out.append(d["scenario"] - d["control"])
    return out


def evaluate(members, test_arm, ref_arm="A"):
    rows = []
    cells = {}          # (family, h) -> breach bookkeeping

    def note(fam, h, breach, severe):
        c = cells.setdefault((fam, h), {"rows": 0, "breach": 0,
                                        "severe": 0})
        c["rows"] += 1
        c["breach"] += int(breach)
        c["severe"] += int(severe)

    informative_terminal = set()
    for h in HORIZONS:
        for name, (get, res) in SCALARS.items():
            fam = _family(name)
            a = [v for v in _arm_values(members, ref_arm, get, h,
                                        "control") if v is not None]
            t = [v for v in _arm_values(members, test_arm, get, h,
                                        "control") if v is not None]
            if len(a) < 3 or len(t) < 3:
                continue
            a, t = np.array(a, float), np.array(t, float)
            mu_a, sd_a = a.mean(), a.std(ddof=1)
            mu_t, sd_t = t.mean(), t.std(ddof=1)
            resolved = _res(res, abs(mu_a))
            diff = abs(mu_t - mu_a)
            if sd_a == 0:
                tol = max(DET_TOL_REL * max(1.0, abs(mu_a)), resolved)
                breach = diff > tol
                severe = diff > 2 * tol
                rows.append({"h": h, "obs": name, "kind": "det",
                             "diff": diff, "tol": tol,
                             "pass": not breach})
                note(fam, h, breach, severe)
                continue
            margin = max(MARGIN_K * sd_a, resolved)
            breach = diff > margin
            severe = diff > 2 * margin
            disp_breach = False
            if sd_t > 0:
                ratio = (sd_t ** 2) / (sd_a ** 2)
                disp_breach = not (DISP_LO <= ratio <= DISP_HI)
            rows.append({"h": h, "obs": name, "kind": "level",
                         "z": round(float(diff / sd_a), 3),
                         "margin_sd": round(float(margin / sd_a), 3),
                         "pass": not (breach or disp_breach)})
            note(fam, h, breach or disp_breach, severe)

            # effect rows
            da = _arm_deltas(members, ref_arm, get, h)
            dt = _arm_deltas(members, test_arm, get, h)
            if len(da) >= 3 and len(dt) >= 3 and resolved > 0:
                da, dt = np.array(da, float), np.array(dt, float)
                if abs(da.mean()) > resolved:      # informative
                    if h == HORIZONS[-1]:
                        informative_terminal.add(name)
                    sd_da = da.std(ddof=1)
                    m_eff = max(MARGIN_K * sd_da, resolved)
                    d_eff = abs(dt.mean() - da.mean())
                    e_breach = d_eff > m_eff
                    e_severe = d_eff > 2 * m_eff
                    e_disp = False
                    if sd_da > 0 and dt.std(ddof=1) > 0:
                        er = (dt.std(ddof=1) ** 2) / (sd_da ** 2)
                        e_disp = not (DISP_LO <= er <= DISP_HI)
                    rows.append({"h": h, "obs": name, "kind": "effect",
                                 "d64_mean": float(da.mean()),
                                 "diff": float(d_eff),
                                 "margin": float(m_eff),
                                 "pass": not (e_breach or e_disp)})
                    note(fam, h, e_breach or e_disp, e_severe)

    failed_cells = []
    for (fam, h), c in sorted(cells.items()):
        frac = c["breach"] / max(c["rows"], 1)
        fail = (frac > 0.20 and c["breach"] >= 2) or c["severe"] > 0
        if fail:
            failed_cells.append((fam, h, c))

    rank_ok, sign_ok, rank_detail = _ens_rankings(members, test_arm,
                                                  ref_arm)
    fams = {_family(n) for n in informative_terminal}
    identifiable = (len(informative_terminal) >= 15 and len(fams) >= 3)
    passed = (not failed_cells) and rank_ok and sign_ok and identifiable
    return {"rows": rows, "failed_cells": failed_cells,
            "rank_detail": rank_detail, "rank_ok": rank_ok,
            "sign_ok": sign_ok,
            "informative_terminal": len(informative_terminal),
            "informative_families": sorted(fams),
            "instrument_identifiable": identifiable,
            "pass": bool(passed)}


def _ens_rankings(members, test_arm, ref_arm):
    terminal = HORIZONS[-1]
    rhos = []
    agree, total = 0, 0
    for chan in ("country_deprivation", "country_fear"):
        def chan_means(arm, kind):
            acc = {}
            for m in members:
                if m["arm"] != arm or m["kind"] != kind:
                    continue
                h = m["horizons"][terminal]
                for c, v in zip(h["rank_countries"], h[chan]):
                    if v is not None:
                        acc.setdefault(c, []).append(v)
            return {c: np.mean(v) for c, v in acc.items()
                    if len(v) >= 2}
        a_c = chan_means(ref_arm, "control")
        t_c = chan_means(test_arm, "control")
        common = sorted(set(a_c) & set(t_c))
        if len(common) >= 5:
            rho = stats.spearmanr([a_c[c] for c in common],
                                  [t_c[c] for c in common])[0]
            rhos.append(float(rho))
        # sign agreement of ensemble-mean effects
        a_s = chan_means(ref_arm, "scenario")
        t_s = chan_means(test_arm, "scenario")
        for c in common:
            if c not in a_s or c not in t_s:
                continue
            per_pair = []
            by = {}
            for m in members:
                if m["arm"] == ref_arm:
                    h = m["horizons"][terminal]
                    d = dict(zip(h["rank_countries"], h[chan]))
                    if c in d and d[c] is not None:
                        by.setdefault(m["seed"], {})[m["kind"]] = d[c]
            for seed, kk in by.items():
                if "control" in kk and "scenario" in kk:
                    per_pair.append(kk["scenario"] - kk["control"])
            if len(per_pair) < 2:
                continue
            sd = float(np.std(per_pair, ddof=1))
            mean_a = a_s[c] - a_c[c]
            if abs(mean_a) > max(sd, 0.01):
                total += 1
                if np.sign(mean_a) == np.sign(t_s[c] - t_c[c]):
                    agree += 1
    rho_min = min(rhos) if rhos else None
    share = agree / total if total else None
    detail = (f"spearman_min={rho_min}, qualifying_cells={total}, "
              f"sign_agree={share}")
    rank_ok = rho_min is not None and rho_min >= 0.9
    sign_ok = (total < 10) or (share is not None and share >= 0.9)
    return rank_ok, sign_ok, detail


def main():
    run_dir = Path(sys.argv[1])
    members = json.loads((run_dir / "members.json").read_text())
    b = evaluate(members, "B")        # known-answer PASS control
    c = evaluate(members, "C")        # known-answer FAIL control
    x = evaluate(members, "X")        # the candidate
    # C must fail ON CELLS (a validity-floor "failure" would not
    # demonstrate discrimination)
    instrument_valid = b["pass"] and len(c["failed_cells"]) > 0
    verdict = {
        "protocol": "v3-ensemble-consistency",
        "B_vs_A_pass (must be true)": b["pass"],
        "B_failed_cells": b["failed_cells"],
        "C_vs_A_pass (must be false)": c["pass"],
        "C_failed_cell_count": len(c["failed_cells"]),
        "instrument_valid": instrument_valid,
        "X_pass": x["pass"],
        "X_failed_cells": x["failed_cells"],
        "X_rank_detail": x["rank_detail"],
        "X_informative_terminal": x["informative_terminal"],
        "X_informative_families": x["informative_families"],
        "certified": bool(instrument_valid and x["pass"]),
    }
    (run_dir / "gate_verdict_v3.json").write_text(
        json.dumps(verdict, indent=1, default=str))
    (run_dir / "gate_rows_v3.json").write_text(
        json.dumps({"B": b["rows"], "X": x["rows"]}, indent=1,
                   default=str))
    print(json.dumps(verdict, indent=1, default=str))
    print(f"\nV3 GATE: "
          f"{'CERTIFIED' if verdict['certified'] else 'NOT CERTIFIED'}"
          f" (instrument {'valid' if instrument_valid else 'INVALID'})")
    return 0 if verdict["certified"] else 1


if __name__ == "__main__":
    sys.exit(main())
