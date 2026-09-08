# Earth-1: a deterministic civilization model with no language model in the loop

**Earthling Labs** · Version 1.0 · 8 September 2026 · Epoch 3 / freeze-0.9
Correspondence: pietro@vaultik.com
Typeset preprint: https://claude.ai/code/artifact/1b0fcfb0-9555-428f-b0cd-5e24de861929

*Census-grounded agents, an eight-force behavioural grammar, and falsifiability as an
architectural property rather than a methodological aspiration.*

| | |
|---|---|
| Population frame | 194 countries, 216-cell joint |
| Verified scale | 10^8 agents, flat per-agent cost |
| Runtime LLM calls | 0, by architecture |
| Determinism | 3 independent paths, one world hash |

---

## Abstract

Computational models of society currently fall into two families. Classical agent-based models are cheap, inspectable and tractable, but behaviourally thin: their agents follow heuristics or fixed equations that were chosen by the modeller. Agent societies powered by large language models are behaviourally rich and demographically groundable, but they are expensive, conditional on the particular model that generates them, and — by the explicit statement of their own authors — best read as hypotheses to be examined empirically, "not as evidence about real societies" (Guan et al., arXiv 2506.12078v2). We describe EARTH-1, a deterministic civilization model that occupies a third position. It contains no language model anywhere in its runtime path, and its distinguishing property is not fidelity but exposure: it can be wrong on the record. Agents are drawn from a census-grounded five-dimensional joint population across 194 countries and advanced by an eight-force behavioural grammar under a deterministic tick; every claim is produced as a contrast between a perturbed branch and a null branch of the same world, and every gate is fixed by ruling before the run. We report determinism verified along three independent paths to a single world hash; a material board that reproduces global poverty, income, mortality and age structure at 200,000 agents and again at twenty times that scale; flat per-agent cost from one million to one hundred million agents; and a calibration ladder with sealed judges. We report the failures at the same resolution as the successes. The opinion readout sits roughly two percentage points behind a region-copy baseline, and the aggregate event-direction gate failed at 40% against an 80% target.

## 1. Introduction

The computational study of societies has divided into two research programmes that trade against each other along a single axis. The older programme, agent-based modelling in the Schelling–Sugarscape lineage, buys tractability with behavioural poverty: rules are hand-specified, parameters are chosen subjectively, and the interesting question — why an agent does what it does — is answered by fiat. The younger programme replaces the rule with a language model. Agents acquire memory, stated reasons, context sensitivity and something that reads as personality, and the resulting societies reproduce recognisable social regularities. That programme has recently reached genuine scale: the comparison system for this paper, Light Society, simulates over one billion agents by combining prompt caching, knowledge distillation to lightweight surrogates, and a mixture-of-models routing engine, against a prior state of the art at most 10^7 agents, with many earlier studies requiring dozens of GPUs and weeks of computation to reach 10^6.

That achievement is real, and the honesty of its authors about what it does not establish is the starting point for this paper. Three limitations are stated in their own text rather than imposed from outside. First, results are conditional on the underlying language model: swapping the communication language between Chinese and French moves the stance-change rate by up to 4.7 percentage points, with a sign that depends on the topic. Second, the reproducibility claim is a coefficient of variation below 0.01% across five runs — statistical stability of an aggregate, which is a different property from determinism, and one that cannot support bit-level replay or a clean contrast between two versions of the same world. Third, and most consequentially, the outputs are offered as hypotheses for empirical examination rather than as evidence about real societies. A model that declines to be evidence cannot be falsified by the world, and a model that cannot be falsified by the world accumulates capability without accumulating credence.

EARTH-1 takes the third position. It is a deterministic model of human civilization with no language model in the runtime path, built so that its claims are scoreable against reality and, when they are scored, frequently wrong in ways that can be named. The thesis of this paper is that the absence of a language model is not a limitation requiring apology but the enabling condition for three properties that the LLM-agent family cannot presently offer together. Determinism: the same seed produces one identical world hash along three independent paths, so a perturbed branch can be contrasted against a null branch under common random numbers and the difference attributed to the perturbation rather than to sampling. Cost: at 981 bytes per agent, one world-day of a four-million-agent world costs sixty seconds on a single 48-core machine, against a token-equivalent of 2.4 billion tokens per world-day for one prompt per agent per day — roughly $2,400 at a price below frontier rates. Persistence: because a world-day is cheap and replay from the hash-chained ledger is bit-identical, one world has now run continuously past day 16,860, which is a regime that per-token economics does not reach.

Two constraints govern how these claims are stated. The project's governing document forbids benchmarking EARTH-1 against frontier language models, and no such comparison appears here; the claims advanced are structural — determinism, falsifiability, cost, persistence, and having been scored against reality at all — not claims of superior accuracy over any language model. And EARTH-1 is currently measured at 100 million agents, an order of magnitude below the billion-agent demonstration of the comparison class. Where this paper claims an advantage it is in what the numbers are exposed to, not in how large or how accurate they are.

The contributions, each tied to a measured result, are as follows.

1. **Determinism as a verified property, not an aspiration.** Six of six checks pass; same-seed rebirth, save/load continuation and flag-on-baseline converge on one identical world hash (49bb7d1d949f28f3), with branch common-random-numbers and historical rebirth passing independently.

2. **A census-grounded joint population substrate.** 194 countries, each represented by a 216-cell five-dimensional joint over sex, age band, education, income and urbanicity, fitted over pooled donors; the joint beats an independent-marginal baseline by 24.8% on withheld cells at p ≤ 2.4 × 10⁻¹³, with per-agent census weighting to a world population anchor of 8,140,897,523.

3. **A material board scored against observed statistics, misses included.** Poverty at $8.30/day 45.9% against 46.1% real; median income $9.61/day against $9.27; crude death rate 0.0073/yr against 0.0076; 65+ adult share 14.1% against 13.6%. The named misses are poverty at $3.00/day (16.8% against 10.4%) and unemployment (approximately 9.7% against 4.8%, a factor of two over).

4. **Scale at flat per-agent cost, with scale invariance demonstrated.** From one million to one hundred million agents, per-agent memory moves from 975.2 to 981.6 bytes — flat to 0.7% across a hundredfold range — with tick cost scaling as n^1.07; 100 million agents are born in 756.7 s and advanced at 924.8 s per world-day within a 324.5 GB peak on one 48-core AMD EPYC 9454P. The day-5 census is identical across a 500-fold population range, the poverty line varying by 0.08 percentage points.

5. **An opinion readout scored against surveys and reported as a miss.** Across 21,776 (item, country) cells under leave-one-country-out, majority agreement with the real human majority is 83.5% and median distance is 3.78 sampling errors; but mean absolute error is 11.84 pp on 98 held-out WVS items against 9.70 pp for a region-copy baseline, and 12.01 pp against 10.31 pp on 468 Pew-frame items. EARTH-1 beats only the naive baseline and sits behind region-copy. Replication on 110 never-labelled items (11.20 pp against 9.81 pp) confirms that the deficit is not item selection.

6. **Frozen-forecast retrodiction under sealed judges, including a failed gate.** Arab Spring material-stress geography correlates with observed protest counts at Spearman +0.168 (p = 0.022); the 2008 unemployment response is 0.64× the real delta and the 2020 response 3.5×; the SVB contagion event was under-called at p = 0.302 and resolved yes; the Truss gilt crisis produced a clean physics abstention, the shocked branch being indistinguishable from control. The aggregate event-direction gate failed at 40% against an 80% target, and physics was frozen carrying that failure rather than patched around it.

7. **A pre-registered counterfactual that failed on its own terms and converted the failure into named mechanism.** For UKR-2022, output was frozen before any outcome data was fetched; against the sealed judge the model overshot food-insecurity magnitude by 8.5× (+326M against +38.5M real), showed no geographic signal (Spearman −0.137) and matched one of five top countries. A written prior sealed before the fetch predicted all three failures and their cause.

