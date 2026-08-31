"""c-SHOCK GAIN picker (prereg ops/alive/cycles/cshock.md).

Reads the sweep artifacts, reports G-inv, the covid dose-response
(paired per-seed vs null flag-on), and the interpolated GAIN* hitting
the fetched target (+0.999pp, data/anchors_unemployment_series.v1.json).
"""
import glob
import json
import os

import numpy as np

OUT = os.environ.get("CSHOCK_GAIN_OUT", "/opt/earth1-data/cshock_gain")
TARGET = 0.999
GAINS = (0.0005, 0.001, 0.002, 0.005, 0.01, 0.02)
SEEDS = tuple(range(401, 411))

runs = {}
for p in glob.glob(os.path.join(OUT, "*.json")):
    d = json.load(open(p))
    runs[(d["arm"], d["flag"], d["gain"], d["seed"])] = d

print("G-INV (null arm, flag-on layoff counter + u vs flag-off):")
ginv_ok = True
for s in SEEDS:
    on = runs[("null", "on", 0.05, s)]
    off = runs[("null", "off", 0.0, s)]
    lo = on["distress_layoffs"]
    ginv_ok &= (lo == 0)
    print("  seed %d: layoffs=%d  u_on=%.4f u_off=%.4f  pre_on=%.4f pre_off=%.4f"
          % (s, lo, on["final_u"], off["final_u"], on["pre_u"], off["pre_u"]))
print("  G-inv counter zero:", ginv_ok)

print("COVID dose-response (paired delta vs same-seed null flag-on, pp of LF):")
curve = []
for g in GAINS:
    ds, lo = [], []
    for s in SEEDS:
        c = runs[("covid", "on", g, s)]
        nn = runs[("null", "on", 0.05, s)]
        ds.append((c["final_u"] - nn["final_u"]) * 100)
        lo.append(c["distress_layoffs"])
    m, sd = float(np.mean(ds)), float(np.std(ds))
    curve.append((g, m, sd))
    print("  gain %-6g du=%+.2f ± %.2f pp | layoffs %s" % (g, m, sd, lo))

xs = np.array([c[0] for c in curve])
ys = np.array([c[1] for c in curve])
gain_star = None
for i in range(len(xs) - 1):
    y0, y1 = ys[i], ys[i + 1]
    if (y0 - TARGET) * (y1 - TARGET) <= 0 and y1 != y0:
        lx0, lx1 = np.log(xs[i]), np.log(xs[i + 1])
        gain_star = float(np.exp(lx0 + (TARGET - y0) / (y1 - y0) * (lx1 - lx0)))
        break
print("GAIN* (log-interp to %+.3fpp): %s" % (TARGET, gain_star))
json.dump({"ginv_counter_zero": bool(ginv_ok),
           "curve": [{"gain": g, "du_pp": m, "sd_pp": sd} for g, m, sd in curve],
           "target_pp": TARGET, "gain_star": gain_star},
          open(os.path.join(OUT, "pick.json"), "w"), indent=1)
