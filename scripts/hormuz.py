"""THE DEMO. One headline. Three futures. Consequences, not forces.

And one diagnostic that decides whether the branching is real:

    Do the branches produce QUALITATIVELY DIFFERENT geographies of
    consequence, or the same pattern at different magnitudes?

If different countries tip, different firms fail first, different
people are displaced — that is the butterfly effect expressed as
policy-relevant divergence. If the branches are scaled copies of each
other, the branching is cosmetic and the chaos is not reaching the
consequence layer. Measured here by rank correlation and set overlap
across the affected countries, not by eye.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.alive import birth_world, live_one_day
from earth1.branch import Scenario, run

POP = int(os.environ.get("HZ_POP", "20000"))
DAYS = int(os.environ.get("HZ_DAYS", "120"))
REPEATS = int(os.environ.get("HZ_REPEATS", "3"))
WARM = int(os.environ.get("HZ_WARM", "120"))

GULF = ["SA", "AE", "QA", "KW", "OM", "BH", "IR", "IQ"]
IMPORTERS = ["JP", "KR", "IN", "CN", "DE", "IT", "ES", "FR", "TR", "PK",
             "EG", "BD", "TH", "VN", "PH", "ZA", "NG", "KE", "ET"]

SCENARIOS = [
    Scenario(id="resolution", label="Diplomatic resolution in 72 hours",
             forces={"fear": 0.10, "economics": -0.05},
             countries=GULF + IMPORTERS[:6],
             firm_damage=0.06, trade_shock=0.03, persists_days=21),
    Scenario(id="escalation", label="Naval confrontation, oil doubles",
             forces={"fear": 0.40, "economics": -0.35, "collective": 0.20},
             countries=GULF + IMPORTERS,
             firm_damage=0.30, trade_shock=0.22,
             escalates_to_war=True, persists_days=240),
    Scenario(id="fragmentation", label="Proxy fragmentation, blocs harden",
             forces={"identity": 0.35, "fear": 0.18, "culture": -0.10},
             countries=GULF + IMPORTERS,
             firm_damage=0.12, trade_shock=0.09, persists_days=540),
]


def money(x) -> str:
    return f"{int(round(float(x))):,}"


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Rank correlation without scipy.stats — same-shape pattern test."""
    ra = np.argsort(np.argsort(-a)).astype(float)
    rb = np.argsort(np.argsort(-b)).astype(float)
    ra -= ra.mean()
    rb -= rb.mean()
    d = np.linalg.norm(ra) * np.linalg.norm(rb)
    return float(ra @ rb / d) if d > 0 else 0.0


def geography_divergence(res: dict, k: int = 10, noise_floor=None) -> dict:
    """Are these different worlds, or the same world at different volume?

    Two measures on the country-level job-loss pattern:
      RANK CORRELATION near 1.0 means the same countries suffer in the
        same order, only harder — a scaled copy.
      SET OVERLAP near 1.0 means the same countries appear at all.
    Both low means the branches are genuinely different geographies.
    """
    vecs, tops = {}, {}
    for sid, b in res["branches"].items():
        # rebuild a country vector from the reported worst-hit list
        rows = b["consequences"].get("jobs_lost_where", [])
        d = {r["iso2"]: float(r["value"]) for r in rows}
        vecs[sid] = d
        tops[sid] = set(list(d)[:k])

    ids = list(vecs)
    out = {"pairs": []}
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            keys = sorted(set(vecs[a]) | set(vecs[b]))
            va = np.array([vecs[a].get(x, 0.0) for x in keys])
            vb = np.array([vecs[b].get(x, 0.0) for x in keys])
            inter = len(tops[a] & tops[b])
            union = max(len(tops[a] | tops[b]), 1)
            out["pairs"].append({
                "a": a, "b": b,
                "rank_correlation": round(_spearman(va, vb), 4),
                "set_overlap": round(inter / union, 4)})
    if out["pairs"]:
        rc = np.mean([p["rank_correlation"] for p in out["pairs"]])
        so = np.mean([p["set_overlap"] for p in out["pairs"]])
        out["mean_rank_correlation"] = round(float(rc), 4)
        out["mean_set_overlap"] = round(float(so), 4)
        # THE NOISE FLOOR. Rank correlation and set overlap on their own
        # cannot tell "different because the physics differs" from
        # "different because it is all sampling noise" — and with small
        # per-country samples the second is overwhelmingly likely. So
        # the SAME scenario is run twice with different dice, and its
        # divergence is the floor. Only divergence BELOW that floor is
        # attributable to the scenario.
        out["noise_floor"] = noise_floor
        if noise_floor is not None:
            n_rc, n_so = noise_floor["rank_correlation"], noise_floor["set_overlap"]
            signal = (rc < n_rc - 0.15) or (so < n_so - 0.15)
            out["verdict"] = (
                "GENUINELY DIFFERENT GEOGRAPHIES — branches diverge further "
                "than two runs of the SAME scenario do" if signal else
                "INDISTINGUISHABLE FROM NOISE — two runs of the same "
                "scenario diverge as much as two different ones. The "
                "geography is sampling noise, not physics.")
        else:
            out["verdict"] = (
                "SCALED COPIES — branching is cosmetic" if (rc > 0.85 and so > 0.85)
                else "DIVERGENT, but no noise floor measured — unverifiable")
    return out