8. **Persistence that measurably beats not-persisting.** The experience loop beats an informed non-learner — a control given identical observations each cycle but no memory — by 4.8× on late-window score (+1.51 log-CRPS, p = 3 × 10⁻⁵, positive in 16 of 16 worlds) and a frozen model by 8.7×, at 0.963 interval coverage, with bit-identical replay from the hash-chained ledger.

## 2. Earth-1 is not an agent swarm

The distinction drawn in this section is architectural, not a matter of degree. The dominant design for large-scale social simulation instantiates N reasoning entities, gives each a natural-language profile and a policy realised by a language model, dispatches their interactions through an event queue, and aggregates the emitted actions into a population-level statistic. Light Society is the mature form of that design: one billion agents on a scale-free network, profiles drawn from World Values Survey records, and a distilled surrogate standing in for the teacher model wherever full inference is infeasible. Earth-1 does not do a smaller version of this. It does not instantiate a population of reasoners at all.

We should be plain about what is therefore not being claimed. Earth-1's largest measured configuration is 100M agents — an order of magnitude below the billion-agent systems, not above them. There is no per-agent natural-language reasoning anywhere in Earth-1: agents do not deliberate, do not emit text, and hold no beliefs expressible as sentences. Nothing in this section is a claim that Earth-1 is more accurate than a language-model-driven simulation; the project's governing document forbids benchmarking against frontier language models, and the claims below are structural.

What Earth-1 evolves is a single civilization whose population is a state manifold: a census-grounded joint distribution instantiated in memory at 981 bytes per agent, with behaviour expressed as arithmetic over that state. An individual is an addressable view of the manifold rather than a separately-reasoned process. In a swarm the agent is the unit of computation and the society is the sum of its outputs; in Earth-1 the civilization is the unit and the person is a coordinate within it.

### 2.1 The substrate is a population, not a roster

Earth-1 carries 194 countries. Each holds a five-dimensional joint over sex (2), age band (6), education (3), income (3) and urban residence (2) — 216 cells per country. The provenance of that joint is declared rather than assumed: 63 countries are survey-measured, with WVS-7 microdata supplying the education and income margins; the remaining 131 are tier-fallback, constructed by income-tier donor pooling. Age, sex and urban margins are census-derived for all 194. The joint itself is drawn by iterative proportional fitting over pooled donors, which beat an independent-marginal baseline by 24.8% on withheld joints at p ≤ 2.4e-13 — the correlation structure between education, income and residence is measured, not assumed away. The adult age pyramid is derived from stable-population density using each country's own Gompertz survival rather than a parametric draw.

This is a different object from a profile pool. Where a swarm samples agent personas from a fixed set of survey records — Light Society draws from a pool of 10,000 — Earth-1 instantiates a country's joint and then weights it: each agent's weight is its country's census share divided by its share of the instantiated population, so every global figure the engine reports is population-true against a world anchor of 8,140,897,523. A global poverty rate is an estimate of the world, not of the sample that happens to be resident in memory.

The signature of a manifold rather than a crowd is visible under scaling. The day-5 census is identical at 200k, 1M, 4M and 100M agents, the poverty line varying by 0.08pp across a 500-fold range in population; a 4M board reproduces the 200k board across every material line. Adding agents raises the resolution at which the same distribution is sampled; it does not change what is being sampled. This is the opposite scaling signature to a swarm, in which demographic effects sharpen and individual variability diminishes as the population grows — a property of averaging noisy reasoners, and a useful diagnostic that the two systems are not the same kind of thing. The substrate's principal weakness is equally structural and is registered as a defect: two-thirds of country joints are tier-fallback rather than survey-measured, and there is at present no subnational geography and no household frame.

### 2.2 A universal grammar with contextual activation

Behaviour in Earth-1 is generated by eight forces. The grammar is universal: the same eight act on every agent in every country, in every domain the engine is asked about. What is contextual is activation — which forces are live, and with what weight, given the state of the agent and of the world around it. The update rules, their fitted constants and the readout that maps state to expressed opinion are outside the scope of this description.

The architectural consequence of that split is the one worth stating. Because the grammar is fixed and only its activation varies, domain-specific models are configurations of one civilization rather than separate simulators. A swarm achieves generality by re-prompting: a new question means a new template, a new operator, often a new distilled surrogate. Earth-1 achieves it by re-activating an invariant grammar over a world that already exists. Post-hoc attribution follows for free — after a shock one can ask which force moved, and where, as a property of the run rather than as an interpretation of generated text.

Two further consequences follow from there being no language model in the runtime path. First, there is no model-dependence axis: Light Society's authors are explicit that their results are "conditional on the underlying language model", and report that swapping the communication language moves the stance-change rate by up to 4.7 percentage points with topic-dependent sign. Earth-1 has no such parameter, and its determinism is exact rather than statistical — three independent paths, same-seed rebirth, save/load continuation and flag-on-baseline, converge on one identical world hash. Second, opinions exist only where a readout is applied to state, and that readout is currently a miss: on 98 held-out WVS items Earth-1 records 11.84pp mean absolute error against a region-copy baseline's 9.70, and on a 468-item Pew frame 12.01 against 10.31. Earth-1 beats a naive baseline and is roughly two points behind region-copy. A replication on 110 never-labelled items returns the same verdict, so the miss is not item selection.

### 2.3 Persistence rather than instantiation

A swarm is instantiated per experiment. Its population is born for the run, evolved for a fixed number of rounds, read out and discarded; nothing in round one of the next experiment remembers the last. Earth-1 runs a 4M world continuously past day 16,860, at roughly one world-day per sixty seconds, publishing a hash-chained event stream as it goes. Agents age, die and are born inside a history that accumulates. Persistence is what makes counterfactual work well-posed: a question is asked as a branch against a null continuation of the same world under common random numbers, so the contrast isolates the injected event rather than the difference between two separate instantiations. Persistence also has a measured cost, registered as an open defect — a world warmed on ninety days of real news ticks substantially slower than a cold one, with memory spread dominating the tick.

### 2.4 Emergence as a measurement

The practical payoff of all three properties is that emergence becomes something one measures rather than something one narrates. Because the state is arithmetic and the world is deterministic, the branch-null difference is attributable to the injection alone; run-to-run stability, however tight, is a weaker guarantee than a reproducible hash. And because the object measured is state rather than generated discourse, a null result is a legal outcome. When a UK fiscal shock was injected at full fidelity, the shocked branch was indistinguishable from control — a physics abstention traceable to a named absence, no bond or pension channel. A system that narrates emergence cannot return that answer; it will always produce a story.

The current accounting is not flattering. The aggregate event-direction gate failed at 40% against an 80% target, and the physics tag was frozen carrying that failure alongside five named regressions. The argument of this section is not that Earth-1 is currently right. It is that a civilization held as state, rather than as a swarm of reasoners, can be wrong in a locatable place.

## 3. Social structure, transmission, and the measurement of emergence

The claim most often made of agent-based societies, and least often demonstrated, is that collective behaviour *emerges* rather than being written in. The claim is hard to establish because the two candidate explanations for any neighbour-correlated pattern — genuine transmission between agents, and a shared response by similar agents to a common input — produce the same signature in aggregate statistics. A model that cannot separate them can only narrate emergence. This section states what EARTH-1's social layer does, what has been verified in code, what has been measured, and what has not.

### 3.1 The social layer is a graph over people, not a channel over aggregates

Each agent holds ties across several relationship channels — household, colleagues, neighbours, friends, weak ties, and a small set of high-degree media hubs — with channel-specific weights and degrees. The graph is constructed once at genesis with homophilous structure, and it is a genuine object rather than a summary statistic: every social computation on the daily path reads a *living view* of it, rebuilt after each day's deaths, migrations and job changes, so that the deceased retain their edges as history while carrying no weight in current dynamics.

Two properties of the construction matter for the emergence question and are stated here because they bound what can later be claimed. First, the graph's *structure* is drawn at genesis and is not itself grown; what changes over time are tie weights and a limited amount of rewiring. Second, the graph is homophilous by construction — people are connected preferentially to people like them — which means neighbour similarity exists at t = 0, before any dynamics have run. Any observed correlation between connected agents must therefore be decomposed before it can be attributed to influence.

