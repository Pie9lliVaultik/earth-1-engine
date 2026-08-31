# c-SHOCK — shock-response direction regression (XI.A.2)

**Opened:** 2026-08-31 · **Status:** ITERATING (VERIFY complete, DIAGNOSE in flight, no fix named)
**Ruling context:** Founder ruling 2026-08-31 — Option B, narrowly: one mechanism cycle on
shock response before the 0.9 freeze tag. Benchmark campaign runs in parallel
(`ops/alive/CAMPAIGN_BENCH_v1.md`). Nothing irreversible (tag, holdout spend) until the
founder's explicit word.

## RESULT (the registered MISS)

Two independent instruments name the same mechanism class:

1. **B-DEV direction 80% → 60%** under candidate physics 0.9
   (`/opt/earth1-data/benchmark_b/scoreboard_b.json`, 2026-08-31 17:48, commit 4ba109c).
2. **Dose-suppression:** the registered uniform protest dose SUPPRESSES collective_surge
   onsets relative to null (RETRODICTION_v1, retro estate, seeds 11–18).

## VERIFY (done, from last night's artifacts — no rerun needed, hours old, same commit)

Per-event direction calls, candidate physics:

| event | pct | calls |
|---|---|---|
| gfc_2008 | **100%** | jobs ✓ poverty ✓ hope ✓ |
| covid_2020 | 50% | jobs ✓ poverty ✓ **hope ✗ deaths ✗** |
| arab_spring_2011 | 33% | **govs ✗ displacement ✗** poverty ✓ |

The failures cluster: every **pure-economic** direction passes; every
**force-threshold-mediated** direction (govs via the protest chain, hope via DESIRE,
covid deaths) fails. The miss is real, not instrument noise: same scorer, same events,
same seeds as the 80% run under incumbent physics; only the physics changed.

## DIAGNOSIS (hypothesis to be tested — not assumed)

Mechanical chain, read from code at 4ba109c:

- `life.py:581` gradient: `deprivation = gap·(1−cushion)` — continuous; the cliff put
  ~30.5% of the world at dep≈1.0.
- `life.py:850-860` force coupling is **linear in dep**: FEAR += 0.25·dep,
  COLLECTIVE += 0.40·dep·shared, ECONOMICS −= 0.45·dep, DESIRE −= 0.30·dep.
- Consumption is **hard thresholds tuned against the cliff distribution**:
  `thresholds.py` collective_surge fires on per-agent COLLECTIVE>0.75 & FEAR>0.6;
  `consequences.py:160` protest_risk gates on FEAR>PROTEST_FEAR & **dep>0.4**.

**H1 (absorption):** graded dep halves the force push for the formerly-destitute mass;
threshold-crossers thin out; the same shock that transmitted through the cliff world is
absorbed by the gradient world. Predicts: (dose−null) effect on surge_joint /
protest_risk / onsets is materially smaller under gradient than under cliff, with the
dep>0.4 and force-threshold shares as the mediating stages.

## DIAGNOSE instrument (prereg — frozen before results)

`scripts/cycles/cshock_probe.py` via `scripts/cycles/cshock_chain.sh`:

- Modes: `EARTH1_HARDSHIP_MODE=gradient` (candidate) vs `cliff` (diagnostic config —
  all other candidate constants retained; NOT a physics candidate). Probe records the
  mode the physics actually loaded (tripwire).
- Arms: registered uniform protest dose vs `null_branch()`; contrast is
  (dose − null) **effects** per mode, per the branch-contrast contract.
- Stage 1: 20k × seeds {201,202,203} — chain-stage shares primary (dep>0.4, FEAR>0.6,
  COLLECTIVE>0.75, joint, protest_risk); onsets secondary (known cascade fidelity
  cliff at 20k).
- Stage 2: 200k × seed 301 — onset counts primary.
- **Positive control (Standing Rule 2):** cliff (dose−null) onset effect at 200k must
  be > 0. If the cliff also fails to transmit, the INSTRUMENT is defective →
  VOID-eligible, no mechanism inference, redesign the probe.
- Pre-committed reading: H1 supported iff absorption = cliff_effect − gradient_effect
  is positive on surge_joint AND onsets at 200k.

## VERIFY-2 (2026-08-31, before reading v2 results) — counting instrument defect found

The v1 probe (and `run_retro.py`, and any onset count read from terminal residues)
counts collective_surge onsets from the residue list **surviving at end-of-window**.
Two suppressors live in that instrument, not in the physics:

1. **Residue expiry** (`alive.py:163-181`): a residue leaves the active set when
   `level < 0.01`; at h=30d and |effect|≈0.10 that is ~100 days — shorter than the
   120-day window. Onsets fired in the first ~20 days post-branch are invisible at
   count time. The dose fires exactly there.
