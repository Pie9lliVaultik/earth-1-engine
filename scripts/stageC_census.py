"""0.8 ACCEPTANCE — STAGE C: eight-force + cascade census
(frozen: STAGE_CD_METHOD_LOCK.md + STAGE_C_SUBREG.md).
CHARACTERIZATION ONLY — no gate is scored; VOID on instrument
defect only. Measures the shape of C_t = F_effective - F_stored on
a natural candidate-v2 world: who receives an overlay, how many at
once, how long (per-agent episodes), how often the same people, by
rule, by locality, superposition, clip occupancy, peak vs terminal,
and the post-expiry return (instrument check: C is derived).
Bins 0.05 / 0.20 / 0.45 are DESCRIPTIVE (contract scales)."""
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import multiprocessing as mp

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = Path(os.environ.get("EARTH1_PF_OUT",
                          str(ROOT / "data" / "acceptance_0_8" /
                              "stageC")))
N = int(os.environ.get("EARTH1_IT6_N", "200000"))
DAYS = int(os.environ.get("EARTH1_STAGEC_DAYS", "365"))
SEEDS = tuple(int(x) for x in os.environ.get(
    "EARTH1_STAGEC_SEEDS", "9501,9502").split(","))
BINS = (0.05, 0.20, 0.45)
EVERY = 10


