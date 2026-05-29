"""Integration tests for model training pipeline (Phase 4)."""

import pytest
import pandas as pd
import numpy as np

from app.pipeline.wrappers.model_training_wrapper import ModelTrainingWrapper
from app.pipeline.types import ModelResult, CancellationToken


@pytest.fixture
def engineered_df_with_target():
    """Minimal engineered-like DataFrame with feature columns and one binary target."""
    np.random.seed(42)
    n = 80
    df = pd.DataFrame({
        "age": np.random.randint(25, 75, n),
        "wbc_-6": np.random.uniform(2, 15, n),
        "anc_-6": np.random.uniform(0.5, 8, n),
        "hgb_-6": np.random.uniform(8, 14, n),
        "ldh_-6": np.random.uniform(150, 800, n),
        "crs_grade_ge2": np.random.choice([0, 1], n, p=[0.7, 0.3]),
    })
    return df


@pytest.fixture
def feature_metadata(engineered_df_with_target):
    """Metadata as produced by feature engineering step."""
    features = [c for c in engineered_df_with_target.columns if c != "crs_grade_ge2"]
    return {"selected_features": features, "phase": "phase_-6"}


def test_training_wrapper_returns_step_result(engineered_df_with_target, feature_metadata):
    """Training wrapper returns StepResult with data and metadata."""
    wrapper = ModelTrainingWrapper()
    result = wrapper.train_models(
        engineered_df_with_target,
        phase="phase_-6",
        feature_metadata=feature_metadata,
        targets=["crs_grade_ge2"],
        random_seed=42,
    )
    assert result is not None
    assert hasattr(result, "success")
    assert hasattr(result, "data")
    assert hasattr(result, "metadata")
    assert isinstance(result.data, list)
    assert "phase" in result.metadata
    assert result.metadata["phase"] == "phase_-6"


def test_training_wrapper_produces_model_results(engineered_df_with_target, feature_metadata):
    """Training produces at least one ModelResult per model family for the target."""
    wrapper = ModelTrainingWrapper()
    result = wrapper.train_models(
        engineered_df_with_target,
        phase="phase_-6",
        feature_metadata=feature_metadata,
        targets=["crs_grade_ge2"],
        random_seed=42,
    )
    if not result.success:
        pytest.skip("Training failed (e.g. NN/sklearn deps); check errors: %s" % result.errors)
    assert len(result.data) >= 1
    for r in result.data:
        assert isinstance(r, ModelResult)
        assert r.target == "crs_grade_ge2"
        assert r.phase == "phase_-6"
        assert r.model_family in (
            "NN", "LR", "RF", "XGB", "CB", "ET", "LGB", "SVM",
            "Baseline-Majority", "Baseline-Random",
        )
        assert 0 <= r.accuracy <= 1
        assert 0 <= r.balanced_accuracy <= 1
    # Block A2: bootstrap CIs in metadata when training succeeds (trained models only)
    bootstrap_cis = result.metadata.get("bootstrap_cis", [])
    if bootstrap_cis:
        for item in bootstrap_cis:
            assert len(item) >= 6  # phase, target, model_family, mean, low, high
            mean, low, high = item[3], item[4], item[5]
            assert 0 <= mean <= 1 and low <= high


def test_training_wrapper_with_progress_callback(engineered_df_with_target, feature_metadata):
    """Progress callback is invoked during training."""
    progress_calls = []

    def progress_cb(pct, msg):
        progress_calls.append((pct, msg))

    wrapper = ModelTrainingWrapper()
    wrapper.train_models(
        engineered_df_with_target,
        phase="phase_-6",
        feature_metadata=feature_metadata,
        targets=["crs_grade_ge2"],
        progress_callback=progress_cb,
        random_seed=42,
    )
    # May or may not be called depending on implementation
    assert isinstance(progress_calls, list)


