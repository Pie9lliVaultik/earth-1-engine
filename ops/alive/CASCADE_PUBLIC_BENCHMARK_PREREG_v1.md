# CASCADE PUBLIC BENCHMARK — PREREGISTRATION v1 (FROZEN FOR REVIEW)

Founder empirical-ontology ruling 2026-08-23. Code under test: `main`
0c1365e, physics `0.8-candidate-v3/39994f0-canonical`. Machine-readable
manifest: `benchmarks/cascade_public/manifest_v1.json`; holdout list:
`holdout_v1.json` / `holdout_v1.sha256`; verifier:
`scripts/cascade_benchmark_manifest_check.py`. No physics modified, no
threshold selected, no data downloaded, no holdout run.

## 0. Rule ontology (recorded)

- `collective_surge` := ONSET OF A SUSTAINED COLLECTIVE-MOBILIZATION /
  CONTENTION EPISODE IN A LOCALITY. Candidate mechanism; externally
  benchmarkable (C1, C2).
- `identity_collapse` := UNVALIDATED LATENT HUMAN-RESPONSE MECHANISM.
  Not an event class. Implementation and threshold untouched. Validity
  decided only by I1 (observable human-state change after independently
  observed shocks). No observable called "identity collapse" is defined.
- RETIRED: the a5ceedc four-arm generic test (Arab Spring / #MeToo /
  same-sex-marriage tipping / 2016 polarization). These are four
  different empirical processes — collective mobilization, information
  diffusion, norm/policy diffusion, a population distribution state —
  and cannot calibrate one generic rule.

## 1. Dataset availability (verified 2026-08-23; nothing downloaded)

| dataset | role | version / date | license / access | integrity |
|---|---|---|---|---|
| MEC — Major Episodes of Contention (Chenoweth & Kang) | C1 truth | Harvard Dataverse doi:10.7910/DVN/JQWQNW, v3, 2026-06-06; JPR 63(4) doi:10.1093/jopres/xjaf008 | **CC0 1.0**, unrestricted | publisher MD5s in manifest (data .tab c3ea1cee…; codebook 4c314592…) |
| ACLED | C2 truth; I1 shock truth | weekly; pin ONE export (date + sha256 at ingestion) | free registration; attribution; **redistribution/commercial use restricted by ToU** | sha256 at ingestion |
| Mass Mobilization (Clark & Regan) | C2 secondary | doi:10.7910/DVN/HTTWYL v5.1, 2022-10-10; 1990-01 → 2020-03, 162 countries | **CC0 1.0** | MD5 e6fa8a2e… |
| UCDP GED | I1 shock truth | 26.1 (1989–2025); Candidate 26.0.7 monthly | **CC BY 4.0** | sha256 at ingestion |
| WVS / EVS (IVS trend) | I1 human-state truth | IVS trend 4.1 (2024-06-30); WVS-7 2017–22, 64 societies | registration; **academic / non-commercial; no redistribution** | sha256 at ingestion |
| ESS | I1 human-state truth (Europe, NUTS) | R11 ed. 3.0 (2025-06-02), 28 countries; rounds 1–11 | registration; ESS licence (**non-commercial terms to confirm**) | sha256 at ingestion |

**Licence decision required (founder/legal):** ACLED, WVS and ESS carry
non-commercial / no-redistribution terms. Earthling Labs is a company;
registration and any commercial-use licence must be obtained before
ingestion. Downloads also require your explicit go-ahead. MEC, MM and
UCDP are unencumbered.

## 2. Exact observables

C1 (MEC): per episode — onset date (month/year resolution per
codebook), country (ISO), city/location text where given, duration
(days), peak size category, goal class (reformist/maximalist),
government response, outcome. Negative controls: all country-years
(1955–2018) with no onset. Unit: country-year (locality-year only where
MEC location text resolves to a genesis region).

C2 (ACLED; MM secondary): per event — date, time_precision, event_type ∈
{Protests, Riots, Violence against civilians, Battles}, admin1/admin2,
lat/long, geo_precision, fatalities. Derived per (locality, episode):
active-day fraction within an MEC episode window, inter-event gap
distribution, activity decay after onset, recurrence after ≥ 30 inactive
days. MM replication: protest size class, demands, state response
(1990–2020).

