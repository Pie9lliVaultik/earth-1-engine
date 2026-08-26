"""INFLUENCE — the conviction-conditioned kernel. The amplifying channel.

Construction error #2, named by Pietro: "an averaging kernel that can
only contract distributions. Mathematically proven by sweep — no
parameter setting can manufacture extremes."

He is right, and the proof is trivial once stated: if every agent moves
toward the mean of its neighbours, the variance of the population is a
non-increasing function of time. An averaging operator is a contraction.
No amount of tuning makes a contraction expand. That is why the world
absorbed a perturbation and reconverged, and why the tails were empty.

THE FIX — people do not average, they ALIGN.

When someone who is certain talks to someone who is unsure, the unsure
person does not move to the midpoint. They move toward the certain
person's SIDE. Conviction is what converts a conversation into a
recruitment. That single change turns the operator from a contraction
into an expansion, because agents above the midline are pulled to 1 and
agents below it are pulled to 0.

    alignment = conviction ** beta
    target moves toward the source's POLE     with weight alignment
    target moves toward the source's VALUE    with weight 1 - alignment

beta = 0 recovers the old averaging law exactly, so the old behaviour is
a special case rather than something deleted. beta > 0 opens the
polarizing channel. This is the parameter that decides whether the world
is chaotic, and it is measured rather than assumed — see earth1/chaos.py.

CONVICTION IS ALSO EARNED. An agent whose neighbours agree with it grows
more certain; an agent surrounded by disagreement grows less so. That is
the second amplifier, and it is what makes clusters harden into camps
instead of relaxing back into the mean.
"""
from __future__ import annotations

import numpy as np

BETA = 1.0            # conviction exponent; 0 = pure averaging (legacy)
ETA = 0.18            # propagation rate per layer
CONVICTION_GAIN = 0.06    # how fast agreement hardens conviction
CONVICTION_DECAY = 0.02   # 0.8 A/B arm-B value ONLY - decay is DISABLED in production


def propagate_meanfield_legacy(forces: np.ndarray, alpha: np.ndarray, adj,
              beta: float = BETA, eta: float = ETA,
              layers: int = 1,
              susceptibility: np.ndarray | None = None) -> np.ndarray:
    """One or more layers of conviction-conditioned force propagation.

    forces (N, K), alpha (N,) conviction in [0, 1], adj sparse (N, N).
    Returns the NEW forces; does not mutate the input.

    Vectorized entirely through sparse matmul — every agent talks to
    every neighbour simultaneously, which is what makes this affordable
    at population scale.
    """
    f = forces.copy()
    deg = np.asarray(adj.sum(axis=1)).ravel()
    safe_deg = np.maximum(deg, 1.0)
    a = np.clip(alpha, 0.0, 1.0) ** beta        # alignment weight
    inv_a = 1.0 - a

    n, k = forces.shape
    for _ in range(max(1, layers)):
        # each neighbour's POLE: which side of the midline they are on.
        # this is the term that expands — a source at 0.61 does not pull
        # you to 0.61, it pulls you toward 1.0
        pole = (f > 0.5).astype(f.dtype)

        # weighted sums over neighbours, all at once — and all in ONE
        # pass over the adjacency (0.7: four separate products streamed
        # the full graph four times per layer; csr_matvecs accumulates
        # each column in the same row order as the separate calls, so
        # stacking is bit-identical)
        X = np.empty((n, 2 * k + 2), dtype=f.dtype)
        X[:, :k] = a[:, None] * pole
        X[:, k:2 * k] = inv_a[:, None] * f
        X[:, 2 * k] = a
        X[:, 2 * k + 1] = inv_a
        Y = np.asarray(adj @ X)
        align_num = Y[:, :k]                       # (N, K)
        avg_num = Y[:, k:2 * k]                    # (N, K)
        align_den = Y[:, 2 * k]                    # (N,)
        avg_den = Y[:, 2 * k + 1]                  # (N,)

        pull_pole = align_num - f * align_den[:, None]
        pull_mean = avg_num - f * avg_den[:, None]

        move = eta * (pull_pole + pull_mean) / safe_deg[:, None]
        # SUSCEPTIBILITY: the same push does not move two people the
        # same distance. This is where mental health, addiction, age,
        # conviction and hunger decide who is movable — see
        # earth1/susceptibility.py.
        if susceptibility is not None:
            move = move * susceptibility
        f = np.clip(f + move, 0.0, 1.0)
    return f