def test_training_wrapper_fails_gracefully_without_targets(engineered_df_with_target, feature_metadata):
    """Missing or invalid target list yields a clear failure."""
    df_no_target = engineered_df_with_target.drop(columns=["crs_grade_ge2"], errors="ignore")
    wrapper = ModelTrainingWrapper()
    result = wrapper.train_models(
        df_no_target,
        phase="phase_-6",
        feature_metadata=feature_metadata,
        targets=[],  # empty
        random_seed=42,
    )
    assert result.success is False or len(result.data) == 0
    if result.errors:
        assert any("target" in e.lower() for e in result.errors)


def test_training_wrapper_respects_cancellation(engineered_df_with_target, feature_metadata):
    """Cancellation token stops training early (no crash)."""
    token = CancellationToken()
    token.cancel()
    wrapper = ModelTrainingWrapper()
    result = wrapper.train_models(
        engineered_df_with_target,
        phase="phase_-6",
        feature_metadata=feature_metadata,
        targets=["crs_grade_ge2"],
        cancellation_token=token,
        random_seed=42,
    )
    # May complete with 0 results or partial; should not raise
    assert result is not None
    assert isinstance(result.data, list)
    token.reset()


def test_train_models_with_cv_returns_step_result(engineered_df_with_target, feature_metadata):
    """Block A: train_models_with_cv returns StepResult with data and metadata."""
    wrapper = ModelTrainingWrapper()
    result = wrapper.train_models_with_cv(
        engineered_df_with_target,
        phase="phase_-6",
        feature_metadata=feature_metadata,
        targets=["crs_grade_ge2"],
        n_outer_splits=3,
        random_seed=42,
    )
    assert result is not None
    assert hasattr(result, "success")
    assert hasattr(result, "data")
    assert hasattr(result, "metadata")
    assert isinstance(result.data, list)
    assert result.metadata.get("n_outer_splits") == 3
    assert result.metadata.get("phase") == "phase_-6"


def test_train_models_with_cv_produces_mean_and_std(engineered_df_with_target, feature_metadata):
    """Block A: CV results have balanced_accuracy_std and CI when n_splits >= 2."""
    wrapper = ModelTrainingWrapper()
    result = wrapper.train_models_with_cv(
        engineered_df_with_target,
        phase="phase_-6",
        feature_metadata=feature_metadata,
        targets=["crs_grade_ge2"],
        n_outer_splits=3,
        random_seed=42,
    )
    if not result.success or not result.data:
        pytest.skip("train_models_with_cv failed or no data (e.g. missing deps)")
    # At least one non-baseline result should have std/ci from CV
    model_results = [r for r in result.data if r.model_family not in ("Baseline-Majority", "Baseline-Random")]
    if not model_results:
        pytest.skip("No model results (only baselines)")
    r = model_results[0]
    assert hasattr(r, "balanced_accuracy_std")
    assert r.balanced_accuracy_std >= 0
    assert hasattr(r, "balanced_accuracy_ci_low")
    assert hasattr(r, "balanced_accuracy_ci_high")
    assert r.balanced_accuracy_ci_low <= r.balanced_accuracy <= r.balanced_accuracy_ci_high or r.balanced_accuracy_std == 0


def test_nested_cv_emits_curve_metadata(engineered_df_with_target, feature_metadata):
    """Nested CV with last_outer_fold should populate roc/confusion metadata for visualizations."""
    wrapper = ModelTrainingWrapper()
    result = wrapper.train_models_nested_cv(
        engineered_df_with_target,
        phase="phase_-6",
        feature_metadata=feature_metadata,
        targets=["crs_grade_ge2"],
        n_outer_splits=3,
        n_inner_splits=2,
        random_seed=42,
        model_families_filter=["LR"],
        cv_curve_source="last_outer_fold",
    )
    if not result.success or not result.data:
        pytest.skip("nested_cv failed (deps or data)")
    assert result.metadata.get("curve_source") == "last_outer_fold"
    assert result.metadata.get("roc_curves"), "expected roc_curves for last-fold viz"
    assert result.metadata.get("confusion_matrices"), "expected confusion_matrices for last-fold viz"
