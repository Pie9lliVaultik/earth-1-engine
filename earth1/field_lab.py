"""The IT5 joint-program lab — experimental patches ONLY, frozen at
IT5_BC_REGISTRATION.md (05b0cc6). Production untouched.

Provides the three repairs as independently-attachable patches:
  OPERATOR  — sparse dyadic encounters governing propagate AND feed
              (feed keeps its graph + arousal weights; only the LAW
              changes); contagion ambient smoothing disabled via
              CONTAGION_GAIN=0 (event impulses preserved).
  FLOURISH  — (a) force-writes disabled (restore-after wrapper) or
              (b) the registered level-map conversion inside
              life_force_target.
  CONVICTION— C3 log-odds law at the frozen IT5-B gain candidates
              (earth1.conviction_lab.c3_logodds_symmetric).
"""
from __future__ import annotations

import numpy as np

_DAY = [0]
PASS_LOG = []
FLOUR_REF = [None]          # set per world by the runner
AROUSAL = None              # feed arousal weight vector, set on patch


def _record(tag, before, after):
    PASS_LOG.append((int(_DAY[0]), tag, float(before), float(after)))


def _sample_partners(csr, rng):
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


def make_dyadic_propagate(k=3, mu=0.05, gate=None):
    def op(forces, alpha, adj, beta=1.0, layers=None,
           susceptibility=None, **kw):
        f = forces.copy()
        csr = adj if hasattr(adj, "indptr") else adj.tocsr()
        rng = np.random.default_rng(920_000 + _DAY[0])
        vb = float(f.var())
        for _ in range(k):
            partner, has = _sample_partners(csr, rng)
            f = np.clip(f + dyadic_move(f, partner, has, mu,
                                        susceptibility, gate), 0, 1)
        _record("prop", vb, float(f.var()))
        return f
    return op


def make_dyadic_feed(mu=0.05, gate=None):
    """feed_tick replacement: ONE feed item per reader per day, drawn
    from the (preserved) feed graph, arousal-weighted."""
    def tick(civ, feed, alpha, susceptibility=None, **kw):
        f = civ.forces
        csr = feed if hasattr(feed, "indptr") else feed.tocsr()
        rng = np.random.default_rng(930_000 + _DAY[0])
        partner, has = _sample_partners(csr, rng)
        vb = float(f.var())
        move = dyadic_move(f, partner, has, mu, susceptibility, gate,
                           weights=AROUSAL)
        civ.forces = np.clip(f + move, 0.0, 1.0)
        _record("feed", vb, float(civ.forces.var()))
        return {"feed_moved": round(float(np.abs(move).mean()), 6),
                "feed_readers": int(has.sum())}
    return tick


def flourishing_writes_disabled(orig_tick):
    """Ablation (2): flourishing runs fully (state, hunger, deaths)
    but its force writes are reverted."""
    def tick(*a, **kw):
        civ = a[0]
        before = civ.forces.copy()
        out = orig_tick(*a, **kw)
        civ.forces[:] = before
        return out
    return tick


def flourishing_level_map(orig_target):
    """Ablation (3): the registered conversion — flourishing terms
    become bounded LEVEL contributions to the lived target."""
    from earth1.types import Force

    def target(civ, life):
        t = orig_target(civ, life)
        fl = FLOUR_REF[0]
        if fl is None or fl.hope is None:
            return t
        need = np.clip(0.6 * fl.hunger + 0.4 * fl.thirst, 0, 1)
        t[:, Force.FEAR] = np.clip(
            t[:, Force.FEAR] + 0.30 * need - 0.20 * fl.hope, 0, 1)
        t[:, Force.DESIRE] = np.clip(
            t[:, Force.DESIRE] + 0.20 * fl.hope
            + 0.15 * fl.curiosity - 0.25 * need, 0, 1)
        import os as _os
        if _os.environ.get("EARTH1_COLLECTIVE_CENTERED") == "1":
            # COLLECTIVE-GEO-1: belonging as a DEPARTURE from the
            # registered reference center (COLLECTIVE_GEO_1.md)
            t[:, Force.COLLECTIVE] = np.clip(
                t[:, Force.COLLECTIVE]
                + 0.20 * (fl.belonging - 0.6416), 0, 1)
        else:
            t[:, Force.COLLECTIVE] = np.clip(
                t[:, Force.COLLECTIVE] + 0.20 * fl.belonging, 0, 1)
        t[:, Force.CULTURE] = np.clip(
            t[:, Force.CULTURE] + 0.20 * fl.meaning, 0, 1)
        t[:, Force.EXPERIENCE] = np.clip(
            t[:, Force.EXPERIENCE] + 0.10 * fl.curiosity, 0, 1)
        return t
    return target


