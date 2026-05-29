"""Registry Viewer Widget: view and save champion models per phase/target."""

from datetime import datetime
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QFileDialog,
    QGroupBox, QMessageBox,
)
from PyQt6.QtCore import Qt

from app.core.logger_manager import LoggerManager
from app.core.repo_paths import repo_root
from app.core.model_registry import (
    load_registry,
    save_registry,
    champions_from_results,
    merge_registry,
)
from app.pipeline.types import ModelResult


def _default_registry_path() -> str:
    """Default registry path: repo root models/registry.json."""
    return str((repo_root() / "models" / "registry.json").resolve())


class RegistryViewerWidget(QWidget):
    """Widget to view and save model registry (champion per phase/target)."""

    def __init__(self, logger: LoggerManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = logger
        self._registry: dict = {}
        self._current_results: Optional[List[ModelResult]] = None
        self._registry_path = _default_registry_path()
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Path and file actions
        path_group = QGroupBox("Registry file")
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Path:"))
        self.path_edit = QLineEdit()
        self.path_edit.setText(self._registry_path)
        self.path_edit.setPlaceholderText("models/registry.json")
        path_layout.addWidget(self.path_edit)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse)
        path_layout.addWidget(browse_btn)
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self._on_load)
        path_layout.addWidget(load_btn)
        path_help_btn = QPushButton("?")
        path_help_btn.setFixedSize(22, 22)
        path_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        path_help_btn.setToolTip("Click for explanation")
        path_help_btn.clicked.connect(self._show_path_help)
        path_layout.addWidget(path_help_btn)
        path_layout.addStretch()
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        # Table
        table_group = QGroupBox("Champions (phase × target)")
        table_layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Phase", "Target", "Champion model", "Metric", "Value", "Updated"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_header = QHBoxLayout()
        table_header.addStretch()
        table_help_btn = QPushButton("?")
        table_help_btn.setFixedSize(22, 22)
        table_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        table_help_btn.setToolTip("Click for explanation")
        table_help_btn.clicked.connect(self._show_champions_help)
        table_header.addWidget(table_help_btn)
        table_layout.addLayout(table_header)
        table_layout.addWidget(self.table)
        self.status_label = QLabel("Load a registry file or save results from Pipeline Flow.")
        self.status_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        table_layout.addWidget(self.status_label)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # Save current results
        save_group = QGroupBox("Update registry from training")
        save_layout = QHBoxLayout()
        self.save_current_btn = QPushButton("Save current training results to registry")
        self.save_current_btn.setToolTip("Use last Model Training or Run all phases results as champions")
        self.save_current_btn.clicked.connect(self._on_save_current)
        self.save_current_btn.setEnabled(False)
        save_layout.addWidget(self.save_current_btn)
        save_help_btn = QPushButton("?")
        save_help_btn.setFixedSize(22, 22)
        save_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        save_help_btn.setToolTip("Click for explanation")
        save_help_btn.clicked.connect(self._show_save_help)
        save_layout.addWidget(save_help_btn)
        save_layout.addStretch()
        save_group.setLayout(save_layout)
        layout.addWidget(save_group)

    def _show_path_help(self) -> None:
        QMessageBox.information(
            self, "Registry file",
            "Path to the model registry JSON file (e.g. models/registry.json). Use Browse to choose a file, "
            "then Load to display the current champions table. The registry stores the best model per phase×target."
        )

    def _show_champions_help(self) -> None:
        QMessageBox.information(
            self, "Champions (phase × target)",
            "Each row is one phase×target combination (e.g. phase_15 × D30_response). Champion model is the "
            "best-performing model for that cell; Metric and Value show the criterion (e.g. balanced_accuracy) and "
            "its value. Updated is the last save time. Load a registry file to view; use 'Save current training results' "
            "to update the registry from the last Model Training or Run all phases run."
        )

    def _show_save_help(self) -> None:
        QMessageBox.information(
            self, "Update registry from training",
            "Saves the best model per phase×target from the most recent Model Training or Run all phases run "
            "into the registry file. This overwrites existing champions for those cells. Use after you have run "
            "training and want to promote the new results as the current champions."
        )

    def _on_browse(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Registry file", self.path_edit.text(),
            "JSON (*.json);;All files (*.*)"
        )
        if path:
            self.path_edit.setText(path)
            self._registry_path = path

    def _on_load(self) -> None:
        path = self.path_edit.text().strip()
        if not path:
            self.status_label.setText("Enter a path first.")
            return
        self._registry = load_registry(path)
        self._registry_path = path
        self._fill_table()
        self.status_label.setText(f"Loaded {self._count_entries()} champion(s) from {path}")

    def _count_entries(self) -> int:
        n = 0
        for phase_data in self._registry.values():
            if isinstance(phase_data, dict):
                n += len(phase_data)
        return n

    def _fill_table(self) -> None:
        rows = []
        for phase, targets in sorted(self._registry.items()):
            if not isinstance(targets, dict):
                continue
            for target, entry in sorted(targets.items()):
                if not isinstance(entry, dict):
                    continue
                rows.append((
                    phase,
                    target,
                    entry.get("model_family", ""),
                    entry.get("metric", "balanced_accuracy"),
                    entry.get("value", ""),
                    entry.get("timestamp", ""),
                ))
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))

    def _on_save_current(self) -> None:
        if not self._current_results:
            self.status_label.setText("No training results to save. Run model training first.")
            return
        path = self.path_edit.text().strip()
        if not path:
            self.status_label.setText("Enter a registry path first.")
            return
        # Build path with current datetime in filename (e.g. registry_2026-02-26_16-30-45.json)
        p = Path(path)
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        stem = p.stem or "registry"
        ext = p.suffix if p.suffix else ".json"
        save_path = str((p.parent / f"{stem}_{ts}{ext}").resolve())
        new_champions = champions_from_results(self._current_results, metric="balanced_accuracy")
        self._registry = merge_registry(self._registry, new_champions, only_if_better=False)
        try:
            save_registry(save_path, self._registry)
            self._registry_path = save_path
            self._fill_table()
            self.status_label.setText(f"Saved {self._count_entries()} champion(s) to {save_path}")
            self.logger.info(f"Registry saved to {save_path}", "RegistryViewer")
        except OSError as e:
            self.status_label.setText(f"Save failed: {e}")
            QMessageBox.warning(self, "Save failed", str(e))

    def set_current_results(self, results: List[ModelResult]) -> None:
        """Called when training completes; enables Save current button."""
        self._current_results = results
        self.save_current_btn.setEnabled(bool(results))
        if results:
            self.status_label.setText(f"Ready: {len(results)} model result(s). Click Save to update registry.")