### 3.2 Transmission is dyadic and reads a named partner's state

The daily influence operation is not a mean-field approximation. Each agent draws a small number of encounters per day, sampled by tie weight from its living neighbourhood; for each encounter, the agent's force vector moves a fixed fraction of the way toward *that specific partner's current value*, scaled by a susceptibility term that depends on the agent's own condition — age, conviction, mental state, hunger. The quantity moved is read from the partner's state at that moment. This is transmission in the strict sense: information about one agent's state enters another agent's state through a named edge, and the same encounters simultaneously accumulate the evidence from which conviction is updated at the end of the day.

We state plainly what this operator is and is not. It moves each agent toward a partner's value; it contains no term that pushes an agent toward the partner's *pole*. It is therefore contractive in the variance of the force distribution, considered in isolation. EARTH-1 does not contain a designed polarization mechanism, and this paper makes no claim of emergent polarization. An earlier operator in the codebase's history included a pole term intended to expand variance; it is retired, and the descriptive text surviving at the head of that module refers to the retired form rather than the operator the world runs. We note this because the distinction is exactly the sort that separates a measured claim from an inherited one.

### 3.3 Belief is pulled in two directions every day, and that tension is the design

An agent's forces are moved each day by two competing operations. The social operation pushes the agent toward the people it encounters. A second operation computes the force state the agent's *material circumstances* imply — its work, income, reserves, hunger, housing, health — and relaxes the agent toward that target. The material target is returned rather than applied directly, precisely so that the social layer can act as a push and the circumstance as a restoring pull.

This is the structural core of the model's social dynamics: an agent is moved by the people it knows and pulled back by the life it actually lives. A world with only the push saturates to the poles; a world with only the pull is a lookup table on circumstance. The interesting behaviour lives in the tension, and because both operations are arithmetic on state, the tension is inspectable rather than inferred.

### 3.4 The verified feedback structure

Emergence requires closed loops; a one-way pipeline cannot produce it. The following loops are traceable in the daily path and were verified by reading the executed code rather than its documentation.

**Influence and conviction.** Forces move toward encountered partners; those same encounters accumulate agreement evidence; conviction updates from that evidence; conviction weights the susceptibility of subsequent movement. Belief and certainty co-evolve.

**The fabric responds to the conversation.** Tie strengths are updated from the day's interaction — agreement between connected agents strengthens the tie, disagreement weakens it, and a small number of agents find replacements closer to them in force space. The graph the influence operator runs on tomorrow is a function of what that operator did today. We are careful about the claim this supports: the *direction* of the resulting assortativity is written into the update rule, so segregation is designed; only its *magnitude*, arising from the coupling with the influence dynamics, is emergent. The honest control is a variant that offers a single rewiring candidate rather than a choice.

**Neighbourhood deviation feeds back into disposition.** Each day, an agent's deviation from its neighbourhood's mean force updates its underlying dispositional traits — openness, doubt and desire intensity. Traits then shape subsequent susceptibility and the material force target. This is a slow loop from social position back to personality.

**Memory spreads along the graph.** Events enter the world's chronicle with a scope, and that scope grows: an event known to one part of the graph reaches the people who know the people it happened to, with rehearsal consolidating repeated similar events rather than stacking them.

**Institutions close a loop through the population.** Government policy reads the population's aggregate fear and deprivation, chooses between welfare and policing accordingly, and the resulting policy changes the material conditions from which each agent's force target is computed. Belief thus reaches back to belief through the state.

### 3.5 What is designed, what is emergent, and what is not yet separated

The most important discipline in this section is refusing to attribute to emergence anything that is drawn. Two examples establish the standard.

The population's *income* distribution is heavy-tailed. It would be easy, and wrong, to attribute that tail to correlated shocks travelling through the firm structure and the social graph. We measured it: wage kurtosis is 247.01 at birth and 246.76 after 120 days of living. The tail is drawn at genesis, calibrated against an external income statistic, and living changes it by roughly a quarter of one percent. The heavy tail of income in EARTH-1 is designed.

What is *not* designed is the redistribution of accumulated wealth. Over the same 120 days, the ratio of the 99th percentile to the median rises from 11.88 to 29.48, and the share held by the top one percent rises from 0.122 to 0.194, with only 6.5% of agents having experienced any job loss. Concentration grows from the interaction of correlated employment shocks, scarring, and differential capacity to absorb them. Within a generation, wealth concentration is emergent.

We also state a limit on that claim. Across generations, no mechanism in the current engine creates new mass in the income tail: wage is carried forward at replacement without mobility, and accumulated wealth restarts. Long-run inequality in this model is therefore not grown, and we do not present it as such.

Finally, and most consequentially for the emergence question: **the decomposition of neighbour correlation into transmission and confound has not been performed.** Connected agents in EARTH-1 are correlated for at least four reasons — the homophilous genesis graph, the genesis-anchored material target acting on similar people similarly, locality-scoped common inputs such as weather and policy, and genuine dyadic transmission. Only the last is influence. The experiment that separates them is straightforward and is registered as owed: run identical worlds from one genesis seed with the transmission constants set to zero and everything else unchanged, and report the excess force-correlation of tie-connected pairs over degree-matched random pairs, the spatial autocorrelation of each force channel on the graph, and the within-locality variance. The difference between the canonical arm and the zero-transmission arm is the only defensible measure of genuine agent-to-agent influence. Until that difference is reported, this paper claims that transmission *exists*, which the code establishes, and does not claim what fraction of observed social structure it explains.

### 3.6 Emergence as a measurement rather than a narrative

The practical consequence of determinism is that emergence becomes measurable. Because the world is bit-reproducible, a perturbed branch can be run against a null branch under common random numbers, and any difference between them is attributable to the perturbation rather than to sampling. An emergent claim in EARTH-1 therefore takes the form of a paired difference with a seed-level error bar, not a description of what the model appeared to do.

That instrument also returns negative results, which is the harder test. When a fiscal shock was applied to a single country at full fidelity, the shocked branch was statistically indistinguishable from its control, and the report returned an abstention traceable to a named structural absence rather than a narrative about resilience. A system that narrates emergence cannot return that answer; it will always produce a story.

One methodological caveat belongs in this section rather than buried in limitations. The encounter sampler draws from a random stream keyed on the simulation day, independent of the world seed. Replicates that differ by seed therefore differ in their population draw and graph, which is the dominant source of variance, but they do not resample the encounter sequence itself. Error bars on opinion observables consequently under-sample the influence channel specifically. The magnitude of that under-sampling is quantifiable by reseeding that stream, and is registered as owed work.

## 4. Results

### 4.1 Determinism

The first result is not a measurement of the world but a property of the instrument. Earth-1's determinism block records 6/6 passing checks. Three independent construction paths — rebirth from the same seed, continuation from a saved checkpoint, and a flag-on run against its own baseline — converge on a single identical world hash, `49bb7d1d949f28f3`. The branch common-random-number check passes, historical rebirth passes, and the readout adapter reproduces a stored probability, `p_model 0.4311624`, exactly.

This is the load-bearing property of the whole programme, and it is worth being explicit about why. Pre-registration requires that a frozen output can later be re-derived by a third party from the same inputs; otherwise "we committed this forecast before fetching the judge" is an assertion about the authors' conduct rather than a checkable fact. Bit-identity converts the commitment into an artifact. It also gives the branch-versus-null contrast its meaning: because a shocked branch and its control share a random stream, any divergence between them is attributable to the injected perturbation and not to sampling noise, so a null difference is informative rather than merely inconclusive. Section 3.5 contains one such informative null.

It is useful to state the contrast with the language-model-agent comparison class precisely, and no more strongly than the evidence allows. Light Society reports a coefficient of variation below 0.01% across five runs. That is statistical stability under repetition, which is a real and non-trivial engineering achievement, but it is a different property from bit-identity: it does not permit a hash to be pinned to a commitment. The same paper states that its results are conditional on the underlying language model, and reports that swapping the prompt language from Chinese to French moves the stance-change rate by up to 4.7 percentage points with topic-dependent sign. Determinism is a structural difference, not an accuracy claim, and nothing in this section should be read as the latter.

