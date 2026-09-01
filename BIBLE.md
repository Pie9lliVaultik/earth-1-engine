# EARTH-1 — THE BIBLE

### The canonical technical assessment, research foundation, benchmark specification, and road to v1

**Version 4.1 — 2026-08-19 (three-auditor reconciliation)**
**Status: PRE-BENCHMARK. No validated predictive claim currently exists.**
**Method: three parallel deep audits of all 92 modules, ten literature threads, direct measurement on both machines — now reconciled with two independent external reviews (the v4 Review Addendum and the v3 V1-Readiness assessment). Every load-bearing claim carries either a measurement date or a citation; the central findings now carry three-auditor agreement.**

---

## VERSION 4.1 — WHAT THE TWO EXTERNAL REVIEWS ADDED

Two independent documents reviewed this program against the same code.
Neither knew of the other. Where all three assessments agree, the claim
is now triple-confirmed; where either found something v4.0 missed, it
is folded in below and the phases amended. The most important additions:

### New P0 correctness findings (external, now INDEPENDENTLY VERIFIED here)

| finding | verification (2026-08-19, this machine) | consequence |
|---|---|---|
| **Nobody ages in the living world.** `live_one_day` never advances `civ.age`; `generational.py` exists and is never called. | `max abs(age change) = 0.0` after 30 simulated days, measured | Every age-dependent hazard — cancer t⁵, falls ×2/decade, road-death peak at 24, fertility windows — ran on a frozen age structure through **every long run ever performed** (365-day backtests, the 750-day archived world, 15-year calibration runs). All long-horizon demographic results carry this caveat until re-run. |
| **Reborn slots inherit the dead person's social graph.** | Adjacency row bit-identical through death→rebirth (degree 19 preserved), measured. Field resets are present in current HEAD (partial fix already landed); the tie inheritance is live. | Newborns are born with a dead stranger's friends, colleagues and household. Violates the fabric's whole design. |
| **Presence and mobility are not persisted** by the live daemon or the timeline; RNG state not serialized. | Confirmed by inspection of `world_alive.save_world` and `timeline._save` field lists (same defect class as the climate/flourishing persistence bug fixed 08-19). | Every restart silently drops co-presence physics and mobility; restore→branch loses crowds, riots, flights, road deaths. |
| G5 unit mismatch: logit-space baseline built from probability-space WVS means. | Not re-verified here; old-substrate only. | Old temporal grid results additionally contaminated; do not cite. |

### The external smoke-check discipline is adopted
The V1-Readiness review demonstrated its findings with **executed
smoke checks at tiny population** (semantics, not performance). That
practice — a semantic invariant suite (ages advance; reborn slots are
virgin; save→restore→branch round-trips every subsystem including a
state-hash; RNG continuation) — becomes the **release gate** for
Phase 0 and permanent CI. A feature is not "built" until its state
survives save/restore and a branch from a restored world retains it.

### Evidence vocabulary adopted (from V1-Readiness)
**BUILT** (code exists) → **WIRED** (on the canonical path) → **LIVE**
(deployed, always-on) → **VALIDATED** (externally graded under a
pre-declared protocol). These labels replace looser language
everywhere; a module may hold any prefix of this chain and the
distinctions are non-negotiable.

### Scope ruling refined: multi-fidelity co-simulation
The V1-Readiness review improves Part X's doctrine, and its version is
adopted: **no physical layer is excluded by doctrine; every layer
exists in the ontology at the lowest resolution that transmits causal
consequences to the civilisation, with higher-fidelity solvers invoked
only when a scenario makes that layer decision-relevant** (the
Earth-system digital-twin pattern). The interaction-variance criterion
survives as the *every-tick* rule; scenario-activated layers (nuclear/
radiological, solar-storm/asteroid, EMP/grid, pathogen dynamics) are
BUILT-on-demand rather than OUT. Unknown physics is handled by
branching over competing hypotheses and propagating the epistemic
uncertainty — never by "modelling the unknown as known."

### From the Review Addendum — six deltas, all adopted
1. **R16 (HIGH): temporal ground truth is authored, not transcribed.**
   `wvs_paired.py` W6/W7 aggregates were compiled from published
   summaries with an un-acted "verify against official WVS" note
   (confirmed at `wvs_paired.py:9-12`); authored-truth error was
   previously measured at 6.8pp against a ~3pp signal. Same class:
   `census.py` / `culture.py` literals. **Fix is founder-gated and
   long-lead (official WVS microdata registration) → starts in
   parallel with Phase 0, today.** Until transcribed truth lands, no
   temporal/wave-paired claim may be published.
2. **Benchmark A grounding reworded** (tiers unchanged): the MRP 2–5pp
   band is *domestic* (US states, individual covariates). No published
   cross-national 66-country band exists — which is why even the
   ACCEPT tier, with baselines and provenance attached, is itself a
   contribution. This wording forestalls the transfer-across-problems
   objection.
3. **Benchmark C timestamp discipline:** engine forecast hash-committed
   at time T; market price snapshot **at the same T**; both scored
   against resolution; the T-to-resolution horizon distribution
   reported. Abstention restored **pre-hoc**: the anatomy-gated scope
   rule is committed before the ≥50-contract basket; no filtering
   within scope afterwards.
4. **The founder-gated parallel track** (independent of all wiring,
   on later phases' critical path): WVS microdata registration (gates
   R16 — the most valuable founder-hour available); FRED + ACLED keys;
   RunPod key rotation (open exposure); one **backup restore
   rehearsal** (the timer fires; an unrestored backup is a hope, and
   the script is sized for 900 MB against an 18 GB world); the
   destitution-bar ruling (34.5% measured vs a 25% bar written with
   rich-world intuition — pre-registered FAIL honoured; revising the
   bar is a founder decision, not a quiet adjustment).
5. **Standing Rule 10 — result provenance stamping:** every result
   JSON stamps hostname, git commit, seed, and wall-clock at write
   time. "Which machine produced this file" becomes greppable, not
   arguable.
6. **Two phrasing/method rules made explicit:** (a) all external
   material says **finite-size (FSLE) exponent**, never bare
   "Lyapunov" — the infinitesimal exponent measured ≈ 0 and one
   conflated sentence in a deck is a free referee hit; (b) the VII.3
   loop gains the **iterate/confirm split** — iterate freely on
   training folds, confirm once on untouched holdout, targets never
   move after results (this program has been burned twice by exactly
   this).

### Evidence-ledger corrections accepted from V1-Readiness
MrsP (~8.56pp) is **stronger** than the old engine (10.59pp) at
national means — population-average fidelity is *not* the living
world's strongest case, distributional/counterfactual capability is.
The current prediction-market record is small and **much worse than
the market**; the market is a baseline to beat prospectively, not to
explain away. Chaos results are "inconsistent across metrics" pending
the Phase 0.8 unified re-measurement — consistent with v4.0's own
downgrade. Scenario adapters (COVID/Hormuz/GFC as generic force+economy
shocks) must become **domain causal adapters** (pathogen/policy/
health-system channels; shipping/energy/commodity channels; credit/
liquidity/housing channels) before any official backtest paper — this
moves into Phase 2 as its first task.

### Phase 0 amendments (now 12 tasks)
0.0a **Fix aging** — wire `generational_tick` (or equivalent) into
`live_one_day`; semantic invariant: population mean age advances
1/365 per day ± mortality effects; 365 simulated days age every
survivor by exactly one year.
0.0b **Virgin-slot rebirth** — central reset schema + typed-tie
rebuild on birth; invariant: a forced death→rebirth test proves the
reborn slot carries only intentionally inherited state and zero
inherited ties.
0.0c **Complete persistence** — presence, mobility, RNG state, clock
and version metadata in every save path; invariant: save→restore→hash
round-trip equality, and a branch from a restored snapshot under the
same seed reproduces the branch from the live world.
0.0d **Fabric re-homing** — migration and firm change must rebuild
locality-, workplace- and co-presence-dependent ties (the fabric
currently goes semantically stale when people move — a correctness
mismatch, not a new-physics request); invariant: a migrated agent is
removed from old local/colleague structures and added to new ones.
Then 0.1–0.8 as written, with the semantic invariant suite (above)
added to 0.3 as the release gate. Note that "Two Earths" includes the
**product API**: `earth1/api/deps.py:19-35` still resolves the old
`LivingWorld`/`WorldState`, so 0.5's exit criterion explicitly covers
`/ask`, `/world`, `/forecast` and the observatory — every production
surface answers from the same world UUID/hash as the daemon.

### From the full V1-Readiness read — the execution architecture (adopted)

The document was read in its entirety — 71 pages, 60 chapters,
appendices A–I. Beyond the P0 findings above, its second half
contributes something v4.0 did not have: a complete **execution
architecture** — contracts, gates, work packages, claim discipline and
registry schemas. All of the following is adopted into this Bible.

**1. The E0–E5 evidence hierarchy** (finer-grained than, and mapped
onto, BUILT/WIRED/LIVE/VALIDATED): E0 comment/plan (intent only) →
E1 executable code path → E2 semantic test/deterministic invariant →
E3 internal diagnostic artifact → E4 external empirical benchmark with
verified truth → E5 prospective frozen prediction / independent
replication. Two promotion rules: *a module is never promoted from E1
to E4 by prose*; and *an E3 failure is not grounds to delete a
mechanism if the benchmark never exercised it or a correctness bug
contaminates the route — diagnose the causal path first* (this is why
"delete the dead engines" was wrong and PORT-then-retire is right).

**2. The universal module acceptance test.** A layer is accepted into
V1 only when all five hold: (i) its state survives save/reload and
snapshot/restore; (ii) its parameters have provenance and uncertainty;
(iii) a module-level observable is calibrated against real data;
(iv) disabling it produces the expected causal difference on at least
one benchmark designed to exercise it; (v) its outputs are stable
under timestep/resolution changes within declared tolerance. This
becomes the gate for **every** module row in Part X.

**3. Lifecycle ontology ruling.** `_be_born` can only fill dead slots
and sets `age=0.0` ≈ adult entry at 18 — so the current world is a
**fixed-capacity adult-slot model**, which is valid *only if declared*.
The ruling: declare adult-entry capacity semantics explicitly in API
and papers now (fast path for V1); a resizable population with
childhood stages is the later path to literal 8.3B. No growth claim
beyond capacity until dynamic allocation exists.

**4. One-Earth invariants + the WorldModule contract.** Six invariants:
API reads/writes the world the daemon evolves; branching copies the
complete world, never a reduced substitute; timeline restore
reconstructs the exact module set and schema version; earthling
observation is a view into canonical state; benchmarks may initialize
from snapshots but cannot construct a second ontology; every
physics/submodel version is part of the prediction commitment hash.
Each subsystem migrates toward a formal module contract (the FMI-3.0
co-simulation pattern): declared `state_schema`, typed inputs/outputs
with units, `step(dt, rng, inputs)` with an explicit stochastic
stream, events, calibratable observables, typed parameters,
**fidelity levels** (reduced-form / surrogate / specialist solver) and
bit-consistent checkpoint/restore. This is the architectural answer to
"model ALL of it": a nuclear module exposes reduced geopolitical state
most days and swaps in blast/radiation physics for a nuclear scenario;
climate consumes observed ERA5 fields for replay and DestinE-class
storylines for futures. Resolution follows the causal question.

**5. Scrub / Assimilate / Branch — the time machine formalized.**
SCRUB = restore a state the synthetic world actually lived (versioned
complete snapshots, seekable journal, seeded replay metadata).
ASSIMILATE = condition an ensemble of plausible lived histories on
observations (localized ensemble DA, filtered-vs-unfiltered twin, ESS
diagnostics — never resample the million-dimensional agent array as
one particle). BRANCH = fork any restored world into
scenario/control ensembles (full clone, domain adapter, common random
numbers, consequence distributions). The official backtest protocol:
historical ensemble from a frozen start; dated exogenous history;
assimilate **only information available up to the branch date**;
restore the pre-event ensemble; inject resolved event vs control;
evolve; compare external consequences. The live product is the same
operation with the branch date = now.

**6. Event ontology — natural language is perception; event objects
are physics.** Every ingested headline/document becomes a structured
`WorldEvent` (actors, location, affected systems, magnitude,
confidence, duration, causal channels, provenance). The LLM extracts;
**the LLM must not directly write the outcome.** Domain adapters then
translate events into model inputs with explicit units: pandemic
(pathogen params, seeding, NPIs, hospital capacity), energy/shipping
(route capacity, supply, freight, pass-through), financial (credit,
solvency, asset shock, refinancing), war (territory, casualties,
refugees, sanctions), climate-extreme (fields + sector impacts),
technology and political/policy families.

