"""STRUCTURED CONSEQUENCE REPORT (founder ruling 2026-09-01).

The one output schema for every "what happens if X" (CONDITIONAL door
default) and for FORECAST branches on explain=true. Every line is
scenario minus null_branch control, CRN-paired per seed, with seed
sigma and a per-line calibration tier:

  CALIBRATED    observable has a green anchor gate AND the class has a
                fitted temperature
  UNCALIBRATED  observable green, class not yet calibrated
  ABSTAIN       |mean paired delta| < 2*sem across seeds — the line
                reads "no measurable effect", never a number
  KNOWN-DEFECT  wrong-signed channels from the B-DEV ledger (hope under
                economic shocks t=+2.1; econ-area migration t=-5.1),
                stamped until their mechanism cycles close

Headline: DETERMINISTIC template built strictly from CALIBRATED /
UNCALIBRATED lines (registered deviation from the ruling's "LLM writes
the summary": Earth-1's runtime is LLM-free; a product-layer LLM may
restyle the headline but every number it may use is already in the
table by construction).
"""
import copy
import json
import os

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SNAPSHOT_DAYS = (1, 7, 30, 90, 180)
GREEN_ANCHORS = {"unemployed", "destitute", "dead", "median_buffer",
                 "hungry"}
KNOWN_DEFECT = {"mean_hope": "hope miscoupling (B-DEV gfc t=+2.1 wrong sign)",
                "migrants": "migration sign under economic shocks (t=-5.1)"}
PERISHABLE = {"fear": "perishable", "desire": "perishable",
              "collective": "perishable", "economics": "perishable",
              "identity": "structural", "culture": "structural",
              "experience": "structural", "temperament": "structural"}
SECOND_ORDER = {
    "protest": [("crackdown", {"fear": 0.3, "collective": -0.2}),
                ("concession", {"fear": -0.2, "desire": 0.2,
                                "collective": 0.1})],
    "market_cascade": [("intervention", {"economics": 0.2, "fear": -0.2}),
                       ("contagion", {"fear": 0.3, "economics": -0.25})],
    "_default": [("escalates", {"fear": 0.2, "collective": 0.15}),
                 ("stabilizes", {"fear": -0.15, "desire": 0.1})],
}


def _run_pair(scenario, base_world, seed, horizon, fork_day=90):
    """One CRN-paired (scenario, null) run; returns per-snapshot state
    and the scenario world frozen at fork_day for ORDER-4 branching."""
    from earth1.alive import live_one_day
    from earth1.branch import apply, null_branch
    from earth1.consequences import protest_risk, snapshot
    from earth1.persistence import world_hash
    out = {}
    fork_state = None
    for arm, sc in (("scn", scenario), ("null", null_branch())):
        w = copy.deepcopy(base_world)
        rng = np.random.default_rng(977 * 41 + seed)
        apply(w, sc, rng)
        t0 = float(w.day)
        snaps, onsets, hot_days = {}, 0, 0
        seen = set()
        for d in range(1, horizon + 1):
            live_one_day(w, rng)
            ep = getattr(w.chronicle, "cascade_episode_active", None) or set()
            hot_days += sum(1 for k in ep if k[0] == "collective_surge")
            for r in (getattr(w.chronicle, "cascade_residues", None) or []):
                key = (r["rule"], float(r["day"]), int(r["loc"]))
                if key not in seen and r["day"] >= t0:
                    seen.add(key)
                    if r["rule"] == "collective_surge":
                        onsets += 1
            if d in SNAPSHOT_DAYS or d == horizon:
                s = snapshot(w)
                snaps[d] = {k: v for k, v in s.items()}
                snaps[d]["_forces"] = w.civ.forces[w.health.alive].mean(0)
                snaps[d]["_forces_by_c"] = _forces_by_country(w)
                snaps[d]["_protest_risk"] = float(protest_risk(w).sum())
                snaps[d]["_onsets_event"] = onsets
                snaps[d]["_hot_locality_days"] = hot_days
            if arm == "scn" and d == fork_day:
                fork_state = copy.deepcopy(w)
        out[arm] = {"snaps": snaps, "hash": world_hash(w)[:16]}
    return out, fork_state


def _forces_by_country(w, min_agents=200):
    from earth1.genesis import GENESIS_COUNTRY_CODES
    alive = w.health.alive
    out = {}
    for ci, iso in enumerate(GENESIS_COUNTRY_CODES):
        m = alive & (w.civ.country == ci)
        if m.sum() >= min_agents:
            out[iso] = w.civ.forces[m].mean(0)
    return out


