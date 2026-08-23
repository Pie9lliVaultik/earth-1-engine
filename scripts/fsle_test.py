"""FSLE — the finite-size Lyapunov exponent of the living world.

Earth-1's nonlinearity is THRESHOLD-BASED: deprivation clips at a
buffer, employment is boolean, cascades fire on a participation
fraction. An infinitesimal perturbation never crosses a threshold and
so never amplifies — the infinitesimal exponent is ~0 and that is a
true statement about the system rather than a defect in it.

Real perturbations are not infinitesimal. A person loses a job. The
right instrument for an instability whose strength depends on scale is
the finite-size Lyapunov exponent (Aurell et al. 1997): measure the
time for a separation of size d to grow to r*d, and report ln(r)/T.

An ENSEMBLE is used — many different agents perturbed, one at a time —
because the growth rate depends on who it happened to, and a single
draw would be an anecdote.
"""
from __future__ import annotations
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 0.2 MIGRATION NOTE: this instrument now steps THE canonical loop
# (chaos.world_step delegates to alive.live_one_day over a full World).
# Its numbers are NOT comparable with any measured before 0.2 - the
# instrument itself changed. 0.8 re-runs every measurement from scratch.
from earth1.chaos import world_step
from earth1.alive import birth_world

POP = int(os.environ.get("FS_POP", "20000"))
DAYS = int(os.environ.get("FS_DAYS", "40"))
TRIALS = int(os.environ.get("FS_TRIALS", "8"))
R = 2.0
LIVING = dict(beta=2.0, residue=0.02, critical_fraction=0.12, relax=0.25)
LEGACY = dict(beta=0.0, residue=0.0005, critical_fraction=0.25, relax=0.0)

def fresh():
    return birth_world(POP, 42)

def trial(pick, kw):
    wA = fresh(); wB = fresh()
    cA, lA, cB, lB = wA.civ, wA.life, wB.civ, wB.life
    rA = np.random.default_rng(1234); rB = np.random.default_rng(1234)
    cand = np.flatnonzero(lB.employed)
    who = int(cand[pick % len(cand)])
    lB.employed[who] = False; lB.firm[who] = -1
    lB.tenure[who] = 0.0; lB.spells[who] += 1
    d, reach = [], []
    for _ in range(DAYS):
        world_step(wA, rA, **kw); world_step(wB, rB, **kw)
        df = np.abs(cA.forces - cB.forces)
        d.append(float(np.linalg.norm(df)))
        reach.append(float((df.max(axis=1) > 1e-12).mean()))
    d = np.array(d)
    d0 = d[0]
    hit = np.flatnonzero(d >= R * d0)
    t_double = int(hit[0]) + 1 if hit.size else None
    return t_double, float(max(reach)), d0, float(d.max())

def run(kw, label):
    lams, reaches, times = [], [], []
    for i in range(TRIALS):
        t, reach, d0, dmax = trial(i * 7919, kw)
        reaches.append(reach)
        if t:
            times.append(t); lams.append(np.log(R) / t)
        else:
            lams.append(0.0)
    lam = float(np.mean(lams))
    print(f"  {label:44s} {lam:+9.4f}  {np.mean(reaches):8.1%}  "
          f"{(f'{np.mean(times):.1f}d' if times else '--'):>9s}  "
          f"{len(times)}/{TRIALS}")
    return {"config": label, "fsle_per_day": round(lam, 5),
            "mean_reach": round(float(np.mean(reaches)), 4),
            "mean_doubling_days": (round(float(np.mean(times)), 2)
                                   if times else None),
            "trials_that_doubled": f"{len(times)}/{TRIALS}"}

def main():
    print(f"\n  {POP:,} agents. One agent loses their job. {TRIALS} "
          f"different agents, one per trial.\n")
    print(f"  {'configuration':44s} {'FSLE/day':>9s}  {'reach':>8s}  "
          f"{'doubling':>9s}  doubled")
    rows = [run(LEGACY, "legacy (averaging kernel, dead feedback)"),
            run(LIVING, "living world (conviction kernel, closed ring)")]
    json.dump({"pop": POP, "days": DAYS, "trials": TRIALS, "rows": rows},
              open("data/fsle_test.json", "w"), indent=1)
    live = rows[-1]
    print(f"\nFSLE VERDICT: {'CHAOTIC at realistic scale' if live['fsle_per_day'] > 0 else 'bounded'}"
          f" — lambda = {live['fsle_per_day']:+.4f}/day, one job loss "
          f"reaches {live['mean_reach']:.1%} of the world")

if __name__ == "__main__":
    main()