**7. Observer effects and manifesting — the scientific separation.**
Five concepts that currently share language must never share claims:
psychological observer effect (being asked crystallizes attitude —
potentially real, must be calibrated, never triggered accidentally by
measurement code); statistical observation (new data conditions the
ensemble — the assimilation mathematics, valid); the quantum
measurement analogy (experimental only; no claim that civilization
obeys quantum mechanics); manifesting (model through causal behavior —
expectations altering decisions/actions/social signals — if
measurable, never through unsupported physics); unknown laws (cannot
be encoded as facts; represent as competing hypotheses). Observation
may legitimately change the synthetic state **when there is a causal
channel** — survey reactivity, self-fulfilling expectations, market
reflexivity, assimilation, policy response.

**8. 8.3B — identity namespace ≠ compute resolution.** The scale
design: a canonical live civilization at a validated reference
population; every agent carries a population weight and
representativeness cell; **adaptive splitting** — cells with high
causal sensitivity, rare tails, dense scenario exposure or claimed
real earthlings split to higher resolution; a stable 8.3B identity
namespace can exist before literal 8.3B simultaneous compute (a
claimed earthling gets explicit persistent state). The scale ladder,
each rung earned by an observable that *requires* it: 200K
(correctness/reproducibility) → 1M (country/cohort distributions
stabilize — already measured: country-mean accuracy is flat past ~1M)
→ 10M (rare tails/geography/network) → 100M (does adaptive splitting
still miss local heterogeneity?) → 1B (literal locality vs weights) →
8.3B (does one-state-per-human create demonstrable value?). Never
claim 8.3B because counts were multiplied by 8.3B/N.

**9. The four-partition benchmark doctrine — "no failure mode"
without overfitting.** Every benchmark has four partitions:
engineering tests, calibration/training, development/validation, and
final/prospective holdout. MISS → causal diagnosis → literature →
hypothesis → calibration → DEV retest → repeat → FREEZE → HOLDOUT
once. "We do not accept failure" means the team never stops
engineering; it does not mean the team edits the exam after reading
the answer sheet. A negative holdout stays on the public ledger and
becomes the next model version's program. The nine-step miss protocol
is adopted verbatim into VII.3: reproduce on immutable snapshot →
trace the causal path (units, dt, persistence, reachability *before*
touching physics) → sensitivity/ablation (if no parameter can move the
error, a causal channel is structurally missing) → literature memo
with competing hypotheses → candidate mechanisms behind experiment
flags → calibrate with observation uncertainty → placebos and
adversarial baselines, simplest robust mechanism wins → promote only
with semantic tests + no regression → freeze and score holdout once.

**10. NEVER CALIBRATE TO CHAOS.** A positive Lyapunov/FSLE exponent is
not a quality target; increasing feedback until a metric turns
positive is reverse-engineering an aesthetic. Calibrate mechanisms to
real observables; then *measure* whether sensitive dependence emerges.
The chaos benchmark is comparative: perturbation growth under shared
randomness vs same-state replicate noise, and whether perturbations
change policy-relevant consequence distributions — not whether a
scalar exponent is positive. Emergence is validated by its own table:
cascade reproduction (on > off), network structure vs external social
data, perturbation reach above the noise floor, path dependence
(same event on distinct assimilated histories → plausibly different
responses), distributional tails without hand-injection, and ablation
(removing a mechanism degrades the observable it explains, held-out).

**11. Benchmark A restructured — five tasks, and MRP becomes an ally.**
The WVS benchmark is built from **official microdata with survey
weights** (the WVS/EVS Trend 1981–2022 corpus: 464 surveys, 120
countries/territories, 666,907 respondents — repeated cross-sections,
NOT panel data; cohort validation must be phrased as repeated
cross-sectional cohort distributions, never individual trajectories).
Tasks and targets: (i) country means — non-inferior to strong MRP
(≤0.5pp excess MAE) or significant hybrid gain; *the country mean
alone is no longer sufficient*; (ii) cohort/age cells — ≥10% relative
error reduction vs strongest baseline and ≥75% correct gradient
direction on held-out cells; (iii) joint distributions —
energy/Wasserstein improvement over independent-marginal synthetic
populations; (iv) held-out question generalization — beat the
LLM/semantic-neighbor baseline on a frozen new-question set;
(v) cross-wave deltas — beat no-change and trend baselines, final wave
untouched. If MRP wins national means, Earth-1 *uses MRP as a
calibration layer* and demonstrates value where agent structure
matters: tails, joints, networks, path dependence, intervention
response. V1 reports the incremental value over the best statistical
baseline — that is the honest headline.

**12. Benchmark B universal scenario metrics (reconciled tiers).**
Per-scenario, pre-registered: direction ≥75% of observables (ACCEPT;
v4.0's 85% becomes the GOOD tier); magnitude — median normalized
absolute error beats the strongest simple causal baseline; geography —
median Spearman ρ ≥ 0.5 on exercised outcomes; timing — lag error
within domain tolerance; coverage — nominal 80% intervals empirically
covering 70–90%; scenario discrimination — between-scenario distance
above within-scenario noise with CI; attribution — paired controls
mandatory, zero-effect placebo ≈ 0. Final V1 gate: **at least three
resolved events across ≥ two domains** pass pre-registered criteria.
COVID gets hard aggregate anchors: WHO ≈ **14.9M excess deaths
2020–21**; ILO **8.8% of global working hours lost in 2020 ≈ 255M
FTE jobs**; Oxford Government Response Tracker for policy timing;
excess-mortality, labor, mobility, hospital-load, policy and
opinion outcome families each with a named external truth source. The
Hormuz adapter is specified: shipping network with chokepoint
capacity and rerouting; oil/gas production/import dependency and
inventories; price pass-through into cost of living and firm margins;
sector/geography supply-chain exposure; escalation as a *separate
branch*, not baked into every scenario; government reserve/subsidy
response. Success is not "the branches look different" — it is
treatment−control effects and geographic ranking stable above
stochastic noise and consistent with external elasticity/flow data.

**13. Benchmark C hierarchy — the hybrid is the product.** The
realistic ladder: (i) Earth-1 beats the raw frontier LLM on the scoped
set; (ii) Earth-1 probabilities are calibrated; (iii) the
**market + Earth-1 hybrid** shows positive out-of-sample incremental
skill — commercially the most meaningful result, since it answers
"does civilization state add information to price?"; (iv) ≥30–100
fully prospective resolved predictions before any broad forecasting
claim. Beating the market outright on a scoped domain is the stretch
goal, not the gate. Polymarket CLOB and Kalshi candlestick endpoints
reconstruct the market probability at arming time T (the Delta-3
timestamp discipline).

**14. Benchmark D (new) — the living-macro scoreboard.** Every
submodule gets its own empirical scoreboard *before* it may dominate
scenario results: labor transitions (ILO/World Bank), demography (UN
WPP), health (WHO/IARC/GBD), housing/homelessness (OECD/Eurostat),
crime (UNODC), wealth (WID/OECD/LIS), migration (UN DESA/UNHCR/IOM),
mobility (World Bank/ICAO/WHO), knowledge (UNESCO/OpenAlex),
climate/food (ERA5/FAOSTAT). Module calibration means plausible
marginal rates and response elasticities — otherwise a scenario miss
cannot be diagnosed because one cannot tell whether the adapter, the
substrate or the readout is responsible. Calibration method: global
sensitivity analysis → emulators/surrogates on prime → **history
matching** to eliminate implausible parameter regions (it treats
observation error and model discrepancy explicitly) → ABC/SBI
posterior refinement — the JASSS 2022 ABM-calibration toolkit, run as
designed ensembles on the 96 cores, hierarchical where parameters vary
by country/cohort.

**15. The measurement spine (added to Phase 1).** `data_registry/`
with source manifests, checksums, transformations, uncertainty;
`parameter_registry.yaml` generated *into* runtime constants — no
material numeric literal without source/status (schema per datum:
stable id, module/version, value/unit, scope, source/DOI, vintage,
estimation status authored/fitted/calibrated/derived, uncertainty,
train-data hash, validation status, sensitivity rank, introducing
commit); an experiment manifest on every run (prereg hash, commit +
dirty-tree status, world schema + module versions, snapshot ID,
adapter version, parameter/data hashes with roles, population
size/weights, streams/seeds/pairing, host, thresholds, artifact
checksums, auto-surfaced warnings); and a machine-readable
`STATE_OF_TRUTH.json` generated from tests/artifacts, never
hand-maintained — a design document must not outrank current code.

**16. Work packages and the first instruction.** The build sequence is
restated as WP-0…WP-10 (audit-freeze → One Earth → state continuity →
living CI → provenance → module calibration → timeline → scenario
adapters → benchmark harness → market record → V1 freeze), and the
discipline is adopted: **WP-0 first and alone** — branch
`v1-unification`, no new physics, produce `V1_UNIFICATION_AUDIT.md`
with the entry-point graph, state schemas, persistence fields, test
gaps and exact files to edit, reviewed *before* implementation. This
prevents discovering a second system after coding against the first —
which is precisely what happened between v3 and v4. The WP map onto
Part VIII: WP-0–3 ≙ Phase 0, WP-4 ≙ Phase 1's spine, WP-5 ≙ Phase 2's
module calibration, WP-6 ≙ Phase 5, WP-7–8 ≙ Phase 2, WP-9 ≙ Phase 3,
WP-10 ≙ Phase 6.

**17. Four papers, not three.** A/B/C as specified in Part VI, plus
the **Technical Architecture paper**: an ODD+-style model description
(the Grimm et al. 2010/2020 protocol — purpose/patterns,
entities/state, process overview = the daily heartbeat, design
concepts, initialization, input data, submodels with parameter tables,
fitness-for-purpose = the benchmark suite and claim boundaries). This
is what makes Earth-1 reproducible and reviewable rather than
folklore.

**18. The claim ladder (public claims discipline).** Now: "a living,
branchable synthetic civilization kernel with material, biological,
social, institutional and memory state" (evidence: code, E1–E3).
After One Earth: "every product surface uses one persistent living
civilization." After Paper A: "reproduces specified held-out human
distributions at measured accuracy relative to strong baselines."
After Paper B: "reproduces specified consequences of resolved events
from pre-event worlds within measured uncertainty." After Paper C:
"collective expectations prospectively calibrated, adding measured
forecast skill on scoped questions." After multi-domain replication:
"a validated computational civilization model for specified domains."
**Not until proven, never:** predicts civilization generally; perfect
digital twin of every human; 8.3B literally live; deterministic chaos;
quantum consciousness/observer effect.

**19. Standing Rule 11 — the ten prohibitions** (verbatim class, from
Appendix H, born of this exact week): no third world or "temporary"
production state for a benchmark; no promoting a mechanism because the
output looks more alive/chaotic/polarized/interesting; no fixing a
failed benchmark by authoring the holdout answer into a coefficient;
no calling a module validated off an end-metric that never exercised
it; no claiming 8.3B from multiplied counts; no describing
reduced-form health as clinical prediction or abstract escalation as
nuclear physics; no "quantum" language upgrading an analogy into an
empirical claim; no design document outranking current code; no
reporting a single chaotic branch as a forecast — paired effect
distributions with uncertainty, always; no hiding a failed mechanism —
ledger, diagnosis, calibrated replacement.

**20. Operations.** The machine allocation gains "never-do" columns:
CCX33 — no calibration grids, no mutable experiment branches, no
unversioned physics changes; prime — never becomes canonical just
because a result ran there; Storage Box — no silent overwrites,
retention policy, **restore rehearsal required**; laptop — control
plane only, never the sole copy of anything. Every run launches
through a checked-in job manifest; the supervisor reports run ID,
snapshot, commit, parameter hash, PID, host, progress, artifact
destination. *Observable progress is mandatory; wall-clock estimates
are optional.* Deployment-as-code for the living daemon: checked-in
unit file, health endpoint, restart policy, state lock, deployment
manifest with commit SHA and physics version.

**21. Research foundations added to Part IV** (all primary):
Destination Earth / ECMWF Climate DT (operational multi-fidelity
Earth-system twin — the 8.3B-scale architectural precedent alongside
Covasim); FMI 3.0 (the module-contract standard); Grimm et al.
2010/2020 (ODD protocol, DOIs 10.1016/j.ecolmodel.2010.08.019 and
10.18564/jasss.4259); JASSS 2022 history-matching + ABC for stochastic
ABM calibration; the WVS/EVS Trend File 1981–2022 (DOI
10.14281/18241.27); Polymarket CLOB prices-history and Kalshi
historical endpoints; WHO COVID excess mortality; ILO WESO 2021; IARC
CI5 Volume XII / GLOBOCAN (to replace the income-tier cancer
constants).

**22. The final CTO recommendation, adopted as this document's closing
ruling:** do not freeze Earth-1 v1 today — freeze the **architecture
direction** today. `alive.World` is the civilization; everything else
becomes an adapter, a readout, a module or an archived benchmark. The
next leap comes not from more ambition but from making what exists
coherent, empirically calibrated and impossible to misinterpret. Then
the V1 decision is made from the three benchmark papers, not from a
feeling that the architecture is finished.

---

## HOW TO READ THIS DOCUMENT

Part I is the verdict. Part II describes the system as it actually is — one
model, two substrates, three machines. Part III is the audit: every
disconnection, every defect, every parameter, with file and line. Part IV is
what the research literature has established and what it implies for us,
thread by thread. Part V is the diagnosis — why nothing has moved, stated
causally. Parts VI–VIII are the benchmark specification, the calibration
methodology, and the phased plan with exit criteria. Part IX is risk.
Part X answers, item by item, the founder's scope list ("do they have air,
oxygen, gravity, cancer, flights, atomic bombs…"). Part XI is the standing
rules. The appendices carry the parameter provenance census, the measured
results log, and the full defect ledger.

The single most important sentence in the document is this one:

> **Earth-1 is not one broken system. It is three well-built systems —
> a living world, an opinion engine, and a validation harness — that were
> never connected to each other, and every measurement to date has graded
> the wrong one.**

---

# PART I — EXECUTIVE ASSESSMENT

## I.1 The verdict

Earth-1 is a **25,682-line, 92-module agent-based civilisation simulator**
with:

- a genuinely novel dynamical core (conviction-conditioned polarizing
  kernel with a material restoring force — a bounded-confidence variant
  the field has not validated against surveys, §IV.4),
- a **complete benchmark data estate** (40 questions × 66 countries of
  survey ground truth, GSS microdata, WVS waves 5/6/7, pinned CV folds,
  19 pre-registrations),
- **894 tests**,
- a **live 4,000,000-agent world** ticking every 60 seconds on dedicated
  hardware, reading real news hourly,
- and live, keyless adapters to Polymarket, Manifold, GDELT, and the
  World Bank.

It also has **three architectural disconnections** and a **fourth,
subtler one** discovered in the final audit pass:

1. The **benchmarks grade a dead engine** (`benchmark.py` → `engine`,
   `predictions.py` → `engine`, `answer.py` → `tick`).
2. The **opinion path reads none of the world** (`answer.py` consumes
   exactly `civ.forces` and `civ.means`; zero references to life,
   health, flourishing, knowledge, or class).
3. The **product layer is driverless** (six finished, zero-importer
   modules: `answer`, `embedder`, `observer`, `timeline`, `assimilate`,
   `signal_bus`).
4. **The chaos instrument is not the live world.** `chaos.world_step`
   — the function under which the butterfly effect, FSLE, and Lyapunov
   results were measured — omits susceptibility and nine live
   subsystems (health, institutions, weather, flourishing, contagion,
   mobility, feed, memory, births) and runs at `beta=1.0` where the
   live loop runs `beta=2.0`. The headline chaos number characterises
   a **reduced system**, not the world on the box.

**Consequence:** every quantitative claim Earth-1 has ever produced —
including its strongest — must be re-stated at reduced strength until
re-measured on the unified path. The engine is not broken; the wiring
is. The distance to a defensible v1 is roughly two weeks of disciplined
integration and calibration work, not a rebuild. But none of that work
means anything until the wiring is fixed, and every calibration hour
spent before then is wasted by construction.

## I.2 Claims inventory — what may be said today, at what strength

| claim | evidence | strength after audit |
|---|---|---|
| The (reduced) world is chaotic at realistic perturbation scale | FSLE **+0.1321/day**, doubling 5.4 days, 8/8 trials, placebo divergence exactly 0.0 | **Moderate** (was Strong). Measured on `chaos.world_step`, which omits 9 live subsystems. Must be re-measured on `live_one_day`. Determinism caveat: `memory.spread` uses the unseeded global RNG (§III.5-D4), so any run where memories existed is suspect. |
| Collective structure exceeds individual structure | Novel-coherence 0.79 vs shuffled control 0.48 (pre-registered control) | **Moderate–Strong.** The control is real and can fail. Same reduced-system caveat. |
| The whole exceeds the severed parts | Φ-proxy on full state 0.079; 100% of agents change when the world is cut; severed halves *more* disordered | **Moderate.** Single measurement; group-Φ methodology has published precedent (§IV.7). |
| Relative historical severity is correct | COVID > GFC > Arab Spring ranking, after three measurement bugs fixed | **Moderate.** Ranking is the right test class (needs no historical initialisation); passed at small and full scale. |
| Global consequence aggregates are stable and correctly ordered | jobs 25.1M/34.4M/41.7M (±5–29%), destitution 81M/206M/525M across three Hormuz futures | **Moderate.** Paired-control estimator; spread reported. |
| Country-level consequence geography is reportable | noise floor ≈ 0 rank correlation at every sample size; needs ~15 paired repeats (measured SNR arithmetic) | **NOT REPORTABLE today.** Path to it is priced, not speculative. |
| Population parameters match published sources | addiction 2.3% (WHO), isolation 10.6% (~12%), ownership 64.1% (~65%) | **Not evidence of anything.** These are inputs read back out. The audit confirms each is a constant in a table (§III.6). |
| One unfitted macro result | wealth Gini rises 0.45 → 0.66 with no inequality parameter anywhere | **Weak.** It kept rising past the real ~0.70 to 0.80. The *mechanism* (compounding without brakes) is real; the *level* is uncalibrated. |
| Any opinion/WVS accuracy claim | 10.59pp GOQA etc. | **VOID as a claim about the living world.** All measured on the dead engine. |

## I.3 The three questions a top-tier reviewer asks, and today's answers

1. *"Your benchmarks import `engine` and `tick`. What system do your
   numbers describe?"* — Today: the abandoned one. Fix: Phase 0.
2. *"You have 102 tunable constants and no estimation procedure. How is
   this calibrated?"* — Today: by eye. Fix: §VII (MSM/Indirect
   Inference with pre-registered moments — the field's standard for
   thirty years).
