"""Benchmark harness — GOQA-style regression suite with MAE tracking.

Runs a battery of questions with known survey ground truth against the engine,
computes MAE globally and per-country, classifies accuracy by regime, and
detects regressions against a saved baseline.

Bible §17 gate: MAE ≤ 0.221 on calibrated questions.
Bible §36 regimes: calibrated (≥0.85), transitional (0.65-0.85), forward-estimate (<0.65).
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from earth1.types import Civilization, Question, RunResult, Force, NUM_FORCES, FORCE_NAMES
from earth1.engine import run_question, run_segment, build_civilization
from earth1.questions import _w


@dataclass
class BenchmarkQuestion:
    """A question with known survey ground truth."""
    id: str
    text: str
    domain: str
    baseline: float
    weights: np.ndarray
    lens: str
    global_target: Optional[float] = None
    country_targets: Dict[str, float] = field(default_factory=dict)

    def to_question(self) -> Question:
        return Question(
            id=self.id, text=self.text, domain=self.domain,
            baseline=self.baseline, weights=self.weights, lens=self.lens,
        )


@dataclass
class QuestionResult:
    id: str
    text: str
    lens: str
    predicted_global: float
    target_global: Optional[float]
    global_error: Optional[float]
    dominant: str
    country_results: List[Dict]
    country_mae: Optional[float]


@dataclass
class BenchmarkReport:
    timestamp: str
    population: int
    seed: int
    n_questions: int
    n_country_pairs: int
    global_mae: Optional[float]
    country_mae: Optional[float]
    overall_mae: float
    by_regime: Dict[str, Dict]
    questions: List[QuestionResult]
    duration_s: float


# ---------------------------------------------------------------------------
# Ground truth data — real survey results from WVS Wave 7, Pew, GSS
#
# Each entry: known yes_pct (fraction supporting/agreeing) by country.
# Sources cited per question.  Countries not in survey are omitted.
# ---------------------------------------------------------------------------

BENCHMARK_QUESTIONS: List[BenchmarkQuestion] = [
    # --- 1. Same-sex marriage (WVS7 V204 "Homosexuality justifiable" + Pew 2023) ---
    BenchmarkQuestion(
        id="b_ssm", text="Do people support same-sex marriage?",
        domain="belief_causal", baseline=0.35,
        weights=_w(identity=3.4, culture=-2.2, collective=-1.2, experience=-1.6),
        lens="culture",
        global_target=0.55,
        country_targets={
            "US": 0.71, "GB": 0.77, "DE": 0.75, "FR": 0.77,
            "BR": 0.52, "MX": 0.55, "JP": 0.65,
            "IN": 0.22, "NG": 0.07,
        },
    ),
    # --- 2. Immigration restriction (Pew Global Attitudes 2018-2022) ---
    BenchmarkQuestion(
        id="b_immig", text="Should immigration be more restricted?",
        domain="belief_causal", baseline=-0.1,
        weights=_w(fear=2.8, identity=-2.6, culture=1.8, economics=1.4),
        lens="policy",
        global_target=0.48,
        country_targets={
            "US": 0.48, "GB": 0.52, "DE": 0.46, "FR": 0.56,
            "BR": 0.44, "MX": 0.38, "JP": 0.66,
            "IN": 0.42, "NG": 0.35,
        },
    ),
    # --- 3. Climate urgency (Pew 2021 "Climate as top threat") ---
    BenchmarkQuestion(
        id="b_climate", text="Is urgent climate action a priority?",
        domain="belief_causal", baseline=0.3,
        weights=_w(identity=2.4, experience=-2.0, culture=1.2, economics=-1.0),
        lens="policy",
        global_target=0.62,
        country_targets={
            "US": 0.54, "GB": 0.70, "DE": 0.71, "FR": 0.83,
            "BR": 0.72, "MX": 0.69, "JP": 0.75,
            "IN": 0.56, "NG": 0.48,
        },
    ),
    # --- 4. Trust in government (WVS7 V115 + Pew) ---
    BenchmarkQuestion(
        id="b_gov_trust", text="Do people trust their national government?",
        domain="belief_causal", baseline=-0.25,
        weights=_w(economics=2.6, identity=1.4, fear=-1.2, collective=1.0),
        lens="politics",
        global_target=0.38,
        country_targets={
            "US": 0.20, "GB": 0.35, "DE": 0.45, "FR": 0.28,
            "BR": 0.22, "MX": 0.21, "JP": 0.28,
            "IN": 0.77, "NG": 0.25,
        },
    ),
    # --- 5. Democracy best system (WVS7 V141 "democratic system good") ---
    BenchmarkQuestion(
        id="b_democracy", text="Is democracy the best system of government?",
        domain="belief_causal", baseline=1.2,
        weights=_w(identity=2.0, culture=-0.8, experience=1.4, collective=-1.0),
        lens="politics",
        global_target=0.78,
        country_targets={
            "US": 0.85, "GB": 0.87, "DE": 0.92, "FR": 0.84,
            "BR": 0.72, "MX": 0.68, "JP": 0.82,
            "IN": 0.75, "NG": 0.68,
        },
    ),
    # --- 6. Religion important in life (WVS7 V152) ---
    BenchmarkQuestion(
        id="b_religion", text="Is religion important in your daily life?",
        domain="belief_causal", baseline=0.2,
        weights=_w(identity=2.8, culture=2.4, collective=1.0, experience=0.6, temperament=-1.6),
        lens="culture",
        global_target=0.62,
        country_targets={
            "US": 0.65, "GB": 0.27, "DE": 0.25, "FR": 0.21,
            "BR": 0.86, "MX": 0.78, "JP": 0.13,
            "IN": 0.92, "NG": 0.96,
        },
    ),
    # --- 7. Gender equality progress (Pew 2019 "men have better life") ---
    BenchmarkQuestion(
        id="b_gender_eq", text="Do men generally have a better life than women in your country?",
        domain="belief_causal", baseline=0.1,
        weights=_w(identity=1.8, culture=-2.6, experience=1.2, economics=0.8, temperament=0.6),
        lens="culture",
        global_target=0.52,
        country_targets={
            "US": 0.56, "GB": 0.54, "DE": 0.52, "FR": 0.62,
            "BR": 0.58, "MX": 0.60, "JP": 0.64,
            "IN": 0.48, "NG": 0.42,
        },
    ),
    # --- 8. Technology makes life better (WVS7 V192) ---
    BenchmarkQuestion(
        id="b_tech_good", text="Does technology generally make life better?",
        domain="belief_causal", baseline=0.8,
        weights=_w(desire=1.6, economics=1.2, fear=-1.4, experience=-0.8, temperament=1.0),
        lens="technology",
        global_target=0.72,
        country_targets={
            "US": 0.72, "GB": 0.68, "DE": 0.65, "FR": 0.62,
            "BR": 0.78, "MX": 0.76, "JP": 0.63,
            "IN": 0.85, "NG": 0.82,
        },
    ),
    # --- 9. Abortion access (WVS7 V205 "abortion justifiable" + Pew) ---
    BenchmarkQuestion(
        id="b_abortion", text="Should abortion be legal in most cases?",
        domain="belief_causal", baseline=0.0,
        weights=_w(identity=3.0, culture=-2.8, experience=-1.0, collective=-0.8, temperament=0.6),
        lens="culture",
        global_target=0.52,
        country_targets={
            "US": 0.61, "GB": 0.76, "DE": 0.72, "FR": 0.80,
            "BR": 0.38, "MX": 0.48, "JP": 0.68,
            "IN": 0.36, "NG": 0.12,
        },
    ),
    # --- 10. Death penalty (WVS7 V198 + Pew) ---
    BenchmarkQuestion(
        id="b_death_penalty", text="Do people favor the death penalty for serious crimes?",
        domain="belief_causal", baseline=0.15,
        weights=_w(fear=2.2, identity=-1.8, culture=1.6, collective=1.2, temperament=-1.4),
        lens="policy",
        global_target=0.55,
        country_targets={
            "US": 0.55, "GB": 0.48, "DE": 0.32, "FR": 0.44,
            "BR": 0.57, "MX": 0.52, "JP": 0.80,
            "IN": 0.68, "NG": 0.74,
        },
    ),
    # --- 11. Economic system fairness (Pew 2019 "econ system unfair") ---
    BenchmarkQuestion(
        id="b_econ_unfair", text="Is the economic system in your country unfair to most people?",
        domain="belief_causal", baseline=0.3,
        weights=_w(economics=-2.8, identity=0.8, collective=1.4, fear=1.0, desire=-0.6),
        lens="economics",
        global_target=0.62,
        country_targets={
            "US": 0.58, "GB": 0.62, "DE": 0.48, "FR": 0.72,
            "BR": 0.76, "MX": 0.74, "JP": 0.58,
            "IN": 0.56, "NG": 0.70,
        },
    ),
    # --- 12. Children need both parents (WVS7 V47 + Pew) ---
    BenchmarkQuestion(
        id="b_two_parent", text="Do children need both a mother and father to grow up happily?",
        domain="belief_causal", baseline=0.6,
        weights=_w(culture=2.6, identity=1.6, collective=1.8, experience=0.8, temperament=-1.0),
        lens="family",
        global_target=0.68,
        country_targets={
            "US": 0.56, "GB": 0.48, "DE": 0.42, "FR": 0.38,
            "BR": 0.72, "MX": 0.74, "JP": 0.62,
            "IN": 0.88, "NG": 0.92,
        },
    ),
    # --- 13. Trust in news media (Pew 2022 + WVS7 V120) ---
    BenchmarkQuestion(
        id="b_media_trust", text="Do people trust the news media?",
        domain="belief_causal", baseline=-0.4,
        weights=_w(identity=1.6, fear=-1.2, collective=1.8, economics=0.6, temperament=-0.8),
        lens="media",
        global_target=0.38,
        country_targets={
            "US": 0.26, "GB": 0.36, "DE": 0.50, "FR": 0.30,
            "BR": 0.42, "MX": 0.38, "JP": 0.32,
            "IN": 0.52, "NG": 0.42,
        },
    ),
    # --- 14. Satisfied with life (WVS7 V23 "satisfied with life" 7+/10) ---
    BenchmarkQuestion(
        id="b_life_sat", text="Are people generally satisfied with their life?",
        domain="belief_causal", baseline=0.5,
        weights=_w(economics=2.0, desire=-1.4, fear=-1.0, experience=0.6, temperament=1.2),
        lens="wellbeing",
        global_target=0.58,
        country_targets={
            "US": 0.72, "GB": 0.68, "DE": 0.70, "FR": 0.62,
            "BR": 0.55, "MX": 0.72, "JP": 0.52,
            "IN": 0.42, "NG": 0.38,
        },
    ),
    # --- 15. China viewed favorably (Pew 2023 Global Views of China) ---
    BenchmarkQuestion(
        id="b_china_fav", text="Do people have a favorable view of China?",
        domain="belief_causal", baseline=-0.3,
        weights=_w(economics=1.8, fear=-1.4, identity=-1.0, collective=0.8, culture=0.6),
        lens="geopolitics",
        global_target=0.34,
        country_targets={
            "US": 0.15, "GB": 0.18, "DE": 0.21, "FR": 0.16,
            "BR": 0.48, "MX": 0.42, "JP": 0.09,
            "IN": 0.32, "NG": 0.72,
        },
    ),
    # --- 16. US viewed favorably (Pew 2023) ---
    BenchmarkQuestion(
        id="b_us_fav", text="Do people have a favorable view of the United States?",
        domain="belief_causal", baseline=0.4,
        weights=_w(economics=1.4, identity=0.8, culture=-0.6, collective=0.4, fear=-0.4),
        lens="geopolitics",
        global_target=0.59,
        country_targets={
            "GB": 0.69, "DE": 0.54, "FR": 0.52,
            "BR": 0.62, "MX": 0.52, "JP": 0.73,
            "IN": 0.65, "NG": 0.78,
        },
    ),
    # --- 17. Worry about nuclear weapons (Pew 2022) ---
    BenchmarkQuestion(
        id="b_nukes", text="Are people worried about the threat of nuclear weapons?",
        domain="belief_causal", baseline=0.6,
        weights=_w(fear=3.0, collective=1.2, identity=-0.6, economics=-0.4),
        lens="security",
        global_target=0.72,
        country_targets={
            "US": 0.73, "GB": 0.68, "DE": 0.70, "FR": 0.68,
            "BR": 0.62, "MX": 0.58, "JP": 0.88,
            "IN": 0.72, "NG": 0.52,
        },
    ),
    # --- 18. Nationalism — country is better than most (WVS7 V211) ---
    BenchmarkQuestion(
        id="b_natl_pride", text="Is your country better than most other countries?",
        domain="belief_causal", baseline=0.3,
        weights=_w(identity=2.8, culture=1.8, collective=0.8, experience=0.4, economics=-0.6),
        lens="identity",
        global_target=0.52,
        country_targets={
            "US": 0.68, "GB": 0.55, "DE": 0.42, "FR": 0.52,
            "BR": 0.48, "MX": 0.62, "JP": 0.55,
            "IN": 0.68, "NG": 0.72,
        },
    ),
    # --- 19. Worry about AI (Pew 2023 "concerned about AI") ---
    BenchmarkQuestion(
        id="b_ai_concern", text="Are people concerned about artificial intelligence?",
        domain="belief_causal", baseline=0.2,
        weights=_w(fear=2.6, experience=1.4, identity=-0.8, temperament=-1.2, economics=0.6),
        lens="technology",
        global_target=0.55,
        country_targets={
            "US": 0.52, "GB": 0.58, "DE": 0.62, "FR": 0.64,
            "BR": 0.48, "MX": 0.44, "JP": 0.68,
            "IN": 0.42, "NG": 0.38,
        },
    ),
    # --- 20. Wealth gap too large (Pew 2020 + WVS7) ---
    BenchmarkQuestion(
        id="b_inequality", text="Is the gap between rich and poor too large?",
        domain="belief_causal", baseline=0.8,
        weights=_w(economics=-2.4, identity=0.6, collective=1.6, desire=-0.8, fear=0.6),
        lens="economics",
        global_target=0.74,
        country_targets={
            "US": 0.65, "GB": 0.72, "DE": 0.68, "FR": 0.78,
            "BR": 0.82, "MX": 0.80, "JP": 0.72,
            "IN": 0.68, "NG": 0.76,
        },
    ),

    # ===================================================================
    # Build 25 expansion — 30 new questions from WVS7, Pew, Gallup, EB
    # ===================================================================

    # --- 21. Interpersonal trust (WVS7 V24 "Most people can be trusted") ---
    BenchmarkQuestion(
        id="b_trust_people", text="Can most people be trusted?",
        domain="belief_causal", baseline=-0.4,
        weights=_w(fear=-2.4, collective=2.0, economics=1.2, experience=0.8, identity=-0.6),
        lens="social",
        global_target=0.28,
        country_targets={
            "US": 0.31, "GB": 0.30, "DE": 0.42, "FR": 0.22,
            "BR": 0.07, "MX": 0.12, "JP": 0.36,
            "IN": 0.22, "NG": 0.11, "SE": 0.64, "CN": 0.63,
        },
    ),
    # --- 22. Hard work leads to success (WVS7 V181 "work vs luck") ---
    BenchmarkQuestion(
        id="b_hard_work", text="Does hard work generally lead to a better life?",
        domain="belief_causal", baseline=0.5,
        weights=_w(economics=2.2, desire=1.8, temperament=1.4, identity=0.6, fear=-1.0),
        lens="economics",
        global_target=0.62,
        country_targets={
            "US": 0.73, "GB": 0.58, "DE": 0.52, "FR": 0.42,
            "BR": 0.62, "MX": 0.72, "JP": 0.42,
            "IN": 0.78, "NG": 0.82,
        },
    ),
    # --- 23. Children should obey (WVS7 V18 "obedience important") ---
    BenchmarkQuestion(
        id="b_obedience", text="Is obedience an important quality for children?",
        domain="belief_causal", baseline=0.4,
        weights=_w(collective=2.8, culture=2.2, identity=-1.4, temperament=-1.0, experience=0.6),
        lens="family",
        global_target=0.58,
        country_targets={
            "US": 0.38, "GB": 0.32, "DE": 0.28, "FR": 0.30,
            "BR": 0.72, "MX": 0.68, "JP": 0.44,
            "IN": 0.82, "NG": 0.88,
        },
    ),
    # --- 24. Divorce justifiable (WVS7 V203 "divorce justifiable" 6+/10) ---
    BenchmarkQuestion(
        id="b_divorce", text="Is divorce justifiable?",
        domain="belief_causal", baseline=0.1,
        weights=_w(identity=2.6, culture=-2.4, collective=-1.2, experience=-0.8, temperament=0.8),
        lens="culture",
        global_target=0.56,
        country_targets={
            "US": 0.64, "GB": 0.72, "DE": 0.68, "FR": 0.74,
            "BR": 0.48, "MX": 0.52, "JP": 0.62,
            "IN": 0.28, "NG": 0.22,
        },
    ),
    # --- 25. Science vs religion (WVS7 V153 "science and tech make life better") ---
    BenchmarkQuestion(
        id="b_science_better", text="Does science do more good than harm?",
        domain="belief_causal", baseline=0.6,
        weights=_w(identity=1.8, culture=-1.6, experience=-1.4, economics=1.2, temperament=0.8),
        lens="technology",
        global_target=0.68,
        country_targets={
            "US": 0.62, "GB": 0.68, "DE": 0.72, "FR": 0.64,
            "BR": 0.72, "MX": 0.70, "JP": 0.58,
            "IN": 0.82, "NG": 0.72,
        },
    ),
    # --- 26. Military rule acceptable (WVS7 V139 "army rule good") ---
    BenchmarkQuestion(
        id="b_military_rule", text="Could military rule ever be a good way to govern?",
        domain="belief_causal", baseline=-0.6,
        weights=_w(collective=2.4, fear=2.0, identity=-2.2, culture=1.0, economics=-0.8),
        lens="politics",
        global_target=0.24,
        country_targets={
            "US": 0.18, "GB": 0.12, "DE": 0.08, "FR": 0.14,
            "BR": 0.32, "MX": 0.28, "JP": 0.08,
            "IN": 0.42, "NG": 0.48,
        },
    ),
    # --- 27. Environment vs economy (WVS7 V81 "protect environment vs growth") ---
    BenchmarkQuestion(
        id="b_env_vs_econ", text="Should protecting the environment take priority over economic growth?",
        domain="belief_causal", baseline=0.1,
        weights=_w(identity=2.0, economics=-2.4, experience=-1.2, culture=1.0, desire=-0.6),
        lens="policy",
        global_target=0.52,
        country_targets={
            "US": 0.42, "GB": 0.58, "DE": 0.68, "FR": 0.62,
            "BR": 0.56, "MX": 0.48, "JP": 0.52,
            "IN": 0.38, "NG": 0.32,
        },
    ),
    # --- 28. Police trustworthy (WVS7 V116 "confidence in police") ---
    BenchmarkQuestion(
        id="b_police_trust", text="Do people trust the police?",
        domain="belief_causal", baseline=-0.1,
        weights=_w(collective=2.2, fear=-1.8, identity=1.0, economics=1.2, culture=0.6),
        lens="governance",
        global_target=0.52,
        country_targets={
            "US": 0.48, "GB": 0.62, "DE": 0.72, "FR": 0.58,
            "BR": 0.38, "MX": 0.28, "JP": 0.78,
            "IN": 0.62, "NG": 0.28,
        },
    ),
    # --- 29. Worried about terrorism (Pew 2022 "terrorism top threat") ---
    BenchmarkQuestion(
        id="b_terrorism", text="Are people worried about terrorism?",
        domain="belief_causal", baseline=0.4,
        weights=_w(fear=3.2, collective=1.4, identity=-0.8, culture=0.6, experience=0.4),
        lens="security",
        global_target=0.62,
        country_targets={
            "US": 0.58, "GB": 0.62, "DE": 0.54, "FR": 0.72,
            "BR": 0.42, "MX": 0.48, "JP": 0.38,
            "IN": 0.72, "NG": 0.78,
        },
    ),
    # --- 30. Free speech priority (Pew 2021 "free speech very important") ---
    BenchmarkQuestion(
        id="b_free_speech", text="Is free speech more important than not offending others?",
        domain="belief_causal", baseline=0.2,
        weights=_w(identity=2.8, temperament=1.4, collective=-2.0, culture=-1.2, experience=-0.6),
        lens="politics",
        global_target=0.58,
        country_targets={
            "US": 0.71, "GB": 0.58, "DE": 0.52, "FR": 0.56,
            "BR": 0.48, "MX": 0.52, "JP": 0.42,
            "IN": 0.56, "NG": 0.62,
        },
    ),
    # --- 31. Corruption widespread (Transparency Int'l / WVS7 V117) ---
    BenchmarkQuestion(
        id="b_corruption", text="Is corruption a major problem in your country?",
        domain="belief_causal", baseline=0.6,
        weights=_w(economics=-2.0, fear=1.8, collective=-1.4, identity=0.8, culture=-0.6),
        lens="governance",
        global_target=0.72,
        country_targets={
            "US": 0.52, "GB": 0.42, "DE": 0.38, "FR": 0.58,
            "BR": 0.88, "MX": 0.86, "JP": 0.48,
            "IN": 0.82, "NG": 0.92,
        },
    ),
    # --- 32. Vaccines safe and effective (Wellcome Global Monitor 2018) ---
    BenchmarkQuestion(
        id="b_vaccines", text="Are vaccines safe and effective?",
        domain="belief_causal", baseline=1.0,
        weights=_w(collective=2.4, fear=-2.0, identity=-1.2, experience=1.0, culture=0.8),
        lens="health",
        global_target=0.79,
        country_targets={
            "US": 0.72, "GB": 0.82, "DE": 0.68, "FR": 0.58,
            "BR": 0.82, "MX": 0.78, "JP": 0.72,
            "IN": 0.88, "NG": 0.62,
        },
    ),
    # --- 33. Women equal in workforce (WVS7 V51 + Pew) ---
    BenchmarkQuestion(
        id="b_women_work", text="Should women have equal opportunities in the workforce?",
        domain="belief_causal", baseline=0.8,
        weights=_w(identity=2.4, culture=-2.0, economics=1.2, experience=-0.8, collective=-0.6),
        lens="culture",
        global_target=0.78,
        country_targets={
            "US": 0.82, "GB": 0.86, "DE": 0.84, "FR": 0.88,
            "BR": 0.76, "MX": 0.72, "JP": 0.68,
            "IN": 0.62, "NG": 0.58,
        },
    ),
    # --- 34. Censorship sometimes necessary (WVS7 V143 + Pew) ---
    BenchmarkQuestion(
        id="b_censorship", text="Is government censorship sometimes justified?",
        domain="belief_causal", baseline=-0.2,
        weights=_w(collective=2.6, fear=1.8, identity=-2.4, culture=1.0, temperament=-0.8),
        lens="politics",
        global_target=0.42,
        country_targets={
            "US": 0.28, "GB": 0.35, "DE": 0.38, "FR": 0.32,
            "BR": 0.48, "MX": 0.44, "JP": 0.52,
            "IN": 0.62, "NG": 0.55,
        },
    ),
    # --- 35. Personal economic situation improving (Eurobarometer / Gallup) ---
    BenchmarkQuestion(
        id="b_econ_improving", text="Is your personal economic situation getting better?",
        domain="belief_causal", baseline=-0.2,
        weights=_w(economics=2.8, desire=1.6, fear=-1.4, temperament=0.8, experience=-0.6),
        lens="economics",
        global_target=0.38,
        country_targets={
            "US": 0.42, "GB": 0.35, "DE": 0.38, "FR": 0.32,
            "BR": 0.28, "MX": 0.34, "JP": 0.22,
            "IN": 0.56, "NG": 0.32,
        },
    ),
    # --- 36. NATO important (Pew 2023 "NATO favorable") ---
    BenchmarkQuestion(
        id="b_nato", text="Is NATO important for national security?",
        domain="belief_causal", baseline=0.4,
        weights=_w(collective=2.2, fear=1.6, identity=0.8, economics=-0.6, culture=0.4),
        lens="geopolitics",
        global_target=0.62,
        country_targets={
            "US": 0.65, "GB": 0.72, "DE": 0.64, "FR": 0.58,
            "JP": 0.55, "IN": 0.42, "NG": 0.38,
        },
    ),
    # --- 37. Robots will replace jobs (Eurobarometer 2017 + Pew) ---
    BenchmarkQuestion(
        id="b_automation", text="Will automation replace most jobs in the next 20 years?",
        domain="belief_causal", baseline=0.1,
        weights=_w(fear=2.2, economics=-1.8, temperament=-1.2, experience=1.0, desire=-0.6),
        lens="technology",
        global_target=0.52,
        country_targets={
            "US": 0.48, "GB": 0.55, "DE": 0.58, "FR": 0.56,
            "BR": 0.52, "MX": 0.48, "JP": 0.74,
            "IN": 0.42, "NG": 0.35,
        },
    ),
    # --- 38. Elections fair (WVS7 V228a "honest elections") ---
    BenchmarkQuestion(
        id="b_elections_fair", text="Are elections in your country generally fair?",
        domain="belief_causal", baseline=-0.1,
        weights=_w(collective=2.4, identity=1.2, economics=1.0, fear=-1.4, culture=0.6),
        lens="governance",
        global_target=0.48,
        country_targets={
            "US": 0.52, "GB": 0.68, "DE": 0.72, "FR": 0.56,
            "BR": 0.32, "MX": 0.26, "JP": 0.58,
            "IN": 0.62, "NG": 0.22,
        },
    ),
    # --- 39. Multinationals positive (Pew 2014-2019 + Eurobarometer) ---
    BenchmarkQuestion(
        id="b_multinationals", text="Do multinational corporations have a positive influence?",
        domain="belief_causal", baseline=0.0,
        weights=_w(economics=2.4, desire=1.2, identity=-1.0, collective=-0.8, fear=-0.6),
        lens="economics",
        global_target=0.48,
        country_targets={
            "US": 0.52, "GB": 0.48, "DE": 0.42, "FR": 0.38,
            "BR": 0.56, "MX": 0.54, "JP": 0.38,
            "IN": 0.68, "NG": 0.72,
        },
    ),
    # --- 40. Social mobility declining (Pew 2020 "harder to get ahead") ---
    BenchmarkQuestion(
        id="b_social_mobility", text="Is it harder to get ahead economically than it used to be?",
        domain="belief_causal", baseline=0.4,
        weights=_w(economics=-2.2, fear=1.6, desire=-1.4, experience=1.2, collective=0.6),
        lens="economics",
        global_target=0.64,
        country_targets={
            "US": 0.62, "GB": 0.65, "DE": 0.52, "FR": 0.72,
            "BR": 0.68, "MX": 0.66, "JP": 0.72,
            "IN": 0.48, "NG": 0.58,
        },
    ),
    # --- 41. Internet freedom (Pew 2019 "internet good for society") ---
    BenchmarkQuestion(
        id="b_internet_good", text="Is the internet a good thing for society?",
        domain="belief_causal", baseline=0.6,
        weights=_w(identity=1.6, desire=1.4, economics=1.0, fear=-1.6, temperament=0.8),
        lens="technology",
        global_target=0.68,
        country_targets={
            "US": 0.72, "GB": 0.68, "DE": 0.62, "FR": 0.58,
            "BR": 0.75, "MX": 0.72, "JP": 0.55,
            "IN": 0.82, "NG": 0.78,
        },
    ),
    # --- 42. Traditional family important (WVS7 V47 + Pew) ---
    BenchmarkQuestion(
        id="b_trad_family", text="Are traditional family values important for society?",
        domain="belief_causal", baseline=0.5,
        weights=_w(culture=3.0, collective=2.0, identity=-1.6, experience=0.8, temperament=-0.6),
        lens="culture",
        global_target=0.68,
        country_targets={
            "US": 0.62, "GB": 0.48, "DE": 0.42, "FR": 0.38,
            "BR": 0.78, "MX": 0.76, "JP": 0.58,
            "IN": 0.88, "NG": 0.92,
        },
    ),
    # --- 43. Foreign aid effective (Eurobarometer / Gallup) ---
    BenchmarkQuestion(
        id="b_foreign_aid", text="Does foreign aid effectively help developing countries?",
        domain="belief_causal", baseline=-0.1,
        weights=_w(economics=-1.4, collective=2.0, identity=1.2, experience=-0.8, desire=0.6),
        lens="geopolitics",
        global_target=0.42,
        country_targets={
            "US": 0.38, "GB": 0.48, "DE": 0.52, "FR": 0.44,
            "BR": 0.42, "MX": 0.38, "JP": 0.35,
            "IN": 0.48, "NG": 0.32,
        },
    ),
    # --- 44. Leaders care about people (WVS7/Pew "leaders don't care") ---
    BenchmarkQuestion(
        id="b_leaders_care", text="Do political leaders care about ordinary people?",
        domain="belief_causal", baseline=-0.6,
        weights=_w(economics=2.0, collective=1.6, fear=-1.4, identity=-0.8, desire=-0.6),
        lens="politics",
        global_target=0.26,
        country_targets={
            "US": 0.18, "GB": 0.22, "DE": 0.32, "FR": 0.16,
            "BR": 0.14, "MX": 0.12, "JP": 0.18,
            "IN": 0.52, "NG": 0.18,
        },
    ),
    # --- 45. Satisfied with healthcare (Gallup World Poll) ---
    BenchmarkQuestion(
        id="b_health_sat", text="Are people satisfied with healthcare in their country?",
        domain="belief_causal", baseline=0.0,
        weights=_w(economics=2.4, collective=1.4, fear=-1.0, experience=0.8, desire=-0.6),
        lens="health",
        global_target=0.48,
        country_targets={
            "US": 0.52, "GB": 0.42, "DE": 0.68, "FR": 0.72,
            "BR": 0.28, "MX": 0.32, "JP": 0.55,
            "IN": 0.32, "NG": 0.22,
        },
    ),
    # --- 46. Higher education valuable (Pew 2019 + Gallup) ---
    BenchmarkQuestion(
        id="b_higher_ed", text="Is a university education worth the cost?",
        domain="belief_causal", baseline=0.2,
        weights=_w(economics=2.0, desire=1.8, identity=0.8, experience=-1.2, fear=-0.6),
        lens="economics",
        global_target=0.55,
        country_targets={
            "US": 0.48, "GB": 0.52, "DE": 0.62, "FR": 0.55,
            "BR": 0.68, "MX": 0.72, "JP": 0.42,
            "IN": 0.78, "NG": 0.82,
        },
    ),
    # --- 47. Homosexuality acceptable (Pew 2023 Global) ---
    BenchmarkQuestion(
        id="b_lgbtq_accept", text="Should homosexuality be accepted by society?",
        domain="belief_causal", baseline=0.2,
        weights=_w(identity=3.2, culture=-2.6, collective=-1.0, experience=-1.2, temperament=0.4),
        lens="culture",
        global_target=0.52,
        country_targets={
            "US": 0.64, "GB": 0.76, "DE": 0.78, "FR": 0.77,
            "BR": 0.52, "MX": 0.58, "JP": 0.68,
            "IN": 0.22, "NG": 0.04,
        },
    ),
    # --- 48. Russia viewed unfavorably (Pew 2023) ---
    BenchmarkQuestion(
        id="b_russia_unfav", text="Do people view Russia unfavorably?",
        domain="belief_causal", baseline=0.2,
        weights=_w(fear=2.2, identity=-1.4, collective=1.0, economics=-0.8, culture=-0.6),
        lens="geopolitics",
        global_target=0.62,
        country_targets={
            "US": 0.72, "GB": 0.78, "DE": 0.74, "FR": 0.68,
            "BR": 0.38, "MX": 0.42, "JP": 0.82,
            "IN": 0.28, "NG": 0.32,
        },
    ),
    # --- 49. Worried about cyberattacks (Pew 2022) ---
    BenchmarkQuestion(
        id="b_cyber_threat", text="Are cyberattacks a major threat to your country?",
        domain="belief_causal", baseline=0.3,
        weights=_w(fear=2.8, economics=1.4, collective=0.8, temperament=-0.6, experience=0.4),
        lens="security",
        global_target=0.68,
        country_targets={
            "US": 0.72, "GB": 0.65, "DE": 0.68, "FR": 0.64,
            "BR": 0.52, "MX": 0.48, "JP": 0.78,
            "IN": 0.62, "NG": 0.42,
        },
    ),
    # --- 50. Globalization good (Pew / Eurobarometer) ---
    BenchmarkQuestion(
        id="b_globalization", text="Has globalization been good for your country?",
        domain="belief_causal", baseline=0.1,
        weights=_w(economics=2.2, identity=-1.6, culture=1.0, collective=-0.8, desire=0.6),
        lens="economics",
        global_target=0.52,
        country_targets={
            "US": 0.48, "GB": 0.45, "DE": 0.58, "FR": 0.42,
            "BR": 0.52, "MX": 0.56, "JP": 0.48,
            "IN": 0.68, "NG": 0.62,
        },
    ),
]


def run_benchmark(
    civ: Civilization,
    questions: Optional[List[BenchmarkQuestion]] = None,
    epsilon: float = 0.18,
    layers: int = 8,
    use_force_dynamics: bool = True,
    event_log=None,
    t: float = 0.0,
) -> BenchmarkReport:
    """Run full benchmark suite against the civilization.

    When use_force_dynamics=True, runs questions through force-aware diffusion
    instead of scalar diffusion. At tick 0 with no events, results should be
    nearly identical to scalar mode.
    """
    if questions is None:
        questions = BENCHMARK_QUESTIONS

    t0 = time.time()
    results = []
    all_global_errors = []
    all_country_errors = []

    from earth1.population import COUNTRY_CODES

    for bq in questions:
        q = bq.to_question()

        if use_force_dynamics:
            from earth1.dynamics import run_with_dynamics, compute_susceptibility
            from earth1.decompose import anatomize, histogram

            field_shift = None
            if event_log is not None and len(event_log) > 0:
                field_shift = event_log.effective_deltas_vectorized(t, civ)

            susceptibility = compute_susceptibility(civ)
            settled, _residues, snaps = run_with_dynamics(
                civ, q, epsilon=epsilon, layers=layers,
                susceptibility=susceptibility, field_shift=field_shift,
            )
            anat = anatomize(civ, settled, q)
            dists = [histogram(s) for s in snaps]
            frac_yes = float((settled >= 0.5).mean())
            r = RunResult(
                question=q, n=civ.n,
                yes_pct=float(settled.mean()),
                frac_yes=frac_yes,
                regime="force-dynamics",
                distribution_by_layer=dists,
                final_distribution=dists[-1],
                force_anatomy=anat["force_anatomy"],
                dominant=anat["dominant"],
                conviction=anat["conviction"],
                fragility=anat["fragility"],
                camps=anat["camps"],
                params={"epsilon": epsilon, "layers": layers, "mode": "force_dynamics"},
                settled_stances=settled,
            )
        else:
            r = run_question(q, civ, epsilon=epsilon, layers=layers,
                             event_log=event_log, t=t)

        country_results = []
        country_errors = []

        if bq.country_targets:
            cells = run_segment(q, civ, "country", epsilon=epsilon, layers=layers)
            cell_map = {c.label: c.yes_pct for c in cells}

            for code, target in bq.country_targets.items():
                predicted = cell_map.get(code)
                if predicted is not None:
                    err = abs(predicted - target)
                    country_errors.append(err)
                    all_country_errors.append(err)
                    country_results.append({
                        "country": code,
                        "predicted": round(predicted, 4),
                        "target": target,
                        "error": round(err, 4),
                    })

        global_error = None
        if bq.global_target is not None:
            global_error = abs(r.yes_pct - bq.global_target)
            all_global_errors.append(global_error)

        results.append(QuestionResult(
            id=bq.id,
            text=bq.text,
            lens=bq.lens,
            predicted_global=round(r.yes_pct, 4),
            target_global=bq.global_target,
            global_error=round(global_error, 4) if global_error is not None else None,
            dominant=r.dominant.name.lower(),
            country_results=country_results,
            country_mae=round(np.mean(country_errors), 4) if country_errors else None,
        ))

    global_mae = float(np.mean(all_global_errors)) if all_global_errors else None
    country_mae = float(np.mean(all_country_errors)) if all_country_errors else None

    all_errors = all_global_errors + all_country_errors
    overall_mae = float(np.mean(all_errors)) if all_errors else 0.0

    by_regime = _classify_regimes(results)

    dt = time.time() - t0

    return BenchmarkReport(
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        population=civ.n,
        seed=civ.seed,
        n_questions=len(results),
        n_country_pairs=len(all_country_errors),
        global_mae=round(global_mae, 4) if global_mae is not None else None,
        country_mae=round(country_mae, 4) if country_mae is not None else None,
        overall_mae=round(overall_mae, 4),
        by_regime=by_regime,
        questions=results,
        duration_s=round(dt, 2),
    )


def _classify_regimes(
    results: List[QuestionResult],
    questions: Optional[List[BenchmarkQuestion]] = None,
) -> Dict[str, Dict]:
    """Group results by data provenance, not by error.

    - anchored: ≥7 country-level survey targets from primary sources
    - partial:  3-6 country targets
    - unanchored: <3 country targets (no meaningful geographic validation)
    """
    if questions is None:
        questions = BENCHMARK_QUESTIONS
    q_map = {bq.id: bq for bq in questions}

    regimes = {
        "anchored": {"min_countries": 7, "questions": [], "mae": None},
        "partial": {"min_countries": 3, "questions": [], "mae": None},
        "unanchored": {"min_countries": 0, "questions": [], "mae": None},
    }

    for r in results:
        bq = q_map.get(r.id)
        n_countries = len(bq.country_targets) if bq else 0
        if n_countries >= 7:
            regimes["anchored"]["questions"].append(r.id)
        elif n_countries >= 3:
            regimes["partial"]["questions"].append(r.id)
        else:
            regimes["unanchored"]["questions"].append(r.id)

    for regime in regimes.values():
        ids = set(regime["questions"])
        errors = [r.country_mae for r in results
                  if r.id in ids and r.country_mae is not None]
        regime["count"] = len(regime["questions"])
        regime["mae"] = round(float(np.mean(errors)), 4) if errors else None

    return regimes


def format_report(report: BenchmarkReport) -> str:
    """Format benchmark report as human-readable text."""
    lines = [
        f"Earth-1 Benchmark Report",
        f"{'='*60}",
        f"  Population: {report.population:,}  |  Seed: {report.seed}",
        f"  Questions:  {report.n_questions}  |  Country pairs: {report.n_country_pairs}",
        f"  Duration:   {report.duration_s}s",
        f"",
        f"  OVERALL MAE:  {report.overall_mae:.4f}",
        f"  Global MAE:   {report.global_mae:.4f}" if report.global_mae else "",
        f"  Country MAE:  {report.country_mae:.4f}" if report.country_mae else "",
        f"  Bible target: 0.2210  {'PASS' if report.overall_mae <= 0.221 else 'FAIL'}",
        f"",
        f"  By data provenance:",
    ]

    for name, regime in report.by_regime.items():
        mae_str = f"MAE={regime['mae']:.4f}" if regime['mae'] is not None else "n/a"
        lines.append(f"    {name:20s}: {regime['count']:2d} questions  {mae_str}")

    lines.append(f"\n  Per-question breakdown:")
    lines.append(f"  {'ID':<20s} {'Pred':>6s} {'Tgt':>6s} {'Err':>6s} {'C-MAE':>6s} {'Dom':<12s}")
    lines.append(f"  {'-'*62}")

    for q in sorted(report.questions, key=lambda x: -(x.country_mae or 0)):
        tgt = f"{q.target_global:.2f}" if q.target_global is not None else "  -  "
        err = f"{q.global_error:.4f}" if q.global_error is not None else "  -  "
        cmae = f"{q.country_mae:.4f}" if q.country_mae is not None else "  -  "
        lines.append(f"  {q.id:<20s} {q.predicted_global:6.2f} {tgt:>6s} {err:>6s} {cmae:>6s} {q.dominant:<12s}")

    return "\n".join(lines)


def save_report(report: BenchmarkReport, path: str | Path) -> None:
    """Save benchmark report as JSON for regression tracking."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "timestamp": report.timestamp,
        "population": report.population,
        "seed": report.seed,
        "n_questions": report.n_questions,
        "n_country_pairs": report.n_country_pairs,
        "global_mae": report.global_mae,
        "country_mae": report.country_mae,
        "overall_mae": report.overall_mae,
        "by_regime": report.by_regime,
        "duration_s": report.duration_s,
        "questions": [
            {
                "id": q.id,
                "text": q.text,
                "predicted_global": q.predicted_global,
                "target_global": q.target_global,
                "global_error": q.global_error,
                "dominant": q.dominant,
                "country_mae": q.country_mae,
                "country_results": q.country_results,
            }
            for q in report.questions
        ],
    }

    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def check_regression(
    current: BenchmarkReport,
    baseline_path: str | Path,
    tolerance: float = 0.01,
) -> Dict:
    """Compare current run against a saved baseline. Flag regressions."""
    path = Path(baseline_path)
    if not path.exists():
        return {"status": "no_baseline", "message": "No baseline to compare against."}

    with open(path) as f:
        baseline = json.load(f)

    base_mae = baseline.get("overall_mae", 0)
    diff = current.overall_mae - base_mae

    base_questions = {q["id"]: q for q in baseline.get("questions", [])}
    regressions = []
    improvements = []

    for q in current.questions:
        if q.id in base_questions:
            bq = base_questions[q.id]
            if q.country_mae is not None and bq.get("country_mae") is not None:
                delta = q.country_mae - bq["country_mae"]
                if delta > tolerance:
                    regressions.append({
                        "id": q.id, "was": bq["country_mae"],
                        "now": q.country_mae, "delta": round(delta, 4),
                    })
                elif delta < -tolerance:
                    improvements.append({
                        "id": q.id, "was": bq["country_mae"],
                        "now": q.country_mae, "delta": round(delta, 4),
                    })

    return {
        "status": "regression" if regressions else "ok",
        "overall_mae_delta": round(diff, 4),
        "baseline_mae": base_mae,
        "current_mae": current.overall_mae,
        "regressions": regressions,
        "improvements": improvements,
    }


