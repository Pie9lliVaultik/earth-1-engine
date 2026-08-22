from __future__ import annotations
"""Prediction market validation — resolved outcomes vs engine predictions.

Tests the engine against questions where the real-world outcome is known.
For each resolved prediction, we compare:
  1. Engine's yes_pct (what the population "thinks")
  2. Market's final probability (what bettors thought)
  3. Actual outcome (what happened)

The force anatomy shows WHY the engine predicted what it predicted,
which forces drove it, and whether the decomposition makes sense.
"""
"""LEGACY_COMPARISON_ONLY — retired predictions harness over the retired
engine family. Not an official Earth-1 scoring path; importing requires
EARTH1_LEGACY_COMPARISON=1.
"""
import os as _os
if _os.environ.get("EARTH1_LEGACY_COMPARISON") != "1":
    raise ImportError("earth1.legacy_predictions is LEGACY_COMPARISON_ONLY; "
                      "set EARTH1_LEGACY_COMPARISON=1 to import it.")

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from earth1.types import Civilization, Question, Force, NUM_FORCES, FORCE_KEYS
from earth1.engine import run_question, run_segment
from earth1.questions import _w
from earth1.decompose import anatomize


@dataclass
class ResolvedPrediction:
    """A prediction with a known real-world outcome."""
    id: str
    text: str
    domain: str
    baseline: float
    weights: np.ndarray
    lens: str
    actual_outcome: float
    market_price: float
    market_source: str
    resolution_date: str
    context: str

    def to_question(self) -> Question:
        return Question(
            id=self.id, text=self.text, domain=self.domain,
            baseline=self.baseline, weights=self.weights, lens=self.lens,
        )


@dataclass
class PredictionResult:
    """Engine prediction vs market vs reality for one question."""
    id: str
    text: str
    engine_yes_pct: float
    market_price: float
    actual_outcome: float
    engine_error: float
    market_error: float
    engine_closer: bool
    force_anatomy: Dict[str, float]
    dominant_force: str
    conviction: float
    fragility: float
    camps: Dict
    context: str


@dataclass
class PredictionReport:
    """Full prediction market validation report."""
    timestamp: str
    population: int
    n_predictions: int
    engine_mae: float
    market_mae: float
    engine_brier: float
    market_brier: float
    engine_wins: int
    market_wins: int
    ties: int
    engine_directional_accuracy: float
    market_directional_accuracy: float
    results: List[PredictionResult]
    force_analysis: Dict[str, Dict]


# ---------------------------------------------------------------------------
# Resolved predictions — real events with known outcomes
#
# Sources: Polymarket, Metaculus, PredictIt (2023-2025)
# Each entry has the market's pre-resolution price and the actual outcome.
# ---------------------------------------------------------------------------

