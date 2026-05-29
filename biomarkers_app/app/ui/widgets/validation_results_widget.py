"""Validation Results tab: train/test split info and validation metrics."""

from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QTextEdit, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QMessageBox, QFrame,
)
from PyQt6.QtCore import Qt

from app.core.logger_manager import LoggerManager
from app.pipeline.types import ModelResult

# Help text for ? buttons
HELP_CURRENT_VALIDATION = (
    "Current validation (model training)\n\n"
    "This section shows the train/test split used by the pipeline when you run Model Training or Run all phases. "
    "A single stratified split (e.g. 70% train / 30% test) is applied; the random seed ensures reproducibility. "
    "Metrics below are computed on the held-out test set. Stratification keeps class proportions similar in train and test."
)

HELP_VALIDATION_STRATEGY = (
    "Validation strategy\n\n"
    "The app supports multiple validation approaches:\n\n"
    "• Train/test split (implemented): One random split; fast, simple. Good for development and quick checks.\n\n"
    "• K-fold CV (implemented): Data is split into K folds; each fold serves as test set once. "
    "Reduces variance and gives mean ± std of metrics. Use 'Run k-fold CV' in Pipeline Flow.\n\n"
    "• Bootstrap CI (implemented): After training, the test set is resampled with replacement many times "
    "to estimate confidence intervals (e.g. 95% CI) for metrics. Run Model Training to see bootstrap CIs here.\n\n"
    "Planned: Nested CV, temporal/cohort holdout for external validation."
)

HELP_TRAIN_TEST = (
    "Train/test split metrics\n\n"
    "Aggregated performance (mean ± std across all trained models) on the single held-out test set. "
    "Run Model Training or Run all phases to populate this section."
)

HELP_KFOLD = (
    "K-fold cross-validation\n\n"
    "Stratified K-fold splits the data into K parts; each part is used as test set once while the rest train the model. "
    "Reported metrics are mean ± std across folds, giving a more stable estimate than a single split. "
    "Use the 'Run k-fold CV' button in Pipeline Flow (Model Training section) to run 5-fold CV for the selected phase."
)

HELP_BOOTSTRAP = (
    "Bootstrap confidence intervals\n\n"
    "After training, the test set is resampled with replacement (e.g. 200 times). "
    "For each resample, the metric (e.g. balanced accuracy) is computed. "
    "The 2.5% and 97.5% percentiles give a 95% confidence interval. "
    "Run Model Training or Run all phases to see bootstrap CIs here (computed automatically)."
)

HELP_BASELINE_COMPARISON = (
    "Model vs baseline (Block B)\n\n"
    "For each target and phase, this table shows:\n"
    "• Majority BA: balanced accuracy of the majority-class baseline (always predict the most frequent class).\n"
    "• Best Model: the trained model with highest balanced accuracy.\n"
    "• Best BA: that model's balanced accuracy (with ± std when from 5-fold CV).\n"
    "• Δ vs Majority: Best BA − Majority BA; positive means the model beats the baseline (with ± std when from CV).\n"
    "• Beat Majority: Yes if the best model beats the majority baseline; No otherwise.\n\n"
    "Reporting when a model does not beat majority is required for transparent publication."
)

HELP_TARGET_SUMMARY = (
    "Class balance (target summary, Block C)\n\n"
    "For each outcome target this table shows:\n"
    "• N total: number of evaluable samples used for training/evaluation.\n"
    "• Class counts: count per class (e.g. cls0: 55, cls1: 25).\n"
    "• Gate filtered: Yes if only evaluable patients were included (e.g. D30 response uses D30 evaluable gate).\n\n"
    "Use this to judge whether low performance may be due to very small classes or imbalance."
)


