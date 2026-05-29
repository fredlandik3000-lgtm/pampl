"""Main Window for Biomarkers Pipeline Tool"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTextEdit, QLabel, QMenuBar, QMenu, QStatusBar, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QFont
from typing import Optional

from app.core.config_manager import ConfigManager
from app.core.logger_manager import LoggerManager


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signals
    log_message = pyqtSignal(str, str, str)  # level, source, message
    
    def __init__(
        self,
        config: ConfigManager,
        logger: LoggerManager,
        mode: str = "research",
        parent: Optional[QWidget] = None
    ):
        """
        Initialize main window.
        
        Args:
            config: Configuration manager
            logger: Logger manager
            mode: Application mode ('clinical', 'research', 'demo')
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.config = config
        self.logger = logger
        self.mode = mode
        
        # Initialize UI first
        self._init_ui()
        
        # Set up logger callback AFTER console is created
        self.logger.set_callback(self._on_log_message)
        
        self.logger.info(f"Application started in {mode} mode", "MainWindow")
    
    def _init_ui(self) -> None:
        """Initialize user interface."""
        # Window properties
        self.setWindowTitle(self._get_window_title())
        # Default to smaller size for laptops (1200x800 instead of 1920x1080)
        window_size = self.config.get("ui.window_size", [1200, 800])
        self.resize(window_size[0], window_size[1])
        
        # Center window on screen
        from PyQt6.QtGui import QScreen
        screen = QScreen.availableGeometry(self.screen())
        center_x = (screen.width() - window_size[0]) // 2
        center_y = (screen.height() - window_size[1]) // 2
        self.move(center_x, center_y)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for main content and console
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Create tab widget for main content
        self.tab_widget = QTabWidget()
        self._create_tabs()
        splitter.addWidget(self.tab_widget)
        
        # Create debug console
        self.console = self._create_console()
        splitter.addWidget(self.console)
        
        # Set initial splitter sizes
        console_height = self.config.get("ui.console_height", 200)
        splitter.setSizes([window_size[1] - console_height, console_height])
        
        main_layout.addWidget(splitter)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create status bar
        self._create_status_bar()
    
    def _get_window_title(self) -> str:
        """Get window title based on mode."""
        mode_names = {
            "clinical": "Clinical Prediction Mode",
            "research": "Research & Development Mode",
            "academic_review": "Academic Review Mode"
        }
        
        name = mode_names.get(self.mode, "Biomarkers Pipeline Tool")
        
        return f"{name} - Biomarkers Pipeline Tool"
    
    def _create_tabs(self) -> None:
        """Create tab widgets based on mode."""
        if self.mode == "clinical":
            self._create_clinical_tabs()
        else:
            self._create_research_tabs()
    
    def _create_clinical_tabs(self) -> None:
        """Create tabs for clinical mode."""
        # Patient Input tab
        patient_input = QWidget()
        layout = QVBoxLayout(patient_input)
        label = QLabel("Patient Input Form")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        label.setFont(font)
        layout.addWidget(label)
        self.tab_widget.addTab(patient_input, "📋 Patient Input")
        
        # Results tab
        results = QWidget()
        layout = QVBoxLayout(results)
        label = QLabel("Prediction Results")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(font)
        layout.addWidget(label)
        self.tab_widget.addTab(results, "📊 Results")
        
        # Report tab
        report = QWidget()
        layout = QVBoxLayout(report)
        label = QLabel("Patient Report")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(font)
        layout.addWidget(label)
        self.tab_widget.addTab(report, "📄 Report")
    
    def _create_research_tabs(self) -> None:
        """Create tabs for research mode."""
        # Pipeline Flow tab - with actual pipeline runner
        from app.ui.widgets.pipeline_runner_widget import PipelineRunnerWidget
        from app.pipeline.types import PipelineConfig
        from pathlib import Path

        from app.core.repo_paths import data_dir

        # Default data path: repo_root/data/unified_clinical_data.csv; fallback try cwd
        default_data_path = data_dir() / "unified_clinical_data.csv"
        if not default_data_path.exists():
            # Try data folder next to current working directory (e.g. run from repo root)
            cwd_data = Path.cwd() / "data" / "unified_clinical_data.csv"
            if cwd_data.exists():
                default_data_path = cwd_data
            # else keep repo path so user sees where app expects the file and can use Browse
        
        pipeline_config = PipelineConfig(
            data_path=str(default_data_path.resolve() if default_data_path.exists() else default_data_path),
            phases=self.config.get("pipeline.phases", ["phase_-6", "phase_0", "phase_15", "phase_30"]),
            targets=self.config.get("pipeline.targets", []),
            random_seed=self.config.get("pipeline.random_seed", 42),
            test_size=self.config.get("pipeline.test_size", self.config.get("splitting.test_size", 0.3)),
            validate_data=self.config.get("data.validate_on_load", True),
            use_cv_evaluation=self.config.get("pipeline.use_cv_evaluation", True),
            evaluation_mode=self.config.get("pipeline.evaluation_mode", "nested_cv"),
            n_repeats=self.config.get("pipeline.n_repeats", 3),
            use_feature_selection=self.config.get("pipeline.use_feature_selection", False),
            feature_selection_method=self.config.get("pipeline.feature_selection_method", "mutual_info"),
            feature_selection_top_k=self.config.get("pipeline.feature_selection_top_k", 50),
            cv_curve_source=self.config.get("pipeline.cv_curve_source", "last_outer_fold"),
        )
        
        pipeline = PipelineRunnerWidget(pipeline_config, self.logger)
        self.tab_widget.addTab(pipeline, "Pipeline Flow")
        
        # Store reference to pipeline for connecting later
        self.pipeline_runner = pipeline
        
        # Data Inspector tab - with actual inspector (SECOND TAB - right after Pipeline)
        from app.ui.widgets.data_inspector_widget import DataInspectorWidget
        self.data_inspector = DataInspectorWidget(self.logger)
        self.tab_widget.addTab(self.data_inspector, "Data Inspector")
        
        # Connect pipeline data loading to inspector
        self.pipeline_runner.data_loaded.connect(self.data_inspector.load_data)
        
        # Model Comparison tab - with actual widget
        from app.ui.widgets.model_comparison_widget import ModelComparisonWidget
        self.model_comparison = ModelComparisonWidget(self.logger)
        self.tab_widget.addTab(self.model_comparison, "Model Comparison")
        
        # Create placeholder font for other tabs
        font = QFont()
        font.setPointSize(16)
        
        # Visualizations tab (Phase 5: ROC, confusion matrix, heatmap)
        from app.ui.widgets.visualizations_widget import VisualizationsWidget
        self.visualizations_widget = VisualizationsWidget()
        self.tab_widget.addTab(self.visualizations_widget, "Visualizations")
        
        # Feature Analysis tab - with actual widget
        from app.ui.widgets.feature_analysis_widget import FeatureAnalysisWidget
        self.feature_analysis = FeatureAnalysisWidget(self.logger)
        self.tab_widget.addTab(self.feature_analysis, "Feature Analysis")
        
        # Connect feature engineering to feature analysis (AFTER widget is created)
        self.pipeline_runner.features_engineered.connect(self.feature_analysis.load_engineered_features)
        # Connect training results to Model Comparison tab
        self.pipeline_runner.training_results_ready.connect(self.model_comparison.load_results)
        # Connect full training result (with ROC/confusion) to Visualizations tab
        self.pipeline_runner.training_result_full.connect(self.visualizations_widget.load_training_result)
        # Connect training metadata (feature importances) to Feature Analysis tab
        self.pipeline_runner.training_result_full.connect(
            lambda data, metadata: self.feature_analysis.set_model_importance(metadata)
        )
        
        # Validation Results tab
        from app.ui.widgets.validation_results_widget import ValidationResultsWidget
        self.validation_results = ValidationResultsWidget(self.logger)
        self.tab_widget.addTab(self.validation_results, "Validation Results")
        try:
            self.validation_results.set_split_info(
                getattr(pipeline_config, "test_size", 0.3),
                getattr(pipeline_config, "random_seed", 42),
            )
        except Exception:
            pass
        # Registry Viewer tab (Phase 6)
        from app.ui.widgets.registry_viewer_widget import RegistryViewerWidget
        self.registry_viewer = RegistryViewerWidget(self.logger)
        self.tab_widget.addTab(self.registry_viewer, "Registry Viewer")
        self.pipeline_runner.training_results_ready.connect(self.registry_viewer.set_current_results)
        self.pipeline_runner.training_results_ready.connect(self.validation_results.set_validation_metrics)
        self.pipeline_runner.training_result_full.connect(self._on_training_result_for_validation)
        self.pipeline_runner.validation_kfold_ready.connect(self.validation_results.set_kfold_metrics)

    def _on_training_result_for_validation(self, data, metadata):
        """Update Validation Results tab with train/test metrics, bootstrap CIs, baseline comparison, target summary."""
        self.validation_results.set_validation_metrics(data)
        self.validation_results.set_bootstrap_metrics(metadata.get("bootstrap_cis", []))
        self.validation_results.set_target_summary(metadata.get("target_summary", []))

    def _create_console(self) -> QTextEdit:
        """Create debug console widget."""
        console = QTextEdit()
        console.setReadOnly(True)
        console.setFont(QFont("Consolas", 9))
        console.setStyleSheet("""
            QTextEdit {
                background-color: #263238;
                color: #CCCCCC;
                border: 1px solid #37474F;
            }
        """)
        
        return console
    
    def _create_menu_bar(self) -> None:
        """Create menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        if self.mode == "clinical":
            new_patient_action = QAction("&New Patient", self)
            new_patient_action.setShortcut("Ctrl+N")
            file_menu.addAction(new_patient_action)
            
            load_patient_action = QAction("&Load Patient...", self)
            load_patient_action.setShortcut("Ctrl+O")
            file_menu.addAction(load_patient_action)
            
            save_patient_action = QAction("&Save Patient", self)
            save_patient_action.setShortcut("Ctrl+S")
            file_menu.addAction(save_patient_action)
            
            file_menu.addSeparator()
            
            export_report_action = QAction("Export &Report...", self)
            export_report_action.setShortcut("Ctrl+E")
            file_menu.addAction(export_report_action)
        else:
            load_data_action = QAction("&Load Data...", self)
            load_data_action.setShortcut("Ctrl+O")
            file_menu.addAction(load_data_action)
            
            file_menu.addSeparator()
            
            export_action = QAction("&Export Results...", self)
            export_action.setShortcut("Ctrl+E")
            file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu (research mode only)
        if self.mode != "clinical":
            edit_menu = menubar.addMenu("&Edit")
            
            params_action = QAction("&Parameters...", self)
            params_action.setShortcut("Ctrl+P")
            edit_menu.addAction(params_action)
            
            edit_menu.addSeparator()
            
            presets_action = QAction("P&resets...", self)
            edit_menu.addAction(presets_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        toggle_console_action = QAction("Toggle &Console", self)
        toggle_console_action.setShortcut("Ctrl+`")
        toggle_console_action.triggered.connect(self._toggle_console)
        view_menu.addAction(toggle_console_action)
        
        view_menu.addSeparator()
        
        fullscreen_action = QAction("&Fullscreen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Mode menu
        mode_menu = menubar.addMenu("&Mode")
        
        clinical_mode_action = QAction("&Clinical Prediction", self)
        clinical_mode_action.triggered.connect(lambda: self._switch_mode("clinical"))
        mode_menu.addAction(clinical_mode_action)
        
        research_mode_action = QAction("&Research && Development", self)
        research_mode_action.triggered.connect(lambda: self._switch_mode("research"))
        mode_menu.addAction(research_mode_action)
        
        academic_mode_action = QAction("&Academic Review", self)
        academic_mode_action.triggered.connect(lambda: self._switch_mode("academic_review"))
        mode_menu.addAction(academic_mode_action)
        
        # Run menu (research mode only)
        if self.mode != "clinical":
            run_menu = menubar.addMenu("&Run")
            
            run_all_action = QAction("Run &All Steps", self)
            run_all_action.setShortcut("F5")
            run_menu.addAction(run_all_action)
            
            run_step_action = QAction("Run Current &Step", self)
            run_step_action.setShortcut("F6")
            run_menu.addAction(run_step_action)
            
            run_menu.addSeparator()
            
            stop_action = QAction("&Stop", self)
            stop_action.setShortcut("Shift+F5")
            run_menu.addAction(stop_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        clear_cache_action = QAction("Clear &Cache", self)
        tools_menu.addAction(clear_cache_action)
        
        clear_logs_action = QAction("Clear &Logs", self)
        tools_menu.addAction(clear_logs_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        docs_action = QAction("&Documentation", self)
        docs_action.setShortcut("F1")
        help_menu.addAction(docs_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_status_bar(self) -> None:
        """Create status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Add permanent widgets to status bar
        self.status_label = QLabel("Status: Ready")
        self.progress_label = QLabel("")
        self.time_label = QLabel("")
        
        self.status_bar.addPermanentWidget(self.status_label)
        self.status_bar.addPermanentWidget(self.progress_label)
        self.status_bar.addPermanentWidget(self.time_label)
    
    def _on_log_message(self, level: str, source: str, message: str) -> None:
        """Handle log message for console display."""
        # Color code by level
        color_map = {
            "DEBUG": "#888888",
            "INFO": "#4CAF50",
            "WARNING": "#FF9800",
            "ERROR": "#F44336",
            "CRITICAL": "#D32F2F"
        }
        
        color = color_map.get(level, "#CCCCCC")
        
        # Format message
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f'<span style="color: {color};">[{level}] {timestamp} - [{source}] {message}</span>'
        
        # Append to console
        self.console.append(formatted)
        
        # Auto-scroll if enabled
        if self.config.get("ui.auto_scroll", True):
            self.console.verticalScrollBar().setValue(
                self.console.verticalScrollBar().maximum()
            )
    
    def _toggle_console(self) -> None:
        """Toggle console visibility."""
        self.console.setVisible(not self.console.isVisible())
    
    def _toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def _switch_mode(self, mode: str) -> None:
        """Switch application mode."""
        if mode == self.mode:
            return
        
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Switch Mode",
            f"Switch to {mode.replace('_', ' ').title()} mode?\n\nThis will reload the interface.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.mode = mode
            self.logger.info(f"Switched to {mode} mode", "MainWindow")
            
            # Update window title
            self.setWindowTitle(self._get_window_title())
            
            # Clear and recreate tabs
            self.tab_widget.clear()
            self._create_tabs()
    
    def _show_about(self) -> None:
        """Show about dialog."""
        from PyQt6.QtWidgets import QMessageBox
        
        QMessageBox.about(
            self,
            "About Biomarkers Pipeline Tool",
            "<h2>Biomarkers Pipeline Tool v1.0.0</h2>"
            "<p>A comprehensive tool for CAR-T therapy outcome prediction.</p>"
            "<p>Copyright © 2026</p>"
        )
    
    def update_status(self, message: str) -> None:
        """Update status bar message."""
        self.status_label.setText(f"Status: {message}")
    
    def update_progress(self, progress: int, total: int) -> None:
        """Update progress display."""
        if total > 0:
            percent = int((progress / total) * 100)
            self.progress_label.setText(f"Progress: {percent}% ({progress}/{total} steps)")
        else:
            self.progress_label.setText("")
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.logger.info("Application closing", "MainWindow")
        event.accept()
