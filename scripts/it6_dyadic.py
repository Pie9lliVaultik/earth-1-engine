"""0.8 IT6 — DYADIC FIELD INTEGRATION runner (frozen registration:
IT6_DYADIC_FIELD_INTEGRATION.md). 13 ablation arms + 8 KA arms.
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
    import earth1.conviction_lab as clab
    import earth1.field_lab as flab
    from earth1.alive import birth_world, live_one_day
    from earth1.types import Force

    cfg = dict(ARMS[name])
    seed_arm = int(cfg.get("seed", SEED))
    if cfg.get("cas"):
        os.environ["EARTH1_CASCADE_COOLDOWN"] = "1"
    else:
        os.environ.pop("EARTH1_CASCADE_COOLDOWN", None)
    w = birth_world(N, seed_arm)
    clab.ALPHA0 = w.civ.alpha.copy()
    flab.FLOUR_REF[0] = w.flourishing
    flab.AROUSAL = np.array(
        [feedmod.AROUSAL_WEIGHT[Force(k)] for k in range(8)])
    flab.DRIVE_ACC[0] = np.zeros(N)
    flab.ENC_COUNT[0] = np.zeros(N, dtype=np.int64)
    flab.SAMPLES.clear()
    flab.ENC_STATS.clear()
    flab.DOSE_STATS.clear()
    flab.SAMPLE_DAYS.clear()
    flab.SAMPLE_DAYS.update((1, 60, 90, 120))

    if cfg.get("extra") == "fastmix":
        import earth1.propagation_lab as plab
        for i, (t, m) in enumerate(w.fabric.by_type.items()):
            w.fabric.by_type[t] = plab.randomized_graph(m, seed=911 + i)
        from earth1.rehome import _recompose_adj
        _recompose_adj(w)

    op = cfg["op"]
    k_arm = int(cfg.get("k", 3))
    mu_arm = float(cfg.get("mu", 0.05))
    if op == "dy":
        am.propagate = flab.make_dyadic_propagate_v6(k_arm, mu_arm)
        feedmod.feed_tick = flab.make_dyadic_feed_v6(mu_arm)
        cont.CONTAGION_GAIN = 0.0
    elif op == "dy_noinf_incprop":
        _orig_prop = am.propagate
        _sampler = flab.make_dyadic_propagate_v6(3, 0.05,
                                                 influence=False)
        def combo(forces, alpha, adj, **kw):
            _sampler(forces, alpha, adj, **kw)
            return _orig_prop(forces, alpha, adj, **kw)
        am.propagate = combo
    elif op == "zero":
        am.propagate = flab.make_dyadic_propagate_v6(0, 0.0)
        feedmod.feed_tick = flab.make_dyadic_feed_v6(0.0,
                                                     influence=False)
        cont.CONTAGION_GAIN = 0.0
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
    if cnv == "dy":
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

    relax = cfg["relax"]
    rng = np.random.default_rng(seed_arm)
    genesis_sd = w.civ.forces[w.health.alive].std(axis=0)
    panels, alpha_snaps = {}, {}
    tau = trans = None
    for d in range(1, DAYS + 1):
        flab._DAY[0] = d
        live_one_day(w, rng, relax=relax)
        if d in (60, 90):
            alpha_snaps[d] = w.civ.alpha.copy()
        if d % 10 == 0:
            panels[str(d)] = panel(w, genesis_sd)
        if d == TAU_AT:
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
            for _ in range(TAU_DAYS):
                flab._DAY[0] += 1
                live_one_day(w, rng, relax=relax)
                live_one_day(w2, rng2, relax=relax)
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
    if flab.DOSE_STATS:
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
    enc = {"total": sum(v["n"] for v in flab.ENC_STATS.values()),
           "frac_neg_encounters": round(
               sum(v["neg"] for v in flab.ENC_STATS.values())
               / max(1, sum(v["n"] for v in flab.ENC_STATS.values())),
               4)}
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
    return {"arm": name, "cfg": {k: str(v) for k, v in cfg.items()},
            "panels": panels, "tau": tau, "transmission": trans,
            "capability": soft, "encounters": enc,
            "softening_frac_60_90": softening_frac,
            "cohort_dalpha": cohort_dalpha,
            "realized_dose": dose,
            "samples_n": len(flab.SAMPLES),
            "sample_head": flab.SAMPLES[:5]}


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