RESOLVED_PREDICTIONS: List[ResolvedPrediction] = [

    # === US Politics ===

    ResolvedPrediction(
        id="p_biden_2024",
        text="Will Biden win the 2024 US presidential election?",
        domain="belief_causal", baseline=-0.2,
        weights=_w(collective=2.4, economics=2.0, identity=-1.6, fear=-1.0, experience=0.8),
        lens="politics",
        actual_outcome=0.0,
        market_price=0.40,
        market_source="Polymarket",
        resolution_date="2024-11-05",
        context="Biden dropped out July 2024. Harris ran instead. Trump won.",
    ),
    ResolvedPrediction(
        id="p_us_recession_2024",
        text="Will the US enter a recession in 2024?",
        domain="belief_causal", baseline=0.3,
        weights=_w(economics=-2.8, fear=2.4, desire=-1.2, collective=0.8),
        lens="economy",
        actual_outcome=0.0,
        market_price=0.15,
        market_source="Metaculus",
        resolution_date="2024-12-31",
        context="US economy grew throughout 2024. No NBER recession declared.",
    ),
    ResolvedPrediction(
        id="p_fed_cut_2024",
        text="Will the Federal Reserve cut interest rates in 2024?",
        domain="belief_causal", baseline=0.4,
        weights=_w(economics=3.0, fear=-1.4, desire=1.6, collective=0.8),
        lens="economy",
        actual_outcome=1.0,
        market_price=0.85,
        market_source="Polymarket",
        resolution_date="2024-09-18",
        context="Fed cut rates 50bp in September 2024, first cut since 2020.",
    ),
    ResolvedPrediction(
        id="p_sp500_5000",
        text="Will the S&P 500 reach 5000 in 2024?",
        domain="belief_causal", baseline=0.2,
        weights=_w(economics=2.6, desire=2.0, fear=-1.8, temperament=1.2),
        lens="economy",
        actual_outcome=1.0,
        market_price=0.72,
        market_source="Metaculus",
        resolution_date="2024-02-09",
        context="S&P 500 crossed 5000 on Feb 9 2024, driven by AI rally.",
    ),

    # === Geopolitics ===

    ResolvedPrediction(
        id="p_ukraine_nato_2024",
        text="Will Ukraine join NATO by end of 2024?",
        domain="belief_causal", baseline=-0.8,
        weights=_w(collective=2.8, fear=2.2, identity=1.6, economics=-1.0, culture=0.8),
        lens="geopolitics",
        actual_outcome=0.0,
        market_price=0.03,
        market_source="Metaculus",
        resolution_date="2024-12-31",
        context="No NATO membership. Ongoing war. NATO signaled future membership but no timeline.",
    ),
    ResolvedPrediction(
        id="p_china_taiwan_2024",
        text="Will China invade Taiwan in 2024?",
        domain="belief_causal", baseline=-1.2,
        weights=_w(fear=3.2, collective=2.0, identity=1.8, economics=-2.4),
        lens="geopolitics",
        actual_outcome=0.0,
        market_price=0.03,
        market_source="Metaculus",
        resolution_date="2024-12-31",
        context="No invasion. Tensions continued. Military exercises but no kinetic action.",
    ),
    ResolvedPrediction(
        id="p_russia_nuclear_2024",
        text="Will Russia use a nuclear weapon in 2024?",
        domain="belief_causal", baseline=-1.5,
        weights=_w(fear=3.6, collective=1.4, identity=0.8, economics=-0.6),
        lens="security",
        actual_outcome=0.0,
        market_price=0.02,
        market_source="Metaculus",
        resolution_date="2024-12-31",
        context="No nuclear use. Conventional warfare continued in Ukraine.",
    ),

    # === Technology ===

    ResolvedPrediction(
        id="p_gpt5_2024",
        text="Will OpenAI release GPT-5 in 2024?",
        domain="belief_causal", baseline=0.1,
        weights=_w(desire=2.4, temperament=1.8, economics=1.2, fear=-0.8, identity=0.6),
        lens="technology",
        actual_outcome=0.0,
        market_price=0.35,
        market_source="Metaculus",
        resolution_date="2024-12-31",
        context="GPT-5 not released in 2024. GPT-4o and o1 released instead.",
    ),
    ResolvedPrediction(
        id="p_ai_job_loss",
        text="Will AI cause measurable job losses (>1% unemployment increase) by 2025?",
        domain="belief_causal", baseline=-0.4,
        weights=_w(fear=2.6, economics=-2.2, temperament=-1.0, desire=-0.8, collective=0.6),
        lens="technology",
        actual_outcome=0.0,
        market_price=0.08,
        market_source="Metaculus",
        resolution_date="2025-03-31",
        context="No measurable AI-driven unemployment spike by early 2025.",
    ),

    # === Social / Cultural ===

    ResolvedPrediction(
        id="p_japan_ssm",
        text="Will Japan legalize same-sex marriage by end of 2024?",
        domain="belief_causal", baseline=-0.6,
        weights=_w(identity=3.0, culture=-2.8, collective=-1.4, experience=-1.0),
        lens="culture",
        actual_outcome=0.0,
        market_price=0.08,
        market_source="Metaculus",
        resolution_date="2024-12-31",
        context="Multiple courts ruled ban unconstitutional but no legislation passed.",
    ),
    ResolvedPrediction(
        id="p_uk_rejoin_eu",
        text="Will the UK rejoin the EU by 2025?",
        domain="belief_causal", baseline=-1.0,
        weights=_w(identity=-2.6, collective=2.2, economics=1.8, culture=1.4),
        lens="geopolitics",
        actual_outcome=0.0,
        market_price=0.01,
        market_source="PredictIt",
        resolution_date="2025-01-01",
        context="No movement toward rejoining. Labour government focused on closer ties, not membership.",
    ),

    # === Economics ===

    ResolvedPrediction(
        id="p_us_inflation_3pct",
        text="Will US CPI inflation be above 3% at end of 2024?",
        domain="belief_causal", baseline=0.4,
        weights=_w(economics=3.0, fear=1.8, desire=-1.2, collective=0.6),
        lens="economy",
        actual_outcome=0.0,
        market_price=0.30,
        market_source="Polymarket",
        resolution_date="2024-12-31",
        context="CPI came in at 2.7% for December 2024. Below 3% threshold.",
    ),
    ResolvedPrediction(
        id="p_bitcoin_100k",
        text="Will Bitcoin reach $100,000 in 2024?",
        domain="belief_causal", baseline=-0.2,
        weights=_w(temperament=2.8, desire=2.4, fear=-1.6, economics=1.2, identity=0.8),
        lens="economy",
        actual_outcome=1.0,
        market_price=0.45,
        market_source="Polymarket",
        resolution_date="2024-12-05",
        context="Bitcoin crossed $100K on Dec 5 2024 after Trump election win and crypto-friendly cabinet picks.",
    ),

    # === Health / Science ===

    ResolvedPrediction(
        id="p_who_pandemic_2024",
        text="Will the WHO declare a new pandemic in 2024?",
        domain="belief_causal", baseline=-0.8,
        weights=_w(fear=3.0, collective=2.2, experience=1.4, economics=-1.0),
        lens="health",
        actual_outcome=0.0,
        market_price=0.05,
        market_source="Metaculus",
        resolution_date="2024-12-31",
        context="Mpox declared PHEIC (Aug 2024) but not a pandemic. No new pandemic declaration.",
    ),

    # === Climate / Environment ===

    ResolvedPrediction(
        id="p_hottest_year_2024",
        text="Will 2024 be the hottest year on record?",
        domain="belief_causal", baseline=0.6,
        weights=_w(identity=2.2, experience=-1.8, fear=1.4, economics=-0.8, culture=0.6),
        lens="policy",
        actual_outcome=1.0,
        market_price=0.88,
        market_source="Metaculus",
        resolution_date="2025-01-10",
        context="2024 confirmed as hottest year on record. First year above 1.5°C average.",
    ),

    # === Elections (non-US) ===

    ResolvedPrediction(
        id="p_modi_2024",
        text="Will Modi's BJP win the 2024 Indian general election?",
        domain="belief_causal", baseline=0.8,
        weights=_w(collective=2.6, identity=2.2, economics=1.4, culture=1.0, fear=-0.6),
        lens="politics",
        actual_outcome=1.0,
        market_price=0.92,
        market_source="Metaculus",
        resolution_date="2024-06-04",
        context="BJP won but lost majority. Formed coalition government. Modi continued as PM.",
    ),
    ResolvedPrediction(
        id="p_uk_labour_2024",
        text="Will Labour win the UK general election?",
        domain="belief_causal", baseline=0.8,
        weights=_w(collective=2.4, economics=2.0, identity=-1.2, fear=-0.8, desire=0.6),
        lens="politics",
        actual_outcome=1.0,
        market_price=0.95,
        market_source="Polymarket",
        resolution_date="2024-07-04",
        context="Labour won landslide. 412 seats. Starmer became PM.",
    ),

    # === Crypto / Markets ===

    ResolvedPrediction(
        id="p_eth_etf_2024",
        text="Will a spot Ethereum ETF be approved in the US in 2024?",
        domain="belief_causal", baseline=-0.1,
        weights=_w(economics=2.4, desire=2.0, temperament=1.6, collective=0.8, identity=0.4),
        lens="economy",
        actual_outcome=1.0,
        market_price=0.55,
        market_source="Polymarket",
        resolution_date="2024-05-23",
        context="SEC approved spot ETH ETFs in May 2024. Trading began July 2024.",
    ),
    ResolvedPrediction(
        id="p_tiktok_ban_2024",
        text="Will TikTok be banned in the US in 2024?",
        domain="belief_causal", baseline=0.1,
        weights=_w(fear=2.0, collective=2.4, identity=-1.8, culture=-1.2, temperament=-0.6),
        lens="technology",
        actual_outcome=0.0,
        market_price=0.20,
        market_source="Polymarket",
        resolution_date="2024-12-31",
        context="Ban legislation passed but enforcement delayed. TikTok still operating end of 2024.",
    ),

    # === US Politics (continued) ===

    ResolvedPrediction(
        id="p_trump_2024",
        text="Will Trump win the 2024 US presidential election?",
        domain="belief_causal", baseline=0.2,
        weights=_w(collective=-2.4, economics=2.2, identity=2.6, fear=1.4, desire=-0.8),
        lens="politics",
        actual_outcome=1.0,
        market_price=0.55,
        market_source="Polymarket",
        resolution_date="2024-11-05",
        context="Trump won the 2024 election with 312 electoral votes.",
    ),
]


