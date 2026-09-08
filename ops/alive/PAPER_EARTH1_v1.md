# Earth-1: a deterministic civilization model with no language model in the loop

**Earthling Labs** · Version 2.0 · 8 September 2026 · Epoch 3 / freeze-0.9
Correspondence: pietro@vaultik.com
Typeset preprint: https://claude.ai/code/artifact/1b0fcfb0-9555-428f-b0cd-5e24de861929

*Census-grounded agents, an eight-force behavioural grammar, and falsifiability as an
architectural property rather than a methodological aspiration.*

## Principal results

| Result | Earth-1 | Reference | Verdict |
|---|---|---|---|
| Global poverty, $8.30/day | 45.9% | 46.1% real | on anchor |
| Median income | $9.61/day | $9.27 real | on anchor |
| Crude death rate | 0.0073/yr | 0.0076 real | on anchor |
| Adult share 65 and over | 14.1% | 13.6% real | on anchor |
| Mean age at death | 69.0 yr | band 66.2–71.8 | in band |
| Majority agreement with real humans | 83.5% | 21,776 scored cells | — |
| Answers inside the survey's own noise | 14.2% | of 12,669 cells | — |
| Population joint vs independent marginals | +24.8% | p ≤ 2.4 × 10⁻¹³ | wins |
| Determinism | one world hash | 3 independent paths | exact |
| Scale invariance, poverty line | 0.08 pp | across 500× population | flat |
| Board reproduced at 20× population | −0.59 pp | 4M vs 200k, poverty | holds |
| State per agent | 981 bytes | flat to 0.7% across 100× | flat |
| Learning vs informed non-learner | 4.8× | 16 of 16 worlds, p = 3 × 10⁻⁵ | wins |
| Continuous operation | past day 16,860 | 4M agents, one 48-core server | live |
| Language-model calls in runtime path | 0 | by architecture | — |

---

## Abstract

Computational models of society divide into two families that trade against each other along a single axis. Classical agent-based models are cheap and inspectable but behaviourally thin: their agents follow heuristics the modeller chose. Societies of language-model agents are behaviourally rich and demographically groundable, but their cost scales with the product of agents, questions and days; their results are conditional on the particular checkpoint behind the agents; and their own authors state that outputs are best read as hypotheses to be examined empirically, "not as evidence about real societies" (Guan et al., arXiv 2506.12078v2). We describe EARTH-1, a deterministic civilization model that occupies a third position. It contains no language model anywhere in its runtime path, and it can be held to a prediction it made before the outcome existed.

Agents are drawn from a census-grounded five-dimensional joint population across 194 countries — 216 cells per country, fitted by iterative proportional fitting over pooled donors, which beat an independent-marginal baseline on withheld joints by 24.8% at p ≤ 2.4 × 10⁻¹³ — and are advanced by an eight-force behavioural grammar under a deterministic tick.

The system reproduces the world it models. At 200,000 census-true agents over 180 days it puts global poverty at 45.9% against a real 46.1%, median income at $9.61 per day against $9.27, the crude death rate at 0.0073 per year against 0.0076, and the 65-and-over adult share at 14.1% against 13.6%. That board reproduces at twenty times the population, and the poverty line moves by 0.08 percentage points across a 500-fold range of population size. Determinism is exact rather than statistical: three independent paths — same-seed rebirth, save-and-load continuation, and flag-on baseline — converge on one identical world hash. Against 21,776 scored item-country survey cells under leave-one-country-out, the model agrees with the real human majority on 83.5%, and 14.2% of its answers fall inside the survey's own 95% sampling noise. Given experience it improves: against an informed non-learner receiving identical observations but no persistence, the learning loop wins by 4.8× on late-window score at p = 3 × 10⁻⁵, positive in 16 of 16 worlds.

The architecture is what makes this affordable. State costs 981 bytes per agent, flat to 0.7% across a hundredfold range of population, and one world of four million people has now run continuously past day 16,860 on a single 48-core server. Serving the same world by prompting each agent once per day would have consumed roughly 40 trillion tokens.

We report the misses at the same resolution as the results. The opinion readout sits about two percentage points behind a region-copy baseline in aggregate, while being outright best of four methods on 64 of 468 held-out survey items with its wins concentrated in outgroup trust and material hardship; and the aggregate event-direction gate stands at 40% against an 80% target. Both were measured against gates fixed by ruling before the runs that tested them. That is the property this paper is really about: Earth-1's distinguishing feature is not that it is right, but that it is the kind of object that can be shown to be wrong.

## 1. Introduction

### 1.1 Two families, one axis

The computational study of societies has organised itself into two research programmes that trade against each other along a single axis.

The older programme, agent-based modelling in the Schelling–Sugarscape lineage, buys tractability with behavioural poverty. Rules are hand-specified, parameters are chosen subjectively, and the interesting question — why a population does what it does — is answered by the modeller before the simulation starts. What such models gain is enormous: they are cheap, they are inspectable, and every mechanism in them can be read.

The newer programme replaces the rule with a language model. Recent work has demonstrated societies at genuinely impressive scale; the largest reported to date instantiates one billion language-model-powered agents through prompt caching, distillation to surrogate models, and mixture-of-models routing. These populations are behaviourally rich in a way no hand-written rule reproduces, and they can be conditioned on real demographic distributions. But three properties travel with the design. Cost scales with the product of agents, questions and days, because behaviour is generated per agent per question. Results are conditional on the model behind the agents: the same reported system moves its stance-change rate by up to 4.7 percentage points, with topic-dependent sign, when the underlying model is swapped between two languages. And reproducibility is statistical rather than exact — the strongest such claim in the literature is a coefficient of variation below 0.01% across five runs, which is a statement about the narrowness of a distribution, not about the recovery of a particular world.

Their authors are admirably direct about what follows. Outputs "should not be treated as substitutes for human participants" and are "best read as hypotheses to be examined empirically, not as evidence about real societies."

### 1.2 The property neither family has

Take that disclaimer seriously and a gap opens that neither programme fills.

A model whose outputs are hypotheses cannot be falsified by the world. It can be interesting, it can be suggestive, it can generate research directions — but it cannot lose a bet, because nothing it produces was ever committed to in a form that the world could later contradict. And a model that cannot be falsified accumulates capability without accumulating credence. It gets more impressive every year without ever becoming more trustworthy.

