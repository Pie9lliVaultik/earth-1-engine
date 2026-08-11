"""Layer-scrub analysis — proves flat -> sharp -> correct at each diffusion layer.

Bible G1 gate: "One well-calibrated country (~20k agents), one question the
one-layer engine flattens to ~50%.  Run the diffusion, plot the distribution
at each layer, and show flat -> sharp -> correct, with a conviction core
separating from a conformity crust."
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

from earth1.types import Civilization, Question, Force, NUM_FORCES
from earth1.forces import project_all
from earth1.diffusion import diffuse
from earth1.decompose import histogram


def layer_scrub(
    civ: Civilization,
    q: Question,
    epsilon: float = 0.18,
    layers: int = 8,
    country_idx: Optional[int] = None,
    conviction_threshold: float = 0.5,
    n_bins: int = 40,
) -> dict:
    """Full layer-scrub analysis with core/crust separation.

    Returns per-layer stats showing the conviction core (high-alpha agents)
    sharpening into a settled opinion while the conformity crust (low-alpha)
    drifts toward the social mean.
    """
    if country_idx is not None:
        mask = civ.country == country_idx
    else:
        mask = np.ones(civ.n, dtype=bool)

    s0 = project_all(civ, q)
    snaps = diffuse(s0, civ.alpha, civ.adj, epsilon, layers)

    alpha = civ.alpha[mask]
    core_mask_local = alpha >= conviction_threshold
    crust_mask_local = ~core_mask_local
    n_core = int(core_mask_local.sum())
    n_crust = int(crust_mask_local.sum())
    n_total = int(mask.sum())

    layer_data = []
    for i, s_full in enumerate(snaps):
        s = s_full[mask]
        s_core = s[core_mask_local] if n_core > 0 else np.array([0.5])
        s_crust = s[crust_mask_local] if n_crust > 0 else np.array([0.5])

        hist_all = np.histogram(s, bins=n_bins, range=(0, 1))[0]
        hist_core = np.histogram(s_core, bins=n_bins, range=(0, 1))[0]
        hist_crust = np.histogram(s_crust, bins=n_bins, range=(0, 1))[0]

        yes_pct_all = float(s.mean())
        yes_pct_core = float(s_core.mean())
        yes_pct_crust = float(s_crust.mean())

        std_all = float(s.std())
        std_core = float(s_core.std())
        std_crust = float(s_crust.std())

        bimodality = _bimodality_coefficient(s)

        polarization = float(np.mean(np.abs(s - 0.5)))

        core_crust_gap = abs(yes_pct_core - yes_pct_crust)

        layer_data.append({
            "layer": i,
            "all": {
                "yes_pct": round(yes_pct_all, 4),
                "std": round(std_all, 4),
                "bimodality": round(bimodality, 4),
                "polarization": round(polarization, 4),
                "histogram": hist_all.tolist(),
            },
            "core": {
                "n": n_core,
                "yes_pct": round(yes_pct_core, 4),
                "std": round(std_core, 4),
                "histogram": hist_core.tolist(),
            },
            "crust": {
                "n": n_crust,
                "yes_pct": round(yes_pct_crust, 4),
                "std": round(std_crust, 4),
                "histogram": hist_crust.tolist(),
            },
            "core_crust_gap": round(core_crust_gap, 4),
        })

    sharpening = _measure_sharpening(layer_data)

    return {
        "question_id": q.id,
        "question_text": q.text,
        "population": n_total,
        "n_core": n_core,
        "n_crust": n_crust,
        "conviction_threshold": conviction_threshold,
        "epsilon": epsilon,
        "n_layers": layers,
        "n_bins": n_bins,
        "layers": layer_data,
        "sharpening": sharpening,
    }


def _bimodality_coefficient(s: np.ndarray) -> float:
    """Sarle's bimodality coefficient. >0.555 suggests bimodal."""
    n = len(s)
    if n < 3:
        return 0.0
    m = s.mean()
    m2 = np.mean((s - m) ** 2)
    m3 = np.mean((s - m) ** 3)
    m4 = np.mean((s - m) ** 4)
    if m2 < 1e-12:
        return 0.0
    skew = m3 / (m2 ** 1.5)
    kurt = m4 / (m2 ** 2) - 3
    bc = (skew ** 2 + 1) / (kurt + 3 * (n - 1) ** 2 / ((n - 2) * (n - 3)))
    return float(np.clip(bc, 0, 1))


def _measure_sharpening(layer_data: list) -> dict:
    """Quantify the flat -> sharp -> correct trajectory."""
    if len(layer_data) < 2:
        return {"verdict": "insufficient_layers"}

    first = layer_data[0]
    last = layer_data[-1]

    std_reduction = 1.0 - (last["all"]["std"] / max(first["all"]["std"], 1e-6))
    polarization_gain = last["all"]["polarization"] - first["all"]["polarization"]
    final_gap = last["core_crust_gap"]
    initial_gap = first["core_crust_gap"]
    gap_growth = final_gap - initial_gap

    initial_flat = first["all"]["std"] > 0.15
    final_sharp = last["all"]["std"] < first["all"]["std"]
    core_separated = final_gap > 0.03

    if initial_flat and final_sharp and core_separated:
        verdict = "flat_to_sharp_confirmed"
    elif final_sharp and not core_separated:
        verdict = "sharpened_no_separation"
    elif not final_sharp:
        verdict = "no_sharpening"
    else:
        verdict = "partial"

    return {
        "verdict": verdict,
        "std_reduction_pct": round(std_reduction * 100, 1),
        "polarization_gain": round(polarization_gain, 4),
        "initial_core_crust_gap": round(initial_gap, 4),
        "final_core_crust_gap": round(final_gap, 4),
        "gap_growth": round(gap_growth, 4),
    }
