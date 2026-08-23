# CASCADE_IDENTITY_DIAGNOSTIC_1 — REPORT (steps 1–3 of the Bible miss protocol)

Canonical executable 424c5b2 lineage (physics identical to 02a9366;
instruments only). Registration: CASCADE_IDENTITY_DIAGNOSTIC_1.md.
Sections 1, 4, 5 are filled from measurement (see bottom); sections
2–3 and 6 are from source. No physics touched; no repair proposed.

## 2. CAUSAL TRACE — the exact executable route

    stored state ──▶ trigger ──▶ cascade creation ──▶ residue ──▶ decay/superposition ──▶ effective IDENTITY

**Trigger substrate.** `w.civ.forces` — the STORED field, never the
overlay (`alive.py:372-384`, `_det_forces = civ.forces`; the
contaminated-detector twin exists only behind `EARTH1_TEST_*`).

**Locality.** `loc = country·1000 + region·2 + urban` (`alive.py:340-342`):
country × genesis region × urban flag. CORRECTION (38ef1f1 follow-up):
the "≈2,300" first written here was an unmeasured estimate; the measured
count is 879 occupied localities at 200k (194 countries × 1–7 observed
regions × 2 = 886 theoretical cells), summing to all 200,000 agents every
day; 869 are cascade-eligible (pop ≥ 10) and hold 199,955 agents.

**Trigger equation** (`alive.py:378-387`), evaluated EVERY DAY:
    met_i = ∧_c [ F_i[force_c] (op_c) thresh_c ]        per agent
    frac_L = (1/pop_L) Σ_{i∈L} met_i
    hot_L  = (frac_L ≥ critical_fraction=0.12) ∧ (pop_L ≥ 10)
Units: forces in [0,1]; thresholds absolute levels; fraction of the
locality's residents (alive or not — `pop_l` counts all slots).
**It is a LEVEL trigger**: no derivative, no transition, no hysteresis,
no reference to the locality's own history or normal state.

**Rules** (`thresholds.py:29-68`, unchanged since f933c59):
| rule | conditions (stored) | effects | cooldown | half-life |
|---|---|---|---|---|
| identity_collapse | FEAR > 0.7 ∧ COLLECTIVE > 0.6 | IDENTITY −0.15 | 30 d | 60 d |
| collective_surge  | COLLECTIVE > 0.75 ∧ FEAR > 0.6 | IDENTITY −0.10, TEMPERAMENT −0.08 | 20 d | 30 d |
| panic_cascade     | ECONOMICS < 0.3 ∧ FEAR > 0.5  | FEAR +0.10, DESIRE −0.08 | 14 d | 45 d |
| polarization_lock | IDENTITY > 0.8 ∧ CULTURE > 0.7 | COLLECTIVE −0.12 | 60 d | 90 d |
| economic_boom     | ECONOMICS > 0.8 ∧ FEAR < 0.3  | DESIRE +0.12, FEAR −0.05 | 30 d | 60 d |

**Cooldown / re-arm / reset** (`alive.py:388-397`): per (rule, locality)
`last_fired`; a hot locality fires iff `last is None or
(w.day − last) < cooldown_days` is FALSE (strict `<` ⇒ eligible at
exactly `last + cooldown`). **The ONLY re-arm condition is elapsed
time.** There is no reset: the condition is never required to become
false between firings. ⇒ **An unchanged underlying condition creates
a new residue after every cooldown, indefinitely.**

**Cascade creation → residue** (`alive.py:399-412`): each firing
appends `{rule, loc, day=w.day, effects(8-vector), h}` to
`chronicle.cascade_residues`. Nothing is written to stored forces
(open-loop, PF-DECAY-2).

**Decay law** (`cascade_residue_levels`, `alive.py:106-124`):
    level(t) = effects · 2^(−(t − t_f)/h)    (h ≤ 0 ⇒ permanent)
    active iff 2^(−Δt/h) ≥ 0.01 ∧ max|effects|·2^(−Δt/h) ≥ 0.01
