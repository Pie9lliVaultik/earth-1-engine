# Earth-1 — Program State of Truth

*Updated 2026-08-16 (night) · maintained alongside every milestone commit*

**Build 29 "One Earth" (external-audit remediation) — LANDED.** Critical event-injection
bug fixed (runs #3–#6 event legs were no-ops — erratum recorded; run #7's pass verified
safe). Sign-aware reinforcement; prior-preserving trait propagation (global rebuild
retired); one WorldState for all API routes; one 194-country registry; corpus wired into
production; all control middlewares mounted. Run #9 on the fixed engine: demography
PASSES (LE 100%, CDR 12.8), legacy cross-sectional event path honestly measured for the
first time (ratio −0.027, wrong sign) — confirming the response law (A3) is the physics
that works. 865 tests green. See PLAN.md.

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
| **Temporal** | 🔶 **A4 registered, run #8 pending — screening predicts partial fail** | Endogenous dynamics ≈ no-change parity (proven via 3-run arc). News statistics carry no signal (proven twice, pre-registered). Response law validated for events (10/12 signs). A4 registered, replay machinery built, headlines fetching. **2026-08-16 evening screen: 38 perceived events through the response law score 44% sign accuracy on W6→W7 — event-driven questions work (environment 86%, abortion 83%, divorce 71%, army_rule 67%), secular-trend questions fail (religion 0%, hard_work 0%, men_leaders 12%). The missing physics is secular drift, not event response. Founder decision pending (see §4).** |
| **Event reaction** | ✅ **PASSING** (run #7, A3, 2026-08-16) | Simulated +0.0572 vs measured +0.0567 — **ratio 1.01** (was 0.02). LLM-read headlines → blind-authored response law → engine. Gain leave-COVID-out; criteria unchanged from original registration. |

### Current honest benchmark numbers (Manifold v2.1, 200K agents, GOQA 40×66)

| Method | CV MAE | Note |
|--------|--------|------|
| **Earth-1 engine** | **10.24pp** | LOO-country folds — sees nothing from held country |
| Aligned country-stereotype | 11.42pp | Strongest leakage-free lookup; sees held country's other answers |
| Plain stereotype | 12.69pp | Mixed polarities cancel |
| Naive global mean | 12.64pp | |

Engine wins 33/40 questions. The v1 "6.1pp" figure used a different protocol and question set — **not comparable**; these are the standing numbers.

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

1. **The age physics laws** (Manifold v2/v2.1). The Bible never specified how age works. We found the world had *no elderly* (all-ages median used as adult mean) and *no aging* (traits frozen at birth). Fixed with: stable-population pyramids from census u18 + the same Gompertz survival the mortality tick uses (one physics, one pyramid); cohort-LE-calibrated mortality; and the **stationarity law** — newborns enter at the young-cohort mean AND everyone's traits slide along the age gradients, so drift can only emerge from composition change, feedback, or exogenous signal, never from the machinery. A test enforces this forever.

2. **Endogenous dynamics cannot track history** (the 63.7% → 39.7% → 44.3% arc). The Bible assumed grounding matters; we *proved* it's necessary — the run #3 "pass" was an artifact of broken physics.

3. **News statistics carry no value-change signal.** Tone (5.6) and theme salience (5.7) both killed by pre-registered, placebo-controlled tests. Signal must be *content*, not statistics. This pruned the grounding stack's cheap tier with evidence.

4. **The temporal response law** — *the week's biggest discovery.* Cross-sectional calibration and temporal response are **different physical quantities with different signs**: COVID fear raised trust (rally) even though fearful societies trust less. The working form:
   `Δopinion = gain × (perceived_shock · question_response_profile)`
   Both structures LLM-authored blind to outcomes; sign prediction is parameter-free. **10/12 correct on real historical reactions, out-of-sample** (p=0.019; effective n≈7–8 stated honestly). 9/11 magnitude near-exact. The Bible has no temporal response law; this is new physics.

5. **Perception discipline** (5.8). One LLM call per news *item* authoring force events — the disciplined version of vivid-node-forge's per-agent absorption (which felt alive but measured 26.4pp GOQA vs our 10.2). Perception authors causes only; clipped, confidence-floored, source-tagged, channel-off-without-key.

6. **Population weighting** (external review, verified, fixed). At 100K agents, 174/194 countries sit at the representation floor — India was 11.2% of agents vs 17.9% of humanity. Census weights now correct all global reads.

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
| FRED key (fred.stlouisfed.org) | Economic signal channel | 2 min |
| ACLED key (acleddata.com) | Conflict signal channel | 5 min + approval wait |
| Hetzner AX102 (when results earn it — your call) | G4 record, permanent world home, scale ladder | 10 min + €259/mo |
| Mail connector or transactional-mail key | Email updates to both inboxes | 5 min |
| Anthropic key | ✅ done (2026-08-16) | — |
