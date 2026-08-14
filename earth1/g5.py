"""G5 harness — "the world is alive" (bible v2 §21).

Three pre-registered legs, protocol in data/g5_preregistration.json
(committed before any results run — results after a protocol change
require a new registration entry):

  1. TEMPORAL   — calibrate on WVS Wave 6 only, evolve the living world
                  through the W6→W7 interval with every endogenous
                  mechanism on and zero hand-authored drift, re-predict
                  with the same weights, score predicted deltas against
                  observed deltas vs. the no-change baseline.
  2. EVENT      — inject a documented real event (COVID rally-round-the-
                  flag, Eurobarometer EB92→EB93) as an a-priori force
                  shock; the simulated trust shift must match the
                  measured one in sign and order of magnitude.
  3. DEMOGRAPHY — the generational tick alone must reproduce census
                  life expectancy per country and a plausible adult
                  crude death rate.

On failure: fix the physics or narrow the domain — never let the LLM
decide (bible v2 §7 risk table).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy import stats as sp_stats

from earth1.types import Civilization, Question, Force, NUM_FORCES
from earth1.genesis import genesis, GENESIS_COUNTRIES
from earth1.calibration import calibrate_single
from earth1.rng import logit, sigmoid
from earth1.event_log import EventLog, WorldEvent
from earth1.tick import WorldState, world_tick, _make_mutable
from earth1.generational import generational_tick
from earth1.wvs_paired import WVS_PAIRED, WVSPairedQuestion


# ── shared: anchored prediction ─────────────────────────────────────────
#
# calibrate_single centers features on civ.means, but civ.means is
# recomputed as the world evolves — predicting at t1 with t1 means would
# silently subtract global secular drift out of the very signal G5
# measures.  All G5 predictions center on the t0 means anchor.

def _predict_country_anchored(
    civ: Civilization,
    baseline: float,
    weights: np.ndarray,
    country_idx: int,
    t0_means: np.ndarray,
    extra_shift: Optional[np.ndarray] = None,
) -> Optional[float]:
    """Per-country prediction with feature centering frozen at t0.

    extra_shift: optional (N, NUM_FORCES) additive force deltas (e.g.
    active event-log deltas at prediction time).
    """
    mask = civ.country == country_idx
    if mask.sum() < 10:
        return None
    feats = civ.forces[mask] - t0_means[np.newaxis, :]
    if extra_shift is not None:
        feats = feats + extra_shift[mask]
    b = logit(np.array([baseline]))[0]
    return float(sigmoid(b + feats @ weights).mean())


def _country_index_map() -> Dict[str, int]:
    return {c["iso2"]: i for i, c in enumerate(GENESIS_COUNTRIES)}


# ── leg 1: temporal ─────────────────────────────────────────────────────

@dataclass
class TemporalLegResult:
    n_pairs: int
    n_sign_pairs: int
    mae_engine: float
    mae_nochange: float
    sign_accuracy: float
    sign_p: float
    passes: bool
    per_question: List[Dict]


def g5_temporal(
    pop: int = 50_000,
    seed: int = 42,
    years: float = 7.0,
    dt_days: float = 30.0,
    min_obs_delta: float = 0.02,
    questions: Optional[List[WVSPairedQuestion]] = None,
    progress: bool = False,
    replay_events: Optional[Dict[int, List]] = None,
) -> TemporalLegResult:
    """The temporal leg: does the evolved world track observed deltas
    better than no-change?

    replay_events (amendment A2): {step_index: [WorldEvent, ...]} of
    historical exogenous signal, injected into the event log as the
    world reaches each step. Requires dt_days to match the replay's
    monthly grid (events are stamped t = month_index * 30)."""
    questions = questions if questions is not None else WVS_PAIRED
    civ = _make_mutable(genesis(pop, seed))
    cmap = _country_index_map()

    # calibrate on Wave 6 ONLY — Wave 7 is held out in time
    calibrated: List[Tuple[WVSPairedQuestion, float, np.ndarray]] = []
    for pq in questions:
        w6 = pq.wave6
        baseline = float(np.mean(list(w6.values())))
        weights = calibrate_single(civ, baseline, w6)
        if not np.any(weights):
            continue
        calibrated.append((pq, baseline, weights))

    t0_means = civ.means.copy()

    # t0 predictions (the engine's own W6-era read, per country)
    t0_pred: Dict[str, Dict[str, float]] = {}
    for pq, baseline, weights in calibrated:
        t0_pred[pq.id] = {}
        for cc in pq.overlapping_countries:
            if cc not in cmap:
                continue
            p = _predict_country_anchored(civ, baseline, weights, cmap[cc], t0_means)
            if p is not None:
                t0_pred[pq.id][cc] = p

    # evolve: every endogenous mechanism on, zero authored drift,
    # receiver off (no historical replay in v1)
    tick_questions = [
        Question(id=pq.id, text=pq.text, domain="belief_causal",
                 baseline=baseline, weights=weights, lens="wvs")
        for pq, baseline, weights in calibrated
    ]
    state = WorldState(
        civ=civ, event_log=EventLog(), t=0.0, tick_count=0,
        question_history=[], coupling_matrix={}, last_fired={},
        rng=np.random.default_rng(seed),
    )
    n_steps = int(round(years * 365.0 / dt_days))
    for step in range(n_steps):
        if replay_events:
            for ev in replay_events.get(step, []):
                state.event_log.append(ev)
        world_tick(state, questions=tick_questions, dt=dt_days)
        generational_tick(state.civ, state.rng, dt_days=dt_days)
        if progress and (step + 1) % 12 == 0:
            print(f"  temporal: {(step + 1) * dt_days / 365.0:.1f}y / {years:.0f}y")

    # t1 predictions with the SAME weights, t0-anchored centering
    per_question = []
    pred_deltas, obs_deltas = [], []
    for pq, baseline, weights in calibrated:
        q_pred, q_obs = [], []
        for cc in pq.overlapping_countries:
            if cc not in t0_pred[pq.id]:
                continue
            p1 = _predict_country_anchored(
                state.civ, baseline, weights, cmap[cc], t0_means)
            if p1 is None:
                continue
            q_pred.append(p1 - t0_pred[pq.id][cc])
            q_obs.append(pq.wave7[cc] - pq.wave6[cc])
        pred_deltas.extend(q_pred)
        obs_deltas.extend(q_obs)
        if q_obs:
            per_question.append({
                "question_id": pq.id,
                "n_countries": len(q_obs),
                "mae_engine": round(float(np.mean(np.abs(
                    np.array(q_pred) - np.array(q_obs)))), 5),
                "mae_nochange": round(float(np.mean(np.abs(q_obs))), 5),
                "mean_pred_delta": round(float(np.mean(q_pred)), 5),
                "mean_obs_delta": round(float(np.mean(q_obs)), 5),
            })

    pred = np.array(pred_deltas)
    obs = np.array(obs_deltas)
    mae_engine = float(np.mean(np.abs(pred - obs))) if len(obs) else 1.0
    mae_nochange = float(np.mean(np.abs(obs))) if len(obs) else 0.0

    sign_mask = np.abs(obs) >= min_obs_delta
    n_sign = int(sign_mask.sum())
    if n_sign > 0:
        hits = int((np.sign(pred[sign_mask]) == np.sign(obs[sign_mask])).sum())
        sign_accuracy = hits / n_sign
        sign_p = float(sp_stats.binomtest(hits, n_sign, 0.5,
                                          alternative="greater").pvalue)
    else:
        sign_accuracy, sign_p = 0.0, 1.0

    passes = (mae_engine < mae_nochange
              and sign_accuracy > 0.5 and sign_p < 0.05)

    return TemporalLegResult(
        n_pairs=len(obs), n_sign_pairs=n_sign,
        mae_engine=round(mae_engine, 5),
        mae_nochange=round(mae_nochange, 5),
        sign_accuracy=round(sign_accuracy, 4),
        sign_p=round(sign_p, 5),
        passes=passes, per_question=per_question,
    )


# ── leg 1b: temporal with historical replay (amendment A2) ──────────────

@dataclass
class TemporalReplayResult:
    endogenous: TemporalLegResult
    real: TemporalLegResult
    shuffled: TemporalLegResult
    passes: bool


def _replay_receiver_config():
    """Replay-specific config: monthly-resolution events need a
    month-scale half-life (the live gdelt default of 3 days would
    evaporate a monthly signal almost immediately)."""
    from earth1.receiver import ReceiverConfig, SourceConfig
    return ReceiverConfig(sources=[
        SourceConfig("gdelt", gain=0.1, decay_half_life=30.0),
    ])


def g5_temporal_replay(
    history: Dict,
    pop: int = 50_000,
    seed: int = 42,
    dt_days: float = 30.0,
    progress: bool = False,
) -> TemporalReplayResult:
    """Amendment A2: the temporal leg with exogenous historical forcing
    and its own inline §14 placebo control.

    Three conditions, identical seeds:
      endogenous — no replay (the A1-era protocol, for reference)
      real       — GDELT 2017-2022 signals on the correct countries
      shuffled   — the same signals, country labels permuted

    Pass: real beats no-change on MAE, beats shuffled on MAE, and has
    sign accuracy > 0.5 at p < 0.05. If real does not beat shuffled,
    the signal is noise, not geography-carrying information.
    """
    from earth1.replay import build_replay_events, shuffle_history_geography

    months = sorted({m for c in history.values() for m in c.get("tone", {})})
    years = max(1.0, len(months) * dt_days / 365.0)
    config = _replay_receiver_config()

    if progress:
        print(f"  replay window: {months[0]}..{months[-1]} "
              f"({len(months)} months, {years:.1f}y)")
        print("  condition 1/3: endogenous...")
    endo = g5_temporal(pop=pop, seed=seed, years=years, dt_days=dt_days,
                       progress=progress)

    if progress:
        print("  condition 2/3: real geography...")
    real_events = build_replay_events(history, config)
    real = g5_temporal(pop=pop, seed=seed, years=years, dt_days=dt_days,
                       progress=progress, replay_events=real_events)

    if progress:
        print("  condition 3/3: shuffled geography (§14 control)...")
    shuf_rng = np.random.default_rng(seed + 1)
    shuf_events = build_replay_events(
        shuffle_history_geography(history, shuf_rng), config)
    shuffled = g5_temporal(pop=pop, seed=seed, years=years, dt_days=dt_days,
                           progress=progress, replay_events=shuf_events)

    passes = (real.mae_engine < real.mae_nochange
              and real.mae_engine < shuffled.mae_engine
              and real.sign_accuracy > 0.5 and real.sign_p < 0.05)

    return TemporalReplayResult(
        endogenous=endo, real=real, shuffled=shuffled, passes=passes,
    )


# ── leg 2: event reaction ───────────────────────────────────────────────

@dataclass
class EventCase:
    """A documented real event with measured before/after poll values.

    Values compiled from published toplines — verify against the archive
    named in `source` before publication.
    """
    id: str
    description: str
    source: str
    question_text: str
    pre: Dict[str, float]          # country -> measured pre-event value
    post: Dict[str, float]         # country -> measured post-event value
    force_deltas: Dict[int, float]  # authored a priori, never tuned
    window_days: float
    decay_half_life: float


# COVID-19 rally-round-the-flag: trust in national government,
# Standard Eurobarometer 92 (autumn 2019) -> 93 (summer 2020).
# Country toplines compiled from published EB reports — verify at GESIS.
COVID_RALLY = EventCase(
    id="covid_rally_2020",
    description="COVID-19 onset: trust in national government rises "
                "across the EU (rally-round-the-flag), EB92->EB93.",
    source="Standard Eurobarometer 92/93 toplines (GESIS archive)",
    question_text="Do you tend to trust your national government?",
    pre={"DE": 0.45, "FR": 0.25, "IT": 0.22, "ES": 0.18, "NL": 0.61,
         "PT": 0.39, "AT": 0.51, "FI": 0.58, "SE": 0.47, "PL": 0.37},
    post={"DE": 0.60, "FR": 0.30, "IT": 0.31, "ES": 0.20, "NL": 0.70,
          "PT": 0.51, "AT": 0.64, "FI": 0.68, "SE": 0.57, "PL": 0.31},
    force_deltas={int(Force.FEAR): 0.15, int(Force.COLLECTIVE): 0.10},
    window_days=90.0,
    decay_half_life=45.0,
)


@dataclass
class EventLegResult:
    case_id: str
    n_countries: int
    simulated_mean_shift: float
    measured_mean_shift: float
    sign_match: bool
    magnitude_ratio: float
    passes: bool
    per_country: List[Dict]


def g5_event_reaction(
    case: EventCase = COVID_RALLY,
    pop: int = 50_000,
    seed: int = 42,
    dt_days: float = 30.0,
) -> EventLegResult:
    """The event leg: inject the documented shock, compare the simulated
    shift to the measured one."""
    civ = _make_mutable(genesis(pop, seed))
    cmap = _country_index_map()

    # calibrate on PRE-event values only
    baseline = float(np.mean(list(case.pre.values())))
    weights = calibrate_single(civ, baseline, case.pre)
    t0_means = civ.means.copy()

    countries = [cc for cc in case.pre if cc in cmap and cc in case.post]
    t0_pred = {}
    for cc in countries:
        p = _predict_country_anchored(civ, baseline, weights, cmap[cc], t0_means)
        if p is not None:
            t0_pred[cc] = p

    # inject the shock — one event per affected country
    q = Question(id=case.id, text=case.question_text, domain="belief_causal",
                 baseline=baseline, weights=weights, lens="eb")
    state = WorldState(
        civ=civ, event_log=EventLog(), t=0.0, tick_count=0,
        question_history=[], coupling_matrix={}, last_fired={},
        rng=np.random.default_rng(seed),
    )
    for cc in countries:
        state.event_log.append(WorldEvent.create(
            timestamp=0.0,
            force_deltas=dict(case.force_deltas),
            region_pattern=f"{cc}-*",
            decay_half_life=case.decay_half_life,
            source=f"g5:{case.id}",
        ))

    n_steps = max(1, int(round(case.window_days / dt_days)))
    for _ in range(n_steps):
        world_tick(state, questions=[q], dt=dt_days,
                   enable_event_generation=False)
        generational_tick(state.civ, state.rng, dt_days=dt_days)

    # measure at the end of the window WITH the still-active event field
    event_deltas = state.event_log.effective_deltas_vectorized(
        state.t, state.civ)
    per_country = []
    sim_shifts, meas_shifts = [], []
    for cc in countries:
        if cc not in t0_pred:
            continue
        p1 = _predict_country_anchored(
            state.civ, baseline, weights, cmap[cc], t0_means,
            extra_shift=event_deltas)
        if p1 is None:
            continue
        sim = p1 - t0_pred[cc]
        meas = case.post[cc] - case.pre[cc]
        sim_shifts.append(sim)
        meas_shifts.append(meas)
        per_country.append({"country": cc,
                            "simulated": round(sim, 5),
                            "measured": round(meas, 5)})

    sim_mean = float(np.mean(sim_shifts)) if sim_shifts else 0.0
    meas_mean = float(np.mean(meas_shifts)) if meas_shifts else 0.0
    sign_match = bool(np.sign(sim_mean) == np.sign(meas_mean) and sim_mean != 0)
    ratio = sim_mean / meas_mean if meas_mean != 0 else 0.0
    passes = sign_match and 0.25 <= ratio <= 4.0

    return EventLegResult(
        case_id=case.id, n_countries=len(sim_shifts),
        simulated_mean_shift=round(sim_mean, 5),
        measured_mean_shift=round(meas_mean, 5),
        sign_match=sign_match,
        magnitude_ratio=round(ratio, 4),
        passes=passes, per_country=per_country,
    )


# ── leg 3: demography (amendment A1: cohort metric) ─────────────────────

@dataclass
class DemographyLegResult:
    years: float
    total_deaths: int
    world_adult_cdr: float          # per 1000 agents per year
    n_countries_scored: int         # here: distinct census LE values tested
    le_tracking: float              # fraction of LE values within +/- 6y
    passes: bool
    per_country: List[Dict]


def _simulate_cohort_le(
    life_expectancy: float,
    rng: np.random.Generator,
    n: int = 4_000,
    dt_days: float = 30.0,
) -> float:
    """Step a synthetic cohort from 18 to extinction through the SAME
    hazard formula and dt-scaling the generational tick uses; return
    the cohort's mean age at death.

    Not satisfiable by construction: bugs in dt scaling, the hazard
    code, or clipping fail it (amendment A1)."""
    from earth1.generational import _gompertz_a, GOMPERTZ_B, _AGE_MIN

    a = _gompertz_a(life_expectancy)
    dt_years = dt_days / 365.0
    age = np.full(n, _AGE_MIN)
    alive = np.ones(n, dtype=bool)
    death_age = np.zeros(n)
    while alive.any() and age.max() < 130.0:
        age[alive] += dt_years
        hazard_yr = a * np.exp(GOMPERTZ_B * (age[alive] - _AGE_MIN))
        p_death = np.clip(hazard_yr * dt_years, 0.0, 1.0)
        dies = rng.random(alive.sum()) < p_death
        idx = np.flatnonzero(alive)[dies]
        death_age[idx] = age[idx]
        alive[idx] = False
    death_age[alive] = age[alive]
    return float(death_age.mean())


def g5_demography(
    pop: int = 50_000,
    seed: int = 42,
    years: float = 5.0,
    dt_days: float = 30.0,
    le_tolerance: float = 6.0,
    cohort_n: int = 4_000,
) -> DemographyLegResult:
    """The demography leg (amendment A1).

    LE tracking: per distinct census LE value, a cohort stepped through
    the tick's own hazard path must die at mean age within +/- 6y of LE.
    CDR: the standing population's annualized adult crude death rate
    must sit in the externally-anchored [6, 15]/1000 band (unamended)."""
    rng = np.random.default_rng(seed)

    # cohort LE tracking over every distinct census LE value
    les = sorted({round(float(c.get("le", 72.0)), 1) for c in GENESIS_COUNTRIES})
    per_country = []
    within = 0
    for le in les:
        mean_death = _simulate_cohort_le(le, rng, n=cohort_n, dt_days=dt_days)
        ok = abs(mean_death - le) <= le_tolerance
        within += int(ok)
        per_country.append({
            "census_le": le,
            "cohort_mean_age_at_death": round(mean_death, 1),
            "within_tolerance": ok,
        })
    le_tracking = within / len(les) if les else 0.0

    # standing-population CDR — external anchor, unamended
    civ = _make_mutable(genesis(pop, seed))
    total = 0
    n_steps = int(round(years * 365.0 / dt_days))
    for _ in range(n_steps):
        total += generational_tick(civ, rng, dt_days=dt_days)["deaths"]
    cdr = (total / pop) / years * 1000.0

    passes = le_tracking >= 0.90 and 6.0 <= cdr <= 15.0

    return DemographyLegResult(
        years=years, total_deaths=total,
        world_adult_cdr=round(cdr, 2),
        n_countries_scored=len(les),
        le_tracking=round(le_tracking, 4),
        passes=passes, per_country=per_country,
    )


# ── the gate ────────────────────────────────────────────────────────────

@dataclass
class G5Report:
    temporal: TemporalLegResult
    event: EventLegResult
    demography: DemographyLegResult
    all_pass: bool


def run_g5_gate(
    pop: int = 50_000,
    seed: int = 42,
    temporal_years: float = 7.0,
    demography_years: float = 5.0,
    dt_days: float = 30.0,
    progress: bool = False,
) -> G5Report:
    """Run all three pre-registered legs. The gate passes only if all do."""
    if progress:
        print("G5 leg 1/3: temporal (WVS W6->W7)...")
    temporal = g5_temporal(pop=pop, seed=seed, years=temporal_years,
                           dt_days=dt_days, progress=progress)
    if progress:
        print("G5 leg 2/3: event reaction (COVID rally)...")
    event = g5_event_reaction(pop=pop, seed=seed, dt_days=dt_days)
    if progress:
        print("G5 leg 3/3: demography...")
    demography = g5_demography(pop=pop, seed=seed, years=demography_years,
                               dt_days=dt_days)
    return G5Report(
        temporal=temporal, event=event, demography=demography,
        all_pass=temporal.passes and event.passes and demography.passes,
    )


def print_g5_report(report: G5Report) -> str:
    t, e, d = report.temporal, report.event, report.demography
    lines = [
        "G5 GATE — THE WORLD IS ALIVE", "=" * 52,
        f"1. TEMPORAL   {'PASS' if t.passes else 'FAIL'}",
        f"     engine MAE {t.mae_engine:.4f} vs no-change {t.mae_nochange:.4f}"
        f"  ({t.n_pairs} pairs)",
        f"     sign accuracy {t.sign_accuracy:.1%} on {t.n_sign_pairs} pairs"
        f"  (p={t.sign_p:.4f})",
        f"2. EVENT      {'PASS' if e.passes else 'FAIL'}   [{e.case_id}]",
        f"     simulated {e.simulated_mean_shift:+.4f} vs measured "
        f"{e.measured_mean_shift:+.4f}  (ratio {e.magnitude_ratio:.2f})",
        f"3. DEMOGRAPHY {'PASS' if d.passes else 'FAIL'}",
        f"     LE tracking {d.le_tracking:.1%} of {d.n_countries_scored} "
        f"countries; adult CDR {d.world_adult_cdr:.1f}/1000/yr",
        "-" * 52,
        f"GATE: {'ALL LEGS PASS — the world is alive' if report.all_pass else 'BLOCKED'}",
    ]
    return "\n".join(lines)
