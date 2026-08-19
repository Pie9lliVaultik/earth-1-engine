# 0.4 Development Diagnostic — RESULT: MISS (dev gate not passed)

**2026-08-19 · dev-only · no holdout touched · thresholds unmoved ·
artifacts preserved: `data/living_readout_dev.json`,
`data/living_readout_dev_cohort.json`**

## RESULT

| arm | national MAE | cohort MAE | gradient dir | calibration | within-country R² |
|---|---:|---:|---:|---:|---:|
| naive | 12.47 | 16.15 | 0.0% | 0.82 | 0.000 |
| legacy-18 | **10.47** | **12.06** | **77.6%** | 0.87 | −0.395 |
| living-26 | 11.33 | 12.54 | 74.1% | 0.85 | −0.615 |

Family ablations (Δ cohort MAE vs full living-26; negative = removal
helps): hope −0.304 · employment −0.143 · mental −0.015 · hunger
−0.003 · deprivation +0.007 · isolation +0.005 · addiction +0.023.
**No living channel currently earns its place on this instrument.**

## INSTRUMENT (verified before believing the negative)

- legacy-18 reproduces the known ~10.5pp national figure → the
  instrument replicates the known answer (Rule 1).
- naive behaves exactly as a floor must: 0% gradient, R²within = 0.
- gradient_n = 903 held-out country×question pairs; cells median n=352.
- **A genuine positive along the way:** legacy-18's 77.6% cohort
  gradient direction is real, previously unmeasured within-country
  structure carried by the trait-age geometry.

## DIAGNOSIS (causal, from the artifacts)

1. **The living channels are ~entirely within-country variance**
   (85–99% per channel) — so country-mean aggregation destroys them at
   national level while still charging the ridge 8 columns on ~53 rows.
   The national miss is mechanistically explained and expected.
2. **At cohort level the lived state adds noise, not cohort signal.**
   The diagnostic world had lived only 60 days from genesis: cohort
   differences in lived state (older = fewer spells, more wealth, more
   decline) take YEARS of coupled evolution to form, and aging has only
   been active since day 284 of the production world. A 60-day fresh
   world cannot have age-graded lives; its lived-state cohort contrasts
   are stochastic.
3. **Both arms have negative within-country R²** — direction majority-
   right, magnitudes overshoot. Uniform ridge shrinks between- and
   within-country effects equally; the within component needs far
   stronger shrinkage. This is precisely the partial-pooling failure
   MRP theory names.

## NEXT ITERATION (smallest defensible corrections, literature-grounded)

- **Feature source: the real civilization, not a fresh toy** — extract
  features from the production day-570 4M snapshot (570 lived days,
  286 of them with active aging), where lived state has had time to
  become age- and place-structured.
- **Partial pooling** (Gelman & Little 1997; Gelman et al., *Improving
  MRP* — already the Bible's IV.2 foundation): country intercepts fit
  freely; within-country cohort effects shrunk hard toward the global
  effect. Implementation: hierarchical ridge with separate λ for the
  demeaned within-component — the minimal multilevel estimator, no new
  nonlinearity.
- Re-run the SAME frozen dev protocol. Report deltas against this
  table. If lived state still adds nothing, the next hypothesis is
  model-side (the world's cohort gradients themselves — Phase 2
  calibration territory), and 0.4 documents that honestly.

## STATUS

0.4 structural layer: green (14 proofs, 6 sabotage controls, leakage
gate, provenance table). **0.4 acceptance: WITHHELD pending the
iteration above.** No deploy, no tag. Do not stop at "the model
failed" — this document is where the job starts.
