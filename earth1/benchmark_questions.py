"""BENCHMARK QUESTION DATA — pure data, engine-free.

The registered benchmark question set (text, survey baselines, force
weight vectors, lenses, targets) extracted from the retired
`benchmark.py` harness (Phase 0.5 Program 3) so that living-world
modules (confidence, training, the canonical benchmark entry point)
never import the dead engine family. Scoring harnesses live in
`benchmark_living.py` (canonical) and `legacy_benchmark.py`
(LEGACY_COMPARISON_ONLY).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from earth1.questions import _w
from earth1.types import Question, Force, NUM_FORCES, FORCE_NAMES


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
