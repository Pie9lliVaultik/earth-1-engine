# COLLECTIVE-GEO-1 — CENTERED-DEVIATION TARGET LAW (pre-registered)

Founder-authorized single candidate; NO coefficient search. Only
COLLECTIVE target construction changes; everything else identical to
1ae8740 (relax, dose, conviction, propagation, Chronicle, cascade
law, flourishing state, genesis, rail threshold, Stage A gates all
untouched). Model principle under test: BASELINE ENCODES NORMAL
STATE; MODIFIERS ENCODE DEPARTURES FROM NORMAL STATE.

## The candidate law (flag EARTH1_COLLECTIVE_CENTERED=1)

Incumbent:  t1 = clip(B + 0.40·ds)
            t2 = clip(t1·(1−0.6·addiction) + 0.25·P − 0.20·S)
            T  = clip(t2 + 0.20·G)          [flourishing map]
Centered:   t1 = clip(B + 0.40·(ds − REF_DS))
            t2 = clip(t1·(1−0.6·addiction)
                      + 0.25·(P − REF_POL) − 0.20·(S − REF_SN))
            T  = clip(t2 + 0.20·(G − REF_BEL))
ds = deprivation·shared; P = political; S = social_need;
G = belonging. The multiplicative addiction term is retained
unchanged: it is ALREADY deviation-form (neutral person addiction=0
⇒ factor 1; reference-pop mean 0.0136). Slopes 0.40/0.25/0.20/0.20
UNCHANGED and remain tagged AUTHORED / REQUIRES PARAMETER
PROVENANCE. Reference centers are FIXED CONSTANTS — never computed
from the running population (no dynamic centering).

## Frozen reference constants (provenance)

Registered reference population: birth_world(200000, seed=424242),
day 0 — the calibrated genesis state; seed fresh, independent of
9001–9003/8905/all scored seeds; measured once, frozen here:
    REF_DS  = 0.0      (deprivation is zero at calibration state:
                        lived shared hardship is genuinely a
                        deviation; term numerically unchanged)
    REF_POL = 0.3998   (the authored Beta(2,3) engagement mean —
                        normal engagement is no longer a daily
                        positive shock)
    REF_SN  = 0.2855
    REF_BEL = 0.6416
Registered analytic EXPECTATION (not a gate): with equilibrium
lived-state means from GEO-0 (ds .081, P .40, S .075, G .73), the
centered equilibrium target mean ≈ 0.73 — pole-parking removed
while lived deviations (hardship up, social_need down, belonging
up) legitimately keep the lived world above the 0.65 birth base.

## Known answers (any required failure ⇒ VOID)

KA0 incumbent continuity: flag off ⇒ bit-identical to 1ae8740
    behavior (it6-ALL @8890 recorded metrics exact).
KA1 neutral-state preservation (core invariant): construct agents
    at exactly ds=REF_DS, P=REF_POL, S=REF_SN, G=REF_BEL,
    addiction=0 ⇒ T = B to numerical precision (away from clips).
KA2 monotonicity: raising each of P, G, ds above reference raises
    T; raising S lowers T (signs unchanged by centering).
KA3 slope preservation, per modifier: T(ref+δ) − T(ref) equals
    exactly 0.25δ (P), 0.20δ (G), −0.20δ (S), 0.40δ (ds), away
    from clips, to 1e-12.
KA4 no dynamic centering: altering every OTHER agent's state leaves
    a fixed agent's T unchanged except through its own ds
    neighborhood term (the one legitimately relational input);
    P/S/G centering constants provably constant.
KA5 other forces untouched: the seven non-COLLECTIVE target rows
    bit-identical under identical inputs, flag on vs off.
KA6 no new rail/clamp machinery: diff of the change is inspected —
    no new clip, remap, or special-case beyond the centered terms.

## GEO-1A — known-failure development controls (never validation)

Seeds 9001/9002/9003 (+8905 optional), 365d, N=200k, exact Stage A
observables. Required (mechanism-directed, not perfection):
COLLECTIVE target no longer structurally parked at the pole
(frac(T>0.95) collapses from 41.8%; stored COLLECTIVE sat no longer
the year-scale breach driver); no seven-force regressions; no
conviction/diversity regressions; no new clamp dependence. Mean
remaining ≈0.86 or a heavily railed target ⇒ GEO-1 FAIL; no
reference-center fiddling.

## Full regression (only if GEO-1A supports the mechanism)

IT6-ALL social equilibrium (recorded-gate class); softening/
hardening; SDR/diversity; transmission rings; conviction interior;
IT12 Chronicle persistence arms; PF-DECAY open-loop KA battery;
complete eight-force census. COLLECTIVE is socially connected —
second-order consequences are measured, not assumed.

## Parameter registry entries (standing)

    COLLECTIVE political slope 0.25: authored / experimental
    COLLECTIVE belonging slope 0.20: authored / experimental
    COLLECTIVE ds slope 0.40 / social_need slope 0.20: authored
    COLLECTIVE reference centers: reference-derived (this doc)
    COLLECTIVE baseline/genesis: empirical

## Decision

Any KA fails ⇒ VOID (fix implementation only). GEO-1A misses the
mechanism ⇒ GEO-1 FAIL ⇒ STOP (no center/slope adjustment).
KAs pass + GEO-1A attacks the diagnosed pathology + regressions
healthy ⇒ GEO-1 PASS ⇒ NEW frozen candidate hash (1ae8740 remains
the historical Stage-A-failing candidate) ⇒ Stage A v2 on FRESH
seeds under the unchanged 334abf5 gates ⇒ Stage B (unchanged)
behind it with a version-continuity declaration.
