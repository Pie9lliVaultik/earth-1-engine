"""Force field dynamics — agents communicate through force signatures.

Replaces scalar diffusion with force-vector propagation. Agents broadcast
their centered force state. Neighbors absorb selectively based on non-linear
susceptibility. Absorption leaves trait residue — learning built into
the physics of interaction.

This is the "language" of Earth-1: not words, not tokens, but force
configurations propagating through a social graph with force-specific
absorption rates."""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
from scipy import sparse

from earth1.types import Civilization, Question, Force, NUM_FORCES
from earth1.feedback import FORCE_TO_TRAITS, apply_trait_delta


# ---------------------------------------------------------------------------
# Deep copy (used by loop.py and others)
# ---------------------------------------------------------------------------

def _deep_copy_civ(civ: Civilization) -> Civilization:
    """Create a fully independent copy of a civilization with writable arrays."""
    kwargs = {}
    for attr in civ.__dataclass_fields__:
        val = getattr(civ, attr)
        if isinstance(val, np.ndarray):
            kwargs[attr] = val.copy()
        elif hasattr(val, 'copy'):
            kwargs[attr] = val.copy()
        else:
            kwargs[attr] = val
    return Civilization(**kwargs)


# ---------------------------------------------------------------------------
# Susceptibility
# ---------------------------------------------------------------------------

def _sigmoid(x: np.ndarray, gain: float = 4.0, center: float = 0.5) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-gain * (x - center)))


def _saturation(force_values: np.ndarray, strength: float = 1.5) -> np.ndarray:
    """Diminishing returns near extremes. Max at 0.5, zero at 0 and 1."""
    raw = 1.0 - strength * np.power(2.0 * force_values - 1.0, 2)
    return np.clip(raw, 0.0, 1.0)


def compute_susceptibility(civ: Civilization, gain: float = 4.0) -> np.ndarray:
    """Compute (N, 8) susceptibility matrix from traits.

    Each agent's susceptibility to each force is a non-linear function of
    the same traits that generate that force. The sigmoid creates tipping
    points. Saturation damping prevents runaway: agents near force extremes
    absorb less (you can't become infinitely afraid).
    """
    n = civ.n
    S = np.zeros((n, NUM_FORCES), dtype=np.float64)

    # FEAR: doubtful, risk-averse, neurotic agents absorb fear
    basis = (civ.doubt + (1.0 - civ.risk_appetite) + civ.neuroticism * 0.3) / 2.3
    S[:, Force.FEAR] = _sigmoid(basis, gain) * _saturation(civ.forces[:, Force.FEAR])

    # DESIRE: desiring agents absorb desire signals
    S[:, Force.DESIRE] = _sigmoid(civ.desire_intensity, gain) * _saturation(civ.forces[:, Force.DESIRE])

    # ECONOMICS: economically aware agents absorb economic signals
    S[:, Force.ECONOMICS] = _sigmoid(civ.economic_field, gain) * _saturation(civ.forces[:, Force.ECONOMICS])

    # COLLECTIVE: conformist agents absorb collective pressure
    basis = (1.0 - civ.openness) * 0.6 + civ.power_distance * 0.4
    S[:, Force.COLLECTIVE] = _sigmoid(basis, gain) * _saturation(civ.forces[:, Force.COLLECTIVE])

    # IDENTITY: open/individualistic agents absorb identity signals
    basis = civ.openness * 0.5 + civ.individualism * 0.5
    S[:, Force.IDENTITY] = _sigmoid(basis, gain) * _saturation(civ.forces[:, Force.IDENTITY])

    # CULTURE: culturally oriented agents absorb cultural signals
    basis = np.clip(0.5 + civ.culture_offset + civ.long_term_orientation * 0.1, 0, 1)
    S[:, Force.CULTURE] = _sigmoid(basis, gain) * _saturation(civ.forces[:, Force.CULTURE])

    # EXPERIENCE: empathetic young agents absorb experience signals
    basis = civ.empathy * 0.7 + (1.0 - civ.age) * 0.3
    S[:, Force.EXPERIENCE] = _sigmoid(basis, gain) * _saturation(civ.forces[:, Force.EXPERIENCE])

    # TEMPERAMENT: extraverted agents absorb temperament signals
    basis = civ.risk_appetite * 0.5 + civ.extraversion * 0.5
    S[:, Force.TEMPERAMENT] = _sigmoid(basis, gain) * _saturation(civ.forces[:, Force.TEMPERAMENT])

    return S


