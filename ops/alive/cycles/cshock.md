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

## RESEARCH / IMPLEMENTATION / ABLATION / RETEST

Blocked until DIAGNOSE lands. Admissible change classes will be named from the measured
failing stage (coupling gains vs threshold levels vs dep-rate term), each with the exact
DEV retest: full B-DEV direction gate rerun + retro dose-response rerun + the standing
200k census gates (poverty/mortality must not regress — frozen floors apply).

## STATUS

ITERATING. Chain launched on prime (see `chain.log` in `/opt/earth1-data/cshock/`).
