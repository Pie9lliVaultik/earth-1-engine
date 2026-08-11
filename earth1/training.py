"""Training loop — learn force weights from survey targets by gradient descent.

Bible §18.3 gate: "Gradient flows end-to-end; a held-out survey batch improves."

Loss = sum of (predicted_yes_pct - target_yes_pct)^2 over survey targets.
Optimizer: Adam on {baseline, weights, log_sigma, alpha_bias}.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn

from earth1.types import Civilization, Question, NUM_FORCES
from earth1.torch_forward import DifferentiableEngine, CivGraph, prepare_tensors
from earth1.benchmark import BENCHMARK_QUESTIONS, BenchmarkQuestion


@dataclass
class TrainTarget:
    """A single training target: question + expected yes_pct."""
    question: BenchmarkQuestion
    target_yes_pct: float
    country_idx: Optional[int] = None


@dataclass
class TrainResult:
    """Result of a training run."""
    epochs: int
    initial_loss: float
    final_loss: float
    initial_mae: float
    final_mae: float
    loss_history: List[float]
    mae_history: List[float]
    duration_s: float
    learned_params: Dict[str, float]


def prepare_targets(
    questions: Optional[List[BenchmarkQuestion]] = None,
    use_global: bool = True,
) -> List[TrainTarget]:
    """Convert benchmark questions into training targets."""
    if questions is None:
        questions = BENCHMARK_QUESTIONS

    targets = []
    for bq in questions:
        if bq.domain != "belief_causal":
            continue
        if use_global and bq.global_target is not None:
            targets.append(TrainTarget(question=bq, target_yes_pct=bq.global_target))

    return targets


def train(
    civ: Civilization,
    targets: Optional[List[TrainTarget]] = None,
    epochs: int = 100,
    lr: float = 0.01,
    init_sigma: float = 0.18,
    n_layers: int = 8,
    patience: int = 15,
    verbose: bool = False,
) -> TrainResult:
    """Train the differentiable engine against survey targets.

    Learns shared sigma and alpha_bias across all questions.
    Each question's baseline+weights are fixed (from LLM/calibration);
    the training tunes the diffusion dynamics (sigma, alpha_bias).
    """
    if targets is None:
        targets = prepare_targets()

    forces, means, alpha_raw, graph = prepare_tensors(civ)

    model = DifferentiableEngine(
        init_sigma=init_sigma,
        n_layers=n_layers,
    )

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    loss_history = []
    mae_history = []
    best_loss = float("inf")
    best_epoch = 0
    t0 = time.time()

    for epoch in range(epochs):
        optimizer.zero_grad()
        total_loss = torch.tensor(0.0)
        errors = []

        for target in targets:
            bq = target.question
            result = model.forward_question(
                forces, means, alpha_raw, graph,
                baseline=bq.baseline,
                weights=bq.weights,
            )
            predicted = result["yes_pct"]
            target_val = torch.tensor(target.target_yes_pct)
            loss = (predicted - target_val) ** 2
            total_loss = total_loss + loss
            errors.append(abs(predicted.detach().item() - target.target_yes_pct))

        total_loss = total_loss / len(targets)
        mae = float(np.mean(errors))

        total_loss.backward()
        optimizer.step()

        loss_val = float(total_loss)
        loss_history.append(loss_val)
        mae_history.append(mae)

        if loss_val < best_loss:
            best_loss = loss_val
            best_epoch = epoch

        if verbose and epoch % 10 == 0:
            sigma = float(model.sigma)
            alpha_b = float(model.alpha_bias)
            print(f"  epoch {epoch:4d}  loss={loss_val:.6f}  mae={mae:.4f}  sigma={sigma:.4f}  alpha_bias={alpha_b:.4f}")

        if epoch - best_epoch > patience:
            if verbose:
                print(f"  Early stop at epoch {epoch} (best was {best_epoch})")
            break

    dt = time.time() - t0

    return TrainResult(
        epochs=epoch + 1,
        initial_loss=loss_history[0],
        final_loss=loss_history[-1],
        initial_mae=mae_history[0],
        final_mae=mae_history[-1],
        loss_history=loss_history,
        mae_history=mae_history,
        duration_s=round(dt, 2),
        learned_params={
            "sigma": round(float(model.sigma), 6),
            "alpha_bias": round(float(model.alpha_bias), 6),
            "log_sigma": round(float(model.log_sigma), 6),
        },
    )


def train_weights(
    civ: Civilization,
    targets: Optional[List[TrainTarget]] = None,
    epochs: int = 200,
    lr: float = 0.005,
    init_sigma: float = 0.18,
    n_layers: int = 8,
    patience: int = 25,
    verbose: bool = False,
) -> Tuple[TrainResult, DifferentiableEngine]:
    """Train a single-question model where baseline + weights are also learned.

    This is the full trainable model: all parameters optimized jointly.
    Uses the first target's weights as initialization.
    """
    if targets is None:
        targets = prepare_targets()

    if not targets:
        raise ValueError("No training targets provided")

    forces, means, alpha_raw, graph = prepare_tensors(civ)

    bq0 = targets[0].question
    model = DifferentiableEngine(
        init_baseline=bq0.baseline,
        init_weights=bq0.weights,
        init_sigma=init_sigma,
        n_layers=n_layers,
    )

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    loss_history = []
    mae_history = []
    best_loss = float("inf")
    best_epoch = 0
    t0 = time.time()

    for epoch in range(epochs):
        optimizer.zero_grad()

        result = model(forces, means, alpha_raw, graph)
        predicted = result["yes_pct"]
        target_val = torch.tensor(targets[0].target_yes_pct)

        loss = (predicted - target_val) ** 2
        mae = abs(float(predicted) - targets[0].target_yes_pct)

        loss.backward()
        optimizer.step()

        loss_val = float(loss)
        loss_history.append(loss_val)
        mae_history.append(mae)

        if loss_val < best_loss:
            best_loss = loss_val
            best_epoch = epoch

        if verbose and epoch % 20 == 0:
            print(f"  epoch {epoch:4d}  loss={loss_val:.6f}  mae={mae:.4f}  "
                  f"baseline={float(model.baseline):.3f}  sigma={float(model.sigma):.4f}")

        if epoch - best_epoch > patience:
            if verbose:
                print(f"  Early stop at epoch {epoch} (best was {best_epoch})")
            break

    dt = time.time() - t0

    learned = {
        "baseline": round(float(model.baseline), 4),
        "sigma": round(float(model.sigma), 6),
        "alpha_bias": round(float(model.alpha_bias), 6),
    }
    for i, name in enumerate(["fear", "desire", "economics", "collective",
                               "identity", "culture", "experience", "temperament"]):
        learned[f"w_{name}"] = round(float(model.weights[i]), 4)

    return TrainResult(
        epochs=epoch + 1,
        initial_loss=loss_history[0],
        final_loss=loss_history[-1],
        initial_mae=mae_history[0],
        final_mae=mae_history[-1],
        loss_history=loss_history,
        mae_history=mae_history,
        duration_s=round(dt, 2),
        learned_params=learned,
    ), model


def train_holdout_experiment(
    civ: Civilization,
    train_frac: float = 0.7,
    epochs: int = 150,
    lr: float = 0.01,
    verbose: bool = True,
) -> dict:
    """The bible's G2 gate test: train on a subset, measure improvement on held-out.

    Splits benchmark questions into train/test, trains shared dynamics (sigma,
    alpha_bias) on the training set, measures MAE on the held-out set.
    """
    all_targets = prepare_targets()
    np.random.seed(42)
    indices = np.random.permutation(len(all_targets))
    split = int(len(indices) * train_frac)
    train_idx = indices[:split]
    test_idx = indices[split:]

    train_targets = [all_targets[i] for i in train_idx]
    test_targets = [all_targets[i] for i in test_idx]

    if verbose:
        print(f"Train: {len(train_targets)} questions, Test: {len(test_targets)} questions")

    forces, means, alpha_raw, graph = prepare_tensors(civ)

    def evaluate(model, targets):
        errors = []
        with torch.no_grad():
            for t in targets:
                r = model.forward_question(
                    forces, means, alpha_raw, graph,
                    baseline=t.question.baseline, weights=t.question.weights,
                )
                errors.append(abs(float(r["yes_pct"]) - t.target_yes_pct))
        return float(np.mean(errors))

    model = DifferentiableEngine(init_sigma=0.18, n_layers=8)

    pre_train_mae = evaluate(model, train_targets)
    pre_test_mae = evaluate(model, test_targets)

    if verbose:
        print(f"Before training — Train MAE: {pre_train_mae:.4f}, Test MAE: {pre_test_mae:.4f}")

    result = train(civ, targets=train_targets, epochs=epochs, lr=lr, verbose=verbose)

    model_trained = DifferentiableEngine(init_sigma=0.18, n_layers=8)
    model_trained.log_sigma.data = torch.tensor(result.learned_params["log_sigma"])
    model_trained.alpha_bias.data = torch.tensor(result.learned_params["alpha_bias"])

    post_train_mae = evaluate(model_trained, train_targets)
    post_test_mae = evaluate(model_trained, test_targets)

    if verbose:
        print(f"After training  — Train MAE: {post_train_mae:.4f}, Test MAE: {post_test_mae:.4f}")
        print(f"Train improvement: {pre_train_mae - post_train_mae:+.4f}")
        print(f"Test improvement:  {pre_test_mae - post_test_mae:+.4f}")

    gate_passed = post_test_mae < pre_test_mae

    return {
        "gate_passed": gate_passed,
        "pre_train_mae": round(pre_train_mae, 4),
        "pre_test_mae": round(pre_test_mae, 4),
        "post_train_mae": round(post_train_mae, 4),
        "post_test_mae": round(post_test_mae, 4),
        "train_improvement": round(pre_train_mae - post_train_mae, 4),
        "test_improvement": round(pre_test_mae - post_test_mae, 4),
        "n_train": len(train_targets),
        "n_test": len(test_targets),
        "learned_params": result.learned_params,
        "epochs": result.epochs,
        "duration_s": result.duration_s,
    }