### 4.2 The material board

The population substrate is a per-country five-dimensional joint over sex, age band, education, income and urban status — 216 cells per country across 194 countries. Sixty-three countries are survey-measured on the education and income margins; the remaining 131 are filled by income-tier donor pooling. Age, sex and urban margins are census-derived for all 194. Drawing the joint by iterative proportional fitting over pooled donors beats an independent-marginal baseline by +24.8% on withheld joints, p ≤ 2.4 × 10⁻¹³. Each agent carries a census weight equal to its country's census share divided by its agent share, so global aggregates are population-true against a world anchor of 8,140,897,523 persons.

The material board scores a 200,000-agent true-census world run for 180 simulated days at physics tag freeze-0.9, against anchors fetched independently of the run.

| Quantity | Earth-1 | Real anchor | Status |
|---|---|---|---|
| Poverty, $8.30/day | 45.9% | 46.1% | on |
| Median income | $9.61/day | $9.27/day | on |
| Crude death rate | 0.0073/yr | 0.0076/yr | on |
| Mean age at death | 69.0 | structural band 66.2–71.8 | in band |
| 65+ adult share | 14.1% | 13.6% | on |
| Poverty, $3.00/day | 16.8% | 10.4% | **miss, 1.6× over** |
| Unemployment | ~9.7% | 4.8% | **miss, 2× over** |

Two lines miss, and both misses are attributable to named absent mechanisms rather than to parameter error. The engine has no unemployment-insurance operator, so nothing absorbs a labour-market shock and the unemployment rate runs roughly double reality. The deep-poverty overshoot at $3.00/day sits alongside a well-fitted headcount at $8.30/day, which is the signature of a distribution whose lower tail is too heavy rather than a level error. Both are registered as open defects.

### 4.3 Scale

Memory per agent is flat. Across a ladder of 1M, 4M, 16M, 64M and 100M agents, the per-agent footprint is 975.2, 978.7, 980.4, 981.6 and ~980 bytes respectively — a spread of 0.7% across a hundredfold change in population. Tick cost scales as n^1.07. Birth requires roughly 3.2× the final state size as transient working memory, which is the binding constraint on the ceiling rather than steady-state residency. At 100M agents on a single AMD EPYC 9454P (48 cores), birth takes 756.7 s, one world-day takes 924.8 s, and peak memory is 324.5 GB.

**100M agents is the measured ceiling actually reached, not a billion.** The comparison class runs an order of magnitude larger. This section makes no scale claim over it.

Behaviour is invariant to population size over the range tested. The day-5 census is identical at 200k, 1M, 4M and 100M agents, with the poverty line varying by 0.08 percentage points across a 500× range. The full material board reproduces at 20× the reference population:

| Quantity | 4M × 180 days | 200k board | Difference |
|---|---|---|---|
| Median income | 9.52 | 9.605 | −0.9% |
| Poverty ($8.30) | 45.29% | 45.88% | −0.59pp |
| Poverty ($3.00) | 16.30% | 16.80% | — |
| Crude death rate | 0.00738 | 0.00727 | — |
| Mean age at death | 68.29 | 68.99 | — |

All five lie inside their pre-set gates. The 100M world tracks the 4M control through equilibration, with a poverty gap of 0.01, 0.00, 0.02 and 0.06 percentage points at days 5, 15, 30 and 60, and an identical mean age at death of 67.96 at day 60. Separately, a 4M world has run continuously past day 16,860, at one world-day per 60 seconds, publishing a hash-chained event stream.

The runtime path contains zero language-model calls. At 981 bytes per agent and 60 seconds per world-day for 4M agents, the resource profile is that of a physics code rather than an inference workload. For reference, one prompt per agent per day at 500 input and 100 output tokens over a 4M world would be 2.4 billion tokens per world-day, or about $2,400 per world-day at $1 per million tokens — below frontier pricing — against 16,800 days already run.

### 4.4 Distance from humans

The opinion readout was scored on 21,776 (item, country) cells across three estates, under leave-one-country-out evaluation with named-entity abstention enabled and abstentions excluded from both sides. Majority agreement with the real human majority is 83.5%. Of the 12,669 cells where the survey's own sample size is known, 14.2% are statistically indistinguishable from the survey's 95% sampling noise. Median distance is 3.78 sampling errors and mean absolute error is 10.65 percentage points. The best item family is technology and climate at 2.97 σ, the worst religion and values at 3.91 σ; the best region is Oceania at 2.28 σ, the worst East Asia at 4.66 σ. Signed error is near zero overall, so the residual is a set of family-specific tilts rather than a single systematic bias.

Against baselines, the result is a miss. The registered ACCEPT tier was ≤ 7.0 pp MAE.

| Frame | Earth-1 | MrsP | Naive | Region-copy |
|---|---|---|---|---|
| WVS held-out, 98 items | 11.84 | 11.18 | 12.80 | **9.70** |
| Pew frame, 468 items | 12.01 | 11.06 | 12.02 | **10.31** |

Earth-1 beats only the naive baseline and sits roughly 2 pp behind region-copy on both frames. It does not meet the registered tier. A replication on 110 further WVS items that had never been labelled returned 11.20 against region-copy's 9.81 — the same verdict, which rules out item selection as the explanation and confirms the miss as a property of the readout. At item level the picture is not uniform: on the Pew frame Earth-1 is outright best of the four methods on 64 of 468 items and beats region-copy on 137, with wins concentrated in outgroup trust and material hardship and losses in religion and geopolitics. That pattern maps onto two registered absences — no national religiosity input and no geopolitical-alignment input — which is diagnostic but does not change the verdict. No comparison against frontier language models is reported here; the project's governing document does not permit one.

### 4.5 Historical retrodiction

Each retrodiction follows the same protocol. The world is born at a date T on real archive news, under a mechanical assertion that no input, anchor or news item postdates T. The output is frozen and committed. Only then is the judge fetched, from a source registered by name and location in advance, with its outcome values unread until the commit.

| Event | T | Registered judge | Result |
|---|---|---|---|
| Arab Spring | 2010-12-16 | Protest events by country, 90 days, 185-country overlap | Material-stress geography Spearman +0.168, p = 0.022; fear-channel +0.069, not significant |
| Global financial crisis | 2008-09-14 | Real 2008→2009 unemployment delta | Response 0.64× real (within 2×); direction right, t = 2.2 at 16 seeds, against t = 0.7 at 5 reps |
| COVID-19 | 2020-02-28 | Real unemployment delta | Response 3.5× real (within 5×); direction t ≈ 18 |
| Silicon Valley Bank | 2023-03-08 | Contagion to ≥2 further banks within 30 days | p_model 0.302; resolved YES — **under-called** |
| Truss gilt crisis | 2022-09-22 | Branch versus control at full fidelity | **Physics abstention**: shocked branch indistinguishable from control |
| Sri Lanka | 2022-03-31 | Government fall within 120 days | p_model 0.3985; government fell — **under-called** |

**The aggregate event-direction gate failed: 40% against an 80% target.** Physics was frozen at 0.9 as a "freeze-with-named-regression", the tag carrying that failure plus five named regressions rather than a fix that would have reopened the loop.

The individual rows are informative about why. COVID's 3.5× overshoot is expected of a model with no furlough state. On SVB every material line abstained while the United States was nonetheless the top force mover at twice the runner-up — right about the fear, missing the plumbing, there being no interbank or deposit channel. The Truss row is the cleanest of the negatives: at full fidelity the shocked branch is indistinguishable from its control, because a UK fiscal crisis transmitted through gilts and pension collateral is simply invisible to an engine with no bond or pension channel. Determinism is what makes that null a result rather than an absence of one.

