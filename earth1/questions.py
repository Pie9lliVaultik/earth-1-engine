"""Question library with solved force weights."""
from __future__ import annotations
import numpy as np
from earth1.types import Question, Force, NUM_FORCES


def _w(**kw: float) -> np.ndarray:
    v = np.zeros(NUM_FORCES)
    for name, val in kw.items():
        v[Force[name.upper()].value] = val
    return v


QUESTIONS = [
    # --- Original 7 + rain ---
    Question("ssm", "Do people support same-sex marriage?", "belief_causal",
             0.35, _w(identity=3.4, culture=-2.2, collective=-1.2, experience=-1.6),
             "culture", "Identity-dominant — a durable consensus."),
    Question("svb", "Is your money safe at your bank right now?", "belief_causal",
             2.1, _w(fear=-3.6, collective=2.4, economics=1.1, temperament=-1.0),
             "finance", "Fear-dominant surface consensus — the SVB signature."),
    Question("immig", "Should immigration be more restricted?", "belief_causal",
             -0.1, _w(fear=2.8, identity=-2.6, culture=1.8, economics=1.4),
             "policy", "Polarized — fear and identity pull opposite camps apart."),
    Question("incumbent", "Do people approve of the incumbent government?", "belief_causal",
             -0.25, _w(economics=2.6, identity=1.4, fear=-1.2, collective=1.0),
             "politics", "Economics-dominant — shifts with conditions."),
    Question("ai_trust", "Do people trust AI to make important decisions?", "belief_causal",
             -0.6, _w(fear=-2.4, identity=2.2, experience=-1.8, temperament=1.2),
             "ai_blindspot", "Openness and age split the room."),
    Question("fourday", "Do people support a four-day work week?", "belief_causal",
             0.4, _w(desire=2.6, economics=-1.6, temperament=1.0, collective=0.8),
             "brand", "Desire-dominant — high but perishable."),
    Question("climate", "Is urgent climate action a priority?", "belief_causal",
             0.3, _w(identity=2.4, experience=-2.0, culture=1.2, economics=-1.0),
             "policy", "Generational — identity vs experience."),
    Question("rain", "Will it rain in London tomorrow?", "external_substrate",
             0.0, _w(),
             "", "Out of domain — belief is not the cause."),
    # --- Economy ---
    Question("inflation", "Are people worried about inflation?", "belief_causal",
             0.8, _w(fear=2.2, economics=3.0, experience=1.0, desire=-1.4),
             "economy", "Economics-dominant with fear amplifier."),
    Question("ubi", "Do people support universal basic income?", "belief_causal",
             -0.2, _w(desire=2.8, economics=-2.0, collective=1.6, identity=1.0),
             "economy", "Desire-collective tension."),
    Question("crypto_trust", "Do people trust cryptocurrency?", "belief_causal",
             -0.8, _w(temperament=2.8, fear=-2.2, identity=1.6, economics=1.2),
             "economy", "Temperament-driven — risk appetite splits."),
    Question("free_trade", "Do people support free trade?", "belief_causal",
             0.1, _w(economics=2.4, identity=-1.8, culture=1.4, collective=-1.0),
             "economy", "Economics vs identity tension."),
    Question("housing", "Is housing affordability a crisis?", "belief_causal",
             1.2, _w(economics=3.2, desire=2.0, fear=1.4, experience=1.0),
             "economy", "Strong consensus — economics and desire align."),
    # --- Security ---
    Question("nuclear_risk", "Is nuclear war a serious threat?", "belief_causal",
             0.6, _w(fear=3.6, collective=1.8, experience=1.2, culture=-1.0),
             "security", "Fear-dominant — collective reinforces."),
    Question("surveillance", "Should governments expand surveillance?", "belief_causal",
             -0.4, _w(fear=2.0, identity=-3.0, collective=2.2, culture=1.2),
             "security", "Identity-collective split."),
    Question("gun_control", "Should gun ownership be more regulated?", "belief_causal",
             0.2, _w(fear=2.4, identity=-2.8, culture=2.0, collective=1.6),
             "security", "Culture war — fear vs identity."),
    # --- Social ---
    Question("abortion", "Should abortion remain legal?", "belief_causal",
             0.1, _w(identity=3.0, culture=-3.2, collective=-1.4, experience=-1.0),
             "social", "Identity-culture clash — deeply polarized."),
    Question("drug_legalization", "Should recreational drugs be legalized?", "belief_causal",
             -0.3, _w(identity=2.6, temperament=2.0, collective=-2.2, culture=-1.4),
             "social", "Temperament and identity vs collective."),
    Question("death_penalty", "Should the death penalty be abolished?", "belief_causal",
             0.0, _w(identity=2.4, fear=-2.0, culture=-1.8, collective=1.6),
             "social", "Polarized identity-fear split."),
    Question("universal_healthcare", "Should healthcare be universal and free?", "belief_causal",
             0.5, _w(desire=2.8, economics=-2.2, collective=2.0, identity=1.0),
             "social", "Desire-economics tension with collective support."),
    # --- Technology ---
    Question("social_media_ban", "Should social media be restricted for minors?", "belief_causal",
             0.8, _w(fear=2.4, collective=2.6, experience=1.8, identity=-1.2),
             "technology", "Collective-fear consensus across demographics."),
    Question("genetic_editing", "Should human genetic editing be allowed?", "belief_causal",
             -0.6, _w(fear=-2.0, identity=2.8, temperament=1.6, culture=-2.4),
             "technology", "Identity-culture split with temperament factor."),
    Question("space_colonization", "Should space colonization be a priority?", "belief_causal",
             -0.4, _w(desire=2.4, temperament=1.8, economics=-2.0, experience=-1.2),
             "technology", "Desire-temperament vs economic pragmatism."),
    # --- Governance ---
    Question("democracy_trust", "Do people trust their democratic institutions?", "belief_causal",
             -0.3, _w(collective=2.8, economics=1.8, identity=-1.4, culture=1.2),
             "governance", "Collective-economics driven trust."),
    Question("eu_expansion", "Should the EU expand further?", "belief_causal",
             -0.1, _w(identity=-2.2, collective=2.0, economics=1.6, culture=1.4),
             "governance", "Identity vs collective-economic consensus."),
    Question("un_reform", "Does the UN need major reform?", "belief_causal",
             0.4, _w(collective=2.4, economics=1.2, identity=1.0, culture=-1.0),
             "governance", "Broad consensus — collective dominant."),
    # --- Environment ---
    Question("nuclear_energy", "Should nuclear energy be expanded?", "belief_causal",
             0.0, _w(fear=-2.6, economics=2.2, identity=1.4, temperament=1.0),
             "environment", "Fear-economics split."),
    Question("meat_tax", "Should meat be taxed to reduce emissions?", "belief_causal",
             -0.6, _w(identity=2.0, economics=-2.4, culture=-1.8, desire=-1.2),
             "environment", "Highly polarized — identity vs economics-culture."),
]

SURVEY_MATCHED = {"ssm", "incumbent", "climate"}

QUESTION_MAP = {q.id: q for q in QUESTIONS}


def question_by_id(qid: str) -> Question | None:
    return QUESTION_MAP.get(qid)
