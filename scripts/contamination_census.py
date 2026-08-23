"""0.8-B (blast radius) — quantify the persistent footprint of three
years of pinned force dynamics on the canonical civilization state.

    python3 scripts/contamination_census.py <snapshot_dir>
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from earth1 import persistence
    from earth1.alive import birth_world
    from earth1.types import CauseOfDeath

    d = Path(sys.argv[1])
    adj = d / "adj.npz"
    w, _r, _i = persistence.load_world(
        d / "world.pkl", adj_path=(adj if adj.exists() else None))
    g = birth_world(200_000, 8801)          # genesis contrast

    out = {"day": int(w.day)}
    alive = w.health.alive
    dead = ~alive

    # 1. who died of what (WAR is fear-driven)
    cod = w.health.cause_of_death[dead]
    counts = {CauseOfDeath(c).name: int(n) for c, n in
              zip(*np.unique(cod, return_counts=True)) if c != 0}
    total_dead = int(dead.sum())
    out["deaths"] = {"total_dead_slots": total_dead, "by_cause": counts}

    # 2. network: tie-weight pile-up at the plasticity cap
    for t in ("friends", "weak"):
        m = w.fabric.by_type[t].tocsr()
        gm = g.fabric.by_type[t].tocsr()
        out[t] = {
            "share_at_cap_2.0": round(float((m.data >= 1.999).mean()), 4)
            if m.nnz else None,
            "w_mean": round(float(m.data.mean()), 4),
            "genesis_share_at_cap": round(
                float((gm.data >= 1.999).mean()), 4) if gm.nnz else None,
            "genesis_w_mean": round(float(gm.data.mean()), 4),
        }

    # 3. traits: variance collapse vs genesis
    for tr in ("openness", "doubt", "desire_intensity"):
        p = getattr(w.civ, tr)[alive]
        gg = getattr(g.civ, tr)[g.health.alive]
        out[tr] = {"sd": round(float(p.std()), 4),
                   "genesis_sd": round(float(gg.std()), 4),
                   "mean": round(float(p.mean()), 4),
                   "genesis_mean": round(float(gg.mean()), 4)}

    # 4. fear-gated economy: durables and spending
    life = w.life
    if life.durables is not None:
        out["durables"] = {
            "mean": round(float(life.durables[alive].mean()), 4),
            "spend_mean": round(float(life.durable_spend[alive].mean()), 5)
            if life.durable_spend is not None else None}

    # 5. migration footprint (diaspora graph = cumulative moves)
    out["diaspora_nnz"] = int(w.fabric.by_type["diaspora"].nnz)
    out["genesis_diaspora_nnz"] = int(g.fabric.by_type["diaspora"].nnz)

    # 6. scarring
    out["spells"] = {
        "mean": round(float(life.spells[alive].mean()), 3),
        "p95": int(np.percentile(life.spells[alive], 95))}

    # 7. governments
    gov = getattr(w, "governments", None) or getattr(w, "gov", None)
    if gov is not None:
        for f in ("legitimacy", "tax", "policing", "welfare"):
            a = getattr(gov, f, None)
            if a is not None:
                a = np.asarray(a, dtype=np.float64)
                out[f"gov_{f}"] = {"mean": round(float(a.mean()), 4),
                                   "max": round(float(a.max()), 4)}
        aww = getattr(gov, "at_war_with", None)
        if aww is not None:
            out["gov_at_war_count"] = int((np.asarray(aww) >= 0).sum())

    path = ROOT / "data" / "contamination_census.json"
    path.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
