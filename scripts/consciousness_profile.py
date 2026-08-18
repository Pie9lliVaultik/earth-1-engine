"""THE CONSCIOUSNESS PROFILE — five functional signatures, measured.

Not a consciousness detector. A profile: quantities that in a brain are
necessary conditions for consciousness and in a population either
appear or do not.
"""
from __future__ import annotations
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from earth1.fabric import build_fabric
from earth1.genesis import genesis
from earth1.integration import (anticipation, novel_coherence, phase_scan,
                                phi_proxy, self_reference)
from earth1.life import birth_life

POP = int(os.environ.get("CP_POP", "12000"))
DAYS = int(os.environ.get("CP_DAYS", "25"))

def make_world():
    civ = genesis(POP, 42)
    life = birth_life(civ, seed=42)
    civ.adj = build_fabric(civ, life, seed=42).adj
    return civ, life

def main():
    out = {"pop": POP}
    print(f"\n  {POP:,} agents on the structured fabric\n")

    print("  1 GLOBAL INTEGRATION — cut the world in half")
    r = phi_proxy(make_world, days=DAYS); out["phi"] = r
    print(f"      phi-proxy (full state)        {r['phi_proxy']:.5f}")
    print(f"      phi if measured on mean only  {r['phi_on_mean_only']:.5f}")
    print(f"      agents depending on other half "
          f"{r['agents_depending_on_other_half']:.1%}")
    print(f"      cascades whole vs severed     {r['cascades_whole']:.0f} "
          f"vs {r['cascades_severed']:.0f}   (gap {r['cascade_gap']:+.0f})")
    print(f"      entropy  whole vs severed     {r['entropy_whole_end']:.4f} "
          f"vs {r['entropy_severed_end']:.4f}")

    print("\n  2 SELF-MODELLING — the world reads about itself")
    r = self_reference(make_world, days=DAYS + 15); out["self"] = r
    print(f"      self-reference index          {r['self_reference_index']:.5f}")
    print(f"      published state predicts shift {str(r['published_predicts_shift']):>8s}")

    print("\n  3 NOVEL COHERENCE — an event with no precedent")
    r = novel_coherence(make_world, days=DAYS); out["novel"] = r
    print(f"      structure, real fabric        {r['structure_real']:.5f}")
    print(f"      structure, shuffled control   {r['structure_shuffled']:.5f}")
    print(f"      NOVEL COHERENCE               {r['novel_coherence']:+.5f}")

    print("\n  4 ANTICIPATION — does it lean before the crisis lands")
    r = anticipation(make_world, days=90); out["anticipation"] = r
    if r.get("anticipation_lead") is None and r.get("z_score") is None:
        print(f"      {r.get('note')}")
    else:
        print(f"      crisis waves observed         {r['waves']}")
        print(f"      pre-crisis fear drift         {r['pre_crisis_fear_drift']:+.3e}")
        print(f"      vs shuffled null              {r['null_mean']:+.3e}")
        print(f"      z                             {r['z_score']:+.2f}"
              f"   {'ANTICIPATES' if r['anticipates'] else 'no lead'}")

    print("\n  5 PHASE TRANSITION — integration vs coupling")
    r = phase_scan(make_world, days=18); out["phase"] = r
    print(f"      {'beta':>6s} {'phi':>9s} {'cascades':>10s} {'entropy':>9s}")
    for row in r["scan"]:
        print(f"      {row['beta']:6.1f} {row['phi_proxy']:9.5f} "
              f"{row['cascades']:10.0f} {row['entropy_end']:9.4f}")
    print(f"      largest jump between beta {r['largest_jump_between']}, "
          f"size {r['jump_size']:.5f}")
    print(f"      discontinuity ratio (max step / mean step) "
          f"{r['discontinuity_ratio']}")

    json.dump(out, open("data/consciousness_profile.json", "w"), indent=1)

if __name__ == "__main__":
    main()