The pre-registered UKR-2022 counterfactual was frozen and committed before any outcome data was fetched, then judged against the GRFC acutely-food-insecure database over the 48 countries assessed in both 2021 and 2022. It failed on all three registered criteria: magnitude 8.5× over (+326M modelled against +38.5M real), geography Spearman −0.137 (no signal), and top-five overlap 1/5. The written prior sealed before the fetch predicted all three failures and named the mechanism — no substitution, no subsidies, no stock drawdown. Reality confirmed the named damper: Egypt's real change was exactly zero, absorbed by its bread subsidy.

### 4.6 Learning

The experience loop is evaluated against two controls. Against a frozen model it improves late-window score by 8.7×. The demanding comparison is the second: an *informed non-learner*, given the same observations every cycle but denied persistence across them. Against that control the loop still wins by 4.8×, with a log-CRPS gain of +1.51 at p = 3 × 10⁻⁵, positive in 16 of 16 worlds. Calibration coverage is 0.963, and the loop remains honest under deliberate misspecification in 4 of 4 tests. Replay from the hash-chained ledger is bit-identical.

The informed non-learner is the control that matters because it removes the trivial explanation. A frozen baseline can be beaten simply by being given fresh information; that result would say only that information helps, which is uninteresting. Holding the information stream identical and removing only the carry-forward of state isolates persistence itself as the source of the gain. It is a control the loop could straightforwardly have failed, and the fact that it did not is the claim being made.

## 5. Falsifiability as an architectural property

A simulation output is not automatically evidence. For it to bear on a claim about the world, it must have been possible for the run to be wrong in a manner specified before the answer was known. Most properties commonly reported for large social simulations — population size, throughput, behavioural richness, run-to-run stability — are orthogonal to that requirement. Earth-1 treats it as the primary design constraint, from which the engineering choices follow rather than the reverse. Determinism is not pursued as a performance property; it is pursued because nothing downstream of it works without it.

### 5.1 The chain from determinism to evidence

The argument runs in four links, each of which is inert without the one before it.

*Determinism.* Identical inputs yield an identical world, and the claim is verified along three independent execution paths — same-seed rebirth, save/load continuation, and flag-on-baseline — which converge on a single world hash, 49bb7d1d949f28f3. Six of six determinism checks pass, including branch-contrast and historical rebirth; the scoring adapter reproduces a model probability of 0.4311624 exactly. No component of the runtime path depends on a third-party inference service whose behaviour may drift between invocations.

*A frozen artefact.* Because a run reproduces exactly, its output can be committed as a fixed object with a hash. "The model said X" becomes a checkable assertion about a particular artefact, not a summary of a distribution that would have to be regenerated — and might regenerate differently — in order to be inspected.

*Pre-registration.* Once the artefact is fixed, the claim, the gates, and the scoring procedure can be written and sealed while the answer is still unknown. In historical retrodiction, a world is born at date T from archive material under a mechanical assertion that no input, anchor, or news item postdates T; the output is then frozen and committed.

*A judge fetched afterwards.* Only at that point is the outcome data retrieved. The judge is registered beforehand by name and location, with its values unfetched, and the result is scored once.

It is the ordering, not any individual step, that does the work. Under this sequence the model has no move available after the outcome is visible: it cannot reselect the metric, the horizon, the country set, or the threshold. Retrospective scoring, by contrast, leaves the space of admissible framings open until after the answer is in hand, and a sufficiently large space always contains a favourable framing.

### 5.2 Why statistical reproducibility cannot substitute

Light Society reports a coefficient of variation below 0.01% across five independent billion-agent runs — a genuine and non-trivial result at that scale. But it is a statement about the dispersion of a distribution, not about the identity of an object. Every run is a fresh draw, so there is no artefact to freeze and consequently nothing for a pre-registration to attach to. The strongest claim such a measurement supports is the one its authors make: that a conclusion drawn from a single run is not an artefact of stochastic seeding. The same paper is explicit that its results are conditional on the underlying language model — a Chinese-to-French swap in communication language shifts the stance-change rate by up to 4.7 percentage points, with the sign depending on the topic — and concludes that outputs are best read as hypotheses to be examined empirically rather than as evidence about real societies. That is the correct claim for that architecture.

Nothing in this comparison concerns accuracy, and no accuracy comparison against language models is made in this paper; the project's governing document forbids it. Nor is it a claim of scale: Earth-1's measured ceiling is 100 million agents, an order of magnitude below one billion. The claim is narrower and structural — that a frozen artefact plus a sealed judge is a mechanism by which a run can be held to a prior commitment, and that a variance statistic, however small, is not.

### 5.3 The governance that operationalises it

A chain of this kind fails through procedure rather than through theory, so the procedure is codified. One named change per cycle, so that any movement in the gates is attributable. Gates fixed by ruling before the run. VOID reserved for defects in the measuring instrument and never invoked for an unwelcome result. Sealed judges registered by name and location, with outcome values unfetched until the model output is committed.

Such rules are only tested when they cost something. The physics froze at version 0.9 as a freeze-with-named-regression: the aggregate event-direction gate had failed at 40% against an 80% target, and the release tag carries that failure, together with five named regressions, rather than a repair that would have reopened the loop and invalidated the frozen substrate. A registered substrate defect — an inverted urban flag reaching two physics consumers — was likewise recorded and deliberately left unpatched, scheduled as a later cycle, because the physics was frozen. Both decisions are locally uncomfortable and structurally necessary. A gate that may be revised once the result is visible is not a gate.

### 5.4 A worked example: the UKR-2022 counterfactual

The 2022 grain-shock counterfactual was frozen and committed before any outcome data was fetched, against a judge registered in advance: the GRFC acutely-food-insecure database (sha 44de7226), restricted to the 48 countries assessed in both 2021 and 2022. The model lost on all three registered dimensions. Magnitude overshot by 8.5x (+326M modelled against +38.5M real). Geography carried no signal at all, at Spearman -0.137. Top-5 overlap was 1 of 5.

Sealed before the fetch, the founder's written prior had predicted all three failures and named the mechanism responsible: no substitution, no subsidies, no stock drawdown. Reality then confirmed the named damper directly — Egypt's real change was exactly zero, absorbed by its bread subsidy. The run is therefore, simultaneously and without contradiction, a triple failure against its own registered gates and a successful test of a stated mechanistic hypothesis. Only the ordering makes the second reading admissible. Had the prior been written after the numbers were known, it would be a narrative rather than a prediction, and the identical text would carry no evidential weight whatsoever.

### 5.5 Enumerable absence versus diffuse error

This is the property that distinguishes the object being built. Earth-1's misses resolve, one by one, onto absent operators that can be named in advance of any repair. Unemployment runs roughly twice over (about 9.7% against a real 4.8%) and there is no unemployment-insurance operator. The SVB question was under-called at a model probability of 0.302 on an outcome that resolved YES, with every material line abstaining while the United States emerged as the top force mover at twice the runner-up — right about the fear, missing the plumbing, which is to say no interbank or deposit channel. The Truss gilt episode produced a physics abstention, the shocked branch indistinguishable from control, which is precisely what a model with no bond or pension channel should produce.

The opinion readout is a miss and is reported as one. Against a region-copy baseline it is behind by roughly two percentage points: 11.84pp MAE on 98 held-out WVS items against 9.70, and 12.01pp on the 468-item Pew frame against 10.31, replicated on 110 never-labelled items at 11.20 against 9.81. Its worst family, religion and values at 3.91 sampling errors, corresponds to an input the substrate does not carry.

The defect list is finite, written down, and each entry constitutes a testable prediction about what should change once the operator is added. A model whose errors are distributed across a learned parameter set offers no comparable handles: it is wrong without being wrong about anything in particular. Falsifiability, on this account, is not a virtue claimed for the results. It is a property of the architecture, and it is what makes the failures usable.

## 6. The economics of a language-model-free civilization

Earth-1 makes zero language-model calls in its runtime path. This is not an efficiency optimisation applied to an otherwise prompted architecture; it is the architectural premise from which the engine's cost structure follows. The consequences are measurable, and this section reports the measurements, the arithmetic that follows from them, and — with equal weight — what the design does not buy.