# ---------------------------------------------------------------------------
# Agent-relative temporal filtering
# ---------------------------------------------------------------------------

def agent_relative_decay(
    dt: float,
    half_life: float,
    civ: Civilization,
    temporal_mass_rate: float = 0.3,
    lto_rate: float = 0.5,
) -> np.ndarray:
    """Per-agent decay factor for an event. Returns (N,).

    Three mechanisms:
    - Temporal mass: older agents have more experience, new events are
      a smaller fraction — slower to shift
    - Temporal orientation: high long_term_orientation agents remember
      events longer (slower decay)
    - Both create agent-specific half-lives
    """
    if dt < 0:
        return np.zeros(civ.n)
    if half_life <= 0:
        return np.ones(civ.n)

    # Agent-specific half-life: base × LTO stretch × age stability
    agent_half = half_life * (1.0 + lto_rate * civ.long_term_orientation)

    base_decay = np.power(2.0, -dt / agent_half)

    # Temporal mass: older agents are harder to shift
    temporal_mass = 1.0 / (1.0 + temporal_mass_rate * civ.age)

    return base_decay * temporal_mass


# ---------------------------------------------------------------------------
# Force-aware diffusion
# ---------------------------------------------------------------------------

def diffuse_forces(
    s0: np.ndarray,
    civ: Civilization,
    q: Question,
    susceptibility: np.ndarray,
    epsilon: float,
    layers: int,
    residue_rate: float = 0.0005,
    field_shift: np.ndarray | None = None,
) -> Tuple[List[np.ndarray], np.ndarray]:
    """Force-aware bounded-confidence diffusion.

    Instead of propagating scalar stances, agents broadcast their centered
    force vectors. Neighbors absorb selectively based on susceptibility.
    The absorbed forces are projected through question weights to produce
    stance influence.

    Returns (stance_snapshots, force_residues).
    force_residues is (N, 8) — accumulated absorption from all layers.
    """
    n = civ.n
    snapshots = [s0.copy()]
    cur = s0.copy()
    residues = np.zeros((n, NUM_FORCES), dtype=np.float64)

    rows, cols = civ.adj.nonzero()
    edge_weights = np.asarray(civ.adj[rows, cols]).ravel()
    centered = civ.forces - civ.means[np.newaxis, :]  # (N, 8)
    if field_shift is not None:
        if field_shift.ndim == 1:
            centered = centered + field_shift[np.newaxis, :]
        else:
            centered = centered + field_shift

    for _ in range(layers):
        # Epsilon filtering: only interact with stance-proximate neighbors
        diffs = np.abs(cur[cols] - cur[rows])
        mask = diffs < epsilon
        mask_float = mask.astype(np.float64)

        w_mask = edge_weights * mask_float
        weight_sums = sparse.csr_matrix(
            (w_mask, (rows, cols)), shape=(n, n))
        w_totals = np.asarray(weight_sums.sum(axis=1)).ravel()
        safe_w = np.where(w_totals > 0, w_totals, 1.0)

        received = np.zeros((n, NUM_FORCES), dtype=np.float64)
        for f in range(NUM_FORCES):
            vals = centered[cols, f] * w_mask
            force_adj = sparse.csr_matrix((vals, (rows, cols)), shape=(n, n))
            received[:, f] = np.asarray(force_adj.sum(axis=1)).ravel() / safe_w

        # Susceptibility-weighted absorption: each agent absorbs selectively
        absorbed = received * susceptibility  # (N, 8)

        # Project absorbed forces through question weights → stance influence
        stance_influence = absorbed @ q.weights  # (N,)

        # Apply with alpha gating: s = alpha * s0 + (1-alpha) * (social_stance)
        # social_stance = current stance modified by force absorption
        social = cur + stance_influence
        social = np.clip(social, 0, 1)

        cur_new = np.where(
            w_totals > 0,
            civ.alpha * s0 + (1.0 - civ.alpha) * social,
            cur,
        )
        cur = cur_new
        snapshots.append(cur.copy())

        # Accumulate residue — the learning signal
        # Alpha-gated: convicted agents resist trait change
        alpha_gate = (1.0 - civ.alpha)[:, np.newaxis]  # (N, 1)
        residues += absorbed * residue_rate * alpha_gate

    return snapshots, residues