2. **Episode-entry semantics** (`alive.py`, H-CASCADE-1): collective_surge counts
   cold→hot ENTRIES. A dose that makes localities hot and keeps them hot yields one
   entry; a flickering null world yields many. "Onsets" measures entries, not pressure.

20k v1 data shows the dissociation these predict: dose RAISES the joint
threshold-crosser share under gradient (+0.040) while terminal-counted onsets FALL
(−70). The RETRODICTION_v1 dose-suppression finding is therefore **suspect as an
instrument artifact** (VOID-eligible for that sub-finding; the null-arm geography
Spearman is unaffected — counting bias is uniform across countries in a ranking).

**Probe v2 (prereg):** event-time capture (every residue logged the tick it appears),
terminal count retained to quantify the bias, all rules logged (competing-rule
dynamics, e.g. polarization_lock's collective −0.12), plus hot-locality-days
(episode intensity, immune to entry counting). Positive control re-read on
event-time counts. v1 200k reads are superseded by v2 on arrival.

Interim v1 20k findings (recorded before v2): absorption REAL on protest_risk
transmission (cliff +182 vs gradient +36, 5×); H1's mediating stage REFUTED — the
dose barely moves deprivation in either mode (dep>0.4 effect ≤0.0014); the dose acts
through direct force injection, and fear transmits MORE under gradient (+0.143 vs
+0.104). Mechanism locus is somewhere between threshold-crossing and onset
accounting, which is exactly what v2 instruments.

## DIAGNOSE — COMPLETE (v2 event-time chain + event-scale artifact analysis)

**v2 probe (event-time counting, 200k seed 301 + 20k×3):**
- Positive control FAILS on surge ENTRIES (cliff dose−null = 0 exactly): the onset-entry
  observable measures cold→hot flicker, not dose response → declared UNINFORMATIVE for
  dose response; RETRODICTION dose-suppression sub-finding **VOID (instrument defect:
  metric semantics)**. Null-arm geography Spearman unaffected.
- On INTENSITY (hot-locality-days) the gradient world transmits MORE than cliff
  (+2,167 vs +300 at 200k; +2,841 vs +470 at 20k): the graded world turns a sustained
  dose into sustained unrest episodes. Rule-mix: gradient responds via identity_collapse
  (+575 events), cliff via panic_cascade (+1,476). The physics responds; the channels
  moved.
- protest_risk absorption is real (cliff +282 vs gradient +7): the `dep>0.4` conjunct
  (consequences.py:160) is cliff-tuned. Real, but SECONDARY — protest_risk is not in
  the failing B-DEV direction set.

**Event-scale transmission (B arm snapshots, candidate, n=5, vs paired controls):**
covid: jobs −24±671 (real: ~10⁸), destitute +2.7 people (real: ~1pp of humanity),
excess deaths ≈0 (no epidemic channel — deliberate exclusion), hope +0.004 (wrong
sign); yet hungry +2,801, evicted +2,501, legitimacy −0.064 — the world responds
internally, the scored observables never see it. gfc: employed −309±885 (noise-scale;
its 100% direction is luck). arab: migrants −2.7 (wrong sign), legitimacy falls −0.034.

**ROOT CAUSE (measured, three links):** (1) the only shock→jobs path is total firm
failure, hazard `0.08/yr × (2−health)` — a MAXIMUM shock merely doubles a 9.6%/yr rate,
while firm health self-heals (173d half-life). covid's firm_damage=0.35 leaves health
at ~0.45: barely distressed, no wave. (2) With jobs ≈ noise, income/gap never move, and
the gradient's cushion (correct for LEVELS) means what little hardship arrives is
absorbed by savings. (3) The old cliff physics transmitted only because binary 0→1
destitution flips manufactured large Δdep from the same weak inputs — an amplifier of
noise, not a transmission channel. The 80%→60% "regression" is mostly the coin
re-flipping on noise-scale responses.

## RESEARCH

Real anchor, fetched and hashed (`data/anchors_unemployment_series.v1.json`, raw sha
fe7ea9012b9995f4…, WB SL.UEM.TOTL.ZS, WLD, 2005–2024): world unemployment
2019→2020 **+0.999pp** (covid), 2008→2009 **+0.585pp** (GFC). Economics: employment
responds to demand CHANGES (Okun); firms shed workers under distress well before
failing. The model's missing mechanism is exactly that.

## IMPLEMENTATION — THE NAMED CHANGE

**Distress-layoff channel** (`earth1/life.py` §2b, flag `EARTH1_DISTRESS_LAYOFFS`,
default off; flag-off is bit-identical — RNG drawn only when on):
per-worker daily layoff probability = `LAYOFF_GAIN × max(0, ema − health − 0.10)` of
their firm, where ema is the firm's own 30-day trailing health. A DROP detector:
exactly zero at any steady state (baseline anchors untouched by construction);
deadband 0.10 ≈ 5× the daily health-noise σ (0.02) so noise never fires it.
LAYOFF_EMA_TAU=30 and DEADBAND=0.10 are FIXED constants (bracket-checked in ablation,
not tuned). LAYOFF_GAIN is the cycle's single FITTED constant.

**Calibration prereg (frozen before results):** sweep GAIN ∈ {0.002, 0.005, 0.01,
0.02, 0.05, 0.10} on the covid_2020 REGISTRY scenario, 20k × seeds {401,402,403},
365d, paired against null-branch. GAIN\* = interpolated to hit **+0.999pp** Δu-rate at
day 365 (census-weighted LF frame). Gates: (G-inv) null-arm flag-on ≡ flag-off within
seed noise; (G-gfc) HELD-OUT check — gfc_2008 scenario at GAIN\* lands +0.585pp within
sign and factor-2 (NOT fitted); (G-anchor) 200k standing census gates unchanged.
RETEST: full B-DEV battery + retro v2-metric rerun under
candidate+`DISTRESS_LAYOFFS=on,GAIN=GAIN\*` — direction gate target ≥80% per the
freeze decision rule.

## IMPLEMENTATION v2 (detector corrected — first sweep's G-inv analysis caught it)

Sweep 1 (24 runs, 50s wall-clock) showed null-arm flag-on drifting **+0.7pp** above
flag-off: the deadband was sized to the DAILY health-noise σ (0.02), but health is a
mean-reverting walk whose 30-day deviation from its own EMA has σ≈0.11 — baseline
noise routinely crossed 0.10 and fired phantom layoffs. Detector v2 adds a
**coherence gate**: layoffs open only where the country-MEAN drop clears
`LAYOFF_COHERENCE=0.08` (~2σ of a small country's mean noise; idiosyncratic noise
cannot move a mean, a real shock hitting a country's firms together can — covid 0.35,
gfc 0.28, arab 0.15 all clear it). Per-firm proportionality past the 0.10 deadband
unchanged. Baseline: all gates closed → exact zero, and a `distress_layoffs` counter
now makes G-inv directly measurable. Sweep 1 artifacts retained
(`cshock_gain/` v1 files); sweep 2 re-runs the same prereg grid.

## IMPLEMENTATION v3 (final form) + CALIBRATION

Detector v2 (coherence gate) ALSO failed G-inv (~600 phantom layoffs/455d at 20k):
firm health is an OU process (reversion 0.004/d, noise 0.02/d) whose 30-day deviation
σ≈0.11 is the same order as real shock damage — with ~9 firms/country at 20k, a 0.08
country-mean gate is ~2σ and 194 countries × 455 days of trials guarantees false
opens. **No within-firm drop detector works in this noise regime.** Final form:
acute distress is its OWN state — `branch.apply()` adds firm_damage to
`firm_distress` (τ=60d exponential decay), layoffs ∝ GAIN × distress of your firm.
Ambient churn and acute shock are now different quantities. Limitation (recorded):
only exogenous/scenario damage drives it until firms have an endogenous P&L.

**Sweep 4 (10 seeds × 6 gains, 20k, covid vs paired null):**
- **G-inv PASSES BITWISE**: 0 layoffs in all null runs; u_on ≡ u_off and pre_u
  identical to 4 decimals on all 10 seeds.
- Dose-response monotone; layoff counters tight (CV ~2%) and linear in gain.
- **GAIN\* = 0.00633** (log-interp to the fetched +0.999pp covid target).

**G-gfc at 20k: UNRESOLVED, not refuted** (mean −0.318, sem 0.39): the registry GFC is
`countries=OECD` — ~18% of the census-weighted world — so its expected world-u signal
is ~+0.3pp, below this instrument's resolution (covid fired ~1,450 layoffs at GAIN\*,
gfc ~85: exactly the scope ratio). Escalated per the standing 20k→200k ladder:
200k × 6 seeds confirmation at FROZEN GAIN\*=0.00633 (nothing retuned) running —
covid must hold +0.999pp; gfc read at decision precision there.

**G-anchor passes by construction**: G-inv is bitwise, and scenario-free worlds have
zero distress — baseline census gates, Benchmark A, and the frozen cohort floor are
untouched by this channel identically. (Corollary: A-FULL-1 will never need a
SUPERSEDED rerun for this change.)

## STATUS

ITERATING — detector v3 calibrated (GAIN\*=0.00633); 200k confirmation in flight;
next: full B-DEV battery retest at candidate+flag (direction gate ≥80% per the freeze
decision rule), then retro rerun on the intensity metric.
Artifacts: `/opt/earth1-data/cshock/` (v1), `cshock_v2/` (event-time),
`cshock_gain_v1detector/`, `_v2detector/`, `_v3detector/` (sweep archaeology),
`cshock_gain/` (sweep 4 + gfc), `cshock_gain_200k/` (confirmation).
