"""Integration tests for target derivation"""

import pytest
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

from app.pipeline.types import CancellationToken
from app.pipeline.wrappers.target_derivation_wrapper import TargetDerivationWrapper


@pytest.fixture
def sample_data():
    """Create sample clinical data with response columns"""
    data = {
        'patient_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
        'age': [45, 52, 38, 61, 48],
        'disease': ['DLBCL', 'MCL', 'FL', 'DLBCL', 'MCL'],
        # Response columns that will be used for derivation
        'cart_response_category_D30': [
            'Complete Response',
            'Partial Response',
            'Progressive Disease',
            'Complete Response',
            'Inevaluable'
        ],
        'cart_response_90_days': [
            'Complete Response',
            'Partial Response',
            'Complete Response',
            np.nan,
            'Complete Response'
        ],
        'cart_response_6_mos': [
            'Complete Response',
            'Complete Response',
            'Partial Response',
            'Progressive Disease',
            'Complete Response'
        ],
        'cart_response_1_yr': [
            'Complete Response',
            np.nan,
            'Progressive Disease',
            'Progressive Disease',
            'Complete Response'
        ],
        'best_response': [
            'Complete Response',
            'Complete Response',
            'Complete Response',
            'Partial Response',
            'Complete Response'
        ]
    }
    return pd.DataFrame(data)


def test_target_derivation_basic(sample_data):
    """Test basic target derivation functionality"""
    wrapper = TargetDerivationWrapper()
    
    result = wrapper.derive_targets(sample_data)
    
    assert result.success
    assert result.data is not None
    assert isinstance(result.data, pd.DataFrame)
    
    # Should have created gates
    assert 'gates_created' in result.metadata
    assert len(result.metadata['gates_created']) > 0
    
    # Should have created targets
    assert 'targets_created' in result.metadata
    assert len(result.metadata['targets_created']) > 0


def test_target_derivation_creates_gates(sample_data):
    """Test that evaluability gates are created"""
    wrapper = TargetDerivationWrapper()
    
    result = wrapper.derive_targets(sample_data)
    
    assert result.success
    gates = result.metadata['gates_created']
    
    # Expected gates based on DERIVED_CONFIG
    expected_gates = [
        'D30_evaluable_gate',
        'D90_evaluable_gate',
        'M6_evaluable_gate',
        'Y1_evaluable_gate',
        'BEST_evaluable_gate'
    ]
    
    for gate in expected_gates:
        assert gate in gates, f"Expected gate {gate} not created"
        assert gate in result.data.columns


def test_target_derivation_creates_response_targets(sample_data):
    """Test that response targets are created"""
    wrapper = TargetDerivationWrapper()
    
    result = wrapper.derive_targets(sample_data)
    
    assert result.success
    targets = result.metadata['targets_created']
    
    # Should create D30_response_3class (mode='3class')
    assert 'D30_response_3class' in targets
    assert 'D30_response_3class' in result.data.columns
    
    # Should create D90_is_cr (mode='binary_cr')
    assert 'D90_is_cr' in targets
    assert 'D90_is_cr' in result.data.columns


def test_target_derivation_evaluability_stats(sample_data):
    """Test that evaluability statistics are calculated"""
    wrapper = TargetDerivationWrapper()
    
    result = wrapper.derive_targets(sample_data)
    
    assert result.success
    assert 'evaluability_stats' in result.metadata
    
    stats = result.metadata['evaluability_stats']
    
    # Check D30 gate - should have 1 inevaluable (row with 'Inevaluable')
    if 'D30_evaluable_gate' in stats:
        d30_stats = stats['D30_evaluable_gate']
        assert 'evaluable' in d30_stats
        assert 'inevaluable' in d30_stats
        assert d30_stats['inevaluable'] == 1  # One inevaluable record


def test_target_derivation_with_progress(sample_data):
    """Test target derivation with progress callback"""
    wrapper = TargetDerivationWrapper()
    
    progress_updates = []
    
    def progress_callback(percent, message):
        progress_updates.append((percent, message))
    
    result = wrapper.derive_targets(sample_data, progress_callback=progress_callback)
    
    assert result.success
    assert len(progress_updates) > 0
    # Should have progress at 0%, 20%, 80%, 100%
    assert any(p[0] == 100.0 for p in progress_updates)


def test_target_derivation_with_cancellation(sample_data):
    """Test target derivation with immediate cancellation"""
    wrapper = TargetDerivationWrapper()
    cancellation_token = CancellationToken()
    
    # Cancel immediately
    cancellation_token.cancel()
    
    result = wrapper.derive_targets(
        sample_data,
        cancellation_token=cancellation_token
    )
    
    assert not result.success
    assert "cancel" in result.errors[0].lower()


def test_target_derivation_preserves_original_columns(sample_data):
    """Test that original columns are preserved"""
    wrapper = TargetDerivationWrapper()
    
    original_cols = set(sample_data.columns)
    result = wrapper.derive_targets(sample_data)
    
    assert result.success
    
    # All original columns should still be present
    for col in original_cols:
        assert col in result.data.columns


def test_target_derivation_metadata(sample_data):
    """Test that metadata contains expected fields"""
    wrapper = TargetDerivationWrapper()
    
    result = wrapper.derive_targets(sample_data)
    
    assert result.success
    
    # Check required metadata fields
    assert 'targets_created' in result.metadata
    assert 'gates_created' in result.metadata
    assert 'evaluability_stats' in result.metadata
    assert 'target_completeness' in result.metadata
    assert 'total_columns_added' in result.metadata
    assert 'derive_time_sec' in result.metadata
    
    # Check types
    assert isinstance(result.metadata['targets_created'], list)
    assert isinstance(result.metadata['gates_created'], list)
    assert isinstance(result.metadata['evaluability_stats'], dict)
    assert isinstance(result.metadata['target_completeness'], dict)
    assert isinstance(result.metadata['derive_time_sec'], float)


def test_target_derivation_warnings_for_inevaluable(sample_data):
    """Test that warnings are generated for inevaluable records"""
    wrapper = TargetDerivationWrapper()
    
    result = wrapper.derive_targets(sample_data)
    
    assert result.success
    
    # Should have warnings for gates with inevaluable records
    # D30 has 1 inevaluable, D90 has 1 missing (also counts as inevaluable potentially)
    assert len(result.warnings) > 0
    
    # Check that warnings mention inevaluable
    warning_text = ' '.join(result.warnings).lower()
    assert 'inevaluable' in warning_text


def test_target_derivation_empty_dataframe():
    """Test target derivation with empty DataFrame"""
    wrapper = TargetDerivationWrapper()
    
    empty_df = pd.DataFrame()
    result = wrapper.derive_targets(empty_df)
    
    # Should fail gracefully with empty DataFrame
    # (or succeed with no targets - depends on implementation)
    assert result.data is not None or not result.success