@dataclass
class ComparisonResult:
    """Side-by-side scalar vs force dynamics benchmark."""
    scalar_report: BenchmarkReport
    force_report: BenchmarkReport
    per_question: List[Dict]
    mae_delta: float
    max_divergence: float
    divergent_questions: List[str]


def run_benchmark_comparison(
    civ: Civilization,
    questions: Optional[List[BenchmarkQuestion]] = None,
    event_log=None,
    t: float = 0.0,
    divergence_threshold: float = 0.02,
) -> ComparisonResult:
    """Run both scalar and force dynamics, compare results."""
    qs = questions or BENCHMARK_QUESTIONS

    scalar = run_benchmark(civ, qs, use_force_dynamics=False,
                           event_log=event_log, t=t)
    force = run_benchmark(civ, qs, use_force_dynamics=True,
                          event_log=event_log, t=t)

    per_question = []
    max_div = 0.0
    divergent = []

    scalar_map = {q.id: q for q in scalar.questions}
    force_map = {q.id: q for q in force.questions}

    for qid in scalar_map:
        sq = scalar_map[qid]
        fq = force_map.get(qid)
        if fq is None:
            continue
        div = abs(sq.predicted_global - fq.predicted_global)
        max_div = max(max_div, div)
        if div > divergence_threshold:
            divergent.append(qid)

        per_question.append({
            "id": qid,
            "scalar_pred": sq.predicted_global,
            "force_pred": fq.predicted_global,
            "divergence": round(div, 4),
            "scalar_cmae": sq.country_mae,
            "force_cmae": fq.country_mae,
        })

    return ComparisonResult(
        scalar_report=scalar,
        force_report=force,
        per_question=sorted(per_question, key=lambda x: -x["divergence"]),
        mae_delta=round(force.overall_mae - scalar.overall_mae, 4),
        max_divergence=round(max_div, 4),
        divergent_questions=divergent,
    )


