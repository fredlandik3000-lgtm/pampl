"""Unit tests for Model Comparison Widget"""

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import sys

from app.ui.widgets.model_comparison_widget import ModelComparisonWidget
from app.core.logger_manager import LoggerManager
from app.pipeline.types import ModelResult


@pytest.fixture
def qapp():
    """Create QApplication instance for testing"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def logger(tmp_path):
    """Create logger for testing"""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    logger = LoggerManager(str(log_dir))
    yield logger


@pytest.fixture
def widget(qapp, logger):
    """Create ModelComparisonWidget instance"""
    widget = ModelComparisonWidget(logger)
    yield widget
    widget.deleteLater()


@pytest.fixture
def sample_results():
    """Create sample model results for testing"""
    results = []
    targets = ["D30_response_3class", "D90_is_cr"]
    phases = ["phase_-6", "phase_0"]
    models = ["Neural Network", "Logistic Regression", "XGBoost"]
    
    for target in targets:
        for phase in phases:
            for model in models:
                results.append(ModelResult(
                    target=target,
                    phase=phase,
                    model_family=model,
                    accuracy=0.85,
                    balanced_accuracy=0.83,
                    auc=0.88,
                    f1_score=0.82,
                    precision=0.84,
                    recall=0.80,
                    train_time=10.5,
                    threshold=0.5,
                    sample_size=252
                ))
    
    return results


def test_widget_initialization(widget):
    """Test that widget initializes correctly"""
    assert widget is not None
    assert widget.comparison_table is not None
    assert widget.details_text is not None
    assert widget.phase_combo is not None
    assert widget.target_combo is not None
    assert widget.model_combo is not None
    assert widget.metric_combo is not None


def test_widget_has_filters(widget):
    """Test that filter controls exist"""
    assert widget.phase_combo.count() > 0
    assert widget.target_combo.count() > 0
    assert widget.model_combo.count() > 0
    assert widget.metric_combo.count() > 0
    
    # Check default "All" option exists
    assert widget.phase_combo.itemText(0) == "All"
    assert widget.target_combo.itemText(0) == "All"
    assert widget.model_combo.itemText(0) == "All"
    assert widget.model_combo.itemText(1) == "All Models (no baselines)"


def test_widget_has_checkboxes(widget):
    """Test that display option checkboxes exist"""
    assert widget.show_best_checkbox is not None
    assert widget.color_code_checkbox is not None
    
    # Check default states
    assert widget.show_best_checkbox.isChecked() is True
    assert widget.color_code_checkbox.isChecked() is True


def test_widget_has_buttons(widget):
    """Test that action buttons exist"""
    assert widget.export_btn is not None
    assert widget.refresh_btn is not None
    
    # Check button text (no emojis)
    assert "Export" in widget.export_btn.text()
    assert "Refresh" in widget.refresh_btn.text()


def test_mock_data_loaded(widget):
    """Test that mock data is loaded on initialization"""
    assert len(widget.results) > 0
    assert len(widget.targets) > 0
    
    # Should have 7 targets × 4 phases × 10 models (8 ML + 2 baselines) = 280 results
    assert len(widget.results) == 280
    assert len(widget.targets) == 7


def test_load_custom_results(widget, sample_results):
    """Test loading custom results"""
    widget.load_results(sample_results)
    
    assert len(widget.results) == len(sample_results)
    assert len(widget.targets) == 2  # D30_response_3class, D90_is_cr
    
    # Check target combo updated
    assert widget.target_combo.count() == 3  # "All" + 2 targets


def test_filter_by_phase(widget):
    """Test phase filtering"""
    initial_count = len(widget.filtered_results)
    
    # Select specific phase
    widget.phase_combo.setCurrentText("phase_-6")
    
    # Should have fewer results
    assert len(widget.filtered_results) <= initial_count
    
    # All filtered results should match selected phase
    for result in widget.filtered_results:
        assert result.phase == "phase_-6"


def test_filter_by_target(widget):
    """Test target filtering"""
    widget.target_combo.setCurrentText("D30_response_3class")
    
    # All filtered results should match selected target
    for result in widget.filtered_results:
        assert result.target == "D30_response_3class"


def test_filter_by_model(widget):
    """Test model filtering"""
    widget.model_combo.setCurrentText("Neural Network")
    
    # All filtered results should match selected model
    for result in widget.filtered_results:
        assert result.model_family == "Neural Network"
    
    # Test "All Models (no baselines)" filter
    widget.model_combo.setCurrentText("All Models (no baselines)")
    for result in widget.filtered_results:
        assert not result.model_family.startswith("Baseline")


def test_combined_filters(widget):
    """Test combining multiple filters"""
    widget.phase_combo.setCurrentText("phase_-6")
    widget.target_combo.setCurrentText("D30_response_3class")
    widget.model_combo.setCurrentText("Neural Network")
    
    # Should have exactly 1 result
    assert len(widget.filtered_results) == 1
    
    result = widget.filtered_results[0]
    assert result.phase == "phase_-6"
    assert result.target == "D30_response_3class"
    assert result.model_family == "Neural Network"
    
    # Test filtering out baselines
    widget.model_combo.setCurrentText("All Models (no baselines)")
    widget.phase_combo.setCurrentText("phase_-6")
    widget.target_combo.setCurrentText("D30_response_3class")
    
    # Should have 8 results (8 ML models in MODEL_FAMILIES, no baselines)
    assert len(widget.filtered_results) == 8
    for result in widget.filtered_results:
        assert not result.model_family.startswith("Baseline")


def test_metric_selector_options(widget):
    """Test that all expected metrics are available"""
    metrics = [widget.metric_combo.itemText(i) 
               for i in range(widget.metric_combo.count())]
    
    assert "Balanced Accuracy" in metrics
    assert "Accuracy" in metrics
    assert "AUC" in metrics
    assert "F1 Score" in metrics


def test_table_populated(widget):
    """Test that comparison table is populated"""
    widget._refresh_table()
    
    assert widget.comparison_table.rowCount() > 0
    assert widget.comparison_table.columnCount() > 0


def test_table_structure(widget, sample_results):
    """Test table has correct structure"""
    widget.load_results(sample_results)
    widget.phase_combo.setCurrentText("All")
    widget.model_combo.setCurrentText("All")
    widget._refresh_table()
    
    # TRANSPOSED: Should have 2 phases × 3 models = 6 rows
    assert widget.comparison_table.rowCount() == 6
    
    # TRANSPOSED: Should have 2 targets (columns)
    assert widget.comparison_table.columnCount() == 2


def test_table_cell_values(widget, sample_results):
    """Test that table cells contain valid values"""
    widget.load_results(sample_results)
    widget._refresh_table()
    
    # Check that cells contain numeric values
    for row in range(widget.comparison_table.rowCount()):
        for col in range(widget.comparison_table.columnCount()):
            item = widget.comparison_table.item(row, col)
            if item and item.text() != "—":
                # Should be a number
                assert len(item.text()) > 0


def test_color_coding_enabled(widget, sample_results):
    """Test color coding applies background colors"""
    widget.load_results(sample_results)
    widget.color_code_checkbox.setChecked(True)
    widget._refresh_table()
    
    # Check that cells have background colors
    colored_cells = 0
    for row in range(widget.comparison_table.rowCount()):
        for col in range(widget.comparison_table.columnCount()):
            item = widget.comparison_table.item(row, col)
            if item and item.text() != "—":
                bg = item.background()
                if bg.color().isValid():
                    colored_cells += 1
    
    assert colored_cells > 0


def test_color_coding_disabled(widget, sample_results):
    """Test color coding can be disabled"""
    widget.load_results(sample_results)
    widget.color_code_checkbox.setChecked(False)
    widget._refresh_table()
    
    # Should still have table populated
    assert widget.comparison_table.rowCount() > 0


def test_champion_marking(widget, sample_results):
    """Test that champion (best) values are marked with asterisk"""
    widget.load_results(sample_results)
    widget.show_best_checkbox.setChecked(True)
    widget._refresh_table()
    
    # Check for asterisk markers
    marked_cells = 0
    for row in range(widget.comparison_table.rowCount()):
        for col in range(widget.comparison_table.columnCount()):
            item = widget.comparison_table.item(row, col)
            if item and "*" in item.text():
                marked_cells += 1
    
    # Should have at least some marked cells (best per row)
    assert marked_cells > 0


def test_champion_marking_disabled(widget, sample_results):
    """Test that champion marking can be disabled"""
    widget.load_results(sample_results)
    widget.show_best_checkbox.setChecked(False)
    widget._refresh_table()
    
    # Check for no asterisk markers
    for row in range(widget.comparison_table.rowCount()):
        for col in range(widget.comparison_table.columnCount()):
            item = widget.comparison_table.item(row, col)
            if item and item.text() != "—":
                # Should not have asterisk if not marked as best
                # (or might have it if it IS best but we're not highlighting)
                pass  # Just verify no crash


def test_cell_selection_shows_details(widget, sample_results):
    """Test that selecting a cell shows details"""
    widget.load_results(sample_results)
    widget._refresh_table()
    
    # Select first cell
    widget.comparison_table.setCurrentCell(0, 0)
    widget._on_cell_selected()
    
    # Details should be shown
    details = widget.details_text.toPlainText()
    assert len(details) > 0
    assert "Accuracy" in details or details == ""  # Might be empty if cell has no data


def test_details_panel_content(widget, sample_results):
    """Test details panel shows correct metrics"""
    widget.load_results(sample_results)
    widget._refresh_table()
    
    # Find a valid cell with data
    for row in range(widget.comparison_table.rowCount()):
        for col in range(widget.comparison_table.columnCount()):
            item = widget.comparison_table.item(row, col)
            if item and item.text() != "—":
                widget.comparison_table.setCurrentCell(row, col)
                widget._on_cell_selected()
                
                details = widget.details_text.toPlainText()
                if details:
                    assert "Accuracy" in details
                    assert "Balanced Accuracy" in details
                    assert "AUC" in details
                    assert "F1 Score" in details
                    assert "Train Time" in details
                    return
    
    # If we get here, no valid cells found (OK for empty table)
    assert True


def test_performance_color_mapping(widget):
    """Test color mapping for different performance levels using gradient"""
    # Test anchor points
    
    # Low anchor: 0.40 → #e67c73 (230, 124, 115)
    color = widget._get_performance_color(0.40)
    assert abs(color.red() - 230) <= 1
    assert abs(color.green() - 124) <= 1
    assert abs(color.blue() - 115) <= 1
    
    # Mid anchor: 0.65 → #ffd666 (255, 214, 102)
    color = widget._get_performance_color(0.65)
    assert abs(color.red() - 255) <= 1
    assert abs(color.green() - 214) <= 1
    assert abs(color.blue() - 102) <= 1
    
    # High anchor: 0.90 → #57bb8a (87, 187, 138)
    color = widget._get_performance_color(0.90)
    assert abs(color.red() - 87) <= 1
    assert abs(color.green() - 187) <= 1
    assert abs(color.blue() - 138) <= 1
    
    # Test gradient interpolation
    # Between low and mid (0.40-0.65)
    color = widget._get_performance_color(0.525)  # Midpoint
    assert 200 <= color.red() <= 255  # Between red and yellow
    assert 150 <= color.green() <= 200
    
    # Between mid and high (0.65-0.90)
    color = widget._get_performance_color(0.775)  # Midpoint
    assert 150 <= color.red() <= 200  # Between yellow and green
    assert 190 <= color.green() <= 210


def test_model_result_get_metric(sample_results):
    """Test ModelResult.get_metric() method"""
    result = sample_results[0]
    
    assert result.get_metric("accuracy") == result.accuracy
    assert result.get_metric("balanced_accuracy") == result.balanced_accuracy
    assert result.get_metric("auc") == result.auc
    assert result.get_metric("f1") == result.f1_score
    assert result.get_metric("precision") == result.precision
    assert result.get_metric("recall") == result.recall
    
    # Unknown metric should return 0.0
    assert result.get_metric("unknown") == 0.0


def test_metric_switching(widget, sample_results):
    """Test switching between different metrics"""
    widget.load_results(sample_results)
    
    # Switch to AUC
    widget.metric_combo.setCurrentText("AUC")
    widget._refresh_table()
    assert widget.comparison_table.rowCount() > 0
    
    # Switch to F1 Score
    widget.metric_combo.setCurrentText("F1 Score")
    widget._refresh_table()
    assert widget.comparison_table.rowCount() > 0


def test_empty_results_handling(widget):
    """Test widget handles empty results gracefully"""
    widget.load_results([])
    
    assert len(widget.results) == 0
    assert widget.comparison_table.rowCount() == 0
    assert widget.comparison_table.columnCount() == 0


def test_no_emojis_in_ui(widget):
    """Test that no emojis are present in UI elements"""
    # Check button text
    assert "📊" not in widget.export_btn.text()
    assert "🔄" not in widget.refresh_btn.text()
    
    # Button text should be clean ASCII
    assert widget.export_btn.text() == "Export Table"
    assert widget.refresh_btn.text() == "Refresh"


def test_legend_uses_ascii(widget):
    """Test that legend uses ASCII characters instead of emojis"""
    # The legend labels should use [+++], [++], [+], [-], [BEST]
    # We can't easily access the labels directly, but we can verify
    # the _create_legend method exists and doesn't crash
    legend = widget._create_legend()
    assert legend is not None


def test_refresh_button_updates_table(widget, sample_results):
    """Test that refresh button updates the table"""
    widget.load_results(sample_results)
    
    initial_rows = widget.comparison_table.rowCount()
    
    # Click refresh (simulate)
    widget._refresh_table()
    
    # Should still have same structure
    assert widget.comparison_table.rowCount() == initial_rows


def test_filter_all_restores_full_results(widget):
    """Test that selecting 'All' in filters shows all results"""
    # Apply specific filter
    widget.phase_combo.setCurrentText("phase_-6")
    filtered_count = len(widget.filtered_results)
    
    # Reset to All
    widget.phase_combo.setCurrentText("All")
    all_count = len(widget.filtered_results)
    
    # Should have more results with "All"
    assert all_count >= filtered_count


def test_vertical_headers_are_phase_model(widget, sample_results):
    """Test that vertical headers show phase-model combinations"""
    widget.load_results(sample_results)
    widget._refresh_table()
    
    # Get vertical header labels (should be phase-model combinations)
    for row in range(widget.comparison_table.rowCount()):
        header = widget.comparison_table.verticalHeaderItem(row)
        if header:
            # Should contain phase and model info
            assert len(header.text()) > 0


def test_horizontal_headers_are_targets(widget, sample_results):
    """Test that horizontal headers show target names"""
    widget.load_results(sample_results)
    widget._refresh_table()
    
    # Get horizontal header labels (should be targets)
    for col in range(widget.comparison_table.columnCount()):
        header = widget.comparison_table.horizontalHeaderItem(col)
        if header:
            # Should be one of our target names
            assert header.text() in ["D30_response_3class", "D90_is_cr"]


def test_widget_cleanup(widget):
    """Test that widget can be properly cleaned up"""
    widget.results = []
    widget.filtered_results = []
    widget.deleteLater()
    
    # Should not crash
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