3. *"Where is the out-of-sample validated number?"* — Today: none.
   Fix: Part VI, three benchmarks with targets set from the published
   state of the art before measurement.

All three are answerable within the plan in Part VIII. None is
answerable now. **Until Phase 0 exits, the system should not be shown
to a technical audience.**

## I.4 What is genuinely impressive and defensible right now

A reviewer who reads the code rather than the numbers would find:

- The **paired common-random-numbers estimator** in `branch.py` (control
  and scenario on identical dice, matched-pair differencing) — the
  correct variance-reduction design, measured to triple the extracted
  signal.
- **Nineteen pre-registrations** with thresholds committed before
  measurement, several of which *fired against us* and were honoured
  (the knife-edge FAIL on local thresholds, the destitution-bar FAIL).
- The **falsifiable-control discipline** — unfiltered twin in the
  assimilation filter, shuffled-fabric control in novel coherence,
  placebo world in the butterfly test (which returned exactly 0.0).
- A **consequence layer** whose numbers are always attributable
  differences with spreads, never point forecasts.
- The **two-substrate diagnosis itself**, done before benchmarking
  rather than after publishing.

This is the material the eventual paper's methods section is made of.
It is genuinely above the standard of the ABM literature we audited,
where empirical validation is the exception (§IV.4).

---

# PART II — THE SYSTEM AS IT IS

## II.1 One model, two substrates

Everything in `earth1/` is one project, but the code carries **two
generations of physics**:

**Substrate A — the opinion engine (older).** A static `Civilization`
(struct-of-arrays population; 18 country-level features from Hofstede,
Inglehart, and census) read by `engine.run_question`: baseline + force
projection + diffusion → a yes-percentage with force anatomy. On top of
it sit the grounding cascade (`grounding.py`, four paths A/B/D/C with
`calibration_source` as a first-class receipt), the LLM gateway, the
narration layer, and the entire FastAPI surface. **This is what every
benchmark, and the API, executes today.**

**Substrate B — the living world (current).** The `World` dataclass in
`alive.py`: `civ, life, fabric, health, knowledge, gov, klass,
chronicle, feed, climate, flourishing, presence, mobility, day` —
advanced by `live_one_day`. **This is what runs on the world box.**

The two substrates share `genesis.py`, `calibration._build_features`,
`types.py`, and the data estate. They do not share physics, and no
serving or scoring path crosses from A's questions to B's world.

## II.2 The living day, in causal order

`live_one_day` executes, per simulated day:

1. **govern** — each of 194 governments reads yesterday's deprivation
   and unrest *against the norm its population is habituated to*, sets
   welfare/policing/tax, and may start or end wars (nuclear deterrence
   and escalation-ceiling modifiers).
2. **policy & war land on people** — welfare generosity *is* the safety
   net (a decision, not a constant); war wrecks firms and kills the
   conscripted young.
3. **matter** (`life_tick`) — firms fail and lay off everyone inside at
   once (the correlated-shock mechanism); separation/finding hazards;
   wages, rent, arrears → eviction at 90 days; savings in
   days-of-survival; deprivation; and the body/self: mental health with
   heritable setpoints, addiction onset/recovery, relationships,
   crime victimisation, bereavement, children.
4. **bodies** (`health_tick`) — cancer by Armitage-Doll
   (`incidence ∝ t^(k−1)`, k=6: a 70-year-old is 2⁵ = 32× a
   35-year-old), CVD, infection, injury, **falls** (hazard doubling per
   decade past 65, with the decline cascade into isolation), treatment
   gated by country income *and* personal wealth; a death bereaves the
   dead person's whole neighbourhood.
5. **class** — homelessness as a conjunction (broke ∧ alone ∧ weak
   net), crime from pressure minus policing and status, wealth
   compounding above a buffer, migration.
6. **knowledge** — learning from people who know more (network
   property), status, scientists as the 99.5th percentile, discoveries
   ratcheting a permanent global commons, art as decaying works.
7. **weather** — a persistent temperature-anomaly field per country;
   heat and cold kill the frail, heat raises aggression, drought cuts
   farm wages, storms wreck firms and savings.
8. **flourishing** — hunger (income-driven, slow, political), thirst
   (infrastructure-driven, fast), breath as a continuous tax; then
   hope, curiosity, meaning, belonging, satisfaction — with unmet need
   crowding out everything above it.
9. **susceptibility** — an (N,8) gain matrix: the distressed are
   measured 1.52× more movable by fear, the addicted 0.62× as movable
   by collective pressure, the young 1.60× the old.
10. **influence** — the conviction-conditioned kernel: the certain pull
    the unsure toward their *pole*, not the midpoint (contraction →
    expansion; β=0 recovers plain averaging exactly).
11. **the restoring pull** toward the force state each agent's actual
    circumstances imply (`life_force_target`) — the tension that makes
    the system a forced nonlinear oscillator instead of either a frozen
    saturation or a spreadsheet.
12. **co-presence contagion** — affect (not opinion) spreading between
    bodies in the same place through the evidenced channels
    (chemosignalling, mimicry, prosody, synchrony); gatherings; crowds
    when enough co-present people are aroused *and aggrieved*; riots;
    plus **shared attention** — national simultaneity (sport, ceremony).
13. **mobility** — road deaths (peaked in the twenties), commuting as a
    tie tax, flights importing disease and providing the model's *only*
    non-convergent cultural channel.
14. **the feed** — an asymmetric, agreement-selected, arousal-weighted
    graph applied only to the online (HIC 79% … LIC 38%); measured
    polarisation gap online vs offline +1.4% → +2.2% and compounding.
15. **memory** — events as objects with salience half-lives, rehearsal
    on similar recurrence, spread along the fabric.
16. **cascades** — per-locality threshold rules (critical fraction on
    the people it actually happened to, never a national mean).
