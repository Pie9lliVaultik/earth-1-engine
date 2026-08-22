"""READ-ONLY DIAGNOSTIC (CASCADE_IDENTITY_DIAGNOSTIC_1, narrowly
targeted): how does the IDENTITY overlay reach ~85% of Earthlings?
Records, on the frozen canonical model, per day: every agent's
locality, whether the agent carries an IDENTITY overlay > 0.05, the
cascade firings; and at three census points the structural traits of
every locality. Computes DIRECT exposure (agent resided in the
locality when a contributing residue was created) vs INDIRECT
(agent moved in after every contributing firing). No physics touched."""
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = Path(os.environ.get("EARTH1_PF_OUT", str(ROOT / "data" / "diag1")))
N = int(os.environ.get("EARTH1_IT6_N", "200000"))
DAYS = int(os.environ.get("EARTH1_DIAG_DAYS", "365"))
SEED = int(os.environ.get("EARTH1_DIAG_SEED", "9501"))
ID = 4   # IDENTITY


def main():
    from earth1.alive import birth_world, live_one_day, effective_forces
    from earth1.thresholds import TRANSITION_RULES
    w = birth_world(N, SEED)
    rng = np.random.default_rng(SEED)
    civ = w.civ
    expiry = {r.name: (r.decay_half_life * np.log2(
        max(abs(v) for v in r.effects.values()) / 0.01))
        for r in TRANSITION_RULES}
    loc_hist = np.zeros((DAYS + 1, N), dtype=np.int32)
    exp_hist = np.zeros((DAYS + 1, N), dtype=bool)
    alive_hist = np.zeros((DAYS + 1, N), dtype=bool)
    fires = []
    census = {}

    def lockey():
        return (civ.country.astype(np.int64) * 1000
                + civ.region.astype(np.int64) * 2
                + civ.urban.astype(np.int64)).astype(np.int32)

    def locality_census(day):
        lk = lockey(); a = w.health.alive
        u, inv = np.unique(lk, return_inverse=True)
        pop = np.bincount(inv).astype(float)
        def mean_of(x):
            return np.bincount(inv, weights=np.where(a, x, 0.0)) / np.maximum(
                np.bincount(inv, weights=a.astype(float)), 1.0)
        lf = a & w.life.in_lf
        unemp = np.bincount(inv, weights=(lf & ~w.life.employed).astype(float)) / \
            np.maximum(np.bincount(inv, weights=lf.astype(float)), 1.0)
        war = None
        if hasattr(w.gov, "at_war_with"):
            cw = np.asarray(w.gov.at_war_with)
            war = (cw[(u // 1000).astype(int)] >= 0)
        census[day] = {"loc": u.tolist(), "pop": pop.tolist(),
                       "urban": (u % 2 == 1).tolist(),
                       "country": (u // 1000).tolist(),
                       "deprivation": mean_of(w.life.deprivation).tolist(),
                       "unemployment": unemp.tolist(),
                       "fear": mean_of(civ.forces[:, 0]).tolist(),
                       "collective": mean_of(civ.forces[:, 3]).tolist(),
                       "identity": mean_of(civ.forces[:, ID]).tolist(),
                       "war": war.tolist() if war is not None else None}

    loc_hist[0] = lockey(); alive_hist[0] = w.health.alive
    locality_census(0)
    for d in range(1, DAYS + 1):
        live_one_day(w, rng)
        loc_hist[d] = lockey()
        alive_hist[d] = w.health.alive
        C = np.asarray(effective_forces(w))[:, ID] - civ.forces[:, ID]
        exp_hist[d] = np.abs(C) > 0.05
        for r in (getattr(w.chronicle, "cascade_residues", None) or []):
            if r["day"] == w.day - 1 and r["effects"][ID] != 0:
                fires.append((r["rule"], int(r["loc"]), int(r["day"])))
        if d in (180, DAYS):
            locality_census(d)
    np.savez_compressed(OUT / f"reach_{SEED}.npz", loc_hist=loc_hist,
                        exp_hist=exp_hist, alive_hist=alive_hist)
    json.dump({"fires": fires, "census": census, "expiry": expiry,
               "seed": SEED, "days": DAYS},
              open(OUT / f"reach_{SEED}.json", "w"))
    # ── direct vs indirect ──────────────────────────────────────────
    by_loc = defaultdict(list)      # loc -> [(fire_day, rule)]
    for rule, lk, fd in fires:
        by_loc[lk].append((fd, rule))
    first_kind = np.zeros(N, dtype=np.int8)   # 0 never, 1 direct, 2 indirect
    direct_days = indirect_days = 0
    ever_in_firing_loc_at_fire = np.zeros(N, dtype=bool)
    for d in range(1, DAYS + 1):
        ex = np.flatnonzero(exp_hist[d] & alive_hist[d])
        lk_d = loc_hist[d]
        # group exposed agents by locality
        for L in np.unique(lk_d[ex]):
            agents = ex[lk_d[ex] == L]
            contrib = [(fd, rule) for (fd, rule) in by_loc.get(int(L), [])
                       if fd < d and (d - fd) <= expiry[rule]]
            if not contrib:
                continue
            fdays = np.array([fd for fd, _ in contrib])
            # resident at any contributing firing day?
            res = np.zeros(agents.size, dtype=bool)
            for fd in np.unique(fdays):
                res |= (loc_hist[fd, agents] == L)
            direct_days += int(res.sum()); indirect_days += int((~res).sum())
            ever_in_firing_loc_at_fire[agents[res]] = True
            newly = agents[first_kind[agents] == 0]
            first_kind[newly] = np.where(res[first_kind[agents] == 0], 1, 2)
    alive_end = alive_hist[DAYS]
    ever = (exp_hist[1:] & alive_hist[1:]).any(axis=0)
    out = {"seed": SEED, "days": DAYS,
           "fires_identity_rules": len(fires),
           "ever_exposed_frac": float(ever[alive_end].mean()),
           "first_exposure_direct_frac": float((first_kind[alive_end] == 1).sum()
                                               / max(ever[alive_end].sum(), 1)),
           "first_exposure_indirect_frac": float((first_kind[alive_end] == 2).sum()
                                                 / max(ever[alive_end].sum(), 1)),
           "exposed_agent_days_direct_frac": direct_days / max(direct_days + indirect_days, 1),
           "exposed_agent_days_indirect_frac": indirect_days / max(direct_days + indirect_days, 1),
           "agents_ever_resident_in_firing_loc_at_fire_frac":
               float(ever_in_firing_loc_at_fire[alive_end].mean()),
           "migrations_total_agent_moves": int((loc_hist[1:] != loc_hist[:-1]).sum()),
           "agents_who_ever_moved_frac": float((loc_hist[1:] != loc_hist[:-1]).any(axis=0)[alive_end].mean())}
    json.dump(out, open(OUT / f"reach_summary_{SEED}.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