### 6.1 The measured memory and time laws

Two laws govern the engine's resource behaviour, both measured on a frozen physics tag verified by a configuration gate.

The memory law is flat per agent. Across a ladder of 1M, 4M, 16M, 64M and 100M agents, the resident footprint measured 975.2, 978.7, 980.4, 981.6 and approximately 980 bytes per agent respectively — flat to 0.7% across a hundredfold change in population. Total memory is therefore linear in population with a constant of roughly 981 bytes, and the constant does not drift with scale. Birth is the peak, not the steady state: constructing a world requires about 3.2 times the final state as working memory, so the machine is sized by initialisation rather than by the tick.

The time law is mildly superlinear: the tick scales as n to the power 1.07. At the largest measured configuration — 100M agents on a single AMD EPYC 9454P with 48 cores — birth took 756.7 seconds, a world-day took 924.8 seconds, and peak memory reached 324.5 GB. At 4M agents, one world-day takes 60 seconds on one 48-core box; a 4M world has been running continuously past day 16,860 on that budget, publishing a hash-chained event stream as it goes.

A third measurement bears on whether scale is even required for aggregate claims. The day-5 census is identical at 200k, 1M, 4M and 100M agents, with the poverty line varying 0.08 percentage points across a 500-fold population range, and a 4M world run for 180 days reproduces the 200k reference board on every gated line. Census weighting makes each agent carry its country's population share, so global figures are population-true at any sample size.

### 6.2 The token-equivalent of a prompted tick

The relevant counterfactual is not what a prompted architecture actually spends — its designers work hard to spend less — but what the same simulated day would cost if each agent's daily decision were a generation. At one prompt per agent per day, with 500 input and 100 output tokens, a 4M world consumes 2.4 billion tokens per world-day. Priced at one dollar per million tokens, below frontier pricing, that is about 2,400 dollars per world-day. The engine's own cost for the same day is 60 seconds of one 48-core machine.

The daily figure is not the interesting number; the multiplication by time is. A bounded experiment amortises its inference bill over a fixed horizon and then stops. A persistent world does not stop. Multiplying the token-equivalent by the living world's elapsed 16,800 days gives roughly forty trillion tokens and something on the order of forty million dollars — arithmetic on two measured quantities, offered as an illustration of the scaling in time rather than as an observed expenditure. Cost per world-day is what determines whether the object under construction is an experiment or a world, and it is the axis on which a language-model-free substrate differs from a prompted one by orders of magnitude rather than by a factor.

### 6.3 Marginal cost of a question, and of a contrast

The asymmetry sharpens when a new question is asked of an existing world. In a deterministic engine the answer is compute over state that already exists: the readout is re-run, or a branch is opened and contrasted against its null. The state was paid for once, at birth, and every subsequent question amortises against it. In a prompted architecture the answer is produced by generation rather than read from state, so each new question is a fresh inference bill regardless of how much simulation has already been paid for.

The same asymmetry applies to the contrast itself. A branch-versus-null comparison is only clean if intervention and control differ by the intervention alone; under common random numbers this holds exactly, and the engine's determinism block records a passing branch-CRN check. Where the substrate is stochastic generation, the same contrast is a difference between two noisy estimates and must be recovered by replication, which multiplies the bill again.

### 6.4 What caching, distillation and routing do — and do not — remove

Prompt caching, knowledge distillation into surrogates, and mixture-of-models routing are genuine engineering advances and should be credited as such. Prior systems in this class reached at most 10^7 agents, and many required dozens of GPUs and weeks of computation for 10^6; Light Society's optimisation stack is what carries it two orders of magnitude beyond that ceiling, with the billion-agent policy operation precomputed into a lookup so that a simulation round reduces to array accesses. This is a large and real reduction in cost.

It is not, however, a reduction in dependence. A cache stores a model's answers; a distilled surrogate is fitted to a teacher model's outputs; a router selects among models. In every case the output distribution remains a function of the model that produced the responses being reused. The Light Society authors state this plainly: their results are "conditional on the underlying language model", and swapping the communication language from Chinese to French moves the stance-change rate by up to 4.7 percentage points with a topic-dependent sign. Surrogate selection compounds the point, since architectures with near-identical per-sample accuracy can differ materially in how closely their aggregate distribution tracks the teacher. Cost engineering acts on the compute; the conditioning lives in the content.

### 6.5 What the comparison class buys that Earth-1 does not

Two concessions must be made without qualification. Light Society simulates over one billion agents; Earth-1's largest measured configuration is 100M — an order of magnitude smaller. And per-agent natural-language reasoning purchases expressive richness for which Earth-1 has no equivalent: an agent that articulates a reason, a free-discussion transcript, a scenario posed in words on the day it is invented. Earth-1's agents carry no language at all.

Nor does cost advantage translate into accuracy. On held-out opinion frames the engine's readout sits behind a region-copy baseline — 11.84 against 9.70 points mean absolute error on 98 WVS items, and 12.01 against 10.31 on 468 Pew items — a miss reproduced on 110 never-labelled replication items and reported here as a miss. The aggregate event-direction gate failed at 40% against an 80% target. No claim of accuracy superiority over language models is made; the project's governing document forbids benchmarking against them at all.

### 6.6 Structural asymmetries that scale does not close

Three differences persist irrespective of population or price. First, vendor deprecation: an architecture whose outputs are produced by a hosted model inherits a dependency on an endpoint that a third party may retire, reprice or silently revise, whereas a language-model-free runtime depends only on its own code and data. Second, language-conditioned outcomes, quantified above at up to 4.7 percentage points. Third, the impossibility of bit-exact replay: a coefficient of variation below 0.01% across five runs is statistical stability, not determinism. Earth-1's determinism block passes 6 of 6, with three independent paths — same-seed rebirth, save/load continuation and flag-on-baseline — converging on one world hash, 49bb7d1d949f28f3; an adapter reproduces p_model 0.4311624 exactly; learning-loop replay from the hash-chained ledger is bit-identical. For audit, what matters is that the run reproduces, not that the distribution is narrow.

### 6.7 Projection toward a full-humanity population

The following is a projection, not a measurement, obtained by extending measured laws beyond their measured range. Against the world population anchor of 8,140,897,523, the flat memory law implies resident state of order eight terabytes, and the birth multiplier implies a peak of order twenty-six. The population is roughly eighty times the largest measured configuration, so the n^1.07 tick law implies about a hundred-and-tenfold increase over the measured 924.8-second world-day — of order thirty hours per world-day on a single box.

That defines an engineering programme with named levers: shard the population, which the flat memory law renders a linear storage problem; reduce the 0.07 of superlinearity in the tick; stage birth so the 3.2x multiplier is a streaming rather than a resident cost; and resolve the registered chronicle-cost defect, in which a world warmed on 90 days of real news ticks far slower than a cold one because memory spread dominates the tick. That defect is registered and unfixed, scheduled as a pre-scale cycle. Finally, scale invariance and census weighting establish what full humanity is and is not for: with the day-5 census identical across a 500-fold range, the case for eight billion agents is individual and subnational resolution, not aggregate accuracy, which is already population-true at 200k.

## 7. Limitations

What follows is the complete register of defects currently standing against Earth-1, each with its measured consequence and an account of what closing it would require. The list is presented in full, and without mitigation, because it is the substantive claim of this section: a model that fails in enumerable, mechanism-shaped ways is a different kind of object from one that is diffusely wrong. Every entry below names a channel the engine does not contain, an instrument fault found by the engine's own checks, a coverage boundary in the substrate, or a score that fell short of a gate fixed before the run. None of them is a residual, a nuisance term, or an unexplained discrepancy. That property — that each miss resolves to a nameable absence rather than to noise — is what makes the instrument falsifiable, and it is the reason the register is published rather than summarised.

### 7.1 Absent institutional mechanisms

Six institutional channels are absent from the physics, and each has a measured consequence in the record.

