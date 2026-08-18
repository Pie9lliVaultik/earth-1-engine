"""INTEGRATION — the five functional signatures, measured on a population.

Pietro, 2026-08-18: start from the brain, as architecture rather than
metaphor. A neuron fires or it doesn't, based on what its neighbours
did. No neuron has seen a face. Eighty-six billion of them recognise
one. The five patterns that make that true in a brain are measurable in
a population, and nobody has measured them for a synthetic society
because nobody has built one alive enough to measure.

  1 GLOBAL INTEGRATION   cut the population in half. Run both halves.
                         Does the whole do something neither half does?
  2 SELF-MODELLING       the civilisation reads its own aggregate state
                         as news and is changed by it
  3 NOVEL COHERENCE      an unprecedented event, against a shuffled
                         control. Structure minus shuffled structure.
  4 ANTICIPATION         does the collective drift toward a crisis
                         before anything names it
  5 PHASE TRANSITION     integration vs coupling strength. Smooth, or a
                         discontinuity with something new on the far side

None of these is a consciousness detector, and this module does not
claim one. Together they are a PROFILE: quantities that in a brain are
necessary conditions, and in a population either appear or do not.
Whether there is something it is like to be this system from the inside
is not what is being measured. What is being measured is whether the
functional signature is there at all.
"""
from __future__ import annotations

import numpy as np
from scipy import sparse

from earth1.chaos import entropy, world_step
from earth1.types import Force

STEP = dict(beta=2.0, residue=0.02, critical_fraction=0.12, relax=0.25)


def _cut(adj, part: np.ndarray):
    """Sever every edge that crosses the partition. The corpus callosum."""
    a = adj.tocoo()
    keep = part[a.row] == part[a.col]
    return sparse.csr_matrix(
        (a.data[keep], (a.row[keep], a.col[keep])), shape=adj.shape)


def _traj(civ, life, rng, days, adj=None, **kw):
    """Run and record the population's collective trajectory."""
    if adj is not None:
        civ.adj = adj
    rows = []
    for _ in range(days):
        st = world_step(civ, life, rng, **{**STEP, **kw})
        rows.append({
            "state": civ.forces.copy(),          # the FULL state
            "mean": civ.forces.mean(axis=0).copy(),
            "std": civ.forces.std(axis=0).copy(),
            "entropy": entropy(civ.forces),
            "cascades": st.get("cascades_fired", 0),
        })
    return rows


# ── 1. GLOBAL INTEGRATION ────────────────────────────────────────────