Falsifiability of this kind is not a matter of scientific etiquette. It is an architectural requirement, and it has a hard precondition: to hold a model to a prediction, you must be able to recover the exact world that produced it. Not a world drawn from the same distribution — that world, bit for bit, months later, on different hardware. Everything else this paper describes follows from taking that requirement literally.

### 1.3 Earth-1

EARTH-1 is a deterministic civilization model built on that requirement. Its population is drawn from a census-grounded five-dimensional joint distribution across 194 countries and aggregated with census weights, so that every global figure it reports is an estimate of the world rather than of the sample resident in memory. Its agents are advanced by an eight-force behavioural grammar under a deterministic tick. No language model appears anywhere in its runtime path.

The design is not an economy measure. Removing generative inference from the loop is what buys exact reproducibility, and exact reproducibility is what makes every subsequent claim in this paper checkable: a frozen forecast can be reopened and re-run, a perturbation can be contrasted against a null branch of the same world under common random numbers, and a result that arrives months after the run can still be attributed to the thing that caused it.

### 1.4 Contributions

1. **A census-grounded population substrate.** A per-country joint over sex, age band, education, income and settlement, fitted by iterative proportional fitting over pooled donors, which beats an independent-marginal baseline on withheld joints by 24.8% at p ≤ 2.4 × 10⁻¹³. Adult age structure is derived from stable-population density under each country's own survival curve.

2. **Exact determinism, verified along three independent paths.** Same-seed rebirth, save-and-load continuation, and flag-on baseline converge on a single world hash. The question-answering layer reproduces a model probability to seven decimal places on demand.

3. **A material board that matches the real world and holds under scale.** Poverty, income, mortality and age structure land on their real anchors at 200,000 agents, reproduce at four million, and shift the poverty line by 0.08 percentage points across a 500-fold range of population.

4. **Population-level agreement with real humans.** 83.5% majority agreement across 21,776 scored item-country cells under leave-one-country-out, with 14.2% of cells inside the survey's own sampling noise.

5. **Demonstrated learning against a hard control.** A 4.8× advantage on late-window score over an informed non-learner given identical observations without persistence, positive in 16 of 16 worlds, with bit-identical replay from a hash-chained ledger.

6. **An economics that permits continuous operation.** 981 bytes per agent, flat across a hundredfold scale range; a four-million-person world running past day 16,860 on one server; roughly 40 trillion tokens of generative inference not spent.

7. **A falsification apparatus, and its results — including the negative ones.** Frozen-forecast-then-judge with sealed judges and gates fixed by ruling before the run, reported in Section 5, with the full register of hits and misses in Sections 4 and 7.

### 1.5 What this paper withholds

This is a description of a system and its measured behaviour, not a reproduction specification. Force update equations, fitted constant values, calibration readout formulae, injector templates, the registered vocabulary and internal module structure are proprietary and are described functionally. Every claim below rests on measured outputs against registered gates and sealed judges rather than on disclosed internals — which is, in any case, the standard by which such a system should be judged.

## 2. Earth-1 is not an agent swarm

The distinction drawn in this section is architectural, not a matter of degree. The dominant design for large-scale social simulation instantiates N reasoning entities, gives each a natural-language profile and a policy realised by a language model, dispatches their interactions through an event queue, and aggregates the emitted actions into a population-level statistic. Earth-1 does not do a smaller version of this. It does not instantiate a population of reasoners at all.

The difference is categorical rather than one of degree. There is no per-agent natural-language reasoning anywhere in Earth-1: agents do not deliberate, do not emit text, and hold no beliefs expressible as sentences. The comparison class is the mature form of the opposite design — a billion agents on a scale-free network, each with a survey-derived profile and a language model behind it — and this section argues that the two systems are answering different questions rather than competing on the same one.

What Earth-1 evolves is a single civilization whose population is a state manifold: a census-grounded joint distribution instantiated in memory at 981 bytes per agent, with behaviour expressed as arithmetic over that state. An individual is an addressable view of the manifold rather than a separately-reasoned process. In a swarm the agent is the unit of computation and the society is the sum of its outputs; in Earth-1 the civilization is the unit and the person is a coordinate within it.

### 2.1 The substrate is a population, not a roster

Earth-1 carries 194 countries. Each holds a five-dimensional joint over sex (2), age band (6), education (3), income (3) and urban residence (2) — 216 cells per country. Age, sex and urban margins are census-derived for all 194. The joint itself is drawn by iterative proportional fitting over pooled donors, which beat an independent-marginal baseline by 24.8% on withheld joints at p ≤ 2.4e-13 — the correlation structure between education, income and residence is measured, not assumed away. The adult age pyramid is derived from stable-population density using each country's own Gompertz survival rather than a parametric draw. Every country's joint additionally carries a declared provenance — whether its education and income margins were measured from survey microdata or pooled from income-tier donors — so a consumer of any figure can see which countries are carrying it and how well grounded each one is. The provenance register is reported in Section 7.

This is a different object from a profile pool. Where a swarm samples agent personas from a fixed set of survey records — Light Society draws from a pool of 10,000 — Earth-1 instantiates a country's joint and then weights it: each agent's weight is its country's census share divided by its share of the instantiated population, so every global figure the engine reports is population-true against a world anchor of 8,140,897,523. A global poverty rate is an estimate of the world, not of the sample that happens to be resident in memory.

The signature of a manifold rather than a crowd is visible under scaling. The day-5 census is identical at 200k, 1M, 4M and 100M agents, the poverty line varying by 0.08pp across a 500-fold range in population; a 4M board reproduces the 200k board across every material line. Adding agents raises the resolution at which the same distribution is sampled; it does not change what is being sampled. This is the opposite scaling signature to a swarm, in which demographic effects sharpen and individual variability diminishes as the population grows — a property of averaging noisy reasoners, and a useful diagnostic that the two systems are not the same kind of thing.

### 2.2 A universal grammar with contextual activation

Behaviour in Earth-1 is generated by eight forces. The grammar is universal: the same eight act on every agent in every country, in every domain the engine is asked about. What is contextual is activation — which forces are live, and with what weight, given the state of the agent and of the world around it. The update rules, their fitted constants and the readout that maps state to expressed opinion are outside the scope of this description.

The architectural consequence of that split is the one worth stating. Because the grammar is fixed and only its activation varies, domain-specific models are configurations of one civilization rather than separate simulators. A swarm achieves generality by re-prompting: a new question means a new template, a new operator, often a new distilled surrogate. Earth-1 achieves it by re-activating an invariant grammar over a world that already exists. Post-hoc attribution follows for free — after a shock one can ask which force moved, and where, as a property of the run rather than as an interpretation of generated text.

