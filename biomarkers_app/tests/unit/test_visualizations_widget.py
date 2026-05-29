"""Unit tests for Visualizations Widget"""

import pytest
import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from app.ui.widgets.visualizations_widget import VisualizationsWidget, _build_heatmap_plot
from app.pipeline.types import ModelResult


@pytest.fixture
def qapp():
    """Create QApplication instance for testing"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def widget(qapp):
    """Create VisualizationsWidget instance"""
    w = VisualizationsWidget()
    yield w
    w.deleteLater()


@pytest.fixture
def sample_training_result():
    """Sample training result with ROC and confusion matrix data"""
    results = [
        ModelResult(
            target="D90_is_cr",
            phase="phase_15",
            model_family="LR",
            accuracy=0.82,
            balanced_accuracy=0.80,
            auc=0.85,
            f1_score=0.78,
            precision=0.81,
            recall=0.79,
            train_time=2.5,
            threshold=0.5,
            sample_size=200,
        ),
    ]
    metadata = {
        "phase": "phase_15",
        "roc_curves": [
            ("phase_15", "D90_is_cr", "LR", [0.0, 0.2, 0.5, 1.0], [0.0, 0.6, 0.9, 1.0]),
        ],
        "confusion_matrices": [
            ("phase_15", "D90_is_cr", "LR", [[50, 10], [5, 35]]),
        ],
    }
    return results, metadata


def test_widget_initialization(widget):
    """Test that widget initializes correctly (phase, category, view structure)"""
    assert widget is not None
    assert widget.phase_combo is not None
    assert widget.category_combo is not None
    assert widget.view_combo is not None
    assert widget.series_combo is not None
    assert widget.heatmap_metric_combo is not None
    assert widget.plot_stack is not None
    assert widget.phase_combo.currentText() == "All phases"


def test_view_options(widget):
    """Test that categories exist and each exposes expected views (dispersed structure)"""
    categories = list(widget.CATEGORY_VIEWS.keys())
    assert "Discrimination" in categories
    assert "Calibration" in categories
    assert "Classification" in categories
    assert "Summary" in categories
    assert widget.CATEGORY_VIEWS["Discrimination"] == ["ROC Curve", "Precision-Recall Curve"]
    assert "Calibration Curve" in widget.CATEGORY_VIEWS["Calibration"]
    assert "Confusion Matrix" in widget.CATEGORY_VIEWS["Classification"]
    assert "Performance Heatmap" in widget.CATEGORY_VIEWS["Summary"]
    assert "Class Distribution" in widget.CATEGORY_VIEWS["Summary"]
    # Default category (Discrimination) gives ROC and PR in view combo
    views = [widget.view_combo.itemText(i) for i in range(widget.view_combo.count())]
    assert "ROC Curve" in views
    assert "Precision-Recall Curve" in views


def test_heatmap_metric_options(widget):
    """Test heatmap metric combo has expected options"""
    metrics = [widget.heatmap_metric_combo.itemText(i) for i in range(widget.heatmap_metric_combo.count())]
    assert "balanced_accuracy" in metrics
    assert "auc" in metrics


def test_load_training_result(widget, sample_training_result):
    """Test loading training results"""
    results, metadata = sample_training_result
    widget.load_training_result(results, metadata)
    
    assert len(widget._results) == 1
    assert widget._results[0].target == "D90_is_cr"
    assert len(widget._roc_options) == 1
    assert len(widget._cm_options) == 1


def test_load_empty_result(widget):
    """Test loading empty results"""
    widget.load_training_result([], {})
    
    assert len(widget._results) == 0
    assert len(widget._roc_options) == 0
    assert len(widget._cm_options) == 0


def test_roc_option_label_includes_phase(widget, sample_training_result):
    """Test ROC options include phase in label for multi-phase format"""
    results, metadata = sample_training_result
    widget.load_training_result(results, metadata)
    
    assert len(widget._roc_options) == 1
    label, phase, target, model = widget._roc_options[0]
    assert "phase_15" in label
    assert "D90_is_cr" in label
    assert "LR" in label


def test_legacy_format_supported(widget):
    """Test legacy (target, model, fpr, tpr) format is supported"""
    results = [
        ModelResult("T1", "phase_0", "NN", 0.8, 0.78, 0.82, 0.76, 0.79, 0.77, 1.0, 0.5, 100),
    ]
    metadata = {
        "roc_curves": [
            ("T1", "NN", [0.0, 0.5, 1.0], [0.0, 0.8, 1.0]),
        ],
        "confusion_matrices": [
            ("T1", "NN", [[40, 5], [5, 50]]),
        ],
    }
    widget.load_training_result(results, metadata)
    
    assert len(widget._roc_options) == 1
    label, phase, target, model = widget._roc_options[0]
    assert phase is None
    assert target == "T1"
    assert model == "NN"


def test_heatmap_with_results(widget, sample_training_result):
    """Test heatmap view works with results (Summary category)"""
    results, metadata = sample_training_result
    widget.load_training_result(results, metadata)
    widget.category_combo.setCurrentText("Summary")
    widget.view_combo.setCurrentText("Performance Heatmap")
    widget._refresh_plot()
    
    # Should show heatmap (plot_container has content)
    assert widget.plot_stack.currentWidget() == widget.plot_container


def test_placeholder_when_no_data(widget):
    """Test placeholder shown when no training data"""
    widget.load_training_result([], {})
    widget.view_combo.setCurrentText("ROC Curve")
    widget._refresh_plot()
    
    assert widget.plot_stack.currentWidget() == widget.plot_placeholder


def test_calibration_and_pr_curves_loaded(widget):
    """Test calibration and PR curve data loaded from metadata (academic paper standards)"""
    results = [
        ModelResult("T1", "phase_0", "LR", 0.8, 0.78, 0.82, 0.76, 0.79, 0.77, 1.0, 0.5, 100),
    ]
    metadata = {
        "roc_curves": [("phase_0", "T1", "LR", [0.0, 0.5, 1.0], [0.0, 0.8, 1.0])],
        "confusion_matrices": [("phase_0", "T1", "LR", [[40, 5], [5, 50]])],
        "calibration_curves": [
            ("phase_0", "T1", "LR", [0.1, 0.3, 0.5, 0.7, 0.9], [0.0, 0.2, 0.5, 0.7, 1.0])
        ],
        "pr_curves": [
            ("phase_0", "T1", "LR", [0.9, 0.85, 0.8], [0.0, 0.5, 1.0], 0.82)
        ],
    }
    widget.load_training_result(results, metadata)
    assert len(widget._cal_options) == 1
    assert len(widget._pr_options) == 1
    widget.category_combo.setCurrentText("Calibration")
    widget.view_combo.setCurrentText("Calibration Curve")
    widget._refresh_plot()
    assert widget.plot_stack.currentWidget() == widget.plot_container
    widget.category_combo.setCurrentText("Discrimination")
    widget.view_combo.setCurrentText("Precision-Recall Curve")
    widget._refresh_plot()
    assert widget.plot_stack.currentWidget() == widget.plot_container


def test_class_distribution_view(widget, sample_training_result):
    """Test class distribution view from confusion matrices (Summary category)"""
    results, metadata = sample_training_result
    widget.load_training_result(results, metadata)
    widget.category_combo.setCurrentText("Summary")
    widget.view_combo.setCurrentText("Class Distribution")
    widget._refresh_plot()
    assert widget.plot_stack.currentWidget() == widget.plot_container


def test_status_shows_curve_metadata(widget):
    """Status label reflects curve_source and curve_note from training metadata."""
    results = [
        ModelResult(
            target="T1", phase="phase_0", model_family="LR",
            accuracy=0.8, balanced_accuracy=0.78, auc=0.82, f1_score=0.76,
            precision=0.8, recall=0.77, train_time=1.0, threshold=0.5, sample_size=50,
        ),
    ]
    metadata = {
        "curve_source": "last_outer_fold",
        "curve_note": "Illustrative curves from last outer CV fold.",
        "n_outer_splits": 5,
    }
    widget.load_training_result(results, metadata)
    assert "last_outer_fold" in widget.status_label.text()
    assert "Illustrative" in widget.status_label.text()


def test_no_series_shows_message_not_blank_container(widget):
    """When results exist but no curve series for the view, show plot_message (not empty plot area)."""
    results = [
        ModelResult(
            target="T1", phase="phase_0", model_family="LR",
            accuracy=0.8, balanced_accuracy=0.78, auc=0.82, f1_score=0.76,
            precision=0.8, recall=0.77, train_time=1.0, threshold=0.5, sample_size=50,
        ),
    ]
    widget.load_training_result(results, {})
    widget.category_combo.setCurrentText("Discrimination")
    widget.view_combo.setCurrentText("ROC Curve")
    widget._refresh_plot()
    assert widget.plot_stack.currentWidget() == widget.plot_message
    assert len(widget.plot_message.text()) > 20


def test_build_heatmap_plot_exclude_baselines_unit():
    """_build_heatmap_plot drops baseline model rows/cols when exclude_baselines=True."""
    results = [
        ModelResult("T1", "p1", "LR", 0.8, 0.78, 0.82, 0.76, 0.8, 0.77, 1.0, 0.5, 100),
        ModelResult("T1", "p1", "RF", 0.7, 0.68, 0.72, 0.66, 0.7, 0.67, 1.0, 0.5, 100),
        ModelResult("T1", "p1", "Baseline-Majority", 0.5, 0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 0.5, 100),
    ]
    canvas_all = _build_heatmap_plot(results, exclude_baselines=False)
    canvas_ex = _build_heatmap_plot(results, exclude_baselines=True)
    assert canvas_all is not None and canvas_ex is not None
    x_labels_ex = "".join(t.get_text() for t in canvas_ex.figure.get_axes()[0].get_xticklabels())
    assert "Baseline" not in x_labels_ex


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