def run_prediction_validation(
    civ: Civilization,
    predictions: Optional[List[ResolvedPrediction]] = None,
    epsilon: float = 0.18,
    layers: int = 8,
) -> PredictionReport:
    """Run all resolved predictions through the engine and compare."""
    if predictions is None:
        predictions = RESOLVED_PREDICTIONS

    t0 = time.time()
    results = []
    engine_errors = []
    market_errors = []
    engine_brier = []
    market_brier = []
    engine_wins = 0
    market_wins = 0
    ties = 0

    force_names = [f.name.lower() for f in Force]
    force_totals = {f: 0.0 for f in force_names}
    force_correct_totals = {f: 0.0 for f in force_names}
    force_wrong_totals = {f: 0.0 for f in force_names}
    n_correct = 0
    n_wrong = 0

    for pred in predictions:
        q = pred.to_question()
        r = run_question(q, civ, epsilon=epsilon, layers=layers)

        stances = r.settled_stances if r.settled_stances is not None else np.full(civ.n, r.yes_pct)
        anat_data = anatomize(civ, stances, q)
        force_anat = {force_names[i]: round(float(anat_data["force_anatomy"][i]), 4)
                      for i in range(NUM_FORCES)}
        dominant = anat_data["dominant"].name.lower()

        e_err = abs(r.yes_pct - pred.actual_outcome)
        m_err = abs(pred.market_price - pred.actual_outcome)
        engine_errors.append(e_err)
        market_errors.append(m_err)

        e_brier = (r.yes_pct - pred.actual_outcome) ** 2
        m_brier = (pred.market_price - pred.actual_outcome) ** 2
        engine_brier.append(e_brier)
        market_brier.append(m_brier)

        closer = e_err < m_err - 0.01
        market_closer = m_err < e_err - 0.01
        if closer:
            engine_wins += 1
        elif market_closer:
            market_wins += 1
        else:
            ties += 1

        engine_correct = (r.yes_pct >= 0.5) == (pred.actual_outcome >= 0.5)
        for i, fname in enumerate(force_names):
            val = float(anat_data["force_anatomy"][i])
            force_totals[fname] += val
            if engine_correct:
                force_correct_totals[fname] += val
            else:
                force_wrong_totals[fname] += val

        if engine_correct:
            n_correct += 1
        else:
            n_wrong += 1

        results.append(PredictionResult(
            id=pred.id,
            text=pred.text,
            engine_yes_pct=round(r.yes_pct, 4),
            market_price=pred.market_price,
            actual_outcome=pred.actual_outcome,
            engine_error=round(e_err, 4),
            market_error=round(m_err, 4),
            engine_closer=closer,
            force_anatomy=force_anat,
            dominant_force=dominant,
            conviction=round(anat_data["conviction"], 4),
            fragility=round(anat_data["fragility"], 4),
            camps={
                "yes": {"size": anat_data["camps"]["yes"].size,
                        "mean_stance": round(anat_data["camps"]["yes"].mean_stance, 4)},
                "no": {"size": anat_data["camps"]["no"].size,
                        "mean_stance": round(anat_data["camps"]["no"].mean_stance, 4)},
            },
            context=pred.context,
        ))

    force_analysis = {}
    for fname in force_names:
        n = len(predictions)
        force_analysis[fname] = {
            "mean_contribution": round(force_totals[fname] / max(n, 1), 4),
            "when_correct": round(force_correct_totals[fname] / max(n_correct, 1), 4),
            "when_wrong": round(force_wrong_totals[fname] / max(n_wrong, 1), 4),
        }

    market_correct = sum(
        1 for r, p in zip(results, predictions)
        if (r.market_price >= 0.5) == (p.actual_outcome >= 0.5)
    )

    return PredictionReport(
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        population=civ.n,
        n_predictions=len(predictions),
        engine_mae=round(float(np.mean(engine_errors)), 4),
        market_mae=round(float(np.mean(market_errors)), 4),
        engine_brier=round(float(np.mean(engine_brier)), 4),
        market_brier=round(float(np.mean(market_brier)), 4),
        engine_wins=engine_wins,
        market_wins=market_wins,
        ties=ties,
        engine_directional_accuracy=round(n_correct / max(len(predictions), 1), 4),
        market_directional_accuracy=round(market_correct / max(len(predictions), 1), 4),
        results=sorted(results, key=lambda x: -abs(x.engine_error - x.market_error)),
        force_analysis=force_analysis,
    )


