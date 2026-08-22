"""FEED — social media, which is not a social tie. It is a different physics.

Every other channel in this world connects people who are near each
other: the same house, the same firm, the same street, the same life
stage. Distance is geographic or biographical, and it is SYMMETRIC —
your neighbour is your neighbour.

A feed is none of those things.

  IT IS SELECTED, NOT ENCOUNTERED. You do not meet the people in your
  feed, an optimiser chooses them, and it chooses them by predicted
  engagement. What engages a person most reliably is what they already
  believe, stated more strongly. So the feed is a homophily machine
  running at a speed no village could reach: not "people like me" but
  "people like me, filtered, ranked, and served continuously".

  IT IS ASYMMETRIC AND SCALE-FREE. A handful of accounts reach
  millions and hear back from nobody. That is nothing like a
  conversation and it breaks the reciprocity every other tie has.

  IT IS AROUSAL-WEIGHTED. High-arousal content travels further than
  calm content, and this is measured, not alleged. Fear and identity
  propagate; nuance does not. So the feed does not amplify opinion
  uniformly — it amplifies SPECIFIC CHANNELS, which is why it changes
  the shape of a population rather than just the speed.

The consequence, in this model's own terms: the feed is a polarizing
kernel with a much higher effective beta, applied only to the arousing
channels, along edges chosen for agreement. It is the strongest
variance-generating structure in the world, and it did not exist here
until now — which is a strange omission in an engine built to model
opinion.

Access is unequal. Where connectivity is low the feed barely exists,
so a population's exposure to this physics is itself a function of
where it lives.
"""
from __future__ import annotations

import numpy as np
from scipy import sparse

from earth1.types import Force

# how much stronger the feed's alignment pressure is than a conversation
FEED_BETA_MULTIPLIER = 2.2
FEED_ETA = 0.10
# which channels the optimiser actually amplifies. Arousal travels;
# nuance does not. Measured repeatedly in diffusion studies.
AROUSAL_WEIGHT = {
    Force.FEAR: 1.00, Force.IDENTITY: 0.95, Force.COLLECTIVE: 0.55,
    Force.DESIRE: 0.45, Force.CULTURE: 0.30, Force.ECONOMICS: 0.25,
    Force.EXPERIENCE: 0.10, Force.TEMPERAMENT: 0.10,
}
FEED_SIZE = 24           # accounts a connected agent effectively reads
INFLUENCER_SHARE = 0.001