Two further consequences follow from there being no language model in the runtime path. First, there is no model-dependence axis: Light Society's authors are explicit that their results are "conditional on the underlying language model", and report that swapping the communication language moves the stance-change rate by up to 4.7 percentage points with topic-dependent sign. Earth-1 has no such parameter, and its determinism is exact rather than statistical — three independent paths, same-seed rebirth, save/load continuation and flag-on-baseline, converge on one identical world hash. A replication on 110 never-labelled items returns the same verdict, so the miss is not item selection.

### 2.3 Persistence rather than instantiation

A swarm is instantiated per experiment. Its population is born for the run, evolved for a fixed number of rounds, read out and discarded; nothing in round one of the next experiment remembers the last. Earth-1 runs a 4M world continuously past day 16,860, at roughly one world-day per sixty seconds, publishing a hash-chained event stream as it goes. Agents age, die and are born inside a history that accumulates. Persistence is what makes counterfactual work well-posed: a question is asked as a branch against a null continuation of the same world under common random numbers, so the contrast isolates the injected event rather than the difference between two separate instantiations.

### 2.4 Emergence as a measurement

The practical payoff of all three properties is that emergence becomes something one measures rather than something one narrates. Because the state is arithmetic and the world is deterministic, the branch-null difference is attributable to the injection alone; run-to-run stability, however tight, is a weaker guarantee than a reproducible hash. And because the object measured is state rather than generated discourse, a null result is a legal outcome. A system that narrates emergence cannot return that answer; it will always produce a story.

The current accounting is not flattering. The argument of this section is not that Earth-1 is currently right. It is that a civilization held as state, rather than as a swarm of reasoners, can be wrong in a locatable place.

## 3. Social structure, transmission, and emergence

Agent-based societies routinely claim that collective behaviour *emerges* rather than being written in, and the claim is routinely unfalsifiable. Two explanations for any neighbour-correlated pattern — genuine transmission between agents, and a shared response by similar agents to a common input — leave the same signature in aggregate statistics. A model that cannot separate them can only narrate emergence.

Earth-1 can separate them, and this section is about the machinery that makes that possible: a real graph over named people, dyadic transmission along its edges, a competing pull from material circumstance, and a determinism strong enough to turn emergence from a story into a measurement.

### 3.1 A graph over people, not a channel over aggregates

Each agent holds ties across several relationship channels — household, colleagues, neighbours, friends, weak ties, and a small set of high-degree media hubs — with channel-specific weights and degrees. Every social computation on the daily path reads a *living view* of that graph, rebuilt after each day's deaths, migrations and job changes, so that the dead retain their edges as history while carrying no weight in current dynamics.

The graph is constructed at genesis with homophilous structure: people are connected preferentially to people like them, as they are in the world being modelled. Tie weights then move continuously, and a limited amount of rewiring changes who is connected to whom.

### 3.2 Transmission is dyadic and reads a named partner's state

The daily influence operation is not a mean-field approximation. Each agent draws a small number of encounters per day, sampled by tie weight from its living neighbourhood. For each encounter, the agent's force vector moves a fixed fraction of the way toward *that specific partner's current value*, scaled by a susceptibility term depending on the agent's own condition — age, conviction, mental state, hunger. The quantity moved is read from the partner's state at that moment.

This is transmission in the strict sense. Information about one person's state enters another person's state through a named edge, and the same encounters simultaneously accumulate the evidence from which conviction is updated at the end of the day. Belief and certainty co-evolve out of the same interactions.

### 3.3 Two forces act on every belief, every day

An agent's forces are moved each day by two competing operations. The social operation pushes the agent toward the people it encounters. A second operation computes the force state the agent's *material circumstances* imply — work, income, reserves, hunger, housing, health — and relaxes the agent toward that target. The material target is deliberately returned rather than applied, so the social layer acts as a push and circumstance as a restoring pull.

This tension is the structural core of the model's social dynamics: an agent is moved by the people it knows and pulled back by the life it actually lives. A world with only the push saturates; a world with only the pull is a lookup table on circumstance. Because both operations are arithmetic on inspectable state, the balance between them can be read directly rather than inferred from outputs.

### 3.4 The feedback structure

Emergence requires closed loops. Five are traceable on the daily path.

**Influence and conviction.** Encounters move forces and simultaneously accumulate agreement evidence; conviction updates from that evidence; conviction then weights susceptibility to subsequent movement.

**The fabric responds to the conversation.** Tie strengths update from the day's interaction — agreement strengthens a tie, disagreement weakens it — and a small number of agents find replacements closer to them in force space. The graph the influence operator runs on tomorrow is a function of what that operator did today.

**Social position feeds back into disposition.** Each day, an agent's deviation from its neighbourhood's mean force updates its dispositional traits, which in turn shape both susceptibility and the material force target. This is a slow loop from where you sit in a population back to who you are.

**Memory spreads along the graph.** Events enter the world's chronicle with a scope, and that scope grows: an event known to one part of the graph reaches the people who know the people it happened to, with rehearsal consolidating repeated similar events rather than stacking them.

**Institutions close the loop through the population.** Government policy reads aggregate population state and chooses accordingly, and the resulting policy changes the material conditions from which every agent's force target is computed. Belief reaches back to belief through the state.

### 3.5 Drawn or grown: a distinction Earth-1 can make

The discipline that matters is refusing to credit emergence for anything that was drawn at genesis. Earth-1 is unusual in being able to tell the difference, and the demonstration is worth stating precisely.

The population's income distribution is heavy-tailed, and it would be easy to attribute that tail to correlated shocks travelling through the firm structure and the social graph. Measurement says otherwise: wage kurtosis is 247.01 at birth and 246.76 after 120 days of living. Living changes it by roughly a quarter of one percent. **The heavy tail of income is drawn, not grown, and Earth-1 says so.**

Over the same 120 days, the ratio of the 99th percentile of accumulated wealth to the median rises from 11.88 to 29.48, and the share held by the top one percent rises from 0.122 to 0.194 — with only 6.5% of agents having experienced any job loss at all. Nothing placed that concentration in the world at genesis. It grows out of the interaction between correlated employment shocks, scarring, and the differential capacity of households to absorb them. **Within a generation, wealth concentration is emergent, and Earth-1 says that too.**

