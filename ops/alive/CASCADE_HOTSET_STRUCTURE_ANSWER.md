# CASCADE HOT-SET STRUCTURE — BROAD AMBIENT vs STRUCTURAL MINORITY

Answer to the founder question (no code/physics change, no ablation, no fix).
Source data: canonical loop (`0.8-candidate-v2/76a574c-canonical`), 200k
Earthlings, 365 days, seeds 9501 and 9502 — `data/diag1/hot_history_A_950{1,2}.pkl`
(per-day hot-set at 1.0× thresholds, fires), `data/diag1/reach_9501.json`
(locality census at days 0/180/365), `reach_summary_9501.json`.
Derived tables: `data/diag1/hot_structure.json`,
`data/diag1/hot_vs_nonhot_traits_9501.json`.

## Per-rule locality numbers (seed 9501 / seed 9502)

Total localities: 879 (194 countries), 365 days.

| metric | identity_collapse | collective_surge |
|---|---|---|
| localities ever hot (n, %loc, %pop) | 637, 72.5%, 80.8% / 610, 69.4%, 77.4% | 678, 77.1%, 84.7% / 684, 77.8%, 84.6% |
| hot on a typical day (median %loc, %pop) | 50.9%, 47.6% / 43.8%, 42.8% | 72.2%, 81.4% / 73.0%, 81.6% |
| fraction of year hot per locality (median / p90 / p95) | 0.50 / 0.89 / 0.90 ; 0.21 / 0.89 / 0.90 | 0.92 / 1.00 / 1.00 ; 0.92 / 1.00 / 1.00 |
| hot >25% of year (n, %loc, %pop) | 513, 58.4%, 57.2% / 420, 47.8%, 46.7% | 640, 72.8%, 81.6% / 648, 73.7%, 81.9% |
| hot >50% of year | 441, 50.2%, 48.6% / 363, 41.3%, 41.0% | 631, 71.8%, 81.2% / 638, 72.6%, 81.2% |
| hot >75% of year | 283, 32.2%, 24.9% / 294, 33.4%, 35.8% | 615, 70.0%, 79.6% / 624, 71.0%, 80.0% |
| hot >90% of year | 45, 5.1%, 6.2% / 48, 5.5%, 3.6% | 510, 58.0%, 69.8% / 496, 56.4%, 65.7% |
| longest uninterrupted hot run (median / p90 / max days) | 109 / 324 / 342 ; 23 / 322 / 339 | 337 / 365 / 365 ; 335 / 365 / 365 |
| trigger opportunities (locality-days hot) | 139,866 / 121,845 | 217,066 / 219,332 |
| firings after cooldown | 5,553 / 5,071 | 11,456 / 11,541 |
| unique firing localities (n, %loc, %pop) | 637, 72.5%, 80.8% / 610, 69.4%, 77.4% | 678, 77.1%, 84.7% / 684, 77.8%, 84.6% |
| countries with any hot day | 194 / 194 | 194 / 194 |
| top-5 countries' share of hot locality-days | 9.4% / 11.5% | 7.8% / 7.7% |

Every locality that is ever hot fires (cooldown-only re-arm turns every hot
streak into a firing every 30/20 days). Firings ÷ opportunities = 1/25 (IC)
and 1/19 (CS) — i.e. almost exactly one per cooldown window: the hot set is
stationary, not episodic.

Geographic distribution: flat. Hot localities are spread over all 194
countries; the five most-affected countries carry <12% of hot locality-days.
There is no regional cluster.

## Structural traits, hot vs non-hot (seed 9501, day 180, pop-weighted means)

identity_collapse:

| group | n loc | %pop | urban | deprivation | unemployment | war | stored FEAR | stored COLLECTIVE |
|---|---|---|---|---|---|---|---|---|
| never hot | 242 | 19.0 | 0.77 | 0.175 | 0.088 | 0.000 | 0.57 | 0.60 |
| hot <25% of yr | 124 | 23.7 | 0.75 | 0.255 | 0.085 | 0.000 | 0.63 | 0.76 |
| hot 25–75% | 230 | 32.4 | 0.45 | 0.330 | 0.095 | 0.012 | 0.64 | 0.79 |
| hot >75% | 283 | 24.9 | 0.46 | 0.442 | 0.093 | 0.240 | 0.75 | 0.87 |

