# PF-DECAY-1 — RESULT: KA PASS / REGRESSION FAIL → STOP AND DIAGNOSE

Registration eeb84fe; implementation cb6dbbc; artifacts
data/pf_decay/{ka.json, regression.json}. Per the frozen decision
rule: the contract is executable-exact, the implementation is clean,
and activating it inside the accepted candidate materially breaks
the healthy civilization. FAIL. No tuning performed; no freeze.

## 1. The contract is exact (full-N KA battery: ALL PASS)

UNIT law error literally 0.0; expiry boundary exact (active day 149,
gone day 150). KA0: it6-ALL @8890 through the new code path
reproduces every recorded panel/tau/transmission value. KA2: the
level obeys its exact relax recursion at 2.6e-16 while the planted
integrator violates it at 9.6e-2 (14 orders) and blows the envelope
(0.56 vs 0.10) — the instrument discriminates the true law from the
bug class. KA3 fire days {0, 14, 28} exactly (strict-<). KA4
locality independence exact. KA5 bitwise restart through the
canonical serializer. KA6 permanent level holds (0.09916 ± 3e-4).
R4c (rules-off pair): residue flag on vs off IDENTICAL on every
recorded metric — the implementation adds nothing on its own.

## 2. The discovery that changes the picture: natural cascade
   activity is ubiquitous

The accepted candidate, seed 8905, NO engineered events, 120 days:
1,570 (rule, locality) pairs fired; 6,422 residues active at d120,
still growing at d210 (8,661). Every prior iteration ran with this
cascade activity present but uninstrumented — under the incumbent
instant-write semantics each firing was a one-shot force blip that
relax erased in days, so it never showed in any gate. The restored
contract converts that same firing stream into thousands of
superposed multi-week target shifts.

## 3. Attribution (the decisive table: end-of-run sat_max)

  R4c  no cascades at all            0.144   healthy
  R4_off incumbent instant writes    0.191   (transient 0.228-0.230
                                              at d100-110 — see §6)
  R4_on  restored contract           0.388   railing, rising
  R3_res restored, 210d              0.502   railing, still rising

Same world, same seed, same firing stream. The only difference
between 0.19 and 0.39 is what a firing MEANS.

## 4. Diagnosis — why a bounded component sickens the system

(a) TIMESCALE SUPERPOSITION: cooldowns (14-60d) << decay half-lives
(30-90d), so a still-true condition stacks residues to the
superposition bound A/(1 - 2^(-cooldown/h)) — for panic_cascade
5.2 x 0.10 = 0.52, at the legacy clip. Bounded, as designed:
measured envelope max 0.46 < 0.526 analytic (envelope_bounded PASS).
(b) SELF-EXCITATION — the actual killer: the residue raises the
FEAR target; relax carries it into civ.forces; the threshold
detector reads civ.forces; FEAR > 0.5 is panic's own trigger. The
effect of the event re-arms the event. pf_big's record shows the
loop: natural fires at d1/21/41 before any clamp, then near-
continuous multi-rule activity (fear-adjacent rules chain in as
fear crosses 0.7). Negative-effect rules (identity -0.15,
collective -0.12, temperament -0.08) superpose toward the LOW rail
— the probe-1 grinder pattern reborn in level form, now sustained
honestly by the contract instead of by a bug.
(c) THE STRUCTURAL FACT (the contradiction to rule on): in f933c59
the decaying shift was applied at QUESTION-PROJECTION time only —
`detect_transitions` read raw `civ.forces`, which events never
touched. The legacy contract was OPEN-LOOP BY CONSTRUCTION: cascade
effects were invisible to the threshold detector, and self-
excitation was impossible. The frozen modern translation (target
path, per ruling) is CLOSED-LOOP: the level feeds relax, relax
feeds stored forces, stored forces feed the detector. The recovered
LAW survives translation; the recovered LOOP TOPOLOGY does not.
That — not the decay mathematics — is what breaks.

## 5. R1 and R2 instrument notes (honest)

R1 (IT12 arms rerun, residue on) is NOT unchanged: COMPOSITE d30
0.10646 vs 0.09616 recorded (+10%), INTRINSIC 0.01172 vs 0.01196,
KA1_delete 0.00026 vs 0.00027. The registered premise ("no
TransitionRule firing") was false — natural firings run through
both arms. The paired-control design cancels most of it (the small
arms barely move); the Chronicle-vs-residue mechanism separation
still stands on KA1_delete and the R4c identity. R2's single-
engineered-firing instrument was confounded the same way: pf_big
was ALREADY firing panic naturally (d1/21/41), so "one clean
firing" and its analytic decay ratio never existed. Multi-rule
same-locality fires on consecutive days (60/61 etc.) are different
RULES, not cooldown violations (KA3 holds per-rule).

## 6. Candidate-margin disclosure (independent of this contract)

The incumbent instant-write candidate itself transiently breached
the 20% sat gate at seed 8905 (0.228 d100, 0.230 d110, back to
0.191 by d120) — natural cascade activity pushes the health margin
thinner than the 8890 record (0.1601) suggested. A butterfly pair
(R2_inst, which differs only by a 3-day clamp at d60) stayed at
0.161. This seed-sensitivity of the frozen gate near its boundary
is reported as its own fact for the acceptance program regardless
of what happens with decay_half_life.

## 7. Status per the frozen decision rule

FAIL -> STOP AND DIAGNOSE (delivered above). Not performed and not
proposed: tuning h, amplitudes, cooldowns, relax, or dose;
reverting the contract because the candidate looks worse. The
contradiction, stated precisely: the recovered decaying-level LAW
is exact and compatible; the recovered OPEN-LOOP application point
(readout-only, invisible to the detector) and the ruling's frozen
target-path translation are not the same mechanism, and the
closed-loop version self-excites under the candidate's natural
firing rate. Which loop topology Earth-1 should have is a physics
decision, not an implementation detail — awaiting founder ruling.
The freeze does NOT proceed.