I1 (WVS/EVS + ESS; shocks from UCDP GED / ACLED): only items present and
longitudinally comparable — WVS/EVS: national pride (Q254 / G006),
feeling of security in neighbourhood (Q131 / H001), confidence in
government (Q71 / E069_11), generalized trust (Q57 / A165), importance
of belonging to nation (where asked). ESS: `trstplt`, `trstlgl`,
`ppltrst`, `aesfdrk` (safety walking alone after dark), `atchctr`
(attachment to country). Shock definition: UCDP GED or ACLED
organized-violence event cluster in adm1 with ≥ 25 fatalities in a 90-day
window (threshold FROZEN here; no sensitivity tuning on holdout).

## 3. Earth-1 mapping and coverage

- Geography: Earth-1 locality = ISO2 country × genesis region × urban.
  443 genesis regions: 30 tier-1 countries with 5–12 authored regions,
  70 tier-2 with 3–5 template regions, 94 tier-3 countries = 1 region.
  Public adm1 → genesis region needs an AUTHORED crosswalk (443 rows;
  genesis regions are macro-regions such as "North India", so adm1→macro
  is many-to-one and unambiguous in tier 1/2, trivial in tier 3). Urban
  flag: ACLED/UCDP location → GeoNames population ≥ 100k ⇒ urban
  (frozen rule). Country-level observables (MEC, surveys without region)
  map to ISO2 directly — full coverage, 194 countries.
- Time: the canonical world has NO calendar. Benchmarks that only need
  event-time alignment (C2 activity structure relative to onset; I1
  response relative to shock) are executable by matching the public
  event's relative timeline to an Earth-1 branch/control pair (common
  random numbers, existing `branch` machinery). Benchmarks that need the
  state of the world BEFORE a dated real onset (C1 as prediction) are
  NOT executable — see §7.
- Detector outputs used: per-day locality hot set and firing log (the
  Stage C hot-history recorder), under two physics arms: H-CASCADE-1
  (canonical) and the incumbent cooldown-only twin (known-defective
  control; must score WORSE on C2 or the benchmark is not discriminating
  — Standing Rule 2).

## 4. Benchmark definitions, metrics, baselines

**C1-PRED (episode onset as prediction)** — status NOT YET EXECUTABLE
(§7). Frozen definition for when it becomes executable: for each
country-year t, predict P(onset in t) from Earth-1 state at end of t−1
conditioned only on information available to t−1. Metrics: AUC, PR-AUC,
Brier skill vs base rate, calibration slope. Baselines: (i) base rate,
(ii) persistence (onset in t−1), (iii) covariate logistic (log GDP pc,
regime score, population, prior-5-year onsets) fit on DEV.

**C1-STRUCT (executable now; LABELED NON-PREDICTIVE)** — compares
distributions only: Earth-1 onsets per locality-year (collective_surge
episode entries) vs MEC onsets per country-year; Earth-1 episode
duration vs MEC duration; onset clustering across localities within a
country. Metrics: rate ratio with 95% CI; KS / Wasserstein on duration.
Pass/fail is NOT defined for C1-STRUCT; it is descriptive context.

**C2 (event activity / temporal structure)** — within real MEC episodes
that have ACLED coverage: active-day fraction, inter-event gap
distribution, activity half-life after onset, recurrence rate after
≥ 30 quiet days. Earth-1 side: within each detector episode, daily
"activity" = residue creation day (firing) and hot-day indicator.
Metrics: Wasserstein distance between Earth-1 and ACLED distributions of
(active-day fraction, gap length, episode length); Spearman between
episode size rank and duration rank. Baselines: (a) PERSISTENT-STATE
null (active every day of the episode) — must be rejected; (b) Poisson
null with matched mean; (c) incumbent cooldown-only physics (control).
Pre-stated discrimination requirement: H-CASCADE-1 must be closer to
ACLED than both (a) and (c) on gap and active-day-fraction, otherwise
C2 is reported as NOT DISCRIMINATING. MM used only to replicate the
gap/recurrence statistics 1990–2020 at country level.

