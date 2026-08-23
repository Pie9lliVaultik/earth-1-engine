"""ANSWER, LIVING — the canonical opinion readout of `alive.World`.

Phase 0.5 Program 3: the ONE supported answer path. It consumes the
living civilization's actual state — the expressed force field
(`effective_forces`, the readout contract) and the living
life/material/social features (`calibration.living_features`) — and
nothing else: no `earth1.tick`, no bare `Civilization`, no
`LivingWorld`, no second ontology.

Two verbs, deliberately distinct:
  readout(...)  — a non-perturbing measurement of what people would
                  express (benchmarks, dashboards, forecasts);
  ask(...)      — the act of ASKING, which changes them (observer.py:
                  crystallisation + instantiation) and is itself an
                  event in the world's memory.

Calibration status is carried in every result: per-question weight
calibration on the living stack is Benchmark A (Phase 1). Until it
lands, numbers are UNCALIBRATED structural readouts — honest about
what they are, never served as validated answers.
"""
from __future__ import annotations

import numpy as np

from earth1.types import Force, NUM_FORCES

CALIBRATION_STATUS = "UNCALIBRATED — Benchmark A (Phase 1) pending"


def _provenance(w) -> dict:
    from earth1.alive import PHYSICS_VERSION
    from earth1.persistence import world_hash
    return {"physics_version": PHYSICS_VERSION,
            "world_hash": world_hash(w),
            "world_day": int(w.day),
            "population": int(w.civ.n),
            "alive": int(w.health.alive.sum()),
            "calibration": CALIBRATION_STATUS,
            "view": "effective_forces (expression/readout contract)"}


def stance(w, weights, who=None) -> np.ndarray:
    """The observer's stance construction (observer.py), non-mutating,
    on the EXPRESSED force field: clip(F_eff · w / Σ|w|, 0, 1)."""
    from earth1.alive import effective_forces
    wv = np.asarray(weights, dtype=float)
    if wv.shape != (NUM_FORCES,):
        raise ValueError("question weights must be an 8-force vector")
    F = np.asarray(effective_forces(w))
    if who is None:
        who = np.flatnonzero(w.health.alive)
    return np.clip(F[who] @ wv / max(np.abs(wv).sum(), 1e-9), 0.0, 1.0)


def readout(w, weights, *, question_id: str = "", text: str = "",
            by_country: bool = True, cohorts: bool = True) -> dict:
    """Non-perturbing population readout of one question."""
    from earth1.genesis import GENESIS_COUNTRIES
    alive_idx = np.flatnonzero(w.health.alive)
    s = stance(w, weights, alive_idx)
    out = {"question_id": question_id, "text": text,
           "yes_pct": float(s.mean()),
           "frac_yes": float((s >= 0.5).mean()),
           "n": int(alive_idx.size),
           "provenance": _provenance(w)}
    if by_country:
        c = w.civ.country[alive_idx]
        res = {}
        for ci in np.unique(c):
            m = c == ci
            if m.sum() >= 30:
                res[GENESIS_COUNTRIES[int(ci)]["iso2"]] = {
                    "yes_pct": float(s[m].mean()),
                    "frac_yes": float((s[m] >= 0.5).mean()),
                    "n": int(m.sum())}
        out["by_country"] = res
    if cohorts:
        life = w.life
        yrs = w.civ.age[alive_idx] * 100.0
        groups = {
            "low income": w.civ.income[alive_idx] == 0,
            "middle income": w.civ.income[alive_idx] == 1,
            "high income": w.civ.income[alive_idx] == 2,
            "under 30": yrs < 30, "30 to 55": (yrs >= 30) & (yrs < 55),
            "over 55": yrs >= 55,
            "urban": w.civ.urban[alive_idx].astype(bool),
            "rural": ~w.civ.urban[alive_idx].astype(bool),
            "employed": life.employed[alive_idx],
            "unemployed (in labour force)":
                (~life.employed[alive_idx]) & life.in_lf[alive_idx],
            "deprived (>0.5)": life.deprivation[alive_idx] > 0.5,
        }
        out["by_cohort"] = {k: {"yes_pct": float(s[m].mean()),
                                "n": int(m.sum())}
                            for k, m in groups.items() if m.sum() >= 30}
    return out


def answer_question(w, q) -> dict:
    """Readout of a registered BenchmarkQuestion (benchmark_questions)."""
    r = readout(w, q.weights, question_id=q.id, text=q.text)
    r["lens"] = getattr(q, "lens", None)
    r["baseline"] = float(getattr(q, "baseline", float("nan")))
    if getattr(q, "global_target", None) is not None:
        r["global_target"] = float(q.global_target)
        r["global_error_uncalibrated"] = float(
            abs(r["yes_pct"] - q.global_target))
    return r


def ask(w, who, weights, day=None) -> dict:
    """The perturbing act of asking — delegates to the canonical
    observer (crystallisation; recorded in the chronicle)."""
    from earth1.observer import ask as _ask
    return _ask(w.civ, np.asarray(who), np.asarray(weights, dtype=float),
                chronicle=w.chronicle,
                day=float(w.day if day is None else day))
