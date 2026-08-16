"""Opinion-trait feedback — the inner loop that makes agents learn from interactions.

After diffusion settles, agents with strong positions get trait nudges
that reinforce their stance. Over many questions, agents develop consistent
worldviews that weren't programmed.

Two laws fixed after the 2026-08-16 external audit:

1. DIRECTION comes from the sign of the dominant force's question weight.
   Reinforcing a strong-YES agent means moving them toward MORE YES:
   if the dominant force carries a NEGATIVE weight, its traits must go
   DOWN for a YES-reinforcement, not up. The old code reinforced by
   force name alone and measurably pushed strong-YES agents away from
   their own stance when weights were negative.

2. Trait changes propagate to forces LOCALLY through fixed sensitivities
   (the same coefficients the old global rebuild encoded), touching only
   the nudged agents and channels. The old `_recompute_forces` rebuilt
   every agent's forces from a formula that ignored genesis conditioning
   (Hofstede, Inglehart, regional deltas, income, education) — one call
   changed forces for ~84% of agents without a single trait changing.
   Genesis priors are now preserved exactly; feedback with no strong
   agents is the identity.
"""

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

# ∂force/∂trait — the sensitivities implied by the retired global rebuild,
# now applied incrementally so genesis priors survive.
TRAIT_FORCE_SENSITIVITY = {
    "doubt": [(Force.FEAR, 1.0 / 2.3)],
    "risk_appetite": [(Force.FEAR, -1.0 / 2.3), (Force.TEMPERAMENT, 0.7)],
    "neuroticism": [(Force.FEAR, 0.3 / 2.3)],
    "desire_intensity": [(Force.DESIRE, 1.0)],
    "economic_field": [(Force.ECONOMICS, 1.0)],
    "openness": [(Force.COLLECTIVE, -0.6), (Force.IDENTITY, 0.5)],
    "power_distance": [(Force.COLLECTIVE, 0.4)],
    "individualism": [(Force.IDENTITY, 0.5)],
    "culture_offset": [(Force.CULTURE, 1.0)],
    "long_term_orientation": [(Force.CULTURE, 0.1)],
    "extraversion": [(Force.TEMPERAMENT, 0.3)],
}


def apply_trait_delta(
    civ: Civilization,
    mask: np.ndarray,
    trait_name: str,
    delta,
) -> None:
    """Nudge one trait for masked agents and propagate the ACTUAL change
    (post-clip) into the affected force channels. The only sanctioned way
    for living dynamics to modify traits."""
    arr = getattr(civ, trait_name)
    before = arr[mask].copy()
    arr[mask] = np.clip(before + delta, 0.0, 1.0)
    actual = arr[mask] - before
    for force, coeff in TRAIT_FORCE_SENSITIVITY.get(trait_name, []):
        fi = int(force)
        civ.forces[mask, fi] = np.clip(
            civ.forces[mask, fi] + coeff * actual, 0.0, 1.0)


def opinion_feedback(
    civ: Civilization,
    settled: np.ndarray,
    q: Question,
    force_anatomy: np.ndarray,
    learning_rate: float = 0.02,
) -> dict:
    """Nudge traits based on settled stances. Returns stats about what changed.

    Agents with extreme stances (>0.8 or <0.2) get reinforcement TOWARD
    their stance (weight-sign aware). Ambivalent agents (near 0.5) get
    increased doubt. High-alpha agents in the majority get conviction
    reinforcement.
    """
    strong_yes = settled > 0.8
    strong_no = settled < 0.2
    ambivalent = (settled > 0.4) & (settled < 0.6)

    dominant = Force(int(np.argmax(force_anatomy)))
    dom_traits = FORCE_TO_TRAITS.get(dominant, [])

    # The audit's sign law: reinforcement direction must follow the sign
    # of the dominant force's WEIGHT in this question. w>0: YES-agents
    # need the force higher; w<0: YES-agents need it LOWER. w==0: the
    # dominant-by-energy force doesn't move this answer — no reinforcement.
    w_sign = float(np.sign(q.weights[int(dominant)])) if q.weights is not None else 1.0

    n_strong_yes = int(strong_yes.sum())
    n_strong_no = int(strong_no.sum())
    n_ambivalent = int(ambivalent.sum())

    if w_sign != 0.0:
        for trait_name, direction in dom_traits:
            d = direction * w_sign
            intensity_yes = (settled[strong_yes] - 0.8) / 0.2
            apply_trait_delta(civ, strong_yes, trait_name,
                              learning_rate * d * intensity_yes)
            intensity_no = (0.2 - settled[strong_no]) / 0.2
            apply_trait_delta(civ, strong_no, trait_name,
                              -learning_rate * d * intensity_no)

    # Ambivalent agents: increase doubt, decrease risk appetite
    if n_ambivalent > 0:
        apply_trait_delta(civ, ambivalent, "doubt", learning_rate * 0.5)
        apply_trait_delta(civ, ambivalent, "risk_appetite",
                          -learning_rate * 0.5 * 0.3)

    # Conviction reinforcement (alpha is not force-coupled)
    majority_yes = float((settled >= 0.5).mean()) >= 0.5
    correct = (settled >= 0.5) if majority_yes else (settled < 0.5)
    high_alpha_correct = correct & (civ.alpha > 0.6)
    if high_alpha_correct.any():
        civ.alpha[high_alpha_correct] = np.clip(
            civ.alpha[high_alpha_correct] + learning_rate * 0.1, 0, 1)

    # Keep the population anchor tracking the (locally) updated forces.
    civ.means[:] = civ.forces.mean(axis=0)

    return {
        "n_strong_yes": n_strong_yes,
        "n_strong_no": n_strong_no,
        "n_ambivalent": n_ambivalent,
        "dominant_force": dominant.name,
        "weight_sign": w_sign,
        "learning_rate": learning_rate,
    }


def _recompute_forces(civ: Civilization) -> None:
    """RETIRED as a living-path operation (2026-08-16 audit).

    The global rebuild ignored genesis conditioning (regional deltas,
    Hofstede/Inglehart structure, demography) and changed forces for
    ~84% of agents with zero trait changes. Living dynamics must use
    apply_trait_delta. Kept only because external callers may still
    reference it; it now raises to prevent silent prior erasure.
    """
    raise RuntimeError(
        "_recompute_forces is retired: it erased genesis/regional priors. "
        "Use apply_trait_delta for living trait->force updates.")
