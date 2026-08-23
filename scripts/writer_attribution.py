"""Residual probe 1 — who still writes IDENTITY/TEMPERAMENT in the
all3 configuration? Wrap every patchable subsystem with per-channel
signed-delta recording; predict relax analytically; the remainder is
the inline blocks (cascade rules, trait feedback, births). The
accounting must close: sum(writers) + relax + residual = day delta.
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

N = int(os.environ.get("EARTH1_WA_N", "200000"))
DAYS = int(os.environ.get("EARTH1_WA_DAYS", "40"))
SEED = 8860
CH = ["FEAR", "DESIRE", "ECONOMICS", "COLLECTIVE", "IDENTITY",
      "CULTURE", "EXPERIENCE", "TEMPERAMENT"]
OUT = Path(os.environ.get("EARTH1_WA_OUT",
                          str(ROOT / "data" / "writer_attribution")))

LOG = {}          # writer -> per-day list of (8,) signed mean deltas
_CIV = [None]


def wrap(name, fn):
    def inner(*a, **kw):
        civ = _CIV[0]
        before = civ.forces.mean(axis=0).copy()
        out = fn(*a, **kw)
        after = civ.forces.mean(axis=0)
        LOG.setdefault(name, []).append(after - before)
        return out
    return inner


def main():
    import earth1.alive as am
    import earth1.contagion as cont
    import earth1.feed as feedmod
    import earth1.flourishing as flmod
    import earth1.life as lifemod
    import earth1.health as hmod
    import earth1.institutions as inst
    import earth1.knowledge as kmod
    import earth1.weather as wmod
    import earth1.mobility as mobmod
    import earth1.lab_archive.conviction_lab as clab
    import earth1.lab_archive.field_lab as flab
    from earth1.alive import birth_world, live_one_day
    from earth1.types import Force

    w = birth_world(N, SEED)
    _CIV[0] = w.civ
    clab.ALPHA0 = w.civ.alpha.copy()
    flab.FLOUR_REF[0] = w.flourishing
    flab.AROUSAL = np.array(
        [feedmod.AROUSAL_WEIGHT[Force(k)] for k in range(8)])

    # the all3 configuration
    am.propagate = wrap("propagate",
                        flab.make_dyadic_propagate(k=3, mu=0.05))
    feedmod.feed_tick = wrap("feed", flab.make_dyadic_feed(mu=0.05))
    cont.CONTAGION_GAIN = 0.0
    lifemod.life_force_target = flab.flourishing_level_map(
        lifemod.life_force_target)
    flmod.flourishing_tick = wrap("flourishing",
                                  flab.flourishing_writes_disabled(
                                      flmod.flourishing_tick))
    am.update_conviction = partial(clab.c3_logodds_symmetric,
                                  gain=0.003)
    # remaining subsystems
    cont.contagion_tick = wrap("contagion_events", cont.contagion_tick)
    kmod.knowledge_tick = wrap("knowledge", kmod.knowledge_tick)
    wmod.weather_tick = wrap("weather", wmod.weather_tick)
    inst.apply_policy_and_war = wrap("war",
                                     inst.apply_policy_and_war)
    inst.govern = wrap("govern", inst.govern)
    inst.class_tick = wrap("class", inst.class_tick)
    hmod.health_tick = wrap("health", hmod.health_tick)
    lifemod.life_tick = wrap("life", lifemod.life_tick)
    if hasattr(mobmod, "mobility_tick"):
        mobmod.mobility_tick = wrap("mobility", mobmod.mobility_tick)
    from earth1.memory import Chronicle
    Chronicle.tick = wrap("memory", Chronicle.tick)
    Chronicle.spread = wrap("memory_spread", Chronicle.spread)

    relax = 0.045
    rng = np.random.default_rng(SEED)
    relax_pred, day_delta = [], []
    for d in range(1, DAYS + 1):
        flab._DAY[0] = d
        f0 = w.civ.forces.mean(axis=0).copy()
        t = lifemod.life_force_target(w.civ, w.life)
        relax_pred.append(relax * (t - w.civ.forces).mean(axis=0))
        live_one_day(w, rng, relax=relax)
        day_delta.append(w.civ.forces.mean(axis=0) - f0)

    report = {"days": DAYS, "n": N}
    total = np.array(day_delta).mean(axis=0)
    acc = np.zeros(8)
    for name, rows in LOG.items():
        m = np.array(rows).mean(axis=0)
        acc += m
        report[name] = {CH[c]: round(float(m[c]), 6) for c in range(8)
                        if abs(m[c]) > 5e-6}
    rp = np.array(relax_pred).mean(axis=0)
    resid = total - acc - rp
    report["relax_pred"] = {CH[c]: round(float(rp[c]), 6)
                            for c in range(8) if abs(rp[c]) > 5e-6}
    report["UNEXPLAINED"] = {CH[c]: round(float(resid[c]), 6)
                             for c in range(8)}
    report["day_total"] = {CH[c]: round(float(total[c]), 6)
                           for c in range(8)}
    alive = w.health.alive
    f = w.civ.forces[alive]
    report["end_sat"] = {CH[c]: {"lo": round(float((f[:, c] < 0.05
                                                    ).mean()), 3),
                                 "hi": round(float((f[:, c] > 0.95
                                                    ).mean()), 3)}
                         for c in (4, 7)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "attribution.json").write_text(json.dumps(report, indent=1))
    for k in ("day_total", "relax_pred", "UNEXPLAINED"):
        print(k, report[k])
    for name in LOG:
        row = report.get(name, {})
        if any(abs(v) > 1e-5 for v in row.values()):
            print(f"{name:16s} {row}")
    print("end sat IDENTITY/TEMPERAMENT:", report["end_sat"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
