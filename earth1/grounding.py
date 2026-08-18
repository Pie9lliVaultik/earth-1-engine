"""THE GROUNDING CASCADE — four paths, and the answer says which one.

Ported from the old engine's ground-question cascade (verified in
vivid-node-forge at index.ts:784/802/922/941). Earth-1 has been
running Path C — LLM-authored weights — for every question, and
calling it the default rather than the last resort.

    Path A  survey-matched      real survey item, real cohort targets
    Path B  reference-anchored   nearest real item, weights dampened by
                                 similarity and stem-collision class
    Path D  live-grounded        web-searched published polling
                                 (earth1/live_search.py, built after
                                 A vs C is measured)
    Path C  forward-estimate     LLM-derived; honest last resort

`calibration_source` travels with every result forever. A caller must
be able to tell a measurement from a guess.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from earth1.stem_family import classify_pair, dampening_factor

CORPUS = Path(__file__).resolve().parents[1] / "data" / "seed_corpus" / "index.json"
EXACT = 0.92
NEAR = 0.70          # ported: Path B's original floor
LOOSE = 0.45         # EXTENSION (2026-08-18, ours, not in the TS):
                     # below NEAR but still inside the measured space.
                     # Rationale: the corpus spans ten topic families
                     # across fifty years, so almost any opinion
                     # question has SOMETHING near it. An honest
                     # heavily-dampened interpolation from a real
                     # measurement beats LLM-authored weights, and the
                     # DISTANCE is itself reportable information.
LOOSE_CAP = 0.25     # interpolation this far out is directional only
FLAT_BAND = 0.10          # |p - 0.5| below this from a weak anchor = flat
COND_MAX = 20_000.0       # ill-conditioned solves are rejected (old gate)


@dataclass
class Grounding:
    calibration_source: str          # survey-matched | reference-anchored |
                                     # loose-interpolation | live-grounded |
                                     # forward-estimate
    confidence: str                  # high | medium | low
    seed_id: str | None = None
    matched_question: str | None = None
    similarity: float | None = None
    dampening_factor: float | None = None
    stem_class: str | None = None
    cohort_targets: dict = field(default_factory=dict)
    national_target: float | None = None
    source: str | None = None
    source_url: str | None = None
    date: str | None = None
    condition_number: float | None = None
    nearest_seed: str | None = None
    nearest_similarity: float | None = None
    unsurveyed: bool = False         # nothing within LOOSE of this question
    note: str | None = None


_WORD = re.compile(r"[a-z0-9]+")


def _tokens(s: str) -> set:
    return set(_WORD.findall((s or "").lower()))


def lexical_similarity(a: str, b: str) -> float:
    """Jaccard over content tokens — a deliberate placeholder.

    The old engine used embeddings. Until Earth-1's embedder is wired
    into this path, similarity is lexical and therefore CONSERVATIVE:
    it under-matches paraphrases, which pushes questions DOWN the
    cascade (toward honest lower-confidence tiers) rather than up.
    """
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def load_corpus(path: str | None = None) -> list:
    p = Path(path) if path else CORPUS
    if not p.exists():
        return []
    return json.loads(p.read_text())


def condition_number(X: np.ndarray) -> float:
    try:
        s = np.linalg.svd(np.asarray(X, dtype=float), compute_uv=False)
        return float(s[0] / max(s[-1], 1e-12))
    except Exception:
        return float("inf")


def ground(question_text: str, population: str | None = None,
           corpus: list | None = None,
           allow_live: bool = False) -> Grounding:
    """Run the cascade and return the grounding decision with provenance."""
    corpus = corpus if corpus is not None else load_corpus()
    pool = [s for s in corpus
            if population is None or s.get("population") == population]
    if not pool:
        pool = corpus

    scored = sorted(
        ((lexical_similarity(question_text, s["question_text"]), s)
         for s in pool), key=lambda t: -t[0])
    if not scored:
        return Grounding("forward-estimate", "low",
                         note="empty corpus")

    sim, best = scored[0]

    # ── Path A ──
    if sim >= EXACT:
        return Grounding("survey-matched", "high", seed_id=best["id"],
                         matched_question=best["question_text"],
                         similarity=sim,
                         cohort_targets=best.get("cohort_targets", {}),
                         national_target=best.get("national_target"),
                         source=best.get("source"),
                         source_url=best.get("source_url"),
                         date=best.get("date"))

    # ── Path B ──
    if sim >= NEAR:
        klass = classify_pair(question_text, best["question_text"])
        cls = ("stem_collision" if klass == "stem_collision"
               else "different_question")
        factor = dampening_factor(sim, cls)
        nat = best.get("national_target")
        flat = (nat is not None and abs(nat - 0.5) * factor < FLAT_BAND
                and cls != "stem_collision")
        if not flat:
            return Grounding("reference-anchored", "medium",
                             seed_id=best["id"],
                             matched_question=best["question_text"],
                             similarity=sim, dampening_factor=factor,
                             stem_class=cls,
                             cohort_targets=best.get("cohort_targets", {}),
                             national_target=nat,
                             source=best.get("source"),
                             source_url=best.get("source_url"),
                             date=best.get("date"),
                             note="weights must be scaled by dampening_factor")
        # flat result from a weak anchor: fall through rather than guess

    # ── Path D ── (only when explicitly enabled and implemented)
    if allow_live:
        try:
            from earth1.live_search import live_ground
            live = live_ground(question_text, population)
            if live is not None:
                return live
        except ImportError:
            pass

    # ── Path B-loose (EXTENSION) ── still inside the measured space
    if sim >= LOOSE:
        klass = classify_pair(question_text, best["question_text"])
        cls = ("stem_collision" if klass == "stem_collision"
               else "different_question")
        factor = min(LOOSE_CAP, dampening_factor(max(sim, 0.51), cls))
        return Grounding("loose-interpolation", "low",
                         seed_id=best["id"],
                         matched_question=best["question_text"],
                         similarity=sim, dampening_factor=factor,
                         stem_class=cls,
                         cohort_targets=best.get("cohort_targets", {}),
                         national_target=best.get("national_target"),
                         source=best.get("source"),
                         source_url=best.get("source_url"),
                         date=best.get("date"),
                         nearest_seed=best["id"], nearest_similarity=sim,
                         note=("nobody has surveyed this question; "
                               "interpolated from the nearest real "
                               f"measurement at similarity {sim:.2f}, "
                               f"dampened to {factor:.2f} — DIRECTIONAL"))

    # ── Path C ── genuinely outside the measured space
    return Grounding("forward-estimate", "low", similarity=sim,
                     matched_question=best["question_text"],
                     nearest_seed=best["id"], nearest_similarity=sim,
                     unsurveyed=True,
                     note=("no measurement within reach: nearest of "
                           f"{len(pool)} real seeds is {sim:.2f} away. "
                           "This is itself a finding — the question is "
                           "unsurveyed. Weights are LLM-derived, NOT a "
                           "measurement."))
