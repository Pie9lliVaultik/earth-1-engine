"""Tests for the differentiable forward pass and training loop."""
import sys
sys.path.insert(0, ".")

import numpy as np
import torch
import pytest

from earth1.torch_forward import (
    DifferentiableEngine, CivGraph, prepare_tensors, numpy_torch_compare,
)
from earth1.training import (
    train, train_weights, prepare_targets, TrainTarget,
    train_holdout_experiment,
)
from earth1.engine import build_civilization
from earth1.questions import question_by_id
from earth1.benchmark_questions import BENCHMARK_QUESTIONS

POP = 5_000
civ = build_civilization(POP, seed=42)
forces, means, alpha_raw, graph = prepare_tensors(civ)


class TestCivGraph:
    def test_graph_sizes(self):
        assert graph.n == POP
        assert graph.edge_src.shape == graph.edge_dst.shape
        assert len(graph.edge_src) > POP * 4

    def test_graph_tensors_are_long(self):
        assert graph.edge_src.dtype == torch.int64
        assert graph.edge_dst.dtype == torch.int64

    def test_degree(self):
        assert graph.degree.shape == (POP,)
        assert graph.degree.mean() > 4


class TestDifferentiableEngine:
    def test_forward_produces_yes_pct(self):
        model = DifferentiableEngine(init_baseline=0.35, init_weights=np.zeros(8))
        with torch.no_grad():
            result = model(forces, means, alpha_raw, graph)
        assert "yes_pct" in result
        assert 0 <= float(result["yes_pct"]) <= 1

    def test_forward_returns_s_final(self):
        q = question_by_id("ssm")
        model = DifferentiableEngine(init_baseline=q.baseline, init_weights=q.weights)
        with torch.no_grad():
            result = model(forces, means, alpha_raw, graph)
        assert result["s_final"].shape == (POP,)

    def test_forward_with_layers(self):
        q = question_by_id("ssm")
        model = DifferentiableEngine(init_baseline=q.baseline, init_weights=q.weights)
        with torch.no_grad():
            result = model(forces, means, alpha_raw, graph, return_layers=True)
        assert len(result["layer_snapshots"]) == 9

    def test_ssm_reasonable_output(self):
        q = question_by_id("ssm")
        model = DifferentiableEngine(init_baseline=q.baseline, init_weights=q.weights)
        with torch.no_grad():
            result = model(forces, means, alpha_raw, graph)
        yes = float(result["yes_pct"])
        assert 0.3 < yes < 0.8, f"SSM yes_pct {yes} out of expected range"

    def test_gradient_flows(self):
        """Core G2 gate test: gradients must flow from yes_pct back to all parameters."""
        q = question_by_id("ssm")
        model = DifferentiableEngine(init_baseline=q.baseline, init_weights=q.weights)
        result = model(forces, means, alpha_raw, graph)
        loss = (result["yes_pct"] - 0.55) ** 2
        loss.backward()

        assert model.baseline.grad is not None, "No gradient on baseline"
        assert model.weights.grad is not None, "No gradient on weights"
        assert model.log_sigma.grad is not None, "No gradient on log_sigma"
        assert model.alpha_bias.grad is not None, "No gradient on alpha_bias"

        assert not torch.all(model.weights.grad == 0), "All weight gradients are zero"

    def test_sigma_property(self):
        model = DifferentiableEngine(init_sigma=0.18)
        assert abs(model.sigma.detach().item() - 0.18) < 1e-5

    def test_forward_question(self):
        q = question_by_id("ssm")
        model = DifferentiableEngine(init_sigma=0.18)
        result = model.forward_question(
            forces, means, alpha_raw, graph,
            baseline=q.baseline, weights=q.weights,
        )
        assert 0 <= float(result["yes_pct"]) <= 1


class TestNumpyTorchCompare:
    def test_ssm_close(self):
        q = question_by_id("ssm")
        comp = numpy_torch_compare(civ, q)
        assert comp["difference"] < 0.05, (
            f"NumPy vs PyTorch too far apart: {comp['numpy_yes_pct']:.4f} vs {comp['torch_yes_pct']:.4f}"
        )

    def test_svb_close(self):
        q = question_by_id("svb")
        comp = numpy_torch_compare(civ, q)
        assert comp["difference"] < 0.05

    def test_immig_close(self):
        q = question_by_id("immig")
        comp = numpy_torch_compare(civ, q)
        assert comp["difference"] < 0.05


class TestTraining:
    def test_prepare_targets(self):
        targets = prepare_targets()
        assert len(targets) >= 15
        for t in targets:
            assert 0 <= t.target_yes_pct <= 1

    def test_train_reduces_loss(self):
        targets = prepare_targets()[:5]
        result = train(civ, targets=targets, epochs=30, lr=0.01)
        assert result.final_loss <= result.initial_loss * 1.5, "Loss should not increase dramatically"

    def test_train_weights_single_question(self):
        bq = BENCHMARK_QUESTIONS[0]
        target = TrainTarget(question=bq, target_yes_pct=bq.global_target)
        result, model = train_weights(civ, targets=[target], epochs=50, lr=0.01)
        assert result.final_mae < result.initial_mae + 0.1, "MAE should not increase dramatically"

    def test_train_returns_learned_params(self):
        targets = prepare_targets()[:3]
        result = train(civ, targets=targets, epochs=20, lr=0.01)
        assert "sigma" in result.learned_params
        assert "alpha_bias" in result.learned_params
        assert result.learned_params["sigma"] > 0


class TestHoldoutExperiment:
    def test_holdout_runs(self):
        result = train_holdout_experiment(civ, epochs=30, lr=0.01, verbose=False)
        assert "gate_passed" in result
        assert "pre_test_mae" in result
        assert "post_test_mae" in result
        assert result["n_train"] + result["n_test"] == len(prepare_targets())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
