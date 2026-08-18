# WORLD — the specification for a planet

Pietro, 2026-08-18: *"I want all the emergence patterns across everything
to actually work. Earthlings need to behave in ways that we didn't
predict. They need to be ALIVE."*

This is the spec for that. Every requirement he named is in here, mapped
to the layer that carries it, with the test that says whether it works.

Nothing in this document is aspirational. A line either names something
built, or names something with a defined mechanism and a defined test.

---

## 0. The design principle everything else follows from

**Irreducibility comes from nonlinearity and coupling, not from
substrate size.**

The Lorenz system has three state variables and is permanently
unpredictable. A system with 10^80 particles and linear dynamics is
perfectly predictable forever. Simulating electrons would make Earth-1
enormously more expensive and not one bit more mysterious.

So the mystery is built where it actually lives:

- **nonlinear coupling** — thresholds, cascades, conviction-weighted
  influence, feedback from opinion back onto trait
- **correlated shocks through structure** — a firm fails, four hundred
  people lose income in the same tick, and the graph carries it outward
- **compounding without reconvergence** — a drained agent cannot absorb
  the next shock, so trajectories that started together never rejoin
- **observation that changes the observed** — see §6

And then it is **measured**, not asserted: §7 defines the Lyapunov test
that says whether this world is genuinely chaotic or merely complicated.

---

## 1. MATTER — the material substrate  ✅ BUILT

`earth1/life.py`. Occupations, firms, wages, savings measured in days of
survival, the daily cost of food and shelter, job loss, scarring,
informal economy, the welfare state.

Firms are the load-bearing structure: they fail, and failure lays off
everyone inside at once. That is what makes hardship correlated rather
than averaged away.

**Measured**: economics force std 0.2205 → 0.3396; max rule participation
0.292 → 0.763 across 101 countries; threshold sweep at 0.30 went from 1
event to 318. Unemployment equilibrates near 9%.

**Open**: the destitution rate lands at 34.5% against a pre-registered
bar of 25%. Reported as a FAIL rather than re-set after the fact. The
bar was written with rich-world intuition and applied to 194 countries
where ~44% of humanity lives under $6.85/day, so the bar is probably
what is wrong — Pietro's call, not a number to quietly adjust.

---

## 2. SOCIETY — who knows whom, and why  ⏳ NEXT

The graph is currently a random draw with homophily. It becomes a
*consequence* of the material layer:

| tie | source | what it carries |
|---|---|---|
| household | partners, children, elders | income pooling, shared shocks |
| colleagues | same firm | job loss arrives together |
| neighbours | region × settlement | crime, heat, local events |
| friends | homophily on trait + proximity | opinion, taste, contagion |
| followers | hub nodes (§4) | asymmetric broadcast |

**Mechanism**: marriage and partnering as matching on age, education and
proximity; children as real dependents who change household cost and
labour supply; ties that *decay* when the shared context ends — you stop
seeing colleagues when you lose the job.

**Test**: hardship must spread further than the firm it started in, and
the spread must follow the graph rather than the country average.

---

## 3. NEEDS AND THE BODY  ⏳

Sex, pleasure, drugs, addiction, illness, mental health — at real
population distributions, not as decoration.

**Mechanism**: each agent carries a small vector of appetites and
vulnerabilities. Substance use has a dose-dependent hazard of
dependence; dependence raises consumption, drains buffer, damages
employment prospects, and feeds back onto trait. Mental illness has
prevalence by age and sex from real epidemiology, with onset hazards
modulated by deprivation and social isolation — both of which the model
now computes rather than assumes.

**Why it belongs**: these are among the strongest known moderators of
opinion, participation and trust. They are not flavour, they are
variance.

**Test**: prevalence must match published epidemiological distributions
by age, sex and country tier *without being fitted to them* — the
distributions are an out-of-sample check, not a target.

---

## 4. INSTITUTIONS AND CULTURE  ⏳

- **Crime** — local, stochastic, with victims and witnesses. Raises fear
  in a neighbourhood, not a nation. Unpredictable by construction.
- **Government** — one per country, with a policy state: tax, welfare
  generosity, policing, war footing. Policy changes the parameters
  agents live under, so §1's SAFETY_NET stops being a constant and
  becomes a decision. Governments respond to their own population's
  state, which closes a loop between opinion and the conditions that
  produce opinion.
- **War** — a state between countries that reallocates the economy,
  conscripts, kills, displaces, and dominates the media channel.
- **Celebrities, scientists, media** — hub nodes with asymmetric degree.
  Science accumulates a knowledge stock that shifts what is believable.
- **Sport, cars, leisure** — shared attention and identity. Cheap to
  model, and genuinely load-bearing for group identity.

**Test**: policy divergence between two governments facing identical
conditions must produce measurably different populations within a year.

---

## 5. PLANET — the fields agents live inside  ⏳

Light, heat, cold, oxygen, water, ocean, season, storm.

These enter as **fields the agent is coupled to**, which is the level at
which they change behaviour:

