"""0.8 IT6 — DYADIC FIELD INTEGRATION runner (frozen registration:
IT6_DYADIC_FIELD_INTEGRATION.md). 13 ablation arms + 8 KA arms.

POST-CANONICALIZATION (Phase 0.5): the validated candidate 76a574c IS
the flagless canonical live_one_day. op="canon"/cnv="canon" runs it
unpatched; this is the only configuration that remains meaningful.
The historical lab branches ("dy", "dy_noinf_incprop", "c3field",
"meanfield") are RETIRED with field_lab and no longer executable
against the canonical loop; "zero" and "inc" map to explicitly
LEGACY_COMPARISON_ONLY operators for the Stage-B broken twins.
"""
import copy
import json
import os
import sys
from functools import partial
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import multiprocessing as mp

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

N = int(os.environ.get("EARTH1_IT6_N", "200000"))
DAYS = int(os.environ.get("EARTH1_IT6_DAYS", "120"))
TAU_AT = int(os.environ.get("EARTH1_IT6_TAU_AT", "90"))
TAU_DAYS = int(os.environ.get("EARTH1_IT6_TAU_DAYS", "30"))
CAP_DAYS = tuple(range(91, 96))
SEED = 8890
CH_TAU, CH_TRANS = 2, 5
GAIN = 0.003

# arm -> (op, cnv, flr, cascade, relax)
#   op: "inc" | "dy" | "dy_noinf" | "zero" | "instant"
#   cnv: "inc" | "dy" | "meanfield" | "c3field"
D = dict
ARMS = {
    "incumbent":  D(op="inc", cnv="inc", flr=False, cas=False, relax=0.25),
    "dyINF":      D(op="dy", cnv="c3field", flr=False, cas=False, relax=0.045),
    "dyCNV":      D(op="dy_noinf_incprop", cnv="dy", flr=False, cas=False, relax=0.25),
    "FLR":        D(op="inc", cnv="inc", flr=True, cas=False, relax=0.25),
    "CAS":        D(op="inc", cnv="inc", flr=False, cas=True, relax=0.25),
    "dyINF_dyCNV": D(op="dy", cnv="dy", flr=False, cas=False, relax=0.045),
    "dyINF_FLR":  D(op="dy", cnv="c3field", flr=True, cas=False, relax=0.045),
    "dyINF_CAS":  D(op="dy", cnv="c3field", flr=False, cas=True, relax=0.045),
    "dyCNV_FLR":  D(op="dy_noinf_incprop", cnv="dy", flr=True, cas=False, relax=0.25),
    "dyCNV_CAS":  D(op="dy_noinf_incprop", cnv="dy", flr=False, cas=True, relax=0.25),
    "ALL_noFLR":  D(op="dy", cnv="dy", flr=False, cas=True, relax=0.045),
    "ALL_noCAS":  D(op="dy", cnv="dy", flr=True, cas=False, relax=0.045),
    "ALL":        D(op="dy", cnv="dy", flr=True, cas=True, relax=0.045),
    "KA_zero":    D(op="zero", cnv="dy", flr=True, cas=True, relax=0.045),
    "KA_instant": D(op="instant", cnv="dy", flr=True, cas=True, relax=0.045),
    "KA_mfdrive": D(op="dy", cnv="meanfield", flr=True, cas=True, relax=0.045),
    "KA_pull":    D(op="dy", cnv="dy", flr=True, cas=True, relax=0.60),
    "KA_frozen":  D(op="dy", cnv="dy", flr=True, cas=True, relax=0.005),
    "KA_degtgt":  D(op="dy", cnv="dy", flr=True, cas=True, relax=0.045,
                    extra="degtgt"),
    "KA_fastmix": D(op="dy", cnv="dy", flr=True, cas=True, relax=0.045,
                    extra="fastmix"),
    "KA_ratchet": D(op="dy", cnv="inc", flr=True, cas=True, relax=0.045),
}
OUT = Path(os.environ.get("EARTH1_IT6_OUT",
                          str(ROOT / "data" / "it6_dyadic")))