def format_comparison(comp: ComparisonResult) -> str:
    """Format comparison report as human-readable text."""
    lines = [
        "Earth-1 Benchmark Comparison: Scalar vs Force Dynamics",
        "=" * 60,
        f"  Scalar MAE:  {comp.scalar_report.overall_mae:.4f}",
        f"  Force MAE:   {comp.force_report.overall_mae:.4f}",
        f"  Delta:       {comp.mae_delta:+.4f}  "
        f"({'worse' if comp.mae_delta > 0 else 'better' if comp.mae_delta < 0 else 'same'})",
        f"  Max divergence: {comp.max_divergence:.4f}",
        f"  Divergent (>2pp): {len(comp.divergent_questions)}",
        "",
        f"  {'ID':<22s} {'Scalar':>7s} {'Force':>7s} {'Div':>6s} {'S-cMAE':>7s} {'F-cMAE':>7s}",
        f"  {'-'*62}",
    ]
    for q in comp.per_question:
        flag = " ***" if q["id"] in comp.divergent_questions else ""
        sc = f"{q['scalar_cmae']:.4f}" if q['scalar_cmae'] is not None else "  -  "
        fc = f"{q['force_cmae']:.4f}" if q['force_cmae'] is not None else "  -  "
        lines.append(
            f"  {q['id']:<22s} {q['scalar_pred']:7.4f} {q['force_pred']:7.4f} "
            f"{q['divergence']:6.4f} {sc:>7s} {fc:>7s}{flag}"
        )
    return "\n".join(lines)