def _line(name, deltas, unit, tier_hint, pop_scale=None):
    """Aggregate one observable's paired deltas across seeds."""
    a = np.array(deltas, dtype=float)
    if a.size == 0:
        return {"observable": name, "unit": unit, "tier": "ABSTAIN",
                "delta": None, "note": "no snapshot data"}
    mean = float(a.mean())
    sem = (float(a.std(ddof=1) / max(len(a) - 1, 1) ** 0.5)
           if len(a) > 1 else float("inf"))
    if mean == 0.0 and sem == 0.0:
        return {"observable": name, "unit": unit, "tier": "ABSTAIN",
                "delta": None, "note": "no effect (identically zero)"}
    if not np.isfinite(sem):
        sem = abs(mean)
    if name in KNOWN_DEFECT:
        tier = "KNOWN-DEFECT"
    elif abs(mean) < 2 * sem:
        tier = "ABSTAIN"
    else:
        tier = tier_hint
    row = {"observable": name, "unit": unit, "tier": tier,
           "note": KNOWN_DEFECT.get(name)}
    if tier != "ABSTAIN":
        row.update({"delta": round(mean, 5), "sem": round(sem, 5)})
        if pop_scale and unit == "agents":
            row["real_world_approx"] = f"~{mean * pop_scale / 1e6:+.1f}M people"
    else:
        row["delta"] = None
        row["note"] = row.get("note") or "no measurable effect"
    return row


MIN_SEEDS = int(os.environ.get("EARTH1_CQ_MIN_SEEDS", "8"))


def consequence_report(spec: dict, base_world, seeds, horizon=180,
                       class_calibrated=False) -> dict:
    """spec: {question_id, class, country?, scenario: Scenario}. Runs
    len(seeds) CRN pairs serially. For parallel workers use _run_pair
    per (scenario, seed) then build_from_runs."""
    assert len(seeds) >= MIN_SEEDS, (
        f"HARD RULE (founder 2026-09-01): no consequence report below "
        f"{MIN_SEEDS} seeds — at n=2 the sem is a guess and the floor "
        f"passes false-live lines. Got {len(seeds)}.")
    runs, fork_states = [], []
    for s in seeds:
        pair, fs = _run_pair(spec["scenario"], base_world, s, horizon)
        runs.append(pair)
        if fs is not None and len(fork_states) < 1:
            fork_states.append(fs)
    return build_from_runs(spec, runs, fork_states, seeds,
                           int(base_world.civ.n), float(base_world.day),
                           class_calibrated)


