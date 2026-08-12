"""Opinion-trait feedback — the inner loop that makes agents learn from interactions.

After diffusion settles, agents with strong positions get trait nudges
that reinforce their stance. Over many questions, agents develop consistent
worldviews that weren't programmed."""

from __future__ import annotations

import numpy as np

from earth1.types import Civilization, Question, Force, NUM_FORCES


FORCE_TO_TRAITS = {
    Force.FEAR: [("doubt", 1.0), ("risk_appetite", -1.0), ("neuroticism", 0.3)],
    Force.DESIRE: [("desire_intensity", 1.0)],
    Force.ECONOMICS: [("economic_field", 1.0)],
    Force.COLLECTIVE: [("openness", -0.6), ("power_distance", 0.4)],
    Force.IDENTITY: [("openness", 0.5), ("individualism", 0.5)],
    Force.CULTURE: [("culture_offset", 1.0), ("long_term_orientation", 0.1)],
    Force.EXPERIENCE: [],
    Force.TEMPERAMENT: [("risk_appetite", 0.7), ("extraversion", 0.3)],
}


def opinion_feedback(
    civ: Civilization,
    settled: np.ndarray,
    q: Question,
    force_anatomy: np.ndarray,
    learning_rate: float = 0.02,
) -> dict:
    """Nudge traits based on settled stances. Returns stats about what changed.

    Agents with extreme stances (>0.8 or <0.2) get reinforcement.
    Ambivalent agents (near 0.5) get increased doubt.
    High-alpha agents in the majority get conviction reinforcement.
    """
    n = civ.n
    strong_yes = settled > 0.8
    strong_no = settled < 0.2
    ambivalent = (settled > 0.4) & (settled < 0.6)

    dominant = Force(int(np.argmax(force_anatomy)))
    dom_traits = FORCE_TO_TRAITS.get(dominant, [])

    n_strong_yes = int(strong_yes.sum())
    n_strong_no = int(strong_no.sum())
    n_ambivalent = int(ambivalent.sum())

    for trait_name, direction in dom_traits:
        arr = getattr(civ, trait_name)
        # Strong yes: nudge traits in the direction of the dominant force
        intensity_yes = (settled[strong_yes] - 0.8) / 0.2
        arr[strong_yes] = np.clip(
            arr[strong_yes] + learning_rate * direction * intensity_yes, 0, 1)
        # Strong no: nudge traits against the dominant force
        intensity_no = (0.2 - settled[strong_no]) / 0.2
        arr[strong_no] = np.clip(
            arr[strong_no] - learning_rate * direction * intensity_no, 0, 1)

    # Ambivalent agents: increase doubt, decrease risk appetite
    if n_ambivalent > 0:
        doubt_nudge = learning_rate * 0.5
        civ.doubt[ambivalent] = np.clip(civ.doubt[ambivalent] + doubt_nudge, 0, 1)
        civ.risk_appetite[ambivalent] = np.clip(
            civ.risk_appetite[ambivalent] - doubt_nudge * 0.3, 0, 1)

    # Recompute forces from updated traits
    _recompute_forces(civ)

    # Conviction reinforcement AFTER recompute so it's not overwritten
    majority_yes = float((settled >= 0.5).mean()) >= 0.5
    if majority_yes:
        correct = settled >= 0.5
    else:
        correct = settled < 0.5
    high_alpha_correct = correct & (civ.alpha > 0.6)
    if high_alpha_correct.any():
        civ.alpha[high_alpha_correct] = np.clip(
            civ.alpha[high_alpha_correct] + learning_rate * 0.1, 0, 1)

    return {
        "n_strong_yes": n_strong_yes,
        "n_strong_no": n_strong_no,
        "n_ambivalent": n_ambivalent,
        "dominant_force": dominant.name,
        "learning_rate": learning_rate,
    }


def _recompute_forces(civ: Civilization) -> None:
    """Recalculate the 8 forces from current trait values."""
    civ.forces[:, Force.FEAR] = np.clip(
        (civ.doubt + (1.0 - civ.risk_appetite) + civ.neuroticism * 0.3) / 2.3, 0, 1)
    civ.forces[:, Force.DESIRE] = np.clip(civ.desire_intensity, 0, 1)
    civ.forces[:, Force.ECONOMICS] = np.clip(civ.economic_field, 0, 1)
    civ.forces[:, Force.COLLECTIVE] = np.clip(
        (1.0 - civ.openness) * 0.6 + civ.power_distance * 0.4, 0, 1)
    civ.forces[:, Force.IDENTITY] = np.clip(
        civ.openness * 0.5 + civ.individualism * 0.5, 0, 1)
    civ.forces[:, Force.CULTURE] = np.clip(
        0.5 + civ.culture_offset + civ.long_term_orientation * 0.1, 0, 1)
    civ.forces[:, Force.EXPERIENCE] = civ.age
    civ.forces[:, Force.TEMPERAMENT] = np.clip(
        civ.risk_appetite * 0.7 + civ.extraversion * 0.3, 0, 1)
    civ.means[:] = civ.forces.mean(axis=0)
    civ.alpha[:] = np.clip(
        0.28 + 0.5 * civ.openness - 0.12 * (1.0 - civ.openness), 0, 1)