Two superficially similar inequalities in the same population, one designed and one grown, correctly distinguished. This separation is not available to a model whose runs differ from each other, because it requires holding an entire world fixed and asking what a single mechanism contributed. It is the sharpest available evidence that Earth-1's emergent claims are measurements rather than descriptions.

### 3.6 Emergence as a measurement

Determinism is what makes the preceding section possible. Because the world is bit-reproducible, a perturbed branch runs against a null branch of the *same* world under common random numbers, and any difference between them is attributable to the perturbation rather than to sampling. An emergent claim in Earth-1 therefore takes the form of a paired difference with a seed-level error bar.

The instrument also returns negative results, which is the harder test and the more useful capability. When a fiscal shock was applied to a single country at full fidelity, the shocked branch was statistically indistinguishable from its control, and the system reported an abstention traceable to a named structural absence. A model that narrates emergence cannot return that answer; it will always produce a story. The decomposition of the remaining neighbour correlation into transmission and homophily is quantified by a zero-transmission ablation on the schedule, using exactly the branch-versus-null apparatus described here.

The general principle is the one this section has been building toward. Earth-1 does not ask to be believed about emergence. It exposes the mechanism as arithmetic, holds the world still, and measures what each part of it contributed.

## 4. Results

### 4.1 Determinism, and the control that makes it meaningful

Earth-1's determinism block records six checks of six passing. Three independent construction paths — rebirth from the same seed, continuation from a saved checkpoint, and a flag-on run against its own baseline — converge on one identical world hash, `49bb7d1d949f28f3`. Branch common-random-number contrast passes, historical rebirth passes, and the question-answering layer reproduces a model probability of 0.4311624 exactly on demand.

A reproducibility claim is only as strong as the sensitivity of the detector that would catch a violation, so the hash was tested in the failing direction. On the live four-million-agent world, moving a single agent's internal well-being value by 10⁻⁹ changed the world hash from `96e1aba8…` to `184d7f0a…`, and undoing the perturbation restored the original hash exactly. Two runs that agree on this hash agree on the state of the world down to one part in a billion of one person's interior. Bit-identity here is not an artefact of a hash too blunt to disagree.

The strongest form of the claim is that the physics, not the code path, is the invariant. Against a registered tolerance of bitwise zero, an independent implementation and the canonical engine produced **38 of 38 identical checkpoints across a full 365-day year at 200,000 agents**, with equal day-365 world hashes, and 11 identical checkpoints per seed across two further seeds. No physics was changed to obtain any of that agreement. Reproducibility that survives re-implementation is a property of the model rather than of one binary.

### 4.2 The material board

At 200,000 census-true agents over 180 days under the frozen physics configuration, the world's material aggregates land on their real anchors.

| Quantity | Earth-1 | Real anchor | Status |
|---|---|---|---|
| Poverty, $8.30/day | 45.9% | 46.1% | on anchor |
| Median income | $9.61/day | $9.27/day | on anchor |
| Crude death rate | 0.0073/yr | 0.0076/yr | on anchor |
| Adult share 65 and over | 14.1% | 13.6% | on anchor |
| Mean age at death | 69.0 yr | band 66.2–71.8 | in band |

These are population-true figures, not sample statistics: each agent carries a weight equal to the ratio of its country's census share to its share of the simulated population, against a world anchor of 8,140,897,523. A global poverty rate here is an estimate of the world rather than of the people who happen to be resident in memory.

Two material quantities sit outside their anchors and are reported in Section 7: the $3.00/day poverty line and the unemployment rate.

### 4.3 Scale

State costs between 975.2 and 981.6 bytes per agent across the 1M, 4M, 16M, 64M and 100M rungs — flat to 0.7% across a hundredfold range. The tick scales as n^1.07. At one hundred million agents, birth takes 756.7 seconds and a world-day 924.8 seconds at a peak of 324.5 GB, on one 48-core AMD EPYC 9454P.

That ladder is a validated instrument rather than a table of observations. Extrapolating from the rungs below it, the hundred-million-agent run was forecast at **311 GB and 14.4 minutes per world-day before it was executed**, and measured 324.5 GB and 15.4 minutes. An out-of-sample engineering forecast, made beyond the largest measured rung, held on both axes.

The board also reproduces at scale. Four million agents over 180 days return a median income of 9.52 against the board's 9.605, poverty of 45.29% against 45.88%, a crude death rate of 0.00738 against 0.00727, and mean age at death of 68.29 against 68.99 — every line inside its gate at twenty times the calibrated population. Through equilibration, a 100M world tracks a 4M control to a poverty gap of 0.01, 0.00, 0.02 and 0.06 percentage points at days 5, 15, 30 and 60, with age at death identical at day 60.

The sharpest scale result concerns invariance rather than accuracy. A five-day census — an equilibration state well before the 180-day board, and not to be read as a calibrated result — is *the same world* at every population size:

| Population | Median $/day | Poverty $8.30 | Poverty $3.00 |
|---|---|---|---|
| 200,000 | 3.30 | 0.9456 | 0.4438 |
| 1,000,000 | 3.24 | 0.9460 | 0.4466 |
| 4,000,000 | 3.23 | 0.9464 | 0.4470 |
| 100,000,000 | 3.23 | 0.9463 | 0.4467 |

Across a 500-fold population range the poverty line varies by 0.08 percentage points and the median by seven cents. The board's dependence is on *time*, not on *N*. This retroactively licenses the entire calibration ladder: tuning at small populations and confirming at larger ones is legitimate precisely because the physics is scale-free, and a calibration that held only at its own sampling frame would have broken here. It did not.

Scale therefore buys statistical resolution rather than a different world. Rare events — deaths, crises, tail behaviour, narrow demographic segments — become measurable in days of world-time instead of years, because population sample substitutes for time sample only when the larger world is demonstrably the same world.

### 4.4 Agreement with real humans

Against 21,776 scored item-country cells across three estates, under leave-one-country-out with named-entity abstention active, Earth-1 agrees with the real human majority on **83.5%** of cells. Of the 12,669 cells where the survey's own sample size is known, **14.2% are statistically indistinguishable from the survey's own 95% sampling noise** — for one cell in seven, the model's answer cannot be told apart from having asked people. Median distance is 3.78 sampling errors and mean absolute error 10.65 percentage points. The signed error is near zero overall, so the residual is family-specific tilt rather than one global bias. The best family is technology and climate at 2.97 sigma, the best region Oceania at 2.28.