def format_prediction_report(report: PredictionReport) -> str:
    """Format prediction report as human-readable text."""
    lines = [
        "Earth-1 Prediction Market Validation",
        "=" * 65,
        f"  Population: {report.population:,}",
        f"  Predictions: {report.n_predictions}  (resolved, known outcomes)",
        "",
        f"  ENGINE MAE:  {report.engine_mae:.4f}",
        f"  MARKET MAE:  {report.market_mae:.4f}",
        f"  ENGINE Brier: {report.engine_brier:.4f}",
        f"  MARKET Brier: {report.market_brier:.4f}",
        "",
        f"  Engine direction: {report.engine_directional_accuracy:.0%}  |  Market direction: {report.market_directional_accuracy:.0%}",
        f"  Engine closer: {report.engine_wins}  |  Market closer: {report.market_wins}  |  Ties: {report.ties}",
        "",
        f"  {'ID':<24s} {'Eng':>5s} {'Mkt':>5s} {'Real':>5s} {'E-err':>6s} {'M-err':>6s} {'Win':>5s} {'Dominant':<12s}",
        f"  {'-'*72}",
    ]

    for r in report.results:
        winner = "ENG" if r.engine_closer else ("MKT" if r.market_error < r.engine_error - 0.01 else "TIE")
        lines.append(
            f"  {r.id:<24s} {r.engine_yes_pct:5.2f} {r.market_price:5.2f} "
            f"{r.actual_outcome:5.1f} {r.engine_error:6.4f} {r.market_error:6.4f} "
            f"{winner:>5s} {r.dominant_force:<12s}"
        )

    lines.append("")
    lines.append("  Force Analysis (mean contribution when correct vs wrong):")
    lines.append(f"  {'Force':<14s} {'Overall':>8s} {'Correct':>8s} {'Wrong':>8s}")
    lines.append(f"  {'-'*40}")
    for fname, stats in sorted(report.force_analysis.items(),
                                key=lambda x: -x[1]["mean_contribution"]):
        lines.append(
            f"  {fname:<14s} {stats['mean_contribution']:8.4f} "
            f"{stats['when_correct']:8.4f} {stats['when_wrong']:8.4f}"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    from earth1.engine import build_civilization

    parser = argparse.ArgumentParser(description="Earth-1 Prediction Market Validation")
    parser.add_argument("--pop", type=int, default=100_000, help="Population size")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--detail", action="store_true", help="Show per-prediction force anatomy")
    args = parser.parse_args()

    print(f"Building civilization with {args.pop:,} agents...")
    civ = build_civilization(args.pop, seed=args.seed)
    print(f"Running {len(RESOLVED_PREDICTIONS)} predictions...\n")

    report = run_prediction_validation(civ)
    print(format_prediction_report(report))

    if args.detail:
        print("\n\nDetailed Force Anatomy per Prediction")
        print("=" * 65)
        for r in report.results:
            print(f"\n  {r.id}: {r.text}")
            print(f"  Engine: {r.engine_yes_pct:.2f}  Market: {r.market_price:.2f}  Actual: {r.actual_outcome:.0f}")
            print(f"  Conviction: {r.conviction:.3f}  Fragility: {r.fragility:.3f}")
            print(f"  Camps: YES={r.camps['yes']['size']} (mean {r.camps['yes']['mean_stance']:.3f})  "
                  f"NO={r.camps['no']['size']} (mean {r.camps['no']['mean_stance']:.3f})")
            print(f"  Context: {r.context}")
            top_forces = sorted(r.force_anatomy.items(), key=lambda x: -x[1])[:4]
            print(f"  Forces: {', '.join(f'{f}={v:.3f}' for f, v in top_forces)}")