# ── IT6: the encounter as causal object ─────────────────────────────
# Dyadic conviction rides the SAME encounters that carry influence
# (never recomputed from aggregates — the mean-field information loss
# must not re-enter through another route). DRIVE_ACC accumulates the
# day's signed encounter drives per agent; the patched conviction law
# consumes and resets it. SAMPLES holds full causal-object records
# for a registered 1000-encounter/day sample on instrument days.

DRIVE_ACC = [None]        # (N,) float accumulated drive
ENC_COUNT = [None]        # (N,) int encounters today
SAMPLES = []
SAMPLE_DAYS = set()
ENC_STATS = {}            # day -> {"n": int, "neg": int}
DOSE_STATS = {}           # day -> realized-dose bookkeeping


def _accumulate_drive(f_pre, partner, has, layer, mu, day):
    tgt = f_pre[np.clip(partner, 0, f_pre.shape[0] - 1)]
    d_e = np.abs(f_pre - tgt).mean(axis=1)
    drive = np.clip((0.5 - d_e) / 0.5, -1.0, 1.0)
    drive[~has] = 0.0
    DRIVE_ACC[0] += drive
    ENC_COUNT[0] += has.astype(np.int64)
    s = ENC_STATS.setdefault(int(day), {"n": 0, "neg": 0})
    s["n"] += int(has.sum())
    s["neg"] += int((drive[has] < 0).sum())
    ds = DOSE_STATS.setdefault(int(day), {"enc": 0, "dist_sum": 0.0})
    ds["enc"] += int(has.sum())
    ds["dist_sum"] += float(d_e[has].sum())
    if day in SAMPLE_DAYS and len(SAMPLES) < 1000 * len(SAMPLE_DAYS):
        idx = np.flatnonzero(has)[:50]
        for i in idx:
            SAMPLES.append({
                "day": int(day), "layer": layer, "recipient": int(i),
                "source": int(partner[i]),
                "pre_distance": round(float(d_e[i]), 4),
                "drive": round(float(drive[i]), 4),
                "strength": mu})


def make_dyadic_propagate_v6(k=3, mu=0.05, influence=True):
    """IT6 operator: dyadic influence + drive accumulation from the
    same encounters. influence=False gives the dyCNV-only arm
    (encounters sampled for conviction evidence, forces untouched by
    this operator)."""
    def op(forces, alpha, adj, beta=1.0, layers=None,
           susceptibility=None, **kw):
        f = forces.copy()
        csr = adj if hasattr(adj, "indptr") else adj.tocsr()
        rng = np.random.default_rng(920_000 + _DAY[0])
        for _ in range(k):
            partner, has = _sample_partners(csr, rng)
            _accumulate_drive(f, partner, has, "tie", mu, _DAY[0])
            if influence:
                mv = dyadic_move(f, partner, has, mu, susceptibility)
                ds = DOSE_STATS.setdefault(int(_DAY[0]), {})
                ds["dose_abs"] = ds.get("dose_abs", 0.0) + float(
                    np.abs(mv).mean(axis=1).sum())
                ds["var_pre"] = ds.get("var_pre", float(f.var()))
                f = np.clip(f + mv, 0, 1)
                ds["var_post"] = float(f.var())
        return f
    return op


def make_dyadic_feed_v6(mu=0.05, influence=True):
    def tick(civ, feed, alpha, susceptibility=None, **kw):
        f = civ.forces
        csr = feed if hasattr(feed, "indptr") else feed.tocsr()
        rng = np.random.default_rng(930_000 + _DAY[0])
        partner, has = _sample_partners(csr, rng)
        _accumulate_drive(f, partner, has, "feed", mu, _DAY[0])
        if influence:
            move = dyadic_move(f, partner, has, mu, susceptibility,
                               weights=AROUSAL)
            civ.forces = np.clip(f + move, 0.0, 1.0)
        return {"feed_readers": int(has.sum())}
    return tick


def dyadic_conviction(forces, alpha, adj, gain=0.003, lam=0.0):
    """C3 log-odds form driven by the day's ACCUMULATED encounter
    evidence (mean drive over today's encounters; no encounters ->
    no update)."""
    n_enc = np.maximum(ENC_COUNT[0], 1)
    drive = DRIVE_ACC[0] / n_enc
    drive[ENC_COUNT[0] == 0] = 0.0
    a = np.clip(alpha, 0.02, 0.98)
    logit = np.log(a / (1.0 - a)) + gain * drive
    out = np.clip(1.0 / (1.0 + np.exp(-logit)), 0.02, 1.0)
    DRIVE_ACC[0][:] = 0.0
    ENC_COUNT[0][:] = 0
    return out
