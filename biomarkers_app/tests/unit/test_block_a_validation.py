"""Unit tests for Block A: validation and uncertainty; Block C: evaluable gate and primary targets."""

import pytest
import numpy as np
import pandas as pd

from app.pipeline.wrappers.model_training_wrapper import (
    _bootstrap_balanced_accuracy,
    _gate_column_for_target,
    _filter_by_evaluable_gate,
)
from app.pipeline.types import ModelResult, PRIMARY_TARGETS


class TestBootstrapBalancedAccuracy:
    """Tests for _bootstrap_balanced_accuracy."""

    def test_returns_three_floats(self):
        y_test = np.array([0, 1, 0, 1, 1, 0, 1, 0, 1, 0])
        y_pred = np.array([0, 1, 0, 0, 1, 0, 1, 1, 1, 0])
        mean, low, high = _bootstrap_balanced_accuracy(
            y_test, y_pred, n_bootstrap=50, random_state=42
        )
        assert isinstance(mean, float)
        assert isinstance(low, float)
        assert isinstance(high, float)

    def test_mean_in_valid_range(self):
        y_test = np.array([0, 1, 0, 1, 1, 0, 1, 0, 1, 0])
        y_pred = np.array([0, 1, 0, 0, 1, 0, 1, 1, 1, 0])
        mean, low, high = _bootstrap_balanced_accuracy(
            y_test, y_pred, n_bootstrap=100, random_state=42
        )
        assert 0 <= mean <= 1
        assert 0 <= low <= 1
        assert 0 <= high <= 1

    def test_ci_bounds(self):
        y_test = np.array([0, 1, 0, 1, 1, 0, 1, 0, 1, 0])
        y_pred = np.array([0, 1, 0, 0, 1, 0, 1, 1, 1, 0])
        mean, low, high = _bootstrap_balanced_accuracy(
            y_test, y_pred, n_bootstrap=100, random_state=42
        )
        assert low <= mean <= high
        assert low <= high

    def test_reproducibility_with_same_seed(self):
        y_test = np.array([0, 1, 0, 1, 1, 0, 1, 0, 1, 0])
        y_pred = np.array([0, 1, 0, 0, 1, 0, 1, 1, 1, 0])
        a = _bootstrap_balanced_accuracy(y_test, y_pred, n_bootstrap=30, random_state=99)
        b = _bootstrap_balanced_accuracy(y_test, y_pred, n_bootstrap=30, random_state=99)
        assert a == b

    def test_small_sample_returns_sensible(self):
        y_test = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
        mean, low, high = _bootstrap_balanced_accuracy(
            y_test, y_pred, n_bootstrap=50, random_state=42
        )
        assert mean == 1.0
        assert low <= mean <= high

    def test_too_short_returns_zeros_or_point_estimate(self):
        y_test = np.array([0, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 1])
        mean, low, high = _bootstrap_balanced_accuracy(
            y_test, y_pred, n_bootstrap=20, random_state=42
        )
        assert 0 <= mean <= 1
        assert low <= high


class TestModelResultMetricDisplay:
    """Tests for ModelResult.get_metric_display (Block A)."""

    def test_display_without_std_returns_three_decimal(self):
        r = ModelResult(
            target="t", phase="p", model_family="LR",
            accuracy=0.7, balanced_accuracy=0.65, auc=0.72, f1_score=0.68,
        )
        assert r.get_metric_display("balanced_accuracy") == "0.650"
        assert r.get_metric_display("auc") == "0.720"

    def test_display_with_std_includes_plus_minus(self):
        r = ModelResult(
            target="t", phase="p", model_family="LR",
            accuracy=0.7, balanced_accuracy=0.65, auc=0.72, f1_score=0.68,
            balanced_accuracy_std=0.04, auc_std=0.03, f1_score_std=0.05,
        )
        s = r.get_metric_display("balanced_accuracy")
        assert "±" in s
        assert "0.650" in s
        assert "0.040" in s

    def test_display_with_ci_includes_brackets(self):
        r = ModelResult(
            target="t", phase="p", model_family="LR",
            accuracy=0.7, balanced_accuracy=0.65, auc=0.72, f1_score=0.68,
            balanced_accuracy_ci_low=0.58, balanced_accuracy_ci_high=0.72,
        )
        s = r.get_metric_display("balanced_accuracy")
        assert "[" in s
        assert "]" in s
        assert "0.58" in s
        assert "0.72" in s


class TestBlockCEvaluableGate:
    """Block C1: evaluable gate filter."""

    def test_gate_column_for_target_response(self):
        assert _gate_column_for_target("D30_response_3class") == "D30_evaluable_gate"
        assert _gate_column_for_target("cart_response_90_days") == "D90_evaluable_gate"
        assert _gate_column_for_target("best_response") == "BEST_evaluable_gate"

    def test_gate_column_for_target_no_gate(self):
        assert _gate_column_for_target("crs_grade_ge2") is None
        assert _gate_column_for_target("relapse_or_progression") is None

    def test_filter_by_evaluable_gate_restricts_rows(self):
        df = pd.DataFrame({
            "x": [1, 2, 3],
            "D30_evaluable_gate": [1, 0, 1],
        })
        out = _filter_by_evaluable_gate(df, "D30_response_3class")
        assert len(out) == 2
        assert list(out["x"]) == [1, 3]

    def test_filter_by_evaluable_gate_no_gate_returns_unchanged(self):
        df = pd.DataFrame({"x": [1, 2, 3]})
        out = _filter_by_evaluable_gate(df, "crs_grade_ge2")
        assert len(out) == 3


class TestBlockCPrimaryTargets:
    """Block C2: primary targets constant."""

    def test_primary_targets_list(self):
        assert "D30_response_3class" in PRIMARY_TARGETS
        assert "crs_grade_ge2" in PRIMARY_TARGETS
        assert len(PRIMARY_TARGETS) >= 5
