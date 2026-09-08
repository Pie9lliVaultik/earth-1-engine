# EMERGENCE AUDIT — all 32 tick-path modules (2026-09-08)

Commissioned because a paper draft repeated a docstring's claim that fat tails
"emerged" from correlated shocks. Measurement showed the heavy-tailed wage
distribution is present AT GENESIS (kurtosis 247.01 at birth vs 246.76 after 120
days) and is fitted to a World Bank target. The audit asked whether that error was
isolated. It was not.

Method: six auditors over the 32 modules reachable from `live_one_day`, instructed
to read CODE and treat every docstring as an unverified hypothesis. Per-cluster
reports in `ops/alive/audit/`.

## FINDING 1 — mechanisms that are dead or disabled in the live path
- **Cascades write nothing.** `thresholds.py` is not the live detector; `alive.py`
  imports only the rule list and re-implements detection inline (`alive.py:470-523`)
  with different locality, critical fraction and semantics. A firing writes into no
  dynamical quantity; the decayed level is a read-time overlay for the readout only.
  `cascades_fired` is an INSTRUMENT READING, not a mechanism. The docstring's
  "emergent cascading dynamics" cannot occur in this world.
- **Contagion is an algebraic no-op.** `CONTAGION_GAIN = 0.0`; measured
  `contagion_moved = 0.0` on 150/150 days. The crowd gate is unreachable
  (`CROWD_AROUSAL = 0.82` exceeds the global FEAR maximum of 0.7935): 0 crowds and
  0 riots in 120 days.
- **Mobility imports no disease.** 0 imports in 2,666 flights, and no onward
  transmission exists anywhere (`health.py` has no contact or density term).
- **`generational_tick` is not in the live world.** Births run through
  `rebirth.apply_rebirth`; the demographic claims in `generational.py` describe a
  parallel non-production authority whose inheritance geometry contradicts the live one.
- **`opinion_feedback` is unreachable** from `live_one_day`.

## FINDING 2 — the influence operator is a CONTRACTION, not an expansion
The docstring's argument ("people do not average, they ALIGN… turns the operator
from a contraction into an expansion") describes `propagate_meanfield_legacy`, which
is retired. The canonical `propagate` moves each agent a fixed step toward a
partner's VALUE with no pole term — a contraction. The variance-expansion and
polarization story does not apply to the operator the world runs.

## FINDING 3 — agent-to-agent transmission is real, but its magnitude is unmeasured
`propagate` → `dyadic_move` reads a named partner's current value and moves the
reader toward it: genuine transmission, not shared response to a common input.
BUT three confounds on the same path produce neighbour-correlated opinion with NO
transmission: a homophilous genesis graph, a genesis-anchored restoring target, and
memory press (literally a common input). The A−B ablation (zero the transmission
constants, hold everything else) is the only defensible measure and HAS NOT BEEN RUN.

## FINDING 4 — long-run inequality is not grown
"There is no mechanism anywhere in the engine that can create new mass in the wage
tail." Wage is copied forward unchanged at rebirth with zero mobility; wealth is
re-drawn from zero each generation. Worse, the live birth operator blends traits
toward the GLOBAL mean and forces 50/50 toward the planetary mean, systematically
destroying between-country structure — `rebirth.py:27-32` admits it. What IS
emergent is within-generation wealth concentration (p99/p50 11.88 → 29.48; top-1%
share 0.122 → 0.194 over 120 days).

## FINDING 5 — genesis contains essentially no emergence
Every agent attribute at t=0 is drawn, algebraically transformed, or looked up.
Measured between-country variance shares: empathy 1.9%, conscientiousness 0.7% —
the "soul" traits are ~98% hand-set noise. The EXPERIENCE force IS `civ.age`
(identity map, rewritten every tick), so any result attributed to it is attributed
to age. 84/194 countries carry imputed (regional-mean) Hofstede values; 118/194
carry a single constant Inglehart pair.

## FINDING 6 — two methodological defects affecting PUBLISHED numbers
- **Seed-independent influence randomness.** `influence.py:242` and `feed.py:173`
  seed private generators from the DAY INDEX ALONE. Every world, at every seed,
  draws identical encounter uniforms on day d. **An ensemble over seeds does not
  sample the influence channel's randomness at all** — every Monte-Carlo error bar
  on an opinion observable is understated by an unquantified amount.
- **Two orchestrators exist.** `earth1/tick.py::world_tick` is a structurally
  different loop that DOES close the cascade loop, and is still used by `g5.py`,
  `living.py`, `advance.py`. Any published number must state which loop produced it.

## FINDING 7 — two defects that corrupt figures
- `api/readouts.py:394` publishes `unrest_norm` (the 500-day habituation baseline)
  under the field name `"unrest"`. Actual unrest is never stored.
- `rehome.py:142` clamps the ENTIRE tie matrix rather than the added edges, so the
  first hire day and first migration day flatten tie weights to nominal constants.

## WHAT SURVIVES, UNAFFECTED
These are measurements of OUTPUT and do not depend on any mechanism narrative:
determinism (6/6, three paths one hash); the LLM-free property (32 modules traced,
zero network imports); the material board against fetched anchors; scale invariance
and the board holding at 20x; distance-from-humans (including its miss against
region-copy); the frozen-forecast retrodictions; the learning-loop gates.
Notably, the Arab Spring result — material stress out-predicting fear on real
protest geography — is CONSISTENT with this audit: the collective machinery is
largely inert, so a material-channel explanation is the correct one.

## CONSEQUENCE FOR THE PAPER
The white paper cannot claim emergence broadly, cannot use the words "cascade",
"contagion" or "polarization" as mechanisms, and cannot present long-run inequality
as grown. The defensible paper is narrower and rests on determinism, census
grounding, LLM-free economics, and scored outputs — with an explicit section on
which mechanisms are inert. Publishing that section is itself the contribution.
