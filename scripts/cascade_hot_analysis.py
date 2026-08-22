"""CASCADE_IDENTITY_DIAGNOSTIC_1 — offline analysis of the recorded
trigger-opportunity history (open-loop ⇒ exact reconstruction of
cooldown → residue → decay → superposition for any cascade-parameter
variant without rerunning the civilization).

Answers: is the ambient hot set BROAD or a STRUCTURAL MINORITY of
localities? How does exposure reach 85%? Plus the registered one-factor
sensitivity (cooldown / amplitude / half-life / threshold at 0.5/1/2×)
with the known-answer that 1.0× reproduces the recorded fires exactly.
"""
import json
import pickle
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # pickled rule tuples reference earth1.types.Force
RULES_ID = ("identity_collapse", "collective_surge")


def load(path):
    return pickle.load(open(path, "rb"))


def broad_or_minority(h):
    days = len(h["hot"])
    out = {}
    for rule in RULES_ID:
        hot_days = defaultdict(int)
        pop_share = []
        n_hot = []
        for d in range(days):
            uloc, pop = h["loc"][d]
            popmap = dict(zip(uloc.tolist(), pop.tolist()))
            hot = h["hot"][d][(rule, 1.0)]
            for lk in hot.tolist():
                hot_days[lk] += 1
            n_hot.append(len(hot))
            pop_share.append(sum(popmap.get(lk, 0) for lk in hot.tolist())
                             / max(sum(pop.tolist()), 1))
        uloc_last, pop_last = h["loc"][-1]
        popmap = dict(zip(uloc_last.tolist(), pop_last.tolist()))
        n_loc = len(uloc_last)
        hd = np.array([hot_days.get(lk, 0) for lk in uloc_last.tolist()])
        pw = np.array([popmap[lk] for lk in uloc_last.tolist()], float)
        order = np.argsort(-hd)
        top10 = order[: max(1, n_loc // 10)]
        out[rule] = {
            "localities": n_loc,
            "hot_localities_per_day_median": float(np.median(n_hot)),
            "hot_pop_share_per_day_median": round(float(np.median(pop_share)), 4),
            "hot_pop_share_per_day_p90": round(float(np.percentile(pop_share, 90)), 4),
            "frac_localities_ever_hot": round(float((hd > 0).mean()), 4),
            "pop_share_localities_ever_hot": round(float(pw[hd > 0].sum() / pw.sum()), 4),
            "frac_localities_hot_ge_50pct_days": round(float((hd >= days / 2).mean()), 4),
            "pop_share_localities_hot_ge_50pct_days": round(float(pw[hd >= days / 2].sum() / pw.sum()), 4),
            "frac_localities_hot_ge_90pct_days": round(float((hd >= 0.9 * days).mean()), 4),
            "top10pct_localities_share_of_hot_days": round(float(hd[top10].sum() / max(hd.sum(), 1)), 4),
            "hot_days_distribution_quantiles(0,25,50,75,90,100)":
                [int(x) for x in np.percentile(hd, [0, 25, 50, 75, 90, 100])],
            "country_concentration_top5_share_of_hot_days": None,
        }
        # country concentration (loc key // 1000)
        by_c = defaultdict(int)
        for lk, n in hot_days.items():
            by_c[lk // 1000] += n
        tot = max(sum(by_c.values()), 1)
        top = sorted(by_c.values(), reverse=True)[:5]
        out[rule]["country_concentration_top5_share_of_hot_days"] = round(sum(top) / tot, 4)
        out[rule]["countries_with_any_hot_day"] = len(by_c)
    return out


def simulate(h, rule_params, days=None, pre_cooldown_only=False,
             m_thr=1.0):
    """Reconstruct fires + residues for given per-rule parameters:
    rule_params[name] = dict(cooldown, amp, h). Uses hot sets at
    threshold variant m_thr. Returns fires list and per-day per-loc
    IDENTITY shift (pre-clip)."""
    days = days or len(h["hot"])
    last = {}
    fires = []
    residues = []
    shift_days = []
    for d in range(days):
        wday = d            # w.day at detection == d (tick index d+1)
        for rule, p in rule_params.items():
            for lk in h["hot"][d][(rule, m_thr)].tolist():
                key = (rule, lk)
                lastd = last.get(key)
                if lastd is not None and (wday - lastd) < p["cooldown"]:
                    continue
                last[key] = wday
                fires.append((rule, lk, wday))
                residues.append((rule, lk, wday, p["amp"], p["h"]))
        # IDENTITY shift per locality at read day = wday+1 (post-tick)
        rd = wday + 1
        acc = defaultdict(float)
        nres = defaultdict(int)
        alive_res = []
        for (rule, lk, fd, amp, hl) in residues:
            f = 1.0 if hl <= 0 else 2.0 ** (-(rd - fd) / hl)
            if f < 0.01 or abs(amp) * f < 0.01:
                continue
            alive_res.append((rule, lk, fd, amp, hl))
            acc[lk] += -abs(amp) * f      # both rules write IDENTITY negatively
            nres[lk] += 1
        residues = alive_res
        shift_days.append((acc, nres))
    return fires, shift_days


def locality_metrics(h, shift_days, days):
    tot_pop = []
    f05, f20, f45, meanabs, sup3, sup_mean = [], [], [], [], [], []
    episodes = defaultdict(list)
    in_ep = {}
    for d in range(days):
        uloc, pop = h["loc"][d]
        popmap = dict(zip(uloc.tolist(), pop.tolist()))
        P = float(sum(pop.tolist()))
        acc, nres = shift_days[d]
        s05 = s20 = s45 = sab = s3 = 0.0
        wsum = 0.0
        for lk, p in popmap.items():
            sh = max(-0.5, acc.get(lk, 0.0))      # ±0.5 total clip
            a = abs(sh)
            if a > 0.05: s05 += p
            if a > 0.20: s20 += p
            if a > 0.45: s45 += p
            sab += a * p
            n = nres.get(lk, 0)
            if n >= 3: s3 += p
            wsum += n * p
            # episodes at locality level (>0.05)
            if a > 0.05 and lk not in in_ep:
                in_ep[lk] = d
            elif a <= 0.05 and lk in in_ep:
                episodes[lk].append(d - in_ep.pop(lk))
        f05.append(s05 / P); f20.append(s20 / P); f45.append(s45 / P)
        meanabs.append(sab / P); sup3.append(s3 / P); sup_mean.append(wsum / P)
    for lk, st in in_ep.items():
        episodes[lk].append(days - st)
    durs = np.array([x for v in episodes.values() for x in v]) if episodes else np.array([0])
    return {"frac_pop_abs_gt_0.05_terminal": round(f05[-1], 4),
            "frac_pop_abs_gt_0.20_terminal": round(f20[-1], 4),
            "frac_pop_abs_gt_0.45_terminal": round(f45[-1], 4),
            "frac_pop_abs_gt_0.20_max_t": round(max(f20), 4),
            "mean_abs_shift_terminal": round(meanabs[-1], 4),
            "frac_pop_3plus_residues_terminal": round(sup3[-1], 4),
            "mean_residues_per_person_terminal": round(sup_mean[-1], 3),
            "episode_days_median": float(np.median(durs)),
            "episode_days_p95": float(np.percentile(durs, 95))}


def main(paths):
    report = {}
    for path in paths:
        h = load(path)
        seed = h["seed"]; days = len(h["hot"])
        rules = {r[0]: {"cooldown": r[3], "h": r[4],
                        "amp": float(r[2].get("identity", 0.0))}
                 for r in h["rules"] if r[0] in RULES_ID}
        rep = {"days": days, "broad_or_minority": broad_or_minority(h)}
        # KA: 1.0x reproduces the recorded fires for these two rules exactly
        fires, sd = simulate(h, rules)
        rec = sorted((r, l, d) for (r, l, d) in h["fires"] if r in RULES_ID)
        sim = sorted(fires)
        rep["KA_reconstruction_matches_recorded_fires"] = (rec == sim)
        rep["recorded_fires_id_rules"] = len(rec); rep["simulated_fires"] = len(sim)
        rep["baseline_locality_metrics"] = locality_metrics(h, sd, days)
        # exposure mechanism: pop share of localities with >=1 active residue
        # vs the census's per-agent exposed fraction (same thing if overlay is
        # locality-bound) -> reported in baseline metrics (frac>0.05)
        # one-factor sensitivity
        sens = {}
        for factor in ("cooldown", "amp", "h"):
            for m in (0.5, 1.0, 2.0):
                rp = {k: dict(v) for k, v in rules.items()}
                for k in rp:
                    rp[k][factor] = rules[k][factor] * m
                f, s = simulate(h, rp)
                sens[f"{factor}x{m}"] = {"fires": len(f),
                                          **locality_metrics(h, s, days)}
        for m in (0.5, 1.0, 2.0):
            f, s = simulate(h, rules, m_thr=m)
            sens[f"threshold_margin_x{m}"] = {"fires": len(f),
                                               **locality_metrics(h, s, days)}
        rep["sensitivity"] = sens
        report[str(seed)] = rep
    out = ROOT / "data" / "diag1" / "hot_analysis.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, default=str))
    print(json.dumps(report, indent=1, default=str))


if __name__ == "__main__":
    main(sys.argv[1:])