Against continuous-valued baselines, the readout is behind. On 98 held-out WVS items Earth-1 scores 11.84 pp MAE against a naive baseline's 12.80, an MrsP small-area estimator's 11.18 and region-copy's 9.70; on 468 Pew items, 12.01 against 12.02, 11.06 and 10.31. A replication on 110 never-labelled items returns 11.20 against region-copy's 9.81, so the deficit is not item selection. Earth-1 beats the naive baseline and trails both MrsP and region-copy by roughly one to two points. The registered ACCEPT tier is 7.0 pp, and this readout does not reach it.

The per-item structure is where the mechanistic model earns its place. On the Pew frame Earth-1 is **outright best of the four methods on 64 of 468 items and beats region-copy on 137**, and those wins concentrate in outgroup trust and material hardship — precisely the domains where an attitude follows from circumstances the engine simulates. Its losses concentrate in religion and geopolitics, which correspond to inputs the substrate does not currently carry. Region-copy, meanwhile, is a lookup table: it cannot be perturbed, cannot answer a counterfactual, cannot be run forward, and has nothing to say about any individual. Earth-1 is currently the less accurate estimator of a static survey margin and the only one of the four that is a model of anything.

### 4.5 Learning

Earth-1 improves from experience, and the gates were built to catch it pretending to. Experience Loop v0.2 ran twenty worlds with sharp shocks against five pre-registered control arms.

The decisive arm is the informed non-learner — a filter given the learner's identical observation access but forbidden to update its physics, so that any advantage must come from persistence rather than information. The learner beat it by **+1.51 log-CRPS, 95% CI [1.21, 1.81], p = 3 × 10⁻⁵, positive in 16 of 16 well-specified worlds**, with late-window error of 0.216 against 1.04 — a 4.8-fold gap. It beat a frozen model by +2.16 (p < 10⁻⁴), a naive updater by +0.55 [0.32, 0.77] (p = 2 × 10⁻⁴), and its own shuffled-resolution placebo by +2.08 (p = 3 × 10⁻⁵), and it won inside shock windows by +0.59 (p = 10⁻⁴).

The causal control holds in both directions, which is the part that matters: the placebo learner is statistically indistinguishable from the frozen model (Δ = 0.078, p = 0.90). Learning appears when and only when there is something real to learn from. Ninety-percent intervals cover at 0.963, the model stays honest under deliberate misspecification in four cases of four, and replay from the hash-chained ledger is bit-identical.

### 4.6 Retrodiction under a frozen forecast

Every historical result below was produced by birthing a world at date T on real archive material, under a mechanical assertion that no input, anchor or news item postdates T, then freezing and committing the output *before* the judge was fetched.

On a pre-committed register of protest-onset countries against quiet controls, Earth-1's unforced country states rank the real protest-prone countries above the quiet ones at **Spearman ρ = 0.552 (p = 0.0052)**, with a Mann-Whitney separation at p = 0.0044 and a thirteenfold discrimination margin — mean onset probability 0.417 for the positives against 0.031 for the controls. Controls sitting at approximately zero satisfies the placebo criterion. The ordering is a real signal; the probabilities are not yet calibrated as forecasts, since the Brier improvement over base rate is not significant.

Judged retrodictions follow the same protocol. For the Arab Spring, frozen at 2010-12-16 and judged against real protest events across a 185-country overlap in the following 90 days, the material-stress geography correlates at Spearman +0.168 (p = 0.022) — and the finding the row records is that material stress, not fear, carries the signal. For the global financial crisis, frozen at 2008-09-14, the unemployment response is 0.64× the real 2008-to-2009 delta, direction correct at t = 2.2. For COVID, frozen at 2020-02-28, the response is 3.5× the real delta with direction at t ≈ 18.

The aggregate event-direction gate stands at 40% against an 80% target and is reported in Section 7 with the rest of the register. Two of the individual misses are under-calls rather than misdirections: the model put 0.302 on banking contagion and 0.3985 on a government falling, and both happened. In the banking case every material line abstained while the United States was the top force mover at twice the runner-up — right about the fear, missing the plumbing.

Taken together, these results describe an instrument rather than a demonstration. The world is exactly recoverable and its hash is sensitive to one part in a billion of one person's state; the physics survives re-implementation bitwise across a simulated year; the material board lands on real anchors and stays there across a five-hundredfold change in population; the model agrees with real human majorities on five cells in six and is inside survey noise on one in seven; it improves from experience against a control designed to make that improvement impossible to fake; and it forecast its own resource envelope at a scale it had never run. Each of those is a number that a later run can contradict.

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

Nothing in this comparison concerns accuracy, and no accuracy comparison against language models is made in this paper; the project's governing document forbids it. The claim is narrower and structural — that a frozen artefact plus a sealed judge is a mechanism by which a run can be held to a prior commitment, and that a variance statistic, however small, is not.

### 5.3 The governance that operationalises it

A chain of this kind fails through procedure rather than through theory, so the procedure is codified. One named change per cycle, so that any movement in the gates is attributable. Gates fixed by ruling before the run. VOID reserved for defects in the measuring instrument and never invoked for an unwelcome result. Sealed judges registered by name and location, with outcome values unfetched until the model output is committed.

Such rules are only tested when they cost something. A registered substrate defect — an inverted urban flag reaching two physics consumers — was likewise recorded and deliberately left unpatched, scheduled as a later cycle, because the physics was frozen. Both decisions are locally uncomfortable and structurally necessary. A gate that may be revised once the result is visible is not a gate.

### 5.4 A worked example: the UKR-2022 counterfactual

The 2022 grain-shock counterfactual was frozen and committed before any outcome data was fetched, against a judge registered in advance: the GRFC acutely-food-insecure database (sha 44de7226), restricted to the 48 countries assessed in both 2021 and 2022. The model lost on all three registered dimensions. Magnitude overshot by 8.5x (+326M modelled against +38.5M real). Geography carried no signal at all, at Spearman -0.137. Top-5 overlap was 1 of 5.

Sealed before the fetch, the founder's written prior had predicted all three failures and named the mechanism responsible: no substitution, no subsidies, no stock drawdown. Reality then confirmed the named damper directly — Egypt's real change was exactly zero, absorbed by its bread subsidy. The run is therefore, simultaneously and without contradiction, a triple failure against its own registered gates and a successful test of a stated mechanistic hypothesis. Only the ordering makes the second reading admissible. Had the prior been written after the numbers were known, it would be a narrative rather than a prediction, and the identical text would carry no evidential weight whatsoever.

