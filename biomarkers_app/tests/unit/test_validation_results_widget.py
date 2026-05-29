"""Unit tests for Validation Results Widget"""

import pytest
import sys

from PyQt6.QtWidgets import QApplication

from app.ui.widgets.validation_results_widget import (
    ValidationResultsWidget,
    _aggregate_metrics,
)
from app.core.logger_manager import LoggerManager
from app.pipeline.types import ModelResult


@pytest.fixture
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def logger():
    return LoggerManager(save_to_file=False)


@pytest.fixture
def widget(qapp, logger):
    w = ValidationResultsWidget(logger)
    yield w
    w.deleteLater()


def test_widget_initialization(widget):
    """Test widget initializes correctly"""
    assert widget is not None
    assert widget.split_info is not None
    assert widget.metrics_table is not None
    assert widget.train_test_label is not None


def test_set_split_info(widget):
    """Test set_split_info updates display"""
    widget.set_split_info(test_fraction=0.3, random_seed=42)
    text = widget.split_info.toPlainText()
    assert "70" in text  # 70% train
    assert "30" in text  # 30% test
    assert "42" in text
    assert "Stratified" in text


def test_aggregate_metrics_empty():
    """Test _aggregate_metrics with empty list"""
    assert _aggregate_metrics([]) == {}


def test_aggregate_metrics_single():
    """Test _aggregate_metrics with single result"""
    r = ModelResult(
        target="t1", phase="p1", model_family="NN",
        accuracy=0.8, balanced_accuracy=0.75, auc=0.82, f1_score=0.7,
        sample_size=100,
    )
    agg = _aggregate_metrics([r])
    assert agg["n_models"] == 1
    assert agg["accuracy"] == (0.8, 0.0)
    assert agg["balanced_accuracy"] == (0.75, 0.0)
    assert agg["auc"] == (0.82, 0.0)
    assert agg["f1_score"] == (0.7, 0.0)
    assert agg["sample_size"] == 100


def test_aggregate_metrics_multiple():
    """Test _aggregate_metrics with multiple results"""
    results = [
        ModelResult("t1", "p1", "NN", 0.8, 0.75, 0.82, 0.7, sample_size=100),
        ModelResult("t1", "p1", "LR", 0.78, 0.73, 0.80, 0.68, sample_size=100),
        ModelResult("t1", "p1", "XGB", 0.82, 0.77, 0.85, 0.72, sample_size=100),
    ]
    agg = _aggregate_metrics(results)
    assert agg["n_models"] == 3
    assert 0.78 <= agg["accuracy"][0] <= 0.83
    assert agg["accuracy"][1] > 0  # non-zero std


def test_set_validation_metrics_empty(widget):
    """Test set_validation_metrics with empty list resets to placeholder"""
    widget.set_validation_metrics([])
    assert widget.train_test_label.text() == "—"
    assert widget.metrics_table.item(0, 1).text() == "—"


def test_set_validation_metrics_with_results(widget):
    """Test set_validation_metrics populates metrics from results"""
    results = [
        ModelResult("t1", "p1", "NN", 0.85, 0.80, 0.88, 0.82, sample_size=75),
        ModelResult("t1", "p1", "LR", 0.82, 0.78, 0.85, 0.79, sample_size=75),
    ]
    widget.set_validation_metrics(results)
    assert "OK" in widget.train_test_label.text()
    assert "2" in widget.train_test_label.text()
    assert "0.83" in widget.metrics_table.item(0, 1).text() or "0.84" in widget.metrics_table.item(0, 1).text()


def test_set_kfold_metrics_empty(widget):
    """Test set_kfold_metrics with empty dict hides k-fold frame"""
    widget.set_kfold_metrics({})
    assert not widget.kfold_frame.isVisible()
    assert "N/A" in widget.kfold_label.text()


def test_set_kfold_metrics_with_data(widget):
    """Test set_kfold_metrics populates k-fold table"""
    widget.set_kfold_metrics({
        "accuracy": (0.82, 0.03),
        "balanced_accuracy": (0.78, 0.04),
        "auc": (0.85, 0.02),
        "f1_score": (0.76, 0.05),
    })
    assert "OK" in widget.kfold_label.text()
    assert widget.kfold_table.item(0, 1) is not None
    assert "0.82" in widget.kfold_table.item(0, 1).text()


def test_set_bootstrap_metrics_empty(widget):
    """Test set_bootstrap_metrics with empty list hides bootstrap frame"""
    widget.set_bootstrap_metrics([])
    assert not widget.bootstrap_frame.isVisible()
    assert "N/A" in widget.bootstrap_label.text()


def test_set_bootstrap_metrics_with_data(widget):
    """Test set_bootstrap_metrics populates bootstrap table"""
    widget.set_bootstrap_metrics([
        ("phase_-6", "D30_response", "NN", 0.80, 0.72, 0.88),
        ("phase_-6", "D30_response", "LR", 0.76, 0.68, 0.84),
    ])
    assert "OK" in widget.bootstrap_label.text()
    assert widget.bootstrap_table.rowCount() == 2
    assert "0.80" in widget.bootstrap_table.item(0, 1).text()
    assert "0.72" in widget.bootstrap_table.item(0, 2).text()


def test_baseline_comparison_visible_when_results_have_baseline(widget):
    """Block B2: Model vs baseline table is populated when results include Baseline-Majority and models."""
    from app.pipeline.types import ModelResult
    results = [
        ModelResult("t1", "phase_-6", "Baseline-Majority", 0.7, 0.62, 0.5, 0.65, 0.0, 0.0),
        ModelResult("t1", "phase_-6", "LR", 0.72, 0.65, 0.68, 0.66, 0.0, 0.0),
    ]
    widget.set_validation_metrics(results)
    assert widget.baseline_comparison_table.rowCount() >= 1
    assert "0.62" in widget.baseline_comparison_table.item(0, 2).text()
    # Column 5 = Δ vs Majority, column 6 = Beat Majority
    assert widget.baseline_comparison_table.item(0, 6).text() == "Yes"


def test_set_target_summary_populates_table(widget):
    """Block C3: set_target_summary shows class balance table."""
    widget.set_target_summary([
        {"target": "crs_grade_ge2", "phase": "phase_-6", "n_total": 80, "train_class_counts": {0: 55, 1: 25}, "gate_filtered": False},
    ])
    assert widget.target_summary_table.rowCount() == 1
    assert "crs_grade_ge2" in widget.target_summary_table.item(0, 0).text()
    assert "80" in widget.target_summary_table.item(0, 2).text()
    assert "No" in widget.target_summary_table.item(0, 4).text()
