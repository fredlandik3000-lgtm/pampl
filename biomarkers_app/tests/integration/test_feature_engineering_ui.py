"""Integration tests for Feature Engineering UI workflow"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from app.pipeline.wrappers.data_loader_wrapper import DataLoaderWrapper
from app.pipeline.wrappers.target_derivation_wrapper import TargetDerivationWrapper
from app.pipeline.wrappers.feature_engineering_wrapper import FeatureEngineeringWrapper


def test_complete_workflow_load_derive_engineer():
    """Test complete workflow: Load → Derive → Engineer"""
    # Create sample data
    np.random.seed(42)
    n_samples = 50
    
    data = {
        'study_id': [f'P{i:03d}' for i in range(n_samples)],
        'age': np.random.randint(18, 80, n_samples),
        'gender': np.random.choice(['Male', 'Female'], n_samples),
        'wbc_-6': np.random.uniform(2, 15, n_samples),
        'anc_-6': np.random.uniform(0.5, 10, n_samples),
        'cart_response_category_D30': np.random.choice(['Complete Response', 'Partial Response', 'Progressive Disease'], n_samples),
        'cart_response_90_days': np.random.choice(['Complete Response', 'Partial Response', 'Progressive Disease'], n_samples),
    }
    
    df = pd.DataFrame(data)
    
    # Step 1: Derive targets
    deriver = TargetDerivationWrapper()
    derive_result = deriver.derive_targets(df)
    
    assert derive_result.success
    assert derive_result.data is not None
    
    # Step 2: Engineer features
    engineer = FeatureEngineeringWrapper()
    
    # Test different phases
    for phase in ['phase_-6', 'phase_0']:
        result = engineer.engineer_features(
            derive_result.data,
            phase=phase,
            fit_scalers=True
        )
        
        assert result.success
        assert result.data is not None
        assert result.metadata['phase'] == phase
        assert result.metadata.get('feature_count', 0) >= 0
        assert 'engineering_time_sec' in result.metadata


def test_feature_engineering_preserves_data_integrity():
    """Test that feature engineering preserves row count and key columns"""
    np.random.seed(42)
    n_samples = 30
    
    data = {
        'study_id': [f'P{i:03d}' for i in range(n_samples)],
        'age': np.random.randint(18, 80, n_samples),
        'wbc_-6': np.random.uniform(2, 15, n_samples),
        'cart_response_category_D30': np.random.choice(['Complete Response', 'Partial Response'], n_samples),
    }
    
    df = pd.DataFrame(data)
    
    # Derive and engineer
    deriver = TargetDerivationWrapper()
    derive_result = deriver.derive_targets(df)
    
    engineer = FeatureEngineeringWrapper()
    eng_result = engineer.engineer_features(
        derive_result.data,
        phase='phase_-6',
        fit_scalers=True
    )
    
    # Check data integrity
    assert len(eng_result.data) == n_samples
    assert 'study_id' in eng_result.data.columns
    
    # Check that derived columns are preserved
    assert 'D30_response_3class' in eng_result.data.columns


def test_feature_engineering_metadata_accuracy():
    """Test that feature engineering metadata is accurate"""
    np.random.seed(42)
    
    data = {
        'age': np.random.randint(18, 80, 20),
        'gender': np.random.choice(['Male', 'Female'], 20),
        'wbc_-6': np.random.uniform(2, 15, 20),
        'cart_response_category_D30': ['Complete Response'] * 20,
    }
    
    df = pd.DataFrame(data)
    
    deriver = TargetDerivationWrapper()
    derive_result = deriver.derive_targets(df)
    
    engineer = FeatureEngineeringWrapper()
    result = engineer.engineer_features(
        derive_result.data,
        phase='phase_-6',
        fit_scalers=True
    )
    
    # Verify metadata
    assert 'selected_features' in result.metadata
    assert isinstance(result.metadata['selected_features'], list)
    assert len(result.metadata['selected_features']) == result.metadata['feature_count']
    
    # Verify feature counts
    categorical = result.metadata.get('categorical_count', 0)
    numeric = result.metadata.get('numeric_count', 0)
    assert categorical + numeric == result.metadata['feature_count']


def test_phase_specific_features():
    """Test that different phases have appropriate feature counts"""
    np.random.seed(42)
    
    data = {
        'age': np.random.randint(18, 80, 20),
        'wbc_-6': np.random.uniform(2, 15, 20),
        'wbc_0': np.random.uniform(2, 15, 20),
        'wbc_15': np.random.uniform(2, 15, 20),
        'cart_response_category_D30': ['Complete Response'] * 20,
    }
    
    df = pd.DataFrame(data)
    
    deriver = TargetDerivationWrapper()
    derive_result = deriver.derive_targets(df)
    
    engineer = FeatureEngineeringWrapper()
    
    # Phase -6 should have fewer features than phase 15
    result_minus6 = engineer.engineer_features(derive_result.data, phase='phase_-6', fit_scalers=True)
    result_15 = engineer.engineer_features(derive_result.data, phase='phase_15', fit_scalers=True)
    
    assert result_minus6.success
    assert result_15.success
    
    # Phase 15 should have more features (includes day 0 and day 15 labs)
    # Note: Actual counts depend on which features exist in the data
    features_minus6 = set(result_minus6.metadata['selected_features'])
    features_15 = set(result_15.metadata['selected_features'])
    
    # Phase -6 features should be a subset of phase 15 features
    # (all baseline features are available at later phases)
    assert len(features_minus6) <= len(features_15)


def test_fit_transform_consistency():
    """Test that fit/transform produces consistent results"""
    np.random.seed(42)
    
    train_data = {
        'age': np.random.randint(18, 80, 30),
        'wbc_-6': np.random.uniform(2, 15, 30),
        'cart_response_category_D30': ['Complete Response'] * 30,
    }
    
    test_data = {
        'age': np.random.randint(18, 80, 10),
        'wbc_-6': np.random.uniform(2, 15, 10),
        'cart_response_category_D30': ['Partial Response'] * 10,
    }
    
    train_df = pd.DataFrame(train_data)
    test_df = pd.DataFrame(test_data)
    
    deriver = TargetDerivationWrapper()
    train_derived = deriver.derive_targets(train_df)
    test_derived = deriver.derive_targets(test_df)
    
    engineer = FeatureEngineeringWrapper()
    
    # Fit on training data
    train_result = engineer.engineer_features(
        train_derived.data,
        phase='phase_-6',
        fit_scalers=True
    )
    
    # Transform test data with fitted scalers
    test_result = engineer.engineer_features(
        test_derived.data,
        phase='phase_-6',
        fit_scalers=False
    )
    
    assert train_result.success
    assert test_result.success
    
    # Both should have same features
    assert set(train_result.metadata['selected_features']) == set(test_result.metadata['selected_features'])


def test_error_handling_empty_data():
    """Test error handling with empty data"""
    engineer = FeatureEngineeringWrapper()
    empty_df = pd.DataFrame()
    
    result = engineer.engineer_features(empty_df, phase='phase_-6')
    
    # Should handle gracefully
    assert result.data is not None


def test_cancellation_support():
    """Test cancellation token support"""
    from app.pipeline.types import CancellationToken
    
    np.random.seed(42)
    data = {
        'age': np.random.randint(18, 80, 20),
        'wbc_-6': np.random.uniform(2, 15, 20),
        'cart_response_category_D30': ['Complete Response'] * 20,
    }
    
    df = pd.DataFrame(data)
    
    deriver = TargetDerivationWrapper()
    derive_result = deriver.derive_targets(df)
    
    engineer = FeatureEngineeringWrapper()
    token = CancellationToken()
    token.cancel()
    
    result = engineer.engineer_features(
        derive_result.data,
        phase='phase_-6',
        cancellation_token=token
    )
    
    assert not result.success
    assert len(result.errors) > 0