def update_conviction_ratchet_legacy(forces: np.ndarray, alpha: np.ndarray, adj,
                      gain: float = CONVICTION_GAIN,
                      _experimental_decay_0_8_ab: float = 0.0) -> np.ndarray:
    """Agreement hardens conviction; disagreement softens it.

    The second amplifier. Without it, clusters form and then relax. With
    it, a cluster that agrees becomes a cluster that is CERTAIN, which
    by the kernel above makes it better at recruiting — and that loop is
    what produces cascades that do not simply decay.

    ISOLATION DECAY IS DISABLED. The original code carried a
    `- decay * 0.0` no-op while the docstring claimed isolation softens
    conviction — implementation and documentation disagreed, and alpha
    has been a ratchet for the world's entire history. Making the term
    real changes the conviction kernel, propagation, polarization and
    possibly the chaotic regime — that is physics, not a bug fix, so
    it is adjudicated by the registered 0.8 A/B (arm A: disabled, as
    here; arm B: `_experimental_decay_0_8_ab=CONVICTION_DECAY`), never
    switched on silently. Production output is bit-identical to the
    pre-0.1 code.
    """
    deg = np.maximum(np.asarray(adj.sum(axis=1)).ravel(), 1.0)
    pole = (forces > 0.5).astype(forces.dtype)
    # fraction of neighbours sharing this agent's side, averaged over
    # every force channel
    nb_pole = (adj @ pole) / deg[:, None]
    agreement = 1.0 - np.abs(nb_pole - pole).mean(axis=1)   # (N,) in [0,1]
    out = alpha + gain * (agreement - 0.5) * 2.0
    if _experimental_decay_0_8_ab:
        # THE REGISTERED 0.8 A/B ARM — never taken in production. The
        # isolation channel softens conviction for the unconnected.
        isolation = 1.0 / (1.0 + deg)
        out = out - _experimental_decay_0_8_ab * isolation
    return np.clip(out, 0.02, 1.0)


# ═══════════════════════════════════════════════════════════════════
# CANONICAL SOCIAL PHYSICS — the validated candidate 76a574c, ported
# verbatim from the 0.8 laboratory (field_lab.make_dyadic_propagate_v6,
# make_dyadic_feed_v6 companion in feed.py, dyadic_conviction).
# Phase 0.5 canonicalization (ops/alive/CANONICALIZATION_PROGRAM.md).
#
# THE ENCOUNTER IS THE CAUSAL UNIT. Each day every agent meets
# K_ENCOUNTERS tie-weighted partners and moves MU_INFLUENCE of the way
# toward each partner's VALUE (never a neighbourhood mean — mean-field
# aggregation destroys minority signal and hides disagreement; IT6).
# The SAME encounters supply the evidence that drives conviction: the
# signed "drive" (agreement = +, disagreement = −) accumulates through
# the day's scratch and is consumed once by update_conviction.
#
# ENCOUNTER RNG CONTRACT: partner draws use a private generator seeded
# by the tick index (ENCOUNTER_SEED_TIE + day). Two worlds ticking the
# same day draw the same partners — common random numbers for paired
# branches (treatment vs control), a registered property of the
# candidate, not an accident.
#
# The functions above (propagate_meanfield_legacy,
# update_conviction_ratchet_legacy) are LEGACY_COMPARISON_ONLY: the
# retired incumbent laws, kept solely as the Stage-B broken twins
# ("zero influence", "conviction ratchet"). They are never on the
# canonical path.
# ═══════════════════════════════════════════════════════════════════

K_ENCOUNTERS = 3            # IT6 (derived; validated)
MU_INFLUENCE = 0.05         # IT6 per-encounter move toward partner value
CONVICTION_GAIN_DYADIC = 0.003   # C3 log-odds gain per unit mean drive
ENCOUNTER_SEED_TIE = 920_000
ENCOUNTER_SEED_FEED = 930_000


