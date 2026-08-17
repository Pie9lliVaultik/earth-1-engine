# Earth-1 — Program State of Truth

## ❄️ ARCHITECTURE FREEZE — 2026-08-17

The behavioral physics of Earth-1 is FROZEN at this commit. Nine external
audit rounds converged: One Earth (one WorldState, one country registry,
one heartbeat — advance_world()), One Law (events enter humans through
the response operator only; E1-0.4 scalar canonical), all 1,591 questions
(27 built-in + 1,564 corpus) carrying blind temporal response profiles,
outcome_forecast domain live, deterioration-checked bit-identical (GOQA
10.24pp across three engine generations). The world lives on Hetzner
(167.233.77.48), single-writer, systemd heartbeat, Polymarket armed.

STANDING RULE from here: NO new mechanisms. Measurement only — G5 rerun
on the served binary with distribution metrics, the benchmark battery,
heterogeneity/ablation program, and the compounding standing record.
Physics changes require a new registered build with the same audit
discipline that produced this freeze.

## 📏 THE MEASUREMENT ERA — first battery (2026-08-17, all same-day)

An external review (the eleventh) attacked the frozen engine. Every
attack that could be answered by measurement was answered same-day on
earth1-prime. Verdicts, plainly:

1. **What produces the headline number.** The GOQA benchmark predicts
   via the calibration model — a ridge regression on 18 national
   feature means through `sigmoid(baseline_logit + features·w)` — not
   through diffusion/feedback/coupling/thresholds. The agents constrain
   the features; the dynamics stack does not produce this number. Said
   here so no reader discovers it as a gotcha.
2. **Inglehart leakage: claim SURVIVES.** Leakage-clean CV (Inglehart
   channel neutralized) 10.57pp vs naive 12.25, still 33/40 — cost of
   the contested channel: 0.33pp (`data/leakage_test.json`).
3. **Attribution (ablation table,** `data/ablation_table.json`**):**
   census-only 11.42 (24/40) → +Hofstede 10.57 (33/40) → +Inglehart
   10.24 (33/40). ~85% of the margin comes from WVS-independent
   sources. Every tier beats naive.
4. **Ridge quality:** honest fitting (standardized features + nested
   alpha) IMPROVES the number (20K smoke: 10.44 vs replica 10.89;
   200K run supervised). The production alpha was accidental massive
   shrinkage — the margin was understated, not inflated.
5. **Scale:** 1M CV = 10.03pp, better than 200K's 10.24 — the review's
   "scale hurts" claim used the wrong number (0.1077 is the 50K parity
   harness). Gain per 5× agents is small; the 8.3B ladder decision is
   Pietro's, with the honest statement being "1M earned 0.21pp".
6. **Unexpected long-run endogenous drift — UNDER ADJUDICATION.** 200y
   zero-forcing: present-state inheritance (A, incumbent) drifts
   conservative (openness −0.0011/yr, desire floor-saturates);
   cohort-entry inheritance (B, candidate E1-0.5) is stationary to 4
   decimals. Neither drift nor stationarity is a bug BY DEFINITION —
   A/B runs vs W6→W7 decide which ontology reality supports
   (`scripts/inheritance_ab_test.py`, registered interpretation in
   docstring). The old stationarity axiom is itself on trial.
7. **Phase-transition thresholds are unreachable — measured.** Max
   national FEAR 0.602 vs trigger 0.7; ECONOMICS floor 0.536 vs 0.3
   (`data/threshold_reachability.json`). Cascades are dead code in
   current physics. Dynamic envelope under a year of continuous
   2008-scale forcing: supervised 50K run pending
   (`data/threshold_envelope.json`). Repair is a design decision, not
   a constant-tweak.
