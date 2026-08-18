# Aggregation Audit — Earth-1 Build 12

Two measurements on the frozen engine, both reproducible with
`scripts/audit_aggregation.py`. Neither appears in CRITIQUE_INTERNAL.md or
the eleven external reviews. Both are fixable; neither invalidates the
program.

Measured at pop=100K and 300K, genesis seeds 42/43, CV seeds 42/7/13.
All numbers below are held-out (fold-based CV), extended features,
ridge_alpha=0.1 — the production path.

---

## F1 — The agent population makes the headline number WORSE

Replacing each country's entire agent sub-population with **one mean
agent** — same weights, same baseline, same everything — improves
held-out MAE:

| config | full population | one mean agent | delta |
|---|---|---|---|
| pop 100K, gseed 42, cvseed 42 | 0.1025 | 0.0976 | **−0.49pp** |
| pop 100K, gseed 42, cvseed 7 | 0.1096 | 0.1058 | −0.38pp |
| pop 100K, gseed 43, cvseed 42 | 0.1020 | 0.0974 | −0.47pp |
| pop 300K, gseed 42, cvseed 42 | 0.1023 | 0.0978 | −0.45pp |
| pop 300K, gseed 42, cvseed 7 | 0.1089 | 0.1059 | −0.30pp |

Consistent in sign and magnitude across every configuration tested.

### Mechanism

`calibrate_single` fits in **logit space on country means**:

```
y = logit(target) − baseline_logit   regressed on   mean(features)
```

but prediction evaluates in **probability space over individuals**:

```
pred = mean( sigmoid(baseline_logit + features_i · w) )
```

`mean(sigmoid(z)) ≠ sigmoid(mean(z))`. The gap is Jensen compression
toward 0.5, and it scales with within-country spread.

Measured in the live engine:

- within-country `sd(z)`: **mean 0.91, p90 1.47, max 2.69**
- resulting compression: **mean 2.1pp, p90 5.3pp, max 15.2pp**

Against a total MAE of ~10pp, aggregation artifact is consuming roughly
a fifth of the error budget on average and half of it in the tail.
48% of GOQA targets sit beyond 0.2/0.8, exactly where the gap is largest.

### Why this matters more than the 0.44pp

1. **It explains ladder saturation.** The compression is a property of
   the *distribution*, not the sample size. More agents resolve the same
   compressed distribution more precisely — converging to a slightly
   worse answer. No rung can fix this; 8.3B would not either.
2. **It contaminates force anatomy.** The ridge partially absorbs the
   compression by inflating `w`. So learned weights are not clean force
   sensitivities — their magnitudes carry an aggregation correction
   term. Any "why" narrative read off these weights inherits that.
   (Tested: a post-hoc scalar rescale of `w` recovers only 0.02pp,
   confirming the inflation is already absorbed in-sample.)
3. **Weights are not scale-transferable.** Because the absorbed
   correction depends on within-country variance, weights fitted at one
   population size are mis-specified at another.

### Fixes, cheapest first

- **A (1 line, honest):** report the mean-agent prediction as the
  headline and the population prediction as the distributional
  claim. Removes the artifact; costs the "agents produce the number"
  story, which STATUS.md §1 already concedes.
- **B (correct, ~20 lines):** fit `w` by minimizing error against the
  *aggregated* prediction — i.e. optimize
  `mean(sigmoid(bl + X_c w))` vs target directly (scipy least_squares,
  64 countries, seconds per question). Objective then matches metric.
- **C (analytic, cheap):** second-order correction —
  `E[σ(z)] ≈ σ(μ) + ½σ''(μ)·Var(z)` — applied inside the fit. Fast,
  accurate to ~sd(z) ≲ 1.5, degrades in the tail.

**B is the right one.** It is the only fix under which adding agents can
help rather than hurt, which is the precondition for the population
being load-bearing at all.

---

## F2 — CV-fold noise is 3× the ladder's claimed scale gain

Same rung, same engine, only the CV fold seed changes:

| cv_seed | held-out MAE |
|---|---|
| 42 | 0.1024 |
| 7 | 0.1096 |
| 13 | 0.1085 |

**Spread: 0.72pp.** The ladder's flagship statement — 10.24 → 10.03 →
10.19, "1M earned 0.21pp" — is comfortably inside fold noise measured at
a single scale. Genesis-seed variation, by contrast, is small
(0.1025 vs 0.1020): the dominant noise source is *which countries land
in which fold*, not agent sampling.

Implication: the 200K/1M/10M comparison as currently reported cannot
support any conclusion about scale, in either direction. The honest
statement today is "no measured scale effect above fold noise."

**Fix:** fix the fold partition once (a committed
`data/cv_folds.json`), reuse it across every rung, and report
mean ± spread over ≥3 fold seeds. Cost: minutes. This also makes the
ladder table comparable across future builds.

Secondary: `mask.sum() < 10` silently drops countries, and the dropped
set changes with population (63 countries at 200K vs 64 at 1M — Andorra
enters). Small, but it means rungs are not evaluated on identical sets.
Pin the country set alongside the folds.

---

## Reproduce

```bash
PYTHONPATH=. python3 scripts/audit_aggregation.py \
    --pop 200000 --genesis-seed 42 --cv-seeds 42,7,13
```

Writes `data/audit_aggregation.json`.

---

## What this does not touch

The adversarial ladder result stands: engine 10.24 vs aligned-stereotype
11.42 vs naive 12.25. F1 shifts the engine number *in its favour*
(9.8 with the mean-agent estimator); F2 widens the error bar on all
three. The ranking is unaffected. Ablation attribution (census→Hofstede
→Inglehart) is likewise unaffected — it is a relative comparison under
the same estimator.