17. **feedback** — absorbed force leaves a permanent trait residue
    measured against the agent's *own neighbourhood*, never a global
    mean; experience moves the force baseline (the closed ring that
    made permanence possible).
18. **birth** — conception by partnered fertile agents into freed
    capacity; population genuinely grows and shrinks (measured birth
    rate 1.34%/yr vs real 1.7%).

## II.3 The machines

| machine | spec | role | state (2026-08-19) |
|---|---|---|---|
| **world box** (CCX-class, 167.233.77.48) | 8 cores, 30 GB | the single writer; `earth1-alive.service` | ✅ **live: 4,000,000 agents, day ~40+, one world-day/60s**, reading GDELT hourly, full state persisted every 30 min, SIGTERM-safe, `Restart=always` |
| **prime** (AX162, 46.4.189.237) | **96 cores, 503 GB** | the laboratory | ❌ **idle all week** — every ensemble ran on a 10-core laptop. Supervisor + 5-min timer installed and healthy. |
| **storage box** | €4/mo | off-site memory | ⚠️ backup timer **enabled and firing**; last-run success **unverified** (script unreadable to the agent — contains the credential); sized for a 900 MB world, now serving an 18 GB one |
| **laptop (this machine)** | 10 cores | iteration | ⚠️ carries a **launchd job at 09:07 daily** running `world_daily.py --read-news` — a *third* world, on the **old substrate**. Goes on the kill list. |

Performance, measured: **4.5 KB/agent, 0.58 s per world-day at 200K**
(≈0.35M person-days/sec). Reference implementation (Covasim, §IV.6):
**1 KB/agent, 7M person-days/sec** — we are 4.5× heavier and ~20×
slower, with the reference's fixes (float32, Numba) directly
applicable. Scale ceilings, measured and computed: 2M = 9 GB (running
now), 10M = 45 GB (prime, trivially), 100M = 450 GB (prime, batch
only), 8.3B = 37 TB and 6.7 h/world-day (**not reachable
full-fidelity**; reachable by dynamic rescaling — Covasim's published
technique — plus observation-triggered instantiation).

## II.4 The data estate (measured)

- **Ground truth (~26 files):** GOQA 40 questions × 66 countries (plus
  polarity-corrected v2), GSS 1972–2024 microdata extraction (513 KB),
  WVS-7 cohort aggregates, WVS wave-5/6 inline datasets, WDI tide
  (464 KB), OWID trust, GDELT history/themes, headlines 2017–2022,
  joint priors and cell densities from WVS7 microdata.
- **Pre-registrations: 19** — every major experiment this week ran
  against a threshold committed first.
- **Results: ~64** experiment outputs, each mirrored by a script.
- **The living world on disk:** `data/living/earth1/` (~42 MB) plus the
  4M world under `data/alive/` on the box.
- **Missing:** `data/history/` — the timeline's snapshot store —
  **does not exist**. The 2015 timeline has never actually been run.
- Infrastructure: pinned CV folds, standing-record SQLite, market-scope
  cache, one captured signal-bus day.

---

# PART III — THE AUDIT

## III.1 Inventory and classification (measured)

92 modules, 25,682 lines:

| class | modules | lines | share |
|---|---|---|---|
| LIVE (reachable from `live_one_day`) | 25 | 8,100 | 32% |
| DEAD-ENGINE family | 11 | 1,937 | 8% |
| BENCHMARK/validation | 19 | 6,007 | 23% |
| PRODUCT, finished but unwired | 24 | 5,782 | 23% |
| other orphans | 13 | 3,856 | 15% |

**No stubs anywhere.** Every audited module is functionally complete.
The entire liability is integration debt.

## III.2 Disconnection ledger

**D1 — Benchmarks grade the dead engine.** `benchmark.py` imports
`engine` + `dynamics`; `predictions.py` imports `engine`;
`calibrate.py` inherits it; `placebo.py` couples to `receiver`/`engine`
field-shift machinery; `g5.py` is built on `tick`/`advance`;
`validation_ladder.py` R4 drags in `benchmark`. **Every opinion-side
number ever reported (including 10.59pp GOQA) describes the dead
engine.** Already live and clean: `backtest_run.py`, `hormuz.py`,
`markets.py`, `wvs_paired.py`, `wvs_wave5.py`, `holdout.py`,
`calibration.py` (live-shared).

**D2 — The opinion path reads none of the world.** `answer.py` +
`_build_features`: inputs are `civ.forces`, `civ.means`. Zero
references to life/health/flourishing/knowledge/class. The MRP
literature identifies exactly this (no within-unit covariates) as the
cause of within-country failure (§IV.2) — and we measured exactly that
failure (R1 FAIL, R2/R4 PASS).

**D3 — Six finished modules with zero importers.** `answer`,
`embedder` (the cascade still runs hashed TF-IDF, not the built GTE
embeddings — silent retrieval-quality loss), `observer` (the
manifesting mechanic), `timeline`, `assimilate`, `signal_bus`. Four of
six are already World-native and lack only a driver.

**D4 — The instrument is not the world.** `chaos.world_step` vs
`live_one_day`: missing susceptibility, health, institutions, weather,
flourishing, contagion, mobility, feed, memory, births; `beta` 1.0 vs
2.0; cascade block duplicated (drift risk already realised). All chaos
constants (FSLE, Lyapunov, entropy trajectories) therefore describe a
reduced system.

## III.3 The dead engines are not dead weight — unique physics at risk

The deletion recommendation in earlier drafts was **wrong**. The audit
found five modules whose physics has **no live-path replacement**:

| module | unique capability | disposition |
|---|---|---|
| `coupling.py` | cross-question interference (a stance on immigration bleeds into trade) via weight-vector cosine overlap | **PORT** — the live world answers questions independently, which is false of humans |
| `graph_dynamics.py` | evolving topology: agreement strengthens ties, disagreement severs them → echo-chamber formation | **PORT** — the live fabric is static after birth; the feed's homophily edges are frozen at day-0 stances |
| `event_generation.py` | endogenous event detection: the world notices its own polarization/consensus/reversal/cascade and reacts | **PORT** — live events come only from thresholds and news |
| `perishability.py` | force-specific opinion decay (fear decays in weeks, identity holds generations) — "the commercially decisive claim" | **PORT** — trivially small (1 KB) |
| `dynamics.py` | per-force nonlinear susceptibility + trait-residue learning on force *vectors* | **MERGE** — the live `susceptibility.py` supersedes part; residue mechanics differ and must be reconciled |
| `engine/tick/living/advance/diffusion/forces` | superseded loops; but `run_multiverse`, `run_freetext`, `attend`, `civ_breakdown`, census-drift re-anchoring (§34), and `tick._make_mutable` (imported by the **live** `answer.py`) still live here | **REPOINT then RETIRE** — cannot be deleted first: the FastAPI surface and 611 tests sit on them |

## III.4 Test estate — the finding that explains the dead engine's survival

- **894 test functions** across 53 files.
- **611 (68%) import a dead-engine module.**
- **Zero test files import the live path.** `alive`, `influence`,
  `chaos`, `answer`, `branch`, `backtest`: no unit coverage at all.

The dead engine survived because its tests kept passing. The live world
has no tests to fail. **Rule for Phase 0: write live-path tests before
retiring dead-path tests, or coverage drops to zero at the exact moment
of migration.**

## III.5 Live-module defect ledger (from the line-level audit)

**Correctness (fix in Phase 0):**

- **D4-a `memory.spread` uses the unseeded global RNG**
  (`np.random.random`) — breaks reproducibility of any run in which a
  memory exists, invisibly to seed control. Every paired-difference
  measurement made with a populated chronicle is suspect. One-line fix;
  large blast radius.
- **D4-b `health.py` shared random row:** treatment acceptance reuses
  `u[4]`, the same draw as fall onset — treatment is statistically
  correlated with falling. Row 5 allocated, never used.
- **D4-c `influence.update_conviction` decay is a no-op:**
  `- decay * 0.0`. Isolation *never* softens conviction, contradicting
  both docstring and design. Conviction is a ratchet.
- **D4-d cause-code collision:** war writes `cause_of_death=5`, which
  collides with fall=5 in `condition` space; weather=6, want=7, road=8
  assigned ad hoc across four modules with no shared enum.
- **D4-e two fertility implementations** (in `alive._be_born` and
  `life_tick`) with different windows and rates, both live.
