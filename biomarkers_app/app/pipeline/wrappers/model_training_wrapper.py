"""Model Training Wrapper for training NN, LR, XGB, RF, CatBoost per target/phase"""

import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any, Union

import numpy as np
import pandas as pd

from app.core.repo_paths import catboost_info_dir, repo_root

_project_root = repo_root()
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from app.pipeline.types import (
    ProgressCallback, LogCallback, CancellationToken, StepResult, ModelResult
)


def _build_X_from_engineered(
    df: pd.DataFrame,
    selected_features: List[str],
    logger: LogCallback
) -> Tuple[np.ndarray, List[str]]:
    """Build numeric feature matrix from engineered DataFrame."""
    existing = [c for c in selected_features if c in df.columns]
    if not existing:
        return np.array([]), []

    numeric_cols = []
    categorical_cols = []
    for c in existing:
        if df[c].dtype in ('object', 'string', 'category'):
            categorical_cols.append(c)
        else:
            numeric_cols.append(c)

    blocks = []
    names = []

    if numeric_cols:
        X_num = df[numeric_cols].fillna(0).astype(np.float32).values
        blocks.append(X_num)
        names.extend(numeric_cols)

    if categorical_cols:
        cat_df = df[categorical_cols].astype(str).fillna('Unknown')
        cat_ohe = pd.get_dummies(cat_df, columns=categorical_cols, dummy_na=False)
        blocks.append(cat_ohe.values.astype(np.float32))
        names.extend(list(cat_ohe.columns))

    if not blocks:
        return np.array([]), []
    X = np.hstack(blocks)
    return X, names


def _bootstrap_balanced_accuracy(
    y_test: np.ndarray,
    y_pred: np.ndarray,
    n_bootstrap: int = 200,
    random_state: int = 42,
) -> Tuple[float, float, float]:
    """Compute balanced accuracy and 95% CI via bootstrap resampling of test set. Returns (mean, 2.5%, 97.5%)."""
    from sklearn.metrics import balanced_accuracy_score
    if len(y_test) < 10 or len(y_pred) != len(y_test):
        return 0.0, 0.0, 0.0
    rng = np.random.default_rng(random_state)
    scores = []
    n = len(y_test)
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        try:
            ba = balanced_accuracy_score(y_test[idx], y_pred[idx])
            scores.append(ba)
        except Exception:
            pass
    if not scores:
        return float(balanced_accuracy_score(y_test, y_pred)), 0.0, 0.0
    scores_arr = np.array(scores)
    return float(np.mean(scores_arr)), float(np.percentile(scores_arr, 2.5)), float(np.percentile(scores_arr, 97.5))


def _append_viz_from_model_output(
    phase: str,
    target: str,
    model_family: str,
    res: Dict[str, Any],
    roc_curves: List[Tuple],
    confusion_matrices: List[Tuple],
    calibration_curves: List[Tuple],
    pr_curves: List[Tuple],
) -> None:
    """Append ROC/CM/calibration/PR tuples from a trainer result dict (same shape as train_models)."""
    if 'roc_fpr' in res and 'roc_tpr' in res:
        roc_curves.append((phase, target, model_family, res['roc_fpr'], res['roc_tpr']))
    if 'confusion_matrix' in res and res['confusion_matrix']:
        confusion_matrices.append((phase, target, model_family, res['confusion_matrix']))
    if 'calibration_frac' in res and 'calibration_mean' in res:
        calibration_curves.append((
            phase, target, model_family,
            res['calibration_frac'], res['calibration_mean'],
        ))
    if 'pr_precision' in res and 'pr_recall' in res:
        pr_curves.append((
            phase, target, model_family,
            res['pr_precision'], res['pr_recall'], res.get('auprc', 0.0),
        ))


def _add_binary_academic_curves(
    y_test: np.ndarray, proba: np.ndarray, res: Dict[str, Any]
) -> None:
    """Add calibration and precision-recall curves for binary classification (academic paper standards)."""
    try:
        from sklearn.calibration import calibration_curve
        from sklearn.metrics import precision_recall_curve, average_precision_score
        frac_pos, mean_pred = calibration_curve(y_test, proba, n_bins=10)
        res['calibration_frac'] = frac_pos.tolist()
        res['calibration_mean'] = mean_pred.tolist()
    except Exception:
        pass
    try:
        precision, recall, _ = precision_recall_curve(y_test, proba)
        res['pr_precision'] = precision.tolist()
        res['pr_recall'] = recall.tolist()
        res['auprc'] = float(average_precision_score(y_test, proba))
    except Exception:
        pass