def run_seed(seed):
    os.environ["EARTH1_CASCADE_COOLDOWN"] = "1"
    os.environ["EARTH1_DECAY_RESIDUE"] = "1"
    os.environ["EARTH1_COLLECTIVE_CENTERED"] = "1"
    import earth1.alive as am
    import earth1.contagion as cont
    import earth1.feed as feedmod
    import earth1.flourishing as flmod
    import earth1.life as lifemod
    import earth1.conviction_lab as clab
    import earth1.field_lab as flab
    from earth1.alive import (birth_world, live_one_day,
                              effective_forces, cascade_residue_levels)
    from earth1.types import Force
    from earth1.thresholds import TRANSITION_RULES
    w = birth_world(N, seed)
    clab.ALPHA0 = w.civ.alpha.copy()
    flab.FLOUR_REF[0] = w.flourishing
    flab.AROUSAL = np.array(
        [feedmod.AROUSAL_WEIGHT[Force(k)] for k in range(8)])
    flab.DRIVE_ACC[0] = np.zeros(N)
    flab.ENC_COUNT[0] = np.zeros(N, dtype=np.int64)
    am.propagate = flab.make_dyadic_propagate_v6(3, 0.05)
    feedmod.feed_tick = flab.make_dyadic_feed_v6(0.05)
    cont.CONTAGION_GAIN = 0.0
    lifemod.life_force_target = flab.flourishing_level_map(
        lifemod.life_force_target)
    flmod.flourishing_tick = flab.flourishing_writes_disabled(
        flmod.flourishing_tick)

    def conv(forces, alpha, adj):
        n_enc = np.maximum(flab.ENC_COUNT[0], 1)
        drive = flab.DRIVE_ACC[0] / n_enc
        drive[flab.ENC_COUNT[0] == 0] = 0.0
        a = np.clip(alpha, 0.02, 0.98)
        out = np.clip(1 / (1 + np.exp(-(np.log(a / (1 - a))
                                        + 0.003 * drive))), 0.02, 1.0)
        flab.DRIVE_ACC[0][:] = 0.0
        flab.ENC_COUNT[0][:] = 0
        return out
    am.update_conviction = conv
    rng = np.random.default_rng(seed)

    civ = w.civ
    loc = (civ.country.astype(np.int64) * 1000
           + civ.region.astype(np.int64) * 2
           + civ.urban.astype(np.int64))
    rule_fear = {r.name: {k: float(v) for k, v in r.effects.items()}
                 for r in TRANSITION_RULES}
    # per-agent, per-channel episode tracking at the 0.05 bin
    in_ep = np.zeros((N, 8), dtype=bool)
    ep_start = np.zeros((N, 8), dtype=np.int64)
    ep_count = np.zeros((N, 8), dtype=np.int64)
    ep_durations = [[] for _ in range(8)]
    ever = np.zeros((N, 8), dtype=bool)
    days_exposed = np.zeros((N, 8), dtype=np.int64)
    yrs = civ.age * 100.0
    cohorts = {"low income": civ.income == 0,
               "middle income": civ.income == 1,
               "high income": civ.income == 2,
               "under 30": yrs < 30, "over 55": yrs >= 55,
               "urban": civ.urban.astype(bool),
               "rural": ~civ.urban.astype(bool)}
    panels = {}
    for d in range(1, DAYS + 1):
        flab._DAY[0] = d
        live_one_day(w, rng, relax=0.045)
        a = w.health.alive
        C = np.asarray(effective_forces(w)) - civ.forces
        absC = np.abs(C)
        big = absC > BINS[0]
        # episodes
        start = big & ~in_ep
        end = ~big & in_ep
        ep_start[start] = d
        for k in range(8):
            e = end[:, k]
            if e.any():
                ep_durations[k].extend(
                    (d - ep_start[e, k]).tolist())
        ep_count[start] += 1
        in_ep = big
        ever |= big
        days_exposed += big
        if d % EVERY == 0:
            resl = getattr(w.chronicle, "cascade_residues", None) or []
            levels, _ = cascade_residue_levels(resl, w.day)
            # superposition count per agent (locality-level)
            sup_loc = {}
            rule_contrib = {}
            for r in resl:
                sup_loc[r["loc"]] = sup_loc.get(r["loc"], 0) + 1
            for lk, vec in levels:
                pass
            sup_agent = np.zeros(N, dtype=np.int64)
            for lk, cnt in sup_loc.items():
                sup_agent[loc == lk] = cnt
            # rule attribution on FEAR + COLLECTIVE (+ all channels)
            rule_sum = {}
            for r in resl:
                dt = w.day - r["day"]
                f = 1.0 if r["h"] <= 0 else 2.0 ** (-dt / r["h"])
                n_loc = int((loc == r["loc"]).sum())
                rule_sum.setdefault(r["rule"], np.zeros(8))
                rule_sum[r["rule"]] += r["effects"] * f * n_loc
            ages = [int(w.day - r["day"]) for r in resl]
            # locality concentration: share of total |C| in top decile
            locC = {}
            absC_sum_agent = absC[a].sum(axis=1)
            la = loc[a]
            u, inv = np.unique(la, return_inverse=True)
            per_loc = np.bincount(inv, weights=absC_sum_agent)
            srt = np.sort(per_loc)[::-1]
            top_dec = float(srt[:max(1, len(srt) // 10)].sum()
                            / max(srt.sum(), 1e-9))
            clip_pm = float((absC[a].max(axis=1) >= 0.499).mean())
            at_bound_eff = float(((np.asarray(effective_forces(w))[a]
                                   <= 1e-9)
                                  | (np.asarray(effective_forces(w))[a]
                                     >= 1 - 1e-9)).mean())
            P = {
                "alive": int(a.sum()),
                "n_residues": len(resl),
                "frac_now_gt": {str(b): [round(float(
                    (absC[a][:, k] > b).mean()), 4) for k in range(8)]
                    for b in BINS},
                "mean_C": [round(float(C[a][:, k].mean()), 4)
                           for k in range(8)],
                "mean_absC": [round(float(absC[a][:, k].mean()), 4)
                              for k in range(8)],
                "sat_stored": [round(float(max(
                    (civ.forces[a][:, k] > 0.95).mean(),
                    (civ.forces[a][:, k] < 0.05).mean())), 4)
                    for k in range(8)],
                "sat_eff": [round(float(max(
                    (np.asarray(effective_forces(w))[a][:, k] > 0.95)
                    .mean(),
                    (np.asarray(effective_forces(w))[a][:, k] < 0.05)
                    .mean())), 4) for k in range(8)],
                "superposition": {
                    "mean_over_exposed": round(float(
                        sup_agent[a][sup_agent[a] > 0].mean()), 3)
                    if (sup_agent[a] > 0).any() else 0.0,
                    "p95": int(np.percentile(sup_agent[a], 95)),
                    "max": int(sup_agent[a].max()),
                    "frac_pop_with_0": round(float(
                        (sup_agent[a] == 0).mean()), 4),
                    "frac_pop_with_1": round(float(
                        (sup_agent[a] == 1).mean()), 4),
                    "frac_pop_with_2": round(float(
                        (sup_agent[a] == 2).mean()), 4),
                    "frac_pop_with_3plus": round(float(
                        (sup_agent[a] >= 3).mean()), 4)},
                "absC_magnitude": {
                    "p95_over_exposed": [round(float(np.percentile(
                        absC[a][:, k][absC[a][:, k] > BINS[0]], 95)), 4)
                        if (absC[a][:, k] > BINS[0]).any() else 0.0
                        for k in range(8)],
                    "max": [round(float(absC[a][:, k].max()), 4)
                            for k in range(8)]},
                "rule_weighted_level": {
                    k: [round(float(v[c]), 1) for c in range(8)]
                    for k, v in rule_sum.items()},
                "residue_age_days": {
                    "median": float(np.median(ages)) if ages else None,
                    "p95": float(np.percentile(ages, 95)) if ages
                    else None},
                "locality_top_decile_share": round(top_dec, 3),
                "clip_pm05_frac": round(clip_pm, 5),
                "at_bound_effective": round(at_bound_eff, 5),
                "cohort_exposed_gt005_anych": {
                    cn: round(float((big[a & m].any(axis=1)).mean()),
                              4)
                    for cn, m in cohorts.items()},
            }
            panels[str(d)] = P
    # end-of-run per-agent summaries
    a = w.health.alive
    summary = {}
    for k in range(8):
        dur = np.array(ep_durations[k] + [
            DAYS - ep_start[i, k] + 1 for i in np.flatnonzero(in_ep[:, k])
        ]) if (ep_durations[k] or in_ep[:, k].any()) else np.array([])
        ex = ever[a, k]
        summary[k] = {
            "frac_ever_exposed": round(float(ex.mean()), 4),
            "episodes_per_exposed_agent": {
                "median": float(np.median(ep_count[a, k][ex]))
                if ex.any() else 0,
                "p95": float(np.percentile(ep_count[a, k][ex], 95))
                if ex.any() else 0,
                "max": int(ep_count[a, k].max())},
            "repeat_exposure_frac_ge3": round(float(
                (ep_count[a, k] >= 3).mean()), 4),
            "episode_duration_days": {
                "median": float(np.median(dur)) if dur.size else None,
                "p95": float(np.percentile(dur, 95)) if dur.size
                else None,
                "max": int(dur.max()) if dur.size else None},
            "days_exposed_frac_of_year_median_over_exposed": round(
                float(np.median(days_exposed[a, k][ex]) / DAYS), 4)
            if ex.any() else 0.0,
        }
    # instrument recovery check: C is derived -> delete residues -> 0
    w.chronicle.cascade_residues = []
    Cz = np.abs(np.asarray(effective_forces(w)) - civ.forces).max()
    return {"seed": seed, "panels": panels,
            "per_agent_summary": summary,
            "recovery_check_maxC_after_expiry": float(Cz),
            "force_names": [Force(k).name for k in range(8)]}


def _worker(seed):
    try:
        return run_seed(seed)
    except Exception as e:
        import traceback
        return {"seed": seed, "error": str(e),
                "trace": traceback.format_exc()[-2000:]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    ctx = mp.get_context("spawn")
    with ctx.Pool(processes=len(SEEDS), maxtasksperchild=1) as pool:
        res = pool.map(_worker, list(SEEDS))
    errs = [r for r in res if "error" in r]
    verdict = "VOID" if errs else "CHARACTERIZED"
    for r in res:
        if "error" not in r and r["recovery_check_maxC_after_expiry"] > 1e-12:
            verdict = "VOID"
    (OUT / "census.json").write_text(json.dumps(
        {"verdict": verdict, "results": res}, indent=1, default=str))
    print(json.dumps({"verdict": verdict,
                      "errors": [e.get("error") for e in errs]},
                     indent=1))
    print(f"STAGE C {verdict} {round((time.monotonic()-t0)/60,1)} min")


if __name__ == "__main__":
    main()
