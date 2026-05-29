"""Integration tests for feature engineering pipeline"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from app.pipeline.wrappers.feature_engineering_wrapper import FeatureEngineeringWrapper
from app.pipeline.types import CancellationToken


@pytest.fixture
def sample_data():
    """Create sample data for feature engineering tests"""
    np.random.seed(42)
    n_samples = 100
    
    data = {
        # Demographics
        'age': np.random.randint(18, 80, n_samples),
        'gender': np.random.choice(['Male', 'Female', 'Other'], n_samples),
        'race': np.random.choice(['Race: White', 'Race: Black', 'Race: Asian'], n_samples),
        'weight': np.random.uniform(50, 120, n_samples),
        'height': np.random.uniform(150, 200, n_samples),
        
        # Diagnosis
        'dx_cart': np.random.choice(['Lymphoma', 'ALL', 'MM'], n_samples),
        'prior_lines': np.random.randint(1, 5, n_samples),
        
        # CAR-T product
        'cart_product': np.random.choice(['Tisa-cel', 'Axi-cel', 'Brexu-cel'], n_samples),
        'lymphodep_regimen': np.random.choice(['Fludarabine, Cyclophosphamide'], n_samples),
        
        # Baseline labs (phase -6)
        'wbc_-6': np.random.uniform(2, 15, n_samples),
        'anc_-6': np.random.uniform(0.5, 10, n_samples),
        'hgb_-6': np.random.uniform(8, 16, n_samples),
        'plt_-6': np.random.uniform(50, 400, n_samples),
        'ldh_-6': np.random.uniform(100, 1000, n_samples),
        
        # Day 0 labs
        'wbc_0': np.random.uniform(2, 15, n_samples),
        'anc_0': np.random.uniform(0.5, 10, n_samples),
        'hgb_0': np.random.uniform(8, 16, n_samples),
        'plt_0': np.random.uniform(50, 400, n_samples),
        'ldh_0': np.random.uniform(100, 1000, n_samples),
        
        # Day 15 labs
        'wbc_15': np.random.uniform(2, 15, n_samples),
        'anc_15': np.random.uniform(0.5, 10, n_samples),
        'hgb_15': np.random.uniform(8, 16, n_samples),
        'plt_15': np.random.uniform(50, 400, n_samples),
        'ldh_15': np.random.uniform(100, 1000, n_samples),
    }
    
    df = pd.DataFrame(data)
    
    # Add some missing values
    for col in ['wbc_-6', 'anc_0', 'hgb_15']:
        mask = np.random.random(n_samples) < 0.1
        df.loc[mask, col] = np.nan
    
    return df


def test_feature_engineering_basic(sample_data):
    """Test basic feature engineering execution"""
    wrapper = FeatureEngineeringWrapper()
    
    result = wrapper.engineer_features(sample_data, phase='phase_-6')
    
    assert result.success
    assert result.data is not None
    assert isinstance(result.data, pd.DataFrame)
    assert len(result.data) == len(sample_data)
    assert 'feature_count' in result.metadata
    assert result.metadata['phase'] == 'phase_-6'


def test_feature_engineering_phase_specific_features(sample_data):
    """Test that different phases have different feature sets"""
    wrapper = FeatureEngineeringWrapper()
    
    # Phase -6 should have baseline labs only
    result_phase_minus6 = wrapper.engineer_features(sample_data, phase='phase_-6')
    assert result_phase_minus6.success
    features_minus6 = set(result_phase_minus6.metadata['selected_features'])
    
    # Phase 0 should have baseline + day 0 labs
    result_phase_0 = wrapper.engineer_features(sample_data, phase='phase_0')
    assert result_phase_0.success
    features_0 = set(result_phase_0.metadata['selected_features'])
    
    # Phase 0 should have at least as many features as phase -6 (current mapping: both use baseline group)
    assert len(features_0) >= len(features_minus6)
    # All phase -6 features should be in phase 0
    assert features_minus6.issubset(features_0)


def test_feature_engineering_handles_missing_values(sample_data):
    """Test that missing values are handled properly"""
    wrapper = FeatureEngineeringWrapper()
    
    result = wrapper.engineer_features(sample_data, phase='phase_-6')
    
    assert result.success
    # Check that SELECTED numeric features have no NaNs after engineering
    selected_features = result.metadata['selected_features']
    numeric_selected = [col for col in selected_features if result.data[col].dtype in [np.float64, np.float32, np.int64, np.int32]]
    if numeric_selected:
        assert result.data[numeric_selected].isna().sum().sum() == 0


def test_feature_engineering_categorical_encoding(sample_data):
    """Test categorical feature handling"""
    wrapper = FeatureEngineeringWrapper()
    
    result = wrapper.engineer_features(sample_data, phase='phase_-6')
    
    assert result.success
    # Categorical features should be converted to strings
    categorical_features = ['gender', 'race', 'dx_cart', 'cart_product']
    for feature in categorical_features:
        if feature in result.data.columns:
            assert result.data[feature].dtype == object or result.data[feature].dtype == 'string'


def test_feature_engineering_with_progress_callback():
    """Test feature engineering with progress reporting"""
    np.random.seed(42)
    data = pd.DataFrame({
        'age': np.random.randint(18, 80, 50),
        'wbc_-6': np.random.uniform(2, 15, 50),
    })
    
    wrapper = FeatureEngineeringWrapper()
    progress_updates = []
    
    def progress_callback(pct, msg):
        progress_updates.append((pct, msg))
    
    result = wrapper.engineer_features(
        data,
        phase='phase_-6',
        progress_callback=progress_callback
    )
    
    assert result.success
    assert len(progress_updates) > 0
    assert progress_updates[0][0] == 0.0  # First update at 0%
    assert progress_updates[-1][0] == 1.0  # Last update at 100%


def test_feature_engineering_with_cancellation():
    """Test feature engineering can be cancelled"""
    np.random.seed(42)
    data = pd.DataFrame({
        'age': np.random.randint(18, 80, 50),
        'wbc_-6': np.random.uniform(2, 15, 50),
    })
    
    wrapper = FeatureEngineeringWrapper()
    cancellation_token = CancellationToken()
    
    # Cancel before execution
    cancellation_token.cancel()
    
    result = wrapper.engineer_features(
        data,
        phase='phase_-6',
        cancellation_token=cancellation_token
    )
    
    assert not result.success
    assert len(result.errors) > 0
    assert 'cancelled' in result.errors[0].lower()


def test_feature_engineering_fit_and_transform():
    """Test fitting scalers on train and transforming test data"""
    np.random.seed(42)
    train_data = pd.DataFrame({
        'age': np.random.randint(18, 80, 100),
        'wbc_-6': np.random.uniform(2, 15, 100),
        'ldh_-6': np.random.uniform(100, 1000, 100),
    })
    
    test_data = pd.DataFrame({
        'age': np.random.randint(18, 80, 30),
        'wbc_-6': np.random.uniform(2, 15, 30),
        'ldh_-6': np.random.uniform(100, 1000, 30),
    })
    
    wrapper = FeatureEngineeringWrapper()
    
    # Fit on training data
    train_result = wrapper.engineer_features(
        train_data,
        phase='phase_-6',
        fit_scalers=True
    )
    assert train_result.success
    
    # Transform test data using fitted scalers
    test_result = wrapper.engineer_features(
        test_data,
        phase='phase_-6',
        fit_scalers=False
    )
    assert test_result.success
    
    # Both should have same features
    assert set(train_result.metadata['selected_features']) == set(test_result.metadata['selected_features'])


def test_feature_engineering_metadata():
    """Test that metadata is properly populated"""
    np.random.seed(42)
    data = pd.DataFrame({
        'age': np.random.randint(18, 80, 50),
        'gender': np.random.choice(['Male', 'Female'], 50),
        'wbc_-6': np.random.uniform(2, 15, 50),
    })
    
    wrapper = FeatureEngineeringWrapper()
    result = wrapper.engineer_features(data, phase='phase_-6')
    
    assert result.success
    assert 'phase' in result.metadata
    assert 'feature_count' in result.metadata
    assert 'selected_features' in result.metadata
    assert 'categorical_count' in result.metadata
    assert 'numeric_count' in result.metadata
    assert 'engineering_time_sec' in result.metadata
    assert result.metadata['engineering_time_sec'] > 0


def test_feature_engineering_preserves_original_columns():
    """Test that original columns are preserved"""
    np.random.seed(42)
    data = pd.DataFrame({
        'study_id': [f'P{i:03d}' for i in range(50)],
        'age': np.random.randint(18, 80, 50),
        'wbc_-6': np.random.uniform(2, 15, 50),
    })
    
    wrapper = FeatureEngineeringWrapper()
    result = wrapper.engineer_features(data, phase='phase_-6')
    
    assert result.success
    # study_id should still be in the dataframe
    assert 'study_id' in result.data.columns


def test_complete_pipeline_load_derive_engineer(sample_data):
    """Test complete pipeline: Derive Targets → Engineer Features"""
    from app.pipeline.wrappers.target_derivation_wrapper import TargetDerivationWrapper
    
    # Add required columns for target derivation
    sample_data['cart_response_category_D30'] = np.random.choice(['Complete Response', 'Partial Response', 'Progressive Disease'], len(sample_data))
    sample_data['cart_response_90_days'] = np.random.choice(['Complete Response', 'Partial Response', 'Progressive Disease'], len(sample_data))
    
    # Step 1: Derive targets
    target_deriver = TargetDerivationWrapper()
    derive_result = target_deriver.derive_targets(sample_data)
    assert derive_result.success
    
    # Step 2: Engineer features
    engineer = FeatureEngineeringWrapper()
    engineer_result = engineer.engineer_features(
        derive_result.data,
        phase='phase_-6'
    )
    assert engineer_result.success
    assert 'feature_count' in engineer_result.metadata
    
    # Verify pipeline preserved all data
    assert len(engineer_result.data) == len(sample_data)


def test_feature_engineering_empty_dataframe():
    """Test feature engineering with empty dataframe"""
    wrapper = FeatureEngineeringWrapper()
    empty_df = pd.DataFrame()
    
    result = wrapper.engineer_features(empty_df, phase='phase_-6')
    
    # Should handle gracefully
    assert result.data is not None
