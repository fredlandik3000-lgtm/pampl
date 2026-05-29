"""Feature Analysis Widget for visualizing feature statistics and importance"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QTextEdit, QGroupBox, QComboBox, QSpinBox, QMessageBox,
)
from PyQt6.QtCore import Qt
from typing import Optional
import pandas as pd
import numpy as np

from app.core.logger_manager import LoggerManager


class FeatureAnalysisWidget(QWidget):
    """Widget for analyzing features from engineered data"""
    
    def __init__(
        self,
        logger: LoggerManager,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self.logger = logger
        self.data: Optional[pd.DataFrame] = None
        self.engineered_metadata: dict = {}
        self._model_importance: list = []  # list of (label, [(feat, value), ...])
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Control panel
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # Tab widget for different analyses
        self.analysis_tabs = QTabWidget()
        
        # Feature Summary tab
        self.summary_view = self._create_summary_view()
        self.analysis_tabs.addTab(self.summary_view, "Feature Summary")
        
        # Feature Statistics tab
        self.stats_view = self._create_stats_view()
        self.analysis_tabs.addTab(self.stats_view, "Statistics")
        
        # Missing Values tab
        self.missing_view = self._create_missing_view()
        self.analysis_tabs.addTab(self.missing_view, "Missing Values")
        
        # Correlations tab (placeholder for now)
        self.corr_view = self._create_correlation_view()
        self.analysis_tabs.addTab(self.corr_view, "Correlations")

        # Feature Importance tab (Phase 6 placeholder)
        self.importance_view = self._create_importance_view()
        self.analysis_tabs.addTab(self.importance_view, "Feature Importance")

        layout.addWidget(self.analysis_tabs)
    
    def _create_control_panel(self) -> QGroupBox:
        """Create control panel"""
        group = QGroupBox("Feature Analysis Controls")
        layout = QHBoxLayout()
        
        # Status label
        self.status_label = QLabel("No features loaded - Run feature engineering to analyze")
        self.status_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh Analysis")
        self.refresh_btn.clicked.connect(self._refresh_all_views)
        self.refresh_btn.setEnabled(False)
        layout.addWidget(self.refresh_btn)
        fa_help_btn = QPushButton("?")
        fa_help_btn.setFixedSize(22, 22)
        fa_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        fa_help_btn.setToolTip("Click for explanation")
        fa_help_btn.clicked.connect(self._show_controls_help)
        layout.addWidget(fa_help_btn)
        
        group.setLayout(layout)
        return group
    
    def _create_summary_view(self) -> QWidget:
        """Create feature summary view"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        summary_header = QHBoxLayout()
        self.summary_info_label = QLabel("Feature engineering summary will appear here")
        summary_header.addWidget(self.summary_info_label)
        summary_help_btn = QPushButton("?")
        summary_help_btn.setFixedSize(22, 22)
        summary_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        summary_help_btn.setToolTip("Click for explanation")
        summary_help_btn.clicked.connect(self._show_summary_help)
        summary_header.addWidget(summary_help_btn)
        summary_header.addStretch()
        layout.addLayout(summary_header)
        # Summary text
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        layout.addWidget(self.summary_text)
        
        return widget
    
    def _create_stats_view(self) -> QWidget:
        """Create statistics view"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        stats_header = QHBoxLayout()
        self.stats_info_label = QLabel("Feature statistics")
        stats_header.addWidget(self.stats_info_label)
        stats_help_btn = QPushButton("?")
        stats_help_btn.setFixedSize(22, 22)
        stats_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        stats_help_btn.setToolTip("Click for explanation")
        stats_help_btn.clicked.connect(self._show_stats_help)
        stats_header.addWidget(stats_help_btn)
        stats_header.addStretch()
        layout.addLayout(stats_header)
        # Stats table
        self.stats_table = QTableWidget()
        self.stats_table.setAlternatingRowColors(True)
        layout.addWidget(self.stats_table)
        
        return widget
    
    def _create_missing_view(self) -> QWidget:
        """Create missing values view"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        missing_header = QHBoxLayout()
        self.missing_info_label = QLabel("Missing value analysis")
        missing_header.addWidget(self.missing_info_label)
        missing_help_btn = QPushButton("?")
        missing_help_btn.setFixedSize(22, 22)
        missing_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        missing_help_btn.setToolTip("Click for explanation")
        missing_help_btn.clicked.connect(self._show_missing_help)
        missing_header.addWidget(missing_help_btn)
        missing_header.addStretch()
        layout.addLayout(missing_header)
        # Missing table
        self.missing_table = QTableWidget()
        self.missing_table.setAlternatingRowColors(True)
        layout.addWidget(self.missing_table)
        
        return widget
    
    def _create_correlation_view(self) -> QWidget:
        """Create correlation view: table of feature pairs and correlation."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        group = QGroupBox("Feature correlations (numeric features)")
        group_layout = QVBoxLayout()
        corr_header = QHBoxLayout()
        self.corr_info_label = QLabel("Top pairwise correlations (by absolute value)")
        corr_header.addWidget(self.corr_info_label)
        corr_help_btn = QPushButton("?")
        corr_help_btn.setFixedSize(22, 22)
        corr_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        corr_help_btn.setToolTip("Click for explanation")
        corr_help_btn.clicked.connect(self._show_corr_help)
        corr_header.addWidget(corr_help_btn)
        corr_header.addStretch()
        group_layout.addLayout(corr_header)
        self.corr_table = QTableWidget()
        self.corr_table.setAlternatingRowColors(True)
        self.corr_table.setHorizontalHeaderLabels(["Feature A", "Feature B", "Correlation"])
        group_layout.addWidget(self.corr_table)
        group.setLayout(group_layout)
        layout.addWidget(group)
        return widget

    def _create_importance_view(self) -> QWidget:
        """Create feature importance view: variability (std) and optional model importance."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        group = QGroupBox("Feature importance")
        group_layout = QVBoxLayout()
        imp_header = QHBoxLayout()
        self.importance_info_label = QLabel(
            "Variability (std) of numeric features — higher values may have more discriminative power. "
            "Model-based importance (e.g. from tree/NN) appears after model training."
        )
        self.importance_info_label.setWordWrap(True)
        imp_header.addWidget(self.importance_info_label)
        imp_help_btn = QPushButton("?")
        imp_help_btn.setFixedSize(22, 22)
        imp_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        imp_help_btn.setToolTip("Click for explanation")
        imp_help_btn.clicked.connect(self._show_importance_help)
        imp_header.addWidget(imp_help_btn)
        imp_header.addStretch()
        group_layout.addLayout(imp_header)
        self.importance_table = QTableWidget()
        self.importance_table.setAlternatingRowColors(True)
        self.importance_table.setHorizontalHeaderLabels(["Feature", "Std", "Variance", "Range", "IQR"])
        group_layout.addWidget(self.importance_table)
        # Model-based importance (filled after training)
        self.importance_model_combo = QComboBox()
        self.importance_model_combo.setMinimumWidth(200)
        self.importance_model_combo.currentIndexChanged.connect(self._refresh_importance_view)
        model_imp_label = QLabel("Model importance (after training):")
        group_layout.addWidget(model_imp_label)
        group_layout.addWidget(self.importance_model_combo)
        self.importance_model_table = QTableWidget()
        self.importance_model_table.setAlternatingRowColors(True)
        self.importance_model_table.setHorizontalHeaderLabels(["Feature", "Importance"])
        group_layout.addWidget(self.importance_model_table)
        group.setLayout(group_layout)
        layout.addWidget(group)
        return widget
    
    def set_model_importance(self, metadata: dict):
        """Store model-based feature importance from training metadata for the Importance tab."""
        raw = metadata.get("feature_importances", [])
        self._model_importance = []
        for entry in raw:
            if len(entry) == 4:
                phase, target, model_family, pairs = entry
                label = f"{phase} | {target} | {model_family}"
                self._model_importance.append((label, list(pairs)))
        self._refresh_importance_view()

    def load_engineered_features(self, data: pd.DataFrame, metadata: dict):
        """
        Load engineered features for analysis.
        
        Args:
            data: DataFrame with engineered features
            metadata: Engineering metadata (phase, feature_count, etc.)
        """
        self.data = data
        self.engineered_metadata = metadata
        
        phase = metadata.get('phase', 'unknown')
        feature_count = metadata.get('feature_count', 0)
        
        self.logger.info(f"Loaded {feature_count} features for analysis (phase: {phase})", "FeatureAnalysis")
        
        self.status_label.setText(f"Analyzing {feature_count} features from {phase}")
        self.status_label.setStyleSheet("QLabel { color: #2E7D32; }")
        self.refresh_btn.setEnabled(True)
        
        # Refresh all views
        self._refresh_all_views()

    def _show_controls_help(self):
        QMessageBox.information(
            self, "Feature Analysis Controls",
            "Run feature engineering in the Pipeline Flow tab first; then use Refresh Analysis to load the "
            "engineered features here. All tabs (Summary, Statistics, Missing, Correlations, Importance) then "
            "show analysis for that phase's feature set."
        )

    def _show_summary_help(self):
        QMessageBox.information(
            self, "Feature Summary",
            "Overview of the engineered feature set: phase, feature count, and list of feature names. "
            "Use this to confirm which columns are passed to model training."
        )

    def _show_stats_help(self):
        QMessageBox.information(
            self, "Feature statistics",
            "Per-feature statistics (count, mean, std, min, max) for the engineered numeric features. "
            "Helps spot scaling needs and outliers before training."
        )

    def _show_missing_help(self):
        QMessageBox.information(
            self, "Missing values",
            "Missing value counts and percentages per feature after engineering. "
            "Features with high missingness may be excluded or imputed in the pipeline."
        )

    def _show_corr_help(self):
        QMessageBox.information(
            self, "Feature correlations",
            "Pairwise Pearson correlations between numeric features (top by absolute value). "
            "High correlation may indicate redundancy; useful for feature selection."
        )

    def _show_importance_help(self):
        QMessageBox.information(
            self, "Feature importance",
            "Variability (standard deviation): higher std often means more discriminative potential. "
            "Model-based importance (from tree or NN) appears here after model training has been run."
        )
    
    def _refresh_all_views(self):
        """Refresh all analysis views"""
        if self.data is None:
            return

        self._refresh_summary_view()
        self._refresh_stats_view()
        self._refresh_missing_view()
        self._refresh_correlation_view()
        self._refresh_importance_view()
    
    def _refresh_summary_view(self):
        """Refresh feature summary view"""
        if self.data is None:
            return
        
        summary = "FEATURE ENGINEERING SUMMARY\n"
        summary += "=" * 60 + "\n\n"
        
        # Basic info
        summary += f"Phase: {self.engineered_metadata.get('phase', 'unknown')}\n"
        summary += f"Total Features: {self.engineered_metadata.get('feature_count', 0)}\n"
        summary += f"Samples: {len(self.data):,}\n\n"
        
        # Feature types
        selected_features = self.engineered_metadata.get('selected_features', [])
        if selected_features:
            categorical_count = sum(1 for col in selected_features if col in self.data.columns and self.data[col].dtype == 'object')
            numeric_count = sum(1 for col in selected_features if col in self.data.columns and self.data[col].dtype != 'object')
            
            summary += "Feature Types:\n"
            summary += f"  - Categorical: {categorical_count}\n"
            summary += f"  - Numeric: {numeric_count}\n\n"
        
        # Engineering time
        eng_time = self.engineered_metadata.get('engineering_time_sec', 0)
        summary += f"Engineering Time: {eng_time:.3f}s\n\n"
        
        # Selected features list
        if selected_features:
            summary += "Selected Features:\n"
            summary += "-" * 60 + "\n"
            for i, feature in enumerate(selected_features, 1):
                feature_type = "categorical" if feature in self.data.columns and self.data[feature].dtype == 'object' else "numeric"
                summary += f"{i:2d}. {feature:30s} [{feature_type}]\n"
        
        self.summary_text.setPlainText(summary)
    
    def _refresh_stats_view(self):
        """Refresh statistics view"""
        if self.data is None:
            return
        
        selected_features = self.engineered_metadata.get('selected_features', [])
        if not selected_features:
            return
        
        # Get numeric features
        numeric_features = [col for col in selected_features if col in self.data.columns and self.data[col].dtype != 'object']
        
        if not numeric_features:
            self.stats_table.setRowCount(0)
            self.stats_info_label.setText("No numeric features available")
            return
        
        self.stats_info_label.setText(f"Statistics for {len(numeric_features)} numeric features")
        
        # Create table
        self.stats_table.setRowCount(len(numeric_features))
        self.stats_table.setColumnCount(7)
        self.stats_table.setHorizontalHeaderLabels([
            "Feature", "Mean", "Std", "Min", "25%", "Median", "Max"
        ])
        
        for i, feature in enumerate(numeric_features):
            if feature not in self.data.columns:
                continue
            
            col_data = self.data[feature].dropna()
            
            # Feature name
            self.stats_table.setItem(i, 0, QTableWidgetItem(feature))
            
            if len(col_data) > 0:
                # Statistics
                self.stats_table.setItem(i, 1, QTableWidgetItem(f"{col_data.mean():.3f}"))
                self.stats_table.setItem(i, 2, QTableWidgetItem(f"{col_data.std():.3f}"))
                self.stats_table.setItem(i, 3, QTableWidgetItem(f"{col_data.min():.3f}"))
                self.stats_table.setItem(i, 4, QTableWidgetItem(f"{col_data.quantile(0.25):.3f}"))
                self.stats_table.setItem(i, 5, QTableWidgetItem(f"{col_data.median():.3f}"))
                self.stats_table.setItem(i, 6, QTableWidgetItem(f"{col_data.max():.3f}"))
            else:
                for j in range(1, 7):
                    self.stats_table.setItem(i, j, QTableWidgetItem("N/A"))
        
        # Resize columns
        self.stats_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 7):
            self.stats_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
    
    def _refresh_missing_view(self):
        """Refresh missing values view"""
        if self.data is None:
            return
        
        selected_features = self.engineered_metadata.get('selected_features', [])
        if not selected_features:
            return
        
        # Calculate missing values
        missing_data = []
        for feature in selected_features:
            if feature not in self.data.columns:
                continue
            
            missing_count = self.data[feature].isna().sum()
            missing_pct = (missing_count / len(self.data)) * 100
            
            if missing_count > 0:  # Only show features with missing values
                missing_data.append({
                    'feature': feature,
                    'missing_count': missing_count,
                    'missing_pct': missing_pct,
                    'available': len(self.data) - missing_count
                })
        
        # Sort by missing percentage
        missing_data.sort(key=lambda x: x['missing_pct'], reverse=True)
        
        if not missing_data:
            self.missing_table.setRowCount(0)
            self.missing_info_label.setText("No missing values in engineered features")
            return
        
        self.missing_info_label.setText(f"{len(missing_data)} features have missing values")
        
        # Create table
        self.missing_table.setRowCount(len(missing_data))
        self.missing_table.setColumnCount(4)
        self.missing_table.setHorizontalHeaderLabels([
            "Feature", "Missing Count", "Missing %", "Available"
        ])
        
        for i, item in enumerate(missing_data):
            self.missing_table.setItem(i, 0, QTableWidgetItem(item['feature']))
            self.missing_table.setItem(i, 1, QTableWidgetItem(f"{item['missing_count']:,}"))
            self.missing_table.setItem(i, 2, QTableWidgetItem(f"{item['missing_pct']:.2f}%"))
            self.missing_table.setItem(i, 3, QTableWidgetItem(f"{item['available']:,}"))
        
        # Resize columns
        self.missing_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 4):
            self.missing_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

    def _refresh_correlation_view(self):
        """Compute and display top pairwise correlations for numeric features."""
        if self.data is None:
            return

        selected_features = self.engineered_metadata.get("selected_features", [])
        numeric_features = [
            c for c in selected_features
            if c in self.data.columns and self.data[c].dtype != "object"
        ]
        if len(numeric_features) < 2:
            self.corr_info_label.setText("Need at least 2 numeric features for correlations.")
            self.corr_table.setRowCount(0)
            return

        try:
            corr_df = self.data[numeric_features].corr()
        except Exception:
            self.corr_info_label.setText("Could not compute correlations.")
            self.corr_table.setRowCount(0)
            return

        # Collect upper triangle (excluding diagonal), sort by abs(correlation)
        pairs = []
        for i in range(len(numeric_features)):
            for j in range(i + 1, len(numeric_features)):
                a, b = numeric_features[i], numeric_features[j]
                r = corr_df.loc[a, b]
                if pd.notna(r):
                    pairs.append((a, b, float(r)))
        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        top_n = min(150, len(pairs))

        self.corr_info_label.setText(
            f"Top {top_n} pairwise correlations (of {len(pairs)} pairs, {len(numeric_features)} numeric features)"
        )
        self.corr_table.setRowCount(top_n)
        self.corr_table.setColumnCount(3)
        self.corr_table.setHorizontalHeaderLabels(["Feature A", "Feature B", "Correlation"])
        for i, (a, b, r) in enumerate(pairs[:top_n]):
            self.corr_table.setItem(i, 0, QTableWidgetItem(a))
            self.corr_table.setItem(i, 1, QTableWidgetItem(b))
            self.corr_table.setItem(i, 2, QTableWidgetItem(f"{r:.4f}"))
        self.corr_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.corr_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.corr_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

    def _refresh_importance_view(self):
        """Display variability (std, variance, range, IQR) and model-based importance when available."""
        # Variability table: require engineered data
        if self.data is not None:
            selected_features = self.engineered_metadata.get("selected_features", [])
            # Use all numeric columns so we show full data; fallback when selected_features missing
            numeric_features = [
                c for c in (selected_features if selected_features else self.data.columns)
                if c in self.data.columns and self.data[c].dtype != "object"
            ]
        else:
            numeric_features = []
        if not numeric_features:
            self.importance_table.setRowCount(0)
        else:
            rows = []
            for c in numeric_features:
                s = self.data[c].dropna()
                if len(s) > 0:
                    std_val = s.std()
                    var_val = s.var()
                    range_val = float(s.max() - s.min())
                    q1, q3 = s.quantile(0.25), s.quantile(0.75)
                    iqr_val = float(q3 - q1)
                    rows.append((c, std_val, var_val, range_val, iqr_val))
                else:
                    rows.append((c, np.nan, np.nan, np.nan, np.nan))
            # Sort by IQR (or range) so most variable features are first; avoids "all same" when std is normalized
            rows.sort(key=lambda x: (x[4] if pd.notna(x[4]) else -1), reverse=True)

            self.importance_table.setRowCount(len(rows))
            self.importance_table.setColumnCount(5)
            self.importance_table.setHorizontalHeaderLabels(["Feature", "Std", "Variance", "Range", "IQR"])
            for i, (feat, std_val, var_val, range_val, iqr_val) in enumerate(rows):
                self.importance_table.setItem(i, 0, QTableWidgetItem(feat))
                self.importance_table.setItem(
                    i, 1, QTableWidgetItem(f"{std_val:.4f}" if pd.notna(std_val) else "N/A")
                )
                self.importance_table.setItem(
                    i, 2, QTableWidgetItem(f"{var_val:.4f}" if pd.notna(var_val) else "N/A")
                )
                self.importance_table.setItem(
                    i, 3, QTableWidgetItem(f"{range_val:.4f}" if pd.notna(range_val) else "N/A")
                )
                self.importance_table.setItem(
                    i, 4, QTableWidgetItem(f"{iqr_val:.4f}" if pd.notna(iqr_val) else "N/A")
                )
            self.importance_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            for j in range(1, 5):
                self.importance_table.horizontalHeader().setSectionResizeMode(j, QHeaderView.ResizeMode.ResizeToContents)

        # Model-based importance (from training)
        self.importance_model_combo.blockSignals(True)
        self.importance_model_combo.clear()
        self.importance_model_combo.addItem("— Select model —", None)
        for label, pairs in self._model_importance:
            self.importance_model_combo.addItem(label, (label, pairs))
        self.importance_model_combo.blockSignals(False)

        sel = self.importance_model_combo.currentData()
        if sel and isinstance(sel, tuple):
            _label, pairs = sel
            pairs = sorted(pairs, key=lambda x: (x[1] if len(x) == 2 else 0), reverse=True)
            self.importance_model_table.setRowCount(len(pairs))
            self.importance_model_table.setColumnCount(2)
            self.importance_model_table.setHorizontalHeaderLabels(["Feature", "Importance"])
            for i, (feat, val) in enumerate(pairs):
                self.importance_model_table.setItem(i, 0, QTableWidgetItem(str(feat)))
                self.importance_model_table.setItem(i, 1, QTableWidgetItem(f"{float(val):.4f}"))
            self.importance_model_table.setVisible(True)
            self.importance_model_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            self.importance_model_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        else:
            self.importance_model_table.setRowCount(0)
            self.importance_model_table.setVisible(bool(self._model_importance))