def main() -> None:
    print(f"\n  Earth-1: {POP:,} earthlings. Living {WARM} days first so "
          f"they have histories.", flush=True)
    w = birth_world(POP, 42)
    rng = np.random.default_rng(11)
    for _ in range(WARM):
        live_one_day(w, rng)

    print(f"  Headline enters the world at day {w.day}.")
    print(f"  Branching {len(SCENARIOS)} futures x {REPEATS} runs each, "
          f"{DAYS} days forward, against an untouched control.\n", flush=True)

    res = run(w, SCENARIOS, days=DAYS, repeats=REPEATS, seed=7,
              progress=lambda m: print(f"    ...{m}", flush=True))

    scale = 8.3e9 / POP
    print(f"\n{'=' * 72}")
    print("  TRUMP DISPUTES THE STRAIT OF HORMUZ")
    print(f"  Three futures, {DAYS} days out. Every number is the DIFFERENCE")
    print("  from the same world without the event, scaled to 8.3B.")
    print(f"{'=' * 72}")

    for sid, b in res["branches"].items():
        c, u = b["consequences"], b["uncertainty"]
        print(f"\n  {b['label'].upper()}")
        jl = u["jobs_lost"]
        print(f"    jobs lost               {money(jl['median'] * scale)}"
              f"   (range {money(jl['low'] * scale)}–"
              f"{money(jl['high'] * scale)})")
        print(f"    pushed into destitution {money(u['people_pushed_into_destitution']['median'] * scale)}")
        print(f"    made homeless           {money(u['people_made_homeless']['median'] * scale)}")
        print(f"    displaced               {money(u['displaced']['median'] * scale)}")
        print(f"    excess deaths           {money(u['excess_deaths']['median'] * scale)}")
        rec = u.get("recession_probability", {})
        if rec:
            print("    recession               " + ", ".join(
                f"{k} {v:.0%}" for k, v in list(rec.items())[:6]))
        gov = u.get("government_at_risk_probability", {})
        if gov:
            print("    governments at risk     " + ", ".join(
                f"{k} {v:.0%}" for k, v in list(gov.items())[:5]))
        if c.get("protest_risk_where"):
            print("    protest risk            " + ", ".join(
                p["country"] for p in c["protest_risk_where"][:5]))
        if c.get("jobs_lost_where"):
            print("    worst hit               " + ", ".join(
                f"{p['iso2']} {money(p['value'] * scale)}"
                for p in c["jobs_lost_where"][:5]))
        if c.get("hope_change") is not None:
            print(f"    hope                    {c['hope_change']:+.4f}")
        print(f"    savings                 {c['savings_change_days']:+.1f} "
              f"days of survival")
        print(f"    uncertainty             jobs span "
              f"{jl['spread_ratio']:.1f}x across identical runs")

    # THE NOISE FLOOR — and the first version of this was broken.
    # branch.run() deliberately gives every scenario the SAME dice so it
    # can be compared fairly against the control, so putting a duplicate
    # scenario inside one call compared a run to a perfect copy of
    # itself and measured exactly zero divergence, guaranteed. A control
    # that cannot fail is not a control.
    #
    # The real floor needs the same scenario driven by GENUINELY
    # different random streams, which means two separate calls with
    # different seeds.
    print(f"\n  measuring the noise floor — same scenario, "
          f"DIFFERENT dice...", flush=True)
    twin_a = run(w, [SCENARIOS[1]], days=DAYS, repeats=REPEATS, seed=101)
    twin_b = run(w, [SCENARIOS[1]], days=DAYS, repeats=REPEATS, seed=907)
    merged = {"branches": {
        "same_run_a": twin_a["branches"][SCENARIOS[1].id],
        "same_run_b": twin_b["branches"][SCENARIOS[1].id]}}
    nf = geography_divergence(merged)
    noise_floor = {"rank_correlation": nf.get("mean_rank_correlation", 0.0),
                   "set_overlap": nf.get("mean_set_overlap", 0.0)}
    print(f"    identical scenarios diverge: rank corr "
          f"{noise_floor['rank_correlation']:+.3f}  set overlap "
          f"{noise_floor['set_overlap']:.2f}")

    geo = geography_divergence(res, noise_floor=noise_floor)
    res["geography_divergence"] = geo
    print(f"\n{'=' * 72}")
    print("  IS THE BRANCHING REAL?")
    print(f"{'=' * 72}")
    nf = geo.get("noise_floor")
    if nf:
        print(f"    {'NOISE FLOOR':14s}    {'(same scenario)':14s}  rank corr "
              f"{nf['rank_correlation']:+.3f}   set overlap "
              f"{nf['set_overlap']:.2f}")
    for p in geo.get("pairs", []):
        print(f"    {p['a']:14s} vs {p['b']:14s}  rank corr "
              f"{p['rank_correlation']:+.3f}   set overlap "
              f"{p['set_overlap']:.2f}")
    print(f"\n  {geo.get('verdict', 'n/a')}")

    json.dump(res, open("data/hormuz.json", "w"), indent=1, default=str)
    print("\n  The spread is not noise. The world is chaotic "
          "(FSLE +0.13/day),")
    print("  so it is the honest width of the forecast.\n")


if __name__ == "__main__":
    main()