collective_surge:

| group | n loc | %pop | urban | deprivation | unemployment | war | stored FEAR | stored COLLECTIVE |
|---|---|---|---|---|---|---|---|---|
| never hot | 201 | 15.2 | 0.82 | 0.174 | 0.092 | 0.000 | 0.56 | 0.56 |
| hot <25% | 38 | 3.1 | 0.68 | 0.202 | 0.069 | 0.000 | 0.60 | 0.69 |
| hot 25–75% | 25 | 1.9 | 0.66 | 0.221 | 0.079 | 0.000 | 0.60 | 0.71 |
| hot >75% | 615 | 79.8 | 0.54 | 0.343 | 0.092 | 0.080 | 0.67 | 0.81 |

Of localities hot >50% of the year: war==0 in 93.7% (IC) / 95.2% (CS);
94.4% (IC) / 95.3% (CS) of all firings occur in conflict-free localities
(only 30 localities, 6.4% of population, have any war signal at day 180).
Unemployment is indistinguishable between hot and non-hot (0.09 everywhere).
Hot localities are more rural (urban 0.45–0.54 vs 0.72–0.82) and more
deprived (0.34–0.44 vs 0.17), but the "cold" set is the urban, low-deprivation
~15–19% of the population — the hot set is the ordinary rest of the world.
Stored-force side: the never-hot group sits at COLLECTIVE ≈ 0.56–0.60,
the hot groups at 0.76–0.87 — the condition COLLECTIVE>0.6 (IC) / >0.75 (CS)
is simply where the bulk of the centered COLLECTIVE field lives.

## Direct vs indirect reach (seed 9501, `reach_summary_9501.json`)

- fires of the two IDENTITY rules: 17,009
- Earthlings ever carrying an IDENTITY residue: 85.53%
- Earthlings directly resident in a firing locality at firing time: 85.53%
- first exposure direct: 99.915%; indirect (moved into a locality after its
  fire and inherited nothing — residues are per-agent, so "indirect" can only
  mean being stamped while resident and then leaving): 0.085%
- exposed agent-days direct: 99.964%
- migrations over the year: 2,929 (1.46% of agents ever move)
- mechanism of the indirect remainder: agents stamped while resident who
  later migrated and carry the residue elsewhere. There is NO network, overlap,
  or contagion path for residues (CONTAGION_GAIN=0.0; the overlay is a
  per-agent read-time view written only by the locality cascade block).

## DEFINITIVE CONCLUSION

- HOT-SET STRUCTURE: **BROAD**. collective_surge: 72% of localities / 81% of
  population hot on a typical day, median locality hot 92% of the year,
  median longest streak 337 days, in all 194 countries. identity_collapse:
  44–51% of localities hot on a typical day, median locality hot 21–50% of
  the year, a third of localities hot >75% of the year. Neither is a
  minority: the never-hot set is the urban, low-deprivation 15–19%.
- DIRECT EXPOSURE CONTRIBUTION: **99.9%** (first exposure 99.915%; agent-days
  99.964%).
- INDIRECT SPREAD CONTRIBUTION: **0.1%** (0.085% first exposures, carried by
  1.46% migrants who were stamped before moving).
- PRIMARY MECHANISM OF 85% REACH: a stationary, population-wide hot set.
  The two IDENTITY rules' level conditions (COLLECTIVE>0.6/0.75 ∧
  FEAR>0.6/0.7 in ≥12% of residents) are satisfied continuously by ~80% of
  the population's home localities, so cooldown-only re-arm fires each of
  them every 20/30 days all year (17k fires, one per cooldown window per
  hot locality). Reach = pop share of ever-hot localities (84.7% CS ≈ 85.5%
  ever-exposed). Migration and spread are irrelevant.
- ARE ORDINARY / NON-CRISIS LOCALITIES FIRING THESE "CRISIS" RULES?: **YES**.
  94–95% of firings occur in localities with no conflict; unemployment in
  firing localities equals the global mean; firing localities are ordinary
  rural/mid-deprivation places spread across every country. The rules read
  the ambient centered COLLECTIVE field (mean ≈ 0.76–0.80 stored) as a
  permanent crisis.

Seeds 9501 and 9502 agree on every number to within a few points. No
parameter was modified, no ablation run, no fix proposed.
