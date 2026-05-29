"""Visualizations Widget: ROC, confusion matrices, calibration, PR curves, heatmaps (academic paper standards)."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QStackedWidget, QPushButton, QMessageBox, QCheckBox, QFileDialog,
)
from PyQt6.QtCore import Qt
from typing import Optional, List, Dict, Any, Tuple, cast

from app.pipeline.types import ModelResult

# Publication-ready styling (TRIPOD+AI / REMARK)
_FONT_SIZE = 11
_TITLE_SIZE = 12
_DPI = 100  # Screen; export at 300 for publication


def _get_auc_for(phase: Optional[str], target: str, model: str, results: List[ModelResult]) -> Optional[float]:
    """Look up AUC from ModelResult for display in ROC title."""
    for r in results:
        if r.target == target and r.model_family == model and (phase is None or r.phase == phase):
            return r.auc
    return None


def _get_sample_size_for(phase: Optional[str], target: str, model: str, results: List[ModelResult]) -> Optional[int]:
    """Look up sample size from ModelResult for figure legend."""
    for r in results:
        if r.target == target and r.model_family == model and (phase is None or r.phase == phase):
            return r.sample_size
    return None


def _build_roc_plot(
    fpr: List[float], tpr: List[float], title: str,
    auc: Optional[float] = None, sample_size: Optional[int] = None,
) -> Any:
    """Build ROC curve with AUC in title, diagonal reference, publication styling."""
    try:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    except ImportError:
        return None
    fig = Figure(figsize=(6, 5), dpi=_DPI)
    ax = fig.add_subplot(111)
    ax.plot(fpr, tpr, 'b-', linewidth=2, label='Model')
    ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random')
    ax.set_xlabel('False Positive Rate', fontsize=_FONT_SIZE)
    ax.set_ylabel('True Positive Rate', fontsize=_FONT_SIZE)
    tit = title or 'ROC Curve'
    if auc is not None:
        tit += f' (AUC = {auc:.3f})'
    if sample_size is not None:
        tit += f'\nn = {sample_size}'
    ax.set_title(tit, fontsize=_TITLE_SIZE)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(loc='lower right', fontsize=_FONT_SIZE - 1)
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis='both', labelsize=_FONT_SIZE - 1)
    fig.tight_layout()
    return FigureCanvas(fig)


def _build_confusion_matrix_plot(
    cm: List[List[float]], title: str,
    class_labels: Optional[List[str]] = None,
    normalized: bool = False,
) -> Any:
    """Build confusion matrix with class labels on axes; optional normalized (%)."""
    try:
        import numpy as np
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    except ImportError:
        return None
    fig = Figure(figsize=(5, 4), dpi=_DPI)
    ax = fig.add_subplot(111)
    arr = np.array(cm, dtype=float)
    if normalized:
        row_sums = arr.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        arr = arr / row_sums * 100
    im = ax.imshow(arr, cmap='Blues', vmin=0, vmax=arr.max() if arr.size else 1)
    n_classes = arr.shape[0]
    labels = class_labels or [f'Class {i}' for i in range(n_classes)]
    ax.set_xticks(range(n_classes))
    ax.set_xticklabels(labels, fontsize=_FONT_SIZE - 1)
    ax.set_yticks(range(n_classes))
    ax.set_yticklabels(labels, fontsize=_FONT_SIZE - 1)
    ax.set_xlabel('Predicted', fontsize=_FONT_SIZE)
    ax.set_ylabel('Actual', fontsize=_FONT_SIZE)
    tit = (title or 'Confusion Matrix') + (' (normalized %)' if normalized else '')
    ax.set_title(tit, fontsize=_TITLE_SIZE)
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            val = arr[i, j]
            color = 'white' if val > (arr.max() * 0.6 if arr.size else 0) else 'black'
            text = f'{val:.0f}%' if normalized else int(val)
            ax.text(j, i, text, ha='center', va='center', color=color, fontsize=_FONT_SIZE)
    fig.colorbar(im, ax=ax, label='%' if normalized else 'Count')
    fig.tight_layout()
    return FigureCanvas(fig)


def _build_calibration_plot(
    frac_pos: List[float], mean_pred: List[float], title: str,
    sample_size: Optional[int] = None,
) -> Any:
    """Build calibration curve: predicted vs observed probability (TRIPOD+AI standard)."""
    try:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    except ImportError:
        return None
    fig = Figure(figsize=(5, 5), dpi=_DPI)
    ax = fig.add_subplot(111)
    ax.plot(mean_pred, frac_pos, 's-', color='#2E86AB', linewidth=2, markersize=8, label='Model')
    ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Perfect calibration')
    ax.set_xlabel('Mean predicted probability', fontsize=_FONT_SIZE)
    ax.set_ylabel('Fraction of positives', fontsize=_FONT_SIZE)
    tit = title or 'Calibration Curve'
    if sample_size is not None:
        tit += f'\nn = {sample_size}'
    ax.set_title(tit, fontsize=_TITLE_SIZE)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(loc='lower right', fontsize=_FONT_SIZE - 1)
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis='both', labelsize=_FONT_SIZE - 1)
    fig.tight_layout()
    return FigureCanvas(fig)


def _build_pr_plot(
    precision: List[float], recall: List[float], title: str,
    auprc: Optional[float] = None, sample_size: Optional[int] = None,
) -> Any:
    """Build Precision-Recall curve with AU-PR (preferred for imbalanced classes)."""
    try:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    except ImportError:
        return None
    fig = Figure(figsize=(5, 5), dpi=_DPI)
    ax = fig.add_subplot(111)
    ax.plot(recall, precision, 'b-', linewidth=2, label='Model')
    ax.set_xlabel('Recall', fontsize=_FONT_SIZE)
    ax.set_ylabel('Precision', fontsize=_FONT_SIZE)
    tit = title or 'Precision-Recall Curve'
    if auprc is not None:
        tit += f' (AU-PR = {auprc:.3f})'
    if sample_size is not None:
        tit += f'\nn = {sample_size}'
    ax.set_title(tit, fontsize=_TITLE_SIZE)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(loc='upper right', fontsize=_FONT_SIZE - 1)
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis='both', labelsize=_FONT_SIZE - 1)
    fig.tight_layout()
    return FigureCanvas(fig)


def _build_heatmap_plot(
    results: List[ModelResult], metric: str = 'balanced_accuracy',
    phase_filter: Optional[str] = None,
    exclude_baselines: bool = False,
) -> Any:
    """Build heatmap: rows=targets (optionally phase-specific), cols=model_family."""
    try:
        import numpy as np
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    except ImportError:
        return None
    if exclude_baselines:
        results = [
            r for r in results
            if r.model_family not in ('Baseline-Majority', 'Baseline-Random')
        ]
    if phase_filter:
        results = [r for r in results if r.phase == phase_filter]
    if not results:
        return None
    # Rows: target (or "phase | target" if multiple phases and no filter)
    use_phase_in_row = not phase_filter and len(set(r.phase for r in results)) > 1
    if use_phase_in_row:
        row_key = lambda r: (r.phase, r.target)
        row_labels = sorted(set(row_key(r) for r in results))
        row_labels = [f"{p} | {t}" for p, t in row_labels]
    else:
        row_labels = sorted(set(r.target for r in results))
    models = sorted(set(r.model_family for r in results))
    if not row_labels or not models:
        return None
    if use_phase_in_row:
        key = lambda r: ((r.phase, r.target), r.model_family)
        by_key = {key(r): r.get_metric(metric) for r in results}
        data = np.array([
            [by_key.get(((p, t), m), 0.0) for m in models]
            for (p, t) in sorted(set((r.phase, r.target) for r in results))
        ])
    else:
        key = lambda r: (r.target, r.model_family)
        by_key = {key(r): r.get_metric(metric) for r in results}
        data = np.array([[by_key.get((t, m), 0.0) for m in models] for t in row_labels])
    fig = Figure(figsize=(8, max(4, len(row_labels) * 0.35)), dpi=_DPI)
    ax = fig.add_subplot(111)
    im = ax.imshow(data, cmap='RdYlGn', vmin=0, vmax=1)
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models, rotation=45, ha='right', fontsize=_FONT_SIZE - 1)
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=_FONT_SIZE - 1)
    ax.set_xlabel('Model', fontsize=_FONT_SIZE)
    ax.set_ylabel('Phase | Target' if use_phase_in_row else 'Target', fontsize=_FONT_SIZE)
    title = f'Model Comparison ({metric.replace("_", " ").title()})'
    if phase_filter:
        title += f' — {phase_filter}'
    ax.set_title(title, fontsize=_TITLE_SIZE)
    for i in range(len(row_labels)):
        for j in range(len(models)):
            v = data[i, j]
            ax.text(j, i, f'{v:.2f}', ha='center', va='center', fontsize=_FONT_SIZE - 1)
    fig.colorbar(im, ax=ax, label=metric.replace('_', ' ').title())
    fig.tight_layout()
    return FigureCanvas(fig)


def _build_class_distribution_plot(
    confusion_matrices: List[Tuple], results: List[ModelResult],
    phase_filter: Optional[str] = None,
) -> Any:
    """Build class distribution from confusion matrices (row sums = actual class counts)."""
    try:
        import numpy as np
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    except ImportError:
        return None
    if not confusion_matrices:
        return None
    # Aggregate by (phase, target): row sums of CM = actual class counts (one per target-phase)
    dist: Dict[Tuple[str, str], np.ndarray] = {}
    for entry in confusion_matrices:
        if len(entry) == 4:
            phase, target, model, cm = entry
        else:
            target, model, cm = entry
            phase = None
        if phase_filter and (phase or '') != phase_filter:
            continue
        key = (phase or '', target)
        if key not in dist:
            arr = np.array(cm)
            dist[key] = arr.sum(axis=1)
    items = sorted(dist.items(), key=lambda x: (x[0][0], x[0][1]))
    if not items:
        return None
    labels = [f"{p} | {t}" if p else t for (p, t), _ in items]
    all_counts = [v for _, v in items]
    n_classes = max(len(v) for v in all_counts)
    x = np.arange(len(labels))
    width = 0.8 / n_classes
    fig = Figure(figsize=(max(8, len(labels) * 0.5), 5), dpi=_DPI)
    ax = fig.add_subplot(111)
    for c in range(n_classes):
        counts = [v[c] if len(v) > c else 0 for _, v in items]
        offset = (c - n_classes / 2 + 0.5) * width
        ax.bar(x + offset, counts, width, label=f'Class {c}')
    ax.set_ylabel('Count', fontsize=_FONT_SIZE)
    ax.set_xlabel('Phase | Target', fontsize=_FONT_SIZE)
    ax.set_title('Class Distribution (Test Set)', fontsize=_TITLE_SIZE)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=_FONT_SIZE - 1)
    ax.legend(fontsize=_FONT_SIZE - 1)
    ax.tick_params(axis='both', labelsize=_FONT_SIZE - 1)
    fig.tight_layout()
    return FigureCanvas(fig)


class VisualizationsWidget(QWidget):
    """Widget for ROC, confusion matrices, calibration, PR curves, heatmaps (academic paper standards)."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._results: List[ModelResult] = []
        self._metadata: Dict[str, Any] = {}
        self._roc_options: List[tuple] = []
        self._cm_options: List[tuple] = []
        self._cal_options: List[tuple] = []
        self._pr_options: List[tuple] = []
        self._active_canvas: Any = None
        self._init_ui()

    # View categories (academic: dispersed by purpose)
    CATEGORY_VIEWS = {
        "Discrimination": ["ROC Curve", "Precision-Recall Curve"],
        "Calibration": ["Calibration Curve"],
        "Classification": ["Confusion Matrix"],
        "Summary": ["Performance Heatmap", "Class Distribution"],
    }

    # Short tooltips on the ? buttons (updated when View changes)
    _VIEW_HINT_TOOLTIP: Dict[str, str] = {
        "ROC Curve": "ROC: TPR vs FPR, AUC vs chance diagonal — click for full explanation.",
        "Precision-Recall Curve": "PR curve: precision vs recall; AU-PR — click for when to use it.",
        "Calibration Curve": "Calibration: predicted vs observed risk — click for TRIPOD context.",
        "Confusion Matrix": "Confusion matrix: actual vs predicted class counts — click for details.",
        "Performance Heatmap": "Heatmap: metric across targets (or phase|target) × models — click for how to read it.",
        "Class Distribution": "Bar chart of class counts per outcome from test-set confusion data — click for details.",
    }
    _SELECTION_HINT_TOOLTIP: Dict[str, str] = {
        "ROC Curve": "Pick phase|target|model series; Phase filter narrows rows. Click for more.",
        "Precision-Recall Curve": "Pick a series with PR data (binary). Phase filter applies. Click for more.",
        "Calibration Curve": "Pick a series with calibration bins (binary). Click for more.",
        "Confusion Matrix": "Pick series; use Normalized (%) for row percentages. Click for more.",
        "Performance Heatmap": "Choose metric, optional hide baselines; Phase filters rows. Click for more.",
        "Class Distribution": "Phase filter restricts bars; needs confusion matrices in the run. Click for more.",
    }
    _VIEW_HINT_DIALOG: Dict[str, Tuple[str, str]] = {
        "ROC Curve": (
            "ROC curve",
            "True positive rate (y) vs false positive rate (x) across thresholds.\n\n"
            "AUC in the title summarizes discrimination; the dashed diagonal is random guessing.\n"
            "n is the test (or fold) sample size when available.\n"
            "Use Phase to show one phase or All phases; pick the target/model series that matches your question.",
        ),
        "Precision-Recall Curve": (
            "Precision–Recall curve",
            "Precision (y) vs recall (x). AU-PR in the title is especially informative when classes are imbalanced, "
            "where ROC can look optimistic.\n\n"
            "Available for binary outcomes with PR metadata from training. Pick the matching series in Target / Model.",
        ),
        "Calibration Curve": (
            "Calibration curve",
            "Mean predicted probability (x) vs observed fraction of positives (y) in bins. "
            "The diagonal is perfect calibration — important for clinical interpretation (TRIPOD+AI).\n\n"
            "Binary targets only. Pick the series that matches your model and outcome.",
        ),
        "Confusion Matrix": (
            "Confusion matrix",
            "Rows = actual class, columns = predicted class. Cell values are counts unless you enable "
            "Normalized (%) for row-wise percentages (publication-friendly).\n\n"
            "Pick phase|target|model from Target / Model. Class labels are generic until the pipeline supplies named levels.",
        ),
        "Performance Heatmap": (
            "Performance heatmap",
            "Each cell is one metric (e.g. balanced accuracy) for one target (or phase|target) and one model family. "
            "Red–yellow–green encodes performance.\n\n"
            "Use Heatmap metric to switch the score. Hide baselines removes majority/random rows/columns for a cleaner model-only view. "
            "Phase filter restricts to one phase or shows phase|target on rows when All phases is selected.",
        ),
        "Class Distribution": (
            "Class distribution",
            "Bars show class counts on the test set derived from confusion matrices (row sums), aggregated per phase|target.\n\n"
            "Requires confusion matrices in the saved training metadata. Use Phase to restrict. "
            "If nothing appears, re-run training with a mode that emits CM data or load a saved run that includes it.",
        ),
    }
    _SELECTION_HINT_DIALOG: Dict[str, Tuple[str, str]] = {
        "ROC Curve": (
            "Controls: ROC",
            "Target / Model lists every available ROC series from the current run (phase | target | model).\n\n"
            "Phase (top row): when set to a single phase, titles and filters align to that phase; "
            "All phases keeps multi-phase labels in the series text.",
        ),
        "Precision-Recall Curve": (
            "Controls: Precision–Recall",
            "Target / Model lists series that have PR curve data (binary outcomes).\n\n"
            "If the list is empty, training did not emit pr_curves for this run — try Summary → Performance Heatmap, "
            "or adjust CV figure settings and re-train.",
        ),
        "Calibration Curve": (
            "Controls: Calibration",
            "Target / Model lists series with calibration bin data.\n\n"
            "If empty, there is no calibration metadata for this run (e.g. multiclass-only).",
        ),
        "Confusion Matrix": (
            "Controls: Confusion matrix",
            "Target / Model picks which confusion matrix to plot.\n\n"
            "Normalized (%) shows each row as percentages (useful for unequal class sizes). "
            "Uncheck for raw counts.",
        ),
        "Performance Heatmap": (
            "Controls: Heatmap",
            "Heatmap metric selects which score colors the cells (balanced accuracy, accuracy, AUC, F1).\n\n"
            "Hide baselines on heatmap removes Baseline-Majority and Baseline-Random so you compare trained models only.\n"
            "Phase filters which rows appear when you have multiple phases.",
        ),
        "Class Distribution": (
            "Controls: Class distribution",
            "Target / Model is not used for this view.\n\n"
            "Phase filters which phase|target bars are shown. The chart needs confusion_matrices in run metadata.",
        ),
    }

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.status_label = QLabel(
            "Load training results from Pipeline Flow (or a saved run) to see figures. "
            "For nested CV, ROC/PR/calibration use the configured curve source (Training settings)."
        )
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("QLabel { color: #444; padding: 4px; font-size: 11px; }")
        layout.addWidget(self.status_label)
        # Row 1: Phase filter (when multi-phase), Category, View
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Phase:"))
        self.phase_combo = QComboBox()
        self.phase_combo.addItem("All phases")
        self.phase_combo.currentTextChanged.connect(self._on_phase_or_category_changed)
        row1.addWidget(self.phase_combo)
        row1.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(list(self.CATEGORY_VIEWS.keys()))
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        row1.addWidget(self.category_combo)
        row1.addWidget(QLabel("View:"))
        self.view_combo = QComboBox()
        self.view_combo.currentTextChanged.connect(self._on_view_changed)
        row1.addWidget(self.view_combo)
        self._view_help_btn = QPushButton("?")
        self._view_help_btn.setFixedSize(22, 22)
        self._view_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        self._view_help_btn.clicked.connect(self._show_view_help)
        row1.addWidget(self._view_help_btn)
        layout.addLayout(row1)
        # Row 2: Target/Model selector, Heatmap metric, options
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Target / Model:"))
        self.series_combo = QComboBox()
        self.series_combo.currentTextChanged.connect(self._refresh_plot)
        row2.addWidget(self.series_combo, 1)
        self._heatmap_metric_label = QLabel("Heatmap metric:")
        row2.addWidget(self._heatmap_metric_label)
        self.heatmap_metric_combo = QComboBox()
        self.heatmap_metric_combo.addItems(["balanced_accuracy", "accuracy", "auc", "f1_score"])
        self.heatmap_metric_combo.currentTextChanged.connect(self._refresh_plot)
        row2.addWidget(self.heatmap_metric_combo)
        self.heatmap_exclude_baselines = QCheckBox("Hide baselines on heatmap")
        self.heatmap_exclude_baselines.setToolTip("Exclude Baseline-Majority and Baseline-Random rows/columns for clearer comparison.")
        self.heatmap_exclude_baselines.toggled.connect(self._refresh_plot)
        row2.addWidget(self.heatmap_exclude_baselines)
        self.cm_normalized_check = QCheckBox("Normalized (%)")
        self.cm_normalized_check.setChecked(False)
        self.cm_normalized_check.toggled.connect(self._refresh_plot)
        row2.addWidget(self.cm_normalized_check)
        self._row2_help_btn = QPushButton("?")
        self._row2_help_btn.setFixedSize(22, 22)
        self._row2_help_btn.setStyleSheet("QPushButton { font-weight: bold; color: #666; }")
        self._row2_help_btn.clicked.connect(self._show_selection_help)
        row2.addWidget(self._row2_help_btn)
        layout.addLayout(row2)
        export_row = QHBoxLayout()
        self.export_png_btn = QPushButton("Export PNG (300 DPI)")
        self.export_png_btn.clicked.connect(lambda: self._export_current_figure("png"))
        self.export_pdf_btn = QPushButton("Export PDF")
        self.export_pdf_btn.clicked.connect(lambda: self._export_current_figure("pdf"))
        export_row.addWidget(self.export_png_btn)
        export_row.addWidget(self.export_pdf_btn)
        export_row.addStretch()
        layout.addLayout(export_row)
        self.plot_stack = QStackedWidget()
        self.plot_placeholder = QLabel(
            "Run model training from Pipeline Flow to see ROC curves, confusion matrices, "
            "calibration curves, precision-recall curves, and performance heatmaps."
        )
        self.plot_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.plot_placeholder.setStyleSheet("QLabel { color: #666; padding: 40px; }")
        self.plot_stack.addWidget(self.plot_placeholder)
        self.plot_container = QWidget()
        self.plot_layout = QVBoxLayout(self.plot_container)
        self.plot_stack.addWidget(self.plot_container)
        self.plot_message = QLabel("")
        self.plot_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.plot_message.setWordWrap(True)
        self.plot_message.setStyleSheet("QLabel { color: #666; padding: 40px; }")
        self.plot_stack.addWidget(self.plot_message)
        layout.addWidget(self.plot_stack, 1)
        # Initialize View list from first category
        self._on_category_changed(self.category_combo.currentText())
        self._update_heatmap_controls_visibility()
        self._update_contextual_hints()

    def _current_view_name(self) -> str:
        return self.view_combo.currentText() or ""

    def _update_contextual_hints(self) -> None:
        """Tooltips on ? buttons follow the selected View (chart type)."""
        view = self._current_view_name()
        tip_v = self._VIEW_HINT_TOOLTIP.get(view, "Click for help on this chart.")
        tip_r = self._SELECTION_HINT_TOOLTIP.get(view, "Click for help on these controls.")
        self._view_help_btn.setToolTip(tip_v)
        self._row2_help_btn.setToolTip(tip_r)

    def _show_view_help(self):
        """Explain the current chart type (matches Category → View)."""
        view = self._current_view_name()
        title, body = self._VIEW_HINT_DIALOG.get(
            view,
            ("Visualization", "Select a view under Category and View to see a figure-specific explanation."),
        )
        QMessageBox.information(self, title, body)

    def _show_selection_help(self):
        """Explain the controls that apply to the current chart (Target/Model, heatmap, CM options)."""
        view = self._current_view_name()
        title, body = self._SELECTION_HINT_DIALOG.get(
            view,
            ("Controls", "Select a view to see which controls apply (series picker, heatmap metric, etc.)."),
        )
        QMessageBox.information(self, title, body)

    def _on_phase_or_category_changed(self):
        self._refresh_plot()

    def _on_category_changed(self, _category: str):
        """Populate View combo with views for selected category."""
        self.view_combo.blockSignals(True)
        self.view_combo.clear()
        self.view_combo.addItems(self.CATEGORY_VIEWS.get(self.category_combo.currentText(), []))
        self.view_combo.blockSignals(False)
        self._on_view_changed()

    def _update_status_from_metadata(self):
        meta = self._metadata
        parts: List[str] = []
        src = meta.get("curve_source")
        if src:
            parts.append(f"Curve source: {src}")
        note = meta.get("curve_note")
        if note:
            parts.append(note)
        if meta.get("n_outer_splits"):
            parts.append(f"Outer folds: {meta['n_outer_splits']}")
        self.status_label.setText(
            " ".join(parts) if parts else "Results loaded. Pick a category and view to plot."
        )

    def _update_heatmap_controls_visibility(self):
        view = self.view_combo.currentText()
        hm = view == "Performance Heatmap"
        self._heatmap_metric_label.setVisible(hm)
        self.heatmap_metric_combo.setVisible(hm)
        self.heatmap_exclude_baselines.setVisible(hm)

    def _export_current_figure(self, fmt: str):
        canvas = self._active_canvas
        if canvas is None or not getattr(canvas, "figure", None):
            QMessageBox.information(self, "Export", "No figure to export. Select a view that draws a plot first.")
            return
        ext = f".{fmt}"
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Save figure ({fmt.upper()})",
            f"visualization{ext}",
            f"PNG image (*.png)" if fmt == "png" else "PDF (*.pdf)",
        )
        if not path:
            return
        if not path.lower().endswith(ext):
            path += ext
        try:
            dpi = 300 if fmt == "png" else None
            canvas.figure.savefig(path, dpi=dpi, bbox_inches="tight", format=fmt)
        except Exception as e:
            QMessageBox.warning(self, "Export", f"Could not save: {e}")
            return
        QMessageBox.information(self, "Export", f"Saved:\n{path}")

    def load_training_result(self, results: List[ModelResult], metadata: Dict[str, Any]):
        """Load training results and metadata for visualization."""
        self._results = list(results) if results else []
        self._metadata = dict(metadata) if metadata else {}
        self._roc_options = []
        self._cm_options = []
        self._cal_options = []
        self._pr_options = []
        for curve in self._metadata.get('roc_curves', []):
            if len(curve) == 5:
                phase, target, model, _fpr, _tpr = curve
                label = f"{phase} | {target} / {model}"
                self._roc_options.append((label, phase, target, model))
            else:
                target, model, _fpr, _tpr = curve
                self._roc_options.append((f"{target} / {model}", None, target, model))
        for cm_entry in self._metadata.get('confusion_matrices', []):
            if len(cm_entry) == 4:
                phase, target, model, _cm = cm_entry
                label = f"{phase} | {target} / {model}"
                self._cm_options.append((label, phase, target, model))
            else:
                target, model, _cm = cm_entry
                self._cm_options.append((f"{target} / {model}", None, target, model))
        for cal in self._metadata.get('calibration_curves', []):
            if len(cal) == 5:
                phase, target, model, _, _ = cal
                label = f"{phase} | {target} / {model}"
                self._cal_options.append((label, phase, target, model))
        for pr in self._metadata.get('pr_curves', []):
            if len(pr) == 6:
                phase, target, model, _, _, _ = pr
                label = f"{phase} | {target} / {model}"
                self._pr_options.append((label, phase, target, model))
        phases = sorted(set(r.phase for r in self._results))
        self.phase_combo.blockSignals(True)
        self.phase_combo.clear()
        self.phase_combo.addItem("All phases")
        for p in phases:
            self.phase_combo.addItem(p)
        self.phase_combo.blockSignals(False)
        self._update_status_from_metadata()
        self._on_category_changed(self.category_combo.currentText())
        if self._results and not self.series_combo.count() and self.view_combo.currentText() != "Performance Heatmap":
            self.category_combo.blockSignals(True)
            self.view_combo.blockSignals(True)
            self.category_combo.setCurrentText("Summary")
            self.view_combo.setCurrentText("Performance Heatmap")
            self.category_combo.blockSignals(False)
            self.view_combo.blockSignals(False)
            self._on_view_changed()
        self._refresh_plot()

    def _on_view_changed(self):
        """Repopulate series combo based on selected view; show/hide options by view."""
        self.series_combo.clear()
        view = self.view_combo.currentText()
        self.cm_normalized_check.setVisible(view == "Confusion Matrix")
        self._update_heatmap_controls_visibility()
        if view == "ROC Curve":
            for label, phase, t, m in self._roc_options:
                self.series_combo.addItem(label, ('roc', phase, t, m))
        elif view == "Confusion Matrix":
            for label, phase, t, m in self._cm_options:
                self.series_combo.addItem(label, ('cm', phase, t, m))
        elif view == "Calibration Curve":
            for label, phase, t, m in self._cal_options:
                self.series_combo.addItem(label, ('cal', phase, t, m))
        elif view == "Precision-Recall Curve":
            for label, phase, t, m in self._pr_options:
                self.series_combo.addItem(label, ('pr', phase, t, m))
        if self.series_combo.count():
            self.series_combo.setCurrentIndex(0)
        self._update_contextual_hints()
        self._refresh_plot()

    def _refresh_plot(self):
        """Redraw current view."""
        self._active_canvas = None
        while self.plot_layout.count():
            child = self.plot_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        view = self.view_combo.currentText()
        phase_filter = None
        if self.phase_combo.currentText() and self.phase_combo.currentText() != "All phases":
            phase_filter = self.phase_combo.currentText()

        def _attach_canvas(canvas: Any) -> None:
            self.plot_layout.addWidget(canvas)
            self._active_canvas = canvas
            self.plot_stack.setCurrentWidget(self.plot_container)

        def _show_message(msg: str) -> None:
            self.plot_message.setText(msg)
            self.plot_stack.setCurrentWidget(self.plot_message)

        if view == "Performance Heatmap" and self._results:
            metric = self.heatmap_metric_combo.currentText()
            excl = self.heatmap_exclude_baselines.isChecked()
            canvas = _build_heatmap_plot(
                self._results, metric=metric, phase_filter=phase_filter,
                exclude_baselines=excl,
            )
            if canvas:
                _attach_canvas(canvas)
                return
            _show_message(
                "Could not build heatmap (no rows after filters, or matplotlib unavailable). "
                "Try another phase or uncheck 'Hide baselines'."
            )
            return
        if view == "Class Distribution":
            cm_list = self._metadata.get('confusion_matrices', [])
            canvas = _build_class_distribution_plot(cm_list, self._results, phase_filter=phase_filter)
            if canvas:
                _attach_canvas(canvas)
                return
            if not self._results:
                self.plot_stack.setCurrentWidget(self.plot_placeholder)
            else:
                _show_message(
                    "Class distribution needs confusion matrices in the saved run metadata. "
                    "Use a training mode that emits curve data (e.g. nested CV with curve source), or pick Performance Heatmap."
                )
            return
        data = self.series_combo.currentData()
        if not data:
            if not self._results:
                self.plot_stack.setCurrentWidget(self.plot_placeholder)
            else:
                _show_message(
                    f"No series data for “{view}”. "
                    "Curve metadata may be missing (e.g. old saved run). Try Summary → Performance Heatmap, "
                    "or re-run training with curve source enabled in Pipeline → Training settings."
                )
            return
        kind = cast(tuple, data)[0]
        phase, target, model = cast(tuple, data)[1], cast(tuple, data)[2], cast(tuple, data)[3]
        auc = _get_auc_for(phase, target, model, self._results)
        n = _get_sample_size_for(phase, target, model, self._results)
        if kind == 'roc' and view == "ROC Curve":
            for curve in self._metadata.get('roc_curves', []):
                if len(curve) == 5:
                    p, t, m, fpr, tpr = curve
                    if p == phase and t == target and m == model:
                        tit = f"{target} / {model}" + (f" ({p})" if p else "")
                        canvas = _build_roc_plot(fpr, tpr, tit, auc=auc, sample_size=n)
                        if canvas:
                            _attach_canvas(canvas)
                        return
                else:
                    t, m, fpr, tpr = curve
                    if phase is None and t == target and m == model:
                        canvas = _build_roc_plot(fpr, tpr, f"{target} / {model}", auc=auc, sample_size=n)
                        if canvas:
                            _attach_canvas(canvas)
                        return
        if kind == 'cm' and view == "Confusion Matrix":
            normalized = self.cm_normalized_check.isChecked()
            for cm_entry in self._metadata.get('confusion_matrices', []):
                if len(cm_entry) == 4:
                    p, t, m, cm = cm_entry
                    if p == phase and t == target and m == model:
                        tit = f"{target} / {model}" + (f" ({p})" if p else "")
                        canvas = _build_confusion_matrix_plot(cm, tit, normalized=normalized)
                        if canvas:
                            _attach_canvas(canvas)
                        return
                else:
                    t, m, cm = cm_entry
                    if phase is None and t == target and m == model:
                        canvas = _build_confusion_matrix_plot(cm, f"{target} / {model}", normalized=normalized)
                        if canvas:
                            _attach_canvas(canvas)
                        return
        if kind == 'cal' and view == "Calibration Curve":
            for cal in self._metadata.get('calibration_curves', []):
                if len(cal) == 5:
                    p, t, m, frac, mean = cal
                    if p == phase and t == target and m == model:
                        tit = f"{target} / {model}" + (f" ({p})" if p else "")
                        canvas = _build_calibration_plot(frac, mean, tit, sample_size=n)
                        if canvas:
                            _attach_canvas(canvas)
                        return
        if kind == 'pr' and view == "Precision-Recall Curve":
            for pr in self._metadata.get('pr_curves', []):
                if len(pr) == 6:
                    p, t, m, prec, rec, auprc = pr
                    if p == phase and t == target and m == model:
                        tit = f"{target} / {model}" + (f" ({p})" if p else "")
                        canvas = _build_pr_plot(prec, rec, tit, auprc=auprc, sample_size=n)
                        if canvas:
                            _attach_canvas(canvas)
                        return
        if not self._results:
            self.plot_stack.setCurrentWidget(self.plot_placeholder)
        else:
            _show_message(
                "Could not draw this series (missing matching curve in metadata or matplotlib error). "
                "Try another Target/Model or use Performance Heatmap."
            )