For identity_collapse (|A|=0.15, h=60): expiry when factor < 0.0667
⇒ Δt > 60·log2(15) ≈ 234 d. collective_surge (0.10, h=30): factor <
0.1 ⇒ Δt > 30·log2(10) ≈ 100 d.

**Superposition** (`effective_forces`, `alive.py:146-159`): for each
agent, shift = Σ over ALL active residues whose `loc` equals the
agent's CURRENT locality of `effects·factor` — linear stacking across
rules and across repeated firings of the same rule; then total clip to
[−0.5, +0.5]; then F_eff = clip(F_stored + shift, 0, 1).
**Overlap across rules:** identity_collapse and collective_surge both
write IDENTITY negatively and share FEAR/COLLECTIVE-high conditions, so
the same hot localities typically carry both.
**Overlap across localities:** none in the overlay itself — the shift is
locality-bound; an agent is exposed only through its own locality
(migration moves agents between localities).

**Steady-state superposition, analytic** (condition permanently hot):
firings every `c` days, each decaying with half-life `h`, expiring at
factor f_min: simultaneous residues ≈ ⌈(h·log2(1/f_min))/c⌉ and summed
level ≈ A·Σ_k 2^(−kc/h) = A/(1 − 2^(−c/h)):
    identity_collapse: 234/30 ≈ 8 residues, level ≈ 0.15/(1−2^(−0.5)) = 0.512
    collective_surge:  100/20 ≈ 5 residues, level ≈ 0.10/(1−2^(−0.667)) = 0.270
    combined ≈ 13 simultaneous residues; raw level ≈ −0.78 → clipped −0.50.
These are the Stage C observations (12–13 residues/person; |C| p95
0.43 with clip engaged; |C|>0.20 for ¾ of people) — they follow from
the equations alone, GIVEN a permanently hot condition. Whether the
condition IS permanently hot, and for whom, is the measured question
(§1/§4 below).

## 6. PROVENANCE INVENTORY (no replacement research)

| constant | value | status | pointer |
|---|---|---|---|
| rule thresholds (0.7, 0.6, 0.75, 0.6, 0.3, 0.5, 0.8, 0.7, 0.8, 0.3) | as above | **AUTHORED** (f933c59, "Builds 16-25: Emergence architecture"; never re-derived after genesis/GEO-1 geometry changes) | Bible III.6: "threshold effect deltas" listed UNSOURCED |
| effects/amplitudes (−0.15, −0.10/−0.08, +0.10/−0.08, −0.12, +0.12/−0.05) | as above | **AUTHORED** (f933c59) | Bible III.6 UNSOURCED |
| cooldown_days (30, 20, 14, 60, 30) | as above | **AUTHORED** (f933c59) | — |
| decay_half_life (60, 30, 45, 90, 60) | as above | **AUTHORED** (f933c59; contract recovered exactly, PF-DECAY trace) | PF_DECAY_1.md |
| critical_fraction = 0.12 (locality hot fraction) | 0.12 | **AUTHORED** (daemon STEP dict; declared canonical at 0.2, ca95903) | CANONICAL_DAY; NOT the Centola/Granovetter 25% committed-minority figure (SOURCED, Bible III.6) — different construct |
| pop_L ≥ 10 locality floor | 10 | AUTHORED | alive.py:387 |
| expiry threshold 0.01; total clip ±0.5 | — | **DERIVED** from f933c59 contract (recovered, KA-exact) | PF_DECAY_1.md |
| locality key (country·1000+region·2+urban) | — | DERIVED (genesis regions) | genesis/regions |
| day-seeded encounter RNG etc. | — | not involved (open-loop) | — |

Summary: every constant that determines whether and how often a
locality fires, and how hard, is AUTHORED and listed UNSOURCED by the
Bible's own parameter census; the decay/expiry/clip contract is the
only DERIVED piece (recovered historical semantics).
