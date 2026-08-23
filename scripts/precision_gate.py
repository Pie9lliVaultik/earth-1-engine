"""Evaluate the pre-registered f32 equivalence gate — 0.7.

Reads the study's members.json and applies
PRECISION_EQUIVALENCE_PROTOCOL_0_7.md mechanically: per-family
R_j = RMSE(paired f32-f64)/SD_seed(f64), TOST-style CI-within-margin,
Δ(scenario-control) equivalence, rankings/sign agreement at the
terminal horizon, at every horizon — and the float16-control must
FAIL the same machinery or the instrument is void.

    python3 scripts/precision_gate.py <run_dir>
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

POP = 4_000_000

# scalar -> (extractor over obs dict, RES resolution floor; 0 = none,
#            ("rel", x) = x relative to the f64 mean)
def _chan(name, i):
    return lambda o: (o[name][i] if o.get(name) is not None else None)


SCALARS = {}
for key, res in [
    ("alive", 0.001 * POP), ("cum_deaths", 0.001 * POP),
    ("cum_births", 0.001 * POP), ("cum_disease_deaths", 0.001 * POP),
    ("employment_rate", 0.005), ("destitute_share", 0.005),
    ("evicted_share", 0.005),
    ("wage_mean_employed", 0), ("tenure_mean_employed", 0),
    ("wealth_mean", 0), ("arrears_mean", 0),
    ("mental_mean", 0.01), ("physical_mean", 0.01),
    ("addiction_mean", 0.01), ("policy_net_mean", 0.01),
    ("firm_health_mean", 0.01), ("knowledge_stock_mean", 0),
    ("cum_migrants_rehomed", ("rel", 0.01)),
    ("cum_workers_rehomed", ("rel", 0.01)),
    ("cum_firms_failed", ("rel", 0.01)),
    ("cum_cascades", ("rel", 0.01)),
    ("memories_remembered", ("rel", 0.01)),
    ("friends_nnz", ("rel", 0.01)), ("weak_nnz", ("rel", 0.01)),
    ("friends_degree_mean", ("rel", 0.01)),
    ("weak_degree_mean", ("rel", 0.01)),
    ("friends_w_mean", 0.01), ("weak_w_mean", 0.01),
    ("friends_w_max", ("rel", 0.01)), ("weak_w_max", ("rel", 0.01)),
    ("cum_ties_strengthened", ("rel", 0.01)),
    ("cum_ties_weakened", ("rel", 0.01)),
    ("cum_ties_pruned", ("rel", 0.01)),
    ("cum_ties_rewired", ("rel", 0.01)),
]:
    SCALARS[key] = (lambda o, k=key: o.get(k), res)
for q in ("mean", "p10", "p50", "p90"):
    SCALARS[f"deprivation_{q}"] = (
        lambda o, q=q: o["deprivation"][q], 0.01)
for i in range(8):
    SCALARS[f"force_mean_{i}"] = (_chan("force_mean", i), 0.01)
    SCALARS[f"force_sd_{i}"] = (_chan("force_sd", i), 0.01)
    SCALARS[f"pole_share_{i}"] = (_chan("pole_share", i), 0.03)

R_LIMIT = 0.5
HORIZONS = ("3", "15", "30")


def _index(members, precisions):
    by = {}
    for m in members:
        if m["precision"] in precisions:
            by[(m["pair"], m["precision"], m["kind"])] = m
    return by


def _res(res, ref_mean):
    if isinstance(res, tuple):
        return abs(res[1] * ref_mean)
    return res


def _tost(diffs, margin):
    """Paired CI-within-margin. diffs: one value per pair."""
    d = np.asarray(diffs, dtype=np.float64)
    n = d.size
    m = d.mean()
    if n < 2:
        return abs(m) <= margin, m, margin
    se = d.std(ddof=1) / np.sqrt(n)
    tcrit = stats.t.ppf(0.975, n - 1)
    lo, hi = m - tcrit * se, m + tcrit * se
    return (lo >= -margin) and (hi <= margin), m, margin


def evaluate(members, alt_precision, pairs):
    by = _index(members, ("float64", alt_precision))
    rows = []
    breaches = []
    degenerate = []
    for h in HORIZONS:
        for name, (get, res) in SCALARS.items():
            # levels, paired by (pair, kind)
            d_pairs, x64_ctrl = [], []
            d64, d_alt = [], []
            ok = True
            for i in pairs:
                vals = {}
                for prec in ("float64", alt_precision):
                    for kind in ("control", "scenario"):
                        mm = by.get((i, prec, kind))
                        v = get(mm["horizons"][h]) if mm else None
                        if v is None:
                            ok = False
                        vals[(prec, kind)] = v
                if not ok:
                    break
                x64_ctrl.append(vals[("float64", "control")])
                d_pairs.append(np.mean(
                    [vals[(alt_precision, k)] - vals[("float64", k)]
                     for k in ("control", "scenario")]))
                d64.append(vals[("float64", "scenario")]
                           - vals[("float64", "control")])
                d_alt.append(vals[(alt_precision, "scenario")]
                             - vals[(alt_precision, "control")])
            if not ok:
                continue
            x64_ctrl = np.array(x64_ctrl, dtype=np.float64)
            sd_seed = float(x64_ctrl.std(ddof=1))
            rmse = float(np.sqrt(np.mean(np.square(d_pairs))))
            level_scale = float(np.abs(x64_ctrl).mean())
            resolved = _res(res, level_scale)
            # V2: deterministic-in-reference rows get a numerical
            # tolerance (~10x f32 eps), never a bit-identity demand
            if sd_seed == 0:
                tol = 1e-6 * max(1.0, level_scale)
                det_ok = rmse <= tol and (resolved <= 0
                                          or rmse <= resolved)
                rows.append({"horizon": h, "observable": name,
                             "deterministic": True,
                             "rmse": rmse, "tol": tol,
                             "pass": bool(det_ok)})
                if not det_ok:
                    breaches.append((h, name, "deterministic",
                                     f"rmse={rmse:.3g} > tol={tol:.3g}"))
                else:
                    degenerate.append((h, name,
                                       f"deterministic, rmse={rmse:.3g}"
                                       f" within tol"))
                continue
            r = rmse / sd_seed
            margin = max(sd_seed, resolved)
            t_ok, mdiff, marg = _tost(d_pairs, margin)
            lvl_ok = (r <= R_LIMIT) and t_ok
            # V2 effect gate: RES-floored denominator, and rows whose
            # true f64 effect is below scientific resolution are
            # UNINFORMATIVE — reported, not graded
            d64a = np.array(d64, dtype=np.float64)
            delta_diff = np.array(d_alt) - d64a
            sd_d64 = float(d64a.std(ddof=1))
            rmse_d = float(np.sqrt(np.mean(np.square(delta_diff))))
            informative = (resolved > 0
                           and abs(float(d64a.mean())) > resolved)
            if informative:
                floor = max(sd_d64, resolved)
                r_d = rmse_d / floor
                t2_ok, _, _ = _tost(delta_diff, floor)
                eff_ok = (r_d <= R_LIMIT) and t2_ok
            else:
                r_d, eff_ok = None, True     # ungraded
            rows.append({"horizon": h, "observable": name,
                         "R_level": round(r, 3),
                         "R_effect": (round(r_d, 3)
                                      if r_d is not None else None),
                         "effect_informative": bool(informative),
                         "mean_d64": float(d64a.mean()),
                         "mean_diff": float(mdiff),
                         "sd_seed": sd_seed,
                         "pass": bool(lvl_ok and eff_ok)})
            if not (lvl_ok and eff_ok):
                breaches.append((h, name, "level" if not lvl_ok
                                 else "effect",
                                 f"R={r:.3f} R_eff={r_d}"))
    # rankings + effect signs, terminal horizon
    rank_ok, sign_ok, rank_detail = _rankings(by, alt_precision, pairs)
    if not rank_ok:
        breaches.append(("30", "country_rankings", "rank", rank_detail))
    if not sign_ok:
        breaches.append(("30", "effect_signs", "sign", rank_detail))
    # V2 validity floor: the effect test needs something to test
    terminal = HORIZONS[-1]
    informative_rows = [r for r in rows
                        if r.get("horizon") == terminal
                        and r.get("effect_informative")]
    fams = {_family(r["observable"]) for r in informative_rows}
    valid = len(informative_rows) >= 15 and len(fams) >= 3
    return {"rows": rows, "breaches": breaches,
            "degenerate": degenerate,
            "rank_detail": rank_detail,
            "informative_terminal": len(informative_rows),
            "informative_families": sorted(fams),
            "instrument_identifiable": valid,
            "pass": (not breaches) and valid}


_FAMILIES = (
    ("demography", ("alive", "cum_deaths", "cum_births")),
    ("labour", ("employment_rate", "wage_", "tenure_")),
    ("material", ("wealth_", "deprivation", "destitute")),
    ("health", ("cum_disease", "mental_", "physical_", "addiction_")),
    ("housing", ("evicted", "arrears")),
    ("migration", ("cum_migrants", "cum_workers")),
    ("institutions", ("policy_", "firm_", "cum_firms")),
    ("forces", ("force_",)),
    ("opinion", ("pole_",)),
    ("network", ("friends_", "weak_", "cum_ties")),
    ("memory_knowledge", ("memories_", "knowledge_")),
    ("cascades", ("cum_cascades",)),
)


def _family(name):
    for fam, prefixes in _FAMILIES:
        if any(name.startswith(p) for p in prefixes):
            return fam
    return "other"


def _rankings(by, alt, pairs):
    terminal = HORIZONS[-1]
    rhos, agree, total = [], 0, 0
    for chan in ("country_deprivation", "country_fear"):
        for i in pairs:
            m64c = by.get((i, "float64", "control"))
            malc = by.get((i, alt, "control"))
            if not (m64c and malc):
                continue
            h64c = m64c["horizons"][terminal]
            halc = malc["horizons"][terminal]
            c64 = dict(zip(h64c["rank_countries"], h64c[chan]))
            cal = dict(zip(halc["rank_countries"], halc[chan]))
            common = [c for c in c64 if c in cal
                      and c64[c] is not None and cal[c] is not None]
            if len(common) >= 5:
                rho = stats.spearmanr(
                    [c64[c] for c in common],
                    [cal[c] for c in common])[0]
                rhos.append(float(rho))
    # effect-sign agreement where |Δ64| beats its own seed noise
    for chan in ("country_deprivation", "country_fear"):
        noise = {}
        effs = {}
        for i in pairs:
            m64c = by.get((i, "float64", "control"))
            m64s = by.get((i, "float64", "scenario"))
            malc = by.get((i, alt, "control"))
            mals = by.get((i, alt, "scenario"))
            if not all((m64c, m64s, malc, mals)):
                continue
            h = lambda m: m["horizons"][terminal]
            c64 = dict(zip(h(m64c)["rank_countries"], h(m64c)[chan]))
            s64 = dict(zip(h(m64s)["rank_countries"], h(m64s)[chan]))
            cal = dict(zip(h(malc)["rank_countries"], h(malc)[chan]))
            sal = dict(zip(h(mals)["rank_countries"], h(mals)[chan]))
            for c in c64:
                if c in s64 and c in cal and c in sal \
                        and None not in (c64[c], s64[c], cal[c], sal[c]):
                    noise.setdefault(c, []).append(s64[c] - c64[c])
                    effs.setdefault(c, []).append(
                        (s64[c] - c64[c], sal[c] - cal[c]))
        # V2: a cell qualifies iff |mean Δ64| beats both its own seed
        # noise and the 0.01 bounded-mean resolution; signs compared
        # on cell MEANS. Fewer than 10 qualifying cells across both
        # channels -> Spearman decides family 13 alone.
        for c, pairs_e in effs.items():
            d64s = np.array([d for d, _ in pairs_e])
            dals = np.array([d for _, d in pairs_e])
            sd = d64s.std(ddof=1) if d64s.size > 1 else 0.0
            if abs(d64s.mean()) > max(sd, 0.01):
                total += 1
                if np.sign(d64s.mean()) == np.sign(dals.mean()):
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
    f32 = evaluate(members, "float32", list(range(1, 9)))
    f16 = evaluate(members, "float16-control", [1, 2, 3])
    instrument_valid = not f16["pass"]      # the degraded control MUST fail
    verdict = {
        "protocol": "v2",
        "f32_pass": f32["pass"],
        "instrument_identifiable": f32["instrument_identifiable"],
        "informative_terminal_rows": f32["informative_terminal"],
        "informative_families": f32["informative_families"],
        "f16_control_rejected": instrument_valid,
        "certified": bool(f32["pass"] and instrument_valid),
        "f32_breaches": f32["breaches"],
        "f32_degenerate": f32["degenerate"],
        "f32_rank_detail": f32["rank_detail"],
        "f16_breach_count": len(f16["breaches"]),
        "f16_first_breaches": f16["breaches"][:8],
        "n_rows": len(f32["rows"]),
        "worst_R_level": max((r["R_level"] for r in f32["rows"]
                              if "R_level" in r), default=None),
        "worst_R_effect": max((r["R_effect"] for r in f32["rows"]
                               if r.get("R_effect") is not None),
                              default=None),
    }
    (run_dir / "gate_verdict.json").write_text(json.dumps(verdict,
                                                          indent=1))
    (run_dir / "gate_rows.json").write_text(json.dumps(f32["rows"],
                                                       indent=1))
    print(json.dumps({k: v for k, v in verdict.items()
                      if k not in ("f32_breaches",)}, indent=1))
    if verdict["f32_breaches"]:
        print("\nBREACHES:")
        for b in verdict["f32_breaches"][:20]:
            print("  ", b)
    state = "CERTIFIED" if verdict["certified"] else "REJECTED"
    instr = ("valid" if instrument_valid
             else "VOID - f16 control was accepted")
    print(f"\nGATE: {state} (instrument {instr})")
    return 0 if verdict["certified"] else 1


if __name__ == "__main__":
    sys.exit(main())