- **heat** — mortality, unrest, productivity loss; heat waves are
  spatially correlated shocks, exactly the kind §1 showed matter
- **light** — daylight hours by latitude and season, driving mood
- **oxygen / altitude** — physiology by elevation
- **ocean** — fishing as livelihood, shipping, storms, coastal exposure,
  sea level; a coastal agent and an inland agent face different worlds
- **season** — agriculture, income seasonality, disease

**Not modelled, and why**: electrons, photons as particles, and
electromagnetic field equations. They are the substrate *of* heat and
light rather than an alternative to them, and resolving them would
change no earthling's behaviour while costing everything. Heat that
kills and light that changes mood are the parts that reach a person.
This is the one place the spec deliberately stops, and §0 is the reason.

---

## 6. THE MULTIVERSE, AT EARTHLING LEVEL  ⏳ partially built

Today `rehearse()` branches the *world*. The requirement is that every
*agent* carries superposed futures.

**Mechanism**: an agent's stance is already a superposition — the
Born-rule readout in `earth1/readout.py` collapses R_yes²/(R_yes²+R_no²)
into a probability. Extend that from stance to *trajectory*: each agent
holds a distribution over its own next states, and the world holds the
product. Collapse happens on observation.

**Observation changes the observed, and this is not a metaphor here.**
Two independent reasons, and they coincide:

1. *Empirically true of humans.* Asking someone their opinion causes
   them to form one. Survey researchers have measured this for decades
   as attitude crystallisation. A question is an intervention.
2. *Architecturally true at 8.3B.* See §8 — an unobserved agent is
   carried as a distribution and only instantiated as a concrete
   individual when someone looks. Looking is what collapses it.

Manifesting-by-observation is therefore a real mechanic of this engine,
not a mystical layer bolted on: the act of asking Earth-1 a question
perturbs Earth-1.

---

## 7. CHAOS, ENTROPY, AND THE BUTTERFLY — measured, not claimed  ⏳ NOW

The requirement "behave in ways we didn't predict" is testable, and it
is the single most important test in this document.

**The butterfly test.** Two worlds, identical seed, identical draws. In
one of them, one agent — out of hundreds of thousands — loses their job
on day zero. Run both forward. Measure how far the difference spreads
and how fast.

- **chaotic**: divergence grows exponentially, positive Lyapunov
  exponent, and reaches agents with no connection to the perturbed one
- **merely complicated**: divergence stays local and bounded, and the
  world is predictable in principle — a spreadsheet with weather

Entropy is tracked as the Shannon entropy of the population's force
distribution over time: a world that loses entropy is collapsing toward
a fixed point and is not alive.

**This is the honest arbiter of whether any of this worked.** A world
that fails it is decoration regardless of how many subsystems it has.

---

## 8. EIGHT POINT THREE BILLION

Full fidelity for 8.3B agents on one machine is not physically possible:
the state alone is ~930 GB before the social graph, and the graph at 20
ties each is 166 billion edges.

The architecture that does deliver it is **multi-resolution with
observation-triggered instantiation**:

- the world is carried as a **hierarchy**: 8.3B agents represented as
  distributions over cells (country × region × cohort × material state),
  with a full-fidelity sample instantiated inside each cell
- **zoom in and an individual becomes concrete.** Ask about a specific
  person, or follow someone walking down a street, and that agent is
  instantiated at full resolution — traits, job, household, ties,
  history — drawn from the distribution its cell carries, and thereafter
  persisted as a real individual
- population totals, force distributions and aggregate dynamics are
  exact at 8.3B; only the *identity* of unobserved individuals is
  deferred

This is not a compromise on the vision. It is §6's observer effect
expressed as an architecture: **an earthling exists as a distribution
until someone looks at it, and looking is what makes it a person.** The
metaphysics Pietro asked for and the engineering that scales to 8.3B are
the same design.

---

## 9. ALWAYS ALIVE

No timer. A persistent process, ticking continuously, reading news as it
arrives rather than on a schedule, with the world state journalled so it
survives restarts and can be replayed.

Blocked pending permission: this is a persistent change to production
infrastructure on the world host.

---

## Order of build

Each layer is gated on the one before, because each supplies the
variance the next one needs.

1. ✅ **Matter** — done, and it unlocked the threshold detector
2. ⏳ **Chaos measurement** — before building further, find out whether
   what exists is already chaotic. This decides everything after it.
3. **Society** — households, marriage, colleagues, decay
4. **Always-alive process**
5. **Body and needs** — drugs, addiction, illness, sex
6. **Institutions** — crime, government, war, hubs
7. **Planet** — heat, light, ocean, season
8. **Earthling multiverse** — superposed trajectories, collapse on
   observation
9. **8.3B** — the hierarchy, and instantiation on zoom

Step 2 comes before step 3 deliberately. If one agent losing a job
already propagates chaotically through a population of 200,000, that is
the finding — and it changes what every later layer needs to do.