@dataclass
class CrossValResult:
    """Geographic cross-validation result for one question."""
    id: str
    text: str
    llm_insample_mae: Optional[float]
    llm_holdout_mae: Optional[float]
    learned_insample_mae: Optional[float]
    learned_holdout_mae: Optional[float]
    holdout_countries: List[str]
    train_countries: List[str]


@dataclass
class CrossValReport:
    """Full geographic cross-validation report."""
    n_questions: int
    n_folds: int
    llm_insample_mae: float
    llm_holdout_mae: float
    learned_insample_mae: float
    learned_holdout_mae: float
    questions: List[CrossValResult]


def run_cross_validation(
    civ: Civilization,
    questions: Optional[List[BenchmarkQuestion]] = None,
    n_folds: int = 3,
    seed: int = 42,
) -> CrossValReport:
    """Geographic cross-validation: train on some countries, test on others.

    For each question, splits its country targets into train/test sets.
    Tests two weight sources:
    1. LLM weights (hardcoded) — are they in-sample?
    2. Learned weights (calibrated from train countries) — does the engine generalize?

    If LLM holdout MAE is low, the weights capture real structure.
    If learned holdout MAE is low, the engine's force profiles enable geographic transfer.
    """
    from earth1.calibration import calibrate_single, evaluate_weights

    if questions is None:
        questions = BENCHMARK_QUESTIONS

    rng = np.random.RandomState(seed)
    results = []

    for bq in questions:
        if len(bq.country_targets) < 6:
            continue

        codes = list(bq.country_targets.keys())
        rng.shuffle(codes)

        fold_size = len(codes) // n_folds
        if fold_size < 1:
            continue

        llm_holdout_errors = []
        llm_insample_errors = []
        learned_holdout_errors = []
        learned_insample_errors = []
        last_holdout = []
        last_train = []

        for fold in range(n_folds):
            start = fold * fold_size
            end = start + fold_size if fold < n_folds - 1 else len(codes)
            holdout_codes = codes[start:end]
            train_codes = [c for c in codes if c not in holdout_codes]

            train_targets = {c: bq.country_targets[c] for c in train_codes}
            holdout_targets = {c: bq.country_targets[c] for c in holdout_codes}

            learned_w = calibrate_single(civ, bq.baseline, train_targets)

            llm_train_eval = evaluate_weights(civ, bq.baseline, bq.weights, train_targets)
            llm_hold_eval = evaluate_weights(civ, bq.baseline, bq.weights, holdout_targets)

            learned_train_eval = evaluate_weights(civ, bq.baseline, learned_w, train_targets)
            learned_hold_eval = evaluate_weights(civ, bq.baseline, learned_w, holdout_targets)

            if llm_train_eval["mae"] is not None:
                llm_insample_errors.append(llm_train_eval["mae"])
            if llm_hold_eval["mae"] is not None:
                llm_holdout_errors.append(llm_hold_eval["mae"])
            if learned_train_eval["mae"] is not None:
                learned_insample_errors.append(learned_train_eval["mae"])
            if learned_hold_eval["mae"] is not None:
                learned_holdout_errors.append(learned_hold_eval["mae"])

            last_holdout = holdout_codes
            last_train = train_codes

        results.append(CrossValResult(
            id=bq.id,
            text=bq.text,
            llm_insample_mae=round(np.mean(llm_insample_errors), 4) if llm_insample_errors else None,
            llm_holdout_mae=round(np.mean(llm_holdout_errors), 4) if llm_holdout_errors else None,
            learned_insample_mae=round(np.mean(learned_insample_errors), 4) if learned_insample_errors else None,
            learned_holdout_mae=round(np.mean(learned_holdout_errors), 4) if learned_holdout_errors else None,
            holdout_countries=last_holdout,
            train_countries=last_train,
        ))

    def safe_mean(vals):
        vals = [v for v in vals if v is not None]
        return round(float(np.mean(vals)), 4) if vals else 0.0

    return CrossValReport(
        n_questions=len(results),
        n_folds=n_folds,
        llm_insample_mae=safe_mean([r.llm_insample_mae for r in results]),
        llm_holdout_mae=safe_mean([r.llm_holdout_mae for r in results]),
        learned_insample_mae=safe_mean([r.learned_insample_mae for r in results]),
        learned_holdout_mae=safe_mean([r.learned_holdout_mae for r in results]),
        questions=sorted(results, key=lambda x: -(x.llm_holdout_mae or 0)),
    )


