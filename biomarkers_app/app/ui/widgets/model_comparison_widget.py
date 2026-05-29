"""Model Comparison Widget for displaying model performance metrics"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QComboBox, QCheckBox, QTextEdit, QFileDialog, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QFont
from typing import Optional, List, Dict
import csv

from app.core.logger_manager import LoggerManager
from app.pipeline.types import ModelResult, PRIMARY_TARGETS
from app.ui.widgets.model_comparison_constants import (
    PHASES, MODEL_FAMILIES, METRICS, MODEL_DISPLAY_NAMES,
    PERFORMANCE_EXCELLENT, PERFORMANCE_GOOD, PERFORMANCE_FAIR,
    COLOR_EXCELLENT, COLOR_GOOD, COLOR_FAIR, COLOR_POOR
)
from app.ui.widgets.model_comparison_mock_data import generate_mock_results


class ModelComparisonWidget(QWidget):
    """Widget for comparing model performance across phases and targets"""
    
    def __init__(
        self,
        logger: LoggerManager,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self.logger = logger
        self.results: List[ModelResult] = []
        self.filtered_results: List[ModelResult] = []
        
        # Available options
        self.phases = PHASES
        self.model_families = MODEL_FAMILIES
        self.metrics = METRICS
        self.targets = []  # Will be populated from results
        
        self._init_ui()
        self._load_mock_data()  # Load placeholder data for now

    def _model_display_name(self, model_family: str) -> str:
        """Return display name for model (e.g. 'Baseline-Majority (Dominant class)')."""
        return MODEL_DISPLAY_NAMES.get(model_family, model_family)
    
    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Filter panel
        filter_panel = self._create_filter_panel()
        layout.addWidget(filter_panel)
        
        # Comparison table
        table_group = QGroupBox("Model Comparison")
        table_layout = QVBoxLayout()
        table_header = QHBoxLayout()
        table_header.addStretch()
        table_help_btn = QPushButton("?")
        table_help_btn.setFixedSize(22, 22)
        table_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        table_help_btn.setToolTip("Click for explanation")
        table_help_btn.clicked.connect(self._show_table_help)
        table_header.addWidget(table_help_btn)
        table_layout.addLayout(table_header)
        self.comparison_table = QTableWidget()
        self.comparison_table.setAlternatingRowColors(True)
        self.comparison_table.itemSelectionChanged.connect(self._on_cell_selected)
        # Fixed viewport size so table scrolls vertically and horizontally
        self.comparison_table.setMinimumHeight(500)
        self.comparison_table.verticalHeader().setDefaultSectionSize(28)
        self.comparison_table.verticalHeader().setMinimumSectionSize(24)
        # Smaller font for cells and for headers so row/column names fit
        cell_font = QFont()
        cell_font.setPointSize(8)
        self.comparison_table.setFont(cell_font)
        header_font = QFont()
        header_font.setPointSize(7)
        self.comparison_table.horizontalHeader().setFont(header_font)
        self.comparison_table.verticalHeader().setFont(header_font)
        self.comparison_table.verticalHeader().setMinimumWidth(105)

        table_layout.addWidget(self.comparison_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group, stretch=3)
        
        # Color legend
        legend = self._create_legend()
        layout.addWidget(legend)
        
        # Details panel
        details_group = QGroupBox("Selected Cell Details")
        details_layout = QVBoxLayout()
        details_header = QHBoxLayout()
        details_header.addStretch()
        details_help_btn = QPushButton("?")
        details_help_btn.setFixedSize(22, 22)
        details_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        details_help_btn.setToolTip("Click for explanation")
        details_help_btn.clicked.connect(self._show_details_help)
        details_header.addWidget(details_help_btn)
        details_layout.addLayout(details_header)
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(120)
        self.details_text.setFontFamily("Consolas")
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group, stretch=1)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("Export Table")
        self.export_btn.clicked.connect(self._export_table)
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_table)
        button_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(button_layout)
    
    def _create_filter_panel(self) -> QGroupBox:
        """Create filter controls"""
        group = QGroupBox("Filters")
        layout = QHBoxLayout()
        
        # Phase filter
        layout.addWidget(QLabel("Phase:"))
        self.phase_combo = QComboBox()
        self.phase_combo.addItem("All")
        self.phase_combo.addItems(self.phases)
        self.phase_combo.currentTextChanged.connect(self._apply_filters)
        layout.addWidget(self.phase_combo)
        
        # Target filter
        layout.addWidget(QLabel("Target:"))
        self.target_combo = QComboBox()
        self.target_combo.addItem("All")
        self.target_combo.currentTextChanged.connect(self._apply_filters)
        layout.addWidget(self.target_combo)
        
        # Model filter
        layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItem("All")
        self.model_combo.addItem("All Models (no baselines)")
        self.model_combo.addItems(self.model_families)
        self.model_combo.currentTextChanged.connect(self._apply_filters)
        layout.addWidget(self.model_combo)
        
        # Metric selector with hint
        layout.addWidget(QLabel("Metric:"))
        self.metric_combo = QComboBox()
        self.metric_combo.addItems(self.metrics)
        self.metric_combo.currentTextChanged.connect(self._refresh_table)
        layout.addWidget(self.metric_combo)
        filters_help_btn = QPushButton("?")
        filters_help_btn.setFixedSize(22, 22)
        filters_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        filters_help_btn.setToolTip("Metrics, baselines & filters")
        filters_help_btn.clicked.connect(self._show_filters_and_metrics_help)
        layout.addWidget(filters_help_btn)

        layout.addStretch()
        
        # Display options
        layout.addWidget(QLabel("Display:"))
        self.display_mode_combo = QComboBox()
        self.display_mode_combo.addItem("All models")
        self.display_mode_combo.addItem("Best only (champion per cell)")
        self.display_mode_combo.currentTextChanged.connect(self._refresh_table)
        layout.addWidget(self.display_mode_combo)

        self.show_best_checkbox = QCheckBox("Highlight best per target")
        self.show_best_checkbox.setChecked(True)
        self.show_best_checkbox.stateChanged.connect(self._refresh_table)
        layout.addWidget(self.show_best_checkbox)

        self.color_code_checkbox = QCheckBox("Color code")
        self.color_code_checkbox.setChecked(True)
        self.color_code_checkbox.stateChanged.connect(self._refresh_table)
        layout.addWidget(self.color_code_checkbox)

        group.setLayout(layout)
        return group
    
    def _create_legend(self) -> QWidget:
        """Create color legend"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 5)
        
        layout.addWidget(QLabel("Color Gradient:"))
        
        # Show gradient anchors
        red_label = QLabel("0.40 (Red)")
        red_label.setStyleSheet("background-color: #e67c73; padding: 2px 8px; border-radius: 3px;")
        layout.addWidget(red_label)
        
        layout.addWidget(QLabel("→"))
        
        yellow_label = QLabel("0.65 (Yellow)")
        yellow_label.setStyleSheet("background-color: #ffd666; padding: 2px 8px; border-radius: 3px;")
        layout.addWidget(yellow_label)
        
        layout.addWidget(QLabel("→"))
        
        green_label = QLabel("0.90 (Green)")
        green_label.setStyleSheet("background-color: #57bb8a; padding: 2px 8px; border-radius: 3px;")
        layout.addWidget(green_label)
        
        layout.addWidget(QLabel("  |  "))
        
        # Champion marker
        champion_label = QLabel("* = Best model for target in phase")
        layout.addWidget(champion_label)
        
        layout.addStretch()
        
        return widget
    
    def _load_mock_data(self):
        """Load placeholder data for testing UI"""
        self.logger.info("Loading mock model comparison data", "ModelComparison")
        
        # Generate mock results
        self.results, self.targets = generate_mock_results()
        
        # Populate target combo
        self.target_combo.addItems(self.targets)
        
        self.logger.info(f"Loaded {len(self.results)} mock model results", "ModelComparison")
        self._apply_filters()
    
    def _show_filters_and_metrics_help(self):
        """Show metrics, baselines, and filters in one dialog."""
        msg = (
            "Metrics\n"
            "• Balanced Accuracy: (sensitivity + specificity)/2; use for imbalanced classes.\n"
            "• Accuracy: fraction correct; can be inflated by class imbalance.\n"
            "• AUC: area under ROC; 0.5 = random, 1.0 = perfect. Threshold-free.\n"
            "• F1: harmonic mean of precision and recall.\n\n"
            "Using ROC with accuracy / balanced accuracy\n"
            "AUC measures ranking (all thresholds); accuracy and balanced accuracy use a single threshold (e.g. 0.5). "
            "Compare all three: good AUC with low BA suggests the threshold is wrong; similar BA and accuracy suggest balanced classes. "
            "Report AUC for discrimination, BA for a chosen operating point.\n\n"
            "Baselines\n"
            "• Random (Baseline-Random): predicts by chance (AUC ≈ 0.5, BA ≈ 0.5). Your model should beat this.\n"
            "• Dominance (Baseline-Majority): always predicts the majority class. Compare your model’s BA to Majority_BA; "
            "use 'All Models (no baselines)' in Model filter to hide baselines when comparing only trained models.\n\n"
            "Filters\n"
            "Phase, Target, Model narrow the table. Metric chooses the value in each cell. "
            "Display: All models lists every model per cell; Best only shows the champion per phase×target. "
            "5-fold CV: values shown as mean ± std; export includes BA_std, BA_CI_low, BA_CI_high."
        )
        QMessageBox.information(self, "Metrics, baselines & filters", msg)

    def _show_table_help(self):
        """Show explanation of the comparison table."""
        QMessageBox.information(
            self,
            "Model Comparison table",
            "Layout: rows = phases (timepoints), columns = outcome targets. Each cell shows the metric chosen in Filters.\n\n"
            "Display: 'Best only' shows one value per cell (champion model name + value); 'All models' lists every model’s value "
            "for that phase×target. 'Highlight best per target' marks the best cell per column.\n\n"
            "Colors: green = excellent (≥0.85), light green = good (≥0.75), yellow = fair (≥0.65), red = poor. "
            "Turn off with 'Color code' if needed.\n\n"
            "Export: CSV includes phase, target, model, selected metric; when from CV, also Majority_BA, Beat_Majority, "
            "BA_std, BA_CI_low, BA_CI_high. Primary targets are used in exports."
        )

    def _show_details_help(self):
        """Show explanation of selected cell details."""
        QMessageBox.information(
            self,
            "Selected Cell Details",
            "Click a cell to load details for that phase×target (and model if filtered). Shown: model name, sample size, "
            "Accuracy, Balanced Accuracy, AUC, F1, and—when from 5-fold CV—mean ± std and confidence interval. "
            "Use this to compare metrics for one cell or to check whether a model beats the majority baseline (Beat_Majority)."
        )
    
    def _apply_filters(self):
        """Apply selected filters to results"""
        phase_filter = self.phase_combo.currentText()
        target_filter = self.target_combo.currentText()
        model_filter = self.model_combo.currentText()
        
        self.filtered_results = []
        for result in self.results:
            # Check phase filter
            if phase_filter != "All" and result.phase != phase_filter:
                continue
            
            # Check target filter
            if target_filter != "All" and result.target != target_filter:
                continue
            
            # Check model filter (dropdown shows raw names e.g. Baseline-Majority; pipeline uses same or NN, LR, etc.)
            if model_filter == "All Models (no baselines)":
                # Exclude baseline models
                if result.model_family.startswith("Baseline"):
                    continue
            elif model_filter != "All":
                # Match by raw model_family (e.g. Baseline-Majority) or display name (e.g. Neural Network for NN)
                display = self._model_display_name(result.model_family)
                if result.model_family != model_filter and display != model_filter:
                    continue
            
            self.filtered_results.append(result)
        
        self._refresh_table()
    
    def _refresh_table(self):
        """Refresh the comparison table"""
        if not self.filtered_results:
            self.comparison_table.clear()
            self.comparison_table.setRowCount(0)
            self.comparison_table.setColumnCount(0)
            return

        selected_metric = self.metric_combo.currentText().lower().replace(" ", "_")
        show_best_only = self.display_mode_combo.currentText() == "Best only (champion per cell)"

        if show_best_only:
            self._refresh_table_best_only(selected_metric)
        else:
            self._refresh_table_all_models(selected_metric)

        self.comparison_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.comparison_table.horizontalHeader().setDefaultSectionSize(72)
        self.comparison_table.horizontalHeader().setMinimumSectionSize(50)
        self.comparison_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

    def _refresh_table_best_only(self, selected_metric: str):
        """Build table: rows = phases, columns = targets; each cell = best value (model)."""
        targets = sorted(list(set(r.target for r in self.filtered_results)))
        phases = sorted(list(set(r.phase for r in self.filtered_results)))

        self.comparison_table.clear()
        self.comparison_table.setRowCount(len(phases))
        self.comparison_table.setColumnCount(len(targets))
        self.comparison_table.setHorizontalHeaderLabels(targets)
        self.comparison_table.setVerticalHeaderLabels(phases)

        for row_idx, phase in enumerate(phases):
            for col_idx, target in enumerate(targets):
                matching = [
                    r for r in self.filtered_results
                    if r.target == target and r.phase == phase
                ]
                if not matching:
                    item = QTableWidgetItem("—")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.comparison_table.setItem(row_idx, col_idx, item)
                    continue

                best = max(matching, key=lambda r: r.get_metric(selected_metric))
                value = best.get_metric(selected_metric)
                display_str = best.get_metric_display(selected_metric)
                item = QTableWidgetItem(f"{display_str} ({self._model_display_name(best.model_family)})")
                item.setData(Qt.ItemDataRole.UserRole, best)
                item.setToolTip(f"{self._model_display_name(best.model_family)}: {selected_metric}={value:.4f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if self.color_code_checkbox.isChecked():
                    item.setBackground(self._get_performance_color(value))
                    item.setForeground(QColor(0, 0, 0))
                self.comparison_table.setItem(row_idx, col_idx, item)

    def _refresh_table_all_models(self, selected_metric: str):
        """Build table: rows = phase × model, columns = targets (original behavior)."""
        targets = sorted(list(set(r.target for r in self.filtered_results)))
        phases = sorted(list(set(r.phase for r in self.filtered_results)))
        models = sorted(list(set(r.model_family for r in self.filtered_results)))

        self.comparison_table.clear()
        row_headers = []
        for phase in phases:
            for model in models:
                row_headers.append(f"{phase}\n{self._model_display_name(model)}")

        self.comparison_table.setRowCount(len(row_headers))
        self.comparison_table.setColumnCount(len(targets))
        self.comparison_table.setHorizontalHeaderLabels(targets)
        self.comparison_table.setVerticalHeaderLabels(row_headers)

        row_idx = 0
        for phase in phases:
            for model in models:
                for col_idx, target in enumerate(targets):
                    matching = [
                        r for r in self.filtered_results
                        if r.target == target and r.phase == phase and r.model_family == model
                    ]
                    if matching:
                        result = matching[0]
                        value = result.get_metric(selected_metric)
                        item = QTableWidgetItem(result.get_metric_display(selected_metric))
                        item.setData(Qt.ItemDataRole.UserRole, result)
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        if self.color_code_checkbox.isChecked():
                            item.setBackground(self._get_performance_color(value))
                            item.setForeground(QColor(0, 0, 0))
                        self.comparison_table.setItem(row_idx, col_idx, item)
                    else:
                        item = QTableWidgetItem("—")
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.comparison_table.setItem(row_idx, col_idx, item)
                row_idx += 1

        # Mark best (champion) per target within each phase
        if self.show_best_checkbox.isChecked():
            for col_idx, target in enumerate(targets):
                for phase in phases:
                    phase_models = []
                    for r_idx in range(self.comparison_table.rowCount()):
                        header = self.comparison_table.verticalHeaderItem(r_idx).text()
                        if header.startswith(phase):
                            cell = self.comparison_table.item(r_idx, col_idx)
                            if cell and cell.text() != "—":
                                result_obj = cell.data(Qt.ItemDataRole.UserRole)
                                if result_obj is not None and hasattr(result_obj, "get_metric"):
                                    value = result_obj.get_metric(selected_metric)
                                    phase_models.append((value, r_idx))
                                else:
                                    try:
                                        value = float(cell.text().replace(" *", "").split()[0])
                                        phase_models.append((value, r_idx))
                                    except (ValueError, IndexError):
                                        pass
                    if phase_models:
                        best_value, best_row_idx = max(phase_models, key=lambda x: x[0])
                        cell = self.comparison_table.item(best_row_idx, col_idx)
                        if cell:
                            current_text = cell.text().replace(" *", "")
                            cell.setText(f"{current_text} *")
    
    def _get_performance_color(self, value: float) -> QColor:
        """Get color based on performance value using gradient interpolation
        
        Anchors:
        - 0.40: #e67c73 (red)
        - 0.65: #ffd666 (yellow)
        - 0.90: #57bb8a (green)
        """
        # Anchor points: (value, (R, G, B))
        anchor_low = (0.40, (230, 124, 115))    # #e67c73
        anchor_mid = (0.65, (255, 214, 102))    # #ffd666
        anchor_high = (0.90, (87, 187, 138))    # #57bb8a
        
        # Clamp value to reasonable range
        value = max(0.0, min(1.0, value))
        
        # Determine which segment we're in and interpolate
        if value <= anchor_low[0]:
            # Below lowest anchor - use solid red
            return QColor(*anchor_low[1])
        elif value <= anchor_mid[0]:
            # Between low and mid - interpolate red to yellow
            t = (value - anchor_low[0]) / (anchor_mid[0] - anchor_low[0])
            r = int(anchor_low[1][0] + t * (anchor_mid[1][0] - anchor_low[1][0]))
            g = int(anchor_low[1][1] + t * (anchor_mid[1][1] - anchor_low[1][1]))
            b = int(anchor_low[1][2] + t * (anchor_mid[1][2] - anchor_low[1][2]))
            return QColor(r, g, b)
        elif value <= anchor_high[0]:
            # Between mid and high - interpolate yellow to green
            t = (value - anchor_mid[0]) / (anchor_high[0] - anchor_mid[0])
            r = int(anchor_mid[1][0] + t * (anchor_high[1][0] - anchor_mid[1][0]))
            g = int(anchor_mid[1][1] + t * (anchor_high[1][1] - anchor_mid[1][1]))
            b = int(anchor_mid[1][2] + t * (anchor_high[1][2] - anchor_mid[1][2]))
            return QColor(r, g, b)
        else:
            # Above highest anchor - use solid green
            return QColor(*anchor_high[1])
    
    def _on_cell_selected(self):
        """Handle cell selection"""
        selected_items = self.comparison_table.selectedItems()
        if not selected_items:
            self.details_text.clear()
            return
        
        item = selected_items[0]
        result = item.data(Qt.ItemDataRole.UserRole)
        
        if not isinstance(result, ModelResult):
            self.details_text.clear()
            return
        
        # Display detailed metrics
        details = f"Selected Cell: {self._model_display_name(result.model_family)}, {result.target}, {result.phase}\n"
        details += "=" * 70 + "\n\n"
        details += f"Accuracy:          {result.accuracy:.4f}\n"
        details += f"Balanced Accuracy: {result.balanced_accuracy:.4f}\n"
        details += f"AUC:               {result.auc:.4f}\n"
        details += f"F1 Score:          {result.f1_score:.4f}\n"
        details += f"Precision:         {result.precision:.4f}\n"
        details += f"Recall:            {result.recall:.4f}\n"
        details += "\n" + "=" * 70 + "\n\n"
        details += f"Train Time:        {result.train_time:.2f}s\n"
        details += f"Threshold:         {result.threshold:.3f}\n"
        details += f"Sample Size:       {result.sample_size}\n"
        self.details_text.setPlainText(details)
    
    def _export_table(self):
        """Export table to CSV"""
        if not self.filtered_results:
            self.logger.warning("No data to export", "ModelComparison")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Model Comparison",
            "model_comparison.csv",
            "CSV Files (*.csv);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            # Block B2: lookup (target, phase) -> majority BA for Beat_Majority column
            majority_ba_by_key: Dict[tuple, float] = {}
            for r in self.filtered_results:
                if r.model_family == "Baseline-Majority":
                    majority_ba_by_key[(r.target, r.phase)] = r.balanced_accuracy
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                headers = [
                    "Target", "Phase", "Model", "Primary_Target",
                    "Accuracy", "Balanced Accuracy", "BA_std", "BA_CI_low", "BA_CI_high",
                    "AUC", "F1 Score", "Precision", "Recall", "Train Time",
                    "Threshold", "Sample Size",
                    "Majority_BA", "Beat_Majority",
                ]
                writer.writerow(headers)
                for result in self.filtered_results:
                    key = (result.target, result.phase)
                    majority_ba = majority_ba_by_key.get(key, float("nan"))
                    is_primary = result.target in PRIMARY_TARGETS
                    beat_majority = ""
                    if result.model_family not in ("Baseline-Majority", "Baseline-Random") and key in majority_ba_by_key:
                        beat_majority = "Yes" if result.balanced_accuracy > majority_ba else "No"
                    row = [
                        result.target,
                        result.phase,
                        result.model_family,
                        "Yes" if is_primary else "No",
                        f"{result.accuracy:.4f}",
                        f"{result.balanced_accuracy:.4f}",
                        f"{getattr(result, 'balanced_accuracy_std', 0):.4f}",
                        f"{getattr(result, 'balanced_accuracy_ci_low', 0):.4f}",
                        f"{getattr(result, 'balanced_accuracy_ci_high', 0):.4f}",
                        f"{result.auc:.4f}",
                        f"{result.f1_score:.4f}",
                        f"{result.precision:.4f}",
                        f"{result.recall:.4f}",
                        f"{result.train_time:.2f}",
                        f"{result.threshold:.3f}",
                        result.sample_size,
                        f"{majority_ba:.4f}" if key in majority_ba_by_key else "",
                        beat_majority,
                    ]
                    writer.writerow(row)
            
            self.logger.info(f"Exported {len(self.filtered_results)} results to {file_path}", "ModelComparison")
            
        except Exception as e:
            self.logger.error(f"Failed to export table: {str(e)}", "ModelComparison")
    
    def load_results(self, results: List[ModelResult]):
        """Load actual model results (when available)"""
        self.results = results
        
        # Update targets, phases, and models from actual results (supports NN, LR, etc.)
        self.targets = sorted(list(set(r.target for r in results)))
        phases_from_data = sorted(list(set(r.phase for r in results)))
        models_from_data = sorted(list(set(r.model_family for r in results)))
        
        self.target_combo.clear()
        self.target_combo.addItem("All")
        self.target_combo.addItems(self.targets)
        
        self.phase_combo.clear()
        self.phase_combo.addItem("All")
        self.phase_combo.addItems(phases_from_data if phases_from_data else self.phases)
        
        self.model_combo.clear()
        self.model_combo.addItem("All")
        self.model_combo.addItem("All Models (no baselines)")
        self.model_combo.addItems(models_from_data if models_from_data else self.model_families)
        
        self.logger.info(f"Loaded {len(results)} model results", "ModelComparison")
        self._apply_filters()
