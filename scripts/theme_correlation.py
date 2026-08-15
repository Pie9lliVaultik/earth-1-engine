#!/usr/bin/env python3
"""Phase 5.7 gate zero: does theme salience correlate with opinion change?

Engine-free by design (5.6 lesson: test the signal BEFORE building the
machinery). For each question with fetched theme data, correlate each
country's theme-coverage statistics (mean salience, salience trend)
against its observed WVS W6->W7 delta.

A theme replay gets built ONLY if this shows signal. Run any time;
scores whatever data/gdelt_themes.json currently holds.
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from earth1.wvs_paired import WVS_PAIRED

MIN_COUNTRIES = 10


def main():
    data = json.loads((ROOT / "data" / "gdelt_themes.json").read_text())
    themes = data.get("_theme_map", {})
    by_id = {pq.id: pq for pq in WVS_PAIRED}

    print("Theme salience vs observed W6->W7 deltas (engine-free):")
    print(f"{'question':18s} {'theme':16s} {'n':>3s} "
          f"{'rho(mean)':>10s} {'p':>7s} {'rho(trend)':>11s} {'p':>7s}")
    any_signal = False
    for qid, theme in themes.items():
        block = data.get(qid, {})
        pq = by_id.get(qid)
        if pq is None:
            continue
        means, trends, deltas = [], [], []
        for cc, series in block.items():
            if cc not in pq.wave6 or cc not in pq.wave7:
                continue
            vals = [series[m] for m in sorted(series)]
            n = len(vals)
            if n < 24:
                continue
            means.append(float(np.mean(vals)))
            trends.append(float(np.mean(vals[-n // 3:]) - np.mean(vals[:n // 3])))
            deltas.append(pq.wave7[cc] - pq.wave6[cc])
        if len(deltas) < MIN_COUNTRIES:
            print(f"{qid:18s} {theme:16s} {len(deltas):>3d}  (waiting for data)")
            continue
        rho_m, p_m = stats.spearmanr(means, deltas)
        rho_t, p_t = stats.spearmanr(trends, deltas)
        flag = " <-- signal" if min(p_m, p_t) < 0.05 else ""
        if min(p_m, p_t) < 0.05:
            any_signal = True
        print(f"{qid:18s} {theme:16s} {len(deltas):>3d} "
              f"{rho_m:>+10.3f} {p_m:>7.4f} {rho_t:>+11.3f} {p_t:>7.4f}{flag}")

    print()
    print("VERDICT: signal present — theme replay justified" if any_signal
          else "VERDICT: no significant signal yet (multiple-comparison "
               "caution applies; ~10 tests at alpha=0.05 expects ~0.5 "
               "false positives)")

    # Pre-specified confirmatory test (declared 2026-08-15 after 3/7
    # themes were visible, before the remaining 4 reported): pooled
    # trend correlation across ALL themes via Stouffer's combined z.
    zs, ns = [], []
    for qid, theme in themes.items():
        block = data.get(qid, {})
        pq = by_id.get(qid)
        if pq is None:
            continue
        trends, deltas = [], []
        for cc, series in block.items():
            if cc not in pq.wave6 or cc not in pq.wave7:
                continue
            vals = [series[m] for m in sorted(series)]
            n = len(vals)
            if n < 24:
                continue
            trends.append(float(np.mean(vals[-n // 3:]) - np.mean(vals[:n // 3])))
            deltas.append(pq.wave7[cc] - pq.wave6[cc])
        if len(deltas) >= MIN_COUNTRIES:
            rho, _ = stats.spearmanr(trends, deltas)
            # Fisher z of rho, weighted by sqrt(n-3)
            zs.append(np.arctanh(np.clip(rho, -0.99, 0.99)) * np.sqrt(len(deltas) - 3))
            ns.append(len(deltas))
    if len(zs) >= 4:
        z_comb = float(np.sum(zs) / np.sqrt(len(zs)))
        p_comb = float(1 - stats.norm.cdf(z_comb))
        print(f"\nPOOLED (pre-specified, {len(zs)} themes): "
              f"Stouffer z={z_comb:.3f}, one-sided p={p_comb:.4f}"
              + ("  <-- CONFIRMED" if p_comb < 0.05 else "  (not significant)"))
    else:
        print(f"\nPOOLED: waiting for >=4 theme blocks ({len(zs)} ready)")


if __name__ == "__main__":
    main()