- **D4-f newborn traits/knowledge blend toward the *planetary* living
  mean** — a child in Niger inherits 50–65% of a global average
  (the recurring global-mean defect, occurrence #7).
- **D4-g migration ignores the diaspora corridors** the fabric builds —
  destinations drawn from a global "calmest-25" list, unrelated to the
  mover's ties.
- **D4-h `thresholds.detect_transitions` is entirely bypassed live** —
  the inlined per-locality cascade ignores the rules' cooldowns and
  decay half-lives (dead fields), and `_check_condition` silently
  swallows malformed operators.
- **D4-i fabric symmetrizes media-hub edges** — broadcasters become
  mutual in the conviction kernel, contradicting the asymmetry the feed
  correctly preserves.
- **D4-j genesis builds a homophily graph that `birth_world` throws
  away** (overwritten by `fabric.adj`) — wasted compute and a trap for
  non-live scripts.
- **D4-k `EXPERIENCE` force = normalized age**, then polarized toward
  {0,1} by the same pole kernel as opinions — the young and old are
  treated as opposite *opinion camps* of an age axis.
- **D4-l dead code:** `CONSCRIPT_SHARE` and `NUCLEAR_USE_PER_WAR_YR`
  declared and never used (conscription is counted, never applied; the
  docstring's nuclear-use hazard is unimplemented); `mobility` fuel
  branch unreachable live; `couple_life_to_forces` (70 lines)
  superseded and dead; `chaos` imports `_participation` unused;
  duplicated `_gini`, `_tier`, locality-hash (4 sites), cascade block
  (2 sites).
- **D4-m flight disease import and cultural mixing pull from a
  uniform-random global agent**, not a destination — the "most
  connected countries hit first" claim is not structurally realised.
- **D4-n memory is nearly inert live:** nothing in `live_one_day` calls
  `remember`; only the hourly news event in `world_alive.py` feeds it.
  Scenario events (via `branch.apply`) do reach it.

**Defect classes, formally named (they recur, so they get names):**

- **Class GM — a global/national mean where a local quantity belongs.**
  Seven confirmed occurrences to date (national-mean thresholds,
  country-mean hardship, planetary-mean feedback, country-wide
  cascades, Φ-on-the-mean, top-5 geography lists, newborn planetary
  blend). Standing grep: every `.mean(axis=0)` in a coupling is a
  suspect until proven local.
- **Class CF — controls that cannot fail.** Three confirmed (self-
  compared noise floor returning exactly +1.000; two others). Standing
  rule: verify every instrument on a case with a known answer first.
- **Class IP — inputs read back as findings.** The parameter-echo
  fallacy (ownership 64.1% "matching" reality etc.).

## III.6 Parameter census

**102 hardcoded constants** across the ten dynamical live modules.
Provenance, per the line-level audit:

- **Genuinely SOURCED (≈10):** Armitage-Doll k=6; GBD mental-illness
  13%; WHO substance 2.3%; UN ICVS crime 4.5%/yr; WHO road deaths
  (8.3–27 per 100k by tier); falls ≈684K/yr + age-doubling decade;
  Centola/Granovetter 25% committed minority; Engel's-law cost shares;
  Rosenstein and Benettin estimator constants.
- **ANCHORED (≈40):** defended by a named real magnitude but no formal
  source (OECD separation ~12%/yr, ~8%/yr firm exit, heat+cold ~5M/yr,
  welfare tiers, connectivity tiers, TFR→household mapping…).
- **UNSOURCED (≈52):** the majority of the *coupling* constants — every
  force-coupling gain, relax/residue rates, threshold effect deltas,
  contagion gains, feed multipliers, body-clock rates, hope/meaning
  relaxations.

**Implication:** the dynamics are governed mostly by unsourced gains.
This is not fatal — it is the normal starting state of an ABM — but it
is exactly what §VII's estimation procedure exists to fix, and until
then no dynamical magnitude may be presented as calibrated.

## III.7 What is already right (audit-confirmed)

The consequence spine — `branch → consequences → backtest → observe` —
is finished, World-native, wired, and methodologically sound (paired
CRN estimator, attributable differences, spreads, suppress-below-noise
default). `markets.py` is engine-agnostic with live endpoints.
`grounding` + `live_search` + `stem_family` are a faithful, working
port of the validated old-model cascade, Path D verified live against
real Pew/Gallup data. The supervisor infrastructure on both boxes is
self-healing and has an append-only incident journal. Nineteen
pre-registrations exist and several fired against us and were honoured.

---

# PART IV — RESEARCH FOUNDATION

Ten threads. Each states what the field established, the source, and
the specific consequence for Earth-1.

## IV.1 ABM calibration is a solved methodological problem

**Established:** the estimation family for agent-based models is
**Simulated Minimum Distance** — the Method of Simulated Moments (MSM:
choose summary statistics, simulate, minimise the simulated–empirical
distance) and Indirect Inference (II: fit a simple *auxiliary model* to
both real and simulated data and match its parameters). MSM's
documented weakness is that **moment selection is arbitrary**; II's is
the arbitrary auxiliary model. Comparative treatment:
[Platt 2019, arXiv:1902.05938](https://arxiv.org/pdf/1902.05938);
surrogate-regression calibration
[JASSS 23(1)7](https://www.jasss.org/23/1/7.html); MSM applied to
agent asset-pricing
[Franke, J. Empirical Finance](https://www.sciencedirect.com/science/article/abs/pii/S0927539809000425).

**Consequence:** hand-tuning 102 constants is thirty years behind the
field. Adopted: MSM with a **pre-registered moment set** (our existing
prereg discipline is precisely the cure for MSM's known weakness), II
with impulse-response auxiliaries for the dynamic/scenario work.

## IV.2 The MRP literature predicted our exact failure

**Established:** MRP achieves **2–5 pp MAE** at state level
([Gelman et al., *Improving MRP*](https://sites.stat.columbia.edu/gelman/research/published/improving_mrp.pdf)),
and its decisive success factor is *"the strength of the
geographic-level covariates and the ratio of opinion variation ACROSS
geographic units relative to variation WITHIN units"*
([Warshaw & Rodden](https://sites.stat.columbia.edu/gelman/research/unpublished/MRT(1).pdf)).

**Consequence:** Earth-1's 18 genesis features are all country-level →
theory predicts cross-national success and within-country failure. We
measured exactly that (R2 0.1167 vs naive 0.1388 PASS; R4 0.1059 vs
0.1264 PASS; R1 0.1557 vs fair anchor 0.1158 FAIL). **R1 is a
textbook result, not a broken engine — and the prescribed remedy,
within-unit covariates, is precisely the life state that D2 blocks.**
This converts our most embarrassing measurement into a
theoretically-predicted one with a named fix.

## IV.3 The LLM competitive floor is lower than assumed

**Established:**
- Generative agents grounded in 2-hour interviews with 1,052 real
  people replicate their GSS answers at **85% of test-retest accuracy**
  ([Park et al., arXiv:2411.10109](https://arxiv.org/pdf/2411.10109)).
- LLMs reproduce direction/significance of up to **81%** of effects
  across 156 studies but **overestimate effect sizes**.
- Best LLMs align with WVS distributions on only **72–75%** of
  questions (16.7–33.3% under strict thresholds).
- Across 64 countries / 64,000 individuals, **plain OLS and Lasso beat
  every LLM tested** at predicting life satisfaction (MAE 1.37)
  ([arXiv:2507.06141](https://arxiv.org/pdf/2507.06141)); LLM agents do
  **not** outperform simple text classifiers at predicting social-media
  reactions.

**Consequence:** the competition is weak exactly where Earth-1 is
strong by construction — cross-national quantitative structure,
magnitudes, and counterfactuals (which neither an LLM nor a regression
can answer at all). The WVS benchmark must report the *coverage*
statistic (share of questions aligned) for head-to-head comparability
with the LLM literature.

## IV.4 Opinion dynamics: theory-rich, validation-poor

**Established:** the canonical bounded-confidence models are
Hegselmann–Krause and Deffuant–Weisbuch
([survey, arXiv:0707.1762](https://arxiv.org/abs/0707.1762));
**empirical validation against survey data remains an emerging area**
— Lorenz 2017 (ESS left-right landscapes) was among the first attempts
([JASSS calibration study](https://www.jasss.org/26/4/9.html)).

**Consequence:** Earth-1's conviction kernel is a
bounded-confidence-family variant (with the alignment-to-pole term as
the polarizing extension). The field's own validation gap is our
opportunity: **a BC-family model validated against WVS at MRP-band
accuracy would be a genuine contribution**, not a re-implementation.

## IV.5 The informal economy is the named missing mechanism

**Established:** informal employment is **counter-cyclical** and
buffers household income in downturns, especially outside the OECD
([IMF WP 2023/182](https://www.elibrary.imf.org/view/journals/001/2023/182/article-A001-en.xml);
[shadow-economy cyclicality](https://www.sciencedirect.com/science/article/abs/pii/S1062976922000254);
[World Bank, *The Long Shadow of Informality*](https://www.worldbank.org/en/research/publication/informal-economy)).
Two qualifiers: the buffer **saturates** in deep recessions, and it
**failed in 2020** — pandemic lockdowns hit informal work itself, and
ILO's monitor recorded **71% of employment losses as inactivity rather
than unemployment**.

**Consequence:** the destitution overshoot (881M vs 80M) and the
runaway Gini share one cause — Earth-1's informal income is a fixed
fraction of a wage that just collapsed, so the floor falls with the
ceiling. The fix is one mechanism with a shock-type distinction
(ordinary recession: buffer expands; lockdown-type shock: buffer
suppressed) plus an **inactive-but-surviving labour state** the model
currently lacks entirely. Calibration moments: the ILO 71%
inactivity share and World Bank informality shares by tier.

## IV.6 Large-scale ABM engineering has a published reference point

**Established:** Covasim — ~**1 KB/agent**, ~**7M simulated
person-days/sec/core**, pure Python with Numba 32-bit kernels;
OpenABM-Covid19 (C) similar; reference implementations **fail
out-of-memory at 128–256M agents**; Covasim ships **dynamic rescaling**
(agents represent more than one person past a threshold)
([PLOS Comp Biol](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fpcbi.1009149),
[OpenABM](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1009146)).

**Consequence:** our 4.5 KB/agent and 0.35M person-days/sec have a
concrete published path to ~1 KB and multi-million person-days
(float32 + Numba), and **dynamic rescaling is the peer-reviewed
precedent for the 8.3B architecture** — the same multi-resolution
design as WORLD.md §8, already validated in production epidemiology.

## IV.7 Group-Φ has published method and precedent

**Established:** exact IIT Φ is uncomputable for large systems; the
accepted practice is **proxy measures** (Barrett & Seth) estimated from
observed state transitions; applied to *groups*, higher measured Φ
predicts work-team performance and Wikipedia article quality
([Engel & Malone, PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0205335);
critical treatment [arXiv:1902.04321](https://arxiv.org/pdf/1902.04321)).

**Consequence:** the consciousness-profile instrument
(`integration.py`) is methodologically respectable — a Φ-proxy on the
full state with partition controls is exactly the published practice.
Results to date (integration present, novel coherence +0.31 present,
self-model weak-negative, anticipation z=+1.82 marginal, no phase
transition) may be described as a **functional-signature profile**,
never as consciousness detection.

## IV.8 Data assimilation for ABMs exists and hit our exact failure mode

**Established:** particle filters have been fused with ABMs
(Malleson et al., crowd simulation at Grand Central,
[JASSS 23(3)3](https://www.jasss.org/23/3/3.html);
[review, MDPI Mathematics](https://www.mdpi.com/2227-7390/11/20/4296);
COVID policy-diffusion ABM+PF
[arXiv:2302.11277](https://arxiv.org/pdf/2302.11277)). Documented
failure mode: **particle deprivation** — particles needed grow
exponentially with agents; documented remedy: **filter parts of the
state space, not all of it**.

**Consequence:** `assimilate.py`'s design — score only the 194-country
observable, localized per-country resampling (licensed by the measured
5.3% cross-border edge share), tempering, ESS floor, unfiltered twin —
is the published remedy implemented in advance of hitting the wall. The
"history-friendly" framing for the 2015 timeline also has a literature
home: ABMs as **credible counterfactuals for economic history**
([Italian Economic Journal 2025](https://link.springer.com/article/10.1007/s40797-025-00349-y);
[history-friendly models](https://link.springer.com/article/10.1007/s40821-019-00121-0)).

## IV.9 Prediction-market accuracy defines Benchmark C's scale

**Established (Brier, lower better):** Polymarket **0.0843** on
resolved markets; Kalshi/Polymarket cluster ~0.09; superforecasters
~0.09–0.10; frontier LLMs ~0.12 (ForecastBench); general public ~0.12
([Keyrock](https://keyrock.com/knowledge-hub/prediction-market-accuracy-brier-scores/),
[ForecastBench, arXiv:2409.19839](https://arxiv.org/pdf/2409.19839)).

## IV.10 Chaos and forecastability: the weather/climate precedent

**Established** (standard dynamical-systems results used, not novel):
finite-size Lyapunov exponents for scale-dependent instability (Aurell
et al. 1997); Benettin renormalisation for bounded attractors;
Rosenstein fitting on the initial linear region. The
weather-vs-climate distinction — trajectories unpredictable, **response
to forcing predictable** — is the epistemic license for the entire
consequence layer, and our country-map refusal is its measured local
expression.

---

# PART V — DIAGNOSIS

**V.1 Why no benchmark ever moved.** The causal chain is now fully
established: benchmarks import the dead engine (D1) → the graded path
never changed while the living world was built → "we built something
and the number didn't move" was structurally guaranteed. Not bad luck;
wiring.

**V.2 Why within-country failed.** No within-unit covariates (D2);
predicted by MRP theory (IV.2); remedy named (life state into
`_build_features`).

**V.3 Why consequence magnitudes are wrong.** One missing mechanism
(counter-cyclical informal buffer + inactive state, IV.5) explains the
destitution overshoot AND the unbounded Gini; plus the wealth layer has
no brakes (no consumption scaling with wealth, no crash losses, no
estate dilution).

**V.4 Why even the chaos numbers need re-measurement.** The instrument
system (D4) is smaller than the live system, and the determinism bug
(D4-a) contaminates paired designs whenever memories exist. Expected
outcome of re-measurement: chaos likely *stronger* on the full loop
(more coupled nonlinearity), but that is a prediction to be tested, not
assumed.

**V.5 Why the week felt chaotic to the founder.** Nine measurement
instruments were wrong before the systems they measured were: top-5
geography lists, a pinned allocation floor, an unpaired estimator, a
control compared to a bit-identical copy, a mean-based Φ, raw-level
region correlations, an endpoint graded against an integral, a
suppressed field read as zero, an inverted persistence parameter. Every
false "impossible" this week traces to an unverified instrument —
hence Standing Rule 1.

---

# PART VI — BENCHMARK SPECIFICATION

Three benchmarks. Targets fixed **now**, before measurement, at the
published state of the art. Each reports every baseline alongside.

> **Every tier below is governed by Part XI.A — NO DEAD-END RESULTS.**
> A miss against ACCEPT *starts* the MISS → VERIFY → DIAGNOSE →
> RESEARCH → IMPLEMENT → CALIBRATE → ABLATE → RETEST → PASS → FREEZE
> cycle; it never ends the work. A miss report that is only an
> explanation of why the number was bad is an incomplete deliverable.
> Thresholds never move after a result is seen, and the holdout is
> never tuned on. **Do not stop at "the model failed." Your job starts
> there.**

## VI.A — Opinions vs WVS

- **Instrument:** held-out WVS-7 items, cross-national, pinned CV folds
  (`data/cv_folds.json`), polarity-corrected ground truth, leakage
  gate (`feature_adjacency_gate`) enforced.
- **Baselines reported every run:** naive country grand-mean; MrsP;
  published MRP band; LLM coverage numbers from IV.3.
- **Metrics:** MAE (pp) and *coverage* (share of questions within the
  alignment threshold, for LLM comparability).

| tier | target | grounding |
|---|---|---|
| ACCEPT | **≤ 7.0 pp MAE** | −⅓ vs the dead-engine 10.59 pp; must beat naive and MrsP |
| GOOD | **≤ 5.0 pp MAE** | enters the published MRP band (2–5 pp) |
| WIN | **≤ 3.5 pp MAE** | mid-band MRP, cross-national — publishable |

## VI.B — Scenario simulation (COVID, GFC, Arab Spring, Hormuz)

- **Instrument:** paired-CRN branch vs control on the live world;
  cumulative person-years graded against cumulative records; every
  figure an attributable difference with spread; country detail
  suppressed below the measured noise floor.
- **Recorded anchors** (ILO/IMF/World Bank/UNHCR) are marked VERIFY in
  `backtest.py` and must be sourced to primary documents before any
  publication.

| tier | target | current |
|---|---|---|
| ACCEPT | direction ≥ 85% and ranking correct | 78%, ranking **PASS** |
| GOOD | + magnitude within 1 order on ≥ 70% of quantities | 50% |
| WIN | + within 0.5 orders on jobs (the primary quantity) | — |

## VI.C — Prediction markets (Polymarket, Kalshi, Manifold)

- **Instrument:** `markets.py` live endpoints; **≥ 50 contracts
  registered before resolution**, hash-committed; no post-hoc
  filtering; Brier against the market's own final price as the
  primary baseline.

| tier | target | meaning |
|---|---|---|
| ACCEPT | **Brier ≤ 0.12** | frontier-LLM / general-public band |
| GOOD | **≤ 0.10** | superforecaster band |
| WIN | **≤ 0.084** | beats Polymarket itself |

---

# PART VII — CALIBRATION METHODOLOGY

Hand-tuning is retired as of this document.

**VII.1 MSM with pre-registered moments (economic layer).** Moment set,
committed before any fitting run: unemployment rate;
**employment-to-inactivity ratio under shock (ILO 71%)**; wealth Gini;
destitution rate; homelessness stock; recovery half-life after a
standard shock; informality share by income tier. Empirical targets and
sources declared in the same prereg. Optimise the parameter vector by
weighted simulated–empirical distance; report the full vector with
provenance class (SOURCED / ANCHORED / ESTIMATED / ASSUMED).

**VII.2 Indirect Inference for dynamics (scenario layer).** Auxiliary
model: an impulse-response regression of the outcome path on shock
magnitude and lags. Match auxiliary coefficients between simulated and
real paths — this captures **recovery shape**, exactly where the COVID
magnitude failure lives and what raw moments miss.

**VII.3 The loop (mandatory, every iteration).**
1. Measure. 2. **Explain the number from the code** — name file and
line. 3. **Search the literature** for how the field solves it.
4. Adapt. 5. Retest until target. *No result is reported without steps
2–4 completed. A number without a mechanism and a citation is not a
result.*

---

# PART VIII — THE PLAN

## PHASE 0 — INTEGRITY (blocks everything; nothing downstream is meaningful before its exit)

| # | task | detail | exit criterion |
|---|---|---|---|
| 0.1 | **Fix the four correctness bugs** | seeded RNG in `memory.spread`; separate RNG row for treatment; make conviction decay real (or delete the parameter and the docstring claim); shared `CauseOfDeath` enum | bugs closed with regression tests |
| 0.2 | **Unify the loop** | `chaos.world_step` becomes a thin wrapper over (or is replaced by) `live_one_day`; one cascade implementation; one beta, declared | the instrument and the world are the same program |
| 0.3 | **Write live-path tests first** | smoke + invariants for `alive`, `influence`, `chaos`, `branch`, `consequences`, `answer` | live path coverage > 0 before any dead-path retirement |
| 0.4 | **Repoint the opinion path** | `answer.py` gets a World adapter; `_build_features` extended with within-unit life state (deprivation, employment, hunger, mental health, addiction, isolation, hope) — the IV.2 fix; leakage gate re-run on the new features | a WVS item answered from the living world end-to-end |
| 0.5 | **Port the unique physics, then retire the shells** | `perishability` (1 KB, first), `coupling`, `graph_dynamics`, `event_generation`, `dynamics`-residue → live modules; then repoint `benchmark.py`/`predictions.py`/API; then quarantine `engine/tick/living/advance/diffusion/forces` | no benchmark or API route imports the dead family |
| 0.6 | **Kill the third world** | remove the laptop launchd job (old substrate); world box is the single writer | one live world |
| 0.7 | **Prime goes to work** | all ensembles on 96 cores; storage-box backup verified green and made incremental (18 GB worlds) | a paired 20-repeat ensemble completes < 30 min |
| 0.8 | **Re-measure the physics on the unified loop** | butterfly, FSLE, noise floor, consciousness profile — same preregs, same thresholds | the chaos chapter re-stated on the real system |

## PHASE 1 — BENCHMARK A (WVS) to ≤ 5.0 pp, by the VII.3 loop
First move dictated by IV.2 (within-unit covariates — done in 0.4);
then MSM. Also wire `embedder` into the cascade (D3) — retrieval
quality is currently hashed TF-IDF.

## PHASE 2 — BENCHMARK B (scenarios) to direction ≥ 85% + magnitude ≥ 70%
First move dictated by IV.5: counter-cyclical informal buffer with
shock-type distinction + inactive-but-surviving state; wealth brakes
(consumption scaling, crash losses). Calibrated by II against the ILO
71% moment. Verify all recorded anchors to primary sources.

## PHASE 3 — BENCHMARK C (markets) to Brier ≤ 0.12
Pre-register the ≥50-contract basket; run through the live world +
grounded answer path.

## PHASE 4 — PERFORMANCE (parallel): float32 + Numba per Covasim; target 1 KB/agent, ≥ 5M person-days/sec.

## PHASE 5 — THE TIMELINE AND THE FILTER (after benchmarks exist)
GDELT 2.0 BigQuery daily driver table → 2015 cold start → monthly
snapshots to the storage box (~2.5 TB budget) → assimilation on
unemployment first (unfiltered twin, ESS floor, localization) →
history-friendly backtests from organic pre-event states.

## PHASE 6 — LOCK v1. Freeze. Publish the paper: three benchmark
tables, full parameter provenance, every baseline, every failure mode,
the defect ledger, and the chaos chapter re-measured on the unified
loop.

---

# PART IX — RISK REGISTER

| # | risk | sev | status / mitigation |
|---|---|---|---|
| R1 | Benchmarks grade the dead engine (D1) | **CRITICAL** | Phase 0.4–0.5 |
| R2 | Chaos claims measured on a reduced system (D4) | **CRITICAL** | Phase 0.2 + 0.8 re-measurement; until then all chaos numbers carry the caveat |
| R3 | Determinism broken by unseeded RNG in `memory.spread` | **HIGH** | Phase 0.1; audit past paired results for chronicle contamination |
| R4 | Zero live-path test coverage (611/894 tests on dead path) | **HIGH** | Phase 0.3 — tests before migration |
| R5 | 102 constants, ~52 unsourced, no estimation procedure | **HIGH** | Part VII; provenance classes mandatory in the paper |
| R6 | Class-GM defect (7 occurrences) recurs in new code | HIGH | standing grep on `.mean(axis=0)` in couplings; named class in review |
| R7 | Class-CF defect (3 occurrences) recurs | HIGH | Standing Rule 1 |
| R8 | Unbounded wealth Gini distorts everything downstream of money | MED | Phase 2 wealth brakes |
| R9 | Country geography oversold | MED | structurally suppressed below noise floor; 15-repeat path priced |
| R10 | Recorded backtest anchors unverified (marked VERIFY) | MED | Phase 2 primary-source pass before any publication |
| R11 | Storage box sized for 900 MB worlds, now 18 GB | MED | Phase 0.7 incremental backup + verify green |
| R12 | Third world on the laptop (old substrate, daily launchd) | MED | Phase 0.6 kill |
| R13 | 8.3B claim unsupportable full-fidelity | LOW | dynamic-rescaling architecture per Covasim precedent; claim worded as instantiation-on-observation |
| R14 | Single writer (world box) SPOF | LOW | verified off-site backup; archive of prior worlds retained |
| R15 | Feed homophily edges frozen at day-0 stances; static online status | LOW | port `graph_dynamics` (Phase 0.5) to make ties evolve |
| R16 | Temporal ground truth authored, not transcribed (`wvs_paired.py:9-12`; same class in `census.py`/`culture.py` literals) | **HIGH** | founder-gated WVS microdata registration starts now, in parallel; transcription + committed diff; re-run every frozen temporal pipeline; no temporal claim published until closed |
| R17 | Aging frozen, rebirth graph inheritance, presence/mobility/RNG unpersisted (external-found, independently verified 08-19) | **CRITICAL** | Phase 0.0a–0.0d; all long-horizon demographic results carry the caveat until re-run |

---

# PART X — SCOPE: THE FOUNDER'S LIST, ANSWERED ITEM BY ITEM

The test applied throughout — settled during this build and now the
canonical criterion: **not "is it physical" but "does the quantity's
INTERACTION with a person vary."** Gravity is constant; falling is not.
A quantity whose interaction with every agent is identical contributes
zero variance, cannot differentiate two people, cannot fire a
threshold, cannot carry a cascade.

| item | status | where / mechanism |
|---|---|---|
| air / oxygen / breathing | **LIVE** (as interaction) | `flourishing.breath`: continuous physiological tax by air quality and urbanicity — "nobody appreciates oxygen; they are diminished without it" |
| gravity | **OUT** (constant) → **its varying interaction is LIVE** | falls in `health.py`: ~684K deaths/yr, hazard ×2 per decade past 65, occupational height exposure, the elderly decline cascade |
| laws of physics & chemistry | **OUT as substrate; IN as constraint** (deferred) | drug potency → addiction lethality; fertiliser → yield; water treatment → disease. Mechanisms specified, not yet built |
| vegetables / trees / animals / fish | **DEFERRED (ecology)** | yields, fisheries, water tables — sits upstream of `life.cost` food prices; the largest remaining coupled gap |
| storms / weather / heat / cold | **LIVE** | `weather.py`: anomaly field, heat/cold mortality on the frail, heat→aggression, drought→farm wages, storms→firms & savings |
| electromagnetic field between people | **REFUSED as mechanism; the phenomenon is LIVE** | body EM at conversational distance ≈ 10⁻⁶ of Earth's field, no replicated behavioural effect. The real thing — energy passing between co-present bodies — is `contagion.py`: chemosignalling, mimicry, prosody, synchrony |
| neurons / brains | **OUT as substrate; IN as architecture** | the five brain-derived functional signatures are the measured consciousness profile (`integration.py`) |
| atoms / particles / quarks / leptons | **OUT** (zero interaction variance) | Lorenz: three variables suffice for permanent unpredictability; irreducibility comes from coupling, not substrate size — and it was *measured*, not asserted |
| blood | **IN as physiology** | `life.physical`, disease, treatment, mortality |
| social behavior | **LIVE** | fabric (7 tie types), conviction kernel, contagion, crowds/riots, shared attention, feed |
| knowledge & status accumulation | **LIVE** | `knowledge.py`: learning from those who know more; status = wealth+occupation+knowledge+audience; scientists as the 99.5th percentile; discoveries ratchet a permanent commons |
| homeless / criminal / wealthy | **LIVE** | `institutions.class_tick`: homelessness as conjunction; crime = pressure − policing − status; wealth compounds above a buffer |
| hospitals & cancer | **LIVE** | treatment access by country income + personal wealth; the same tumour survivable in Stockholm, fatal in Niamey |
| **the formula of cancer** | **LIVE, sourced** | Armitage–Doll 1954: `incidence(t) = c·t^(k−1)`, k = 6 mutational hits; modulated by addiction (smoking) and deprivation (late presentation) |
| paint / beauty / order out of chaos | **LIVE (metric flagged)** | `knowledge.py` creation: works as negentropy with a decay half-life — the current negentropy metric is degenerate (D-ledger) and is rewritten in Phase 1 |
| migration | **LIVE (fix queued)** | `institutions`: flees deprivation; **must** route through the fabric's diaspora corridors (D4-g) |
| flights | **LIVE** | disease import + the model's only non-convergent cultural channel; destination realism queued (D4-m) |
| cars | **LIVE** | road deaths (leading killer of ages 5–29, hazard peaked in the twenties), commute as tie tax, fuel exposure (branch to be activated) |
| computers / smartphones / media / social media | **LIVE** | `knowledge.connected` by tier (HIC 94% … LIC 28%); `feed.py` as a distinct physics: selected not encountered, asymmetric, arousal-weighted |
| bombs / atomic bombs / wars | **LIVE** | war onset from fear+illegitimacy; conscription; killed young; wrecked firms; nuclear deterrence (×0.08 target weight) and escalation ceiling (×2.2) as declared knobs; nuclear *use* documented but not yet implemented (D4-l) |
| our events as world objects with fading memory | **LIVE** | `memory.py` Chronicle: salience half-life, rehearsal on similar recurrence, spread along ties; fed by news and scenarios; fuller wiring in Phase 0 |
| planets / stars / universe | **OUT as cosmology; IN as experience** (deferred) | transcendence/awe as a meaning source — specified for `flourishing`, not yet built |
| scientists & discoveries | **LIVE** | discoveries raise the global stock permanently for everyone including the unborn — the ratchet no individual can turn |
| sex & pleasures | **PARTIAL** | partnering, relationships, conception, satisfaction live; desire channel live; explicit pleasure economy deferred |
| drugs / addiction / mental issues | **LIVE, level-sourced** | onset ∝ (1−mental), WHO 2.3% level; addiction locks the desire channel and deafens to collective pressure; GBD-anchored mental illness with **emergent, unfitted gradients** (1.8%→18.6% by deprivation; 5.1%→10.6% HIC→LIC) |
| butterfly effect / chaos / entropy | **MEASURED** (reduced system; re-measure in 0.8) | FSLE +0.1321/day; entropy tracked per force; placebo exactly 0.0 |
| multiverse at earthling level | **LIVE (driverless)** | `observe.futures`: one person's life run forward N times → a distribution over their possible lives; `branch.py` at world level |
| manifesting / observation changes reality | **LIVE (unwired)** | `observer.py`: attitude crystallisation (asking hardens conviction and drifts the asked toward their stated position — survey methodology's measured contaminant, used as mechanism) + instantiation-on-observation; the same mathematics as the assimilation filter's ensemble collapse |
| 8.3B | **ARCHITECTED, not full-fidelity** | 37 TB / 6.7 h-per-day measured infeasible; dynamic rescaling (Covasim precedent) + an earthling exists as a distribution until someone looks |
| governments deciding per country | **LIVE** | 194 governments; spend-vs-repress by legitimacy against the inherited norm; welfare IS the safety net |
| always alive, no timers | **LIVE** | `earth1-alive.service`, one world-day per 60 s, ~1,440 world-days per real day, news hourly, SIGTERM-safe, restart-proof |

---

# PART XI — STANDING ENGINEERING RULES

1. **Verify the instrument on a known answer before believing any
   negative result.** Two identical runs must score +1.0. Nine wrong
   instruments this week; every false "impossible" traces to one.
2. **Every control must be able to fail.** A control that cannot fail
   is not a control (three caught).

   **A test that cannot demonstrate failure is not yet evidence.**
   Show the control that makes the check fail, or the green is
   decoration. Two 2026-08-19 near-misses make the point, and both
   passed at the implementation level while failing at the *meta*
   level — which is why neither was caught by reading the code:

   - The **backup timer was green and watching the wrong Earth.**
     `run_backup.sh` protected `data/living/` (the retired 200K
     opinion world) while the live 4M civilization went unbacked. Every
     component worked; the target was wrong. Had Epoch 0 been stopped
     on the strength of that green, the only living world would have
     been halted with no recoverable copy.
   - The **persistence guard derived its expectation from itself.**
     `test_every_world_field_is_saved` compared the saved payload
     against `dataclasses.fields(World)` — but the serializer *built*
     the payload from that same call. A mirror, not a control; it could
     never have failed on a new field. The cure was a **declared**
     policy the test checks against independently.

   Applies for the rest of the program — calibration, assimilation,
   scenarios, WVS, market forecasting: before believing any green
   result, name the failure case and verify the instrument reports it.
3. **Small before large.** A binary question never needs a full-scale
   run (the ranking answer took 90 seconds at 20K after hours were
   wasted at 200K).
4. **A parameter read back out is not a finding.** Provenance classes
   (SOURCED / ANCHORED / ESTIMATED / ASSUMED) accompany every reported
   magnitude.
5. **Calibrate by MSM / Indirect Inference with pre-registered
   moments. Never by eye.**
6. **One engine, one path, one world.** The instrument and the product
   run the same program. Research on prime; iteration local; the world
   box is the single writer.
7. **No result without mechanism and citation** (the VII.3 loop,
   steps 2–4).
8. **Grep the named defect classes in review**: Class GM (global mean
   where local belongs), Class CF (unfalsifiable control), Class IP
   (input echoed as finding).
9. **Report failures as solved problems.** The founder's standing
   instruction: find the solution, verify it honestly, then report the
   working state with receipts — never a negative result as a
   deliverable, and never a cheated positive. **Rule 9 is stated in
   full as Part XI.A below, which is its canonical form.**

---

# PART XI.A — EARTH-1 V1: NO DEAD-END RESULTS

*The scientific operating doctrine. Founder instruction, 2026-08-19,
verbatim. This is the canonical text; `CLAUDE.md` and every benchmark
plan carry copies so it cannot quietly disappear. If they disagree,
this one governs.*

> **Do not stop at "the model failed." Your job starts there.**

A benchmark miss is not an acceptable final deliverable. It is a
diagnostic result that starts the next engineering/research cycle.

When any experiment, calibration, benchmark, scenario backtest,
prediction task, module validation, or acceptance gate misses its
predefined target:

1. **Record the result exactly.** Never hide, soften, delete, or
   rewrite a bad result.
2. **Verify the instrument first.** Check ground truth, provenance,
   units, leakage, implementation correctness, persistence, state
   continuity, metric visibility, benchmark design, and whether the
   tested code is actually the production/canonical path.
3. **Explain causally why the result occurred.** Trace the output back
   through the code and quantify which mechanisms, parameters,
   datasets, or missing channels account for the error.
4. **Research before inventing.** Search peer-reviewed academic
   literature, authoritative technical reports, established
   simulators, government models, white papers, reference
   implementations, and relevant empirical datasets for methods that
   address the diagnosed problem.
5. **Do not make assumptions where established research exists.** Cite
   the methods considered and explain why the selected approach
   applies to Earth-1.
6. **Implement the smallest defensible correction or improvement.**
   Bugs are fixed. Missing empirically justified mechanisms are added.
   Poor parameterizations are calibrated. Weak algorithms are replaced
   with stronger established methods when evidence supports doing so.
7. **Run controlled ablations and sensitivity analysis** so we know
   what actually caused the improvement.
8. **Retest on TRAIN/DEV and iterate** until the predefined
   development gate is met.
9. **Never tune on the final holdout.** Never alter the acceptance
   threshold after seeing holdout results. Never manufacture a pass.
10. **Only freeze a capability** after it passes an untouched external
    holdout or prospective test appropriate to that capability.

The required workflow is:

```
MISS → VERIFY → DIAGNOSE → RESEARCH → IMPLEMENT
     → CALIBRATE → ABLATE → RETEST → PASS → FREEZE
```

A document saying "FAIL" is never the end of the task. It is evidence
preserved in the research record and the beginning of the next
iteration.

**Claude Code must not respond to a bad result with only an
explanation of why it failed.** It must return:

> result → quantified diagnosis → relevant research → proposed
> solution → implementation → new experiment → comparison with
> previous result.

The only legitimate terminal exception is when repeated clean
experiments, correct implementation, strong literature-derived
approaches, appropriate calibration, and untouched external evidence
demonstrate that the underlying hypothesis itself is false. In that
case, preserve the negative evidence and redesign the capability
rather than falsifying success.

Earth-1's goal is not to document avoidable failure. The goal is to
engineer every capability in our wheelhouse until it works, while
preserving a scientifically honest record of every attempt.

## XI.A.1 — How this composes with the rest of the Bible

This doctrine **subsumes and supersedes** the looser phrasings
elsewhere, and it is the operative reading of:

- **Standing Rule 9** (Part XI) — of which this is the full statement.
- **The four-partition doctrine** (§9 of the v4.1 amendments) — steps
  8–10 above *are* the FREEZE / HOLDOUT discipline. "We do not accept
  failure" means the team never stops engineering; it never means the
  team edits the exam after reading the answer sheet.
- **The VII.3 loop** (measure → explain from the code → search the
  literature → adapt → retest) — steps 2–5 here are that loop with
  the verification and research obligations made explicit and
  mandatory rather than customary.
- **The nine-step miss protocol** (§9 of the v4.1 amendments) — that
  protocol is the domain-specific expansion of steps 2–8.
- **Standing Rule 11's prohibitions** — step 9 restates the three that
  matter most under pressure: no authoring the holdout answer into a
  coefficient, no moving a threshold after seeing a result, no hiding
  a failed mechanism.

Where a benchmark tier in Part VI reads ACCEPT / GOOD / WIN, a miss
against ACCEPT **starts** this protocol; it does not end the work.

## XI.A.2 — What a miss report must contain

A miss written up as prose diagnosis alone is an incomplete
deliverable and is to be returned to the cycle. The required artifact
carries, in order:

| section | content |
|---|---|
| **RESULT** | the number, the target, the gap, the prereg hash, the provenance stamp (host, commit, seed, wall-clock) |
| **INSTRUMENT** | what was checked to rule out the instrument — ground truth, units, leakage, persistence, canonical-path confirmation — and the known-answer verification that passed |
| **DIAGNOSIS** | the causal path from code to number, with file:line, and a quantified attribution of the error to mechanisms/parameters/data/missing channels |
| **RESEARCH** | the literature searched, the methods considered, citations, and why the selected approach applies here |
| **IMPLEMENTATION** | the smallest defensible change, and why it is the smallest |
| **ABLATION** | controlled runs isolating what actually produced the improvement, with sensitivity |
| **RETEST** | the new number on TRAIN/DEV against the unchanged gate, compared to the previous result |
| **STATUS** | PASS → eligible for freeze on untouched holdout · ITERATING → next hypothesis named · FALSIFIED → negative evidence preserved, capability redesigned |

---

# APPENDIX A — PARAMETER PROVENANCE CENSUS (summary)

102 constants across ten dynamical live modules
(life 21, institutions 16, contagion 13, flourishing 11, knowledge 9,
weather 9, mobility 7, influence 6, chaos 6, health 4).

**SOURCED (≈10):** Armitage–Doll k=6 · GBD mental illness 13% · WHO
substance dependence 2.3% · UN ICVS crime 4.5%/yr · WHO road deaths
8.3–27/100k by tier · falls ≈684K/yr, ×2/decade past 65 ·
Centola/Granovetter committed-minority 25% · Engel's-law cost shares ·
Rosenstein / Benettin estimator constants.

**ANCHORED (≈40):** named real magnitudes without formal citation —
OECD-range separation 12%/yr · firm exit 8%/yr · finding rate 3.0/yr
(steady-state unemployment identity) · welfare/connectivity/treatment
tiers · TFR→household size mapping · heat+cold ≈5M deaths/yr ·
heat–aggression replication · deterrence and escalation knobs
(explicitly flagged contested) · riot base rate ~1/day worldwide.

**UNSOURCED (≈52):** dominated by coupling gains and clock rates —
every force-coupling coefficient, RELAX 0.25, RESIDUE 0.01, ETA 0.18,
conviction gain, contagion gains, feed multipliers (2.2×, 0.10),
hunger/thirst/breath clocks, hope/curiosity/meaning relaxations,
threshold effect deltas, memory half-life 720d / rehearsal 0.35 /
spread 0.06, discovery and creation rates, gathering shares.
**These 52 are the MSM estimation surface for Phases 1–2.**

# APPENDIX B — MEASURED RESULTS LOG (all 2026-08-18/19, reduced-system caveat where marked)

- FSLE **+0.1321/day**, doubling 5.4 d, 8/8, placebo 0.0 ᴿ
- Butterfly reach: one job loss → 100% of 20K world, divergence
  persisting and growing at day 240 ᴿ
- Consciousness profile: Φ-proxy(state) 0.079, integration present;
  novel coherence **+0.315**; self-model −0.81 (anti-conformity);
  anticipation z=+1.82 (below bar, not claimed); phase transition
  absent ᴿ
- Country noise floor: rank corr ≈ 0 at 258/1,031/3,093 agents-per-
  country (flat) on the corrected full-vector instrument; paired CRN
  estimator raises signal 0.0103 → 0.0359 (3.5×) and corr −0.004 →
  +0.121; 15 paired repeats computed to clear +0.5
- Hormuz global aggregates (75-day, weighted, paired): jobs
  25.1M / 34.4M / 41.7M, destitution 81M / 206M / 525M, deaths
  0.6M / 0.7M / 6.1M — ordered correctly, spreads ±5–29%
- COVID backtest: ranking **PASS** (COVID > GFC > Arab Spring) at 20K
  and 200K; direction 78–100% by event; magnitudes ORDERS OFF (jobs
  cumulative fix in; destitution 881M vs 80M = the informal-buffer gap)
- Emergent, unfitted gradients: mental illness 1.8%→18.6% across
  deprivation quartiles; 5.1%→10.6% HIC→LIC; CVD:cancer deaths 2.8:1
- Household size from TFR: Niger 7.48 vs South Korea 1.97
- Performance: 4.5 KB/agent; 0.58 s/world-day at 200K; 2M world = 9 GB
  live on a 30 GB box; birth of 2M on prime = expected ≤ 10 s (untested
  — prime idle)

ᴿ = measured under `chaos.world_step`; re-measure under the unified
loop in Phase 0.8 before external use.

# APPENDIX C — THE FULL DEFECT LEDGER

Correctness: unseeded RNG in `memory.spread` · shared RNG row
(health u[4]: falls↔treatment) · conviction decay ×0.0 no-op ·
cause-code collision (war=5 vs fall=5) · dual fertility paths ·
newborn planetary-mean blend · migration ignores diaspora ·
`detect_transitions` bypassed live (cooldowns/decay dead) ·
media-hub edges symmetrized · genesis graph discarded ·
EXPERIENCE=age polarized as an opinion · negentropy metric degenerate ·
`housing` dead variable · `couple_life_to_forces` dead ·
fuel branch unreachable · CONSCRIPT_SHARE / NUCLEAR_USE unused ·
flight destination uniform-random · `oldest_days` mislabels salience ·
`_water_access` recomputed 3×/tick · comfort=baseline (only anomalies
can kill) · `farm_share` computed, never used · β = 1.0 / 2.0 / ×2.2
in three places · locality hash duplicated ×4 · `_gini`, `_tier`
duplicated · cascade block duplicated ×2 · `_COHORT_LE_CAP` comment
mismatch (6 vs 12).

Historical (fixed, kept for the paper's honesty section): six
Class-GM occurrences · three Class-CF controls · inverted COVID/GFC
persistence · endpoint-vs-integral grading · suppressed field read as
zero · rent double-count · starvation 99.9%/yr · 22 riots/day ·
heat waves that never killed · permanent-drought water cycle ·
0x71ME / 0x60V hex literals · gathering shares summing to 1.2 ·
top-5 geography artifact · self-compared noise floor.

# APPENDIX D — MACHINE & SERVICE INVENTORY

- **world box** 167.233.77.48 · 8c/30 GB · `earth1-alive.service`
  (4M agents, 60 s/day, news hourly, save 30 min) ·
  `earth1-supervisor.timer` 5 min · `earth1-backup.timer` (verify) ·
  `earth1-daily` disabled (old substrate) · archive:
  `world_200k_day750`
- **prime** 46.4.189.237 · 96c/503 GB · supervisor + jobs manifest ·
  otherwise idle (Phase 0.7 assigns all ensemble work here)
- **storage box** · €4/mo · rsync-over-SSH target of the backup timer ·
  future home of the timeline snapshots (~2.5 TB at 4M monthly)
- **laptop** · iteration only · launchd daily job to be removed
  (Phase 0.6)

---

*This document supersedes every prior status claim, including v3's.
Nothing in it is asserted from memory: every number was measured on
2026-08-19 by direct audit of the repository and machines, or carries
a citation to the source that established it.*

---

## VERSION 4.2 — 2026-08-31 — RULINGS OF THE CALIBRATION WEEK, RECONCILED

**Status: DEVELOPMENT CALIBRATION. Nothing frozen. Every holdout sealed. No validated predictive claim exists.**
**Method: seven days of the XI.A loop on the shipping candidate (C2+ v2 substrate + gradient hardship + income calibration v1), reconciled here against v4.1 text. Where a ruling below contradicts v4.1, this section governs; where it refines, v4.1 stands with the refinement.**

### 4.2.1 — Rulings that override v4.1 text

| # | ruling | v4.1 text overridden | consequence |
|---|---|---|---|
| R-A | **No frontier-LLM comparison, anywhere.** Earth-1 is never scored against, tabled beside, or footnoted with a prompted LLM. The category is the claim; the comparison concedes it. | IV.3 ("coverage for head-to-head comparability with the LLM literature"); VI.A baselines ("LLM coverage numbers from IV.3"); §13 Benchmark C rung (i) ("Earth-1 beats the raw frontier LLM"); §11 task (iv) ("beat the LLM/semantic-neighbor baseline"). | Admissible baselines are only: national-copy and region-copy demographic floors; MrsP/MRP; naive grand-mean; poll or market price at time T; no-change and trend baselines for cross-wave. Task (iv) is re-baselined on semantic-neighbour only. Coverage is still reported — as the abstention statistic, not for comparability. |
| R-B | **No unspent WVS holdout exists.** GOQA-40, the 98-item set and the v1 question holdout are recorded CONSUMED. WVS-7 is calibration/DEV only, forever. | VI.A instrument ("held-out WVS-7 items, pinned CV folds"). | Benchmark A's judges become external estates under the **wave-split rule** (4.2.2). Within WVS-7 the team calibrates hard; nothing there is spent twice. |
| R-C | **Publication order: (1) GlobalOpinionQA absolute score on a fresh sealed split; (2) cross-survey out-of-sample on Pew Global Attitudes, Gallup World Poll, ANES, ESS; (3) resolved belief-causal events via rolling-origin `null_branch()` against poll/market at T.** | Part VI paper ordering A → B → C. | Paper A becomes results (1)+(2); Paper B becomes (3) under the §12 metric set; Paper C is the prospective register, reported as it accumulates. The Technical Architecture (ODD+) paper is unchanged. |
| R-D | **Population-structure ceiling for v1.** The transferable cross-country cohort signal in the 98-item set is measured at ≈0.2–0.3pp above national-copy; no mechanism programme before Epoch 4. Cohort structure is reported as a secondary table under a declared ceiling, with a reliability-weighted readout and coverage. | §11 task (ii) target (≥10% relative error reduction). | Task (ii) target is retained as the **v1.1** gate. v1 reports the measured ceiling as a finding. **Condition:** the ruling is provisional until the within-unit-covariate readout (`living_features`, Phase 0.4's own remedy) has been tested on frozen cells and found inert — XI.A permits a ceiling only after the literature-derived approach has been tried. |

### 4.2.2 — Refinements adopted (consistent with v4.1)

1. **The wave-split rule.** For every external survey estate, the latest wave/round is HOLDOUT (purpose `final_scoring` only, hash committed before any scoring); every prior wave is VALIDATION. For events: everything resolved before the register date is DEV; everything registered forward is PROSPECTIVE. This is the four-partition doctrine (§9) applied to estates the program does not own.
2. **The production ladder.** 20k-agent cycles (~27 s) for CALIBRATE ⇄ RETEST → 200k once, sign-flip check only, no calibration at that rung → FREEZE 0.9 (tagged; physics closed; only operators and adapters may change) → 4M birth as Epoch 4, Epoch 3 archived → HOLDOUT spent once, in one sitting → publish and ship through the one typed adapter, as the same event. This refines Phases 1–3 and 6; it does not replace them.
3. **Substrate-keyed constants.** Any calibration file derived on a substrate carries that substrate's tag; `life.py` refuses to load a constant against a different substrate at birth. Fulfils §15 (parameter registry: train-data hash, introducing commit).
4. **Runner tripwires** (Standing Rule 2 made mechanical): a row with a named change is unrecordable if the working-tree hash equals the previous row's; a changed anchors hash with an unchanged label is illegal; the national-copy floor is computed on **frozen WVS-7 DEV cells and weights**, invariant to any physics change by construction. Seed-replicate σ is a column; no win counts below 2σ.
5. **Fixed-capacity adult-slot semantics declared** (§3): mortality anchors are life expectancy at 18 and the 65+ share on the adult denominator, both derived from fetched WPP/World Bank series, never eyeballed.
6. **Benchmark D is the anchor gate table.** Income (PIP median, $3.00/$4.20/$8.30 headcounts, mean/median), mortality (CDR, LE-at-18, age-at-death, cause-of-death shares from WHO GHE/GBD), labour (ILO unemployment via an explicit `H_unemployment` operator), cascade rate — each a fetched series with id, vintage, sha256. Any unfetchable anchor is BLOCKED_ON_DATA in the row, never authored.
7. **Data beyond GDELT** enters only through the `NewsItem → PerceivedEvent` boundary (§6 event ontology: LLM extracts, never writes the outcome). Market prices are INPUT_EXPOSURE; market resolutions are PROSPECTIVE/EVALUATION_OUTCOME; the Benchmark C claim is Earth-1's Brier improvement over the market at T, with frozen and no-market-channel arms as controls (§13 rung iii).

### 4.2.3 — Drift found and corrected on 2026-08-31

| drift | Bible text | correction |
|---|---|---|
| Cycles ran MISS → DIAGNOSE → CALIBRATE → RETEST without RESEARCH or ABLATE. | XI.A steps 4–5, 7; Rule 7 | Every named change now emits the XI.A.2 miss report (template in `ops/alive/CYCLE_TEMPLATE_XI_A.md`); RESEARCH and ABLATION are required sections; retroactive reports owed for the hazard restructure, WANT fold, external-channel RR, income calibration v1. |
| Moments matched one at a time by fixed-point iteration. | VII.1 (MSM, pre-registered moment set, fitted jointly) | Moment set declared in `ops/alive/MOMENTS_v1.md` before the next calibration cycle; serial fixed points are permitted as diagnostic steps but the freeze package carries one joint MSM fit over the declared set with the full parameter vector and provenance classes. |
| Benchmark A gated on region-copy only. | VI.A tiers (ACCEPT ≤7.0 / GOOD ≤5.0 / WIN ≤3.5 pp; beat naive and MrsP); §11 five tasks | Freeze package carries the five-task table; level is reported against ACCEPT and against MrsP (8.56pp) with excess MAE; unrun tasks marked NOT RUN, not omitted. |
| Retrodiction planned outside the §12 metric set. | §12 | Result (3) reports direction, magnitude vs strongest causal baseline, geography Spearman, timing, 80%-interval coverage, discrimination above noise, paired placebo ≈ 0; V1 gate ≥3 resolved events across ≥2 domains; domain causal adapters before any backtest paper. |
| Module ablation absent. | §2 acceptance test (iv) | For every mechanism touched this week, one row with the mechanism disabled on the benchmark built to exercise it. |
| Phase 0 treated as closed. | 08-22 audit: 0.4 PARTIAL, 0.5 PARTIAL, 0.7 OPEN, 0.8 NOT DONE | 0.5's benchmark-module repoint (`benchmark.py`, `predictions.py` off `engine`) is a **freeze prerequisite**; the Benchmark B DEV retest must run through the clean `branch`/`backtest_run` path and its manifest must say so. 0.8 re-measurement is scheduled after FREEZE on the frozen executable. 0.7's incremental backup remains OPEN by ruling. |

### 4.2.4 — Loop position on the date of this amendment

CALIBRATE ⇄ RETEST on development evidence. Living baseline: income, poverty lines, CDR, 65+ share, cascades green through 200k; mortality age structure mid-loop (external channels at DIAGNOSE). Population fidelity: substrate at RETEST-green; structure at provisional ceiling pending the `living_features` cycle. Benchmark B: RETEST owed under candidate physics. Experience Loop: v0.2 at RETEST with the informed-non-learner control as primary gate. Nothing at PASS on the full board; nothing at FREEZE.

### 4.2.5 — Claim ladder, unchanged

Current public claim remains: "a living, branchable synthetic civilization kernel with material, biological, social, institutional and memory state." Nothing in this amendment advances it. The next rung is earned only by the HOLDOUT-once spend after Epoch 4.

*Every number in this section was measured on 2026-08-27 → 08-31 on the cycle runner or prime and is recorded with provenance in `ops/alive/CALIBRATION_CYCLES.md`.*

## v4.2.2 — refinement 9 (founder-ruled 2026-09-01)
All questions route through the multiverse adapter (earth1/adapters/multiverse.py):
real branches via null_branch(), force-distance readout, class noise-floor
abstention, p_model-only scoring. Class-specific code is limited to the outcome
injector (data/question_classes.json, one XI.A.2 report per class).