def _compute_baseline_metrics(
    y_train: np.ndarray,
    y_test: np.ndarray,
    random_seed: int,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Compute majority (dominant class) and random baseline metrics on the same test set.
    Returns (majority_metrics, random_metrics) for fair comparison with trained models.
    """
    from collections import Counter
    from sklearn.metrics import (
        accuracy_score, balanced_accuracy_score, f1_score,
        precision_score, recall_score,
    )
    majority_metrics = {"accuracy": 0.0, "balanced_accuracy": 0.0, "auc": 0.5, "f1_score": 0.0, "precision": 0.0, "recall": 0.0}
    random_metrics = {"accuracy": 0.0, "balanced_accuracy": 0.0, "auc": 0.5, "f1_score": 0.0, "precision": 0.0, "recall": 0.0}
    if len(y_test) == 0:
        return majority_metrics, random_metrics
    classes = np.unique(y_train)
    if len(classes) < 2:
        return majority_metrics, random_metrics

    # Majority baseline: always predict dominant class from training set
    majority_class = Counter(y_train).most_common(1)[0][0]
    y_pred_majority = np.full_like(y_test, majority_class)
    try:
        majority_metrics["accuracy"] = float(accuracy_score(y_test, y_pred_majority))
        majority_metrics["balanced_accuracy"] = float(balanced_accuracy_score(y_test, y_pred_majority))
        majority_metrics["f1_score"] = float(f1_score(y_test, y_pred_majority, average="weighted", zero_division=0))
        majority_metrics["precision"] = float(precision_score(y_test, y_pred_majority, average="weighted", zero_division=0))
        majority_metrics["recall"] = float(recall_score(y_test, y_pred_majority, average="weighted", zero_division=0))
    except Exception:
        pass

    # Random baseline: predict according to training set class distribution
    classes_arr = np.unique(y_train)
    counts = np.array([np.sum(y_train == c) for c in classes_arr])
    probs = counts / counts.sum()
    rng = np.random.default_rng(random_seed)
    chosen_idx = rng.choice(len(classes_arr), size=len(y_test), p=probs)
    y_pred_random = classes_arr[chosen_idx]
    try:
        random_metrics["accuracy"] = float(accuracy_score(y_test, y_pred_random))
        random_metrics["balanced_accuracy"] = float(balanced_accuracy_score(y_test, y_pred_random))
        random_metrics["f1_score"] = float(f1_score(y_test, y_pred_random, average="weighted", zero_division=0))
        random_metrics["precision"] = float(precision_score(y_test, y_pred_random, average="weighted", zero_division=0))
        random_metrics["recall"] = float(recall_score(y_test, y_pred_random, average="weighted", zero_division=0))
    except Exception:
        pass
    return majority_metrics, random_metrics


def _get_targets_list(df: pd.DataFrame) -> List[str]:
    """Get list of trainable target columns (derived, excluding gates if desired)."""
    try:
        from current_state.pipeline import get_expected_targets
        expected = get_expected_targets(df)
    except Exception:
        expected = []
    # Exclude evaluable gates from training (same as command-line pipeline)
    trainable = [t for t in expected if t in df.columns and not t.endswith('_evaluable_gate')]
    return trainable  # No cap; train all targets to match CLI results


# Block C1: target -> evaluable gate column (restrict to evaluable patients per outcome)
TARGET_TO_GATE: Dict[str, str] = {
    "D30_response_3class": "D30_evaluable_gate",
    "D90_is_cr": "D90_evaluable_gate",
    "cart_response_category_D30": "D30_evaluable_gate",
    "cart_response_90_days": "D90_evaluable_gate",
    "cart_response_6_mos": "M6_evaluable_gate",
    "cart_response_1_yr": "Y1_evaluable_gate",
    "best_response": "BEST_evaluable_gate",
}


def _gate_column_for_target(target: str) -> Optional[str]:
    """Return evaluable gate column for this target, or None if no gate (Block C1)."""
    return TARGET_TO_GATE.get(target)


def _filter_by_evaluable_gate(df: pd.DataFrame, target: str) -> pd.DataFrame:
    """Restrict to rows evaluable for this target (Block C1). Returns df subset or full df if no gate."""
    gate_col = _gate_column_for_target(target)
    if gate_col is None or gate_col not in df.columns:
        return df
    try:
        return df.loc[df[gate_col].astype(int) == 1].copy()
    except (TypeError, ValueError):
        return df


class ModelTrainingWrapper:
    """Wrapper for training multiple model families per target/phase."""

    MODEL_FAMILIES = ['NN', 'LR', 'RF', 'XGB', 'CB', 'ET', 'LGB', 'SVM']

    def __init__(self, logger: Optional[LogCallback] = None):
        self.logger = logger or self._default_logger

    def _default_logger(self, level: str, source: str, message: str) -> None:
        print(f"[{level}] {source}: {message}")

    def train_models(
        self,
        engineered_df: pd.DataFrame,
        phase: str,
        feature_metadata: Dict[str, Any],
        targets: Optional[List[str]] = None,
        progress_callback: Optional[ProgressCallback] = None,
        cancellation_token: Optional[CancellationToken] = None,
        random_seed: int = 42,
        test_size: float = 0.3,
        model_families_filter: Optional[List[str]] = None,
    ) -> StepResult:
        """
        Train NN, LR, RF, XGB, CB, Extra Trees (ET), LightGBM (LGB), SVM for each target using engineered features.

        Args:
            engineered_df: DataFrame with engineered feature columns and target columns
            phase: Phase identifier (e.g. phase_-6)
            feature_metadata: From feature engineering step (selected_features, etc.)
            targets: Optional list of target columns; if None, derived from df
            progress_callback: Optional progress reporting
            cancellation_token: Optional cancellation
            random_seed: Random seed for splits and models
            test_size: Fraction of data for test set (0–1)
            model_families_filter: If set, train only these families (e.g. ['LR']); skip baselines. For merge-on-load.

        Returns:
            StepResult with data=list[ModelResult], metadata with timing and counts
        """
        start_time = time.time()
        families_to_train = model_families_filter if model_families_filter else self.MODEL_FAMILIES
        add_baselines = model_families_filter is None
        selected_features = feature_metadata.get('selected_features', [])
        if not selected_features:
            return StepResult(
                success=False,
                data=[],
                metadata={'training_time_sec': time.time() - start_time},
                errors=['No selected_features in feature_metadata']
            )

        target_list = targets or _get_targets_list(engineered_df)
        if not target_list:
            return StepResult(
                success=False,
                data=[],
                metadata={'training_time_sec': time.time() - start_time},
                errors=['No target columns found in dataframe']
            )

        results: List[ModelResult] = []
        roc_curves: List[Tuple[str, str, str, List[float], List[float]]] = []
        confusion_matrices: List[Tuple[str, str, str, List[List[float]]]] = []
        calibration_curves: List[Tuple[str, str, str, List[float], List[float]]] = []
        pr_curves: List[Tuple[str, str, str, List[float], List[float], float]] = []
        bootstrap_cis: List[Tuple[str, str, str, float, float, float]] = []
        feature_importances: List[Tuple[str, str, str, List[Tuple[str, float]]]] = []
        target_summary: List[Dict[str, Any]] = []  # Block C3: class balance per target
        total_work = len(target_list) * (len(families_to_train) + (2 if add_baselines else 0))
        done = 0

        try:
            from sklearn.model_selection import train_test_split
            from sklearn.linear_model import LogisticRegression
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.metrics import (
                accuracy_score, balanced_accuracy_score, f1_score,
                precision_score, recall_score, roc_auc_score, confusion_matrix
            )
            from sklearn.multiclass import OneVsRestClassifier
            from sklearn.calibration import CalibratedClassifierCV
        except ImportError as e:
            return StepResult(
                success=False,
                data=[],
                metadata={'training_time_sec': time.time() - start_time},
                errors=[f'Missing sklearn: {e}']
            )

        # Optional NN trainer (torch)
        nn_trainer = None
        try:
            from versions.nn_module_enhanced_fixed_v6 import EnhancedNeuralNetworkTrainer
            nn_trainer = EnhancedNeuralNetworkTrainer()
        except Exception:
            self.logger('warning', 'ModelTraining', 'NN trainer not available; skipping NN')

        for target in target_list:
            if cancellation_token and cancellation_token.is_cancelled():
                break
            if progress_callback:
                progress_callback(done / max(total_work, 1), f'Target: {target}')

            # Block C1: restrict to evaluable rows for this target when gate exists
            df_for_target = _filter_by_evaluable_gate(engineered_df, target)
            y_enc, target_type, target_index = self._prepare_target(df_for_target, target)
            if len(y_enc) == 0 or len(target_index) == 0:
                continue

            df_sub = df_for_target.loc[target_index]
            X, feat_names = _build_X_from_engineered(df_sub, selected_features, self.logger)
            if X.size == 0:
                continue

            y = np.asarray(y_enc, dtype=np.int64)
            n_classes = len(np.unique(y))
            if n_classes < 2:
                continue

            try:
                strat = y if (np.bincount(y).min() >= 2) else None
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=random_seed, stratify=strat
                )
            except ValueError:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=random_seed
                )

            # Block C3: record class balance and sample sizes per target
            train_counts = dict(zip(*np.unique(y_train, return_counts=True)))
            test_counts = dict(zip(*np.unique(y_test, return_counts=True)))
            target_summary.append({
                "target": target,
                "phase": phase,
                "n_total": len(y),
                "n_train": len(y_train),
                "n_test": len(y_test),
                "train_class_counts": {int(k): int(v) for k, v in train_counts.items()},
                "test_class_counts": {int(k): int(v) for k, v in test_counts.items()},
                "gate_filtered": _gate_column_for_target(target) is not None,
            })

            # Add dominant-class (majority) and random baselines on same split for comparison (skip when filtering)
            if add_baselines:
                majority_metrics, random_metrics = _compute_baseline_metrics(
                    y_train, y_test, random_seed
                )
                n_samples = len(y_train) + len(y_test)
                results.append(ModelResult(
                    target=target,
                    phase=phase,
                    model_family="Baseline-Majority",
                    accuracy=majority_metrics["accuracy"],
                    balanced_accuracy=majority_metrics["balanced_accuracy"],
                    auc=majority_metrics["auc"],
                    f1_score=majority_metrics["f1_score"],
                    precision=majority_metrics["precision"],
                    recall=majority_metrics["recall"],
                    train_time=0.0,
                    threshold=0.5,
                    sample_size=n_samples,
                ))
                results.append(ModelResult(
                    target=target,
                    phase=phase,
                    model_family="Baseline-Random",
                    accuracy=random_metrics["accuracy"],
                    balanced_accuracy=random_metrics["balanced_accuracy"],
                    auc=random_metrics["auc"],
                    f1_score=random_metrics["f1_score"],
                    precision=random_metrics["precision"],
                    recall=random_metrics["recall"],
                    train_time=0.0,
                    threshold=0.5,
                    sample_size=n_samples,
                ))

            # Train each model family
            for model_family in families_to_train:
                if cancellation_token and cancellation_token.is_cancelled():
                    break
                t0 = time.time()
                try:
                    if model_family == 'NN' and nn_trainer is not None:
                        res = self._train_nn(
                            nn_trainer, X_train, y_train, X_test, y_test,
                            target_type, target
                        )
                    elif model_family == 'LR':
                        res = self._train_lr(
                            X_train, y_train, X_test, y_test, n_classes, random_seed, feat_names
                        )
                    elif model_family == 'RF':
                        res = self._train_rf(
                            X_train, y_train, X_test, y_test, n_classes, random_seed, feat_names
                        )
                    elif model_family == 'XGB':
                        res = self._train_xgb(
                            X_train, y_train, X_test, y_test, n_classes, random_seed, feat_names
                        )
                    elif model_family == 'CB':
                        res = self._train_catboost(
                            X_train, y_train, X_test, y_test, n_classes, random_seed, feat_names
                        )
                    elif model_family == 'ET':
                        res = self._train_extra_trees(
                            X_train, y_train, X_test, y_test, n_classes, random_seed, feat_names
                        )
                    elif model_family == 'LGB':
                        res = self._train_lightgbm(
                            X_train, y_train, X_test, y_test, n_classes, random_seed, feat_names
                        )
                    elif model_family == 'SVM':
                        res = self._train_svm(
                            X_train, y_train, X_test, y_test, n_classes, random_seed
                        )
                    else:
                        res = None
                    train_time = time.time() - t0
                    if res:
                        results.append(ModelResult(
                            target=target,
                            phase=phase,
                            model_family=model_family,
                            accuracy=res.get('accuracy', 0.0),
                            balanced_accuracy=res.get('balanced_accuracy', 0.0),
                            auc=res.get('auc', 0.0),
                            f1_score=res.get('f1_score', 0.0),
                            precision=res.get('precision', 0.0),
                            recall=res.get('recall', 0.0),
                            train_time=train_time,
                            threshold=res.get('threshold', 0.5),
                            sample_size=len(y_train) + len(y_test)
                        ))
                        # Store ROC and confusion matrix for visualization (Phase 5)
                        # Include phase for multi-phase runs (Run all phases)
                        if 'roc_fpr' in res and 'roc_tpr' in res:
                            roc_curves.append((phase, target, model_family, res['roc_fpr'], res['roc_tpr']))
                        if 'confusion_matrix' in res:
                            confusion_matrices.append((phase, target, model_family, res['confusion_matrix']))
                        # Academic paper standards: calibration and PR curves (binary only)
                        if 'calibration_frac' in res and 'calibration_mean' in res:
                            calibration_curves.append((
                                phase, target, model_family,
                                res['calibration_frac'], res['calibration_mean']
                            ))
                        if 'pr_precision' in res and 'pr_recall' in res:
                            auprc = res.get('auprc', 0.0)
                            pr_curves.append((
                                phase, target, model_family,
                                res['pr_precision'], res['pr_recall'], auprc
                            ))
                        if 'bootstrap_ba_mean' in res:
                            bootstrap_cis.append((
                                phase, target, model_family,
                                res['bootstrap_ba_mean'],
                                res['bootstrap_ba_low'],
                                res['bootstrap_ba_high'],
                            ))
                        if 'feature_importance' in res and res['feature_importance']:
                            feature_importances.append((
                                phase, target, model_family,
                                list(res['feature_importance']),
                            ))
                except Exception as e:
                    self.logger('error', 'ModelTraining', f'{model_family} {target}: {e}')
                done += 1

        elapsed = time.time() - start_time
        if progress_callback:
            progress_callback(1.0, "Training complete")
        meta = {
            'phase': phase,
            'targets_trained': len(target_list),
            'model_results_count': len(results),
            'training_time_sec': elapsed,
        }
        if roc_curves:
            meta['roc_curves'] = roc_curves
        if confusion_matrices:
            meta['confusion_matrices'] = confusion_matrices
        if calibration_curves:
            meta['calibration_curves'] = calibration_curves
        if pr_curves:
            meta['pr_curves'] = pr_curves
        if bootstrap_cis:
            meta['bootstrap_cis'] = bootstrap_cis
        if feature_importances:
            meta['feature_importances'] = feature_importances
        if target_summary:
            meta['target_summary'] = target_summary
        return StepResult(
            success=len(results) > 0,
            data=results,
            metadata=meta,
        )

    def run_kfold_cv(
        self,
        engineered_df: pd.DataFrame,
        phase: str,
        feature_metadata: Dict[str, Any],
        n_splits: int = 5,
        random_seed: int = 42,
        progress_callback: Optional[ProgressCallback] = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> Dict[str, Tuple[float, float]]:
        """
        Run stratified K-fold CV; return aggregated metrics (mean, std) across all folds and models.
        Returns dict with keys accuracy, balanced_accuracy, auc, f1_score; values are (mean, std).
        """
        try:
            from sklearn.model_selection import StratifiedKFold
        except ImportError:
            return {}
        selected_features = feature_metadata.get('selected_features', [])
        if not selected_features:
            return {}
        target_list = _get_targets_list(engineered_df)
        if not target_list:
            return {}
        nn_trainer = None
        try:
            from versions.nn_module_enhanced_fixed_v6 import EnhancedNeuralNetworkTrainer
            nn_trainer = EnhancedNeuralNetworkTrainer()
        except Exception:
            pass
        accs, bas, aucs, f1s = [], [], [], []
        total_folds = 0
        for target in target_list:
            if cancellation_token and cancellation_token.is_cancelled():
                break
            y_enc, target_type, target_index = self._prepare_target(engineered_df, target)
            if len(y_enc) == 0 or len(target_index) == 0:
                continue
            df_sub = engineered_df.loc[target_index]
            X, _ = _build_X_from_engineered(df_sub, selected_features, self.logger)
            if X.size == 0:
                continue
            y = np.asarray(y_enc, dtype=np.int64)
            n_classes = len(np.unique(y))
            if n_classes < 2:
                continue
            try:
                skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_seed)
            except Exception:
                continue
            for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y)):
                if cancellation_token and cancellation_token.is_cancelled():
                    break
                X_train, X_test = X[train_idx], X[test_idx]
                y_train, y_test = y[train_idx], y[test_idx]
                if progress_callback:
                    progress_callback((total_folds + fold_idx) / max(n_splits * len(target_list), 1), f"{target} fold {fold_idx+1}")
                for model_family in self.MODEL_FAMILIES:
                    try:
                        if model_family == 'NN' and nn_trainer is not None:
                            res = self._train_nn(nn_trainer, X_train, y_train, X_test, y_test, target_type, target)
                        elif model_family == 'LR':
                            res = self._train_lr(X_train, y_train, X_test, y_test, n_classes, random_seed)
                        elif model_family == 'RF':
                            res = self._train_rf(X_train, y_train, X_test, y_test, n_classes, random_seed)
                        elif model_family == 'XGB':
                            res = self._train_xgb(X_train, y_train, X_test, y_test, n_classes, random_seed)
                        elif model_family == 'CB':
                            res = self._train_catboost(X_train, y_train, X_test, y_test, n_classes, random_seed)
                        elif model_family == 'ET':
                            res = self._train_extra_trees(X_train, y_train, X_test, y_test, n_classes, random_seed)
                        elif model_family == 'LGB':
                            res = self._train_lightgbm(X_train, y_train, X_test, y_test, n_classes, random_seed)
                        elif model_family == 'SVM':
                            res = self._train_svm(X_train, y_train, X_test, y_test, n_classes, random_seed)
                        else:
                            res = None
                        if res:
                            accs.append(res.get('accuracy', 0.0))
                            bas.append(res.get('balanced_accuracy', 0.0))
                            aucs.append(res.get('auc', 0.0))
                            f1s.append(res.get('f1_score', 0.0))
                    except Exception:
                        pass
            total_folds += n_splits
        if not accs:
            return {}
        def mean_std(vals):
            a = np.array(vals)
            return float(np.mean(a)), float(np.std(a)) if len(a) > 1 else (float(np.mean(a)), 0.0)
        return {
            'accuracy': mean_std(accs),
            'balanced_accuracy': mean_std(bas),
            'auc': mean_std(aucs),
            'f1_score': mean_std(f1s),
        }

    def train_models_with_cv(
        self,
        engineered_df: pd.DataFrame,
        phase: str,
        feature_metadata: Dict[str, Any],
        targets: Optional[List[str]] = None,
        n_outer_splits: int = 5,
        progress_callback: Optional[ProgressCallback] = None,
        cancellation_token: Optional[CancellationToken] = None,
        random_seed: int = 42,
        model_families_filter: Optional[List[str]] = None,
        cv_curve_source: str = "last_outer_fold",
        test_size: float = 0.3,
    ) -> StepResult:
        """
        Train models with stratified K-fold CV; report mean ± std (and 95% CI from folds) per (target, model).
        Returns StepResult with data=list[ModelResult] where primary metrics are means and *_std / ci fields are set.
        """
        start_time = time.time()
        selected_features = feature_metadata.get('selected_features', [])
        if not selected_features:
            return StepResult(
                success=False,
                data=[],
                metadata={'training_time_sec': time.time() - start_time},
                errors=['No selected_features in feature_metadata'],
            )
        target_list = targets or _get_targets_list(engineered_df)
        if not target_list:
            return StepResult(
                success=False,
                data=[],
                metadata={'training_time_sec': time.time() - start_time},
                errors=['No target columns found in dataframe'],
            )
        try:
            from sklearn.model_selection import StratifiedKFold
        except ImportError:
            return StepResult(
                success=False,
                data=[],
                metadata={'training_time_sec': time.time() - start_time},
                errors=['StratifiedKFold not available'],
            )
        nn_trainer = None
        try:
            from versions.nn_module_enhanced_fixed_v6 import EnhancedNeuralNetworkTrainer
            nn_trainer = EnhancedNeuralNetworkTrainer()
        except Exception:
            pass

        families_to_train = model_families_filter if model_families_filter else self.MODEL_FAMILIES
        results: List[ModelResult] = []
        cv_target_summary: List[Dict[str, Any]] = []  # Block C3
        roc_curves: List[Tuple[str, str, str, List[float], List[float]]] = []
        confusion_matrices: List[Tuple[str, str, str, List[List[float]]]] = []
        calibration_curves: List[Tuple[str, str, str, List[float], List[float]]] = []
        pr_curves: List[Tuple[str, str, str, List[float], List[float], float]] = []
        want_last_fold = cv_curve_source == "last_outer_fold"
        want_refit = cv_curve_source == "refit_holdout"
        n_model_fams = len(families_to_train)
        total_work = len(target_list) * n_outer_splits * (n_model_fams + 2)  # +2 baselines
        done = 0

        for target in target_list:
            if cancellation_token and cancellation_token.is_cancelled():
                break
            # Block C1: restrict to evaluable rows for this target when gate exists
            df_for_target = _filter_by_evaluable_gate(engineered_df, target)
            y_enc, target_type, target_index = self._prepare_target(df_for_target, target)
            if len(y_enc) == 0 or len(target_index) == 0:
                continue
            df_sub = df_for_target.loc[target_index]
            X, feat_names = _build_X_from_engineered(df_sub, selected_features, self.logger)
            if X.size == 0:
                continue
            y = np.asarray(y_enc, dtype=np.int64)
            n_classes = len(np.unique(y))
            if n_classes < 2:
                continue
            strat = y if (np.bincount(y).min() >= 2) else None
            try:
                skf = StratifiedKFold(n_splits=n_outer_splits, shuffle=True, random_state=random_seed)
                fold_indices = list(skf.split(X, y))
            except Exception:
                continue

            n_folds = len(fold_indices)

            # Collect per-fold metrics: key (model_family) -> lists of acc, ba, auc, f1
            agg: Dict[str, List[Tuple[float, float, float, float]]] = {}
            for model_fam in ["Baseline-Majority", "Baseline-Random"] + families_to_train:
                agg[model_fam] = []

            for fold_idx, (train_idx, test_idx) in enumerate(fold_indices):
                if cancellation_token and cancellation_token.is_cancelled():
                    break
                is_last_fold = fold_idx == n_folds - 1
                X_train, X_test = X[train_idx], X[test_idx]
                y_train, y_test = y[train_idx], y[test_idx]
                n_samples_fold = len(y_train) + len(y_test)
                seed_fold = random_seed + fold_idx

                majority_metrics, random_metrics = _compute_baseline_metrics(
                    y_train, y_test, random_seed + fold_idx
                )
                agg["Baseline-Majority"].append((
                    majority_metrics["accuracy"], majority_metrics["balanced_accuracy"],
                    majority_metrics["auc"], majority_metrics["f1_score"],
                ))
                agg["Baseline-Random"].append((
                    random_metrics["accuracy"], random_metrics["balanced_accuracy"],
                    random_metrics["auc"], random_metrics["f1_score"],
                ))

                for model_family in families_to_train:
                    if cancellation_token and cancellation_token.is_cancelled():
                        break
                    if progress_callback:
                        progress_callback(done / max(total_work, 1), f"{target} fold {fold_idx+1} {model_family}")
                    try:
                        if model_family == 'NN' and nn_trainer is not None:
                            res = self._train_nn(
                                nn_trainer, X_train, y_train, X_test, y_test, target_type, target
                            )
                        elif model_family == 'LR':
                            res = self._train_lr(
                                X_train, y_train, X_test, y_test, n_classes, seed_fold, feat_names
                            )
                        elif model_family == 'RF':
                            res = self._train_rf(
                                X_train, y_train, X_test, y_test, n_classes, seed_fold, feat_names
                            )
                        elif model_family == 'XGB':
                            res = self._train_xgb(
                                X_train, y_train, X_test, y_test, n_classes, seed_fold, feat_names
                            )
                        elif model_family == 'CB':
                            res = self._train_catboost(
                                X_train, y_train, X_test, y_test, n_classes, seed_fold
                            )
                        elif model_family == 'ET':
                            res = self._train_extra_trees(
                                X_train, y_train, X_test, y_test, n_classes, seed_fold, feat_names
                            )
                        elif model_family == 'LGB':
                            res = self._train_lightgbm(
                                X_train, y_train, X_test, y_test, n_classes, seed_fold, feat_names
                            )
                        elif model_family == 'SVM':
                            res = self._train_svm(
                                X_train, y_train, X_test, y_test, n_classes, seed_fold
                            )
                        else:
                            res = None
                        if res:
                            agg[model_family].append((
                                res.get('accuracy', 0.0),
                                res.get('balanced_accuracy', 0.0),
                                res.get('auc', 0.0),
                                res.get('f1_score', 0.0),
                            ))
                        if want_last_fold and is_last_fold and res:
                            try:
                                _append_viz_from_model_output(
                                    phase, target, model_family, res,
                                    roc_curves, confusion_matrices, calibration_curves, pr_curves,
                                )
                            except Exception:
                                pass
                    except Exception:
                        pass
                    done += 1
                done += 2  # baselines

            def mean_std_percentile(vals: List[Tuple[float, float, float, float]]) -> Tuple[float, float, float, float, float, float, float, float, float]:
                if not vals:
                    return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                accs = [v[0] for v in vals]
                bas = [v[1] for v in vals]
                aucs = [v[2] for v in vals]
                f1s = [v[3] for v in vals]
                n = len(vals)
                mean_acc = float(np.mean(accs))
                mean_ba = float(np.mean(bas))
                mean_auc = float(np.mean(aucs))
                mean_f1 = float(np.mean(f1s))
                std_ba = float(np.std(bas)) if n > 1 else 0.0
                std_auc = float(np.std(aucs)) if n > 1 else 0.0
                std_f1 = float(np.std(f1s)) if n > 1 else 0.0
                ba_lo = float(np.percentile(bas, 2.5)) if n >= 2 else mean_ba
                ba_hi = float(np.percentile(bas, 97.5)) if n >= 2 else mean_ba
                return mean_acc, mean_ba, mean_auc, mean_f1, std_ba, std_auc, std_f1, ba_lo, ba_hi

            for model_fam in ["Baseline-Majority", "Baseline-Random"] + families_to_train:
                vals = agg.get(model_fam, [])
                if not vals:
                    continue
                mean_acc, mean_ba, mean_auc, mean_f1, std_ba, std_auc, std_f1, ba_lo, ba_hi = mean_std_percentile(vals)
                if len(vals) < 2:
                    std_ba = std_auc = std_f1 = 0.0
                    ba_lo = ba_hi = mean_ba
                results.append(ModelResult(
                    target=target,
                    phase=phase,
                    model_family=model_fam,
                    accuracy=mean_acc,
                    balanced_accuracy=mean_ba,
                    auc=mean_auc,
                    f1_score=mean_f1,
                    precision=0.0,
                    recall=0.0,
                    train_time=0.0,
                    threshold=0.5,
                    sample_size=len(y),
                    balanced_accuracy_std=std_ba,
                    auc_std=std_auc,
                    f1_score_std=std_f1,
                    balanced_accuracy_ci_low=ba_lo,
                    balanced_accuracy_ci_high=ba_hi,
                ))

            # Block C3: class balance summary for CV (overall y)
            uniq, counts = np.unique(y, return_counts=True)
            class_counts = {int(k): int(v) for k, v in zip(uniq, counts)}
            cv_target_summary.append({
                "target": target,
                "phase": phase,
                "n_total": len(y),
                "class_counts": class_counts,
                "gate_filtered": _gate_column_for_target(target) is not None,
            })

        elapsed = time.time() - start_time
        if progress_callback:
            progress_callback(1.0, "CV training complete")
        meta = {
            'phase': phase,
            'targets_trained': len(target_list),
            'model_results_count': len(results),
            'training_time_sec': elapsed,
            'n_outer_splits': n_outer_splits,
        }
        if cv_target_summary:
            meta['target_summary'] = cv_target_summary
        meta['curve_source'] = cv_curve_source
        if want_refit:
            r_roc, r_cm, r_cal, r_pr = self._collect_refit_holdout_visualization_curves(
                engineered_df,
                phase,
                feature_metadata,
                target_list,
                families_to_train,
                test_size,
                random_seed,
                progress_callback=progress_callback,
                cancellation_token=cancellation_token,
            )
            meta['roc_curves'] = r_roc
            meta['confusion_matrices'] = r_cm
            meta['calibration_curves'] = r_cal
            meta['pr_curves'] = r_pr
            meta['curve_note'] = (
                f"Figures from stratified holdout (test_size={test_size}, random_seed={random_seed}); "
                "CV metrics above are unchanged."
            )
        else:
            if want_last_fold and roc_curves:
                meta['roc_curves'] = roc_curves
            if want_last_fold and confusion_matrices:
                meta['confusion_matrices'] = confusion_matrices
            if want_last_fold and calibration_curves:
                meta['calibration_curves'] = calibration_curves
            if want_last_fold and pr_curves:
                meta['pr_curves'] = pr_curves
            if want_last_fold:
                meta['curve_note'] = (
                    f"Illustrative curves from last outer CV fold (index {n_outer_splits - 1} of {n_outer_splits}); "
                    "not a pooled cross-validated ROC."
                )
        return StepResult(
            success=len(results) > 0,
            data=results,
            metadata=meta,
        )

    def train_models_repeated_holdout(
        self,
        engineered_df: pd.DataFrame,
        phase: str,
        feature_metadata: Dict[str, Any],
        targets: Optional[List[str]] = None,
        n_repeats: int = 3,
        test_size: float = 0.3,
        progress_callback: Optional[ProgressCallback] = None,
        cancellation_token: Optional[CancellationToken] = None,
        random_seed: int = 42,
        model_families_filter: Optional[List[str]] = None,
    ) -> StepResult:
        """
        Train models with repeated holdout: n_repeats independent 70/30 splits (different seeds).
        Reports mean ± std and 95% CI (percentile) per (target, model). Same output shape as train_models_with_cv.
        """
        start_time = time.time()
        selected_features = feature_metadata.get('selected_features', [])
        if not selected_features:
            return StepResult(
                success=False,
                data=[],
                metadata={'training_time_sec': time.time() - start_time},
                errors=['No selected_features in feature_metadata'],
            )
        target_list = targets or _get_targets_list(engineered_df)
        if not target_list:
            return StepResult(
                success=False,
                data=[],
                metadata={'training_time_sec': time.time() - start_time},
                errors=['No target columns found in dataframe'],
            )
        try:
            from sklearn.model_selection import train_test_split
        except ImportError:
            return StepResult(
                success=False,
                data=[],
                metadata={'training_time_sec': time.time() - start_time},
                errors=['train_test_split not available'],
            )
        nn_trainer = None
        try:
            from versions.nn_module_enhanced_fixed_v6 import EnhancedNeuralNetworkTrainer
            nn_trainer = EnhancedNeuralNetworkTrainer()
        except Exception:
            pass

        # agg[model_fam][target] = list of (acc, ba, auc, f1) across repeats
        model_fams = ["Baseline-Majority", "Baseline-Random"] + self.MODEL_FAMILIES
        agg: Dict[str, Dict[str, List[Tuple[float, float, float, float]]]] = {
            m: {t: [] for t in target_list} for m in model_fams
        }
        cv_target_summary: List[Dict[str, Any]] = []
        total_work = n_repeats * len(target_list) * (len(self.MODEL_FAMILIES) + 2)
        done = 0
        last_roc: List[Tuple[str, str, str, List[float], List[float]]] = []
        last_cm: List[Tuple[str, str, str, List[List[float]]]] = []

        for rep in range(n_repeats):
            seed = random_seed + rep
            if progress_callback:
                progress_callback(done / max(total_work, 1), f"Repeated holdout repeat {rep + 1}/{n_repeats}")

            for target in target_list:
                if cancellation_token and cancellation_token.is_cancelled():
                    break
                df_for_target = _filter_by_evaluable_gate(engineered_df, target)
                y_enc, target_type, target_index = self._prepare_target(df_for_target, target)
                if len(y_enc) == 0 or len(target_index) == 0:
                    continue
                df_sub = df_for_target.loc[target_index]
                X, _ = _build_X_from_engineered(df_sub, selected_features, self.logger)
                if X.size == 0:
                    continue
                y = np.asarray(y_enc, dtype=np.int64)
                n_classes = len(np.unique(y))
                if n_classes < 2:
                    continue
                try:
                    strat = y if (np.bincount(y).min() >= 2) else None
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, test_size=test_size, random_state=seed, stratify=strat
                    )
                except ValueError:
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, test_size=test_size, random_state=seed
                    )
                if rep == 0:
                    uniq, counts = np.unique(y, return_counts=True)
                    cv_target_summary.append({
                        "target": target,
                        "phase": phase,
                        "n_total": len(y),
                        "class_counts": {int(k): int(v) for k, v in zip(uniq, counts)},
                        "gate_filtered": _gate_column_for_target(target) is not None,
                    })
                majority_metrics, random_metrics = _compute_baseline_metrics(y_train, y_test, seed)
                agg["Baseline-Majority"][target].append((
                    majority_metrics["accuracy"], majority_metrics["balanced_accuracy"],
                    majority_metrics["auc"], majority_metrics["f1_score"],
                ))
                agg["Baseline-Random"][target].append((
                    random_metrics["accuracy"], random_metrics["balanced_accuracy"],
                    random_metrics["auc"], random_metrics["f1_score"],
                ))

                for model_family in self.MODEL_FAMILIES:
                    if cancellation_token and cancellation_token.is_cancelled():
                        break
                    if progress_callback:
                        progress_callback(done / max(total_work, 1), f"Repeat {rep+1} {target} {model_family}")
                    try:
                        if model_family == 'NN' and nn_trainer is not None:
                            res = self._train_nn(nn_trainer, X_train, y_train, X_test, y_test, target_type, target)
                        elif model_family == 'LR':
                            res = self._train_lr(X_train, y_train, X_test, y_test, n_classes, seed)
                        elif model_family == 'RF':
                            res = self._train_rf(X_train, y_train, X_test, y_test, n_classes, seed)
                        elif model_family == 'XGB':
                            res = self._train_xgb(X_train, y_train, X_test, y_test, n_classes, seed)
                        elif model_family == 'CB':
                            res = self._train_catboost(X_train, y_train, X_test, y_test, n_classes, seed)
                        elif model_family == 'ET':
                            res = self._train_extra_trees(X_train, y_train, X_test, y_test, n_classes, seed)
                        elif model_family == 'LGB':
                            res = self._train_lightgbm(X_train, y_train, X_test, y_test, n_classes, seed)
                        elif model_family == 'SVM':
                            res = self._train_svm(X_train, y_train, X_test, y_test, n_classes, seed)
                        else:
                            res = None
                        if res:
                            agg[model_family][target].append((
                                res.get('accuracy', 0.0),
                                res.get('balanced_accuracy', 0.0),
                                res.get('auc', 0.0),
                                res.get('f1_score', 0.0),
                            ))
                            if rep == n_repeats - 1 and 'roc_fpr' in res and 'roc_tpr' in res:
                                last_roc.append((phase, target, model_family, res['roc_fpr'], res['roc_tpr']))
                            if rep == n_repeats - 1 and 'confusion_matrix' in res:
                                last_cm.append((phase, target, model_family, res['confusion_matrix']))
                    except Exception:
                        pass
                    done += 1
                done += 2

        results: List[ModelResult] = []
        for target in target_list:
            n_samples = 0
            for model_fam in model_fams:
                vals = agg[model_fam].get(target, [])
                if not vals:
                    continue
                accs = [v[0] for v in vals]
                bas = [v[1] for v in vals]
                aucs = [v[2] for v in vals]
                f1s = [v[3] for v in vals]
                n = len(vals)
                if n_samples == 0:
                    df_for_target = _filter_by_evaluable_gate(engineered_df, target)
                    _, _, target_index = self._prepare_target(df_for_target, target)
                    n_samples = len(target_index)
                mean_acc = float(np.mean(accs))
                mean_ba = float(np.mean(bas))
                mean_auc = float(np.mean(aucs))
                mean_f1 = float(np.mean(f1s))
                std_ba = float(np.std(bas)) if n > 1 else 0.0
                std_auc = float(np.std(aucs)) if n > 1 else 0.0
                std_f1 = float(np.std(f1s)) if n > 1 else 0.0
                ba_lo = float(np.percentile(bas, 2.5)) if n >= 2 else mean_ba
                ba_hi = float(np.percentile(bas, 97.5)) if n >= 2 else mean_ba
                results.append(ModelResult(
                    target=target,
                    phase=phase,
                    model_family=model_fam,
                    accuracy=mean_acc,
                    balanced_accuracy=mean_ba,
                    auc=mean_auc,
                    f1_score=mean_f1,
                    precision=0.0,
                    recall=0.0,
                    train_time=0.0,
                    threshold=0.5,
                    sample_size=n_samples,
                    balanced_accuracy_std=std_ba,
                    auc_std=std_auc,
                    f1_score_std=std_f1,
                    balanced_accuracy_ci_low=ba_lo,
                    balanced_accuracy_ci_high=ba_hi,
                ))
        elapsed = time.time() - start_time
        if progress_callback:
            progress_callback(1.0, "Repeated holdout complete")
        meta = {
            'phase': phase,
            'targets_trained': len(target_list),
            'model_results_count': len(results),
            'training_time_sec': elapsed,
            'n_repeats': n_repeats,
        }
        if cv_target_summary:
            meta['target_summary'] = cv_target_summary
        if last_roc:
            meta['roc_curves'] = last_roc
        if last_cm:
            meta['confusion_matrices'] = last_cm
        return StepResult(
            success=len(results) > 0,
            data=results,
            metadata=meta,
        )

    def _collect_refit_holdout_visualization_curves(
        self,
        engineered_df: pd.DataFrame,
        phase: str,
        feature_metadata: Dict[str, Any],
        target_list: List[str],
        families_to_train: List[str],
        test_size: float,
        random_seed: int,
        progress_callback: Optional[ProgressCallback] = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> Tuple[
        List[Tuple[str, str, str, List[float], List[float]]],
        List[Tuple[str, str, str, List[List[float]]]],
        List[Tuple[str, str, str, List[float], List[float]]],
        List[Tuple[str, str, str, List[float], List[float], float]],
    ]:
        """
        Single stratified train/test split per target; full model outputs for ROC/CM/calibration/PR only.
        Does not produce ModelResult rows (CV metrics unchanged).
        """
        roc_curves: List[Tuple[str, str, str, List[float], List[float]]] = []
        confusion_matrices: List[Tuple[str, str, str, List[List[float]]]] = []
        calibration_curves: List[Tuple[str, str, str, List[float], List[float]]] = []
        pr_curves: List[Tuple[str, str, str, List[float], List[float], float]] = []
        selected_features = feature_metadata.get('selected_features', [])
        if not selected_features:
            return roc_curves, confusion_matrices, calibration_curves, pr_curves
        try:
            from sklearn.model_selection import train_test_split
        except ImportError:
            return roc_curves, confusion_matrices, calibration_curves, pr_curves
        nn_trainer = None
        try:
            from versions.nn_module_enhanced_fixed_v6 import EnhancedNeuralNetworkTrainer
            nn_trainer = EnhancedNeuralNetworkTrainer()
        except Exception:
            pass
        n_t = max(len(target_list), 1)
        for ti, target in enumerate(target_list):
            if cancellation_token and cancellation_token.is_cancelled():
                break
            if progress_callback:
                progress_callback(ti / n_t, f"Refit holdout (viz): {target}")
            df_for_target = _filter_by_evaluable_gate(engineered_df, target)
            y_enc, target_type, target_index = self._prepare_target(df_for_target, target)
            if len(y_enc) == 0 or len(target_index) == 0:
                continue
            df_sub = df_for_target.loc[target_index]
            X, feat_names = _build_X_from_engineered(df_sub, selected_features, self.logger)
            if X.size == 0:
                continue
            y = np.asarray(y_enc, dtype=np.int64)
            n_classes = len(np.unique(y))
            if n_classes < 2:
                continue
            try:
                strat = y if (np.bincount(y).min() >= 2) else None
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=random_seed, stratify=strat
                )
            except ValueError:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=random_seed
                )
            for model_family in families_to_train:
                if cancellation_token and cancellation_token.is_cancelled():
                    break
                try:
                    if model_family == 'NN' and nn_trainer is not None:
                        res = self._train_nn(
                            nn_trainer, X_train, y_train, X_test, y_test, target_type, target
                        )
                    elif model_family == 'LR':
                        res = self._train_lr(
                            X_train, y_train, X_test, y_test, n_classes, random_seed, feat_names
                        )
                    elif model_family == 'RF':
                        res = self._train_rf(
                            X_train, y_train, X_test, y_test, n_classes, random_seed, feat_names
                        )
                    elif model_family == 'XGB':
                        res = self._train_xgb(
                            X_train, y_train, X_test, y_test, n_classes, random_seed, feat_names
                        )
                    elif model_family == 'CB':
                        res = self._train_catboost(
                            X_train, y_train, X_test, y_test, n_classes, random_seed, feat_names
                        )
                    elif model_family == 'ET':
                        res = self._train_extra_trees(
                            X_train, y_train, X_test, y_test, n_classes, random_seed, feat_names
                        )
                    elif model_family == 'LGB':
                        res = self._train_lightgbm(
                            X_train, y_train, X_test, y_test, n_classes, random_seed, feat_names
                        )
                    elif model_family == 'SVM':
                        res = self._train_svm(
                            X_train, y_train, X_test, y_test, n_classes, random_seed
                        )
                    else:
                        res = None
                    if res:
                        _append_viz_from_model_output(
                            phase, target, model_family, res,
                            roc_curves, confusion_matrices, calibration_curves, pr_curves,
                        )
                except Exception as e:
                    self.logger('warning', 'ModelTraining', f'refit viz {model_family} {target}: {e}')
        return roc_curves, confusion_matrices, calibration_curves, pr_curves

    def train_models_nested_cv(
        self,
        engineered_df: pd.DataFrame,
        phase: str,
        feature_metadata: Dict[str, Any],
        targets: Optional[List[str]] = None,
        n_outer_splits: int = 5,
        n_inner_splits: int = 3,
        progress_callback: Optional[ProgressCallback] = None,
        cancellation_token: Optional[CancellationToken] = None,
        random_seed: int = 42,
        model_families_filter: Optional[List[str]] = None,
        cv_curve_source: str = "last_outer_fold",
        test_size: float = 0.3,
    ) -> StepResult:
        """
        Nested CV: outer loop for evaluation, inner loop for hyperparameter tuning (LR, RF, XGB).
        Other families use default params. Reports mean ± std and 95% CI per (target, model).
        model_families_filter: If set, train only these families (e.g. ['LR']).
        """
        start_time = time.time()
        families_to_train = model_families_filter if model_families_filter else self.MODEL_FAMILIES
        add_baselines = model_families_filter is None
        selected_features = feature_metadata.get('selected_features', [])
        if not selected_features:
            return StepResult(
                success=False,
                data=[],
                metadata={'training_time_sec': time.time() - start_time},
                errors=['No selected_features in feature_metadata'],
            )
        target_list = targets or _get_targets_list(engineered_df)
        if not target_list:
            return StepResult(
                success=False,
                data=[],
                metadata={'training_time_sec': time.time() - start_time},
                errors=['No target columns found in dataframe'],
            )
        try:
            from sklearn.model_selection import StratifiedKFold
        except ImportError:
            return StepResult(
                success=False,
                data=[],
                metadata={'training_time_sec': time.time() - start_time},
                errors=['StratifiedKFold not available'],
            )
        nn_trainer = None
        try:
            from versions.nn_module_enhanced_fixed_v6 import EnhancedNeuralNetworkTrainer
            nn_trainer = EnhancedNeuralNetworkTrainer()
        except Exception:
            pass

        # Hyperparameter grids for inner CV (small grids to limit time)
        def _lr_grid():
            return [{'C': c} for c in [0.1, 1.0, 10.0]]
        def _rf_grid():
            return [{'n_estimators': n, 'max_depth': d} for n in [100, 200] for d in [4, 8]]
        def _xgb_grid():
            return [{'n_estimators': n, 'max_depth': d, 'learning_rate': lr} for n in [200, 400] for d in [4, 6] for lr in [0.05, 0.1]]

        results: List[ModelResult] = []
        cv_target_summary: List[Dict[str, Any]] = []
        roc_curves: List[Tuple[str, str, str, List[float], List[float]]] = []
        confusion_matrices: List[Tuple[str, str, str, List[List[float]]]] = []
        calibration_curves: List[Tuple[str, str, str, List[float], List[float]]] = []
        pr_curves: List[Tuple[str, str, str, List[float], List[float], float]] = []
        want_last_fold = cv_curve_source == "last_outer_fold"
        want_refit = cv_curve_source == "refit_holdout"
        n_baselines = 2 if add_baselines else 0
        total_work = len(target_list) * n_outer_splits * (len(families_to_train) + n_baselines)
        done = 0

        for target in target_list:
            if cancellation_token and cancellation_token.is_cancelled():
                break
            df_for_target = _filter_by_evaluable_gate(engineered_df, target)
            y_enc, target_type, target_index = self._prepare_target(df_for_target, target)
            if len(y_enc) == 0 or len(target_index) == 0:
                continue
            df_sub = df_for_target.loc[target_index]
            X, feat_names = _build_X_from_engineered(df_sub, selected_features, self.logger)
            if X.size == 0:
                continue
            y = np.asarray(y_enc, dtype=np.int64)
            n_classes = len(np.unique(y))
            if n_classes < 2:
                continue
            try:
                skf_outer = StratifiedKFold(n_splits=n_outer_splits, shuffle=True, random_state=random_seed)
                fold_indices = list(skf_outer.split(X, y))
            except Exception:
                continue
            n_folds = len(fold_indices)
            agg: Dict[str, List[Tuple[float, float, float, float]]] = {
                m: [] for m in (["Baseline-Majority", "Baseline-Random"] if add_baselines else []) + families_to_train
            }
            for fold_idx, (train_idx, test_idx) in enumerate(fold_indices):
                if cancellation_token and cancellation_token.is_cancelled():
                    break
                is_last_fold = fold_idx == n_folds - 1
                X_train, X_test = X[train_idx], X[test_idx]
                y_train, y_test = y[train_idx], y[test_idx]
                seed_fold = random_seed + fold_idx
                if add_baselines:
                    majority_metrics, random_metrics = _compute_baseline_metrics(y_train, y_test, seed_fold)
                    agg["Baseline-Majority"].append((
                        majority_metrics["accuracy"], majority_metrics["balanced_accuracy"],
                        majority_metrics["auc"], majority_metrics["f1_score"],
                    ))
                    agg["Baseline-Random"].append((
                        random_metrics["accuracy"], random_metrics["balanced_accuracy"],
                        random_metrics["auc"], random_metrics["f1_score"],
                    ))
                for model_family in families_to_train:
                    if cancellation_token and cancellation_token.is_cancelled():
                        break
                    outer_best_params: Optional[Dict[str, Any]] = None
                    if progress_callback:
                        progress_callback(done / max(total_work, 1), f"Nested CV {target} fold {fold_idx+1} {model_family}")
                    try:
                        if model_family in ('LR', 'RF', 'XGB'):
                            best_params, best_ba = None, -1.0
                            if model_family == 'LR':
                                grid = _lr_grid()
                            elif model_family == 'RF':
                                grid = _rf_grid()
                            else:
                                grid = _xgb_grid()
                            skf_inner = StratifiedKFold(n_splits=n_inner_splits, shuffle=True, random_state=random_seed)
                            for params in grid:
                                inner_bas = []
                                for tr_in, val_in in skf_inner.split(X_train, y_train):
                                    X_tr, X_val = X_train[tr_in], X_train[val_in]
                                    y_tr, y_val = y_train[tr_in], y_train[val_in]
                                    res = self._train_one_with_params(
                                        model_family, X_tr, y_tr, X_val, y_val, n_classes, params, seed_fold
                                    )
                                    if res is not None:
                                        inner_bas.append(res.get('balanced_accuracy', 0.0))
                                if inner_bas and np.mean(inner_bas) > best_ba:
                                    best_ba = float(np.mean(inner_bas))
                                    best_params = params
                            outer_best_params = best_params
                            if best_params is not None:
                                res = self._train_one_with_params(
                                    model_family, X_train, y_train, X_test, y_test, n_classes, best_params, seed_fold
                                )
                            else:
                                res = self._train_lr(X_train, y_train, X_test, y_test, n_classes, seed_fold, feat_names) if model_family == 'LR' else \
                                      self._train_rf(X_train, y_train, X_test, y_test, n_classes, seed_fold, feat_names) if model_family == 'RF' else \
                                      self._train_xgb(X_train, y_train, X_test, y_test, n_classes, seed_fold, feat_names)
                        else:
                            if model_family == 'NN' and nn_trainer is not None:
                                res = self._train_nn(nn_trainer, X_train, y_train, X_test, y_test, target_type, target)
                            elif model_family == 'LR':
                                res = self._train_lr(X_train, y_train, X_test, y_test, n_classes, seed_fold, feat_names)
                            elif model_family == 'RF':
                                res = self._train_rf(X_train, y_train, X_test, y_test, n_classes, seed_fold, feat_names)
                            elif model_family == 'XGB':
                                res = self._train_xgb(X_train, y_train, X_test, y_test, n_classes, seed_fold, feat_names)
                            elif model_family == 'CB':
                                res = self._train_catboost(X_train, y_train, X_test, y_test, n_classes, seed_fold)
                            elif model_family == 'ET':
                                res = self._train_extra_trees(X_train, y_train, X_test, y_test, n_classes, seed_fold)
                            elif model_family == 'LGB':
                                res = self._train_lightgbm(X_train, y_train, X_test, y_test, n_classes, seed_fold)
                            elif model_family == 'SVM':
                                res = self._train_svm(X_train, y_train, X_test, y_test, n_classes, seed_fold)
                            else:
                                res = None
                        if res:
                            agg[model_family].append((
                                res.get('accuracy', 0.0),
                                res.get('balanced_accuracy', 0.0),
                                res.get('auc', 0.0),
                                res.get('f1_score', 0.0),
                            ))
                        if want_last_fold and is_last_fold and res:
                            try:
                                if model_family in ('LR', 'RF', 'XGB') and outer_best_params is not None:
                                    if model_family == 'LR':
                                        viz_res = self._train_lr(
                                            X_train, y_train, X_test, y_test, n_classes, seed_fold, feat_names,
                                            hyperparams=outer_best_params,
                                        )
                                    elif model_family == 'RF':
                                        viz_res = self._train_rf(
                                            X_train, y_train, X_test, y_test, n_classes, seed_fold, feat_names,
                                            hyperparams=outer_best_params,
                                        )
                                    else:
                                        viz_res = self._train_xgb(
                                            X_train, y_train, X_test, y_test, n_classes, seed_fold, feat_names,
                                            hyperparams=outer_best_params,
                                        )
                                    _append_viz_from_model_output(
                                        phase, target, model_family, viz_res,
                                        roc_curves, confusion_matrices, calibration_curves, pr_curves,
                                    )
                                else:
                                    _append_viz_from_model_output(
                                        phase, target, model_family, res,
                                        roc_curves, confusion_matrices, calibration_curves, pr_curves,
                                    )
                            except Exception:
                                pass
                    except Exception:
                        pass
                    done += 1
                done += n_baselines  # baselines per fold

            def mean_std_ci(vals):
                if not vals:
                    return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                accs, bas, aucs, f1s = [v[0] for v in vals], [v[1] for v in vals], [v[2] for v in vals], [v[3] for v in vals]
                n = len(vals)
                return (
                    float(np.mean(accs)), float(np.mean(bas)), float(np.mean(aucs)), float(np.mean(f1s)),
                    float(np.std(bas)) if n > 1 else 0.0,
                    float(np.std(aucs)) if n > 1 else 0.0,
                    float(np.std(f1s)) if n > 1 else 0.0,
                    float(np.percentile(bas, 2.5)) if n >= 2 else float(np.mean(bas)),
                    float(np.percentile(bas, 97.5)) if n >= 2 else float(np.mean(bas)),
                )
            for model_fam in (["Baseline-Majority", "Baseline-Random"] if add_baselines else []) + families_to_train:
                vals = agg.get(model_fam, [])
                if not vals:
                    continue
                mean_acc, mean_ba, mean_auc, mean_f1, std_ba, std_auc, std_f1, ba_lo, ba_hi = mean_std_ci(vals)
                results.append(ModelResult(
                    target=target,
                    phase=phase,
                    model_family=model_fam,
                    accuracy=mean_acc,
                    balanced_accuracy=mean_ba,
                    auc=mean_auc,
                    f1_score=mean_f1,
                    precision=0.0,
                    recall=0.0,
                    train_time=0.0,
                    threshold=0.5,
                    sample_size=len(y),
                    balanced_accuracy_std=std_ba,
                    auc_std=std_auc,
                    f1_score_std=std_f1,
                    balanced_accuracy_ci_low=ba_lo,
                    balanced_accuracy_ci_high=ba_hi,
                ))
            uniq, counts = np.unique(y, return_counts=True)
            cv_target_summary.append({
                "target": target,
                "phase": phase,
                "n_total": len(y),
                "class_counts": {int(k): int(v) for k, v in zip(uniq, counts)},
                "gate_filtered": _gate_column_for_target(target) is not None,
            })

        elapsed = time.time() - start_time
        if progress_callback:
            progress_callback(1.0, "Nested CV complete")
        meta = {
            'phase': phase,
            'targets_trained': len(target_list),
            'model_results_count': len(results),
            'training_time_sec': elapsed,
            'n_outer_splits': n_outer_splits,
            'n_inner_splits': n_inner_splits,
        }
        if cv_target_summary:
            meta['target_summary'] = cv_target_summary
        meta['curve_source'] = cv_curve_source
        if want_refit:
            r_roc, r_cm, r_cal, r_pr = self._collect_refit_holdout_visualization_curves(
                engineered_df,
                phase,
                feature_metadata,
                target_list,
                families_to_train,
                test_size,
                random_seed,
                progress_callback=progress_callback,
                cancellation_token=cancellation_token,
            )
            meta['roc_curves'] = r_roc
            meta['confusion_matrices'] = r_cm
            meta['calibration_curves'] = r_cal
            meta['pr_curves'] = r_pr
            meta['curve_note'] = (
                f"Figures from stratified holdout (test_size={test_size}, random_seed={random_seed}); "
                "CV metrics above are unchanged."
            )
        else:
            if want_last_fold and roc_curves:
                meta['roc_curves'] = roc_curves
            if want_last_fold and confusion_matrices:
                meta['confusion_matrices'] = confusion_matrices
            if want_last_fold and calibration_curves:
                meta['calibration_curves'] = calibration_curves
            if want_last_fold and pr_curves:
                meta['pr_curves'] = pr_curves
            if want_last_fold:
                meta['curve_note'] = (
                    f"Illustrative curves from last outer CV fold (index {n_outer_splits - 1} of {n_outer_splits}); "
                    "not a pooled cross-validated ROC."
                )
        return StepResult(
            success=len(results) > 0,
            data=results,
            metadata=meta,
        )

    def _train_one_with_params(
        self,
        model_family: str,
        X_train: np.ndarray, y_train: np.ndarray,
        X_test: np.ndarray, y_test: np.ndarray,
        n_classes: int,
        params: Dict[str, Any],
        random_seed: int,
    ) -> Optional[Dict[str, Any]]:
        """Train a single model family with given params (for nested CV inner loop)."""
        if model_family == 'LR':
            from sklearn.linear_model import LogisticRegression
            from sklearn.multiclass import OneVsRestClassifier
            C = params.get('C', 1.0)
            clf = OneVsRestClassifier(LogisticRegression(max_iter=1000, solver='lbfgs', C=C, class_weight='balanced', random_state=random_seed))
            clf.fit(X_train, y_train)
            pred = clf.predict(X_test)
            from sklearn.metrics import balanced_accuracy_score
            return {'balanced_accuracy': float(balanced_accuracy_score(y_test, pred)), 'accuracy': 0.0, 'auc': 0.0, 'f1_score': 0.0}
        if model_family == 'RF':
            from sklearn.ensemble import RandomForestClassifier
            clf = RandomForestClassifier(
                n_estimators=params.get('n_estimators', 400),
                max_depth=params.get('max_depth', None),
                min_samples_leaf=2, class_weight='balanced',
                random_state=random_seed, n_jobs=-1,
            )
            clf.fit(X_train, y_train)
            pred = clf.predict(X_test)
            from sklearn.metrics import balanced_accuracy_score
            return {'balanced_accuracy': float(balanced_accuracy_score(y_test, pred)), 'accuracy': 0.0, 'auc': 0.0, 'f1_score': 0.0}
        if model_family == 'XGB':
            try:
                from xgboost import XGBClassifier
                clf = XGBClassifier(
                    n_estimators=params.get('n_estimators', 400),
                    max_depth=params.get('max_depth', 6),
                    learning_rate=params.get('learning_rate', 0.05),
                    subsample=0.8, colsample_bytree=0.8,
                    objective='binary:logistic' if n_classes == 2 else 'multi:softmax',
                    n_jobs=-1, random_state=random_seed,
                )
                clf.fit(X_train, y_train)
                pred = clf.predict(X_test)
                from sklearn.metrics import balanced_accuracy_score
                return {'balanced_accuracy': float(balanced_accuracy_score(y_test, pred)), 'accuracy': 0.0, 'auc': 0.0, 'f1_score': 0.0}
            except Exception:
                return None
        return None

    def _prepare_target(
        self, df: pd.DataFrame, target_col: str
    ) -> Tuple[np.ndarray, str, pd.Index]:
        """Prepare target variable; delegate to NN trainer if available."""
        if target_col not in df.columns:
            return np.array([]), 'unknown', pd.Index([])
        try:
            from versions.nn_module_enhanced_fixed_v6 import EnhancedNeuralNetworkTrainer
            trainer = EnhancedNeuralNetworkTrainer()
            return trainer.prepare_target(df, target_col, target_col)
        except Exception:
            pass
        # Fallback: simple numeric/categorical encoding
        from sklearn.preprocessing import LabelEncoder
        s = df[target_col].dropna().astype(str).str.strip()
        s = s[~(s == '')]
        if len(s) < 10 or s.nunique() < 2:
            return np.array([]), 'unknown', pd.Index([])
        le = LabelEncoder()
        y = le.fit_transform(s)
        return y, 'binary' if len(np.unique(y)) == 2 else 'multiclass', s.index

    def _train_nn(
        self,
        trainer: Any,
        X_train: np.ndarray, y_train: np.ndarray,
        X_test: np.ndarray, y_test: np.ndarray,
        target_type: str, target_name: str
    ) -> Dict[str, Any]:
        """Train neural network via existing trainer."""
        from sklearn.metrics import (
            balanced_accuracy_score, f1_score, roc_auc_score,
            roc_curve, confusion_matrix
        )
        # NN trainer expects integer labels (LongTensor); ensure no float dtype
        y_train = np.asarray(y_train, dtype=np.int64)
        y_test = np.asarray(y_test, dtype=np.int64)
        out = trainer.train_model(
            X_train, y_train, X_test, y_test, target_type, target_name
        )
        acc = float(out.get('accuracy', 0.0))
        ba, auc, f1 = acc, 0.0, 0.0
        result = {
            'accuracy': acc,
            'balanced_accuracy': ba,
            'auc': auc,
            'f1_score': f1,
            'precision': out.get('precision', 0.0),
            'recall': out.get('recall', 0.0),
            'threshold': 0.5,
            'confusion_matrix': [],
        }
        if 'model' in out:
            import torch
            model = out['model']
            device = next(model.parameters()).device
            with torch.no_grad():
                X_t = torch.FloatTensor(X_test).to(device)
                pred = model(X_t)
                if target_type == 'binary':
                    proba = torch.sigmoid(pred).cpu().numpy().ravel()
                    pred_np = (proba > 0.5).astype(int)
                    try:
                        result['auc'] = roc_auc_score(y_test, proba)
                        fpr, tpr, _ = roc_curve(y_test, proba)
                        result['roc_fpr'] = fpr.tolist()
                        result['roc_tpr'] = tpr.tolist()
                        _add_binary_academic_curves(y_test, proba, result)
                    except Exception:
                        pass
                else:
                    pred_np = pred.argmax(dim=1).cpu().numpy()
                    try:
                        from sklearn.preprocessing import label_binarize
                        y_bin = label_binarize(y_test, classes=np.unique(y_test))
                        result['auc'] = roc_auc_score(y_bin, torch.softmax(pred, dim=1).cpu().numpy(), average='macro')
                    except Exception:
                        pass
            result['balanced_accuracy'] = balanced_accuracy_score(y_test, pred_np)
            result['f1_score'] = f1_score(y_test, pred_np, average='macro')
            result['confusion_matrix'] = confusion_matrix(y_test, pred_np).tolist()
            ba_mean, ba_lo, ba_hi = _bootstrap_balanced_accuracy(
                y_test, pred_np, random_state=0
            )
            result['bootstrap_ba_mean'], result['bootstrap_ba_low'], result['bootstrap_ba_high'] = ba_mean, ba_lo, ba_hi
        return result

    def _train_lr(
        self,
        X_train: np.ndarray, y_train: np.ndarray,
        X_test: np.ndarray, y_test: np.ndarray,
        n_classes: int, random_seed: int,
        feat_names: Optional[List[str]] = None,
        hyperparams: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Train Logistic Regression. Optional hyperparams (e.g. C from nested CV grid) for full eval."""
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import (
            accuracy_score, balanced_accuracy_score, f1_score, roc_auc_score,
            roc_curve, confusion_matrix
        )
        from sklearn.multiclass import OneVsRestClassifier

        lr_kw: Dict[str, Any] = dict(
            max_iter=1000, solver='lbfgs', class_weight='balanced', random_state=random_seed
        )
        if hyperparams and 'C' in hyperparams:
            lr_kw['C'] = float(hyperparams['C'])
        clf = OneVsRestClassifier(LogisticRegression(**lr_kw))
        clf.fit(X_train, y_train)
        pred = clf.predict(X_test)
        acc = accuracy_score(y_test, pred)
        ba = balanced_accuracy_score(y_test, pred)
        f1 = f1_score(y_test, pred, average='macro')
        out = {
            'accuracy': acc, 'balanced_accuracy': ba, 'auc': 0.0, 'f1_score': f1,
            'precision': 0.0, 'recall': 0.0, 'threshold': 0.5,
            'confusion_matrix': confusion_matrix(y_test, pred).tolist(),
        }
        if feat_names and len(feat_names) == X_train.shape[1]:
            if n_classes == 2:
                coefs = np.abs(clf.estimators_[0].coef_).ravel()
            else:
                coefs = np.abs(np.vstack([e.coef_ for e in clf.estimators_])).mean(axis=0)
            if len(coefs) == len(feat_names):
                out['feature_importance'] = list(zip(feat_names, coefs.tolist()))
        try:
            if n_classes == 2:
                proba = clf.predict_proba(X_test)[:, 1]
                out['auc'] = roc_auc_score(y_test, proba)
                fpr, tpr, _ = roc_curve(y_test, proba)
                out['roc_fpr'] = fpr.tolist()
                out['roc_tpr'] = tpr.tolist()
                _add_binary_academic_curves(y_test, proba, out)
            else:
                from sklearn.preprocessing import label_binarize
                y_bin = label_binarize(y_test, classes=np.unique(y_test))
                out['auc'] = roc_auc_score(y_bin, clf.predict_proba(X_test), average='macro')
        except Exception:
            pass
        ba_mean, ba_lo, ba_hi = _bootstrap_balanced_accuracy(y_test, pred, random_state=random_seed)
        out['bootstrap_ba_mean'], out['bootstrap_ba_low'], out['bootstrap_ba_high'] = ba_mean, ba_lo, ba_hi
        return out

    def _train_rf(
        self,
        X_train: np.ndarray, y_train: np.ndarray,
        X_test: np.ndarray, y_test: np.ndarray,
        n_classes: int, random_seed: int,
        feat_names: Optional[List[str]] = None,
        hyperparams: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Train Random Forest. Optional hyperparams (n_estimators, max_depth) from nested CV grid."""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import (
            accuracy_score, balanced_accuracy_score, f1_score, roc_auc_score,
            roc_curve, confusion_matrix
        )

        n_est = 400
        max_d = None
        if hyperparams:
            n_est = int(hyperparams.get('n_estimators', n_est))
            max_d = hyperparams.get('max_depth', max_d)
        clf = RandomForestClassifier(
            n_estimators=n_est, max_depth=max_d, min_samples_leaf=2,
            class_weight='balanced', random_state=random_seed, n_jobs=-1
        )
        clf.fit(X_train, y_train)
        pred = clf.predict(X_test)
        acc = accuracy_score(y_test, pred)
        ba = balanced_accuracy_score(y_test, pred)
        f1 = f1_score(y_test, pred, average='macro')
        out = {
            'accuracy': acc, 'balanced_accuracy': ba, 'auc': 0.0, 'f1_score': f1,
            'precision': 0.0, 'recall': 0.0, 'threshold': 0.5,
            'confusion_matrix': confusion_matrix(y_test, pred).tolist(),
        }
        if feat_names and hasattr(clf, 'feature_importances_') and len(clf.feature_importances_) == len(feat_names):
            out['feature_importance'] = list(zip(feat_names, clf.feature_importances_.tolist()))
        try:
            if n_classes == 2:
                proba = clf.predict_proba(X_test)[:, 1]
                out['auc'] = roc_auc_score(y_test, proba)
                fpr, tpr, _ = roc_curve(y_test, proba)
                out['roc_fpr'] = fpr.tolist()
                out['roc_tpr'] = tpr.tolist()
                _add_binary_academic_curves(y_test, proba, out)
            else:
                from sklearn.preprocessing import label_binarize
                y_bin = label_binarize(y_test, classes=np.unique(y_test))
                out['auc'] = roc_auc_score(y_bin, clf.predict_proba(X_test), average='macro')
        except Exception:
            pass
        ba_mean, ba_lo, ba_hi = _bootstrap_balanced_accuracy(y_test, pred, random_state=random_seed)
        out['bootstrap_ba_mean'], out['bootstrap_ba_low'], out['bootstrap_ba_high'] = ba_mean, ba_lo, ba_hi
        return out

    def _train_extra_trees(
        self,
        X_train: np.ndarray, y_train: np.ndarray,
        X_test: np.ndarray, y_test: np.ndarray,
        n_classes: int, random_seed: int,
        feat_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Train Extra Trees (more randomized than RF; sklearn, no extra dependency)."""
        from sklearn.ensemble import ExtraTreesClassifier
        from sklearn.metrics import (
            accuracy_score, balanced_accuracy_score, f1_score, roc_auc_score,
            roc_curve, confusion_matrix
        )
        clf = ExtraTreesClassifier(
            n_estimators=400, max_depth=None, min_samples_leaf=2,
            class_weight='balanced', random_state=random_seed, n_jobs=-1
        )
        clf.fit(X_train, y_train)
        pred = clf.predict(X_test)
        acc = accuracy_score(y_test, pred)
        ba = balanced_accuracy_score(y_test, pred)
        f1 = f1_score(y_test, pred, average='macro')
        out = {
            'accuracy': acc, 'balanced_accuracy': ba, 'auc': 0.0, 'f1_score': f1,
            'precision': 0.0, 'recall': 0.0, 'threshold': 0.5,
            'confusion_matrix': confusion_matrix(y_test, pred).tolist(),
        }
        if feat_names and hasattr(clf, 'feature_importances_') and len(clf.feature_importances_) == len(feat_names):
            out['feature_importance'] = list(zip(feat_names, clf.feature_importances_.tolist()))
        try:
            if n_classes == 2:
                proba = clf.predict_proba(X_test)[:, 1]
                out['auc'] = roc_auc_score(y_test, proba)
                fpr, tpr, _ = roc_curve(y_test, proba)
                out['roc_fpr'] = fpr.tolist()
                out['roc_tpr'] = tpr.tolist()
                _add_binary_academic_curves(y_test, proba, out)
            else:
                from sklearn.preprocessing import label_binarize
                y_bin = label_binarize(y_test, classes=np.unique(y_test))
                out['auc'] = roc_auc_score(y_bin, clf.predict_proba(X_test), average='macro')
        except Exception:
            pass
        ba_mean, ba_lo, ba_hi = _bootstrap_balanced_accuracy(y_test, pred, random_state=random_seed)
        out['bootstrap_ba_mean'], out['bootstrap_ba_low'], out['bootstrap_ba_high'] = ba_mean, ba_lo, ba_hi
        return out

    def _train_xgb(
        self,
        X_train: np.ndarray, y_train: np.ndarray,
        X_test: np.ndarray, y_test: np.ndarray,
        n_classes: int, random_seed: int,
        feat_names: Optional[List[str]] = None,
        hyperparams: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Train XGBoost with class weighting. Optional hyperparams from nested CV grid."""
        try:
            from xgboost import XGBClassifier
            from sklearn.metrics import (
                accuracy_score, balanced_accuracy_score, f1_score, roc_auc_score,
                roc_curve, confusion_matrix
            )
        except ImportError:
            return {'accuracy': 0.0, 'balanced_accuracy': 0.0, 'auc': 0.0, 'f1_score': 0.0,
                'precision': 0.0, 'recall': 0.0, 'threshold': 0.5, 'confusion_matrix': []}

        obj = 'multi:softmax' if n_classes > 2 else 'binary:logistic'
        n_est, max_d, lr = 400, 6, 0.05
        if hyperparams:
            n_est = int(hyperparams.get('n_estimators', n_est))
            max_d = int(hyperparams.get('max_depth', max_d))
            lr = float(hyperparams.get('learning_rate', lr))
        clf = XGBClassifier(
            n_estimators=n_est, max_depth=max_d, learning_rate=lr,
            subsample=0.8, colsample_bytree=0.8,
            objective=obj, random_state=random_seed, n_jobs=-1
        )
        clf.fit(X_train, y_train)
        pred = clf.predict(X_test)
        acc = accuracy_score(y_test, pred)
        ba = balanced_accuracy_score(y_test, pred)
        f1 = f1_score(y_test, pred, average='macro')
        out = {
            'accuracy': acc, 'balanced_accuracy': ba, 'auc': 0.0, 'f1_score': f1,
            'precision': 0.0, 'recall': 0.0, 'threshold': 0.5,
            'confusion_matrix': confusion_matrix(y_test, pred).tolist(),
        }
        if feat_names and hasattr(clf, 'feature_importances_') and len(clf.feature_importances_) == len(feat_names):
            out['feature_importance'] = list(zip(feat_names, clf.feature_importances_.tolist()))
        try:
            if n_classes == 2:
                proba = clf.predict_proba(X_test)[:, 1]
                out['auc'] = roc_auc_score(y_test, proba)
                fpr, tpr, _ = roc_curve(y_test, proba)
                out['roc_fpr'] = fpr.tolist()
                out['roc_tpr'] = tpr.tolist()
                _add_binary_academic_curves(y_test, proba, out)
            else:
                from sklearn.preprocessing import label_binarize
                y_bin = label_binarize(y_test, classes=np.unique(y_test))
                out['auc'] = roc_auc_score(y_bin, clf.predict_proba(X_test), average='macro')
        except Exception:
            pass
        ba_mean, ba_lo, ba_hi = _bootstrap_balanced_accuracy(y_test, pred, random_state=random_seed)
        out['bootstrap_ba_mean'], out['bootstrap_ba_low'], out['bootstrap_ba_high'] = ba_mean, ba_lo, ba_hi
        return out

    def _train_lightgbm(
        self,
        X_train: np.ndarray, y_train: np.ndarray,
        X_test: np.ndarray, y_test: np.ndarray,
        n_classes: int, random_seed: int,
        feat_names: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Train LightGBM. Returns None if lightgbm is not installed."""
        try:
            from lightgbm import LGBMClassifier
            from sklearn.metrics import (
                accuracy_score, balanced_accuracy_score, f1_score, roc_auc_score,
                roc_curve, confusion_matrix
            )
        except ImportError:
            if not getattr(self, "_lightgbm_unavailable_logged", False):
                self.logger(
                    "warning",
                    "ModelTraining",
                    "LightGBM not available (install with: pip install lightgbm). LGB results skipped.",
                )
                self._lightgbm_unavailable_logged = True
            return None
        objective = 'multiclass' if n_classes > 2 else 'binary'
        clf = LGBMClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.05,
            objective=objective, random_state=random_seed, verbose=-1,
            class_weight='balanced',
        )
        clf.fit(X_train, y_train)
        pred = clf.predict(X_test).ravel().astype(int)
        acc = accuracy_score(y_test, pred)
        ba = balanced_accuracy_score(y_test, pred)
        f1 = f1_score(y_test, pred, average='macro')
        out = {
            'accuracy': acc, 'balanced_accuracy': ba, 'auc': 0.0, 'f1_score': f1,
            'precision': 0.0, 'recall': 0.0, 'threshold': 0.5,
            'confusion_matrix': confusion_matrix(y_test, pred).tolist(),
        }
        if feat_names and hasattr(clf, 'feature_importances_') and len(clf.feature_importances_) == len(feat_names):
            out['feature_importance'] = list(zip(feat_names, clf.feature_importances_.tolist()))
        try:
            if n_classes == 2:
                proba = clf.predict_proba(X_test)[:, 1]
                out['auc'] = roc_auc_score(y_test, proba)
                fpr, tpr, _ = roc_curve(y_test, proba)
                out['roc_fpr'] = fpr.tolist()
                out['roc_tpr'] = tpr.tolist()
                _add_binary_academic_curves(y_test, proba, out)
            else:
                from sklearn.preprocessing import label_binarize
                y_bin = label_binarize(y_test, classes=np.unique(y_test))
                out['auc'] = roc_auc_score(y_bin, clf.predict_proba(X_test), average='macro')
        except Exception:
            pass
        ba_mean, ba_lo, ba_hi = _bootstrap_balanced_accuracy(y_test, pred, random_state=random_seed)
        out['bootstrap_ba_mean'], out['bootstrap_ba_low'], out['bootstrap_ba_high'] = ba_mean, ba_lo, ba_hi
        return out

    def _train_svm(
        self,
        X_train: np.ndarray, y_train: np.ndarray,
        X_test: np.ndarray, y_test: np.ndarray,
        n_classes: int, random_seed: int
    ) -> Dict[str, Any]:
        """Train SVM (RBF kernel). Features are scaled with StandardScaler for better performance."""
        from sklearn.preprocessing import StandardScaler
        from sklearn.svm import SVC
        from sklearn.metrics import (
            accuracy_score, balanced_accuracy_score, f1_score, roc_auc_score,
            roc_curve, confusion_matrix
        )
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        clf = SVC(
            kernel='rbf', C=1.0, gamma='scale',
            class_weight='balanced', probability=True, random_state=random_seed
        )
        clf.fit(X_train_s, y_train)
        pred = clf.predict(X_test_s)
        acc = accuracy_score(y_test, pred)
        ba = balanced_accuracy_score(y_test, pred)
        f1 = f1_score(y_test, pred, average='macro')
        out = {
            'accuracy': acc, 'balanced_accuracy': ba, 'auc': 0.0, 'f1_score': f1,
            'precision': 0.0, 'recall': 0.0, 'threshold': 0.5,
            'confusion_matrix': confusion_matrix(y_test, pred).tolist(),
        }
        try:
            if n_classes == 2:
                proba = clf.predict_proba(X_test_s)[:, 1]
                out['auc'] = roc_auc_score(y_test, proba)
                fpr, tpr, _ = roc_curve(y_test, proba)
                out['roc_fpr'] = fpr.tolist()
                out['roc_tpr'] = tpr.tolist()
                _add_binary_academic_curves(y_test, proba, out)
            else:
                from sklearn.preprocessing import label_binarize
                y_bin = label_binarize(y_test, classes=np.unique(y_test))
                out['auc'] = roc_auc_score(y_bin, clf.predict_proba(X_test_s), average='macro')
        except Exception:
            pass
        ba_mean, ba_lo, ba_hi = _bootstrap_balanced_accuracy(y_test, pred, random_state=random_seed)
        out['bootstrap_ba_mean'], out['bootstrap_ba_low'], out['bootstrap_ba_high'] = ba_mean, ba_lo, ba_hi
        return out

    def _train_catboost(
        self,
        X_train: np.ndarray, y_train: np.ndarray,
        X_test: np.ndarray, y_test: np.ndarray,
        n_classes: int, random_seed: int
    ) -> Optional[Dict[str, Any]]:
        """Train CatBoost. Returns None if catboost is not installed (avoids a row of zeros in Model Comparison)."""
        try:
            from catboost import CatBoostClassifier
            from sklearn.metrics import (
                accuracy_score, balanced_accuracy_score, f1_score, roc_auc_score,
                roc_curve, confusion_matrix
            )
        except ImportError:
            if not getattr(self, "_catboost_unavailable_logged", False):
                self.logger(
                    "warning",
                    "ModelTraining",
                    "CatBoost not available (install with: pip install catboost). CB results skipped for all targets.",
                )
                self._catboost_unavailable_logged = True
            return None

        loss = 'MultiClass' if n_classes > 2 else 'Logloss'
        catboost_info_dir().mkdir(parents=True, exist_ok=True)
        clf = CatBoostClassifier(
            iterations=300, depth=6, learning_rate=0.05,
            loss_function=loss, verbose=False, random_state=random_seed,
            auto_class_weights='Balanced',
            train_dir=str(catboost_info_dir()),
        )
        clf.fit(X_train, y_train)
        pred = clf.predict(X_test).ravel().astype(int)
        acc = accuracy_score(y_test, pred)
        ba = balanced_accuracy_score(y_test, pred)
        f1 = f1_score(y_test, pred, average='macro')
        out = {
            'accuracy': acc, 'balanced_accuracy': ba, 'auc': 0.0, 'f1_score': f1,
            'precision': 0.0, 'recall': 0.0, 'threshold': 0.5,
            'confusion_matrix': confusion_matrix(y_test, pred).tolist(),
        }
        try:
            if n_classes == 2:
                proba = clf.predict_proba(X_test)[:, 1]
                out['auc'] = roc_auc_score(y_test, proba)
                fpr, tpr, _ = roc_curve(y_test, proba)
                out['roc_fpr'] = fpr.tolist()
                out['roc_tpr'] = tpr.tolist()
                _add_binary_academic_curves(y_test, proba, out)
            else:
                from sklearn.preprocessing import label_binarize
                y_bin = label_binarize(y_test, classes=np.unique(y_test))
                out['auc'] = roc_auc_score(y_bin, clf.predict_proba(X_test), average='macro')
        except Exception:
            pass
        ba_mean, ba_lo, ba_hi = _bootstrap_balanced_accuracy(y_test, pred, random_state=random_seed)
        out['bootstrap_ba_mean'], out['bootstrap_ba_low'], out['bootstrap_ba_high'] = ba_mean, ba_lo, ba_hi
        return out