There is no unemployment-insurance operator. Unemployment runs at approximately 9.7% against a real 4.8%, roughly twice over, and the same absence propagates into shock response: the COVID retrodiction (frozen at 2020-02-28) produced an unemployment response 3.5 times the real delta. The direction is strongly right (t of order 18) and the overshoot is expected rather than surprising, because the model has no furlough state to absorb displacement. The GFC retrodiction (frozen at 2008-09-14) sits on the other side, at 0.64 times the real 2008-to-2009 delta, direction right at t = 2.2 over sixteen seeds. Closing this requires an operator that holds displaced agents in a supported state rather than moving them directly to hardship.

There is no subsidy, substitution, or stock-drawdown machinery. In the pre-registered UKR-2022 counterfactual — model output frozen and committed before any outcome data was fetched, judged against the GRFC acutely-food-insecure database over 48 countries assessed in both 2021 and 2022 — the engine overshot by 8.5 times (+326M modelled against +38.5M real), returned a geographic Spearman of −0.137, and matched one of five countries in the top-5 overlap. The mechanism was named in a sealed written prior before the fetch, and reality confirmed it: Egypt's real change was exactly zero, absorbed by its bread subsidy. Closing this requires operators for price substitution, state transfer, and inventory buffering.

There is no interbank or deposit channel. On the SVB question (frozen at 2023-03-08, contagion to at least two further banks within thirty days) the engine returned a model probability of 0.302; the question resolved YES. Every material line abstained, yet the United States was the top force mover at twice the runner-up — the engine registered the fear and missed the plumbing. The Sri Lanka question (frozen at 2022-03-31, government fall within 120 days) has the same shape: 0.3985 against an event that occurred. Both are under-calls, not misdirections.

There is no bond or pension channel, and the Truss gilt crisis (frozen at 2022-09-22) is consequently invisible: at full fidelity the shocked branch is statistically indistinguishable from its control. The engine abstained rather than fabricating a response. This is recorded as a clean negative result, and it is the clearest illustration of the register's logic — a channel that does not exist produces no signal, which is a more informative failure than a confident wrong number.

Finally, there is no national religiosity input and no geopolitical-alignment input. These are the two worst-performing regions of the opinion surface: religion and values is the worst item family at 3.91 sampling errors against a best family (technology and climate) of 2.97, and per-item losses on the Pew frame concentrate in religion and geopolitics. Closing these requires country-level inputs the substrate does not currently carry.

### 7.2 Instrument defects found and registered rather than patched

Two faults were found in the engine's own apparatus and deliberately left unfixed. The urban indicator in the population substrate is inverted: what the model marks urban is in fact rural, in every country and by exactly one census margin, so the marginal totals remain population-true while the sign is wrong. Two physics consumers are affected — a contagion density multiplier and an air-quality channel. It was registered and not patched because the physics was frozen at the time of discovery, and it is scheduled as a v1.1 cycle under the one-named-change rule. Separately, chronicle cost: a world warmed on ninety days of real news ticks far more slowly than a cold one, with memory spread dominating the tick. It is registered as a pre-scale cycle. The warm-start configuration is the one historical retrodiction requires, and the retrodiction studies reported here stand at 200k agents while the scale ladder reaches 100M.

### 7.3 Substrate coverage limits

Only 63 of 194 countries have survey-measured education and income margins; the remaining 131 joints are constructed by income-tier donor pooling. Age, sex and urban margins are census-derived for all 194, so the fallback affects the socio-economic joint rather than the demographic frame, and the construction beats an independent-marginal baseline by 24.8% on withheld joints at p ≤ 2.4 × 10⁻¹³. That validates the method, not any individual donor's applicability to a particular fallback country. Closing it requires microdata acquisition, country by country.

There is no subnational geography: the country is the finest spatial unit, so within-country heterogeneity has nowhere to reside, and any event whose real footprint is regional can only be scored at national resolution — as the Arab Spring geography was, at Spearman +0.168, p = 0.022 over a 185-country overlap. There is also no household frame: agents are individuals without co-residence, so income pooling, dependency and intra-household transfer are unrepresented. Deep poverty is where the material board is weakest — 16.8% at $3.00/day against a real 10.4%, 1.6 times over — and household pooling is a candidate mechanism there rather than a demonstrated one.

### 7.4 Standing accuracy misses

The opinion readout is behind the region-copy baseline, and this is a miss. On 98 held-out WVS items Earth-1 records 11.84pp MAE against region-copy at 9.70; on the 468-item Pew frame, 12.01 against 10.31. Earth-1 beats the naive baseline only, and the registered ACCEPT tier is ≤ 7.0pp. A replication on 110 additional never-labelled WVS items returned 11.20 against 9.81 — the same verdict, so the miss is not an artefact of item selection. The per-item picture is more textured (outright best of four methods on 64 of 468 Pew items, ahead of region-copy on 137, with wins concentrated in outgroup trust and material hardship) but the aggregate stands: a baseline requiring no simulation currently estimates opinion levels better than the engine does. Closing it requires the two missing country inputs above and a readout that loses less on the families where it loses.

The aggregate event-direction gate failed at 40% against an 80% target. The physics froze at 0.9 as a freeze-with-named-regression: the tag carries that failure, plus five named regressions, rather than a repair that would have reopened the loop. Closing it means adding the missing operators one per cycle, each with its gate fixed by ruling before the run, and re-scoring.

Finally, on scale: Earth-1 has been measured at 100M agents, which is an order of magnitude below the 1B of the comparison class. The ladder is flat to 0.7% in bytes per agent across a hundredfold range and the tick scales as n^1.07, so the gap is a resourcing statement rather than a demonstrated architectural ceiling — but it has not been demonstrated, and 324.5 GB peak at 100M on a single 48-core node, with birth requiring roughly 3.2 times the final state as working memory, makes the next decade of scale a hardware question that remains open.

### 7.5 The register as a claim

None of the above is offered as an apology. Each entry specifies a mechanism, a measurement, and a closure path, which means each is independently refutable: an added operator either moves its gate or it does not, and the ruling was fixed before the run. This is why VOID is reserved for defects in the measuring instrument and never for unwelcome results, and why the urban inversion was registered rather than quietly corrected — a freeze that can be amended after seeing the score is not a freeze. A system whose errors are diffuse can absorb any result; a system whose errors are enumerable can be wrong in public, one named mechanism at a time.

## 8. Discussion

### 9.1 One substrate, one grammar, many conditioned populations

The claim organising this work is structural rather than competitive. A conventional agent-based study constructs a population for a question: the population encodes the question's assumptions, and a second question requires a second population, whose relationship to the first is a matter of authorial intent rather than of measurement. Earth-1 inverts that ordering. There is one census-grounded joint population substrate, one behavioural grammar of eight forces acting on every agent, and one deterministic tick; a domain study is obtained by conditioning that population and reading out from its state, not by rebuilding it. This is the sense in which we use the term foundation model — not a pretrained network, but a single load-bearing substrate and grammar onto which many domain-specific populations are conditioned.

The substrate behaves as one object rather than as a family of separately tuned coincidences, and this is measured. Across a 500-fold population range the day-5 census is identical to within 0.08 percentage points on the poverty line; a 4M world over 180 days reproduces the 200k material board within every registered gate (median income 9.52 against 9.605, poverty 45.29% against 45.88%, mean age at death 68.29 against 68.99); and a 100M world tracks its 4M control through equilibration with poverty gaps of 0.01, 0.00, 0.02 and 0.06 percentage points at days 5, 15, 30 and 60, with age at death identical at day 60. Per-agent state stays flat to 0.7% across a hundredfold scale-up. Enlarging the population therefore buys resolution rather than a different world — a property that must be demonstrated, not assumed, before any of what follows is admissible.

The structure is economically load-bearing because the expensive step is paid once. The substrate and grammar carry a fixed construction cost; thereafter the marginal domain question costs a run, and a run costs 981 bytes per agent with zero language-model calls anywhere in the runtime path — one world-day of a 4M world in 60 seconds on a single 48-core machine. The counterfactual is instructive. Executing one prompt per agent per day for that same 4M population, at 500 input and 100 output tokens, is 2.4 billion tokens per world-day, roughly $2,400 per world-day at a dollar per million tokens, which is below frontier pricing. The living world has run past 16,800 world-days. Under a per-agent-prompt regime, cost scales with questions multiplied by agents multiplied by days; under a shared-substrate regime it does not.