### 5.5 Enumerable absence versus diffuse error

This is the property that distinguishes the object being built. Earth-1's misses resolve, one by one, onto absent operators that can be named in advance of any repair. The SVB question was under-called at a model probability of 0.302 on an outcome that resolved YES, with every material line abstaining while the United States emerged as the top force mover at twice the runner-up — right about the fear, missing the plumbing, which is to say no interbank or deposit channel. The Truss gilt episode produced a physics abstention, the shocked branch indistinguishable from control, which is precisely what a model with no bond or pension channel should produce.

The opinion readout is a miss and is reported as one. Its worst family, religion and values at 3.91 sampling errors, corresponds to an input the substrate does not carry.

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

Two concessions must be made without qualification. And per-agent natural-language reasoning purchases expressive richness for which Earth-1 has no equivalent: an agent that articulates a reason, a free-discussion transcript, a scenario posed in words on the day it is invented. Earth-1's agents carry no language at all.

Nor does cost advantage translate into accuracy.

### 6.6 Structural asymmetries that scale does not close

Three differences persist irrespective of population or price. First, vendor deprecation: an architecture whose outputs are produced by a hosted model inherits a dependency on an endpoint that a third party may retire, reprice or silently revise, whereas a language-model-free runtime depends only on its own code and data. Second, language-conditioned outcomes, quantified above at up to 4.7 percentage points. Third, the impossibility of bit-exact replay: a coefficient of variation below 0.01% across five runs is statistical stability, not determinism. Earth-1's determinism block passes 6 of 6, with three independent paths — same-seed rebirth, save/load continuation and flag-on-baseline — converging on one world hash, 49bb7d1d949f28f3; an adapter reproduces p_model 0.4311624 exactly; learning-loop replay from the hash-chained ledger is bit-identical. For audit, what matters is that the run reproduces, not that the distribution is narrow.

### 6.7 Projection toward a full-humanity population

The following is a projection, not a measurement, obtained by extending measured laws beyond their measured range. Against the world population anchor of 8,140,897,523, the flat memory law implies resident state of order eight terabytes, and the birth multiplier implies a peak of order twenty-six. The population is roughly eighty times the largest measured configuration, so the n^1.07 tick law implies about a hundred-and-tenfold increase over the measured 924.8-second world-day — of order thirty hours per world-day on a single box.

That defect is registered and unfixed, scheduled as a pre-scale cycle. Scale invariance and census weighting together settle what a larger population is actually for. Because the census is identical across a five-hundredfold range, aggregate accuracy is already population-true at two hundred thousand agents; what more agents buy is individual and subnational resolution, and the statistical power to measure rare events in days of world-time rather than years.

The economic argument is finally a simple one. Removing generative inference from the runtime path is what makes a civilization cheap enough to leave running, cheap enough to re-derive from scratch, and stable enough that a result obtained today can be reproduced exactly a year from now on different hardware. A world that costs almost nothing per day to advance is a world that can be asked questions indefinitely — and one whose entire history can be regenerated for the price of eleven days on a single machine.

## 7. Limitations

What follows is the complete register of defects currently standing against Earth-1, each with its measured consequence and an account of what closing it would require. The list is presented in full, and without mitigation, because it is the substantive claim of this section: a model that fails in enumerable, mechanism-shaped ways is a different kind of object from one that is diffusely wrong. Every entry below names a channel the engine does not contain, an instrument fault found by the engine's own checks, a coverage boundary in the substrate, or a score that fell short of a gate fixed before the run. None of them is a residual, a nuisance term, or an unexplained discrepancy. That property — that each miss resolves to a nameable absence rather than to noise — is what makes the instrument falsifiable, and it is the reason the register is published rather than summarised.

### 7.1 Absent institutional mechanisms

Six institutional channels are absent from the physics, and each has a measured consequence in the record.

There is no unemployment-insurance operator. Unemployment runs at approximately 9.7% against a real 4.8%, roughly twice over, and the same absence propagates into shock response: the COVID retrodiction (frozen at 2020-02-28) produced an unemployment response 3.5 times the real delta. The direction is strongly right (t of order 18) and the overshoot is expected rather than surprising, because the model has no furlough state to absorb displacement. The GFC retrodiction (frozen at 2008-09-14) sits on the other side, at 0.64 times the real 2008-to-2009 delta, direction right at t = 2.2 over sixteen seeds. Closing this requires an operator that holds displaced agents in a supported state rather than moving them directly to hardship.

There is no subsidy, substitution, or stock-drawdown machinery. In the pre-registered UKR-2022 counterfactual — model output frozen and committed before any outcome data was fetched, judged against the GRFC acutely-food-insecure database over 48 countries assessed in both 2021 and 2022 — the engine overshot by 8.5 times (+326M modelled against +38.5M real), returned a geographic Spearman of −0.137, and matched one of five countries in the top-5 overlap. The mechanism was named in a sealed written prior before the fetch, and reality confirmed it: Egypt's real change was exactly zero, absorbed by its bread subsidy. Closing this requires operators for price substitution, state transfer, and inventory buffering.

There is no bond or pension channel, and a UK gilt crisis is consequently invisible to the engine. Frozen at 2022-09-22 and run at full fidelity, the shocked branch was statistically indistinguishable from its control, and the system returned a physics abstention rather than a number. Closing this requires a sovereign-debt and pension-liability channel.

There is no interbank or deposit channel. On the SVB question (frozen at 2023-03-08, contagion to at least two further banks within thirty days) the engine returned a model probability of 0.302; the question resolved YES. Every material line abstained, yet the United States was the top force mover at twice the runner-up — the engine registered the fear and missed the plumbing. The Sri Lanka question (frozen at 2022-03-31, government fall within 120 days) has the same shape: 0.3985 against an event that occurred. Both are under-calls, not misdirections.

The engine abstained rather than fabricating a response. This is recorded as a clean negative result, and it is the clearest illustration of the register's logic — a channel that does not exist produces no signal, which is a more informative failure than a confident wrong number.

