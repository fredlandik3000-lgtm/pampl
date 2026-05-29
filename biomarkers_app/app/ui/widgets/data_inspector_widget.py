"""Data Inspector Widget for viewing and exploring loaded data"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QTextEdit, QGroupBox, QComboBox, QSpinBox, QCheckBox,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from typing import Optional
import pandas as pd

from app.core.logger_manager import LoggerManager
from app.ui.widgets.data_inspector_constants import CATEGORICAL_MAPPINGS


class DataInspectorWidget(QWidget):
    """Widget for inspecting loaded data"""
    
    def __init__(
        self,
        logger: LoggerManager,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self.logger = logger
        self.data: Optional[pd.DataFrame] = None
        self.derived_columns: list = []  # Track which columns are derived
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Control panel
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # Tab widget for different views
        self.view_tabs = QTabWidget()
        
        # Data view tab
        self.data_view = self._create_data_view()
        self.view_tabs.addTab(self.data_view, "Data View")
        
        # Column info tab
        self.column_info = self._create_column_info()
        self.view_tabs.addTab(self.column_info, "Column Info")
        
        # Statistics tab
        self.stats_view = self._create_stats_view()
        self.view_tabs.addTab(self.stats_view, "Statistics")
        
        # Missing data tab
        self.missing_view = self._create_missing_view()
        self.view_tabs.addTab(self.missing_view, "Missing Data")
        
        # Derived columns tab (NEW)
        self.derived_view = self._create_derived_view()
        self.view_tabs.addTab(self.derived_view, "Derived Columns")
        
        layout.addWidget(self.view_tabs)
    
    def _create_control_panel(self) -> QGroupBox:
        """Create control panel for data inspection"""
        group = QGroupBox("Data Controls")
        layout = QHBoxLayout()
        
        # Status label
        self.status_label = QLabel("No data loaded - Load data to see processed data (after target derivation)")
        self.status_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Rows to display
        layout.addWidget(QLabel("Rows to display:"))
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(10, 10000)
        self.rows_spin.setValue(10000)  # Show all rows by default
        self.rows_spin.valueChanged.connect(self._on_rows_changed)
        layout.addWidget(self.rows_spin)
        
        # Show all columns checkbox
        self.show_all_cols = QCheckBox("Show all columns")
        self.show_all_cols.setChecked(True)
        self.show_all_cols.stateChanged.connect(self._refresh_data_view)
        layout.addWidget(self.show_all_cols)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_all_views)
        self.refresh_btn.setEnabled(False)
        layout.addWidget(self.refresh_btn)
        controls_help_btn = QPushButton("?")
        controls_help_btn.setFixedSize(22, 22)
        controls_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        controls_help_btn.setToolTip("Click for explanation")
        controls_help_btn.clicked.connect(self._show_controls_help)
        layout.addWidget(controls_help_btn)
        
        group.setLayout(layout)
        return group
    
    def _create_data_view(self) -> QWidget:
        """Create data table view"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Info label and help
        data_header = QHBoxLayout()
        self.data_info_label = QLabel("Load data to view - Shows processed data (CSV + derived targets)")
        data_header.addWidget(self.data_info_label)
        data_help_btn = QPushButton("?")
        data_help_btn.setFixedSize(22, 22)
        data_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        data_help_btn.setToolTip("Click for explanation")
        data_help_btn.clicked.connect(self._show_data_view_help)
        data_header.addWidget(data_help_btn)
        data_header.addStretch()
        layout.addLayout(data_header)
        # Table
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        layout.addWidget(self.data_table)
        
        return widget
    
    def _create_column_info(self) -> QWidget:
        """Create column information view"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Column selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Select column:"))
        self.column_combo = QComboBox()
        self.column_combo.currentTextChanged.connect(self._on_column_selected)
        selector_layout.addWidget(self.column_combo, 1)
        col_help_btn = QPushButton("?")
        col_help_btn.setFixedSize(22, 22)
        col_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        col_help_btn.setToolTip("Click for explanation")
        col_help_btn.clicked.connect(self._show_column_info_help)
        selector_layout.addWidget(col_help_btn)
        layout.addLayout(selector_layout)
        
        # Column details
        self.column_details = QTextEdit()
        self.column_details.setReadOnly(True)
        self.column_details.setMaximumHeight(300)
        layout.addWidget(self.column_details)
        
        return widget
    
    def _create_stats_view(self) -> QWidget:
        """Create statistics view"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        stats_header = QHBoxLayout()
        stats_header.addStretch()
        stats_help_btn = QPushButton("?")
        stats_help_btn.setFixedSize(22, 22)
        stats_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        stats_help_btn.setToolTip("Click for explanation")
        stats_help_btn.clicked.connect(self._show_stats_help)
        stats_header.addWidget(stats_help_btn)
        layout.addLayout(stats_header)
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setFontFamily("Consolas")
        layout.addWidget(self.stats_text)
        
        return widget
    
    def _create_missing_view(self) -> QWidget:
        """Create missing data analysis view"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        missing_header = QHBoxLayout()
        missing_header.addStretch()
        missing_help_btn = QPushButton("?")
        missing_help_btn.setFixedSize(22, 22)
        missing_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        missing_help_btn.setToolTip("Click for explanation")
        missing_help_btn.clicked.connect(self._show_missing_help)
        missing_header.addWidget(missing_help_btn)
        layout.addLayout(missing_header)
        self.missing_text = QTextEdit()
        self.missing_text.setReadOnly(True)
        self.missing_text.setFontFamily("Consolas")
        layout.addWidget(self.missing_text)
        
        return widget
    
    def _create_derived_view(self) -> QWidget:
        """Create derived/calculated columns view"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Info label and hint
        derived_header = QHBoxLayout()
        self.derived_info_label = QLabel("Shows only derived/calculated columns (gates and response targets)")
        derived_header.addWidget(self.derived_info_label)
        derived_hint_btn = QPushButton("?")
        derived_hint_btn.setFixedSize(22, 22)
        derived_hint_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        derived_hint_btn.setToolTip("Click for explanation")
        derived_hint_btn.clicked.connect(self._show_derived_columns_help)
        derived_header.addWidget(derived_hint_btn)
        derived_header.addStretch()
        layout.addLayout(derived_header)
        
        # Table for derived columns
        self.derived_table = QTableWidget()
        self.derived_table.setAlternatingRowColors(True)
        layout.addWidget(self.derived_table)
        
        # Statistics text
        self.derived_stats_text = QTextEdit()
        self.derived_stats_text.setReadOnly(True)
        self.derived_stats_text.setFontFamily("Consolas")
        self.derived_stats_text.setMaximumHeight(200)
        layout.addWidget(self.derived_stats_text)
        
        return widget
    
    def _show_controls_help(self):
        """Show explanation of Data Controls."""
        QMessageBox.information(
            self,
            "Data Controls",
            "Rows to display: limit how many rows are shown in the Data View table (default: all). "
            "Show all columns: when unchecked, only a subset of key columns is shown. "
            "Refresh: reload views from the current dataset (e.g. after target derivation in Pipeline Flow)."
        )

    def _show_data_view_help(self):
        """Show explanation of Data View tab."""
        QMessageBox.information(
            self,
            "Data View",
            "Shows the processed dataset (after load and target derivation): raw CSV columns plus derived columns "
            "(gates, binary indicators, outcome targets). Use this to inspect values, check for missing data, "
            "and verify derived targets. Data is from the Pipeline Flow: Load Data and Target Derivation must be run first."
        )

    def _show_column_info_help(self):
        """Show explanation of Column Info."""
        QMessageBox.information(
            self,
            "Column Info",
            "Select a column to see its type (numeric, categorical, etc.), sample values, and any categorical mappings. "
            "Useful to understand encoding and valid values before feature engineering or model training."
        )

    def _show_stats_help(self):
        """Show explanation of Statistics view."""
        QMessageBox.information(
            self,
            "Statistics",
            "Summary statistics for numeric columns: count, mean, std, min, max, and quartiles. "
            "Helps identify distributions, outliers, and missing counts before modeling."
        )

    def _show_missing_help(self):
        """Show explanation of Missing Data view."""
        QMessageBox.information(
            self,
            "Missing Data",
            "Per-column counts and percentages of missing values. Use this to decide which columns need imputation "
            "or exclusion in feature engineering. Gates and targets may have missing if not all patients are evaluable."
        )

    def _show_derived_columns_help(self):
        """Show explanation of gates, binary indicators, and targets."""
        QMessageBox.information(
            self,
            "Derived columns",
            "Gates (e.g. D30_evaluable_gate): 0/1 indicating whether the patient is evaluable for that "
            "timepoint (e.g. had response assessment at Day 30). Used to filter who can be included in "
            "training for that outcome.\n\n"
            "Binary indicators: 0/1 derived from clinical events (e.g. CRS grade >= 2, infection).\n\n"
            "Targets: outcome columns used for prediction (e.g. D30_response_3class = Complete/Partial/Minimal "
            "response; D90_is_cr = Complete Response yes/no). Models are trained to predict these."
        )
    
    def load_data(self, data: pd.DataFrame):
        """Load data into inspector - this should be FINAL processed data"""
        try:
            self.data = data
            self.logger.info(f"Processed data loaded into inspector: {data.shape[0]} rows, {data.shape[1]} columns", "DataInspector")
            
            # Identify derived columns (those created by target derivation)
            self._identify_derived_columns()
            
            # Update status to clarify this is processed data
            derived_count = len(self.derived_columns)
            original_count = data.shape[1] - derived_count
            self.status_label.setText(
                f"Processed Data: {data.shape[0]:,} rows × {data.shape[1]} columns "
                f"({original_count} original + {derived_count} derived)"
            )
            self.status_label.setStyleSheet("QLabel { color: #080; font-weight: bold; }")
            self.refresh_btn.setEnabled(True)
            
            # Populate column combo
            self.column_combo.clear()
            self.column_combo.addItems(data.columns.tolist())
            
            # Refresh all views
            self._refresh_all_views()
            
            self.logger.info(f"Data inspector views refreshed successfully ({derived_count} derived columns identified)", "DataInspector")
            
        except Exception as e:
            error_msg = f"Error loading data into inspector: {str(e)}"
            self.logger.error(error_msg, "DataInspector")
            import traceback
            traceback.print_exc()
            
            # Show error in UI
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: #f00; font-weight: bold; }")
    
    def _identify_derived_columns(self):
        """Identify which columns are derived/calculated"""
        if self.data is None:
            self.derived_columns = []
            return
        
        # Known patterns for derived columns from target derivation
        derived_patterns = [
            '_evaluable_gate',  # D30_evaluable_gate, D90_evaluable_gate, etc.
            '_response_3class',  # D30_response_3class
            '_is_cr',           # D90_is_cr
            '_is_responder',    # D90_is_responder
        ]
        
        # Known exact derived column names
        known_derived = [
            'D30_evaluable_gate', 'D90_evaluable_gate', 'M6_evaluable_gate',
            'Y1_evaluable_gate', 'BEST_evaluable_gate',
            'D30_response_3class', 'D90_is_cr', 'D90_is_responder',
            'is_cr_d30', 'is_cr_d90', 'is_responder_d30', 'is_responder_d90',
            'cart_response_6_mos', 'cart_response_1_yr', 'best_response',
            'crs_grade_ge2', 'icans_grade_ge2', 'max_crs_grade', 'icans_max_grade'
        ]
        
        self.derived_columns = []
        for col in self.data.columns:
            # Check if matches any pattern
            is_derived = any(pattern in col for pattern in derived_patterns)
            # Or is in known list
            is_derived = is_derived or col in known_derived
            
            if is_derived:
                self.derived_columns.append(col)
        
        self.logger.info(f"Identified {len(self.derived_columns)} derived columns", "DataInspector")
    
    def _refresh_all_views(self):
        """Refresh all data views"""
        if self.data is None:
            return
        
        self._refresh_data_view()
        self._refresh_stats_view()
        self._refresh_missing_view()
        self._refresh_derived_view()
        if self.column_combo.currentText():
            self._on_column_selected(self.column_combo.currentText())
    
    def _refresh_data_view(self):
        """Refresh the data table view"""
        if self.data is None:
            return
        
        max_rows = self.rows_spin.value()
        df_display = self.data.head(max_rows)
        
        # Update info label
        showing = min(max_rows, len(self.data))
        self.data_info_label.setText(
            f"Showing {showing:,} of {len(self.data):,} rows, "
            f"{len(self.data.columns)} columns"
        )
        
        # Populate table
        self.data_table.clear()
        self.data_table.setRowCount(len(df_display))
        self.data_table.setColumnCount(len(df_display.columns))
        self.data_table.setHorizontalHeaderLabels(df_display.columns.tolist())
        
        for i in range(len(df_display)):
            for j, col in enumerate(df_display.columns):
                value = df_display.iloc[i, j]
                
                # Format numeric values to 2 decimal places
                if isinstance(value, float) and not pd.isna(value):
                    value_str = f"{value:.2f}"
                else:
                    value_str = str(value)
                
                item = QTableWidgetItem(value_str)
                
                # Color missing values
                if pd.isna(value):
                    item.setBackground(Qt.GlobalColor.lightGray)
                    item.setForeground(Qt.GlobalColor.darkGray)
                
                self.data_table.setItem(i, j, item)
        
        # Adjust column widths
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.data_table.resizeColumnsToContents()
    
    def _refresh_stats_view(self):
        """Refresh statistics view"""
        if self.data is None:
            return
        
        # Get numeric columns
        numeric_df = self.data.select_dtypes(include=['number'])
        
        if numeric_df.empty:
            self.stats_text.setPlainText("No numeric columns found in dataset.")
            return
        
        # Calculate statistics - TRANSPOSED for readability
        stats_text = "NUMERIC COLUMN STATISTICS (Per Column)\n"
        stats_text += "=" * 80 + "\n\n"
        stats_text += f"Total numeric columns: {len(numeric_df.columns)}\n"
        stats_text += f"Total rows: {len(numeric_df)}\n\n"
        
        desc = numeric_df.describe()
        
        # Format each column separately (vertical format)
        for col in numeric_df.columns:
            if col in desc.columns:
                stats_text += f"{col}:\n"
                stats_text += f"  Count:  {desc[col]['count']:.0f}\n"
                stats_text += f"  Mean:   {desc[col]['mean']:.2f}\n"
                stats_text += f"  Std:    {desc[col]['std']:.2f}\n"
                stats_text += f"  Min:    {desc[col]['min']:.2f}\n"
                stats_text += f"  25%:    {desc[col]['25%']:.2f}\n"
                stats_text += f"  50%:    {desc[col]['50%']:.2f}\n"
                stats_text += f"  75%:    {desc[col]['75%']:.2f}\n"
                stats_text += f"  Max:    {desc[col]['max']:.2f}\n"
                stats_text += "\n"
        
        stats_text += "=" * 80 + "\n"
        stats_text += "CORRELATION SUMMARY (|r| > 0.7)\n"
        stats_text += "=" * 80 + "\n\n"
        
        # Show high correlations
        if len(numeric_df.columns) > 1:
            corr = numeric_df.corr()
            high_corr = []
            
            for i in range(len(corr.columns)):
                for j in range(i+1, len(corr.columns)):
                    val = corr.iloc[i, j]
                    if abs(val) > 0.7 and not pd.isna(val):
                        high_corr.append((corr.columns[i], corr.columns[j], val))
            
            if high_corr:
                high_corr.sort(key=lambda x: abs(x[2]), reverse=True)
                for col1, col2, val in high_corr[:20]:  # Top 20
                    stats_text += f"{col1} <-> {col2}: {val:.2f}\n"
            else:
                stats_text += "No strong correlations found (|r| > 0.7)\n"
        else:
            stats_text += "Need at least 2 numeric columns for correlation analysis.\n"
        
        self.stats_text.setPlainText(stats_text)
    
    def _refresh_missing_view(self):
        """Refresh missing data view"""
        if self.data is None:
            return
        
        missing_text = "MISSING DATA ANALYSIS\n"
        missing_text += "=" * 80 + "\n\n"
        
        # Overall stats
        total_values = self.data.shape[0] * self.data.shape[1]
        missing_values = self.data.isna().sum().sum()
        missing_pct = (missing_values / total_values) * 100
        
        missing_text += f"Total values: {total_values:,}\n"
        missing_text += f"Missing values: {missing_values:,}\n"
        missing_text += f"Completeness: {100-missing_pct:.1f}%\n\n"
        
        missing_text += "=" * 80 + "\n"
        missing_text += "MISSING VALUES BY COLUMN\n"
        missing_text += "=" * 80 + "\n\n"
        
        # Missing by column
        missing_by_col = self.data.isna().sum()
        missing_by_col = missing_by_col[missing_by_col > 0].sort_values(ascending=False)
        
        if len(missing_by_col) > 0:
            missing_text += f"{'Column':<50} {'Missing':<10} {'%':<10}\n"
            missing_text += "-" * 80 + "\n"
            
            for col, count in missing_by_col.items():
                pct = (count / len(self.data)) * 100
                missing_text += f"{col:<50} {count:<10} {pct:>6.1f}%\n"
        else:
            missing_text += "No missing values found!\n"
        
        missing_text += "\n" + "=" * 80 + "\n"
        missing_text += "MISSING VALUES BY ROW\n"
        missing_text += "=" * 80 + "\n\n"
        
        # Missing by row
        missing_by_row = self.data.isna().sum(axis=1)
        row_stats = missing_by_row.describe()
        
        missing_text += f"Min missing per row: {row_stats['min']:.0f}\n"
        missing_text += f"Max missing per row: {row_stats['max']:.0f}\n"
        missing_text += f"Mean missing per row: {row_stats['mean']:.1f}\n"
        missing_text += f"Median missing per row: {row_stats['50%']:.0f}\n"
        
        # Rows with most missing
        worst_rows = missing_by_row.nlargest(10)
        if len(worst_rows) > 0:
            missing_text += f"\nRows with most missing values:\n"
            for idx, count in worst_rows.items():
                pct = (count / len(self.data.columns)) * 100
                missing_text += f"  Row {idx}: {count} missing ({pct:.1f}%)\n"
        
        self.missing_text.setPlainText(missing_text)
    
    def _on_column_selected(self, column_name: str):
        """Handle column selection"""
        if self.data is None or not column_name:
            return
        
        col_data = self.data[column_name]
        
        details = f"COLUMN: {column_name}\n"
        details += "=" * 60 + "\n\n"
        
        details += f"Data type: {col_data.dtype}\n"
        details += f"Total values: {len(col_data):,}\n"
        details += f"Missing values: {col_data.isna().sum():,} ({col_data.isna().sum()/len(col_data)*100:.1f}%)\n"
        details += f"Unique values: {col_data.nunique():,}\n\n"
        
        # Show mapping information if this is a standardized categorical column
        if column_name in CATEGORICAL_MAPPINGS:
            details += "STANDARDIZATION:\n"
            details += "-" * 60 + "\n"
            details += f"{CATEGORICAL_MAPPINGS[column_name]}\n"
            details += f"(See data/CATEGORICAL_MAPPINGS.md for complete details)\n\n"
        
        # Type-specific info
        if pd.api.types.is_numeric_dtype(col_data):
            details += "NUMERIC STATISTICS:\n"
            details += "-" * 60 + "\n"
            details += f"Min: {col_data.min():.2f}\n"
            details += f"Max: {col_data.max():.2f}\n"
            details += f"Mean: {col_data.mean():.2f}\n"
            details += f"Median: {col_data.median():.2f}\n"
            details += f"Std: {col_data.std():.2f}\n\n"
        
        # Value counts
        details += "TOP VALUE COUNTS:\n"
        details += "-" * 60 + "\n"
        value_counts = col_data.value_counts().head(20)
        for value, count in value_counts.items():
            pct = (count / len(col_data)) * 100
            # Format numeric values to 2 decimal places
            if isinstance(value, (int, float)) and not pd.isna(value):
                value_str = f"{value:.2f}"
            else:
                value_str = str(value)[:40]
            details += f"{value_str:<40} {count:>6} ({pct:>5.1f}%)\n"
        
        self.column_details.setPlainText(details)
    
    def _refresh_derived_view(self):
        """Refresh derived columns view"""
        if self.data is None or len(self.derived_columns) == 0:
            self.derived_info_label.setText("No derived columns found")
            self.derived_table.clear()
            self.derived_table.setRowCount(0)
            self.derived_table.setColumnCount(0)
            self.derived_stats_text.setPlainText("Load data with derived columns to view statistics.")
            return
        
        # Update info label
        self.derived_info_label.setText(
            f"Showing {len(self.derived_columns)} derived/calculated columns "
            f"(gates, response targets, binary indicators)"
        )
        
        # Get only derived columns
        derived_df = self.data[self.derived_columns]
        max_rows = self.rows_spin.value()
        df_display = derived_df.head(max_rows)
        
        # Populate table
        self.derived_table.clear()
        self.derived_table.setRowCount(len(df_display))
        self.derived_table.setColumnCount(len(df_display.columns))
        self.derived_table.setHorizontalHeaderLabels(df_display.columns.tolist())
        
        for i in range(len(df_display)):
            for j, col in enumerate(df_display.columns):
                value = df_display.iloc[i, j]
                
                # Format numeric values to 2 decimal places
                if isinstance(value, float) and not pd.isna(value):
                    value_str = f"{value:.2f}"
                else:
                    value_str = str(value)
                
                item = QTableWidgetItem(value_str)
                
                # Color missing values
                if pd.isna(value):
                    item.setBackground(Qt.GlobalColor.lightGray)
                    item.setForeground(Qt.GlobalColor.darkGray)
                
                self.derived_table.setItem(i, j, item)
        
        # Adjust column widths
        self.derived_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.derived_table.resizeColumnsToContents()
        
        # Generate statistics text
        stats_text = "DERIVED COLUMNS STATISTICS\n"
        stats_text += "=" * 80 + "\n\n"
        
        # Categorize columns
        gates = [col for col in self.derived_columns if '_evaluable_gate' in col]
        response_targets = [col for col in self.derived_columns if 'response' in col.lower() or 'is_cr' in col or 'is_responder' in col]
        other = [col for col in self.derived_columns if col not in gates and col not in response_targets]
        
        stats_text += f"Total derived columns: {len(self.derived_columns)}\n"
        stats_text += f"  - Evaluable gates: {len(gates)}\n"
        stats_text += f"  - Response targets: {len(response_targets)}\n"
        stats_text += f"  - Other indicators: {len(other)}\n\n"
        
        stats_text += "=" * 80 + "\n"
        stats_text += "VALUE DISTRIBUTIONS\n"
        stats_text += "=" * 80 + "\n\n"
        
        # Show value counts for each derived column
        for col in self.derived_columns:
            col_data = self.data[col]
            stats_text += f"{col}:\n"
            stats_text += f"  Non-null: {col_data.notna().sum()} ({col_data.notna().sum()/len(col_data)*100:.1f}%)\n"
            
            value_counts = col_data.value_counts().head(10)
            if len(value_counts) > 0:
                stats_text += "  Top values:\n"
                for value, count in value_counts.items():
                    pct = (count / len(col_data)) * 100
                    stats_text += f"    {str(value)[:30]:<30} {count:>5} ({pct:>5.1f}%)\n"
            
            stats_text += "\n"
        
        self.derived_stats_text.setPlainText(stats_text)
    
    def _on_rows_changed(self, value: int):
        """Handle rows spinner change"""
        self._refresh_data_view()