def panel(w, genesis_sd):
    civ = w.civ
    alive = w.health.alive
    f = civ.forces[alive]
    a = civ.alpha[alive]
    adj = civ.adj
    deg = np.maximum(np.asarray(adj.sum(axis=1)).ravel(), 1.0)
    pole = (civ.forces > 0.5).astype(np.float64)
    nb_pole = np.asarray(adj @ pole) / deg[:, None]
    agr = (1.0 - np.abs(nb_pole - pole).mean(axis=1))[alive]
    ch_sd = f.std(axis=0)
    return {"alpha_mean": round(float(a.mean()), 4),
            "alpha_sd": round(float(a.std()), 4),
            "alpha_gt99": round(float((a > 0.99).mean()), 4),
            "alpha_floor": round(float((a < 0.05).mean()), 4),
            "one_minus_alpha_med": round(float(np.median(1 - a)), 4),
            "sd_ratio_genesis": round(float((ch_sd / genesis_sd
                                             ).mean()), 3),
            "sat_max": round(float(max(
                max((f[:, c] > 0.95).mean(), (f[:, c] < 0.05).mean())
                for c in range(f.shape[1]))), 4),
            "unanimous_share": round(float((agr > 0.95).mean()), 4)}


def run_arm(name):
    import earth1.alive as am
    import earth1.contagion as cont
    import earth1.feed as feedmod
    import earth1.flourishing as flmod
    import earth1.life as lifemod
    from earth1.alive import birth_world, live_one_day
    from earth1.types import Force

    cfg = dict(ARMS[name])
    seed_arm = int(cfg.get("seed", SEED))
    if cfg.get("cas"):
        os.environ["EARTH1_CASCADE_COOLDOWN"] = "1"
    else:
        os.environ.pop("EARTH1_CASCADE_COOLDOWN", None)
    w = birth_world(N, seed_arm)
    op = cfg["op"]
    cnv = cfg.get("cnv", "canon")
    if op not in ("canon", "zero") or cnv not in ("canon", "inc") \
            or cfg.get("flr") or cfg.get("extra"):
        # retired 0.8 lab branches: archive import (opt-in guarded)
        import earth1.lab_archive.conviction_lab as clab
        import earth1.lab_archive.field_lab as flab
        clab.ALPHA0 = w.civ.alpha.copy()
        flab.FLOUR_REF[0] = w.flourishing
        flab.AROUSAL = np.array(
            [feedmod.AROUSAL_WEIGHT[Force(k)] for k in range(8)])
        flab.DRIVE_ACC[0] = np.zeros(N)
        flab.ENC_COUNT[0] = np.zeros(N, dtype=np.int64)
        flab.SAMPLES.clear(); flab.ENC_STATS.clear()
        flab.DOSE_STATS.clear(); flab.SAMPLE_DAYS.clear()
        flab.SAMPLE_DAYS.update((1, 60, 90, 120))
    else:
        flab = None

    if cfg.get("extra") == "fastmix":
        import earth1.lab_archive.propagation_lab as plab
        for i, (t, m) in enumerate(w.fabric.by_type.items()):
            w.fabric.by_type[t] = plab.randomized_graph(m, seed=911 + i)
        from earth1.rehome import _recompose_adj
        _recompose_adj(w)

    k_arm = int(cfg.get("k", 3))
    mu_arm = float(cfg.get("mu", 0.05))
    if op == "canon":
        pass                      # canonical physics, nothing patched
    elif op == "dy":
        raise RuntimeError('op="dy" is the retired lab assembly; the '
                           'canonical loop IS the dyadic candidate — '
                           'use op="canon"')
    elif op == "dy_noinf_incprop":
        _orig_prop = am.propagate
        _sampler = flab.make_dyadic_propagate_v6(3, 0.05,
                                                 influence=False)
        def combo(forces, alpha, adj, **kw):
            _sampler(forces, alpha, adj, **kw)
            return _orig_prop(forces, alpha, adj, **kw)
        am.propagate = combo
    elif op == "zero":
        # Stage-B B3 broken twin: no social influence at all (encounter
        # evidence still sampled so conviction remains defined)
        import earth1.influence as _inf
        _orig_feed = feedmod.feed_tick
        def _zero_prop(forces, alpha, adj, *, day, scratch,
                       susceptibility=None, **kw):
            return _inf.propagate(forces, alpha, adj, day=day,
                                  scratch=scratch,
                                  susceptibility=susceptibility, mu=0.0)
        def _zero_feed(civ, feed, alpha, *, day, scratch, **kw):
            return _orig_feed(civ, feed, alpha, day=day,
                              scratch=scratch, mu=0.0)
        am.propagate = _zero_prop
        feedmod.feed_tick = _zero_feed
    elif op == "instant":
        am.propagate = flab.make_dyadic_propagate_v6(10, 0.9)
        feedmod.feed_tick = flab.make_dyadic_feed_v6(0.9)
        cont.CONTAGION_GAIN = 0.0

    if cfg.get("flr"):
        lifemod.life_force_target = flab.flourishing_level_map(
            lifemod.life_force_target)
        flmod.flourishing_tick = flab.flourishing_writes_disabled(
            flmod.flourishing_tick)
    if cfg.get("extra") == "degtgt":
        _o = lifemod.life_force_target
        def dt_(civ, life, _f=_o):
            t = _f(civ, life)
            t[:] = 0.9
            return t
        lifemod.life_force_target = dt_

    cap = []          # (net_drive, dalpha) instrument records
    cnv = cfg["cnv"]
    forced = cfg.get("forced")        # (drive_value,) KAdis arms
    forced_cohort = None
    if forced is not None:
        forced_cohort = np.arange(min(10_000, N // 4))
    if cnv == "canon":
        pass                      # canonical dyadic conviction
    elif cnv == "inc":
        # Stage-B B2 broken twin: the retired incumbent ratchet
        import earth1.influence as _inf
        am.update_conviction = (lambda f, a, adj, **kw:
                                _inf.update_conviction_ratchet_legacy(
                                    f, a, adj))
    elif cnv == "dy":
        def conv(forces, alpha, adj):
            n_enc = np.maximum(flab.ENC_COUNT[0], 1)
            drive = flab.DRIVE_ACC[0] / n_enc
            drive[flab.ENC_COUNT[0] == 0] = 0.0
            if forced_cohort is not None:
                drive[forced_cohort] = forced
            a = np.clip(alpha, 0.02, 0.98)
            out = np.clip(1 / (1 + np.exp(-(np.log(a / (1 - a))
                                            + GAIN * drive))), 0.02, 1.0)
            if flab._DAY[0] in CAP_DAYS:
                cap.append((drive.copy(), out - alpha))
            flab.DRIVE_ACC[0][:] = 0.0
            flab.ENC_COUNT[0][:] = 0
            return out
        am.update_conviction = conv
    elif cnv == "meanfield":
        if forced_cohort is not None:
            # KAdis_mf: designed exposure destroyed by the mean-field
            # construct — the cohort's forced drive is NOT consulted
            am.update_conviction = partial(clab.c3_logodds_symmetric,
                                          gain=GAIN)
        else:
            am.update_conviction = partial(clab.c3_logodds_symmetric,
                                          gain=GAIN)
    elif cnv == "c3field":
        am.update_conviction = partial(clab.c3_logodds_symmetric,
                                      gain=GAIN)
    # cnv == "inc": leave the incumbent ratchet law

    # PF-DECAY-1 additive hooks (conformance regression only; every
    # key absent => byte-identical behavior): residue (env flag),
    # casfire (clamp days: biggest locality held in panic condition
    # pre-tick), days (arm horizon), no_fork (skip the day-90 fork)
    if cfg.get("residue"):
        os.environ["EARTH1_DECAY_RESIDUE"] = "1"
    else:
        os.environ.pop("EARTH1_DECAY_RESIDUE", None)
    if cfg.get("rules_off"):
        # R4 no-trigger control: a world where no rule CAN fire
        import earth1.thresholds as _th
        _th.TRANSITION_RULES = []
    for _ek, _ev in (cfg.get("env") or {}).items():
        os.environ[_ek] = _ev            # per-arm env (Stage B twins)
    days_arm = int(cfg.get("days", DAYS))
    casfire = cfg.get("casfire") or ()
    pf_cohort = pf_big = None
    pf_series, pf_fire_days, pf_big_fire_days = [], [], []
    pf_fired = 0
    if casfire:
        locv = (w.civ.country.astype(np.int64) * 1000
                + w.civ.region.astype(np.int64) * 2
                + w.civ.urban.astype(np.int64))
        ai = np.flatnonzero(w.health.alive)
        vv, cc = np.unique(locv[ai], return_counts=True)
        pf_big = int(vv[np.argmax(cc)])
        pf_cohort = ai[locv[ai] == pf_big]

    relax = cfg["relax"]
    lam_adapt = cfg.get("lam")        # IT9 adaptive baseline (or None)
    def _adapt():
        if lam_adapt:
            T = lifemod.life_force_target(w.civ, w.life)
            b = w.life.force_baseline
            b[:] = np.clip(b + lam_adapt * (w.civ.forces - T), 0, 1)
    rng = np.random.default_rng(seed_arm)
    genesis_sd = w.civ.forces[w.health.alive].std(axis=0)
    baseline_d90 = None
    panels, alpha_snaps, eff_panels, end_panels = {}, {}, {}, {}
    tau = trans = None
    for d in range(1, days_arm + 1):
        if flab is not None:
            flab._DAY[0] = d
        if casfire and d in casfire:
            w.civ.forces[pf_cohort, 2] = 0.20   # ECONOMICS < 0.3
            w.civ.forces[pf_cohort, 0] = 0.60   # FEAR > 0.5
        st_day = live_one_day(w, rng, relax=relax)
        _brk = cfg.get("broken")
        if _brk == "consensus":
            # STAGE B B1 broken twin: daily global mean reversion
            _fa = w.civ.forces[w.health.alive].mean(axis=0)
            w.civ.forces = np.clip(
                w.civ.forces + 0.05 * (_fa[None, :] - w.civ.forces),
                0, 1)
        elif _brk == "accumulator" and d >= 60:
            # B6 broken twin: unconditional daily global event write
            w.civ.forces[:, 0] = np.clip(
                w.civ.forces[:, 0] + 0.10, 0, 1)
        elif _brk == "bigevents" and d <= 90 and d % 10 == 0:
            # B11 broken twin: 5x event impulses -> clip load-bearing
            w.civ.forces[:, 0] = np.clip(
                w.civ.forces[:, 0] + 0.75, 0, 1)
        if cfg.get("wipe_residues"):
            # PF-DECAY-2 KA10-at-scale control: residues deleted every
            # day — under the open-loop contract this must change
            # NOTHING (detection never reads them)
            w.chronicle.cascade_residues = []
        if casfire:
            nf = int(st_day.get("cascades_fired", 0))
            if nf:
                pf_fired += nf
                pf_fire_days.append(d)
            from earth1.alive import cascade_residue_levels
            resl = getattr(w.chronicle, "cascade_residues", None) or []
            lv, _ = cascade_residue_levels(resl, w.day)
            lvl = float(sum(v[0] for lk, v in lv if lk == pf_big))
            for r in resl:
                if r["loc"] == pf_big and r["day"] == w.day - 1:
                    pf_big_fire_days.append({"day": d,
                                             "wday": int(r["day"]),
                                             "rule": r["rule"]})
            pf_series.append({"day": d, "wday": int(w.day),
                              "fear_level": round(lvl, 5),
                              "n_residues": len(resl)})
        _adapt()
        if d in (60, 90):
            alpha_snaps[d] = w.civ.alpha.copy()
        if d == TAU_AT:
            baseline_d90 = w.life.force_baseline.copy() \
                if w.life.force_baseline is not None else None
        if d % 10 == 0:
            panels[str(d)] = panel(w, genesis_sd)
            if cfg.get("endurance"):
                # Stage A extended census: both health families,
                # cascade/chronicle/material state, clamp occupancy
                from earth1.alive import effective_forces
                a_ = w.health.alive
                f_ = w.civ.forces[a_]
                fe_ = np.asarray(effective_forces(w))[a_]
                resl_ = getattr(w.chronicle, "cascade_residues",
                                None) or []
                lf_ = a_ & w.life.in_lf
                end_panels[str(d)] = {
                    "alive": int(a_.sum()),
                    "sat_stored": [round(float(max(
                        (f_[:, c] > 0.95).mean(),
                        (f_[:, c] < 0.05).mean())), 4)
                        for c in range(8)],
                    "sat_eff": [round(float(max(
                        (fe_[:, c] > 0.95).mean(),
                        (fe_[:, c] < 0.05).mean())), 4)
                        for c in range(8)],
                    "mean_stored": [round(float(f_[:, c].mean()), 4)
                                    for c in range(8)],
                    "mean_eff": [round(float(fe_[:, c].mean()), 4)
                                 for c in range(8)],
                    "at_bound_stored": round(float(
                        ((f_ <= 1e-9) | (f_ >= 1 - 1e-9)).mean()), 5),
                    "overlay_clip_frac": round(float(
                        (np.abs(fe_ - f_) >= 0.499).mean()), 5),
                    "n_residues": len(resl_),
                    "fired_cum": len(getattr(
                        w.chronicle, "cascade_last_fired", None)
                        or {}),
                    "memories": len(w.chronicle.events),
                    "employment": round(float(
                        w.life.employed[lf_].mean()), 4),
                    "firm_health": round(float(
                        w.life.firm_health.mean()), 4),
                    "deprivation": round(float(
                        w.life.deprivation[a_].mean()), 4),
                    "wealth_days": round(float(
                        w.life.wealth[a_].mean()), 2),
                    # GEO-1A criterion probe: the COLLECTIVE target
                    # distribution itself (lifemod.life_force_target
                    # is the candidate-wrapped law at this point)
                    "T_col_mean": round(float(
                        lifemod.life_force_target(w.civ, w.life,
                                                  w.flourishing)
                        [a_, 3].mean()), 4),
                    "frac_T95_col": round(float(
                        (lifemod.life_force_target(w.civ, w.life,
                                                   w.flourishing)
                         [a_, 3] > 0.95).mean()), 4),
                }
            if os.environ.get("EARTH1_DECAY_RESIDUE") == "1":
                # effective-view saturation, reported SEPARATELY from
                # the stored-force gates (never merged into panels)
                from earth1.alive import effective_forces
                fe = effective_forces(w)[w.health.alive]
                eff_panels[str(d)] = round(float(max(
                    max((fe[:, c] > 0.95).mean(),
                        (fe[:, c] < 0.05).mean())
                    for c in range(8))), 4)
        if d == TAU_AT and not cfg.get("no_fork"):
            rng_state = rng.bit_generator.state
            w2 = copy.deepcopy(w)
            rng2 = np.random.default_rng()
            rng2.bit_generator.state = rng_state
            gr = np.random.default_rng(99)
            alive_idx = np.flatnonzero(w.health.alive)
            idx = gr.choice(alive_idx, size=N // 4, replace=False)
            col = w2.civ.forces[:, CH_TAU]
            col[idx] = np.clip(col[idx] + 0.15, 0.0, 1.0)
            # CLUSTERED seeding (primary, registered)
            loc = (w.civ.country.astype(np.int64) * 1000
                   + w.civ.region.astype(np.int64) * 2
                   + w.civ.urban.astype(np.int64))
            vals, counts = np.unique(loc[alive_idx],
                                     return_counts=True)
            big = vals[np.argmax(counts)]
            cand = alive_idx[loc[alive_idx] == big]
            seeds = cand[:min(5000, cand.size)]
            colt = w2.civ.forces[:, CH_TRANS]
            colt[seeds] = np.clip(colt[seeds] + 0.30, 0.0, 1.0)
            adjc = w.civ.adj.tocsr()
            ring1 = np.setdiff1d(np.unique(adjc[seeds].indices), seeds)
            ring2 = np.setdiff1d(np.unique(adjc[ring1].indices),
                                 np.union1d(seeds, ring1))
            ring3 = np.setdiff1d(
                np.unique(adjc[ring2].indices),
                np.union1d(np.union1d(seeds, ring1), ring2))
            deltas = [float(w2.civ.forces[idx, CH_TAU].mean()
                            - w.civ.forces[idx, CH_TAU].mean())]
            def _adapt2():
                if lam_adapt:
                    T2 = lifemod.life_force_target(w2.civ, w2.life)
                    b2 = w2.life.force_baseline
                    b2[:] = np.clip(b2 + lam_adapt
                                    * (w2.civ.forces - T2), 0, 1)
            for _ in range(TAU_DAYS):
                if flab is not None:
                    flab._DAY[0] += 1
                live_one_day(w, rng, relax=relax)
                _adapt()
                live_one_day(w2, rng2, relax=relax)
                _adapt2()
                deltas.append(float(
                    w2.civ.forces[idx, CH_TAU].mean()
                    - w.civ.forces[idx, CH_TAU].mean()))
            d0 = deltas[0]
            half = None
            for i in range(1, len(deltas)):
                if abs(deltas[i]) <= abs(d0) / 2:
                    half = i
                    break
            tau = {"half_life_d": half,
                   "resid_d30": round(deltas[-1] / d0, 3) if d0 else None}
            if lam_adapt is not None and \
                    w.life.force_baseline is not None:
                db = (w2.life.force_baseline[idx, CH_TAU]
                      - w.life.force_baseline[idx, CH_TAU]).mean()
                tau["baseline_shift_d30"] = round(float(db), 5)
                tau["frac_carried_by_baseline"] = round(
                    float(db / deltas[-1]), 3) if deltas[-1] else None
                tau["live_resid_d30"] = round(
                    float((deltas[-1] - db) / d0), 3) if d0 else None
            trans = {f"ring{j}_d30": round(float(
                w2.civ.forces[r_, CH_TRANS].mean()
                - w.civ.forces[r_, CH_TRANS].mean()), 5)
                for j, r_ in ((1, ring1), (2, ring2), (3, ring3))}
    # capability + prevalence
    soft = None
    if cap:
        dr = np.concatenate([c[0] for c in cap])
        da = np.concatenate([c[1] for c in cap])
        neg = dr < -0.05
        pos = dr > 0.05
        soft = {"P_soften_given_negdrive": round(float(
            (da[neg] < 0).mean()), 4) if neg.any() else None,
            "P_harden_given_posdrive": round(float(
                (da[pos] > 0).mean()), 4) if pos.any() else None,
            "frac_agents_negdrive": round(float(neg.mean()), 4)}
    dose = None
    if flab is not None and flab.DOSE_STATS:
        days_d = [v for v in flab.DOSE_STATS.values() if "dose_abs" in v]
        if days_d:
            dose = {
                "enc_pp_day": round(float(np.mean(
                    [v["enc"] / N for v in flab.DOSE_STATS.values()
                     if "enc" in v])), 3),
                "dose_abs_pp_day": round(float(np.mean(
                    [v["dose_abs"] / N for v in days_d])), 5),
                "dist_mean": round(float(
                    sum(v.get("dist_sum", 0.0)
                        for v in flab.DOSE_STATS.values())
                    / max(1, sum(v.get("enc", 0)
                                 for v in flab.DOSE_STATS.values()))), 4),
            }
    enc = None
    if flab is not None:
        enc = {"total": sum(v["n"] for v in flab.ENC_STATS.values()),
               "frac_neg_encounters": round(
                   sum(v["neg"] for v in flab.ENC_STATS.values())
                   / max(1, sum(v["n"] for v in flab.ENC_STATS.values())),
                   4)}
    rich = None
    if cfg.get("rich") and lam_adapt is not None:
        # negative impulse + sustained-exposure forks from day-120
        # state equivalence is NOT possible (day-90 state consumed);
        # rich forks run from the CURRENT day-120 state — registered
        # as the rich-fork protocol (same world, later branch point).
        import copy as _copy
        base_b = w.life.force_baseline.copy()
        gr2 = np.random.default_rng(77)
        alive_idx2 = np.flatnonzero(w.health.alive)
        idx2 = gr2.choice(alive_idx2, size=N // 8, replace=False)
        rich = {}
        for mode in ("neg", "sustained"):
            wf = _copy.deepcopy(w)
            rf = np.random.default_rng(555)
            mag = -0.15 if mode == "neg" else 0.15
            colf = wf.civ.forces[:, CH_TAU]
            colf[idx2] = np.clip(colf[idx2] + mag, 0, 1)
            for dd in range(1, 31):
                if flab is not None:
                    flab._DAY[0] = DAYS + 40 + dd
                if mode == "sustained" and 1 < dd <= 15:
                    colf = wf.civ.forces[:, CH_TAU]
                    colf[idx2] = np.clip(colf[idx2] + 0.15 / 15, 0, 1)
                live_one_day(wf, rf, relax=relax)
                T3 = lifemod.life_force_target(wf.civ, wf.life)
                b3 = wf.life.force_baseline
                b3[:] = np.clip(b3 + lam_adapt
                                * (wf.civ.forces - T3), 0, 1)
            dbf = float((wf.life.force_baseline[idx2, CH_TAU]
                         - base_b[idx2, CH_TAU]).mean())
            rich[mode] = {"baseline_shift_d30": round(dbf, 5)}
    cohort_dalpha = None
    if forced_cohort is not None and 60 in alpha_snaps:
        cohort_dalpha = round(float(
            (w.civ.alpha[forced_cohort]
             - alpha_snaps[60][forced_cohort]).mean()), 5)
    a60 = alpha_snaps.get(60)
    a90 = alpha_snaps.get(90)
    softening_frac = None
    if a60 is not None and a90 is not None:
        alive = w.health.alive
        softening_frac = round(float(
            (a90[alive] < a60[alive] - 1e-6).mean()), 4)
    pf = None
    if casfire:
        pf = {"big_loc": pf_big, "cohort_n": int(pf_cohort.size),
              "fired_total": pf_fired, "fire_days": pf_fire_days,
              "big_loc_fire_days": pf_big_fire_days,
              "series": pf_series}
    cascade_state = {
        "n_residues": len(getattr(w.chronicle, "cascade_residues",
                                  None) or []),
        "n_last_fired": len(getattr(w.chronicle, "cascade_last_fired",
                                    None) or {})}
    return {"arm": name, "cfg": {k: str(v) for k, v in cfg.items()},
            "pf": pf, "cascade_state": cascade_state,
            "eff_sat": eff_panels or None,
            "endurance": end_panels or None,
            "panels": panels, "tau": tau, "transmission": trans,
            "capability": soft, "encounters": enc,
            "softening_frac_60_90": softening_frac,
            "cohort_dalpha": cohort_dalpha,
            "realized_dose": dose,
            "rich_forks": rich,
            "samples_n": len(flab.SAMPLES) if flab is not None else 0,
            "sample_head": flab.SAMPLES[:5] if flab is not None else []}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    import time
    t0 = time.monotonic()
    results = []
    ctx = mp.get_context("spawn")
    with ctx.Pool(processes=min(21, len(ARMS))) as pool:
        for r in pool.imap_unordered(run_arm, list(ARMS)):
            results.append(r)
            p = r["panels"].get(str(DAYS), {})
            t_ = r["tau"] or {}
            tr = r["transmission"] or {}
            print(f"  [{len(results):2d}/{len(ARMS)}] {r['arm']:12s} "
                  f"tau {t_.get('half_life_d')} res {t_.get('resid_d30')} "
                  f"r1 {tr.get('ring1_d30')} r3 {tr.get('ring3_d30')} "
                  f"a {p.get('alpha_mean')} sat {p.get('sat_max')} "
                  f"sdr {p.get('sd_ratio_genesis')} "
                  f"negenc {r['encounters']['frac_neg_encounters']}",
                  flush=True)
    (OUT / "arms.json").write_text(json.dumps(results, indent=1))
    print(f"\nIT6 COMPLETE {round((time.monotonic()-t0)/60, 1)} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