Finally, there is no national religiosity input and no geopolitical-alignment input. These are the two worst-performing regions of the opinion surface: religion and values is the worst item family at 3.91 sampling errors against a best family (technology and climate) of 2.97, and per-item losses on the Pew frame concentrate in religion and geopolitics. Closing these requires country-level inputs the substrate does not currently carry.

### 7.2 Instrument defects found and registered rather than patched

Two faults were found in the engine's own apparatus and deliberately left unfixed. The urban indicator in the population substrate is inverted: what the model marks urban is in fact rural, in every country and by exactly one census margin, so the marginal totals remain population-true while the sign is wrong. Two physics consumers are affected — a contagion density multiplier and an air-quality channel. It was registered and not patched because the physics was frozen at the time of discovery, and it is scheduled as a v1.1 cycle under the one-named-change rule. Separately, chronicle cost: a world warmed on ninety days of real news ticks far more slowly than a cold one, with memory spread dominating the tick. It is registered as a pre-scale cycle. The warm-start configuration is the one historical retrodiction requires, and the retrodiction studies reported here stand at 200k agents while the scale ladder reaches 100M.

### 7.3 Substrate coverage limits

Only 63 of 194 countries have survey-measured education and income margins; the remaining 131 joints are constructed by income-tier donor pooling. Age, sex and urban margins are census-derived for all 194, so the fallback affects the socio-economic joint rather than the demographic frame, and the construction beats an independent-marginal baseline by 24.8% on withheld joints at p ≤ 2.4 × 10⁻¹³. That validates the method, not any individual donor's applicability to a particular fallback country. Closing it requires microdata acquisition, country by country.

There is no subnational geography: the country is the finest spatial unit, so within-country heterogeneity has nowhere to reside, and any event whose real footprint is regional can only be scored at national resolution — as the Arab Spring geography was, at Spearman +0.168, p = 0.022 over a 185-country overlap. There is also no household frame: agents are individuals without co-residence, so income pooling, dependency and intra-household transfer are unrepresented. Deep poverty is where the material board is weakest — 16.8% at $3.00/day against a real 10.4%, 1.6 times over — and household pooling is a candidate mechanism there rather than a demonstrated one.

### 7.4 Standing accuracy misses

The opinion readout is behind the region-copy baseline, and this is a miss. On 98 held-out WVS items Earth-1 records 11.84pp MAE against region-copy at 9.70; on the 468-item Pew frame, 12.01 against 10.31. Earth-1 beats the naive baseline only, and the registered ACCEPT tier is ≤ 7.0pp. A replication on 110 additional never-labelled WVS items returned 11.20 against 9.81 — the same verdict, so the miss is not an artefact of item selection. The per-item picture is more textured (outright best of four methods on 64 of 468 Pew items, ahead of region-copy on 137, with wins concentrated in outgroup trust and material hardship) but the aggregate stands: a baseline requiring no simulation currently estimates opinion levels better than the engine does. Closing it requires the two missing country inputs above and a readout that loses less on the families where it loses.

The aggregate event-direction gate failed at 40% against an 80% target. The physics froze at 0.9 as a freeze-with-named-regression: the tag carries that failure, plus five named regressions, rather than a repair that would have reopened the loop. Closing it means adding the missing operators one per cycle, each with its gate fixed by ruling before the run, and re-scoring.

The ladder is flat to 0.7% in bytes per agent across a hundredfold range and the tick scales as n^1.07, so the gap is a resourcing statement rather than a demonstrated architectural ceiling — but it has not been demonstrated, and 324.5 GB peak at 100M on a single 48-core node, with birth requiring roughly 3.2 times the final state as working memory, makes the next decade of scale a hardware question that remains open.

### 7.5 The register as a claim

None of the above is offered as an apology. Each entry specifies a mechanism, a measurement, and a closure path, which means each is independently refutable: an added operator either moves its gate or it does not, and the ruling was fixed before the run. This is why VOID is reserved for defects in the measuring instrument and never for unwelcome results, and why the urban inversion was registered rather than quietly corrected — a freeze that can be amended after seeing the score is not a freeze. A system whose errors are diffuse can absorb any result; a system whose errors are enumerable can be wrong in public, one named mechanism at a time.

## 8. Discussion

### 8.1 One substrate, one grammar, many conditioned populations

The claim organising this work is structural rather than competitive. A conventional agent-based study constructs a population for a question: the population encodes the question's assumptions, and a second question requires a second population, whose relationship to the first is a matter of authorial intent rather than of measurement. Earth-1 inverts that ordering. There is one census-grounded joint population substrate, one behavioural grammar of eight forces acting on every agent, and one deterministic tick; a domain study is obtained by conditioning that population and reading out from its state, not by rebuilding it. This is the sense in which we use the term foundation model — not a pretrained network, but a single load-bearing substrate and grammar onto which many domain-specific populations are conditioned.

The substrate behaves as one object rather than as a family of separately tuned coincidences, and this is measured. Across a 500-fold population range the day-5 census is identical to within 0.08 percentage points on the poverty line; a 4M world over 180 days reproduces the 200k material board within every registered gate (median income 9.52 against 9.605, poverty 45.29% against 45.88%, mean age at death 68.29 against 68.99); and a 100M world tracks its 4M control through equilibration with poverty gaps of 0.01, 0.00, 0.02 and 0.06 percentage points at days 5, 15, 30 and 60, with age at death identical at day 60. Per-agent state stays flat to 0.7% across a hundredfold scale-up. Enlarging the population therefore buys resolution rather than a different world — a property that must be demonstrated, not assumed, before any of what follows is admissible.

The structure is economically load-bearing because the expensive step is paid once. The substrate and grammar carry a fixed construction cost; thereafter the marginal domain question costs a run, and a run costs 981 bytes per agent with zero language-model calls anywhere in the runtime path — one world-day of a 4M world in 60 seconds on a single 48-core machine. The counterfactual is instructive. Executing one prompt per agent per day for that same 4M population, at 500 input and 100 output tokens, is 2.4 billion tokens per world-day, roughly $2,400 per world-day at a dollar per million tokens, which is below frontier pricing. The living world has run past 16,800 world-days. Under a per-agent-prompt regime, cost scales with questions multiplied by agents multiplied by days; under a shared-substrate regime it does not.

It is scientifically load-bearing for the mirror-image reason. Because one grammar serves every domain, a defect discovered in one place is a defect everywhere, and its repair is testable everywhere. Each is one missing mechanism with consequences in several places at once. Tight coupling is a liability for accuracy and an asset for falsification, and we regard the second as the more valuable of the two at this stage.

