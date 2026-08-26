# Review — "Earth-1 End-to-End Inference Architecture" PDF (2026-08-26)

Verified against the committed record by a 4-lens audit (contradiction
hunt, build-status map, compute sizing, gap hunt; 67 findings). Verdict:
**independent convergence on the registered architecture** — the PDF
derives the same governing model, same four inference objects, same
build order as EARTH1_INFERENCE_ARCHITECTURE.md, written blind to our
latest results. Adopt its five genuine additions; correct its five
stale/wrong points from campaign evidence.

## Genuinely additive (ADOPT)
1. **SBI synthetic-twin recovery gate** before any real-data θ inference
   (4–6 known parameters, ABC vs NPE vs NRE, SBC ranks, honesty about
   unidentifiable ridges). Not in our plan; sized at 15 min–1.2 h on
   prime (13 s/sim at 20k×90d, 30 slots).
2. **Multi-margin anchoring**: our scalar-K solver is provably right for
   ONE anchor; simultaneous margins need constrained raking with
   per-constraint verification. Correct math; required for C2+.
3. **Data-role registry with read-time enforcement + physical holdout
   isolation** (role ∈ {TRAIN, VALIDATION, HOLDOUT, PROSPECTIVE,
   INPUT_EXPOSURE, EVALUATION_OUTCOME}; target bundles hashed and kept
   off the training mount). Formalizes what we do by hand; would have
   pre-empted the units, fold-collision and GSS bookkeeping slips.
4. **Feature lineage graph** — as an ADDITION to the correlation gate,
   not a replacement (correlation catches leaks lineage cannot see:
   religiosity 0.983 had clean lineage).
5. **`inference_source` receipt** superset of `calibration_source`
   (physics/genesis/latent/θ-draw/forcing/assimilation-cutoff per
   answer) + EnKF-first assimilation (we have a particle filter, no
   EnKF — its recommendation inverts our current estate) + explicit
   macro→micro transport module.

## Stale or wrong (KEEP THE CAMPAIGN RECORD)
1. Its "immediate dose-response experiment" already ran (2A, 24 arms):
   verdicts REDIRECT its plan — adapters repair only a minority; the
   story is gain imbalance + channels, not dose identification.
2. It doesn't know the scorer-units correction: magnitudes are 0.35–1.3
   orders with MIXED signs, and hardship deaths OVERSHOOT ×4 with no
   epi channel — so "WHO meaningful only after an epi module" is
   backwards; the immediate mortality problem is response gain.
3. Mean-preservation theorem, all four KAs, compression trace and the
   abstain-never-recenter guard are BUILT and one-shot confirmed (E3).
4. Its ILO role split is coarser than the registered one (quarterly
   path SHAPE = INPUT; annual total = EVALUATION). Keep ours.
5. Its latent-z holdout plan ("entire untouched WVS items/waves")
   collides with reality: WVS-7 items are essentially consumed. The
   clean external estates are **ESS (never used), EVS Trend, next
   waves, ANES — and prospective data**. Its VNF line numbers differ
   from our verified archive (substance confirmed).

## Catches it forced (fix in the record)
- **GSS is NOT untouched**: R1-COHORT consumed GSS item-years, yet two
  later docs call GSS "untouched". Reclassify: GSS = partially consumed
  (list the R1 item-years); ANES/ESS remain clean.
- Fidelity hazard is concrete here, not generic: cascade physics gates
  on pop≥10 localities — 20k worlds change the cascade regime, so F=0/1
  tiers are invalid for cascade-coupled summaries (SBI pilot must pick
  transfer-safe summaries or run at 200k).
- Assimilation × EPOCH_POLICY needs one amendment when built: a
  state-correction transaction is epoch-preserving (≠ physics change),
  timestamped, never rewrites individual pasts.

## Compute (measured, vs the PDF's "unspecified")
C2+ bake-off ≤1 day · latent-z IRT pilot 1–3 days · SBI synthetic-twin
≤0.5 day · remaining dose axes ≤0.2 day · EnKF 100×200k×365d ≈ 1.5–3 h ·
EnKF 10×4M×30d ≈ 0.5 h. **The PDF's entire identifiability screen ≈ one
week on prime.** Only full trajectory-SBI is weeks-scale, and it is
correctly gated behind the timeline.
