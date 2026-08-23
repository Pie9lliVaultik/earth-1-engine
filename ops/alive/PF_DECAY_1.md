# PF-DECAY-1 — decay_half_life CONTRACT RESTORATION (pre-registered)

Pre-freeze CONFORMANCE experiment (founder-authorized after IT12
PASS @16919e4). Not mechanism discovery, not IT13. Purpose: restore
an already-recovered historical contract lost in the 0.2 port,
verify its executable semantics, and determine whether the corrected
contract is compatible with the accepted candidate. NO parameter
tuning of any kind is authorized.

## The recovered contract (frozen from source, f933c59)

Executable receipts, quoted not paraphrased:

1. DECAY LAW (event_log.py `_decay_factor`): factor =
   2^(−(t−t_f)/h) with t_f the firing time, h = decay_half_life.
   dt < 0 ⇒ 0. **h ≤ 0 ⇒ factor = 1.0 — a PERMANENT level, not
   zero.** (KA6 semantics; no reinterpretation.)
2. LEVEL, NOT ACCUMULATOR (engine.py:81, tick.py:141): the summed
   event deltas entered as a read-time projection shift
   (`project_all(civ, q, effective_shift)`) — NEVER written into
   stored forces. L(t) = A·2^(−(t−t_f)/h) as a level contribution.
3. EXPIRY (event_log.py `active_events`, threshold 0.01): an event
   leaves the active set when factor < 0.01 OR max|delta|·factor
   < 0.01. Bounded state exists → contributes → disappears.
4. TOTAL CLIP (event_log.py:198): summed level per agent/channel
   clipped to [−0.5, 0.5]. Preserved.
5. SIGN (KA7): force_deltas are signed reals applied symmetrically
   (rules already carry negative effects); magnitude decays
   symmetrically. Recovered contract IS symmetric.
6. COOLDOWN (thresholds.py `detect_transitions`): per
   (rule.name, locality) last_fired map; comparison is STRICT
   `t − last < cooldown_days` ⇒ a firing at exactly
   t = last + cooldown IS permitted. Identical strict-`<` semantics
   already live in the probe-1 repair (alive.py cascade block).
   Cooldown independently gates refiring; it does not touch decay.
7. RULES: TRANSITION_RULES today are byte-identical to f933c59
   (5 rules; effects, cooldown_days, decay_half_life all unchanged).

## Modern translation (frozen before implementation)

Per founder ruling the contribution targets the TARGET PATH:
a firing of (rule, locality) at day t_f (probe-1 repaired locality
granularity — the accepted contract) stores bounded residue state
{rule, loc_key, t_f, effects, half_life} on the chronicle
(restart-persistent, like cascade_last_fired). Each day the summed
active residue level for an agent's locality — with the legacy
±0.5 total clip and the legacy 0.01 expiry — is ADDED TO
life_force_target for agents in that locality. It replaces (under
flag) the instant permanent civ.forces write. It is NEVER
F_{t+1} = F_t + L(t). Forces then follow the level through the
standing relax law and revert as the level decays — the same level
channel class as the accepted flourishing level-map.
Recorded translation note (honest): legacy applied the shift at
question-projection time; the living world's level channel is
life_force_target. The preserved invariant is the contract's
substance: bounded decaying level, no integration into stored
force state. Flag: EARTH1_DECAY_RESIDUE=1 (composes with
EARTH1_CASCADE_COOLDOWN=1; PF arms run both).

## Known-answer battery (all required; any failure ⇒ VOID)

KA0 flag-off continuity: residue flag off ⇒ bit-identical
    IT6-ALL @8890 recorded metrics (tau 5, resid 0.074, ring1
    0.00702, sat 0.1601, sdr 0.637, α 0.5113).
KA1 exact half-life: isolated planted residue amplitude A:
    L(0)=A, L(h)=A/2, L(2h)=A/4, intermediate points = A·2^(−Δt/h),
    tolerance 1e-12 on the residue level. Plus expiry: state drops
    from the active set at the legacy 0.01 threshold.
