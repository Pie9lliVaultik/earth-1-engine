"""BUTTERFLY — full world loop, swept over the coupling parameters.

Two worlds, identical seeds and draws. One agent loses their job. The
sweep runs the coupling levers named in the spec (beta, residue,
critical fraction) and reports the Lyapunov exponent for each.
"""
from __future__ import annotations
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 0.2 MIGRATION NOTE: this instrument now steps THE canonical loop
# (chaos.world_step delegates to alive.live_one_day over a full World).
# Its numbers are NOT comparable with any measured before 0.2 - the
# instrument itself changed. 0.8 re-runs every measurement from scratch.
from earth1.chaos import entropy, lyapunov_from, world_step
from earth1.alive import birth_world

POP = int(os.environ.get("BF_POP", "20000"))
DAYS = int(os.environ.get("BF_DAYS", "120"))
SEED = 42

def fresh():
    return birth_world(POP, SEED)

def run(beta, residue, crit, relax=0.25, perturb=True):
    wA = fresh(); wB = fresh()
    cA, lA, cB, lB = wA.civ, wA.life, wB.civ, wB.life
    rA = np.random.default_rng(1234); rB = np.random.default_rng(1234)
    touched = -1
    if perturb:
        cand = np.flatnonzero(lB.employed); touched = int(cand[len(cand)//2])
        lB.employed[touched] = False; lB.firm[touched] = -1
        lB.tenure[touched] = 0.0; lB.spells[touched] += 1
    div, frac, ent = [], [], []
    for d in range(DAYS):
        world_step(wA, rA, beta=beta, residue=residue,
                   critical_fraction=crit, relax=relax)
        world_step(wB, rB, beta=beta, residue=residue,
                   critical_fraction=crit, relax=relax)
        df = np.abs(cA.forces - cB.forces)
        div.append(float(np.linalg.norm(df)))
        frac.append(float((df.max(axis=1) > 1e-12).mean()))
        ent.append(entropy(cA.forces))
    return div, frac, ent, touched

def main():
    # placebo: identical worlds must diverge by exactly zero
    d0, f0, _, _ = run(1.0, 0.01, 0.15, perturb=False)
    if max(d0) != 0.0:
        print(f"HARNESS VOID: placebo divergence {max(d0):.3e}"); return
    print(f"  placebo divergence exactly 0.0 — harness clean\n")
    print(f"  {'beta':>6s} {'relax':>6s} {'residue':>8s} {'crit':>6s} "
          f"{'lyapunov':>10s} {'%world':>8s} {'entropy':>16s}")
    rows = []
    grid = [(0.0, 0.0, 0.0005, 0.25),          # the old world, reference
            (2.0, 0.25, 0.02, 0.12)]           # the operating point
    for beta, relax, residue, crit in grid:
        div, frac, ent, touched = run(beta, residue, crit, relax=relax)
        L = lyapunov_from(div)
        rows.append({"beta": beta, "relax": relax, "residue": residue,
                     "critical_fraction": crit,
                     "lyapunov": round(L, 5), "final_frac_world": round(frac[-1], 5),
                     "max_frac_world": round(max(frac), 5),
                     "entropy_start": round(ent[0], 4), "entropy_end": round(ent[-1], 4),
                     "chaotic": bool(L > 0.01 and max(frac) > 0.01)})
        print(f"  {beta:6.1f} {relax:6.2f} {residue:8.4f} {crit:6.2f} "
              f"{L:+10.4f} {max(frac):7.1%}  {ent[0]:.3f} -> {ent[-1]:.3f}")
    win = [r for r in rows if r["chaotic"]]
    json.dump({"pop": POP, "days": DAYS, "rows": rows,
               "chaotic_settings": win}, open("data/butterfly_full.json","w"), indent=1)
    print(f"\nCHAOTIC SETTINGS: {len(win)}/{len(rows)}")
    if win:
        b = max(win, key=lambda r: r["lyapunov"])
        print(f"BUTTERFLY VERDICT: CHAOTIC — beta={b['beta']} residue={b['residue']} "
              f"crit={b['critical_fraction']} -> lyapunov {b['lyapunov']:+.4f}/day, "
              f"reached {b['max_frac_world']:.1%} of the world")
    else:
        print("BUTTERFLY VERDICT: still bounded across the swept range")


if __name__ == "__main__":
    main()
