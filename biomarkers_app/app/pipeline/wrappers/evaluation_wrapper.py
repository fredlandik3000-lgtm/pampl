"""Evaluation Wrapper: structures training results for metrics and visualization (Phase 5)."""

from typing import Optional, List, Dict, Any

from app.pipeline.types import (
    ProgressCallback, LogCallback, CancellationToken, StepResult, ModelResult
)


class EvaluationWrapper:
    """
    Structures model training results for evaluation display and visualization.
    ROC curves and confusion matrices are produced by the training wrapper;
    this wrapper aggregates and formats them for the UI.
    """

    def __init__(self, logger: Optional[LogCallback] = None):
        self.logger = logger or self._default_logger

    def _default_logger(self, level: str, source: str, message: str) -> None:
        print(f"[{level}] {source}: {message}")

    def evaluate(
        self,
        training_result: StepResult,
        progress_callback: Optional[ProgressCallback] = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> StepResult:
        """
        Produce evaluation summary and visualization data from training result.

        Args:
            training_result: StepResult from model training (data=List[ModelResult], metadata with roc_curves, confusion_matrices)
            progress_callback: Optional progress
            cancellation_token: Optional cancellation

        Returns:
            StepResult with same data plus metadata suitable for ROC/confusion/heatmap views.
        """
        if not training_result.success or training_result.data is None:
            return StepResult(
                success=False,
                data=training_result.data,
                metadata=training_result.metadata,
                errors=training_result.errors or ['No training results to evaluate'],
            )

        results: List[ModelResult] = training_result.data
        meta = dict(training_result.metadata)

        # Aggregate best model per (target, phase) for heatmap
        best_per_target: Dict[str, str] = {}
        for r in results:
            key = (r.target, r.phase)
            existing = best_per_target.get(r.target)
            if existing is None or r.balanced_accuracy > (existing.get('ba') or 0):
                best_per_target[r.target] = {
                    'model_family': r.model_family,
                    'ba': r.balanced_accuracy,
                    'accuracy': r.accuracy,
                    'auc': r.auc,
                }

        meta['best_per_target'] = best_per_target
        meta['roc_curves'] = meta.get('roc_curves', [])
        meta['confusion_matrices'] = meta.get('confusion_matrices', [])

        return StepResult(
            success=True,
            data=results,
            metadata=meta,
            warnings=training_result.warnings,
        )