def format_cross_validation(report: CrossValReport) -> str:
    """Format cross-validation report."""
    lines = [
        "Earth-1 Geographic Cross-Validation",
        "=" * 65,
        f"  Questions: {report.n_questions}  |  Folds: {report.n_folds}",
        f"  Train on some countries, test on held-out countries.",
        "",
        f"  {'Metric':<28s} {'In-Sample':>10s} {'Holdout':>10s}",
        f"  {'-'*50}",
        f"  {'LLM weights MAE':<28s} {report.llm_insample_mae:10.4f} {report.llm_holdout_mae:10.4f}",
        f"  {'Learned weights MAE':<28s} {report.learned_insample_mae:10.4f} {report.learned_holdout_mae:10.4f}",
        "",
    ]

    llm_gap = report.llm_holdout_mae - report.llm_insample_mae
    learned_gap = report.learned_holdout_mae - report.learned_insample_mae

    if llm_gap < 0.03:
        lines.append("  LLM weights: holdout ≈ in-sample → weights capture real structure")
    else:
        lines.append(f"  LLM weights: holdout gap +{llm_gap:.4f} → possible overfitting to targets")

    if learned_gap < 0.05:
        lines.append("  Learned weights: engine force profiles enable geographic transfer")
    else:
        lines.append(f"  Learned weights: holdout gap +{learned_gap:.4f} → limited geographic transfer")

    lines.append("")
    lines.append(f"  NOTE: In-sample MAE {report.llm_insample_mae:.4f} is what was previously")
    lines.append(f"        reported as MAE 0.1124. The holdout MAE {report.llm_holdout_mae:.4f}")
    lines.append(f"        is the honest out-of-sample number.")

    lines.append("")
    lines.append(f"  {'ID':<22s} {'LLM-in':>7s} {'LLM-out':>8s} {'Lrn-in':>7s} {'Lrn-out':>8s}")
    lines.append(f"  {'-'*55}")

    for q in report.questions:
        li = f"{q.llm_insample_mae:.4f}" if q.llm_insample_mae is not None else "   -  "
        lo = f"{q.llm_holdout_mae:.4f}" if q.llm_holdout_mae is not None else "   -  "
        ci = f"{q.learned_insample_mae:.4f}" if q.learned_insample_mae is not None else "   -  "
        co = f"{q.learned_holdout_mae:.4f}" if q.learned_holdout_mae is not None else "   -  "
        lines.append(f"  {q.id:<22s} {li:>7s} {lo:>8s} {ci:>7s} {co:>8s}")

    return "\n".join(lines)