**I1 (identity / security response)** — difference-in-differences on
survey items between consecutive waves for country(-region)s with a
frozen-definition shock between waves vs matched no-shock controls
(same region-income stratum). Earth-1 side: inject the matched shock
class (UCDP/ACLED-defined; NOT Earth-1-detected) into the canonical
world at the matched locality, branch vs control with common random
numbers, read stored and effective FEAR / IDENTITY / COLLECTIVE at
survey-equivalent lags. Executable level: DIRECTION and RANK — sign
agreement of effect per item, Spearman of Earth-1 effect size vs survey
effect size across shocked units, recovery direction at the next wave.
Magnitude is BLOCKED until a force→survey measurement model exists; if
built, it is fit on DEV only and frozen before HOLDOUT. Baselines: zero
effect; sign-only prior (fear ↑, security ↓, trust ↓). `identity_collapse`
is judged solely by whether its IDENTITY response improves I1 sign/rank
agreement over an arm with the rule disabled (rules_off twin) — on DEV
first; holdout once.

## 5. Inclusion / exclusion and negative controls

- C1/C1-STRUCT: MEC episodes 1955–2018, all countries in GENESIS (194);
  MEC countries absent from genesis are dropped and listed. Negative
  controls: every country-year without onset.
- C2: MEC episodes with onset ≥ ACLED country start year + 1 year;
  ACLED events with time_precision = 1 and geo_precision ≤ 2 only.
  Negative controls: matched locality-windows of equal length with no
  MEC episode and < 3 ACLED events.
- I1: survey pairs (wave k, k+1) with the same item wording; shocks per
  §2; controls matched on stratum and pre-wave level. Units with a shock
  in both intervals are excluded.
- Per-country ACLED windows, survey wave pairs, and the shock
  threshold are frozen here and listed in the manifest on ingestion.

## 6. DEV / HOLDOUT

Country-level deterministic split: HOLDOUT iff
sha256("CASCADE_PUBLIC_v1|"+ISO2) mod 10 ≥ 6 → realized 111 DEV / 83
HOLDOUT (`holdout_v1.json`, list sha256 d25828e7…). Temporal holdout in
addition: MEC onsets 2010–2018 and ACLED/UCDP events from 2022 are
HOLDOUT-only. Loaders refuse HOLDOUT rows unless `EARTH1_HOLDOUT_RUN`
carries a founder token; no threshold, crosswalk rule, shock
definition or measurement model may be changed after the first HOLDOUT
read. Balance across UN region × income group is reported, not enforced.

## 7. Feasibility verdict and blockers

- **C1-PRED: NOT YET EXECUTABLE AS PREDICTION.** Earth-1 has no
  historically aligned state: `data/history/` and the 2015 timeline
  were never built (BIBLE.md), the exogenous daily driver table (GDELT
  2.0 BigQuery, macro, conflicts) does not exist, and the assimilation
  filter ("only information available up to the branch date") is
  design-only. Even when built, the overlap with MEC is Feb 2015 →
  Dec 2018 (≈ 4 years, 194 countries ⇒ ~776 country-years, ~tens of
  onsets) — thin for AUC. Missing infrastructure, exactly: (1) driver
  table `data/history/gdelt_daily.csv` + macro + UCDP-dated conflict
  stream; (2) a run of `timeline.build` from 2015-02 with monthly
  snapshots; (3) assimilation restricted to pre-branch information;
  (4) calendar↔synthetic-day alignment recorded in the world manifest.
  No outcome may be fed back into the world to compensate.
- **C1-STRUCT, C2, I1-direction: EXECUTABLE** with event-time
  alignment on the canonical synthetic world; all are labeled
  distribution-level / conditional-response, not prediction.
- **I1-magnitude: BLOCKED** — no force→survey measurement model.
- **Crosswalk:** adm1 → genesis region must be authored (443 rows)
  before C2/I1 at locality level; country level needs none.
- **Licences / downloads:** ACLED, WVS, ESS need registration and a
  commercial-use decision; all downloads need explicit founder
  go-ahead (none performed).
- **Epoch 2 note:** any from-real-world start must initialize
  pre-genesis episode state from MEC/ACLED (H-CASCADE-1's "already hot
  ⇒ no event" convention is an experiment rule, not a history rule).

## 8. What happens on each outcome (frozen)

- C2 discriminating and H-CASCADE-1 closest to ACLED → episode-entry
  semantics retained; flicker/re-entry question goes to a separate
  registered hypothesis informed by the ACLED recurrence statistic.
- C2 not discriminating → benchmark reported as such; no physics change.
- I1 sign/rank: `identity_collapse` arm not better than rules-off →
  rule slated for removal (founder ruling), not re-tuned.

STOP — frozen for founder review. Next action is the licence/download
decision and the adm1→genesis crosswalk authorship, not a run.