### 8.2 Population as a substitute for world-time

Rare events are rare per agent-year, which is why the empirical study of crises is a study of small samples. A simulator whose aggregate behaviour is invariant to population size converts sample size in the time dimension into sample size in the population dimension: one can observe more realisations of a rare configuration without waiting longer, and without accepting a different world as the price. The scale-invariance measurements above are what license that exchange. The same statistical logic is visible in the ensemble dimension: on the 2008 frozen forecast, the direction of the unemployment response was not significant at five replicates (t = 0.7) and was significant at sixteen seeds (t = 2.2), with the response itself 0.64 times the real 2008-to-2009 delta. Nothing about the world changed; only the number of realisations did.

The honest limit is that Earth-1's measured ceiling is presently 100M agents on a single AMD EPYC 9454P — birth in 756.7 seconds, 924.8 seconds per world-day, 324.5 GB peak. That is an order of magnitude below the one billion agents demonstrated by Light Society.

### 8.3 The boundary we do not cross

The project's own governing document forbids benchmarking against frontier language models, and that prohibition is a design constraint rather than a rhetorical hedge: a comparison of that kind would import into the calibration ladder a dependency the ladder exists to exclude.

The claim actually made is narrower and, we would argue, harder to dismiss. It is that this object is deterministic, that it is falsifiable, that it is cheap enough to keep running, and that it has been scored against reality and has posted its losses. Determinism here is literal: three independent paths — same-seed rebirth, save/load continuation, and flag-on-baseline — return one identical world hash, and the adapter reproduces a probability of 0.4311624 exactly. This is a different property from the reproducibility reported for the comparison class, where a coefficient of variation below 0.01% across five runs establishes statistical stability rather than reproduced identity, and where the authors state plainly that their results are conditional on the underlying language model — swapping Chinese for French moves the stance-change rate by up to 4.7 percentage points, with topic-dependent sign — and that their outputs are best read as hypotheses rather than as evidence about real societies.

Scoring against reality is what the determinism is for, and the scores include clear misses that we report as such. The pre-registered Ukraine counterfactual missed on all three registered axes: 8.5-fold magnitude overshoot, geographic Spearman correlation of −0.137, and one of five on top-five overlap. What that exercise did produce was a sealed written prior that named all three failures and their mechanism in advance, and a confirmation in the outcome data — Egypt's real change of exactly zero, absorbed by its bread subsidy. A model that can lose a pre-registered bet, and does, occupies a different epistemic position from one that cannot be placed in the position of losing.

## 9. Methods (overview)

This section describes what exists and how it is evaluated. It is deliberately not a reproduction specification: update equations, fitted constants, functional forms, injector templates, lexicon contents and internal module structure are withheld. The claims in this paper rest on measured outputs against registered gates and sealed judges, not on disclosed internals.

**Substrate construction and provenance.** The population is a per-country joint distribution over five demographic dimensions — sex, age band, education, income and urbanicity — yielding 216 cells for each of 194 countries. Age, sex and urban margins are census-derived for all 194. The joint is recovered by iterative proportional fitting over pooled donors, which beats an independent-marginal baseline by 24.8% on withheld joints at p ≤ 2.4 × 10⁻¹³. The adult age pyramid is derived from stable-population density using each country's own Gompertz survival rather than a parametric draw. Every agent carries a census weight equal to the ratio of its country's census share to its share of the simulated population, so that global figures are population-true at any sample size; the world anchor is 8,140,897,523 (World Bank SP.POP.TOTL 2024).

**Behavioural grammar.** Agent behaviour is generated by eight forces that act on every agent in every domain. The grammar is uniform: there are no domain-specific behavioural rules layered on top for particular studies, which is what makes a defect in one domain diagnostic for the others. The forces' definitions, couplings and constants are withheld.

**Deterministic tick and paired branch contrast.** The world advances by a deterministic tick; identical inputs return an identical world. Determinism is verified on three independent paths — rebirth from the same seed, continuation from a saved state, and running with the branch flag enabled on the baseline — all of which produce one world hash. Interventions are evaluated as a paired contrast between a branch and its null under common random numbers, so that the two worlds differ only by the intervention.

**Calibration ladder and pre-registered gates.** Calibration proceeds one named change per cycle, with acceptance gates fixed by written ruling before the run that tests them. Gates are stated as thresholds on named quantities, and results falling outside them are recorded as regressions rather than absorbed. VOID is reserved exclusively for defects in the measuring instrument and is never available for an unwelcome result. Physics was frozen at 0.9 as a freeze-with-named-regression, the tag carrying the failed event-direction gate and five named regressions.

**Frozen-forecast protocol.** For historical retrodiction, a world is born at a date T on real archive news, under a mechanical assertion that no input, anchor or news item postdates T. The model output is then frozen and committed. Only after the commit is the outcome data fetched. This ordering is enforced by the commit history rather than by assurance.

**Sealed-judge protocol.** Each evaluation registers its judge by name and location before the run, with outcome values left unfetched until the output is frozen — for the Ukraine counterfactual, a specific release of the Global Report on Food Crises acutely-food-insecure database, identified by content hash, restricted to the 48 countries assessed in both comparison years. Where a written prior exists it is sealed alongside the output and opened with it.

**Readout.** Opinion estimates are produced by a readout from agent state to survey-item response, evaluated leave-one-country-out across 21,776 scored item-country cells with abstention on items requiring named-entity knowledge; abstained cells are excluded from both the model and the baselines. The readout's construction is withheld.

**Availability.** The engine exposes a versioned interface for questions, consequence reports, world state and history, and population-frame discovery, so that the results described here can be reproduced against a running world rather than taken on the report's word. Every answer it returns carries its calibration tier, its provenance, and the configuration stamp of the physics that produced it; a run whose stamp does not match the frozen configuration is refused rather than silently served.

---

## Colophon

**Reproducibility.** Every quantity in this paper is produced by the frozen physics
configuration designated freeze-0.9 and is reproducible from the recorded configuration
stamp. A run whose stamp does not match is refused by the engine rather than silently
accepted.

**Held-out data.** The holdout and prospective estates remain sealed. Figures reported
here come from the training and development estates only; no number in this paper was
computed on sealed data.

**Withheld.** Force update equations, fitted constant values, calibration readout
formulae, injector templates, the registered vocabulary and internal module structure
are proprietary and are described functionally rather than reproduced.