def _aggregate_metrics(results: List[ModelResult]) -> dict:
    """Compute mean and std for accuracy, balanced_accuracy, auc, f1 across results."""
    if not results:
        return {}
    n = len(results)
    acc = [r.accuracy for r in results]
    ba = [r.balanced_accuracy for r in results]
    auc = [r.auc for r in results]
    f1 = [r.f1_score for r in results]
    sample_sizes = [r.sample_size for r in results if r.sample_size > 0]

    def mean_std(vals):
        m = sum(vals) / n
        var = sum((x - m) ** 2 for x in vals) / n if n > 1 else 0
        return m, (var ** 0.5) if var > 0 else 0.0

    acc_m, acc_s = mean_std(acc)
    ba_m, ba_s = mean_std(ba)
    auc_m, auc_s = mean_std(auc)
    f1_m, f1_s = mean_std(f1)

    return {
        "n_models": n,
        "accuracy": (acc_m, acc_s),
        "balanced_accuracy": (ba_m, ba_s),
        "auc": (auc_m, auc_s),
        "f1_score": (f1_m, f1_s),
        "sample_size": sample_sizes[-1] if sample_sizes else 0,
    }


class ValidationResultsWidget(QWidget):
    """Tab for validation strategy and results (train/test, future: k-fold, bootstrap)."""

    def __init__(self, logger: LoggerManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = logger
        self._results: List[ModelResult] = []
        self._init_ui()

    def _add_help_button(self, parent_layout: QHBoxLayout, title: str, help_text: str) -> None:
        """Add a ? button that shows help_text in a message box."""
        btn = QPushButton("?")
        btn.setFixedSize(22, 22)
        btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        btn.setToolTip("Click for explanation")
        btn.clicked.connect(lambda: QMessageBox.information(self, title, help_text))
        parent_layout.addWidget(btn)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Current validation (from pipeline)
        current_group = QGroupBox("Current validation (model training)")
        current_header = QHBoxLayout()
        current_header.addStretch()
        self._add_help_button(current_header, "Current validation", HELP_CURRENT_VALIDATION)
        current_layout = QVBoxLayout()
        current_layout.addLayout(current_header)
        self.split_info = QTextEdit()
        self.split_info.setReadOnly(True)
        self.split_info.setMaximumHeight(120)
        self.split_info.setPlaceholderText(
            "Run model training from Pipeline Flow to see train/test split details here."
        )
        current_layout.addWidget(self.split_info)
        current_group.setLayout(current_layout)
        layout.addWidget(current_group)

        # Validation strategy
        strategy_group = QGroupBox("Validation strategy")
        strategy_header = QHBoxLayout()
        strategy_header.addStretch()
        self._add_help_button(strategy_header, "Validation strategy", HELP_VALIDATION_STRATEGY)
        strategy_layout = QVBoxLayout()
        strategy_layout.addLayout(strategy_header)
        strategy_text = QLabel(
            "Model training uses a single stratified train/test split (default 70/30). "
            "K-fold CV and bootstrap CI are available; run from Pipeline Flow. "
            "Planned: nested CV, temporal/cohort holdout for external validation."
        )
        strategy_text.setWordWrap(True)
        strategy_text.setStyleSheet("QLabel { color: #444; padding: 8px; }")
        strategy_layout.addWidget(strategy_text)
        strategy_group.setLayout(strategy_layout)
        layout.addWidget(strategy_group)

        # Validation metrics (train/test, k-fold, bootstrap)
        metrics_group = QGroupBox("Validation metrics")
        metrics_header = QHBoxLayout()
        metrics_header.addStretch()
        self._add_help_button(metrics_header, "Validation metrics", HELP_TRAIN_TEST)
        metrics_layout = QVBoxLayout()
        metrics_layout.addLayout(metrics_header)

        # Train/test summary table
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.metrics_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.metrics_table.setMaximumHeight(180)
        self.metrics_table.setAlternatingRowColors(True)
        self._populate_metrics_placeholder()
        metrics_layout.addWidget(self.metrics_table)

        # Method status rows with ? for each
        status_layout = QGridLayout()
        row = 0
        status_layout.addWidget(QLabel("Train/test split:"), row, 0)
        self.train_test_label = QLabel("—")
        self.train_test_label.setStyleSheet("QLabel { color: #444; }")
        status_layout.addWidget(self.train_test_label, row, 1)
        train_test_help = QPushButton("?")
        train_test_help.setFixedSize(22, 22)
        train_test_help.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        train_test_help.setToolTip("Click for explanation")
        train_test_help.clicked.connect(lambda: QMessageBox.information(self, "Train/test split", HELP_TRAIN_TEST))
        status_layout.addWidget(train_test_help, row, 2)
        row += 1
        status_layout.addWidget(QLabel("k-fold CV:"), row, 0)
        self.kfold_label = QLabel("N/A — run Model Training or Run all phases (CV mode in Settings)")
        self.kfold_label.setStyleSheet("QLabel { color: #888; }")
        status_layout.addWidget(self.kfold_label, row, 1)
        kfold_help = QPushButton("?")
        kfold_help.setFixedSize(22, 22)
        kfold_help.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        kfold_help.setToolTip("Click for explanation")
        kfold_help.clicked.connect(lambda: QMessageBox.information(self, "K-fold CV", HELP_KFOLD))
        status_layout.addWidget(kfold_help, row, 2)
        row += 1
        status_layout.addWidget(QLabel("Bootstrap CI:"), row, 0)
        self.bootstrap_label = QLabel("N/A — run Model Training")
        self.bootstrap_label.setStyleSheet("QLabel { color: #888; }")
        status_layout.addWidget(self.bootstrap_label, row, 1)
        bootstrap_help = QPushButton("?")
        bootstrap_help.setFixedSize(22, 22)
        bootstrap_help.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        bootstrap_help.setToolTip("Click for explanation")
        bootstrap_help.clicked.connect(lambda: QMessageBox.information(self, "Bootstrap CI", HELP_BOOTSTRAP))
        status_layout.addWidget(bootstrap_help, row, 2)
        metrics_layout.addLayout(status_layout)

        # K-fold summary (when available)
        self.kfold_frame = QFrame()
        self.kfold_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        kfold_inner = QVBoxLayout(self.kfold_frame)
        kfold_inner.addWidget(QLabel("K-fold CV summary (mean ± std across folds):"))
        self.kfold_table = QTableWidget()
        self.kfold_table.setColumnCount(2)
        self.kfold_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.kfold_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.kfold_table.setMaximumHeight(120)
        self.kfold_table.setRowCount(0)
        kfold_inner.addWidget(self.kfold_table)
        metrics_layout.addWidget(self.kfold_frame)
        self.kfold_frame.setVisible(False)

        # Bootstrap summary (when available)
        self.bootstrap_frame = QFrame()
        self.bootstrap_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        bootstrap_inner = QVBoxLayout(self.bootstrap_frame)
        bootstrap_inner.addWidget(QLabel("Bootstrap 95% CI (balanced accuracy):"))
        self.bootstrap_table = QTableWidget()
        self.bootstrap_table.setColumnCount(3)
        self.bootstrap_table.setHorizontalHeaderLabels(["Model", "Mean", "95% CI"])
        self.bootstrap_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.bootstrap_table.setMaximumHeight(120)
        self.bootstrap_table.setRowCount(0)
        bootstrap_inner.addWidget(self.bootstrap_table)
        metrics_layout.addWidget(self.bootstrap_frame)
        self.bootstrap_frame.setVisible(False)

        # Block B2: Model vs baseline
        self.baseline_comparison_frame = QFrame()
        self.baseline_comparison_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        bc_inner = QVBoxLayout(self.baseline_comparison_frame)
        bc_header = QHBoxLayout()
        bc_header.addWidget(QLabel("Model vs baseline (per target/phase):"))
        bc_help = QPushButton("?")
        bc_help.setFixedSize(22, 22)
        bc_help.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        bc_help.setToolTip("Click for explanation")
        bc_help.clicked.connect(lambda: QMessageBox.information(self, "Model vs baseline", HELP_BASELINE_COMPARISON))
        bc_header.addWidget(bc_help)
        bc_header.addStretch()
        bc_inner.addLayout(bc_header)
        self.baseline_comparison_table = QTableWidget()
        self.baseline_comparison_table.setColumnCount(7)
        self.baseline_comparison_table.setHorizontalHeaderLabels(
            ["Target", "Phase", "Majority BA", "Best Model", "Best BA", "Δ vs Majority", "Beat Majority"]
        )
        self.baseline_comparison_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.baseline_comparison_table.setMaximumHeight(150)
        self.baseline_comparison_table.setRowCount(0)
        bc_inner.addWidget(self.baseline_comparison_table)
        metrics_layout.addWidget(self.baseline_comparison_frame)
        self.baseline_comparison_frame.setVisible(False)

        # Block C3: Class balance (target summary)
        self.target_summary_frame = QFrame()
        self.target_summary_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        ts_inner = QVBoxLayout(self.target_summary_frame)
        ts_header = QHBoxLayout()
        ts_header.addWidget(QLabel("Class balance (target summary):"))
        ts_help = QPushButton("?")
        ts_help.setFixedSize(22, 22)
        ts_help.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        ts_help.setToolTip("Click for explanation")
        ts_help.clicked.connect(lambda: QMessageBox.information(self, "Class balance", HELP_TARGET_SUMMARY))
        ts_header.addWidget(ts_help)
        ts_header.addStretch()
        ts_inner.addLayout(ts_header)
        self.target_summary_table = QTableWidget()
        self.target_summary_table.setColumnCount(5)
        self.target_summary_table.setHorizontalHeaderLabels(
            ["Target", "Phase", "N total", "Class counts", "Gate filtered"]
        )
        self.target_summary_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.target_summary_table.setMaximumHeight(150)
        self.target_summary_table.setRowCount(0)
        ts_inner.addWidget(self.target_summary_table)
        metrics_layout.addWidget(self.target_summary_frame)
        self.target_summary_frame.setVisible(False)

        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)

        layout.addStretch()

    def _populate_metrics_placeholder(self) -> None:
        """Set metrics table to placeholder state when no results."""
        self.metrics_table.setRowCount(4)
        for row, (metric, val) in enumerate([
            ("Accuracy", "—"),
            ("Balanced Accuracy", "—"),
            ("AUC", "—"),
            ("F1 Score", "—"),
        ]):
            self.metrics_table.setItem(row, 0, QTableWidgetItem(metric))
            self.metrics_table.setItem(row, 1, QTableWidgetItem(val))

    def set_split_info(self, test_fraction: float, random_seed: int) -> None:
        """Update the train/test split info (e.g. from pipeline config)."""
        train_pct = (1.0 - test_fraction) * 100
        test_pct = test_fraction * 100
        self.split_info.setPlainText(
            f"Train/test split: {train_pct:.0f}% / {test_pct:.0f}%\n"
            f"Random seed: {random_seed}\n"
            "Stratified by target where possible."
        )

    def set_validation_metrics(self, results: List[ModelResult]) -> None:
        """Update validation metrics from training results (train/test split)."""
        self._results = results if results else []
        if not self._results:
            self._populate_metrics_placeholder()
            self.train_test_label.setText("—")
            return

        agg = _aggregate_metrics(self._results)
        if not agg:
            self._populate_metrics_placeholder()
            self.train_test_label.setText("—")
            return

        # Update metrics table
        def fmt(m, s):
            return f"{m:.3f} ± {s:.3f}" if s > 0 else f"{m:.3f}"

        self.metrics_table.setRowCount(5)
        self.metrics_table.setItem(0, 0, QTableWidgetItem("Accuracy"))
        self.metrics_table.setItem(0, 1, QTableWidgetItem(fmt(*agg["accuracy"])))
        self.metrics_table.setItem(1, 0, QTableWidgetItem("Balanced Accuracy"))
        self.metrics_table.setItem(1, 1, QTableWidgetItem(fmt(*agg["balanced_accuracy"])))
        self.metrics_table.setItem(2, 0, QTableWidgetItem("AUC"))
        self.metrics_table.setItem(2, 1, QTableWidgetItem(fmt(*agg["auc"])))
        self.metrics_table.setItem(3, 0, QTableWidgetItem("F1 Score"))
        self.metrics_table.setItem(3, 1, QTableWidgetItem(fmt(*agg["f1_score"])))
        n_info = f"{agg['n_models']} models"
        if agg.get("sample_size"):
            n_info += f", n={agg['sample_size']}"
        self.metrics_table.setItem(4, 0, QTableWidgetItem("Summary"))
        self.metrics_table.setItem(4, 1, QTableWidgetItem(n_info))

        self.train_test_label.setText(f"OK ({agg['n_models']} results)")
        self.train_test_label.setStyleSheet("QLabel { color: #2E7D32; }")
        self._refresh_baseline_comparison()

    def _refresh_baseline_comparison(self) -> None:
        """Block B2: Fill Model vs baseline table from self._results."""
        if not self._results:
            self.baseline_comparison_frame.setVisible(False)
            return
        key_to_majority: Dict[tuple, float] = {}
        key_to_best: Dict[tuple, tuple] = {}  # (model_family, ba, ba_std)
        for r in self._results:
            key = (r.target, r.phase)
            if r.model_family == "Baseline-Majority":
                key_to_majority[key] = r.balanced_accuracy
            if r.model_family not in ("Baseline-Majority", "Baseline-Random"):
                ba_std = getattr(r, "balanced_accuracy_std", 0.0) or 0.0
                if key not in key_to_best or r.balanced_accuracy > key_to_best[key][1]:
                    key_to_best[key] = (r.model_family, r.balanced_accuracy, ba_std)
        keys = sorted(set(key_to_majority) | set(key_to_best))
        if not keys:
            self.baseline_comparison_frame.setVisible(False)
            return
        self.baseline_comparison_frame.setVisible(True)
        self.baseline_comparison_table.setRowCount(len(keys))
        for row, (target, phase) in enumerate(keys):
            maj = key_to_majority.get((target, phase))
            best = key_to_best.get((target, phase))
            self.baseline_comparison_table.setItem(row, 0, QTableWidgetItem(target))
            self.baseline_comparison_table.setItem(row, 1, QTableWidgetItem(phase))
            self.baseline_comparison_table.setItem(row, 2, QTableWidgetItem(f"{maj:.3f}" if maj is not None else "—"))
            self.baseline_comparison_table.setItem(row, 3, QTableWidgetItem(best[0] if best else "—"))
            if best:
                ba_str = f"{best[1]:.3f} ± {best[2]:.3f}" if best[2] > 0 else f"{best[1]:.3f}"
                self.baseline_comparison_table.setItem(row, 4, QTableWidgetItem(ba_str))
            else:
                self.baseline_comparison_table.setItem(row, 4, QTableWidgetItem("—"))
            if maj is not None and best is not None:
                delta = best[1] - maj
                delta_str = f"{delta:+.3f}" if best[2] <= 0 else f"{delta:+.3f} ± {best[2]:.3f}"
                self.baseline_comparison_table.setItem(row, 5, QTableWidgetItem(delta_str))
                beat = "Yes" if best[1] > maj else "No"
                self.baseline_comparison_table.setItem(row, 6, QTableWidgetItem(beat))
            else:
                self.baseline_comparison_table.setItem(row, 5, QTableWidgetItem("—"))
                self.baseline_comparison_table.setItem(row, 6, QTableWidgetItem("—"))

    def set_target_summary(self, target_summary: List[Dict[str, Any]]) -> None:
        """Block C3: Update class balance (target summary) table from training metadata."""
        if not target_summary:
            self.target_summary_frame.setVisible(False)
            return
        self.target_summary_frame.setVisible(True)
        self.target_summary_table.setRowCount(len(target_summary))
        for row, item in enumerate(target_summary):
            target = item.get("target", "")
            phase = item.get("phase", "")
            n_total = item.get("n_total", item.get("n_train", 0) + item.get("n_test", 0))
            counts = item.get("class_counts") or item.get("train_class_counts") or {}
            counts_str = ", ".join(f"cls{k}:{v}" for k, v in sorted(counts.items()))
            gate = "Yes" if item.get("gate_filtered") else "No"
            self.target_summary_table.setItem(row, 0, QTableWidgetItem(str(target)))
            self.target_summary_table.setItem(row, 1, QTableWidgetItem(str(phase)))
            self.target_summary_table.setItem(row, 2, QTableWidgetItem(str(n_total)))
            self.target_summary_table.setItem(row, 3, QTableWidgetItem(counts_str or "—"))
            self.target_summary_table.setItem(row, 4, QTableWidgetItem(gate))

    def set_kfold_metrics(self, agg: Dict[str, Any]) -> None:
        """Update k-fold CV summary. agg: dict with keys like accuracy, balanced_accuracy, auc, f1_score (mean, std)."""
        if not agg:
            self.kfold_frame.setVisible(False)
            self.kfold_label.setText("N/A — run Model Training or Run all phases (CV mode in Settings)")
            self.kfold_label.setStyleSheet("QLabel { color: #888; }")
            return
        self.kfold_label.setText("OK")
        self.kfold_label.setStyleSheet("QLabel { color: #2E7D32; }")
        self.kfold_frame.setVisible(True)
        self.kfold_table.setRowCount(4)
        def fmt(m, s):
            return f"{m:.3f} ± {s:.3f}" if s and s > 0 else f"{m:.3f}"
        for row, (name, key) in enumerate([
            ("Accuracy", "accuracy"),
            ("Balanced Accuracy", "balanced_accuracy"),
            ("AUC", "auc"),
            ("F1 Score", "f1_score"),
        ]):
            val = agg.get(key, (0.0, 0.0))
            if isinstance(val, (list, tuple)) and len(val) >= 2:
                self.kfold_table.setItem(row, 0, QTableWidgetItem(name))
                self.kfold_table.setItem(row, 1, QTableWidgetItem(fmt(val[0], val[1])))
            else:
                self.kfold_table.setItem(row, 0, QTableWidgetItem(name))
                self.kfold_table.setItem(row, 1, QTableWidgetItem(str(val)))

    def set_bootstrap_metrics(self, bootstrap_cis: List[tuple]) -> None:
        """Update bootstrap CI display. bootstrap_cis: list of (phase, target, model_family, ba_mean, ba_low, ba_high)."""
        if not bootstrap_cis:
            self.bootstrap_frame.setVisible(False)
            self.bootstrap_label.setText("N/A — run Model Training")
            self.bootstrap_label.setStyleSheet("QLabel { color: #888; }")
            return
        self.bootstrap_label.setText("OK")
        self.bootstrap_label.setStyleSheet("QLabel { color: #2E7D32; }")
        self.bootstrap_frame.setVisible(True)
        self.bootstrap_table.setRowCount(len(bootstrap_cis))
        for row, item in enumerate(bootstrap_cis):
            if len(item) >= 6:
                phase, target, model_fam, ba_mean, ba_low, ba_high = item[:6]
                self.bootstrap_table.setItem(row, 0, QTableWidgetItem(f"{phase} / {target} / {model_fam}"))
                self.bootstrap_table.setItem(row, 1, QTableWidgetItem(f"{ba_mean:.3f}"))
                self.bootstrap_table.setItem(row, 2, QTableWidgetItem(f"[{ba_low:.3f} – {ba_high:.3f}]"))
            else:
                self.bootstrap_table.setItem(row, 0, QTableWidgetItem(str(item)))
                self.bootstrap_table.setItem(row, 1, QTableWidgetItem(""))
                self.bootstrap_table.setItem(row, 2, QTableWidgetItem(""))