8. **Event-leg honesty (run #10):** the aggregate ratio passes (0.97)
   but the distributional claim is negative — per-country MAE 0.0583
   vs 0.0533 for a uniform shift, variance ratio 0.16, rank
   correlation −0.41. The engine predicts THAT the world reacts, not
   yet WHO reacts most. Per-country susceptibility is the registered
   physics proposal that would address this.
9. **Temporal leg (run #10): honest fail.** Sign accuracy 50.3%
   (p=0.48), MAE 0.032 vs no-change 0.029. Per A5's blind partition
   (15/15 SECULAR) this is the stationarity design's own prediction;
   the decade-scale claim lives or dies with A6 (development-driven
   drift, preregistered, fit W5→W6 only).
10. **THE GRID VERDICT (same-day, 80 combos, 5 seeds, spec frozen
   pre-W5): B > A-0 > C.** Earth-1 Individual (demography +
   generational + response law, social machinery OFF) BEATS no-change
   on W6→W7 MAE (0.02707 vs 0.02905, ±0.0001 across seeds). The full
   civilization LOSES to no-change (0.03146) — and per-mechanism
   ablation attributes the entire 0.44pp damage to ONE ring:
   opinion→trait feedback (C−feedback = 0.02702 ≈ B; all other Δm ≈ 0;
   endogenous events never fired — "not exercised"). Event class: all
   eight variants identical to 4 decimals — the response law does all
   the work. The feedback ring is now owed the same
   artifact-vs-intended-vs-valid adjudication the cohort case got.
   Full tables: experiments/predictive_value/REPORT.md.


*Updated 2026-08-16 (night) · maintained alongside every milestone commit*

**Build 29 "One Earth" (external-audit remediation) — LANDED.** Critical event-injection
bug fixed (runs #3–#6 event legs were no-ops — erratum recorded; run #7's pass verified
safe). Sign-aware reinforcement; prior-preserving trait propagation (global rebuild
retired); one WorldState for all API routes; one 194-country registry; corpus wired into
production; all control middlewares mounted. Run #9 on the fixed engine: demography
PASSES (LE 100%, CDR 12.8), legacy cross-sectional event path honestly measured for the
first time (ratio −0.027, wrong sign) — confirming the response law (A3) is the physics
that works. 905 tests collected, 890 core green (rest env-dependent). See PLAN.md.

**Build 30 — honest rename (2026-08-17 pm): "TWO LAWS, ONE BRIDGE."** The week's
best discovery is that cross-sectional calibration and temporal response are
*different physical quantities with different signs* (COVID fear raised trust).
Calling the architecture "ONE LAW" marketed that discovery away. What is
actually live: a cross-sectional law (levels), a temporal response law
(variations), and a declared bridge with a prohibition on mixing channels
(`event_shift` vs `field_shift`). The paragraph below stands as written
originally, with this correction of its name.

**Build 30 "One Law" (2026-08-17): THE canonical transduction law is live.** An event
enters opinion through exactly one operator — the response law — on its own channel
(`event_shift`), never through cross-sectional features (run #9: wrong sign) and never
through the social-broadcast door (re-audit: sign REVERSAL demonstrated). field_shift
keeps counterfactual/coupling semantics (a different physical object). 27/28 production
questions carry blind-authored response profiles; PHYSICS_VERSION E1-0.4 (validated
scalar path) is canonical everywhere — /world/tick and the daily heartbeat no longer
serve physics G5 never validated. Sign-conflict regression pinned.

---

## 1. Where we are — the Bible's gates

| Gate | Claim | Status | Evidence |
|------|-------|--------|----------|
| **G1–G2** (Phases 0–2: foundation, decomposition) | Manifold reproduces survey ground truth | ✅ **Passed, then honestly reopened** | v1 numbers accepted 2026-08-12; Manifold v2.1 (age-physics fix) reopened them by necessity. New honest numbers below. |
| **G3** (Phase 3: perception sovereign) | LLM only at novelty frontier; honesty guard in code | ✅ **Passed** | Corpus retrieval-first, G3 audit in CI (12 tests every build) |
| **G4** (Phase 4: foresight) | Armed predictions beat market prices retrospectively | ⏳ **Machinery complete, blocked on time-in-market** | Multiverse, arming, sha256 record, resolution loop all built. Needs: daily cron, non-Italian IP (Polymarket), calendar time. Cannot be backfilled. |
| **G5** (Phase 5: the world is alive) | Three legs, pre-registered | 🔶 **2 of 3 legs passing** | See detailed table below |
| **G6** (Phase 6: participation) | Human corrections improve accuracy | ⬜ Not started (deferred by design) | Claim flow exists from earlier builds |
| **G7** (Phase 7: public proof & revenue) | Paid API + public benchmark bundle | 🔶 Infra exists (billing, metering, keys), no public bundle, no customers | |

### G5 in detail — the existential gate (7 recorded runs, append-only)

| Leg | Status | The story |
|-----|--------|-----------|
| **Demography** | ✅ **PASSING** (runs #5, #6, #7) | LE tracking 100% of 130 countries; adult CDR 12.8/1000 in band. Passed only after we found and fixed real physics bugs (see §3). |
| **Temporal** | ❌ **HONEST FAIL at decade scale (run #10) — claim now lives with A6** | Run #10 on the frozen build: sign accuracy 50.3% (p=0.48), MAE 0.032 vs no-change 0.029 — coin-flip, worse than stillness. This is the stationarity design's own prediction, measured correctly. A5's blind partition classified ALL 15 questions SECULAR (the event/secular boundary is a timescale boundary, not a question subset); quarter-scale reactions are the event leg's regime. The decade-scale claim lives or dies with **A6**: development-driven drift, sign-constrained, fit on W5→W6 only, frozen before scoring — plus the A/B inheritance adjudication (Measurement Era §6). Run #8 (A4) still fires when headlines land, recorded as a confirmation run. |
| **Event reaction** | ✅ **PASSING on aggregate — distributional claim NEGATIVE** (runs #7, #10) | Simulated +0.0572 vs measured +0.0567 — **ratio 1.01** (was 0.02); frozen-build rerun 0.97. But run #10's distribution metrics, stated inline where the pass is claimed: per-country MAE 0.0583 vs 0.0533 for a uniform global shift, variance ratio 0.16 (6× too flat), rank correlation −0.41. The engine predicts THAT humanity reacts and by how much on average — not yet WHICH countries react most. |

### Current honest benchmark numbers (Manifold v2.1, 200K agents, GOQA 40×66)

| Method | CV MAE | Note |
|--------|--------|------|
| **Earth-1 calibration model, full** | **10.24pp** | LOO-country folds; produced by the ridge calibration layer, NOT the dynamics stack (see Measurement Era §1) |
| **Earth-1, leakage-clean** | **10.57pp** | Inglehart channel neutralized — the number that survives the leakage attack; 33/40 wins |
| Earth-1, census-only features | 11.42pp | Demographics alone beat naive (24/40) |
| Earth-1 at 1M agents | 10.03pp | Scale helps, mildly (rung 1M earned) |
| Aligned country-stereotype | 11.42pp | Strongest leakage-free lookup; sees held country's other answers |
| Plain stereotype | 12.69pp | Mixed polarities cancel |
| Naive global mean | 12.64pp | |

Engine wins 33/40 questions. Attribution: census carries 0.83pp of margin,
Hofstede +0.85pp (both WVS-independent), Inglehart +0.33pp (the contested
polish). The v1 "6.1pp" figure used a different protocol and question set —
**not comparable**; these are the standing numbers. Honest ridge refit
(standardized + nested alpha) improves them further — 200K run in flight.

---

## 2. Where we deliberately diverged from the Bible

| Topic | Bible said | What we actually did | Why |
|-------|-----------|---------------------|-----|
| **Benchmarking** | MAE targets on calibrated questions | Recalibrate-then-measure GOQA + adversarial baseline ladder (naive, stereotype, aligned-stereotype) + LOO-country CV | "Grades its own homework" is the named liability (§5); we built the adversaries ourselves |
| **G5 temporal protocol** | "Validates against historical opinion time-series" (unspecified) | WVS W6→W7 held-out-in-time, pre-registration committed before results, amendments append-only (A1, A2), inline shuffled-geography placebo | Methodology invented here; it caught three would-be false positives |
| **Scale architecture** | Multi-resolution: 8.3B as *derived projection*, never ticked (§21.3) | **Pietro's directive (2026-08-15): 8.3B ticked daily, reached progressively** — ladder 200K→1M→10M→100M→1B→8.3B, each rung earns the next | Founder decision; staged design agreed (shards, burst fleet, ~$2–5K/mo at full scale) |
| **Infrastructure** | Team + compute assumed | Laptop until results earn hardware (Pietro's call); Hetzner AX102 spec'd and parked | |

---

## 3. Discoveries made here that are NOT in the Bible (and the Bible now needs)

These came from gate failures — each one found by a pre-registered test, fixed, and locked with tests.

1. **The age physics laws** (Manifold v2/v2.1). The Bible never specified how age works. We found the world had *no elderly* (all-ages median used as adult mean) and *no aging* (traits frozen at birth). Fixed with: stable-population pyramids from census u18 + the same Gompertz survival the mortality tick uses (one physics, one pyramid); cohort-LE-calibrated mortality; and the **stationarity law** — newborns enter at the young-cohort mean AND everyone's traits slide along the age gradients, so drift can only emerge from composition change, feedback, or exogenous signal, never from the machinery. ~~A test enforces this forever.~~ **2026-08-17 update: the 200y zero-forcing run showed the incumbent inheritance drifts anyway (age-drifted parents transmit their aged state — a compounding cohort effect), and the deeper question was reopened: should a self-changing civilization be stationary at all? The axiom is now an A/B experiment (Measurement Era §6), and the old 3-year-displacement test will be replaced by whatever bound the adjudicated physics actually earns.**

2. **Endogenous dynamics cannot track history** (the 63.7% → 39.7% → 44.3% arc). The Bible assumed grounding matters; we *proved* it's necessary — the run #3 "pass" was an artifact of broken physics.

3. **News statistics carry no value-change signal.** Tone (5.6) and theme salience (5.7) both killed by pre-registered, placebo-controlled tests. Signal must be *content*, not statistics. This pruned the grounding stack's cheap tier with evidence.

4. **The temporal response law** — *the week's biggest discovery.* Cross-sectional calibration and temporal response are **different physical quantities with different signs**: COVID fear raised trust (rally) even though fearful societies trust less. The working form:
   `Δopinion = gain × (perceived_shock · question_response_profile)`
   Both structures LLM-authored blind to outcomes; sign prediction is parameter-free. **10/12 correct on real historical reactions, out-of-sample** (p=0.019; effective n≈7–8 stated honestly). 9/11 magnitude near-exact. The Bible has no temporal response law; this is new physics.

5. **Perception discipline** (5.8). One LLM call per news *item* authoring force events — the disciplined version of vivid-node-forge's per-agent absorption (which felt alive but measured 26.4pp GOQA vs our 10.2). Perception authors causes only; clipped, confidence-floored, source-tagged, channel-off-without-key.

6. **Population weighting** (external review, verified, partially fixed). At 100K agents, 174/194 countries sit at the representation floor — India was 11.2% of agents vs 17.9% of humanity. Census weights correct the Central Mind global HEADLINE; generic /ask, anatomy, camps, histograms and fragility still operate on raw synthetic-agent mass — moving weighting into the model core is queued (Build 30 remainder), and signed anatomy has not landed.

7. **Scoping fixes** (external review, verified, fixed). "What do Italians think?" now answers about Italians; the gateway knows all 194 countries; corpus hits keep scope.

8. **Anatomy-backwards finding.** Temporal failure concentrates in high-weight questions (6/7 losses above |w|=1.0) — drift noise amplifies through large weights. Shrinkage fix designed, queued.

9. **The secular-trend gap** (2026-08-16 evening screen). Value change decomposes into two regimes: EVENT-DRIVEN (environment, abortion, divorce, army rule — the response law predicts these at 67–86% sign accuracy) and SECULAR (religion, hard work, men-as-leaders, democracy, pride — slow societal drift the response law scores 0–33% on, because no headline stream contains "secularization events"). The event leg passes because it tests the first regime; the temporal leg spans both. Caveats stated honestly: the 24 screening events were curated with outcome knowledge (bias favors success — the negative result is therefore strong), and per-question results have now been inspected, so any secular-drift physics built next is calibration, not blind prediction, until validated on held-out structure.

---

## 3b. The emergence stack — built vs. validated (the honest gap)

Every social-interaction mechanism exists and runs in the living world daily.
Almost none has been *individually* validated against reality — the gates test
the ensemble, and the ensemble result so far is "≈ no-change without exogenous
signal." Component by component:

| Mechanism | Built | Validated against reality? |
|-----------|-------|---------------------------|
| Opinion diffusion over social graph (edge-weighted after audit fix) | ✅ | 🔶 Restores dynamic range on held-out shapes (G2-era test); audit found it calibration-*neutral* — it doesn't add predictive accuracy on levels |
| Opinion→trait feedback (inner loop) | ✅ | ❌ Runs in every tick; no isolated reality test exists |
| Cross-question coupling | ✅ | ❌ Same |
| Non-linear thresholds (phase transitions) | ✅ | ❌ Same — no measured cascade has been reproduced |
| Dynamic graph rewiring (homophily) | ✅ | ❌ Same |
| Model→world event generation (emergent events) | ✅ | ❌ Same |
| Force-field dynamics (8-channel propagation, susceptibility, residue) | ✅ | 🔶 Benchmark-equivalent to scalar path at tick 0; temporal contribution untested |
| Emergence observatory (detection/metrics) | ✅ | — (instrument, not claim) |
| Generational replacement + trait aging | ✅ | ✅ **Demography leg passes**; stationarity law enforced by test |

**What this means:** the emergent machinery is currently *plausible physics
awaiting its experiments*. The response-law work (§4) creates the first real
test bed: once perceived events drive the world, each mechanism can be ablated
(on/off) against measured reactions — does rewiring help or hurt tracking the
COVID rally? Does coupling propagate the NATO shock to related questions as
reality did? That ablation program is the validation path for emergence, and it
becomes possible exactly when the event leg starts passing.

## 4. What is missing for the full model — the critical path

Items 1–3 are DONE. The remaining path:

1. ~~**Wire the response law into the engine**~~ — ✅ DONE (commit 10285f6)
2. ~~**A3 registration + G5 event leg run #7**~~ — ✅ DONE (commit 63b1b78, ratio 1.01)
3. **Historical perceived-headline replay (A4) → G5 run #8** — machinery built and tested (862 tests pass), A4 registered, headlines fetching (~3h remaining). **The evening screen predicts run #8 will fail on secular-trend questions** — the founder decision that now gates the path:
   - **Option A — narrow the temporal claim**: re-register the leg on event-driven windows (quarter-scale reactions) where the validated physics applies. Honest, fast, matches what the engine demonstrably does.
   - **Option B — build secular-drift physics**: development-driven value change (Inglehart modernization axis: countries that develop shift toward secular/self-expression values). New physics, needs development indicators, must be validated on held-out structure since per-question results have been inspected.
   - **Option C — accept 2/3 legs**: demography PASS, event PASS, temporal honest-fail with the gap precisely diagnosed. Move to G4/scale with the limitation documented.
   Run #8 fires when headlines land regardless — a recorded confirmation of the prediction either way.
4. **Expand reaction-case library** 6 → 15–20 cases — sharpens confidence in response law (p=0.019 → p<0.001 or honest bust)
5. **G4 record accumulation** — needs always-on cron (Hetzner or any VPS) + calendar time; every day not running is record lost
6. **Scale ladder Stage A** — shard refactor, 10M on one box (design done, build not started)
7. **G6 participation kernel** — after G5
8. **G7 public benchmark bundle** — packaging what §1 already contains

## 5. What only Pietro can do

| Item | Unblocks | Effort |
|------|----------|--------|
| **8.3B ladder decision** | Honest basis: 1M earned 0.21pp; 8.3B is multi-TB memory; record accumulation is the asset compute can't buy back | decision |
| RunPod API key rotation (exposed in chat/screenshots) | closes a credential exposure | 5 min |
| FRED key (fred.stlouisfed.org) | Economic signal channel | 2 min |
| ACLED key (acleddata.com) | Conflict signal channel | 5 min + approval wait |
| Mail connector or transactional-mail key | Email updates to both inboxes | 5 min |
| Anthropic key | ✅ done (2026-08-16) | — |
| Hetzner fleet | ✅ done (2026-08-17): CCX33 = world's body (single writer, systemd heartbeat + off-site backup), AX162 earth1-prime = laboratory (96 threads), Storage Box = memory. Both machines self-supervise (5-min systemd supervisor, append-only incident journal) — laptop-independent | — |
