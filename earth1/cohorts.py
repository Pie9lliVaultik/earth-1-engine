"""POPULATION FRAME — owner-vocabulary cohorts onto the C2+ joint.

The judgment call this module exists for: a model owner writes
"budget-conscious students", and Earth-1 must turn that into a claim
about humanity — a weight over real people — rather than let the owner
declare one.

HOW, and why not an LLM: the engine runtime is LLM-free by
architecture, so the mapping is a REGISTERED DETERMINISTIC LEXICON,
the same pattern as the ground ladder's extractor map. A phrase
contributes constraints on the joint's five axes; a cohort's weight is
the census-weighted mass of the joint cells satisfying them. Every
match is reported, so an owner can see exactly which words moved the
allocation and dispute them.

The joint (C2+ v2), per country, shape [2, 6, 3, 3, 2]:
    sex(2) x age_band(6) x education(3) x income(3) x urban(2)
Provenance is per country: 63 of 194 have WVS-measured education and
income margins; the other 131 pool them from income-tier donors. Age,
sex and urban margins are census-derived for all 194.

DEFECT-URBAN-INVERSION (found 2026-09-08, registered, NOT patched here
because physics is frozen at 0.9): joint axis index 0 carries the URBAN
mass, but draw_c2plus stores it as civ.urban == False. This module
works on the AXIS, so it is correct; any consumer reading the boolean
gets urban and rural swapped.
"""
import json
import os
import re

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FRAME = None
_TABLES = None

# axis order: sex, age_band, education, income, urban
AXES = ("sex", "age_band", "education", "income", "urban")

# ── THE REGISTERED LEXICON ──────────────────────────────────────────
# phrase -> {axis: [allowed indices]}. Multiple phrases intersect.
# Every entry is a modelling claim an owner can read and argue with.
LEXICON = {
    # income
    "budget": {"income": [0]}, "budget-conscious": {"income": [0]},
    "low income": {"income": [0]}, "low-income": {"income": [0]},
    "value seeking": {"income": [0]}, "price sensitive": {"income": [0]},
    "poor": {"income": [0]}, "working class": {"income": [0]},
    "middle income": {"income": [1]}, "middle-income": {"income": [1]},
    "middle class": {"income": [1]}, "mainstream": {"income": [1]},
    "affluent": {"income": [2]}, "wealthy": {"income": [2]},
    "high income": {"income": [2]}, "high-income": {"income": [2]},
    "luxury": {"income": [2]}, "premium": {"income": [2]},
    "hnw": {"income": [2]}, "upper class": {"income": [2]},
    # age
    "student": {"age_band": [0], "education": [1, 2]},
    "students": {"age_band": [0], "education": [1, 2]},
    "gen z": {"age_band": [0]}, "young": {"age_band": [0, 1]},
    "youth": {"age_band": [0]}, "18-24": {"age_band": [0]},
    "millennial": {"age_band": [1, 2]}, "25-34": {"age_band": [1]},
    "young adult": {"age_band": [0, 1]}, "35-44": {"age_band": [2]},
    "middle aged": {"age_band": [2, 3]}, "45-54": {"age_band": [3]},
    "gen x": {"age_band": [2, 3]}, "55-64": {"age_band": [4]},
    "boomer": {"age_band": [4, 5]}, "older": {"age_band": [4, 5]},
    "senior": {"age_band": [5]}, "seniors": {"age_band": [5]},
    "retired": {"age_band": [5]}, "elderly": {"age_band": [5]},
    "65+": {"age_band": [5]}, "working age": {"age_band": [0, 1, 2, 3, 4]},
    # education
    "graduate": {"education": [2]}, "graduates": {"education": [2]},
    "university": {"education": [2]}, "degree": {"education": [2]},
    "educated": {"education": [2]}, "highly educated": {"education": [2]},
    "college": {"education": [2]}, "professional": {"education": [2]},
    "secondary": {"education": [1]}, "less educated": {"education": [0]},
    "no degree": {"education": [0, 1]},
    # sex
    "women": {"sex": [1]}, "female": {"sex": [1]}, "woman": {"sex": [1]},
    "mothers": {"sex": [1]}, "men": {"sex": [0]}, "male": {"sex": [0]},
    "man": {"sex": [0]}, "fathers": {"sex": [0]},
    # settlement  (AXIS index — 0 is urban; see DEFECT-URBAN-INVERSION)
    "urban": {"urban": [0]}, "city": {"urban": [0]},
    "cities": {"urban": [0]}, "metropolitan": {"urban": [0]},
    "rural": {"urban": [1]}, "countryside": {"urban": [1]},
    "villages": {"urban": [1]}, "small town": {"urban": [1]},
}


def frame() -> dict:
    global _FRAME
    if _FRAME is None:
        _FRAME = json.load(open(os.path.join(
            _ROOT, "data", "population_frame.v1.json")))
    return _FRAME


def tables() -> dict:
    global _TABLES
    if _TABLES is None:
        name = os.environ.get("EARTH1_C2PLUS_TABLES",
                              "c2plus_tables_v2.json")
        _TABLES = json.load(open(os.path.join(_ROOT, "data", name)))
    return _TABLES