def build_from_runs(spec, runs, fork_states, seeds, base_pop, base_day,
                    class_calibrated=False) -> dict:
    from earth1.types import FORCE_KEYS
    pop_scale = 8.1e9 / max(base_pop, 1)
    tier_hint = "CALIBRATED" if class_calibrated else "UNCALIBRATED"

    def deltas(key, day, sub=None):
        out = []
        for r in runs:
            avail = sorted(r["scn"]["snaps"])
            use = day if day in r["scn"]["snaps"] else (
                max([d for d in avail if d <= day], default=avail[-1])
                if avail else None)
            if use is None:
                continue
            a, b = r["scn"]["snaps"].get(use), r["null"]["snaps"].get(use)
            if a is None or b is None:
                continue
            va, vb = a.get(key), b.get(key)
            if sub is not None:
                va, vb = va[sub], vb[sub]
            try:
                out.append(float(va) - float(vb))
            except (TypeError, ValueError):
                continue
        return out

    order1 = {"forces_global": [], "top_country_movers": []}
    for i, fk in enumerate(FORCE_KEYS):
        nm = fk.name.lower()
        row = _line(f"force_{nm}", deltas("_forces", 7, i), "force units",
                    tier_hint)
        row["perishability"] = PERISHABLE.get(nm, "structural")
        order1["forces_global"].append(row)
    movers = {}
    for r in runs:
        a = r["scn"]["snaps"].get(7, {}).get("_forces_by_c", {})
        b = r["null"]["snaps"].get(7, {}).get("_forces_by_c", {})
        for iso in set(a) & set(b):
            movers.setdefault(iso, []).append(
                float(np.linalg.norm(a[iso] - b[iso])))
    order1["top_country_movers"] = sorted(
        ({"country": k, "force_shift": round(float(np.mean(v)), 4)}
         for k, v in movers.items()), key=lambda r: -r["force_shift"])[:8]

    order2 = []
    for key, unit, green in (("unemployed", "agents", True),
                             ("destitute", "agents", True),
                             ("hungry", "agents", True),
                             ("evicted", "agents", False),
                             ("homeless", "agents", False),
                             ("dead", "agents", True),
                             ("median_buffer", "days of savings", True),
                             ("migrants", "agents", False),
                             ("mean_hope", "hope units", False)):
        th = tier_hint if green else "UNCALIBRATED"
        order2.append(_line(key, deltas(key, 90), unit, th, pop_scale))

    order3 = []
    order3.append(_line("protest_risk_sum", deltas("_protest_risk", 90),
                        "hot localities", tier_hint))
    order3.append(_line("unrest_intensity_hot_locality_days",
                        deltas("_hot_locality_days", 180),
                        "hot-locality-days", tier_hint))
    _oe = _line("collective_surge_onsets_event",
                deltas("_onsets_event", 180), "onset events", tier_hint)
    _oe["tier"] = "KNOWN-DEFECT"
    _oe["note"] = ("entry-count semantics: sustained-hot worlds under-"
                   "count cold-to-hot transitions (c-SHOCK VOID); use "
                   "unrest_intensity_hot_locality_days")
    order3.append(_oe)
    _legdays = [max([d for d in sorted(r["scn"]["snaps"]) if d <= 90],
                    default=None) for r in runs]
    order3.append(_line("legitimacy_mean",
                        [float(np.mean(r["scn"]["snaps"][dd]["legitimacy"])
                               - np.mean(r["null"]["snaps"][dd]["legitimacy"]))
                         for r, dd in zip(runs, _legdays) if dd],
                        "legitimacy units", tier_hint))
    order3.append(_line("memory_imprint_experience",
                        deltas("_forces", 180,
                               [f.name.lower() for f in FORCE_KEYS]
                               .index("experience")),
                        "force units at day 180", "UNCALIBRATED"))

    order4 = []
    forks = SECOND_ORDER.get(spec.get("class"), SECOND_ORDER["_default"])
    if fork_states:
        from earth1.branch import Scenario
        for name, forces in forks[:2]:
            sc = Scenario(id=f"fork:{name}", label=f"second-order {name}",
                          forces=forces, countries=None, firm_damage=0.0,
                          trade_shock=0.0, persists_days=45)
            pair, _ = _run_pair(sc, fork_states[0], seeds[0], 45,
                                fork_day=10 ** 9)
            f7 = _line("force_shift_d7",
                       [float(np.linalg.norm(
                           pair["scn"]["snaps"][7]["_forces"]
                           - pair["null"]["snaps"][7]["_forces"]))],
                       "force units", "UNCALIBRATED")
            u45 = pair["scn"]["snaps"].get(45, {}).get("unemployed")
            n45 = pair["null"]["snaps"].get(45, {}).get("unemployed")
            order4.append({
                "fork": name, "order1_force_shift": f7,
                "order2_unemployed_delta": (float(u45 - n45)
                                            if u45 is not None else None),
                "epistemics": "Reaction shares describe how the population "
                              "responds inside that world; they are not "
                              "probabilities that the world will occur."})

    # F1: geography from material headcount fields when the runs carry
    # them (post-F1 snapshots); otherwise the force-shift basis is
    # stamped so no reader mistakes it for hunger geography.
    geo_basis = None
    geo_rows = []
    from earth1.genesis import GENESIS_COUNTRY_CODES as _GCC
    for key in ("hungry_by_country", "destitute_by_country"):
        per_c = {}
        for r in runs:
            avail = sorted(r["scn"]["snaps"])
            use = 90 if 90 in r["scn"]["snaps"] else (avail[-1] if avail
                                                      else None)
            if use is None:
                continue
            a = r["scn"]["snaps"][use].get(key)
            b = r["null"]["snaps"][use].get(key)
            ppa = r["scn"]["snaps"][use].get("people_per_agent_by_country")
            if a is None or b is None or ppa is None:
                continue
            for ci in range(len(a)):
                per_c.setdefault(ci, []).append(
                    float((a[ci] - b[ci]) * ppa[ci]))
        if per_c:
            geo_basis = key
            for ci, ds in per_c.items():
                arr = np.array(ds)
                m_ = float(arr.mean())
                sem_ = (float(arr.std(ddof=1) / max(len(arr) - 1, 1) ** 0.5)
                        if len(arr) > 1 else float("inf"))
                if abs(m_) >= 2 * sem_ and m_ != 0.0:
                    geo_rows.append({"country": _GCC[ci],
                                     "delta_people": round(m_, 0),
                                     "sem": round(sem_, 0)})
            geo_rows.sort(key=lambda r_: -abs(r_["delta_people"]))
            break

    lines = order1["forces_global"] + order2 + order3
    counts = {}
    for r in lines:
        counts[r["tier"]] = counts.get(r["tier"], 0) + 1
    headline = []
    for r in sorted([x for x in lines if x["tier"] in
                     ("CALIBRATED", "UNCALIBRATED")
                     and x.get("delta") is not None],
                    key=lambda x: -abs(x.get("delta") or 0))[:5]:
        headline.append(f"{r['observable']}: {r['delta']:+g} {r['unit']}"
                        f" (±{r['sem']:g}, {r['tier']})")

    return {"order0": {"question_id": spec["question_id"],
                       "class": spec.get("class"),
                       "scenario_id": spec["scenario"].id,
                       "forces": spec["scenario"].forces,
                       "geography": spec["scenario"].countries or "global",
                       "ledger_cutoff_day": base_day,
                       "branch_hashes": [r["scn"]["hash"] for r in runs],
                       "seeds": list(seeds), "pop": base_pop},
            "headline": headline,
            "order1": order1, "order2": order2, "order3": order3,
            "order2_geography": {"basis": geo_basis or
                                 "force_shift (pre-F1 snapshots)",
                                 "top": geo_rows[:15]},
            "order4": order4,
            "tier_counts": counts}