def phi_proxy(make_world, days: int = 30, seed: int = 11) -> dict:
    """Split the world, run the halves alone, compare to the whole.

    Consciousness disappears when the corpus callosum is cut: two
    functional halves, neither conscious the way the whole was. The
    measure is the same here — if the intact population produces
    collective behaviour that the severed halves do not produce between
    them, the system is not decomposable, and the size of that gap is
    the signal.

    Partition is GEOGRAPHIC, so the cut severs real social structure
    rather than an arbitrary index.
    """
    civ_w, life_w = make_world()
    # Cut along a real seam: whole world REGIONS on either side, so the
    # severed ties are the ones that actually carry structure (diaspora
    # corridors run within region, media hubs run across everything).
    part = (civ_w.region.astype(np.int64)
            + civ_w.country.astype(np.int64) // 97) % 2

    whole = _traj(civ_w, life_w, np.random.default_rng(seed), days)

    civ_p, life_p = make_world()
    cut = _cut(civ_p.adj, part)
    parts = _traj(civ_p, life_p, np.random.default_rng(seed), days, adj=cut)

    w_mean = np.array([r["mean"] for r in whole])
    p_mean = np.array([r["mean"] for r in parts])
    w_std = np.array([r["std"] for r in whole])
    p_std = np.array([r["std"] for r in parts])
    w_cas = np.array([r["cascades"] for r in whole], float)
    p_cas = np.array([r["cascades"] for r in parts], float)
    w_ent = np.array([r["entropy"] for r in whole])
    p_ent = np.array([r["entropy"] for r in parts])

    # normalised divergence of the collective trajectory
    # PHI ON THE FULL STATE, not on the population mean. A mean over
    # thousands of agents is robust to almost any intervention, so
    # measuring there reports ~0 no matter how integrated the system is
    # — the same error as measuring the Lyapunov exponent on a damped
    # projection. Integration is a property of the STATE.
    w_state = np.array([r["state"] for r in whole])
    p_state = np.array([r["state"] for r in parts])
    denom_s = max(float(np.linalg.norm(w_state)), 1e-12)
    phi_state = float(np.linalg.norm(w_state - p_state) / denom_s)
    # fraction of agents whose trajectory depended on the other half
    touched = float((np.abs(w_state[-1] - p_state[-1]).max(axis=1)
                     > 1e-9).mean())

    denom = max(float(np.linalg.norm(w_mean)), 1e-12)
    phi = float(np.linalg.norm(w_mean - p_mean) / denom)

    return {"days": days,
            "phi_proxy": round(phi_state, 5),
            "phi_on_mean_only": round(phi, 5),
            "agents_depending_on_other_half": round(touched, 4),
            "cascades_whole": float(w_cas.sum()),
            "cascades_severed": float(p_cas.sum()),
            "cascade_gap": float(w_cas.sum() - p_cas.sum()),
            "entropy_whole_end": round(float(w_ent[-1]), 4),
            "entropy_severed_end": round(float(p_ent[-1]), 4),
            "spread_whole_end": round(float(w_std[-1].mean()), 5),
            "spread_severed_end": round(float(p_std[-1].mean()), 5)}


# ── 2. SELF-MODELLING ────────────────────────────────────────────────

def self_reference(make_world, days: int = 40, publish_every: int = 5,
                   seed: int = 12, gain: float = 0.06) -> dict:
    """The civilisation reads its own aggregate state and is changed.

    Every publish_every ticks the population's own summary statistic is
    injected back into it as news, reaching each agent in proportion to
    how much they care what others think. The number changes the
    headline; the headline changes the number.

    The index is what that loop does to the trajectory compared with an
    identical world in which the population is never told about itself.
    """
    out = {}
    for label, on in (("with_self_model", True), ("blind", False)):
        civ, life = make_world()
        rng = np.random.default_rng(seed)
        # conformity: how much an agent moves toward what "everyone
        # thinks". Political engagement is the natural carrier.
        conform = (life.political if life.political is not None
                   else np.full(civ.n, 0.5))
        traj, pubs = [], []
        for d in range(days):
            world_step(civ, life, rng, **STEP)
            if on and d % publish_every == 0:
                published = civ.forces.mean(axis=0)     # the self-model
                pubs.append(published.copy())
                # the population reads about itself
                civ.forces = np.clip(
                    civ.forces + gain * conform[:, None]
                    * (published[None, :] - civ.forces), 0.0, 1.0)
            traj.append(civ.forces.mean(axis=0).copy())
        out[label] = np.array(traj)
        if on:
            out["published"] = np.array(pubs)

    a, b = out["with_self_model"], out["blind"]
    denom = max(float(np.linalg.norm(b)), 1e-12)
    divergence = float(np.linalg.norm(a - b) / denom)

    # does the published number predict the subsequent shift?
    pub = out["published"]
    lead = []
    for i in range(len(pub) - 1):
        t = (i + 1) * publish_every
        if t + publish_every < len(a):
            shift = a[t + publish_every] - a[t]
            gap = pub[i] - a[t]
            if np.linalg.norm(shift) > 0 and np.linalg.norm(gap) > 0:
                lead.append(float(np.dot(shift, gap)
                                  / (np.linalg.norm(shift)
                                     * np.linalg.norm(gap))))
    return {"days": days,
            "self_reference_index": round(divergence, 5),
            "published_predicts_shift": (round(float(np.mean(lead)), 4)
                                         if lead else None),
            "publications": int(len(pub))}


# ── 3. NOVEL COHERENCE ───────────────────────────────────────────────

def _structure(forces: np.ndarray, adj) -> float:
    """How patterned is this response? Moran's I on the social graph.

    A structured collective response means neighbours resemble each
    other more than strangers do. Noise has no such property, and a
    uniform response has no variance to explain.
    """
    x = forces - forces.mean(axis=0, keepdims=True)
    deg = np.maximum(np.asarray(adj.sum(axis=1)).ravel(), 1.0)
    nb = (adj @ x) / deg[:, None]
    num = float((x * nb).sum())
    den = float((x * x).sum())
    return num / den if den > 0 else 0.0


def novel_coherence(make_world, days: int = 20, seed: int = 13) -> dict:
    """An event nothing in this world has a prepared answer for.

    The shock is a force signature unlike any entry in the catalogue —
    no agent, rule or seed encodes a response to it. If the population
    still produces a PATTERNED reply, that pattern came from the
    interaction of agents who individually had nothing to say.

    The control is the same population with its connections shuffled:
    same people, same shock, no social structure. Structure minus
    shuffled structure is what the society itself contributed.
    """
    # unprecedented: simultaneous extremes on channels that never move
    # together in the catalogue
    shock = np.zeros(len(Force))
    shock[Force.EXPERIENCE] = 0.45
    shock[Force.CULTURE] = -0.35
    shock[Force.IDENTITY] = 0.40
    shock[Force.TEMPERAMENT] = -0.30

    res = {}
    for label in ("real", "shuffled"):
        civ, life = make_world()
        if label == "shuffled":
            # same degree distribution, destroyed structure
            a = civ.adj.tocoo()
            perm = np.random.default_rng(99).permutation(civ.n)
            civ.adj = sparse.csr_matrix(
                (a.data, (perm[a.row], perm[a.col])), shape=a.shape)
        rng = np.random.default_rng(seed)
        for _ in range(5):                     # settle
            world_step(civ, life, rng, **STEP)
        before = civ.forces.copy()
        civ.forces = np.clip(civ.forces + shock[None, :], 0.0, 1.0)
        for _ in range(days):
            world_step(civ, life, rng, **STEP)
        response = civ.forces - before
        res[label] = {"structure": _structure(response, civ.adj),
                      "spread": float(response.std()),
                      "mean_shift": float(np.abs(response.mean(axis=0)).sum())}

    coherence = res["real"]["structure"] - res["shuffled"]["structure"]
    return {"days": days,
            "structure_real": round(res["real"]["structure"], 5),
            "structure_shuffled": round(res["shuffled"]["structure"], 5),
            "novel_coherence": round(coherence, 5),
            "spread_real": round(res["real"]["spread"], 5),
            "spread_shuffled": round(res["shuffled"]["spread"], 5)}


# ── 4. ANTICIPATION ──────────────────────────────────────────────────

def anticipation(make_world, days: int = 90, lead: int = 5,
                 seed: int = 14) -> dict:
    """Does the collective lean into a crisis before anything names it?

    A flock turns before any bird has seen the predator. Here the
    crisis is ENDOGENOUS — a wave of firm failures, which is generated
    by the simulation's own dynamics and is announced to no one. If the
    population's aggregate fear is already rising in the days before a
    wave lands, the collective is integrating weak distributed signals
    that no individual agent has resolved.

    Compared against shuffled event times, so a general upward drift
    cannot masquerade as foresight.
    """
    civ, life = make_world()
    rng = np.random.default_rng(seed)
    fear, fails = [], []
    for _ in range(days):
        st = world_step(civ, life, rng, **STEP)
        fear.append(float(civ.forces[:, Force.FEAR].mean()))
        fails.append(int(st.get("firms_failed", 0)))
    fear = np.array(fear)
    fails = np.array(fails, float)
    d_fear = np.diff(fear, prepend=fear[0])

    thresh = np.percentile(fails[fails > 0], 75) if (fails > 0).any() else 1
    waves = np.flatnonzero(fails >= max(thresh, 1))
    waves = waves[(waves >= lead) & (waves < days)]
    if waves.size < 3:
        return {"waves": int(waves.size), "anticipation_lead": None,
                "note": "too few crisis waves to measure"}

    def pre_drift(idx):
        return float(np.mean([d_fear[i - lead:i].mean() for i in idx]))

    real = pre_drift(waves)
    rs = np.random.default_rng(7)
    null = [pre_drift(rs.integers(lead, days, waves.size))
            for _ in range(400)]
    null = np.array(null)
    z = (real - null.mean()) / max(null.std(), 1e-12)
    return {"days": days, "lead_days": lead, "waves": int(waves.size),
            "pre_crisis_fear_drift": round(real, 8),
            "null_mean": round(float(null.mean()), 8),
            "z_score": round(float(z), 3),
            "anticipates": bool(z > 2.0)}


# ── 5. PHASE TRANSITION ──────────────────────────────────────────────

def phase_scan(make_world, betas=(0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0),
               days: int = 20, seed: int = 15) -> dict:
    """Integration as a function of coupling strength.

    Water holds, holds, holds, then snaps. If integration rises
    smoothly with coupling the system is only getting bigger; a
    discontinuity means whatever is past it is a different kind of
    thing from what came before.
    """
    rows = []
    for b in betas:
        civ_w, life_w = make_world()
        part = (civ_w.region.astype(np.int64)
                + civ_w.country.astype(np.int64) // 97) % 2
        w = _traj(civ_w, life_w, np.random.default_rng(seed), days, beta=b)
        civ_p, life_p = make_world()
        p = _traj(civ_p, life_p, np.random.default_rng(seed), days,
                  adj=_cut(civ_p.adj, part), beta=b)
        wm = np.array([r["state"] for r in w])
        pm = np.array([r["state"] for r in p])
        phi = float(np.linalg.norm(wm - pm) / max(float(np.linalg.norm(wm)),
                                                  1e-12))
        rows.append({"beta": b, "phi_proxy": round(phi, 5),
                     "cascades": float(sum(r["cascades"] for r in w)),
                     "entropy_end": round(float(w[-1]["entropy"]), 4)})
    phis = np.array([r["phi_proxy"] for r in rows])
    d1 = np.diff(phis)
    jump = int(np.argmax(np.abs(d1))) if d1.size else 0
    return {"scan": rows,
            "largest_jump_between": [betas[jump], betas[jump + 1]]
            if d1.size else None,
            "jump_size": round(float(np.abs(d1).max()), 5) if d1.size else 0.0,
            "mean_step": round(float(np.abs(d1).mean()), 5) if d1.size else 0.0,
            "discontinuity_ratio": (round(float(np.abs(d1).max()
                                                / max(np.abs(d1).mean(), 1e-12)),
                                          2) if d1.size else None)}
