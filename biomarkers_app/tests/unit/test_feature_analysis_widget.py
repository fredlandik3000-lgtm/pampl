"""Unit tests for Feature Analysis Widget"""

import pytest
import sys
import pandas as pd
import numpy as np

from PyQt6.QtWidgets import QApplication
from app.ui.widgets.feature_analysis_widget import FeatureAnalysisWidget
from app.core.logger_manager import LoggerManager


@pytest.fixture
def qapp():
    """Create QApplication instance so Qt widgets can be created (prevents hang on first widget test)."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def logger():
    """Create a logger instance"""
    return LoggerManager(save_to_file=False)


@pytest.fixture
def sample_engineered_data():
    """Create sample engineered data"""
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'age': np.random.randint(18, 80, n_samples),
        'gender': np.random.choice(['Male', 'Female'], n_samples),
        'wbc_-6': np.random.uniform(2, 15, n_samples),
        'anc_-6': np.random.uniform(0.5, 10, n_samples),
        'ldh_-6': np.random.uniform(100, 1000, n_samples),
    }
    
    df = pd.DataFrame(data)
    
    # Add some missing values
    mask = np.random.random(n_samples) < 0.1
    df.loc[mask, 'wbc_-6'] = np.nan
    
    metadata = {
        'phase': 'phase_-6',
        'feature_count': 5,
        'selected_features': list(data.keys()),
        'categorical_count': 1,
        'numeric_count': 4,
        'engineering_time_sec': 0.123
    }
    
    return df, metadata


def test_widget_initialization(qapp, logger):
    """Test widget initializes correctly"""
    widget = FeatureAnalysisWidget(logger)
    
    assert widget.data is None
    assert widget.engineered_metadata == {}
    assert widget.refresh_btn.isEnabled() == False
    
    widget.deleteLater()


def test_widget_has_tabs(qapp, logger):
    """Test widget has all required tabs"""
    widget = FeatureAnalysisWidget(logger)
    
    assert widget.analysis_tabs.count() == 5
    assert widget.analysis_tabs.tabText(0) == "Feature Summary"
    assert widget.analysis_tabs.tabText(1) == "Statistics"
    assert widget.analysis_tabs.tabText(2) == "Missing Values"
    assert widget.analysis_tabs.tabText(3) == "Correlations"
    assert widget.analysis_tabs.tabText(4) == "Feature Importance"
    
    widget.deleteLater()


def test_load_engineered_features(qapp, logger, sample_engineered_data):
    """Test loading engineered features"""
    widget = FeatureAnalysisWidget(logger)
    
    data, metadata = sample_engineered_data
    widget.load_engineered_features(data, metadata)
    
    assert widget.data is not None
    assert len(widget.data) == 100
    assert widget.engineered_metadata == metadata
    assert widget.refresh_btn.isEnabled() == True
    
    widget.deleteLater()


def test_summary_view_populated(qapp, logger, sample_engineered_data):
    """Test summary view is populated with data"""
    widget = FeatureAnalysisWidget(logger)
    
    data, metadata = sample_engineered_data
    widget.load_engineered_features(data, metadata)
    
    summary_text = widget.summary_text.toPlainText()
    assert "phase_-6" in summary_text
    assert "Total Features: 5" in summary_text
    assert "Samples: 100" in summary_text
    
    widget.deleteLater()


def test_stats_view_populated(qapp, logger, sample_engineered_data):
    """Test statistics view is populated"""
    widget = FeatureAnalysisWidget(logger)
    
    data, metadata = sample_engineered_data
    widget.load_engineered_features(data, metadata)
    
    # Should have rows for numeric features (4 numeric features)
    assert widget.stats_table.rowCount() > 0
    assert widget.stats_table.columnCount() == 7
    
    widget.deleteLater()


def test_missing_values_view(qapp, logger, sample_engineered_data):
    """Test missing values view"""
    widget = FeatureAnalysisWidget(logger)
    
    data, metadata = sample_engineered_data
    widget.load_engineered_features(data, metadata)
    
    # Should show features with missing values
    # We added missing values to wbc_-6
    assert widget.missing_table.rowCount() > 0
    
    widget.deleteLater()


def test_refresh_button_works(qapp, logger, sample_engineered_data):
    """Test refresh button updates views"""
    widget = FeatureAnalysisWidget(logger)
    
    data, metadata = sample_engineered_data
    widget.load_engineered_features(data, metadata)
    
    # Click refresh
    widget.refresh_btn.click()
    
    # Should still have data
    assert widget.data is not None
    
    widget.deleteLater()


def test_empty_data_handling(qapp, logger):
    """Test widget handles empty data gracefully"""
    widget = FeatureAnalysisWidget(logger)
    
    empty_df = pd.DataFrame()
    metadata = {
        'phase': 'phase_-6',
        'feature_count': 0,
        'selected_features': [],
        'categorical_count': 0,
        'numeric_count': 0,
        'engineering_time_sec': 0.0
    }
    
    widget.load_engineered_features(empty_df, metadata)
    
    # Should not crash
    assert widget.data is not None
    assert len(widget.data) == 0
    
    widget.deleteLater()


def test_widget_cleanup(qapp, logger):
    """Test widget cleans up properly"""
    widget = FeatureAnalysisWidget(logger)
    
    widget.close()
    widget.deleteLater()
    # Should not crash