It is scientifically load-bearing for the mirror-image reason. Because one grammar serves every domain, a defect discovered in one place is a defect everywhere, and its repair is testable everywhere. The absence of an unemployment-insurance operator shows up as unemployment running twice the real rate; the absence of substitution, subsidy and stock-drawdown channels shows up as an 8.5-fold overshoot on a food shock; the absence of an interbank or deposit channel shows up as an under-called bank contagion; the absence of a bond or pension channel makes a gilt crisis invisible. Each is one missing mechanism with consequences in several places at once. Tight coupling is a liability for accuracy and an asset for falsification, and we regard the second as the more valuable of the two at this stage.

### 9.2 Population as a substitute for world-time

Rare events are rare per agent-year, which is why the empirical study of crises is a study of small samples. A simulator whose aggregate behaviour is invariant to population size converts sample size in the time dimension into sample size in the population dimension: one can observe more realisations of a rare configuration without waiting longer, and without accepting a different world as the price. The scale-invariance measurements above are what license that exchange. The same statistical logic is visible in the ensemble dimension: on the 2008 frozen forecast, the direction of the unemployment response was not significant at five replicates (t = 0.7) and was significant at sixteen seeds (t = 2.2), with the response itself 0.64 times the real 2008-to-2009 delta. Nothing about the world changed; only the number of realisations did.

The honest limit is that Earth-1's measured ceiling is presently 100M agents on a single AMD EPYC 9454P — birth in 756.7 seconds, 924.8 seconds per world-day, 324.5 GB peak. That is an order of magnitude below the one billion agents demonstrated by Light Society. Scale is not where this system is ahead, and we do not present it as such.

### 9.3 The boundary we do not cross

Earth-1 makes no claim to accuracy superiority over language models. The project's own governing document forbids benchmarking against frontier language models, and that prohibition is a design constraint rather than a rhetorical hedge: a comparison of that kind would import into the calibration ladder a dependency the ladder exists to exclude.

The claim actually made is narrower and, we would argue, harder to dismiss. It is that this object is deterministic, that it is falsifiable, that it is cheap enough to keep running, and that it has been scored against reality and has posted its losses. Determinism here is literal: three independent paths — same-seed rebirth, save/load continuation, and flag-on-baseline — return one identical world hash, and the adapter reproduces a probability of 0.4311624 exactly. This is a different property from the reproducibility reported for the comparison class, where a coefficient of variation below 0.01% across five runs establishes statistical stability rather than reproduced identity, and where the authors state plainly that their results are conditional on the underlying language model — swapping Chinese for French moves the stance-change rate by up to 4.7 percentage points, with topic-dependent sign — and that their outputs are best read as hypotheses rather than as evidence about real societies.

Scoring against reality is what the determinism is for, and the scores include clear misses that we report as such. The opinion readout is behind the region-copy baseline: 11.84 percentage points of mean absolute error against 9.70 on 98 held-out World Values Survey items, 12.01 against 10.31 on the 468-item Pew frame, and 11.20 against 9.81 on 110 never-labelled replication items. Earth-1 beats only the naive baseline, sits roughly two points behind region-copy, and is far from the registered ACCEPT tier of 7.0 points or better. The aggregate event-direction gate failed at 40% against an 80% target, and physics was frozen at 0.9 carrying that failure by name rather than being reopened to remove it. The pre-registered Ukraine counterfactual missed on all three registered axes: 8.5-fold magnitude overshoot, geographic Spearman correlation of −0.137, and one of five on top-five overlap. What that exercise did produce was a sealed written prior that named all three failures and their mechanism in advance, and a confirmation in the outcome data — Egypt's real change of exactly zero, absorbed by its bread subsidy. A model that can lose a pre-registered bet, and does, occupies a different epistemic position from one that cannot be placed in the position of losing.

## 9. Methods (overview)

This section describes what exists and how it is evaluated. It is deliberately not a reproduction specification: update equations, fitted constants, functional forms, injector templates, lexicon contents and internal module structure are withheld. The claims in this paper rest on measured outputs against registered gates and sealed judges, not on disclosed internals.

**Substrate construction and provenance.** The population is a per-country joint distribution over five demographic dimensions — sex, age band, education, income and urbanicity — yielding 216 cells for each of 194 countries. Age, sex and urban margins are census-derived for all 194. Education and income margins are survey-measured for 63 countries from World Values Survey Wave 7 microdata; the remaining 131 are supplied by tier-fallback donor pooling across income tiers, and this asymmetry is registered as an open defect rather than smoothed over. The joint is recovered by iterative proportional fitting over pooled donors, which beats an independent-marginal baseline by 24.8% on withheld joints at p ≤ 2.4 × 10⁻¹³. The adult age pyramid is derived from stable-population density using each country's own Gompertz survival rather than a parametric draw. Every agent carries a census weight equal to the ratio of its country's census share to its share of the simulated population, so that global figures are population-true at any sample size; the world anchor is 8,140,897,523 (World Bank SP.POP.TOTL 2024).

**Behavioural grammar.** Agent behaviour is generated by eight forces that act on every agent in every domain. The grammar is uniform: there are no domain-specific behavioural rules layered on top for particular studies, which is what makes a defect in one domain diagnostic for the others. The forces' definitions, couplings and constants are withheld.

**Deterministic tick and paired branch contrast.** The world advances by a deterministic tick; identical inputs return an identical world. Determinism is verified on three independent paths — rebirth from the same seed, continuation from a saved state, and running with the branch flag enabled on the baseline — all of which produce one world hash. Interventions are evaluated as a paired contrast between a branch and its null under common random numbers, so that the two worlds differ only by the intervention. A branch that is statistically indistinguishable from its control is recorded as a physics abstention and reported as a negative result, as in the 2022 gilt-crisis case, where a model with no bond or pension channel correctly showed nothing.

**Calibration ladder and pre-registered gates.** Calibration proceeds one named change per cycle, with acceptance gates fixed by written ruling before the run that tests them. Gates are stated as thresholds on named quantities, and results falling outside them are recorded as regressions rather than absorbed. VOID is reserved exclusively for defects in the measuring instrument and is never available for an unwelcome result. Physics was frozen at 0.9 as a freeze-with-named-regression, the tag carrying the failed event-direction gate and five named regressions.

**Frozen-forecast protocol.** For historical retrodiction, a world is born at a date T on real archive news, under a mechanical assertion that no input, anchor or news item postdates T. The model output is then frozen and committed. Only after the commit is the outcome data fetched. This ordering is enforced by the commit history rather than by assurance.

**Sealed-judge protocol.** Each evaluation registers its judge by name and location before the run, with outcome values left unfetched until the output is frozen — for the Ukraine counterfactual, a specific release of the Global Report on Food Crises acutely-food-insecure database, identified by content hash, restricted to the 48 countries assessed in both comparison years. Where a written prior exists it is sealed alongside the output and opened with it.

**Readout.** Opinion estimates are produced by a readout from agent state to survey-item response, evaluated leave-one-country-out across 21,776 scored item-country cells with abstention on items requiring named-entity knowledge; abstained cells are excluded from both the model and the baselines. The readout's construction is withheld. Its current performance, reported in full in Section 7.3, is behind the region-copy baseline.

---

## Colophon

**Reproducibility.** Every quantity in this paper is produced by the frozen physics
configuration designated freeze-0.9 and is reproducible from the recorded configuration
stamp. Runs whose stamp does not match are refused by the engine rather than silently
accepted.

**Held-out data.** The holdout and prospective estates referenced in Section 5 remain
sealed. Numbers reported here are from the training and development estates only; no
figure in this paper was computed on sealed data.

**Withheld.** Force update equations, fitted constant values, calibration readout
formulae, injector templates and the registered vocabulary are proprietary and are
described functionally rather than reproduced.