@dataclass
class AdversarialQuestionResult:
    id: str
    text: str
    engine_preds: Dict[str, float]
    naive_preds: Dict[str, float]
    targets: Dict[str, float]
    engine_mae: float
    naive_mae: float
    winner: str


@dataclass
class AdversarialReport:
    n_questions: int
    n_country_pairs: int
    engine_wins: int
    naive_wins: int
    ties: int
    engine_overall_mae: float
    naive_overall_mae: float
    margin: float
    results: List[AdversarialQuestionResult]


def run_adversarial_benchmark(
    civ: Civilization,
    questions: Optional[List[BenchmarkQuestion]] = None,
    epsilon: float = 0.18,
    layers: int = 8,
    use_force_dynamics: bool = True,
    event_log=None,
    t: float = 0.0,
) -> AdversarialReport:
    """Engine vs naive baseline: can the engine beat 'predict global mean for every country'?"""
    qs = questions or BENCHMARK_QUESTIONS

    all_engine_errors = []
    all_naive_errors = []
    results = []

    for bq in qs:
        if not bq.country_targets:
            continue
        q = bq.to_question()

        cells = run_segment(q, civ, "country", epsilon=epsilon, layers=layers)
        engine_preds = {c.label: c.yes_pct for c in cells}

        naive_preds = {code: bq.global_target for code in bq.country_targets}

        engine_errors = []
        naive_errors = []
        for code, target in bq.country_targets.items():
            ep = engine_preds.get(code)
            if ep is not None:
                e_err = abs(ep - target)
                n_err = abs(naive_preds[code] - target)
                engine_errors.append(e_err)
                naive_errors.append(n_err)
                all_engine_errors.append(e_err)
                all_naive_errors.append(n_err)

        e_mae = float(np.mean(engine_errors)) if engine_errors else 0.0
        n_mae = float(np.mean(naive_errors)) if naive_errors else 0.0
        if e_mae < n_mae - 0.005:
            winner = "engine"
        elif n_mae < e_mae - 0.005:
            winner = "naive"
        else:
            winner = "tie"

        results.append(AdversarialQuestionResult(
            id=bq.id, text=bq.text,
            engine_preds={k: round(v, 4) for k, v in engine_preds.items()
                          if k in bq.country_targets},
            naive_preds={k: round(v, 4) for k, v in naive_preds.items()},
            targets=bq.country_targets,
            engine_mae=round(e_mae, 4),
            naive_mae=round(n_mae, 4),
            winner=winner,
        ))

    e_overall = float(np.mean(all_engine_errors)) if all_engine_errors else 0.0
    n_overall = float(np.mean(all_naive_errors)) if all_naive_errors else 0.0

    e_wins = sum(1 for r in results if r.winner == "engine")
    n_wins = sum(1 for r in results if r.winner == "naive")
    ties = sum(1 for r in results if r.winner == "tie")

    return AdversarialReport(
        n_questions=len(results),
        n_country_pairs=len(all_engine_errors),
        engine_wins=e_wins,
        naive_wins=n_wins,
        ties=ties,
        engine_overall_mae=round(e_overall, 4),
        naive_overall_mae=round(n_overall, 4),
        margin=round(n_overall - e_overall, 4),
        results=sorted(results, key=lambda r: r.engine_mae - r.naive_mae),
    )