class DayScratch:
    """The day's encounter evidence. Created at the start of a tick,
    consumed (and zeroed) by update_conviction. Never persisted."""
    __slots__ = ("drive_acc", "enc_count")

    def __init__(self, n: int):
        self.drive_acc = np.zeros(n)
        self.enc_count = np.zeros(n, dtype=np.int64)


def new_day_scratch(n: int) -> DayScratch:
    return DayScratch(n)


def sample_partners(csr, rng):
    """One tie-weighted partner per agent (vectorized inverse-CDF).
    Agents with no ties get partner=-1."""
    indptr, indices, data = csr.indptr, csr.indices, csr.data
    n = csr.shape[0]
    csum = np.concatenate([[0.0], np.cumsum(data)])
    row_lo = csum[indptr[:-1]]
    row_hi = csum[indptr[1:]]
    rowsum = row_hi - row_lo
    has = rowsum > 0
    r = row_lo + rng.random(n) * rowsum
    pos = np.searchsorted(csum, r, side="right") - 1
    pos = np.clip(pos, indptr[:-1], np.maximum(indptr[1:] - 1,
                                               indptr[:-1]))
    partner = np.where(has, indices[np.clip(pos, 0,
                                            indices.size - 1)], -1)
    return partner, has


def dyadic_move(f, partner, has, mu, susceptibility=None,
                gate=None, weights=None):
    tgt = f[np.clip(partner, 0, f.shape[0] - 1)]
    delta = tgt - f
    if gate is not None:
        delta = np.where(np.abs(delta) <= gate, delta, 0.0)
    move = mu * delta
    if weights is not None:
        move = move * weights[None, :]
    if susceptibility is not None:
        move = move * susceptibility
    move[~has] = 0.0
    return move


def accumulate_drive(scratch: DayScratch, f_pre, partner, has):
    """Signed encounter evidence: drive_e = clip((0.5 − d_e)/0.5, −1, 1)
    where d_e is the mean channel distance to the partner BEFORE the
    move. Accumulated per agent; the count of real encounters too."""
    tgt = f_pre[np.clip(partner, 0, f_pre.shape[0] - 1)]
    d_e = np.abs(f_pre - tgt).mean(axis=1)
    drive = np.clip((0.5 - d_e) / 0.5, -1.0, 1.0)
    drive[~has] = 0.0
    scratch.drive_acc += drive
    scratch.enc_count += has.astype(np.int64)


def propagate(forces: np.ndarray, alpha: np.ndarray, adj, *,
              day: int, scratch: DayScratch,
              susceptibility: np.ndarray | None = None,
              k: int = K_ENCOUNTERS, mu: float = MU_INFLUENCE,
              **_ignored) -> np.ndarray:
    """Dyadic influence: k encounters per agent per day, each a move of
    mu toward the partner's value (susceptibility-weighted), and the
    same encounters accumulate conviction evidence into `scratch`."""
    f = forces.copy()
    csr = adj if hasattr(adj, "indptr") else adj.tocsr()
    rng = np.random.default_rng(ENCOUNTER_SEED_TIE + int(day))
    for _ in range(k):
        partner, has = sample_partners(csr, rng)
        accumulate_drive(scratch, f, partner, has)
        mv = dyadic_move(f, partner, has, mu, susceptibility)
        f = np.clip(f + mv, 0, 1)
    return f


def update_conviction(forces: np.ndarray, alpha: np.ndarray, adj, *,
                      scratch: DayScratch,
                      gain: float = None,
                      **_ignored) -> np.ndarray:
    """C3 log-odds conviction driven by the day's ACCUMULATED encounter
    evidence (mean drive over today's encounters; no encounters ⇒ no
    update). Bounds (0.02, 1.0) are asymptotes of the log-odds form,
    not a ratchet. Consumes and zeroes the scratch."""
    if gain is None:
        gain = CONVICTION_GAIN_DYADIC   # read at call time: patchable
    n_enc = np.maximum(scratch.enc_count, 1)
    drive = scratch.drive_acc / n_enc
    drive[scratch.enc_count == 0] = 0.0
    a = np.clip(alpha, 0.02, 0.98)
    logit = np.log(a / (1.0 - a)) + gain * drive
    out = np.clip(1.0 / (1.0 + np.exp(-logit)), 0.02, 1.0)
    scratch.drive_acc[:] = 0.0
    scratch.enc_count[:] = 0
    return out
