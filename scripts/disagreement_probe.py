"""Probe 3 — conviction softening: capability vs prevalence.

all3 configuration to day 60, then 30 days with three cohorts (10k
each) receiving controlled negative agreement drive (the law itself
unchanged — the drive input is overridden for cohort members at
registered strengths), one positive-drive cohort (hardening check),
and a passive control cohort. Alongside: the NATURAL distribution of
agreement drive in the healthy-field world.

Registered drive strengths: −0.1, −0.25, −0.5 (and +0.5).
Measured: P(dAlpha<0 | drive), E[dAlpha | drive], the natural drive
histogram, and the natural fraction with net-negative drive.
"""
import json
import os
import sys
from functools import partial
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

N = int(os.environ.get("EARTH1_DP_N", "200000"))
GROW = int(os.environ.get("EARTH1_DP_GROW", "60"))
PHASE = int(os.environ.get("EARTH1_DP_PHASE", "30"))
SEED = 8880
GAIN = 0.003
COHORT_N = int(os.environ.get("EARTH1_DP_COHORT", "10000"))
OUT = Path(os.environ.get("EARTH1_DP_OUT",
                          str(ROOT / "data" / "disagreement_probe")))

COHORTS = {"d10": -0.10, "d25": -0.25, "d50": -0.50, "p50": +0.50,
           "ctrl": None}


def main():
    import earth1.alive as am
    import earth1.contagion as cont
    import earth1.feed as feedmod
    import earth1.flourishing as flmod
    import earth1.life as lifemod
    import earth1.conviction_lab as clab
    import earth1.field_lab as flab
    from earth1.alive import birth_world, live_one_day
    from earth1.types import Force

    w = birth_world(N, SEED)
    clab.ALPHA0 = w.civ.alpha.copy()
    flab.FLOUR_REF[0] = w.flourishing
    flab.AROUSAL = np.array(
        [feedmod.AROUSAL_WEIGHT[Force(k)] for k in range(8)])
    am.propagate = flab.make_dyadic_propagate(k=3, mu=0.05)
    feedmod.feed_tick = flab.make_dyadic_feed(mu=0.05)
    cont.CONTAGION_GAIN = 0.0
    lifemod.life_force_target = flab.flourishing_level_map(
        lifemod.life_force_target)
    flmod.flourishing_tick = flab.flourishing_writes_disabled(
        flmod.flourishing_tick)
    am.update_conviction = partial(clab.c3_logodds_symmetric,
                                  gain=GAIN)

    rng = np.random.default_rng(SEED)
    for d in range(1, GROW + 1):
        flab._DAY[0] = d
        live_one_day(w, rng, relax=0.045)

    # natural drive distribution in the healthy field
    adj = w.civ.adj
    deg = np.maximum(np.asarray(adj.sum(axis=1)).ravel(), 1.0)
    nbmean = np.asarray(adj @ w.civ.forces) / deg[:, None]
    dist = np.abs(w.civ.forces - nbmean).mean(axis=1)
    agr = 1.0 - 2.0 * np.clip(dist, 0.0, 0.5)
    drive_nat = (agr - 0.5) * 2.0
    alive = w.health.alive
    natural = {
        "drive_mean": round(float(drive_nat[alive].mean()), 4),
        "drive_p05": round(float(np.percentile(drive_nat[alive], 5)), 4),
        "drive_p50": round(float(np.percentile(drive_nat[alive], 50)), 4),
        "frac_negative": round(float((drive_nat[alive] < 0).mean()), 4),
        "hist": np.histogram(drive_nat[alive],
                             bins=np.linspace(-1, 1, 21)
                             )[0].tolist(),
    }

    # assign cohorts and patch the law with per-agent drive override
    gr = np.random.default_rng(7)
    alive_idx = np.flatnonzero(alive)
    chosen = gr.choice(alive_idx, size=min(5 * COHORT_N,
                                       alive_idx.size // 2),
                   replace=False)
    csize = chosen.size // 5
    masks = {}
    override = np.full(N, np.nan)
    for i, (name, drive) in enumerate(COHORTS.items()):
        m = chosen[i * csize:(i + 1) * csize]
        masks[name] = m
        if drive is not None:
            override[m] = drive

    def law_with_override(forces, alpha, adj, gain=GAIN, lam=0.0):
        deg_ = np.maximum(np.asarray(adj.sum(axis=1)).ravel(), 1.0)
        nbmean_ = np.asarray(adj @ forces) / deg_[:, None]
        d_ = np.abs(forces - nbmean_).mean(axis=1)
        agr_ = 1.0 - 2.0 * np.clip(d_, 0.0, 0.5)
        drive = (agr_ - 0.5) * 2.0
        drive = np.where(np.isnan(override), drive, override)
        a = np.clip(alpha, 0.02, 0.98)
        logit = np.log(a / (1.0 - a)) + gain * drive
        return np.clip(1.0 / (1.0 + np.exp(-logit)), 0.02, 1.0)

    am.update_conviction = law_with_override

    a0 = w.civ.alpha.copy()
    for d in range(1, PHASE + 1):
        flab._DAY[0] = GROW + d
        live_one_day(w, rng, relax=0.045)
    a1 = w.civ.alpha

    report = {"natural_drive": natural, "gain": GAIN,
              "phase_days": PHASE, "cohorts": {}}
    for name, m in masks.items():
        live = m[w.health.alive[m]]
        d_alpha = a1[live] - a0[live]
        report["cohorts"][name] = {
            "drive": COHORTS[name],
            "P_soften": round(float((d_alpha < -1e-6).mean()), 4),
            "E_dalpha": round(float(d_alpha.mean()), 6),
            "alpha_end_mean": round(float(a1[live].mean()), 4),
        }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "probe.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
