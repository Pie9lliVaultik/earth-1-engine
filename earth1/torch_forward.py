"""Differentiable forward pass — the trainable civilization model.

Bible §18.3: "Soften the hard mask into a smooth kernel and implement the
forward pass in a differentiable graph framework.  At that point it is not
'SQL that resembles a model'; it is a graph neural network whose nodes are
calibrated people, trained by gradient descent."

Architecture:
  1. Projection:  s0 = sigmoid(baseline + (forces - means) @ weights)
  2. Diffusion:   K layers of soft-attention H-K on the social graph
     - attention: w_ij = exp(-|s_i - s_j|^2 / 2*sigma^2)  (smooth kernel)
     - update:    s = alpha * s0 + (1 - alpha) * weighted_neighbor_mean
  3. Readout:     yes_pct = mean(s_final)

All parameters (baseline, weights, sigma, alpha_bias) are nn.Parameters.
Gradients flow from yes_pct back through diffusion and projection to weights.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from scipy import sparse


class CivGraph:
    """Pre-processed social graph for the differentiable forward pass.

    Converts scipy sparse CSR to torch sparse COO for edge-level ops,
    plus dense edge index arrays for the diffusion kernel.
    """
    __slots__ = ("n", "edge_src", "edge_dst", "degree")

    def __init__(self, adj: sparse.csr_matrix):
        self.n = adj.shape[0]
        coo = adj.tocoo()
        self.edge_src = torch.from_numpy(coo.row.astype(np.int64))
        self.edge_dst = torch.from_numpy(coo.col.astype(np.int64))
        deg = np.asarray(adj.sum(axis=1)).ravel()
        self.degree = torch.from_numpy(deg).float()


class DifferentiableEngine(nn.Module):
    """The trainable civilization model.

    Parameters learned by gradient descent:
      - baseline:   (1,) logit-space prior
      - weights:    (8,) per-force signed weights
      - log_sigma:  (1,) log of the attention kernel width (replaces hard epsilon)
      - alpha_bias: (1,) bias added to per-agent conviction before sigmoid

    Fixed inputs (from the population):
      - forces:     (N, 8) agent force matrix
      - means:      (8,) population means
      - alpha_raw:  (N,) raw conviction values
      - graph:      CivGraph with edge indices
    """

    def __init__(
        self,
        init_baseline: float = 0.0,
        init_weights: Optional[np.ndarray] = None,
        init_sigma: float = 0.18,
        n_forces: int = 8,
        n_layers: int = 8,
    ):
        super().__init__()
        self.n_layers = n_layers

        self.baseline = nn.Parameter(torch.tensor(init_baseline, dtype=torch.float32))

        if init_weights is not None:
            self.weights = nn.Parameter(torch.from_numpy(init_weights).float())
        else:
            self.weights = nn.Parameter(torch.zeros(n_forces))

        self.log_sigma = nn.Parameter(torch.tensor(np.log(init_sigma), dtype=torch.float32))

        self.alpha_bias = nn.Parameter(torch.tensor(0.0, dtype=torch.float32))

    @property
    def sigma(self) -> torch.Tensor:
        return torch.exp(self.log_sigma)

    def forward(
        self,
        forces: torch.Tensor,
        means: torch.Tensor,
        alpha_raw: torch.Tensor,
        graph: CivGraph,
        return_layers: bool = False,
    ) -> dict:
        """Full forward pass: projection → diffusion → readout.

        Args:
            forces:     (N, 8) float tensor
            means:      (8,) float tensor
            alpha_raw:  (N,) float tensor, raw conviction [0,1]
            graph:      CivGraph with edge indices
            return_layers: if True, return per-layer snapshots

        Returns:
            dict with yes_pct, s_final, and optionally layer_snapshots
        """
        alpha = torch.sigmoid(alpha_raw + self.alpha_bias)

        centered = forces - means.unsqueeze(0)
        z = self.baseline + centered @ self.weights
        s0 = torch.sigmoid(z)

        s = s0
        sigma = self.sigma
        sigma_sq_2 = 2.0 * sigma * sigma

        snapshots = [s] if return_layers else None

        src = graph.edge_src
        dst = graph.edge_dst

        for _ in range(self.n_layers):
            s_src = s[src]
            s_dst = s[dst]

            diff_sq = (s_src - s_dst) ** 2
            attn = torch.exp(-diff_sq / sigma_sq_2)

            weighted_vals = s_dst * attn

            sum_weighted = torch.zeros(graph.n, dtype=s.dtype)
            sum_weighted.scatter_add_(0, src, weighted_vals)

            sum_attn = torch.zeros(graph.n, dtype=s.dtype)
            sum_attn.scatter_add_(0, src, attn)

            safe_sum_attn = torch.clamp(sum_attn, min=1e-8)
            social = sum_weighted / safe_sum_attn

            has_neighbors = sum_attn > 1e-7
            social = torch.where(has_neighbors, social, s)

            s = alpha * s0 + (1.0 - alpha) * social

            if return_layers:
                snapshots.append(s)

        yes_pct = s.mean()

        result = {"yes_pct": yes_pct, "s_final": s}
        if return_layers:
            result["layer_snapshots"] = snapshots

        return result

    def forward_question(
        self,
        forces: torch.Tensor,
        means: torch.Tensor,
        alpha_raw: torch.Tensor,
        graph: CivGraph,
        baseline: float,
        weights: np.ndarray,
    ) -> dict:
        """Forward pass using external question weights (for multi-question training).

        Temporarily overrides self.baseline and self.weights with provided values,
        but still uses learned sigma and alpha_bias.
        """
        alpha = torch.sigmoid(alpha_raw + self.alpha_bias)
        sigma = self.sigma
        sigma_sq_2 = 2.0 * sigma * sigma

        w = torch.from_numpy(weights).float()
        centered = forces - means.unsqueeze(0)
        z = baseline + centered @ w
        s0 = torch.sigmoid(z)

        s = s0
        src = graph.edge_src
        dst = graph.edge_dst

        for _ in range(self.n_layers):
            s_src = s[src]
            s_dst = s[dst]
            diff_sq = (s_src - s_dst) ** 2
            attn = torch.exp(-diff_sq / sigma_sq_2)
            weighted_vals = s_dst * attn
            sum_weighted = torch.zeros(graph.n, dtype=s.dtype)
            sum_weighted.scatter_add_(0, src, weighted_vals)
            sum_attn = torch.zeros(graph.n, dtype=s.dtype)
            sum_attn.scatter_add_(0, src, attn)
            safe_sum_attn = torch.clamp(sum_attn, min=1e-8)
            social = sum_weighted / safe_sum_attn
            has_neighbors = sum_attn > 1e-7
            social = torch.where(has_neighbors, social, s)
            s = alpha * s0 + (1.0 - alpha) * social

        return {"yes_pct": s.mean(), "s_final": s}


def prepare_tensors(civ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, CivGraph]:
    """Convert a Civilization's NumPy arrays to PyTorch tensors + CivGraph."""
    forces = torch.from_numpy(civ.forces).float()
    means = torch.from_numpy(civ.means).float()
    alpha_raw = torch.from_numpy(civ.alpha).float()
    graph = CivGraph(civ.adj)
    return forces, means, alpha_raw, graph


def numpy_torch_compare(civ, q, epsilon=0.18, layers=8) -> dict:
    """Run both NumPy and PyTorch forward passes, compare results."""
    from earth1.forces import project_all
    from earth1.diffusion import diffuse

    s0_np = project_all(civ, q)
    snaps_np = diffuse(s0_np, civ.alpha, civ.adj, epsilon, layers)
    yes_np = float(snaps_np[-1].mean())

    forces, means, alpha_raw, graph = prepare_tensors(civ)
    model = DifferentiableEngine(
        init_baseline=q.baseline,
        init_weights=q.weights,
        init_sigma=epsilon,
        n_layers=layers,
    )

    with torch.no_grad():
        result = model(forces, means, alpha_raw, graph)
    yes_torch = float(result["yes_pct"])

    return {
        "numpy_yes_pct": yes_np,
        "torch_yes_pct": yes_torch,
        "difference": abs(yes_np - yes_torch),
    }
