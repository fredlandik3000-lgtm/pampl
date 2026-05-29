"""Type definitions for pipeline operations"""

from typing import Callable, Dict, Any, Optional, List
from dataclasses import dataclass, field
from threading import Event
from enum import Enum

# Block C2: primary targets for main paper (from ANALYSIS_PLAN.md)
PRIMARY_TARGETS: List[str] = [
    "D30_response_3class",
    "D90_is_cr",
    "crs_grade_ge2",
    "icans_grade_ge2",
    "relapse_or_progression",
    "survival_status_lfu",
]


# Callback type definitions
ProgressCallback = Callable[[float, str], None]
"""Progress callback signature: (progress_percent, status_message)"""

LogCallback = Callable[[str, str, str], None]
"""Log callback signature: (level, source, message)"""


class EvaluationMode(Enum):
    """Evaluation mode for model training."""
    SINGLE_SPLIT = "single_split"
    KFOLD_CV = "kfold_cv"
    REPEATED_HOLDOUT = "repeated_holdout"
    NESTED_CV = "nested_cv"


class PipelineStep(Enum):
    """Pipeline step identifiers"""
    LOAD_DATA = "load_data"
    DERIVE_TARGETS = "derive_targets"
    ENGINEER_FEATURES = "engineer_features"
    TRAIN_MODELS = "train_models"
    EVALUATE_MODELS = "evaluate_models"
    GENERATE_VISUALIZATIONS = "generate_visualizations"


@dataclass
class CancellationToken:
    """Thread-safe cancellation token for pipeline operations"""
    _event: Event = field(default_factory=Event)
    
    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested"""
        return self._event.is_set()
    
    def cancel(self) -> None:
        """Request cancellation"""
        self._event.set()
    
    def reset(self) -> None:
        """Reset cancellation state"""
        self._event.clear()


@dataclass
class StepResult:
    """Standard result format for all pipeline steps"""
    success: bool
    data: Any
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        error_info = f", {len(self.errors)} errors" if self.errors else ""
        warning_info = f", {len(self.warnings)} warnings" if self.warnings else ""
        return f"StepResult({status}{error_info}{warning_info})"


@dataclass
class PipelineConfig:
    """Configuration for pipeline execution"""
    data_path: str
    phases: List[str]
    targets: List[str]
    random_seed: int = 42
    test_size: float = 0.3
    validate_data: bool = True
    enable_caching: bool = True
    cache_dir: str = "cache"
    use_cv_evaluation: bool = True  # Kept for backward compat; follows evaluation_mode
    # Evaluation mode: single_split | kfold_cv | repeated_holdout | nested_cv
    evaluation_mode: str = "nested_cv"  # Default: unbiased estimates with inner-loop tuning (LR, RF, XGB)
    n_repeats: int = 3  # For repeated_holdout: number of 70/30 splits with different seeds
    # When evaluation uses CV: how to produce ROC/CM/calibration/PR for the Visualizations tab
    # last_outer_fold: illustrative curves from last outer fold (with full eval for tuned models)
    # refit_holdout: single stratified train/test split after CV, figures only (does not replace CV metrics)
    cv_curve_source: str = "last_outer_fold"
    # Optional feature selection (in feature engineering)
    use_feature_selection: bool = False
    feature_selection_method: str = "mutual_info"  # "none" | "variance" | "mutual_info"
    feature_selection_top_k: int = 50  # Keep top K features (for variance/mutual_info)


@dataclass
class ModelResult:
    """Performance metrics for a trained model (single split or CV-aggregated)."""
    target: str
    phase: str
    model_family: str
    accuracy: float
    balanced_accuracy: float
    auc: float
    f1_score: float
    precision: float = 0.0
    recall: float = 0.0
    train_time: float = 0.0
    threshold: float = 0.5
    sample_size: int = 0
    # Block A: optional std and 95% CI when from CV or bootstrap (default 0 = single-split)
    balanced_accuracy_std: float = 0.0
    auc_std: float = 0.0
    f1_score_std: float = 0.0
    balanced_accuracy_ci_low: float = 0.0
    balanced_accuracy_ci_high: float = 0.0

    def get_metric(self, metric_name: str) -> float:
        """Get metric value by name"""
        metric_map = {
            'accuracy': self.accuracy,
            'balanced_accuracy': self.balanced_accuracy,
            'auc': self.auc,
            'f1': self.f1_score,
            'f1_score': self.f1_score,
            'precision': self.precision,
            'recall': self.recall
        }
        return metric_map.get(metric_name.lower(), 0.0)

    def get_metric_display(self, metric_name: str) -> str:
        """Format metric for display; include ± std when from CV (Block A)."""
        key = metric_name.lower().replace(" ", "_")
        value = self.get_metric(metric_name)
        if key == "balanced_accuracy" and self.balanced_accuracy_std > 0:
            return f"{value:.3f} ± {self.balanced_accuracy_std:.3f}"
        if key == "balanced_accuracy" and (self.balanced_accuracy_ci_low > 0 or self.balanced_accuracy_ci_high > 0):
            return f"{value:.3f} [{self.balanced_accuracy_ci_low:.3f}–{self.balanced_accuracy_ci_high:.3f}]"
        if key == "auc" and self.auc_std > 0:
            return f"{value:.3f} ± {self.auc_std:.3f}"
        if key in ("f1", "f1_score") and self.f1_score_std > 0:
            return f"{value:.3f} ± {self.f1_score_std:.3f}"
        return f"{value:.3f}"
