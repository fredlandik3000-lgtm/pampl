"""Pipeline Runner Widget for executing pipeline steps with progress"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QProgressBar, QLabel, QGroupBox, QTextEdit, QFileDialog, QLineEdit, QComboBox,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QSpinBox, QDoubleSpinBox,
    QCheckBox,
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from typing import Optional
from pathlib import Path
import pickle
import shutil
from datetime import datetime

from app.pipeline.types import PipelineStep, PipelineConfig
from app.core.repo_paths import (
    data_dir,
    results_runs_dir,
    results_latest_dir,
    repo_root,
    LATEST_TRAINING_FILENAME,
)
from app.ui.widgets.pipeline_saved_runs import (
    TRAINING_RESULTS_PREFIX,
    format_saved_result_label,
    iter_saved_run_paths_ordered,
)
from app.core.pipeline_orchestrator import PipelineOrchestrator
from app.pipeline.wrappers.data_loader_wrapper import DataLoaderWrapper
from app.pipeline.wrappers.target_derivation_wrapper import TargetDerivationWrapper
from app.pipeline.wrappers.feature_engineering_wrapper import FeatureEngineeringWrapper
from app.pipeline.wrappers.model_training_wrapper import ModelTrainingWrapper
from app.core.logger_manager import LoggerManager

# Phases to run when "Run all phases" is used (main focus: phase_15)
ALL_PHASES = ["phase_-6", "phase_0", "phase_15", "phase_30"]

# Timestamped saves under repo results/runs/; latest copy in results/latest/
RESULTS_DIR = results_runs_dir()


class AllPhasesWorker(QThread):
    """Worker that runs feature engineering + model training for all phases and emits combined results."""
    progress_updated = pyqtSignal(float, str)
    finished_with_result = pyqtSignal(object)  # StepResult

    def __init__(self, derived_df, config: PipelineConfig, model_families_filter=None):
        super().__init__()
        self.derived_df = derived_df
        self.config = config
        self.model_families_filter = model_families_filter  # e.g. ['LR'] for LR-only (merge-on-load)
        self.feature_engineer = FeatureEngineeringWrapper()
        self.trainer = ModelTrainingWrapper()

    def run(self):
        from app.pipeline.types import StepResult
        n = len(ALL_PHASES)
        all_results = []
        all_roc = []
        all_cm = []
        all_cal = []
        all_pr = []
        all_fi = []
        for i, phase in enumerate(ALL_PHASES):
            self.progress_updated.emit((i + 0.0) / n, f"{phase}: engineering...")
            fe_result = self.feature_engineer.engineer_features(
                self.derived_df,
                phase=phase,
                fit_scalers=True,
                use_feature_selection=getattr(self.config, "use_feature_selection", False),
                feature_selection_method=getattr(self.config, "feature_selection_method", "mutual_info"),
                feature_selection_top_k=getattr(self.config, "feature_selection_top_k", 50),
            )
            if not fe_result.success or fe_result.data is None:
                continue
            self.progress_updated.emit((i + 0.5) / n, f"{phase}: training...")

            def make_progress(phase_idx, phase_total):
                def progress_cb(pct, msg):
                    self.progress_updated.emit((phase_idx + pct) / phase_total, msg)
                return progress_cb

            mode = getattr(self.config, "evaluation_mode", "nested_cv")
            if not mode:
                mode = "nested_cv" if getattr(self.config, "use_cv_evaluation", True) else "single_split"
            if mode == "repeated_holdout":
                train_result = self.trainer.train_models_repeated_holdout(
                    fe_result.data,
                    phase,
                    fe_result.metadata,
                    n_repeats=getattr(self.config, "n_repeats", 3),
                    test_size=getattr(self.config, "test_size", 0.3),
                    progress_callback=make_progress(i, n),
                    random_seed=self.config.random_seed,
                    model_families_filter=getattr(self, "model_families_filter", None),
                )
            elif mode == "nested_cv":
                train_result = self.trainer.train_models_nested_cv(
                    fe_result.data,
                    phase,
                    fe_result.metadata,
                    n_outer_splits=5,
                    n_inner_splits=3,
                    progress_callback=make_progress(i, n),
                    random_seed=self.config.random_seed,
                    model_families_filter=self.model_families_filter,
                    cv_curve_source=getattr(self.config, "cv_curve_source", "last_outer_fold"),
                    test_size=getattr(self.config, "test_size", 0.3),
                )
            elif getattr(self.config, "use_cv_evaluation", False):
                train_result = self.trainer.train_models_with_cv(
                    fe_result.data,
                    phase,
                    fe_result.metadata,
                    n_outer_splits=5,
                    progress_callback=make_progress(i, n),
                    random_seed=self.config.random_seed,
                    model_families_filter=getattr(self, "model_families_filter", None),
                    cv_curve_source=getattr(self.config, "cv_curve_source", "last_outer_fold"),
                    test_size=getattr(self.config, "test_size", 0.3),
                )
            else:
                train_result = self.trainer.train_models(
                    fe_result.data,
                    phase,
                    fe_result.metadata,
                    progress_callback=make_progress(i, n),
                    random_seed=self.config.random_seed,
                    test_size=getattr(self.config, "test_size", 0.3),
                    model_families_filter=getattr(self, "model_families_filter", None),
                )
            if train_result.success and train_result.data:
                all_results.extend(train_result.data)
                # ROC/CM/calibration/PR tuples already include phase from model_training_wrapper
                for tup in train_result.metadata.get("roc_curves", []):
                    all_roc.append(tup)
                for tup in train_result.metadata.get("confusion_matrices", []):
                    all_cm.append(tup)
                for tup in train_result.metadata.get("calibration_curves", []):
                    all_cal.append(tup)
                for tup in train_result.metadata.get("pr_curves", []):
                    all_pr.append(tup)
                for tup in train_result.metadata.get("feature_importances", []):
                    all_fi.append(tup)
            self.progress_updated.emit((i + 1) / n, f"{phase} done.")
        self.progress_updated.emit(1.0, "All phases complete")
        meta = {
            "phases_run": ALL_PHASES,
            "model_results_count": len(all_results),
            "roc_curves": all_roc,
            "confusion_matrices": all_cm,
            "calibration_curves": all_cal,
            "pr_curves": all_pr,
            "feature_importances": all_fi,
        }
        self.finished_with_result.emit(StepResult(
            success=len(all_results) > 0,
            data=all_results,
            metadata=meta,
        ))


class EngineerAllPhasesWorker(QThread):
    """Worker that runs feature engineering for all phases (no training)."""
    progress_updated = pyqtSignal(float, str)
    finished_with_results = pyqtSignal(dict)  # phase -> {"data": df, "metadata": dict}

    def __init__(self, derived_df, config: PipelineConfig):
        super().__init__()
        self.derived_df = derived_df
        self.config = config
        self.feature_engineer = FeatureEngineeringWrapper()

    def run(self):
        n = len(ALL_PHASES)
        results = {}
        for i, phase in enumerate(ALL_PHASES):
            self.progress_updated.emit((i + 0.0) / n, f"{phase}: engineering...")
            fe_result = self.feature_engineer.engineer_features(
                self.derived_df,
                phase=phase,
                fit_scalers=True,
                use_feature_selection=getattr(self.config, "use_feature_selection", False),
                feature_selection_method=getattr(self.config, "feature_selection_method", "mutual_info"),
                feature_selection_top_k=getattr(self.config, "feature_selection_top_k", 50),
            )
            if fe_result.success and fe_result.data is not None:
                results[phase] = {"data": fe_result.data, "metadata": fe_result.metadata}
            self.progress_updated.emit((i + 1) / n, f"{phase} done.")
        self.progress_updated.emit(1.0, "All phases engineered.")
        self.finished_with_results.emit(results)


class TrainingWorker(QThread):
    """Worker thread for model training (Phase 4)."""
    progress_updated = pyqtSignal(float, str)
    finished_with_result = pyqtSignal(object)  # StepResult

    def __init__(self, trainer: ModelTrainingWrapper, engineered_df, phase: str, feature_metadata: dict, config: PipelineConfig):
        super().__init__()
        self.trainer = trainer
        self.engineered_df = engineered_df
        self.phase = phase
        self.feature_metadata = feature_metadata
        self.config = config

    def run(self):
        def progress_cb(pct, msg):
            self.progress_updated.emit(pct, msg)
        mode = getattr(self.config, "evaluation_mode", "kfold_cv")
        if not mode:
            mode = "kfold_cv" if getattr(self.config, "use_cv_evaluation", True) else "single_split"
        if mode == "repeated_holdout":
            result = self.trainer.train_models_repeated_holdout(
                self.engineered_df,
                self.phase,
                self.feature_metadata,
                n_repeats=getattr(self.config, "n_repeats", 3),
                test_size=getattr(self.config, "test_size", 0.3),
                progress_callback=progress_cb,
                random_seed=self.config.random_seed,
            )
        elif mode == "nested_cv":
            result = self.trainer.train_models_nested_cv(
                self.engineered_df,
                self.phase,
                self.feature_metadata,
                n_outer_splits=5,
                n_inner_splits=3,
                progress_callback=progress_cb,
                random_seed=self.config.random_seed,
                cv_curve_source=getattr(self.config, "cv_curve_source", "last_outer_fold"),
                test_size=getattr(self.config, "test_size", 0.3),
            )
        elif getattr(self.config, "use_cv_evaluation", False):
            result = self.trainer.train_models_with_cv(
                self.engineered_df,
                self.phase,
                self.feature_metadata,
                n_outer_splits=5,
                progress_callback=progress_cb,
                random_seed=self.config.random_seed,
                cv_curve_source=getattr(self.config, "cv_curve_source", "last_outer_fold"),
                test_size=getattr(self.config, "test_size", 0.3),
            )
        else:
            result = self.trainer.train_models(
                self.engineered_df,
                self.phase,
                self.feature_metadata,
                progress_callback=progress_cb,
                random_seed=self.config.random_seed,
                test_size=getattr(self.config, "test_size", 0.3),
            )
        self.finished_with_result.emit(result)


def _aggregate_cv_metrics_from_results(data, metadata):
    """Build k-fold summary dict from ModelResult list when run used CV (n_outer_splits or n_repeats)."""
    if not data or not metadata:
        return None
    if not (metadata.get("n_outer_splits") or metadata.get("n_repeats")):
        return None
    import numpy as np
    from app.pipeline.types import ModelResult
    accs, bas, aucs, f1s = [], [], [], []
    for r in data:
        if not isinstance(r, ModelResult) or r.model_family in ("Baseline-Majority", "Baseline-Random"):
            continue
        accs.append(r.accuracy)
        bas.append(r.balanced_accuracy)
        aucs.append(r.auc)
        f1s.append(r.f1_score)
    if not accs:
        return None
    def mean_std(arr):
        a = np.array(arr, dtype=float)
        m = float(np.mean(a))
        s = float(np.std(a)) if len(a) > 1 else 0.0
        return (m, s)
    return {
        "accuracy": mean_std(accs),
        "balanced_accuracy": mean_std(bas),
        "auc": mean_std(aucs),
        "f1_score": mean_std(f1s),
    }


class PipelineWorker(QThread):
    """Worker thread for running pipeline operations"""

    progress_updated = pyqtSignal(float, str)
    step_completed = pyqtSignal(object)  # StepResult
    finished = pyqtSignal(bool)  # success

    def __init__(
        self,
        orchestrator: PipelineOrchestrator,
        config: PipelineConfig
    ):
        super().__init__()
        self.orchestrator = orchestrator
        self.config = config
        self.loader = DataLoaderWrapper()
        self.target_deriver = TargetDerivationWrapper()
        self.feature_engineer = FeatureEngineeringWrapper()
    
    def run(self):
        """Run data loading and target derivation pipeline"""
        try:
            # Set up callbacks with progress scaling
            self.orchestrator.set_progress_callback(self._on_progress)
            
            # STEP 1: Execute data loading (0-50% progress)
            self._current_step_offset = 0.0
            self._current_step_scale = 0.5
            
            load_result = self.orchestrator.execute_step(
                PipelineStep.LOAD_DATA,
                self.loader.load_data,
                self.config.data_path,
                validate=self.config.validate_data
            )
            
            if not load_result.success:
                self.step_completed.emit(load_result)
                self.finished.emit(False)
                return
            
            # Get the loaded data
            loaded_data = load_result.data
            
            # STEP 2: Execute target derivation (50-100% progress)
            self._current_step_offset = 50.0
            self._current_step_scale = 0.5
            
            derive_result = self.orchestrator.execute_step(
                PipelineStep.DERIVE_TARGETS,
                self.target_deriver.derive_targets,
                loaded_data
            )
            
            # Emit the FINAL result (with derived targets)
            self.step_completed.emit(derive_result)
            self.finished.emit(derive_result.success)
            
        except Exception as e:
            from app.pipeline.types import StepResult
            self.progress_updated.emit(0, f"Error: {str(e)}")
            self.step_completed.emit(StepResult(
                success=False,
                data=None,
                metadata={},
                errors=[f"Pipeline error: {str(e)}"],
                warnings=[],
            ))
            self.finished.emit(False)
    
    def _on_progress(self, percent: float, message: str):
        """Handle progress updates with scaling for multi-step pipeline"""
        # Scale progress based on current step
        # Step 1 (Load): 0-50%, Step 2 (Derive): 50-100%
        scaled_percent = self._current_step_offset + (percent * self._current_step_scale)
        self.progress_updated.emit(scaled_percent, message)


class PipelineRunnerWidget(QWidget):
    """Widget for running pipeline operations and showing progress"""
    
    data_loaded = pyqtSignal(object)  # Emits DataFrame when data is loaded
    features_engineered = pyqtSignal(object, dict)  # Emits (DataFrame, metadata) when features are engineered
    training_results_ready = pyqtSignal(object)  # Emits list of ModelResult when training completes
    training_result_full = pyqtSignal(object, object)  # (list ModelResult, metadata dict) for visualizations
    validation_kfold_ready = pyqtSignal(object)  # Emits dict of k-fold aggregated metrics for Validation Results tab
    
    def __init__(
        self,
        config: PipelineConfig,
        logger: LoggerManager,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self.config = config
        self.logger = logger
        self.orchestrator = PipelineOrchestrator(config, logger)
        self.worker: Optional[PipelineWorker] = None
        self._last_engineered_data = None
        self._last_engineered_metadata = None
        self._last_engineered_phase = None
        self._last_engineered_by_phase: dict = {}  # phase -> (data, metadata)

        self._init_ui()
    
    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Data Loading Section
        data_group = QGroupBox("Data Loading")
        data_layout = QVBoxLayout()
        
        # Data path display - selectable with white text on dark grey
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Data Path:"))
        self.path_field = QLineEdit(self.config.data_path)
        self.path_field.setReadOnly(True)
        self.path_field.setStyleSheet(
            "QLineEdit { "
            "background-color: #2b2b2b; "
            "color: #ffffff; "
            "padding: 5px; "
            "border: 1px solid #555; "
            "font-family: 'Consolas', 'Courier New', monospace; "
            "}"
        )
        path_layout.addWidget(self.path_field, 1)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        path_layout.addWidget(self.browse_btn)
        
        data_layout.addLayout(path_layout)
        
        # Load button and Settings
        button_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load Data")
        self.load_btn.clicked.connect(self._on_load_clicked)
        button_layout.addWidget(self.load_btn)
        self.settings_btn = QPushButton("Settings...")
        self.settings_btn.setToolTip("Random seed and test split for model training")
        self.settings_btn.clicked.connect(self._on_settings_clicked)
        button_layout.addWidget(self.settings_btn)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_btn)
        data_help_btn = QPushButton("?")
        data_help_btn.setFixedSize(22, 22)
        data_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        data_help_btn.setToolTip("Click for explanation")
        data_help_btn.clicked.connect(lambda: QMessageBox.information(
            self,
            "Data Loading",
            "Load the clinical dataset (CSV) that will be used for target derivation, feature engineering, and model training. "
            "Use Browse to select a different file. After loading, run Target Derivation (Pipeline Flow tab) and then "
            "Feature Engineering here.\n\n"
            "Settings... (defaults): random seed 42, test fraction 0.3, evaluation mode Nested CV, feature selection off. "
            "Change these before running Model Training if needed."
        ))
        button_layout.addWidget(data_help_btn)
        button_layout.addStretch()
        
        data_layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        data_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to load data")
        data_layout.addWidget(self.status_label)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # Feature Engineering Section
        feature_group = QGroupBox("Feature Engineering")
        feature_layout = QVBoxLayout()
        
        # Phase selector row with hint
        phase_layout = QHBoxLayout()
        phase_layout.addWidget(QLabel("Phase:"))
        self.phase_combo = QComboBox()
        self.phase_combo.addItems(["All phases", "phase_-6", "phase_0", "phase_15", "phase_30"])
        self.phase_combo.setCurrentIndex(0)  # Default: All phases
        self.phase_combo.currentIndexChanged.connect(self._on_phase_changed)
        phase_layout.addWidget(self.phase_combo)
        fe_hint_btn = QPushButton("?")
        fe_hint_btn.setFixedSize(22, 22)
        fe_hint_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        fe_hint_btn.setToolTip("Click for explanation")
        fe_hint_btn.clicked.connect(lambda: QMessageBox.information(
            self,
            "Feature engineering",
            "Feature engineering prepares the dataset for model training: it selects only columns "
            "available at this timepoint (phase), encodes categorical variables, handles missing values, "
            "and scales numeric features. This ensures models use consistent, phase-appropriate inputs.\n\n"
            "Default selection: Phase = \"All phases\" (engineers phase_-6, phase_0, phase_15, phase_30). "
            "Feature selection (Settings...): off by default; if enabled, method mutual_info, top K 50.\n\n"
            "Why only some features? The full dataset has many columns (~190). Feature engineering uses "
            "only a subset for each phase:\n\n"
            "phase_-6 = baseline (demographics, diagnosis, baseline labs)\n"
            "phase_0 = baseline + Day 0 labs\n"
            "phase_15 = baseline + Day 0 + Day 15 labs\n"
            "phase_30 = all through Day 30\n\n"
            "This avoids data leakage and matches what would be available at that clinical timepoint."
        ))
        phase_layout.addWidget(fe_hint_btn)
        phase_layout.addStretch()
        feature_layout.addLayout(phase_layout)
        
        # Engineer Features button
        fe_btn_layout = QHBoxLayout()
        self.engineer_btn = QPushButton("Run Feature Engineering")
        self.engineer_btn.clicked.connect(self._on_engineer_clicked)
        self.engineer_btn.setEnabled(False)  # Enabled after data is loaded
        fe_btn_layout.addWidget(self.engineer_btn)
        fe_btn_layout.addStretch()
        feature_layout.addLayout(fe_btn_layout)

        # Feature engineering status
        self.feature_status_label = QLabel("Load data first")
        self.feature_status_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        feature_layout.addWidget(self.feature_status_label)
        
        feature_group.setLayout(feature_layout)
        layout.addWidget(feature_group)
        
        # Model Training Section (Phase 4)
        training_group = QGroupBox("Model Training")
        training_layout = QVBoxLayout()
        train_header = QHBoxLayout()
        self.train_btn = QPushButton("Run Model Training")
        self.train_btn.clicked.connect(self._on_train_clicked)
        self.train_btn.setEnabled(False)
        train_header.addWidget(self.train_btn)
        self.run_all_phases_btn = QPushButton("Run all phases")
        self.run_all_phases_btn.setToolTip("Engineer features and train models for phase_-6, phase_0, phase_15, phase_30 at once")
        self.run_all_phases_btn.setEnabled(False)
        self.run_all_phases_btn.clicked.connect(self._on_run_all_phases_clicked)
        train_header.addWidget(self.run_all_phases_btn)
        train_hint_btn = QPushButton("?")
        train_hint_btn.setFixedSize(22, 22)
        train_hint_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        train_hint_btn.setToolTip("Click for explanation")
        train_hint_btn.clicked.connect(lambda: QMessageBox.information(
            self,
            "Model training",
            "Model training fits multiple algorithms (Neural Network, Logistic Regression, Random Forest, "
            "XGBoost, CatBoost, Extra Trees, LightGBM, SVM) and baselines (Majority, Random) on the engineered features for each outcome target.\n\n"
            "Default settings (change in Settings...): evaluation mode Nested CV (recommended for publication), random seed 42, test fraction 0.3 "
            "(used for Single split). Phase: default \"All phases\" for Run all phases; otherwise select a specific phase for Run Model Training.\n\n"
            "Evaluation modes:\n"
            "• Nested CV (default): outer 5-fold for evaluation, inner 3-fold for hyperparameter tuning (LR, RF, XGB); unbiased estimates.\n"
            "• 5-fold CV: stratified 5-fold, fixed hyperparameters; faster, no inner tuning.\n"
            "• Single split: one train/test split; metrics and bootstrap CI in Validation Results.\n"
            "• 3× repeated holdout (default 3 repeats): mean ± std and 95% CI.\n\n"
            "Run Model Training: trains on the selected phase. Run all phases: engineer + train for all four phases. "
            "Results appear in Model Comparison, Visualizations, and Validation Results."
        ))
        train_header.addWidget(train_hint_btn)
        train_header.addStretch()
        # Load saved run: dropdown of all previous results (latest default) + Load button
        self.saved_results_combo = QComboBox()
        self.saved_results_combo.setMinimumWidth(200)
        self.saved_results_combo.setToolTip("Select a saved pipeline run to load (model + training and validation results)")
        train_header.addWidget(QLabel("Saved run:"))
        train_header.addWidget(self.saved_results_combo)
        self.load_saved_results_btn = QPushButton("Load")
        self.load_saved_results_btn.setToolTip("Load the selected run (model results, ROC, confusion matrices → Model Comparison, Visualizations, Validation)")
        self.load_saved_results_btn.clicked.connect(self._on_load_saved_results)
        train_header.addWidget(self.load_saved_results_btn)
        self.retrain_lr_merge_btn = QPushButton("Retrain LR & merge")
        self.retrain_lr_merge_btn.setToolTip("Load selected run, retrain only LR (with class_weight fix), merge LR results into loaded data. Requires: Load data first.")
        self.retrain_lr_merge_btn.clicked.connect(self._on_retrain_lr_merge)
        train_header.addWidget(self.retrain_lr_merge_btn)
        self._refresh_saved_results_combo()
        training_layout.addLayout(train_header)
        self.training_status_label = QLabel("Run feature engineering first")
        self.training_status_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        training_layout.addWidget(self.training_status_label)
        training_group.setLayout(training_layout)
        layout.addWidget(training_group)
        
        # Results Section
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        results_header = QHBoxLayout()
        results_header.addStretch()
        results_help_btn = QPushButton("?")
        results_help_btn.setFixedSize(22, 22)
        results_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        results_help_btn.setToolTip("Click for explanation")
        results_help_btn.clicked.connect(lambda: QMessageBox.information(
            self,
            "Results",
            "This area shows a short log of the latest pipeline steps run in this tab: data load, feature engineering, "
            "and model training. It reports the settings used for each run (e.g. evaluation mode, random seed, phase). "
            "Use it to confirm which phase was engineered, how many features were produced, and whether training completed. "
            "For full metrics and baselines, see the Validation Results and Model Comparison tabs."
        ))
        results_header.addWidget(results_help_btn)
        results_layout.addLayout(results_header)
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        results_layout.addWidget(self.results_text)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        layout.addStretch()
    
    def _on_phase_changed(self):
        """Update train button state when phase selection changes."""
        phase = self.phase_combo.currentText()
        if phase == "All phases":
            self.train_btn.setEnabled(False)
            self.training_status_label.setText("Select a specific phase for single-phase training, or use Run all phases")
            self.training_status_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        else:
            has_data = (
                phase in self._last_engineered_by_phase
                or (self._last_engineered_phase == phase and self._last_engineered_data is not None)
            )
            self.train_btn.setEnabled(has_data)
            if has_data:
                self.training_status_label.setText("Ready to run model training")
                self.training_status_label.setStyleSheet("QLabel { color: #2E7D32; }")
            else:
                self.training_status_label.setText("Run feature engineering first")
                self.training_status_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")

    def _on_browse_clicked(self):
        """Handle browse button click"""
        default_folder = data_dir()
        if not default_folder.exists():
            default_folder = repo_root()

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Clinical Data File",
            str(default_folder),
            "CSV Files (*.csv);;All Files (*.*)"
        )
        
        if file_path:
            self.config.data_path = file_path
            self.path_field.setText(file_path)
            self.logger.info(f"Data path updated to: {file_path}", "PipelineRunner")

    def _on_settings_clicked(self):
        """Open training settings dialog (random seed, test size, evaluation mode). All pipeline training settings are here."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Training settings")
        form = QFormLayout(dlg)
        form.addRow(QLabel("All evaluation and split settings for model training:"))
        seed_spin = QSpinBox()
        seed_spin.setRange(1, 999999)
        seed_spin.setValue(getattr(self.config, "random_seed", 42))
        form.addRow("Random seed:", seed_spin)
        test_spin = QDoubleSpinBox()
        test_spin.setRange(0.1, 0.5)
        test_spin.setSingleStep(0.05)
        test_spin.setDecimals(2)
        test_spin.setValue(getattr(self.config, "test_size", 0.3))
        form.addRow("Test fraction:", test_spin)
        eval_combo = QComboBox()
        eval_combo.addItems([
            "Single split",
            "5-fold CV",
            "3× repeated holdout",
            "Nested CV (5-fold outer)",
        ])
        mode = getattr(self.config, "evaluation_mode", "nested_cv")
        idx = {"single_split": 0, "kfold_cv": 1, "repeated_holdout": 2, "nested_cv": 3}.get(mode, 3)
        eval_combo.setCurrentIndex(idx)
        form.addRow("Evaluation mode:", eval_combo)
        n_repeats_spin = QSpinBox()
        n_repeats_spin.setRange(2, 10)
        n_repeats_spin.setValue(getattr(self.config, "n_repeats", 3))
        n_repeats_spin.setToolTip("Number of independent 70/30 splits for repeated holdout")
        form.addRow("Repeats (holdout):", n_repeats_spin)
        curve_combo = QComboBox()
        curve_combo.addItem("Last outer CV fold (illustrative curves)", "last_outer_fold")
        curve_combo.addItem("Refit stratified holdout (figures only, slower)", "refit_holdout")
        cv_src = getattr(self.config, "cv_curve_source", "last_outer_fold")
        curve_combo.setCurrentIndex(1 if cv_src == "refit_holdout" else 0)
        curve_combo.setToolTip(
            "For nested CV and 5-fold CV: how ROC/confusion/calibration/PR curves are built. "
            "Last fold: one outer fold, fast. Refit: separate train/test split for figures only; CV metrics unchanged."
        )
        form.addRow("CV figure curves:", curve_combo)
        fs_check = QCheckBox("Use feature selection")
        fs_check.setChecked(getattr(self.config, "use_feature_selection", False))
        form.addRow("", fs_check)
        fs_method_combo = QComboBox()
        fs_method_combo.addItems(["mutual_info", "variance"])
        fs_method = getattr(self.config, "feature_selection_method", "mutual_info")
        fs_method_combo.setCurrentIndex(1 if fs_method == "variance" else 0)
        form.addRow("Feature selection method:", fs_method_combo)
        fs_top_k = QSpinBox()
        fs_top_k.setRange(5, 500)
        fs_top_k.setValue(getattr(self.config, "feature_selection_top_k", 50))
        form.addRow("Top K features:", fs_top_k)
        settings_help_btn = QPushButton("?")
        settings_help_btn.setFixedSize(22, 22)
        settings_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        settings_help_btn.setToolTip("Click for explanation")
        settings_help_btn.clicked.connect(lambda: QMessageBox.information(
            dlg,
            "Training settings",
            "Defaults: random seed 42, test fraction 0.3, evaluation mode Nested CV, repeats 3 (holdout), "
            "feature selection off, method mutual_info, top K 50.\n\n"
            "Random seed: Fixes data split and model initialization for reproducibility.\n\n"
            "Test fraction: Fraction of data used as test set (0.1–0.5); only used for Single split mode.\n\n"
            "Evaluation mode:\n"
            "• Nested CV (default; recommended for publication): Outer 5-fold for evaluation, inner 3-fold for hyperparameter tuning (LR, RF, XGB); unbiased estimates.\n"
            "• 5-fold CV: Stratified 5-fold, fixed hyperparameters; faster, no inner tuning.\n"
            "• Single split: One train/test split; reports bootstrap 95% CI for balanced accuracy.\n"
            "• 3× repeated holdout: Independent 70/30 splits (default 3 repeats); mean ± std for stability.\n\n"
            "CV figure curves (nested CV / 5-fold): Last outer fold = fast illustrative ROC/CM/PR; "
            "Refit holdout = extra stratified split for publication-style figures only (does not change CV metrics).\n\n"
            "Feature selection: If enabled, keeps top K features by variance or mutual information (fitted on first primary target) before training."
        ))
        form.addRow("", settings_help_btn)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        form.addRow(btns)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.config.random_seed = seed_spin.value()
            self.config.test_size = test_spin.value()
            text = eval_combo.currentText()
            if text == "Single split":
                self.config.evaluation_mode = "single_split"
                self.config.use_cv_evaluation = False
            elif text == "5-fold CV":
                self.config.evaluation_mode = "kfold_cv"
                self.config.use_cv_evaluation = True
            elif text == "3× repeated holdout":
                self.config.evaluation_mode = "repeated_holdout"
                self.config.use_cv_evaluation = True
            else:
                self.config.evaluation_mode = "nested_cv"
                self.config.use_cv_evaluation = True
            self.config.n_repeats = n_repeats_spin.value()
            self.config.cv_curve_source = curve_combo.currentData()
            self.config.use_feature_selection = fs_check.isChecked()
            self.config.feature_selection_method = fs_method_combo.currentText()
            self.config.feature_selection_top_k = fs_top_k.value()
            self.logger.info(
                f"Settings: random_seed={self.config.random_seed}, test_size={self.config.test_size}, "
                f"evaluation_mode={self.config.evaluation_mode}, use_feature_selection={self.config.use_feature_selection}",
                "PipelineRunner",
            )

    def _on_load_clicked(self):
        """Handle load button click"""
        self.logger.info("Starting data load operation", "PipelineRunner")
        # Reset orchestrator
        self.orchestrator.reset()
        
        # Disable buttons during loading
        self.load_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.engineer_btn.setEnabled(False)
        self.run_all_phases_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Loading...")
        self.feature_status_label.setText("Loading...")
        self.results_text.clear()
        
        # Create and start worker thread
        self.worker = PipelineWorker(self.orchestrator, self.config)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.step_completed.connect(self._on_step_completed)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_cancel_clicked(self):
        """Handle cancel button click"""
        self.logger.warning("Cancelling data load operation", "PipelineRunner")
        self.orchestrator.cancel()
        self.status_label.setText("Cancelling...")
        self.cancel_btn.setEnabled(False)
    
    def _on_progress(self, percent: float, message: str):
        """Handle progress updates"""
        self.progress_bar.setValue(int(percent))
        self.status_label.setText(message)
    
    def _on_step_completed(self, result):
        """Handle step completion"""
        try:
            # Guard against None result
            if result is None:
                self.results_text.setPlainText("[ERROR] No result received from pipeline.")
                return
            meta = result.metadata if result.metadata is not None else {}
        except Exception as e:
            self.logger.error(f"Step completion error: {e}", "PipelineRunner")
            self.results_text.setPlainText(f"[ERROR] Step completion failed: {e}")
            return

        # Emit data if pipeline completed successfully
        # (Load CSV -> Derive Targets)
        if result.success and result.data is not None:
            self.data_loaded.emit(result.data)
        else:
            # Show error in a message box so user sees it (not only in Results panel)
            if result.errors:
                err_text = "\n".join(result.errors[:3])
                if len(result.errors) > 3:
                    err_text += "\n..."
                QMessageBox.warning(
                    self,
                    "Pipeline failed",
                    err_text + "\n\nIf the file was not found, use Browse to select your data file (e.g. unified_clinical_data.csv).",
                )
        
        # Display results
        if result.success:
            results = f"[SUCCESS] Pipeline completed successfully!\n\n"
            results += f"Steps: Load Data → Derive Targets\n\n"
            rows = meta.get('rows', 0)
            cols_total = meta.get('columns', 0)
            cols_original = meta.get('columns_original', cols_total)
            cols_derived = meta.get('columns_derived', 0)
            total_values = meta.get('total_values', 0)
            missing_values = meta.get('missing_values', 0)
            present_values = meta.get('present_values', 0)
            
            results += f"Rows: {rows:,}\n"
            results += f"Columns: {cols_total} ({cols_original} original + {cols_derived} derived)\n"
            results += f"\nOriginal Data Quality:\n"
            results += f"  Total values: {total_values:,}\n"
            results += f"  Present values: {present_values:,}\n"
            results += f"  Missing values: {missing_values:,}\n"
            results += f"  Completeness: {meta.get('completeness', 0):.1f}%\n"
            load_t = meta.get('load_time_sec') or meta.get('derive_time_sec') or meta.get('load_time', 0)
            results += f"\nLoad time: {float(load_t):.2f}s\n"
            
            if result.warnings:
                results += f"\nWarnings ({len(result.warnings)}):\n"
                for warning in result.warnings:
                    results += f"  [WARN] {warning}\n"
        else:
            results = f"[FAILED] Data loading failed!\n\n"
            if result.errors:
                results += "Errors:\n"
                for error in result.errors:
                    results += f"  • {error}\n"
        
        self.results_text.setPlainText(results)
    
    def _on_finished(self, success: bool):
        """Handle operation completion"""
        self.load_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        if success:
            self.status_label.setText("[OK] Data loaded successfully")
            self.engineer_btn.setEnabled(True)
            self.run_all_phases_btn.setEnabled(True)
            self.feature_status_label.setText("Ready to engineer features")
            self.feature_status_label.setStyleSheet("QLabel { color: #2E7D32; }")
            self.logger.info("Data load completed successfully", "PipelineRunner")
        else:
            self.status_label.setText("[FAILED] Data loading failed")
            self.engineer_btn.setEnabled(False)
            self.feature_status_label.setText("Load data first")
            self.feature_status_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
            self.logger.error("Data load failed", "PipelineRunner")
        
        # Get execution summary
        summary = self.orchestrator.get_execution_summary()
        self.logger.info(
            f"Execution summary: {summary['successful_steps']}/{summary['total_steps']} steps completed",
            "PipelineRunner"
        )
    
    def _on_engineer_clicked(self):
        """Handle engineer features button click"""
        selected_phase = self.phase_combo.currentText()
        if selected_phase == "All phases":
            self._on_engineer_all_phases_clicked()
            return
        self.logger.info(f"Starting feature engineering for {selected_phase}", "PipelineRunner")
        
        # Check if we have data from the orchestrator's last step
        if PipelineStep.DERIVE_TARGETS not in self.orchestrator.step_results:
            self.logger.error("No derived data available - load data first", "PipelineRunner")
            self.feature_status_label.setText("Error: Load data first")
            self.feature_status_label.setStyleSheet("QLabel { color: #C62828; }")
            return
        
        derive_result = self.orchestrator.step_results[PipelineStep.DERIVE_TARGETS]
        if not derive_result.success or derive_result.data is None:
            self.logger.error("Derived data is not available", "PipelineRunner")
            return
        
        # Disable buttons during engineering
        self.engineer_btn.setEnabled(False)
        self.load_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.feature_status_label.setText(f"Engineering features for {selected_phase}...")
        self.feature_status_label.setStyleSheet("QLabel { color: #1976D2; }")
        
        # Run feature engineering
        if not hasattr(self, 'worker') or self.worker is None:
            self.worker = PipelineWorker(self.orchestrator, self.config)
        
        engineer = self.worker.feature_engineer
        
        def progress_callback(pct, msg):
            self.progress_bar.setValue(int(pct * 100))
            self.feature_status_label.setText(f"{selected_phase}: {msg}")
        
        result = engineer.engineer_features(
            derive_result.data,
            phase=selected_phase,
            fit_scalers=True,
            progress_callback=progress_callback,
            use_feature_selection=getattr(self.config, "use_feature_selection", False),
            feature_selection_method=getattr(self.config, "feature_selection_method", "mutual_info"),
            feature_selection_top_k=getattr(self.config, "feature_selection_top_k", 50),
        )
        
        # Re-enable buttons
        self.engineer_btn.setEnabled(True)
        self.load_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        
        if result.success:
            self.feature_status_label.setText(f"✓ Feature engineering completed! ({result.metadata['feature_count']} features)")
            self.feature_status_label.setStyleSheet("QLabel { color: #2E7D32; }")
            self.logger.info(f"Feature engineering completed: {result.metadata['feature_count']} features", "PipelineRunner")
            
            self._last_engineered_data = result.data
            self._last_engineered_metadata = result.metadata
            self._last_engineered_phase = selected_phase
            self._last_engineered_by_phase[selected_phase] = (result.data, result.metadata)
            self.train_btn.setEnabled(True)
            self.training_status_label.setText("Ready to run model training")
            self.training_status_label.setStyleSheet("QLabel { color: #2E7D32; }")
            self.features_engineered.emit(result.data, result.metadata)
            
            # Update results display
            results = f"\n[SUCCESS] Feature Engineering completed!\n\n"
            results += f"Phase: {selected_phase}\n"
            results += f"Features: {result.metadata['feature_count']}\n"
            results += f"  - Categorical: {result.metadata.get('categorical_count', 0)}\n"
            results += f"  - Numeric: {result.metadata.get('numeric_count', 0)}\n"
            results += f"Engineering time: {result.metadata.get('engineering_time_sec', 0):.3f}s\n"
            self.results_text.append(results)
        else:
            self.feature_status_label.setText("Feature engineering failed")
            self.feature_status_label.setStyleSheet("QLabel { color: #C62828; }")
            self.train_btn.setEnabled(False)
            self.training_status_label.setText("Run feature engineering first")
            self.logger.error("Feature engineering failed", "PipelineRunner")
            if result.errors:
                self.results_text.append(f"\n[ERROR] {result.errors[0]}")

    def _on_engineer_all_phases_clicked(self):
        """Run feature engineering for all four phases (no training)."""
        if PipelineStep.DERIVE_TARGETS not in self.orchestrator.step_results:
            self.logger.error("No derived data - load data first", "PipelineRunner")
            self.feature_status_label.setText("Error: Load data first")
            return
        derive_result = self.orchestrator.step_results[PipelineStep.DERIVE_TARGETS]
        if not derive_result.success or derive_result.data is None:
            return
        self.logger.info("Starting Engineer all phases", "PipelineRunner")
        self.engineer_btn.setEnabled(False)
        self.load_btn.setEnabled(False)
        self.run_all_phases_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.feature_status_label.setText("Engineering all phases...")
        self.feature_status_label.setStyleSheet("QLabel { color: #1976D2; }")

        self._engineer_all_worker = EngineerAllPhasesWorker(derive_result.data, self.config)
        self._engineer_all_worker.progress_updated.connect(self._on_engineer_all_progress)
        self._engineer_all_worker.finished_with_results.connect(self._on_engineer_all_phases_finished)
        self._engineer_all_worker.start()

    def _on_engineer_all_progress(self, pct: float, msg: str):
        self.progress_bar.setValue(int(pct * 100))
        self.feature_status_label.setText(msg)

    def _on_engineer_all_phases_finished(self, results: dict):
        """Store per-phase results; set main phase to phase_15; enable training."""
        self.engineer_btn.setEnabled(True)
        self.load_btn.setEnabled(True)
        self.run_all_phases_btn.setEnabled(True)
        self._last_engineered_by_phase = {}
        for phase, entry in results.items():
            if isinstance(entry, dict) and "data" in entry and "metadata" in entry:
                self._last_engineered_by_phase[phase] = (entry["data"], entry["metadata"])
        # Set default for single-phase training to phase_15 (main focus)
        main_phase = "phase_15" if "phase_15" in self._last_engineered_by_phase else next(iter(self._last_engineered_by_phase), None)
        if main_phase:
            self._last_engineered_data, self._last_engineered_metadata = self._last_engineered_by_phase[main_phase]
            self._last_engineered_phase = main_phase
        self.progress_bar.setValue(100)
        self.feature_status_label.setText(f"✓ All phases engineered ({len(self._last_engineered_by_phase)} phases)")
        self.feature_status_label.setStyleSheet("QLabel { color: #2E7D32; }")
        self._on_phase_changed()  # Update train button based on phase selection
        # Emit for Feature Analysis (use main phase)
        if main_phase and self._last_engineered_metadata:
            self.features_engineered.emit(self._last_engineered_data, self._last_engineered_metadata)
        summary = ", ".join(f"{p}({self._last_engineered_by_phase[p][1].get('feature_count', '?')} feats)" for p in sorted(self._last_engineered_by_phase.keys()))
        self.results_text.append(f"\n[SUCCESS] Engineer all phases completed.\nPhases: {summary}\n")

    def _on_train_clicked(self):
        """Handle Run Model Training button click."""
        phase = self.phase_combo.currentText()
        if phase == "All phases":
            self.logger.error("Select a specific phase for single-phase training, or use Run all phases", "PipelineRunner")
            return
        # Prefer per-phase cache from "Engineer all phases"
        if phase in self._last_engineered_by_phase:
            data, meta = self._last_engineered_by_phase[phase]
        elif self._last_engineered_phase == phase and self._last_engineered_data is not None:
            data, meta = self._last_engineered_data, self._last_engineered_metadata
        else:
            self.logger.error("No engineered data for this phase; run feature engineering first", "PipelineRunner")
            return
        self.logger.info(f"Starting model training for {phase}", "PipelineRunner")
        self.train_btn.setEnabled(False)
        self.load_btn.setEnabled(False)
        self.retrain_lr_merge_btn.setEnabled(False)
        self.engineer_btn.setEnabled(False)
        self.run_all_phases_btn.setEnabled(False)
        self.training_status_label.setText(f"Training models for {phase}...")
        self.training_status_label.setStyleSheet("QLabel { color: #1976D2; }")

        self._training_worker = TrainingWorker(
            ModelTrainingWrapper(),
            data,
            phase,
            meta,
            self.config,
        )
        self._training_worker.progress_updated.connect(self._on_training_progress)
        self._training_worker.finished_with_result.connect(self._on_training_finished)
        self._training_worker.start()

    def _on_training_progress(self, pct: float, msg: str):
        """Update progress bar and status during training."""
        self.progress_bar.setValue(int(pct * 100))
        self.training_status_label.setText(msg)

    def _on_training_finished(self, result):
        """Handle training worker completion."""
        self.train_btn.setEnabled(True)
        self.load_btn.setEnabled(True)
        self.retrain_lr_merge_btn.setEnabled(True)
        self.engineer_btn.setEnabled(True)
        self.run_all_phases_btn.setEnabled(True)
        if result.success:
            self.progress_bar.setValue(100)
            self.training_status_label.setText(
                f"Training complete: {len(result.data)} model results"
            )
            self.training_status_label.setStyleSheet("QLabel { color: #2E7D32; }")
            self._save_training_result(result)
            self.training_results_ready.emit(result.data)
            self.training_result_full.emit(result.data, result.metadata)
            agg = _aggregate_cv_metrics_from_results(result.data, result.metadata)
            if agg:
                self.validation_kfold_ready.emit(agg)
            self.results_text.append(
                f"\n[SUCCESS] Model training completed.\n"
                f"Phase: {result.metadata.get('phase', '')}\n"
                f"Results: {len(result.data)} (target x model)\n"
                f"Time: {result.metadata.get('training_time_sec', 0):.1f}s\n"
            )
        else:
            self.training_status_label.setText("Training failed")
            self.training_status_label.setStyleSheet("QLabel { color: #C62828; }")
            if result.errors:
                self.results_text.append(f"\n[ERROR] Training: {result.errors[0]}")

    def _on_run_all_phases_clicked(self):
        """Run feature engineering + model training for all phases (phase_-6, phase_0, phase_15, phase_30)."""
        if PipelineStep.DERIVE_TARGETS not in self.orchestrator.step_results:
            self.logger.error("No derived data - load data first", "PipelineRunner")
            self.training_status_label.setText("Error: Load data first")
            return
        derive_result = self.orchestrator.step_results[PipelineStep.DERIVE_TARGETS]
        if not derive_result.success or derive_result.data is None:
            self.logger.error("Derived data not available", "PipelineRunner")
            return
        self.logger.info("Starting Run all phases (engineer + train for each phase)", "PipelineRunner")
        self.train_btn.setEnabled(False)
        self.load_btn.setEnabled(False)
        self.retrain_lr_merge_btn.setEnabled(False)
        self.engineer_btn.setEnabled(False)
        self.run_all_phases_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.training_status_label.setText("Running all phases...")
        self.training_status_label.setStyleSheet("QLabel { color: #1976D2; }")

        self._all_phases_worker = AllPhasesWorker(derive_result.data, self.config)
        self._all_phases_worker.progress_updated.connect(self._on_training_progress)
        self._all_phases_worker.finished_with_result.connect(self._on_all_phases_finished)
        self._all_phases_worker.start()

    def _on_all_phases_finished(self, result):
        """Handle Run all phases worker completion; same as single-phase training finish."""
        self.train_btn.setEnabled(True)
        self.load_btn.setEnabled(True)
        self.retrain_lr_merge_btn.setEnabled(True)
        self.engineer_btn.setEnabled(True)
        self.run_all_phases_btn.setEnabled(True)
        if result.success:
            self.progress_bar.setValue(100)
            phases_run = result.metadata.get("phases_run", ALL_PHASES)
            self.training_status_label.setText(
                f"All phases complete: {len(result.data)} model results ({', '.join(phases_run)})"
            )
            self.training_status_label.setStyleSheet("QLabel { color: #2E7D32; }")
            self._save_training_result(result)
            self.training_results_ready.emit(result.data)
            self.training_result_full.emit(result.data, result.metadata)
            agg = _aggregate_cv_metrics_from_results(result.data, result.metadata)
            if agg:
                self.validation_kfold_ready.emit(agg)
            self.results_text.append(
                f"\n[SUCCESS] Run all phases completed.\n"
                f"Phases: {', '.join(phases_run)}\n"
                f"Results: {len(result.data)} (target x model x phase)\n"
            )
        else:
            self.training_status_label.setText("Run all phases failed")
            self.training_status_label.setStyleSheet("QLabel { color: #C62828; }")
            if result.errors:
                self.results_text.append(f"\n[ERROR] Run all phases: {result.errors[0]}")

    def _save_training_result(self, result) -> None:
        """Save to results/runs/ and refresh results/latest/training_results.pkl."""
        try:
            RESULTS_DIR.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            path = RESULTS_DIR / f"{TRAINING_RESULTS_PREFIX}{stamp}.pkl"
            payload = {"data": result.data, "metadata": result.metadata}
            with open(path, "wb") as f:
                pickle.dump(payload, f)
            latest_dir = results_latest_dir()
            latest_dir.mkdir(parents=True, exist_ok=True)
            latest_path = latest_dir / LATEST_TRAINING_FILENAME
            shutil.copy2(path, latest_path)
            self.logger.info(f"Saved training results to {path}", "PipelineRunner")
            try:
                rel = latest_path.relative_to(repo_root())
            except ValueError:
                rel = latest_path
            self.results_text.append(f"  Saved: {path.name} (also → {rel})\n")
            self._refresh_saved_results_combo()
        except Exception as e:
            self.logger.error(f"Failed to save training results: {e}", "PipelineRunner")

    def _refresh_saved_results_combo(self) -> None:
        """Populate dropdown with all saved pipeline runs (newest first); latest is default."""
        self.saved_results_combo.clear()
        files_ordered = iter_saved_run_paths_ordered()
        if not files_ordered:
            self.saved_results_combo.addItem("No saved runs yet", None)
            return
        for path in files_ordered:
            label = format_saved_result_label(path)
            self.saved_results_combo.addItem(label, str(path))

    def _on_load_saved_results(self) -> None:
        """Load the selected saved run and emit to Model Comparison, Visualizations, Validation."""
        try:
            path_str = self.saved_results_combo.currentData()
            if not path_str:
                QMessageBox.information(
                    self,
                    "Load saved results",
                    "No saved run selected. Run Model Training or Run all phases first; results are saved automatically.",
                )
                return
            path = Path(path_str)
            if not path.exists():
                QMessageBox.warning(self, "Load saved results", f"File no longer exists: {path.name}")
                self._refresh_saved_results_combo()
                return
            with open(path, "rb") as f:
                payload = pickle.load(f)
            data = payload.get("data", [])
            metadata = payload.get("metadata", {})
            if not data:
                QMessageBox.warning(self, "Load saved results", "Saved file has no model results.")
                return
            self.training_results_ready.emit(data)
            self.training_result_full.emit(data, metadata)
            self.training_status_label.setText(f"Loaded {path.name}: {len(data)} results")
            self.training_status_label.setStyleSheet("QLabel { color: #2E7D32; }")
            self.results_text.append(f"\n[LOADED] {path.name} — {len(data)} model results.\n")
        except Exception as e:
            self.logger.error(f"Load saved results failed: {e}", "PipelineRunner")
            QMessageBox.warning(self, "Load saved results", f"Could not load: {e}")

    def _on_retrain_lr_merge(self) -> None:
        """Load selected run, retrain LR only (all phases), merge LR results into loaded data, emit."""
        if PipelineStep.DERIVE_TARGETS not in self.orchestrator.step_results:
            QMessageBox.warning(
                self, "Retrain LR & merge",
                "Load data first. Click 'Load Data' to derive targets, then try again.",
            )
            return
        derive_result = self.orchestrator.step_results[PipelineStep.DERIVE_TARGETS]
        if not derive_result.success or derive_result.data is None:
            QMessageBox.warning(self, "Retrain LR & merge", "Derived data not available. Load data first.")
            return
        path_str = self.saved_results_combo.currentData()
        if not path_str:
            QMessageBox.warning(
                self, "Retrain LR & merge",
                "Select a saved run from the dropdown first.",
            )
            return
        path = Path(path_str)
        if not path.exists():
            QMessageBox.warning(self, "Retrain LR & merge", f"File no longer exists: {path.name}")
            self._refresh_saved_results_combo()
            return
        try:
            with open(path, "rb") as f:
                payload = pickle.load(f)
            loaded_data = payload.get("data", [])
            loaded_meta = payload.get("metadata", {})
        except Exception as e:
            QMessageBox.warning(self, "Retrain LR & merge", f"Could not load: {e}")
            return
        if not loaded_data:
            QMessageBox.warning(self, "Retrain LR & merge", "Saved file has no model results.")
            return
        self.retrain_lr_merge_btn.setEnabled(False)
        self.load_saved_results_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.training_status_label.setText("Retraining LR only (merge into loaded)...")
        self.training_status_label.setStyleSheet("QLabel { color: #1976D2; }")
        self._retrain_lr_worker = AllPhasesWorker(
            derive_result.data,
            self.config,
            model_families_filter=["LR"],
        )
        self._retrain_lr_worker._loaded_data = loaded_data
        self._retrain_lr_worker._loaded_meta = loaded_meta
        self._retrain_lr_worker._merge_source_path = path
        self._retrain_lr_worker.progress_updated.connect(self._on_training_progress)
        self._retrain_lr_worker.finished_with_result.connect(self._on_retrain_lr_merge_finished)
        self._retrain_lr_worker.start()

    def _on_retrain_lr_merge_finished(self, result) -> None:
        """Merge new LR results into loaded data and emit."""
        self.retrain_lr_merge_btn.setEnabled(True)
        self.load_saved_results_btn.setEnabled(True)
        worker = self.sender()
        loaded_data = getattr(worker, "_loaded_data", [])
        loaded_meta = getattr(worker, "_loaded_meta", {})
        path = getattr(worker, "_merge_source_path", None)
        if not result.success or not result.data:
            self.training_status_label.setText("LR retrain failed")
            self.training_status_label.setStyleSheet("QLabel { color: #C62828; }")
            if result.errors:
                self.results_text.append(f"\n[ERROR] Retrain LR: {result.errors[0]}\n")
            return
        from app.pipeline.types import ModelResult
        merged = [r for r in loaded_data if r.model_family != "LR"]
        new_lr = [r for r in result.data if r.model_family == "LR"]
        merged.extend(new_lr)
        self.training_results_ready.emit(merged)
        self.training_result_full.emit(merged, loaded_meta)
        agg = _aggregate_cv_metrics_from_results(merged, loaded_meta)
        if agg:
            self.validation_kfold_ready.emit(agg)
        self.training_status_label.setText(f"LR updated: {len(new_lr)} results merged into {path.name if path else 'loaded'}")
        self.training_status_label.setStyleSheet("QLabel { color: #2E7D32; }")
        self.results_text.append(
            f"\n[LR MERGE] Retrained LR (class_weight=balanced), merged {len(new_lr)} results into loaded run.\n"
        )