KA2 no-accumulator (HARD GATE, instrumented receipt): one firing,
    no refire, all other writers off ⇒ exact one-step identity
    F_{t+1} − F_t = relax·(T + L(t) − F_t) every day, AND peak
    displacement bounded by the residue envelope. DISCRIMINATION
    (Standing Rule 2): a deliberately planted integrator variant
    (forces += L(t) daily) run through the SAME instrument must be
    DETECTED as violating both receipts. If the instrument cannot
    distinguish them, the KA is not evidence and the run is VOID.
KA3 cooldown semantics: still-true condition cannot refire within
    the cooldown; at exactly t = last + cooldown a refire IS
    permitted (recovered strict-`<`; no invented boundary).
KA4 locality independence: cooldown in locality X does not suppress
    a legitimate firing of the same rule in locality Y (per-key map).
KA5 restart continuity: save/load mid-decay ⇒ identical age,
    active amplitude, next-day decay, cooldown state, and future
    trajectory within deterministic tolerance.
KA6 disabled semantics: h ≤ 0 ⇒ permanent (factor 1.0) level —
    the recovered legacy meaning, reproduced exactly.
KA7 sign: −A ⇒ −L(t) with symmetric magnitude decay (recovered
    symmetric semantics).

## Duplicate-causality gate (census COMPLETE, receipts)

Traced every representation a TransitionRule firing produces:
the cascade block (alive.py step 9) writes forces ONLY. Chronicle
ingestion sites: observer.py:75 (origin "question" — the asking
mechanism), timeline.py:239 (event_from_news — external news),
branch.py:73 (scenario memory + MATERIAL channels firm_damage/cost —
the war-vs-news-about-war pair, legitimately distinct mechanisms,
and not TransitionRule-mediated). NO site ingests threshold
firings; no event impulse duplicates a cascade. VERDICT: CLEAN —
each representation corresponds to a distinct mechanism; the scored
regression may proceed. (Had this been dirty: STOP, no coefficient
halving.)

## Targeted regression (after ALL KAs pass; fresh scored seed 8905)

The one question: does restoring the correct TransitionRule
contract break the candidate architecture we are about to freeze?
Base = IT6-ALL + Chronicle(h*=10 news-class) + cooldown flag, i.e.
the accepted candidate, residue flag ON.
R1 Chronicle isolation: repeat the IT12 isolated-memory KA set with
   no TransitionRule firing ⇒ unchanged ⇒ experimentally
   Memory.half_life ≠ TransitionRule.decay_half_life as mechanisms.
R2 cascade-event stress: engineered hot locality exercises real
   firings; measure all 8 channels, saturation, diversity (sdr),
   conviction α, disagreement softening / agreement hardening,
   ring1/2/3 transmission, consensus. ALL frozen IT6 gates apply.
   Restored persistence must not reintroduce railing.
R3 repeated-trigger stress: sustained triggering condition long
   enough for ≥3 fire→decay→cooldown→refire cycles (panic_cascade:
   cooldown 14d, h 45d ⇒ ≥120d window); measure the residue-sum
   envelope and force trajectory for resonance or hidden
   accumulation — envelope must plateau (bounded superposition
   A/(1−2^(−c/h)) at most), never ratchet. A mathematically bounded
   component can still create an unhealthy equilibrium: measure it.
R4 no-trigger control: a world where no rule fires must be
   IDENTICAL between current candidate and restored-contract
   candidate (empty residue set ⇒ exact equality gate).

## Decision (mechanical; frozen)

Any required KA fails ⇒ VOID: fix the IMPLEMENTATION of the
recovered contract only; never alter the contract.
Recovered semantics cannot be established ⇒ STOP (gate already
satisfied by the f933c59 trace above).
Contract exact but regression breaks the healthy civilization ⇒
FAIL + STOP AND DIAGNOSE. Not permitted: tuning decay_half_life,
amplitudes, cooldowns, relax, social dose; reverting the contract
because the candidate looks worse.
Contract exact + regression healthy ⇒ PF-DECAY-1 PASS ⇒ FREEZE
COMPLETE CANDIDATE immediately (source commit, physics versions,
IT6-ALL config, conviction law, flourishing semantics, cooldown
semantics, restored decay_half_life semantics, Chronicle mechanism,
news-class half_life 10d, parameter provenance, event semantics,
RNG/seed contract, readout contract) ⇒ MECHANISM DISCOVERY CLOSED
⇒ the 0.8 acceptance battery begins.
