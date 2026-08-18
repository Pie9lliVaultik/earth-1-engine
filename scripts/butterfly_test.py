"""THE BUTTERFLY TEST — is this world chaotic, or merely complicated?

Pietro's requirement, made falsifiable: "Earthlings need to behave in
ways that we didn't predict."

Two worlds. Identical seed, identical draws, identical everything. In
one of them, ONE agent out of hundreds of thousands loses their job on
day zero. Nothing else differs anywhere in the universe.

Then we watch.

  CHAOTIC              divergence grows exponentially, the Lyapunov
                       exponent is positive, and the difference reaches
                       agents who never met the one we touched
  MERELY COMPLICATED   divergence stays local and bounded — the world
                       is predictable in principle and every subsystem
                       in it is decoration

A PLACEBO arm runs the second world with no perturbation at all. It
must diverge by EXACTLY zero. If it does not, the harness is measuring
its own randomness and every number here is void.

Draw alignment (earth1/life.py) is what makes this valid: every random
quantity is drawn at full population size, so one agent's changed state
cannot shift anyone else's random stream. Divergence is causation.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.genesis import genesis
from earth1.life import birth_life, life_tick

POP = int(os.environ.get("BF_POP", "50000"))
DAYS = int(os.environ.get("BF_DAYS", "180"))
SEED = 42


def fresh():
    civ = genesis(POP, SEED)
    life = birth_life(civ, seed=SEED)
    return civ, life


def entropy(forces: np.ndarray) -> float:
    """Shannon entropy of the population's force distribution.

    A world losing entropy is collapsing toward a fixed point, whatever
    else it appears to be doing.
    """
    tot = 0.0
    for k in range(forces.shape[1]):
        h, _ = np.histogram(forces[:, k], bins=50, range=(0, 1))
        p = h / max(h.sum(), 1)
        p = p[p > 0]
        tot += float(-(p * np.log(p)).sum())
    return tot / forces.shape[1]


def run(perturb: bool):
    civA, lifeA = fresh()
    civB, lifeB = fresh()
    rngA = np.random.default_rng(1234)
    rngB = np.random.default_rng(1234)

    touched = -1
    if perturb:
        # one employed agent, in the middle of the population, loses
        # their job. that is the entire difference between two universes
        cand = np.flatnonzero(lifeB.employed)
        touched = int(cand[len(cand) // 2])
        lifeB.employed[touched] = False
        lifeB.firm[touched] = -1
        lifeB.tenure[touched] = 0.0
        lifeB.spells[touched] += 1

    hist = []
    for d in range(DAYS):
        life_tick(civA, lifeA, rngA, dt_days=1.0)
        life_tick(civB, lifeB, rngB, dt_days=1.0)

        df = np.abs(civA.forces - civB.forces)
        per_agent = df.max(axis=1)
        n_diff = int((per_agent > 1e-12).sum())
        hist.append({
            "day": d,
            "agents_diverged": n_diff,
            "frac_diverged": round(n_diff / POP, 6),
            "mean_force_delta": float(df.mean()),
            "max_force_delta": float(df.max()),
            "jobs_differ": int((lifeA.employed != lifeB.employed).sum()),
            "entropy_A": round(entropy(civA.forces), 5),
        })
    return hist, touched


def lyapunov(hist) -> float:
    """Fit exponential growth to the divergence: d(t) ~ d0 * exp(L t).

    Fitted on the growth phase only — once divergence saturates the
    population, the exponent is no longer defined.
    """
    y = np.array([h["mean_force_delta"] for h in hist])
    nz = np.flatnonzero(y > 0)
    if nz.size < 6:
        return 0.0
    start = int(nz[0])
    frac = np.array([h["frac_diverged"] for h in hist])
    end = int(np.argmax(frac > 0.5)) if (frac > 0.5).any() else len(y)
    end = max(start + 6, min(end, len(y)))
    seg = y[start:end]
    seg = seg[seg > 0]
    if seg.size < 6:
        return 0.0
    t = np.arange(seg.size)
    return float(np.polyfit(t, np.log(seg), 1)[0])


def main() -> None:
    placebo, _ = run(perturb=False)
    worst = max(h["agents_diverged"] for h in placebo)
    if worst != 0:
        print(f"HARNESS VOID: placebo diverged on {worst} agents — the "
              f"test is measuring its own randomness, not causation")
        json.dump({"verdict": "VOID", "placebo_max_diverged": worst},
                  open("data/butterfly_test.json", "w"), indent=1)
        return

    hist, touched = run(perturb=True)
    L = lyapunov(hist)
    final = hist[-1]
    e0, e1 = hist[0]["entropy_A"], hist[-1]["entropy_A"]

    chaotic = L > 0.01 and final["frac_diverged"] > 0.01
    verdict = ("CHAOTIC" if chaotic else
               "BOUNDED — divergence stayed local")

    out = {"pop": POP, "days": DAYS, "perturbed_agent": touched,
           "placebo_max_diverged": worst,
           "lyapunov_exponent_per_day": round(L, 5),
           "final_frac_diverged": final["frac_diverged"],
           "final_agents_diverged": final["agents_diverged"],
           "final_jobs_differ": final["jobs_differ"],
           "entropy_start": e0, "entropy_end": e1,
           "verdict": verdict, "history": hist}
    json.dump(out, open("data/butterfly_test.json", "w"), indent=1)

    print(f"\n  {POP:,} agents. ONE of them (#{touched}) loses their job "
          f"on day 0.")
    print(f"  Placebo arm diverged on {worst} agents — harness is clean.\n")
    print(f"  {'day':>5s} {'agents diverged':>16s} {'% of world':>11s} "
          f"{'mean delta':>12s} {'jobs differ':>12s}")
    for h in hist:
        if h["day"] in (0, 1, 2, 5, 10, 20, 40, 80, 120, DAYS - 1):
            print(f"  {h['day']:5d} {h['agents_diverged']:16,d} "
                  f"{h['frac_diverged']:10.2%} {h['mean_force_delta']:12.3e} "
                  f"{h['jobs_differ']:12,d}")
    print(f"\n  Lyapunov exponent   {L:+.4f} per day")
    print(f"  Entropy             {e0:.4f} -> {e1:.4f}")
    print(f"\nBUTTERFLY VERDICT: {verdict}", flush=True)


if __name__ == "__main__":
    main()
