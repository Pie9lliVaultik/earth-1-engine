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
]

SURVEY_MATCHED = {"ssm", "incumbent", "climate"}

QUESTION_MAP = {q.id: q for q in QUESTIONS}


def question_by_id(qid: str) -> Question | None:
    return QUESTION_MAP.get(qid)