def format_adversarial(report: AdversarialReport) -> str:
    """Format adversarial benchmark as human-readable text."""
    verdict = ("ENGINE WINS" if report.margin > 0.005
               else "NAIVE WINS" if report.margin < -0.005
               else "DRAW")
    lines = [
        "Earth-1 Adversarial Benchmark: Engine vs Naive Baseline",
        "=" * 65,
        f"  Engine country MAE:  {report.engine_overall_mae:.4f}",
        f"  Naive country MAE:   {report.naive_overall_mae:.4f}",
        f"  Margin:              {report.margin:+.4f}  ({verdict})",
        "",
        f"  Record: Engine {report.engine_wins} / Naive {report.naive_wins} / Tie {report.ties}"
        f"  ({report.n_questions} questions, {report.n_country_pairs} country pairs)",
        "",
        f"  {'ID':<24s} {'Eng MAE':>8s} {'Naive MAE':>10s} {'Winner':>8s}",
        f"  {'-'*54}",
    ]
    for r in report.results:
        lines.append(
            f"  {r.id:<24s} {r.engine_mae:8.4f} {r.naive_mae:10.4f} {r.winner:>8s}"
        )
    return "\n".join(lines)


@dataclass
class GOQAResult:
    """GOQA benchmark result — engine vs naive vs external systems."""
    n_questions: int
    n_country_pairs: int
    engine_mae: float
    naive_mae: float
    engine_cv_mae: float
    naive_cv_mae: float
    engine_wins: int
    naive_wins: int
    ties: int
    per_question: List[Dict]


ISO3_TO_ISO2 = {
    "AND":"AD","ARG":"AR","ARM":"AM","AUS":"AU","BGD":"BD","BOL":"BO",
    "BRA":"BR","CAN":"CA","CHL":"CL","CHN":"CN","COL":"CO","CYP":"CY",
    "CZE":"CZ","DEU":"DE","ECU":"EC","EGY":"EG","ETH":"ET","GBR":"GB",
    "GRC":"GR","GTM":"GT","HKG":"HK","IDN":"ID","IND":"IN",
    "IRN":"IR","IRQ":"IQ","JOR":"JO","JPN":"JP","KAZ":"KZ","KEN":"KE",
    "KGZ":"KG","KOR":"KR","LBN":"LB","LBY":"LY","MAC":"MO","MAR":"MA",
    "MDV":"MV","MEX":"MX","MMR":"MM","MNG":"MN","MYS":"MY","NGA":"NG",
    "NIC":"NI","NIR":"GB","NLD":"NL","NZL":"NZ","PAK":"PK","PER":"PE",
    "PHL":"PH","PRI":"PR","ROU":"RO","RUS":"RU","SGP":"SG","SRB":"RS",
    "SVK":"SK","THA":"TH","TJK":"TJ","TUN":"TN","TUR":"TR","TWN":"TW",
    "UKR":"UA","URY":"UY","USA":"US","UZB":"UZ","VEN":"VE","VNM":"VN",
    "ZWE":"ZW",
}


def _goqa_prepare_tasks(civ, goqa_data, e1_codes, cv_holdout, cv_seed):
    """Phase A (serial, cheap): country targets + CV folds per question.
    The fold shuffles consume the shared RandomState in EXACTLY the
    order the legacy serial loop did — parallel results stay
    bit-identical to every recorded number.

    EARTH1_PINNED_FOLDS=<path> (F2 fix, external aggregation audit
    2026-08-18: fold noise 0.72pp dominates all claimed scale effects):
    load the partition for this cv_seed from a committed JSON instead
    of using the live draw. Pinned partitions are GENERATED from this
    same draw at the reference config, so pinned-vs-live at the same
    cv_seed and pop is identical by construction; at other pops the pin
    is what makes rungs comparable."""
    import os as _os
    pinned = None
    pin_path = _os.environ.get("EARTH1_PINNED_FOLDS", "")
    if not pin_path and _os.path.exists("data/cv_folds.json"):
        pin_path = "data/cv_folds.json"  # DEFAULT since 2026-08-18 (F2)
    if pin_path in ("off", "0"):
        pin_path = ""
    if pin_path:
        import json as _json
        pinned = _json.load(open(pin_path))["folds"].get(str(cv_seed))
        if pinned is None:
            raise ValueError(f"cv_seed {cv_seed} not in {pin_path}")
    rng = np.random.RandomState(cv_seed)
    tasks = []
    for q in goqa_data:
        ct = {}
        for iso3, dist in q['countries'].items():
            iso2 = ISO3_TO_ISO2.get(iso3)
            if iso2 and iso2 in e1_codes:
                ct[iso2] = dist['yes']
        if len(ct) < 3:
            continue
        test_codes = None
        if len(ct) >= cv_holdout + 3:
            codes = list(ct.keys())
            rng.shuffle(codes)  # always consume RNG (state parity)
            test_codes = codes[:cv_holdout]
        if pinned is not None:
            test_codes = pinned.get(q['id'], test_codes)
        tasks.append({"id": q['id'], "text": q['text'],
                      "global_yes": q['global_yes_popweighted'],
                      "ct": ct, "test_codes": test_codes})
    return tasks


# worker context shared via fork copy-on-write (Linux); set before Pool
_GOQA_CTX = {}