# ---------------------------------------------------------------------------
# Trait residue application
# ---------------------------------------------------------------------------

def apply_residues(
    civ: Civilization,
    residues: np.ndarray,
    regression_rate: float = 0.0,
    baseline_forces: np.ndarray | None = None,
) -> dict:
    """Apply accumulated force residues to traits.

    Three damping mechanisms prevent runaway without compressing variance:
    1. Extreme resistance — nudges diminish as traits approach 0 or 1
    2. Alpha-gating in diffuse_forces (convicted agents accumulate less)
    3. Saturation damping in susceptibility (extreme-force agents absorb less)

    Regression defaults to off — it compresses population variance, killing
    emergence. Enable only when explicitly needed.

    Returns stats about magnitude of trait changes.
    """
    total_nudge = 0.0
    n_traits_changed = 0
    _ALL = np.ones(civ.n, dtype=bool)

    for force_idx in range(NUM_FORCES):
        force = Force(force_idx)
        trait_mappings = FORCE_TO_TRAITS.get(force, [])
        if not trait_mappings:
            continue

        force_residue = residues[:, force_idx]  # (N,)

        for trait_name, direction in trait_mappings:
            arr = getattr(civ, trait_name)
            nudge = force_residue * direction

            # Extreme resistance: nudges diminish near 0 and 1
            headroom = np.where(nudge > 0, 1.0 - arr, arr)
            nudge = nudge * headroom

            # Non-linear regression: quadratic pull toward 0.5
            # Gentle near center, aggressive near extremes
            if regression_rate > 0:
                deviation = arr - 0.5
                regression = regression_rate * deviation * np.abs(deviation) * 2.0
                nudge = nudge - regression

            # canonical trait->force propagation: only nudged agents'
            # affected channels move; genesis/regional priors survive
            apply_trait_delta(civ, _ALL, trait_name, nudge)
            total_nudge += float(np.abs(nudge).sum())
            n_traits_changed += 1

    civ.means[:] = civ.forces.mean(axis=0)

    return {
        "total_nudge": total_nudge,
        "n_traits_changed": n_traits_changed,
        "mean_residue_magnitude": float(np.abs(residues).mean()),
    }


# ---------------------------------------------------------------------------
# Full forward pass with force dynamics
# ---------------------------------------------------------------------------

def run_with_dynamics(
    civ: Civilization,
    q: Question,
    epsilon: float = 0.18,
    layers: int = 8,
    susceptibility: np.ndarray | None = None,
    field_shift: np.ndarray | None = None,
    event_shift: np.ndarray | None = None,
    residue_rate: float = 0.0005,
    gain: float = 4.0,
) -> Tuple[np.ndarray, np.ndarray, List[np.ndarray]]:
    """Run a question through force-aware dynamics.

    ONE LAW: event_shift acts on opinion via the response law inside
    project_all ONLY. It never enters the broadcast channel — a
    constructed sign-conflict showed events propagated through the
    cross-sectional weights REVERSING the validated response law.
    field_shift (counterfactual/coupling field state) keeps its legacy
    semantics in both projection and propagation.

    Returns (settled_stances, force_residues, snapshots).
    Does NOT apply residues to traits — caller decides when to do that.
    """
    from earth1.forces import project_all

    s0 = project_all(civ, q, field_shift=field_shift, event_shift=event_shift)

    if susceptibility is None:
        susceptibility = compute_susceptibility(civ, gain=gain)

    snapshots, residues = diffuse_forces(
        s0, civ, q, susceptibility, epsilon, layers, residue_rate,
        field_shift=field_shift,
    )

    return snapshots[-1], residues, snapshots