def build_feed(civ, knowledge, seed: int = 0):
    """Wire the feed: chosen for agreement, not for proximity.

    Edges are drawn toward agents whose stance already resembles the
    reader's, which is what an engagement optimiser converges on
    whatever its designers intended.
    """
    rng = np.random.default_rng(seed ^ 0xFEED)
    n = civ.n
    online = knowledge.connected

    # rank agents on the axis the feed cares about most, then connect
    # each reader to others NEAR THEM on that axis. Sorting makes this
    # O(n log n) instead of O(n^2), which is what makes it affordable.
    axis = (civ.forces[:, Force.IDENTITY] - civ.forces[:, Force.FEAR])
    order = np.argsort(axis)
    rank = np.empty(n, dtype=np.int64)
    rank[order] = np.arange(n)

    rows, cols = [], []
    for _ in range(6):
        # a reader sees people within a narrow band of their own position
        jitter = rng.integers(-max(n // 200, 2), max(n // 200, 2), n)
        peer_rank = np.clip(rank + jitter, 0, n - 1)
        src = np.flatnonzero(online)
        rows.append(src)
        cols.append(order[peer_rank[src]])

    # The few who reach everyone, and hear nothing back. Row is the
    # READER and column is the source, so the AUDIENCE must be the row —
    # wiring it the other way made every influencer a reader of their own
    # audience and put the whole population online.
    n_inf = max(1, int(n * INFLUENCER_SHARE))
    infl = rng.choice(np.flatnonzero(online) if online.any()
                      else np.arange(n), n_inf, replace=False)
    aud = rng.integers(0, n, n_inf * FEED_SIZE * 8)
    rows.append(aud)
    cols.append(np.repeat(infl, FEED_SIZE * 8))

    r = np.concatenate(rows)
    c = np.concatenate(cols)
    # a person is in the feed only if THEY are online — filtering on the
    # source put offline people in front of a screen they do not own
    keep = online[r] & (r != c)
    m = sparse.csr_matrix((np.ones(keep.sum()), (r[keep], c[keep])),
                          shape=(n, n))
    m.data[:] = 1.0
    return m


def feed_tick_legacy(civ, feed, alpha, susceptibility=None,
              beta: float = 1.0, dt_days: float = 1.0) -> dict:
    """One day of the feed. Deliberately ASYMMETRIC — no reciprocity.

    Note what is NOT done here: the matrix is never symmetrised. Every
    other channel in this world is made mutual because a neighbour is a
    neighbour. A feed is not mutual, and making it mutual would erase
    the thing that makes it different.
    """
    n = civ.n
    raw_deg = np.asarray(feed.sum(axis=1)).ravel()
    reads = raw_deg > 0          # who actually has a feed at all
    deg = np.maximum(raw_deg, 1.0)   # clipped only for the division

    a = np.clip(alpha, 0, 1) ** (beta * FEED_BETA_MULTIPLIER)
    pole = (civ.forces > 0.5).astype(np.float64)

    num = feed @ (a[:, None] * pole)
    den = np.asarray(feed @ a).ravel()
    pull = (num - civ.forces * den[:, None]) / deg[:, None]

    # the optimiser does not amplify everything. It amplifies arousal.
    w = np.array([AROUSAL_WEIGHT[Force(k)] for k in range(civ.forces.shape[1])])
    move = FEED_ETA * pull * w[None, :] * dt_days
    if susceptibility is not None:
        move = move * susceptibility

    before = civ.forces.copy()
    civ.forces[reads] = np.clip(civ.forces[reads] + move[reads], 0.0, 1.0)

    moved = float(np.abs(civ.forces - before).mean())
    # polarisation: how much of the online population sits at the poles
    on = civ.forces[reads]
    extreme = float(((on < 0.2) | (on > 0.8)).mean()) if reads.any() else 0.0
    off = civ.forces[~reads]
    extreme_off = float(((off < 0.2) | (off > 0.8)).mean()) \
        if (~reads).any() else 0.0
    return {"online_share": float(reads.mean()),
            "feed_moved": round(moved, 6),
            "extreme_online": round(extreme, 4),
            "extreme_offline": round(extreme_off, 4),
            "polarisation_gap": round(extreme - extreme_off, 4)}


# ═══════════════════════════════════════════════════════════════════
# CANONICAL FEED — the validated candidate 76a574c, ported verbatim from
# field_lab.make_dyadic_feed_v6 (Phase 0.5 canonicalization).
# The feed is one more encounter per day, drawn from the asymmetric feed
# graph, moving the reader MU toward the source's value weighted by the
# channel arousal vector, and feeding the same conviction evidence as
# tie encounters. feed_tick_legacy above is LEGACY_COMPARISON_ONLY (the
# retired second-pole operator; never on the canonical path).
# ═══════════════════════════════════════════════════════════════════
AROUSAL = np.array([AROUSAL_WEIGHT[Force(k)] for k in range(8)])
MU_FEED = 0.05


def feed_tick(civ, feed, alpha, *, day: int, scratch,
              susceptibility=None, mu: float = MU_FEED,
              **_ignored) -> dict:
    from earth1.influence import (ENCOUNTER_SEED_FEED, sample_partners,
                                  accumulate_drive, dyadic_move)
    f = civ.forces
    csr = feed if hasattr(feed, "indptr") else feed.tocsr()
    rng = np.random.default_rng(ENCOUNTER_SEED_FEED + int(day))
    partner, has = sample_partners(csr, rng)
    accumulate_drive(scratch, f, partner, has)
    move = dyadic_move(f, partner, has, mu, susceptibility,
                       weights=AROUSAL)
    civ.forces = np.clip(f + move, 0.0, 1.0)
    return {"feed_readers": int(has.sum())}
