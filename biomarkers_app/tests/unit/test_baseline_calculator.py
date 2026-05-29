"""Unit tests for Baseline Calculator"""

import pytest
import numpy as np
import pandas as pd
from app.pipeline.baseline_calculator import BaselineCalculator
from app.core.logger_manager import LoggerManager


@pytest.fixture
def logger():
    """Create logger instance"""
    return LoggerManager(log_dir="logs", level="INFO", save_to_file=False)


@pytest.fixture
def calculator(logger):
    """Create baseline calculator instance"""
    return BaselineCalculator(logger, n_splits=5, random_state=42)


def test_random_baseline_binary_balanced(calculator):
    """Test random baseline on balanced binary data"""
    # Create perfectly balanced binary data
    y = np.array([0] * 100 + [1] * 100)
    
    metrics = calculator.compute_random_baseline(y)
    
    # Random baseline should be ~0.50 for balanced binary (wider tolerance for random variance)
    assert 0.40 <= metrics['balanced_accuracy'] <= 0.60
    assert 0.40 <= metrics['accuracy'] <= 0.60
    assert 0.40 <= metrics['auc'] <= 0.60


def test_random_baseline_binary_imbalanced(calculator):
    """Test random baseline on imbalanced binary data"""
    # 70-30 split
    y = np.array([0] * 70 + [1] * 30)
    
    metrics = calculator.compute_random_baseline(y)
    
    # Random baseline should still be ~0.50 for balanced accuracy
    assert 0.45 <= metrics['balanced_accuracy'] <= 0.55
    # But accuracy should reflect the imbalance
    assert 0.45 <= metrics['accuracy'] <= 0.65


def test_random_baseline_multiclass(calculator):
    """Test random baseline on 3-class data"""
    # 3 classes with some imbalance
    y = np.array([0] * 50 + [1] * 30 + [2] * 20)
    
    metrics = calculator.compute_random_baseline(y)
    
    # Random baseline should be ~1/3 = 0.333 for 3 classes
    assert 0.28 <= metrics['balanced_accuracy'] <= 0.38
    assert 0.25 <= metrics['accuracy'] <= 0.45


def test_majority_baseline_binary_balanced(calculator):
    """Test majority baseline on balanced binary data"""
    # Perfectly balanced
    y = np.array([0] * 100 + [1] * 100)
    
    metrics = calculator.compute_majority_baseline(y)
    
    # Majority baseline should be exactly 0.50 for balanced accuracy
    # (100% on majority class, 0% on minority class)
    assert 0.48 <= metrics['balanced_accuracy'] <= 0.52
    # Accuracy should be ~50% for balanced data
    assert 0.48 <= metrics['accuracy'] <= 0.52
    # AUC should be 0.50 (no discrimination)
    assert 0.48 <= metrics['auc'] <= 0.52


def test_majority_baseline_binary_imbalanced(calculator):
    """Test majority baseline on imbalanced binary data"""
    # 70-30 split
    y = np.array([0] * 70 + [1] * 30)
    
    metrics = calculator.compute_majority_baseline(y)
    
    # Balanced accuracy should be ~0.50
    # (100% recall on majority = 1.0, 0% recall on minority = 0.0, avg = 0.50)
    assert 0.48 <= metrics['balanced_accuracy'] <= 0.52
    # But accuracy should be ~0.70 (predicts 70% correctly)
    assert 0.65 <= metrics['accuracy'] <= 0.75
    # AUC should be 0.50
    assert 0.48 <= metrics['auc'] <= 0.52


def test_majority_baseline_multiclass(calculator):
    """Test majority baseline on 3-class data"""
    # 3 classes: 50%, 30%, 20%
    y = np.array([0] * 50 + [1] * 30 + [2] * 20)
    
    metrics = calculator.compute_majority_baseline(y)
    
    # Balanced accuracy should be ~1/3 = 0.333
    # (100% on majority class, 0% on others, avg = 1/3)
    assert 0.28 <= metrics['balanced_accuracy'] <= 0.38
    # Accuracy should be ~0.50 (predicts 50% correctly)
    assert 0.45 <= metrics['accuracy'] <= 0.55
    # AUC should be 0.50
    assert 0.48 <= metrics['auc'] <= 0.52


def test_baseline_insufficient_samples(calculator):
    """Test baseline with insufficient samples"""
    # Only 5 samples, need at least 10 for 5-fold CV
    y = np.array([0, 0, 1, 1, 0])
    
    metrics_random = calculator.compute_random_baseline(y)
    metrics_majority = calculator.compute_majority_baseline(y)
    
    # Should return zeros for insufficient data
    assert metrics_random['balanced_accuracy'] == 0.0
    assert metrics_majority['balanced_accuracy'] == 0.0


def test_compute_baselines_for_target(calculator):
    """Test computing baselines for a specific target in dataframe"""
    # Create test dataframe
    df = pd.DataFrame({
        'target1': [0] * 70 + [1] * 30,
        'feature1': np.random.randn(100),
        'feature2': np.random.randn(100)
    })
    
    baselines = calculator.compute_baselines_for_target(
        df, 'target1', ['feature1', 'feature2']
    )
    
    # Should return both random and majority baselines
    assert 'random' in baselines
    assert 'majority' in baselines
    
    # Check random baseline
    assert 0.45 <= baselines['random']['balanced_accuracy'] <= 0.55
    assert 'accuracy' in baselines['random']
    assert 'auc' in baselines['random']
    
    # Check majority baseline
    assert 0.48 <= baselines['majority']['balanced_accuracy'] <= 0.52
    assert 0.65 <= baselines['majority']['accuracy'] <= 0.75
    assert 'auc' in baselines['majority']


def test_baseline_with_nan_values(calculator):
    """Test baseline calculator handles NaN values correctly"""
    # Create dataframe with NaN values
    df = pd.DataFrame({
        'target': [0, 1, np.nan, 0, 1, np.nan, 0, 1] * 15,  # 120 total, 80 non-nan
        'feature': np.random.randn(120)
    })
    
    baselines = calculator.compute_baselines_for_target(df, 'target', ['feature'])
    
    # Should compute on non-NaN values only
    assert baselines['random']['balanced_accuracy'] > 0.0
    assert baselines['majority']['balanced_accuracy'] > 0.0


def test_baseline_missing_target(calculator):
    """Test baseline calculator with missing target column"""
    df = pd.DataFrame({
        'feature': np.random.randn(100)
    })
    
    baselines = calculator.compute_baselines_for_target(df, 'nonexistent', ['feature'])
    
    # Should return zeros for missing target
    assert baselines['random']['balanced_accuracy'] == 0.0
    assert baselines['majority']['balanced_accuracy'] == 0.0


def test_baseline_deterministic(calculator):
    """Test that baselines are deterministic with fixed random_state"""
    y = np.array([0] * 70 + [1] * 30)
    
    # Run twice
    metrics1 = calculator.compute_random_baseline(y)
    metrics2 = calculator.compute_random_baseline(y)
    
    # Should get identical results due to fixed random_state
    assert metrics1['balanced_accuracy'] == metrics2['balanced_accuracy']
    assert metrics1['accuracy'] == metrics2['accuracy']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