def parse_cohort(text: str) -> dict:
    """-> {"constraints": {axis: [idx]}, "matched": [phrase], "unmatched": bool}"""
    t = " " + (text or "").lower().replace("_", " ") + " "
    cons, matched = {}, []
    for phrase in sorted(LEXICON, key=len, reverse=True):
        # WORD BOUNDARIES, not substring: a naive `phrase in t` matched
        # "men" inside "women", intersected sex to empty, and silently
        # dropped the constraint (caught 2026-09-08 by the frame test).
        if re.search(r"(?<![a-z0-9])" + re.escape(phrase)
                     + r"(?![a-z0-9])", t):
            matched.append(phrase)
            for axis, idx in LEXICON[phrase].items():
                cons[axis] = (sorted(set(cons[axis]) & set(idx))
                              if axis in cons else list(idx))
    contradictions = sorted(a for a, v in cons.items() if not v)
    cons = {a: v for a, v in cons.items() if v}
    return {"constraints": cons, "matched": sorted(set(matched)),
            "contradictions": contradictions,
            "unmatched": not cons}


def _mask_for(constraints: dict) -> np.ndarray:
    """Boolean mask over the [2,6,3,3,2] joint."""
    shape = tuple(tables()["shape"])
    m = np.ones(shape, dtype=bool)
    for ai, axis in enumerate(AXES):
        allowed = constraints.get(axis)
        if not allowed:
            continue
        sel = np.zeros(shape[ai], dtype=bool)
        sel[list(allowed)] = True
        m &= sel.reshape([-1 if i == ai else 1 for i in range(len(shape))])
    return m


def population_frame(cohorts: list, country: str = None,
                     tier_size: int = 200000) -> dict:
    """THE endpoint body. cohorts: [{id, name, description?}]."""
    from earth1.genesis import GENESIS_COUNTRIES
    F, T = frame(), tables()
    surveyed = set(F["joint_provenance"]["survey_measured"])
    world_pop = F["world_population"]["value"]

    countries = [c for c in GENESIS_COUNTRIES
                 if (country is None or c["iso2"] == country)]
    if not countries:
        return {"error": "unknown country %r" % country,
                "known": len(GENESIS_COUNTRIES)}
    share_sum = sum(c["pop"] for c in countries)
    scope_pop = world_pop * share_sum

    alloc = []
    for co in cohorts:
        text = " ".join(str(x) for x in
                        (co.get("name"), co.get("description")) if x)
        p = parse_cohort(text)
        # A contradictory cohort ("young seniors") describes ZERO people.
        # Returning the unconstrained population with a flag would let a
        # caller that ignores the flag model it as all of humanity — the
        # exact failure this frame exists to prevent. Fail safe: zero.
        contradictory = bool(p["contradictions"])
        mask = (np.zeros(tuple(T["shape"]), dtype=bool) if contradictory
                else _mask_for(p["constraints"]))
        num = den = surv_num = 0.0
        for c in countries:
            t = np.asarray(T["tables"][c["iso2"]], dtype=np.float64)
            tot = float(t.sum())
            if tot <= 0:
                continue
            hit = float(t[mask].sum()) / tot          # within-country share
            w = c["pop"]                              # census weight
            num += hit * w
            den += w
            if c["iso2"] in surveyed:
                surv_num += hit * w
        weight = (num / den) if den else 0.0
        surv_share = (surv_num / num) if num > 0 else 0.0
        alloc.append({
            "cohortId": co.get("id"),
            "weight": round(weight, 6),
            "provenance": ("survey_measured" if surv_share >= 0.5
                           else "tier_fallback"),
            "surveyMeasuredShare": round(surv_share, 4),
            "peopleRepresented": int(round(weight * scope_pop)),
            "agentsAtTier": int(round(weight * tier_size)),
            "cellsMatched": int(mask.sum()),
            "cellsTotal": int(mask.size),
            "constraints": p["constraints"],
            "matchedVocabulary": p["matched"],
            "contradictoryAxes": p["contradictions"] or None,
            "unmatched": p["unmatched"],
            "note": ("contradictory vocabulary on %s — this describes zero "
                     "people; weight is 0, not the whole population"
                     % ", ".join(p["contradictions"]) if contradictory else
                     "no registered vocabulary matched — this cohort is the "
                     "whole scoped population, NOT a targeted segment"
                     if p["unmatched"] else None)})

    n_countries = len(countries)
    n_surv = sum(1 for c in countries if c["iso2"] in surveyed)
    limitations = ["no_adm1", "no_household_frame",
                   "no_ethnicity_or_religion_in_joint",
                   "sex_present_but_no_differentiated_mechanism"]
    if n_surv < n_countries:
        limitations.append("tier_fallback_joints_%d_of_%d"
                           % (n_countries - n_surv, n_countries))
    if any(a["unmatched"] for a in alloc):
        limitations.append("unmatched_cohort_vocabulary")
    if any(a["contradictoryAxes"] for a in alloc):
        limitations.append("contradictory_cohort_vocabulary")

    return {
        "allocation": alloc,
        "peoplePerAgent": round(scope_pop / max(tier_size, 1), 1),
        "effectiveN": int(tier_size),
        "scopePopulation": int(round(scope_pop)),
        "scope": {"country": country, "countries": n_countries,
                  "surveyMeasuredCountries": n_surv},
        "limitations": limitations,
        "frameProvenance": {
            "worldPopulation": F["world_population"],
            "jointAxes": F["joint_axes"]["order"],
            "jointShape": T["shape"],
            "lexiconEntries": len(LEXICON),
            "method": "census-weighted mass of C2+ joint cells matching a "
                      "registered deterministic vocabulary; no LLM in the "
                      "runtime path"},
    }