def _goqa_worker(task):
    """Phase B: one question's full computation — calibration,
    predictions, CV — independent of every other question."""
    import os
    os.environ.setdefault("OMP_NUM_THREADS", "2")
    from earth1.calibration import calibrate_single
    from earth1.rng import logit as _logit, sigmoid as _sigmoid

    civ = _GOQA_CTX["civ"]
    features = _GOQA_CTX["features"]
    code_to_idx = _GOQA_CTX["code_to_idx"]
    ridge_alpha = _GOQA_CTX["ridge_alpha"]
    extended = _GOQA_CTX["extended"]
    # EARTH1_ESTIMATOR=aggregated -> estimator B (sim_solver objective
    # restored; F1 fix). Default: production ridge, bit-identical.
    if os.environ.get("EARTH1_ESTIMATOR", "") == "aggregated":
        from earth1.calibration import calibrate_single_aggregated
        calibrate_single = calibrate_single_aggregated

    ct = task["ct"]
    global_yes = task["global_yes"]
    baseline = float(global_yes)
    baseline_logit = _logit(np.array([baseline]))[0]

    w = calibrate_single(civ, baseline, ct, ridge_alpha=ridge_alpha,
                         extended=extended)
    eng_errs, naive_errs, all_e, all_n = [], [], [], []
    for code, target in ct.items():
        if code not in code_to_idx:
            continue
        mask = civ.country == code_to_idx[code]
        if mask.sum() < 10:
            continue
        pred = float(_sigmoid(baseline_logit + features[mask] @ w).mean())
        eng_errs.append(abs(pred - target))
        naive_errs.append(abs(global_yes - target))
        all_e.append(abs(pred - target))
        all_n.append(abs(global_yes - target))

    cv_e, cv_n = [], []
    if task["test_codes"] is not None:
        test_codes = task["test_codes"]
        train_ct = {c: v for c, v in ct.items() if c not in set(test_codes)}
        w_cv = calibrate_single(civ, baseline, train_ct,
                                ridge_alpha=ridge_alpha, extended=extended)
        for code in test_codes:
            if code not in code_to_idx:
                continue
            mask = civ.country == code_to_idx[code]
            if mask.sum() < 10:
                continue
            pred = float(_sigmoid(baseline_logit + features[mask] @ w_cv).mean())
            cv_e.append(abs(pred - ct[code]))
            cv_n.append(abs(global_yes - ct[code]))

    e_mae = np.mean(eng_errs) if eng_errs else 0.0
    n_mae = np.mean(naive_errs) if naive_errs else 0.0
    winner = ('engine' if e_mae < n_mae - 0.005
              else 'naive' if n_mae < e_mae - 0.005 else 'tie')
    return {"result": {'id': task["id"], 'text': task["text"][:60],
                       'n_countries': len(eng_errs),
                       'engine': round(e_mae, 4), 'naive': round(n_mae, 4),
                       'winner': winner},
            "all_e": all_e, "all_n": all_n, "cv_e": cv_e, "cv_n": cv_n}


def run_goqa_benchmark(
    civ: Civilization,
    goqa_data: List[Dict],
    ridge_alpha: float = 0.1,
    extended: bool = True,
    cv_holdout: int = 5,
    cv_seed: int = 42,
) -> GOQAResult:
    """Run GOQA benchmark: 40 WVS questions x 66 countries.

    Uses extended calibration (forces + traits, 18 features) by default.
    Computes both in-sample MAE and leave-k-out cross-validation.

    EARTH1_GOQA_WORKERS > 1 parallelizes per-question across processes
    (fork/copy-on-write). Fold assignment is drawn serially first, so
    parallel output is BIT-IDENTICAL to the legacy serial path.
    """
    import os
    from earth1.calibration import _build_features, _get_country_index

    code_to_idx, country_codes = _get_country_index(civ)
    e1_codes = set(country_codes)
    features = _build_features(civ, extended=extended)

    tasks = _goqa_prepare_tasks(civ, goqa_data, e1_codes, cv_holdout, cv_seed)

    _GOQA_CTX.update(civ=civ, features=features, code_to_idx=code_to_idx,
                     ridge_alpha=ridge_alpha, extended=extended)

    workers = int(os.environ.get("EARTH1_GOQA_WORKERS", "1"))
    if workers > 1 and hasattr(os, "fork"):
        import multiprocessing as mp
        with mp.get_context("fork").Pool(workers) as pool:
            outs = pool.map(_goqa_worker, tasks)
    else:
        outs = [_goqa_worker(t) for t in tasks]

    all_e, all_n, cv_e, cv_n, results = [], [], [], [], []
    for o in outs:
        results.append(o["result"])
        all_e.extend(o["all_e"]); all_n.extend(o["all_n"])
        cv_e.extend(o["cv_e"]); cv_n.extend(o["cv_n"])

    return GOQAResult(
        n_questions=len(results),
        n_country_pairs=len(all_e),
        engine_mae=round(np.mean(all_e), 4),
        naive_mae=round(np.mean(all_n), 4),
        engine_cv_mae=round(np.mean(cv_e), 4) if cv_e else 0.0,
        naive_cv_mae=round(np.mean(cv_n), 4) if cv_n else 0.0,
        engine_wins=sum(1 for r in results if r['winner'] == 'engine'),
        naive_wins=sum(1 for r in results if r['winner'] == 'naive'),
        ties=sum(1 for r in results if r['winner'] == 'tie'),
        per_question=sorted(results, key=lambda r: r['engine'] - r['naive']),
    )


def format_goqa(report: GOQAResult) -> str:
    """Format GOQA benchmark as human-readable text."""
    lines = [
        "Earth-1 GOQA Benchmark (WVS × 66 countries)",
        "=" * 80,
        f"  Questions: {report.n_questions}  |  Country-question pairs: {report.n_country_pairs}",
        "",
        "  IN-SAMPLE (all countries used for calibration):",
        f"    Earth-1 engine:   MAE = {report.engine_mae:.4f}",
        f"    Global-avg naive: MAE = {report.naive_mae:.4f}",
        f"    Margin:                 {report.naive_mae - report.engine_mae:+.4f}",
        "",
        "  CROSS-VALIDATION (5 countries held out per question):",
        f"    Earth-1 engine:   MAE = {report.engine_cv_mae:.4f}",
        f"    Global-avg naive: MAE = {report.naive_cv_mae:.4f}",
        f"    Margin:                 {report.naive_cv_mae - report.engine_cv_mae:+.4f}",
        "",
        "  GOQA Leaderboard (from VNF database):",
        f"    Global-avg naive:        0.1370",
        f"    Claude Sonnet 4.5:       0.1733",
        f"    GPT-5:                   0.1810",
        f"    Gemini 2.5 Pro:          0.1987",
        f"    Anima (VNF best):        0.2636",
        "",
        f"  Record: Engine {report.engine_wins} W / Naive {report.naive_wins} W"
        f" / Tie {report.ties}",
        "",
        f"  {'ID':<8s} {'Text':<55s} {'N':>3s} {'Eng':>7s} {'Naive':>7s} {'Win':>7s}",
        f"  {'-'*88}",
    ]
    for r in report.per_question:
        lines.append(
            f"  {r['id']:<8s} {r['text']:<55s} {r['n_countries']:3d}"
            f" {r['engine']:7.4f} {r['naive']:7.4f} {r['winner']:>7s}"
        )
    return "\n".join(lines)


def run_cli():
    """CLI entry point for running benchmarks."""
    import argparse
    parser = argparse.ArgumentParser(description="Earth-1 Benchmark Suite")
    parser.add_argument("--pop", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--save", type=str, default=None, help="Save JSON report to path")
    parser.add_argument("--baseline", type=str, default=None, help="Compare against baseline JSON")
    parser.add_argument("--force-dynamics", action="store_true", help="Use force dynamics mode")
    parser.add_argument("--compare", action="store_true", help="Compare scalar vs force dynamics")
    parser.add_argument("--cross-validate", action="store_true", help="Geographic cross-validation")
    parser.add_argument("--adversarial", action="store_true", help="Engine vs naive baseline")
    parser.add_argument("--goqa", type=str, default=None,
                        help="Path to GOQA ground truth JSON (40 WVS questions × 66 countries)")
    args = parser.parse_args()

    if args.goqa:
        from earth1.engine import build_genesis_civilization
        print(f"Building genesis civilization ({args.pop:,} agents, seed={args.seed})...")
        civ = build_genesis_civilization(args.pop, args.seed)
        with open(args.goqa) as f:
            goqa = json.load(f)
        print(f"Running GOQA benchmark ({len(goqa['rows'])} questions)...")
        report = run_goqa_benchmark(civ, goqa['rows'])
        print(format_goqa(report))
        return

    print(f"Building civilization ({args.pop:,} agents, seed={args.seed})...")
    civ = build_civilization(args.pop, args.seed)

    if args.adversarial:
        print(f"Running adversarial benchmark: engine vs naive ({len(BENCHMARK_QUESTIONS)} questions)...")
        adv = run_adversarial_benchmark(civ)
        print(format_adversarial(adv))
        return

    if args.cross_validate:
        print(f"Running geographic cross-validation on {len(BENCHMARK_QUESTIONS)} questions...")
        cv = run_cross_validation(civ)
        print(format_cross_validation(cv))
        return

    if args.compare:
        print(f"Running {len(BENCHMARK_QUESTIONS)} questions × 2 modes...")
        comp = run_benchmark_comparison(civ)
        print(format_comparison(comp))
        return

    print(f"Running {len(BENCHMARK_QUESTIONS)} benchmark questions"
          f"{' (force dynamics)' if args.force_dynamics else ''}...")
    report = run_benchmark(civ, use_force_dynamics=args.force_dynamics)

    print(format_report(report))

    if args.save:
        save_report(report, args.save)
        print(f"\nReport saved to {args.save}")

    if args.baseline:
        regression = check_regression(report, args.baseline)
        print(f"\nRegression check: {regression['status']}")
        if regression.get("regressions"):
            for r in regression["regressions"]:
                print(f"  REGRESSION: {r['id']} ({r['was']:.4f} -> {r['now']:.4f}, +{r['delta']:.4f})")
        if regression.get("improvements"):
            for r in regression["improvements"]:
                print(f"  IMPROVED:   {r['id']} ({r['was']:.4f} -> {r['now']:.4f}, {r['delta']:.4f})")


if __name__ == "__main__":
    run_cli()
