"""Unit tests for Registry Viewer Widget"""

import pytest
import sys

from PyQt6.QtWidgets import QApplication

from app.ui.widgets.registry_viewer_widget import RegistryViewerWidget
from app.core.logger_manager import LoggerManager
from app.pipeline.types import ModelResult


@pytest.fixture
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def logger(tmp_path):
    return LoggerManager(str(tmp_path / "logs"))


@pytest.fixture
def widget(qapp, logger):
    w = RegistryViewerWidget(logger)
    yield w
    w.deleteLater()


def test_widget_initialization(widget):
    """Test widget initializes correctly"""
    assert widget is not None
    assert widget.table is not None
    assert widget.save_current_btn is not None
    assert widget.save_current_btn.isEnabled() is False


def test_set_current_results_enables_save(widget):
    """Test set_current_results enables save button"""
    results = [
        ModelResult("T1", "phase_0", "LR", 0.8, 0.78, 0.82, 0.76, 0.79, 0.77, 1.0, 0.5, 100),
    ]
    widget.set_current_results(results)
    assert widget.save_current_btn.isEnabled() is True


def test_set_empty_results_disables_save(widget):
    """Test empty results disables save button"""
    widget.set_current_results([])
    assert widget.save_current_btn.isEnabled() is False
