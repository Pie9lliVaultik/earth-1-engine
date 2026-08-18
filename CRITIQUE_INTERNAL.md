# Internal Critique — 2026-08-18

Written by the system that wrote the code, on request, to be at least as
hard as the eleven external reviews. Items 1–4 are things NO external
reviewer has found yet. Ranked by how much damage each would do in a
referee's hands.

## 1. THE GROUND-TRUTH PROVENANCE HOLE (worst issue in the program)

`earth1/wvs_paired.py` — the W6 and W7 per-country aggregates that every
temporal verdict stands on — were **authored from LLM knowledge**, with a
"verify against the official database" note that nobody has ever acted
on. This is not just the W5 caveat flagged yesterday: it is the ENTIRE
temporal evaluation base. Consequences:

- The grid verdict (B > A-0 > C), the A/B inheritance tie, run #10's
  fail, and the A6 negative all score against numbers I generated.
- An LLM authoring "observed deltas" from training-data knowledge
  plausibly encodes smoothed, direction-correct, magnitude-blurred
  versions of reality. Signals can be created (my hindsight of
  liberalization trends) or destroyed (blurring real heterogeneity).
- D6's 0.48 trend correlation is undecidable between "real persistence"
  and "one model's hindsight agreeing with itself."

By contrast GOQA ground truth is a real published dataset — the
cross-sectional results (10.24/10.57, ablation, leakage) do NOT have
this problem. The split is exactly: **cross-sectional claims stand on
real data; temporal claims stand on my memory.**

FIX (mechanical, high priority): transcribe official WVS
W5/W6/W7 aggregates for the 15 questions from worldvaluessurvey.org
(~1–2h, ideally with Pietro's eyes on the numbers), diff against the
authored values, publish the diff, and re-run every frozen temporal
pipeline. Every diff line is honest; every unrun re-check is a landmine.

## 2. Same-author closure in the event leg

The event leg's 0.97 pass has BOTH sides of its dot-product authored by
the same model family: the response profiles (blind, but mine) AND the
perceived shocks (mine) AND the measured pre/post case deltas
(compiled by me from knowledge). Effective n≈7–8 was disclosed; the
same-author closure was not stated this bluntly: the validated
"response law" is partially a self-consistency result. FIX: real survey
time-series for the six cases transcribed from primary sources, and
future perception through a second model family as a control arm.

## 3. The embedded data layers are unverified literals

`census.py` (1,776 lines) and `culture.py` carry UN/WB/Hofstede/
Inglehart values as authored literals. The ablation table says census +
Hofstede carry the margin — but nobody has diffed those literals
against the actual published tables. A single systematic transcription
bias propagates into every number we publish. FIX: a provenance script
that fetches the primary sources and diffs (WDI fetch already exists as
a pattern), run once, diff committed.

## 4. No zero-shot capability — a product-claim limit

The engine predicts a question's country pattern ONLY after per-question
ridge calibration on that question's own country targets. Given a NEW
question with no survey data, the engine has its 8-force projection but
no validated weights — the honest zero-shot path (corpus retrieval +
blind profile) has never been benchmarked against GOQA-style holdout.
"194 countries × any question" marketing would not survive this fact.
FIX: register a zero-shot benchmark (calibrate on 30 questions, predict
the other 10's country patterns via profile similarity — no target
leakage) before any product claim.

## 5. Invariant-free tests (the drift lesson, generalized)

910 tests passed while two mechanisms drifted state at rates that
compound to absurdity within decades (cohort −0.003/yr; feedback
FEAR +0.16/yr). Tests assert local mechanics, never conservation laws.
FIX: a `test_invariants.py` battery — long-horizon rate bounds per
mechanism-in-isolation, distribution-moment stability, graph degree
bounds — the kind of test that catches the NEXT slow leak.

## 6. Single-seed numbers everywhere except the grid

The ladder statement (10.24 → 10.03 → 10.19 "flat within noise") is
three single-seed points with the noise never measured. Rungs now cost
18 minutes; there is no excuse — 3 seeds × 3 scales gives error bars on
the flagship table. Same for RESPONSE_GAIN (LOO range 2.0–3.1, ±50%
parameter uncertainty never propagated into event predictions).

## 7. Operational honesty

- Backups exist and are verified PRESENT; a restore has never been
  rehearsed. An untested backup is a hope, not a backup.
- Supervisor state/journals live only on each machine (not backed up).
- Secrets in plaintext .env on two servers; RunPod key still unrotated.
- Nothing alerts Pietro directly if I'm gone and a machine dies.

## 8. Architecture strata

Four generations of code coexist: legacy loop.py registry, experimental
force-dynamics path, dormant cube, legacy-tagged multiverse surfaces,
superposition. Every stratum is tagged honestly, but a new engineer
reads five architectures to find the one that runs. Post-freeze, a
Build-32 "one stratum" consolidation is owed.

## 9. The scientific bottom line (unchanged by any of this)

Validated, on real or best-available data: cross-sectional structure
(leakage-clean 10.57, attributed), demographic composition as the only
temporal signal, aggregate event response (with §2's caveat), and a
precise map of what does NOT work. That is the asset. Items 1–3 above
determine whether the temporal half of the map survives contact with
primary sources. Until then, every temporal claim should carry the
provenance asterisk.

## Recommendation on external advisors

Keep them. The track record is complementary, not competitive: externals
found the benchmark bypass, the Inglehart leakage risk, and the cohort
inheritance mechanism (which nine of my audit rounds missed); I found
their factual errors (the 1M number, receiver.py) and everything in
this document. Send them STATUS.md, experiments/predictive_value/
REPORT.md, and this file as the brief — an advisor who reads all three
and finds a #0 I missed is worth their fee.
