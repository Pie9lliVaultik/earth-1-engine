"""Serialization helpers — convert engine dataclasses to API dicts."""
from __future__ import annotations
from earth1.types import RunResult, CohortCell, Branch, CampAnatomy, Force, FORCE_NAMES, NUM_FORCES
import numpy as np


def _force_dict(arr: np.ndarray) -> dict:
    return {FORCE_NAMES[Force(i)]: float(arr[i]) for i in range(NUM_FORCES)}


def _camp_dict(camp: CampAnatomy | None) -> dict | None:
    if camp is None:
        return None
    return {
        "size": camp.size,
        "mean_stance": round(camp.mean_stance, 4),
        "dominant": camp.dominant.name.lower(),
        "contrib": _force_dict(camp.contrib),
    }


def serialize_result(r: RunResult) -> dict:
    return {
        "question_id": r.question.id,
        "question_text": r.question.text,
        "n": r.n,
        "yes_pct": round(r.yes_pct, 4),
        "frac_yes": round(r.frac_yes, 4),
        "regime": r.regime,
        "final_distribution": r.final_distribution.tolist() if isinstance(r.final_distribution, np.ndarray) else r.final_distribution,
        "distribution_by_layer": [
            d.tolist() if isinstance(d, np.ndarray) else d
            for d in r.distribution_by_layer
        ],
        "force_anatomy": _force_dict(r.force_anatomy),
        "dominant": r.dominant.name.lower(),
        "conviction": round(r.conviction, 4),
        "fragility": round(r.fragility, 4),
        "camps": {
            "yes": _camp_dict(r.camps.get("yes")),
            "no": _camp_dict(r.camps.get("no")),
        },
        "params": r.params,
        "abstained": r.abstained,
    }


def serialize_cohort(c: CohortCell) -> dict:
    return {
        "key": c.key,
        "label": c.label,
        "n": c.n,
        "yes_pct": round(c.yes_pct, 4),
        "dominant": c.dominant.name.lower(),
    }


def serialize_branch(b: Branch) -> dict:
    return {
        "id": b.id,
        "label": b.label,
        "yes_pct": round(b.yes_pct, 4),
        "dominant": b.dominant.name.lower(),
        "fragility": round(b.fragility, 4),
        "contortion": round(b.contortion, 4),
        "force_anatomy": _force_dict(b.force_anatomy),
    }
