# API Specifications - Wrapper Layer
## Biomarkers Pipeline Tool v1.0

This document specifies the API for wrapping existing pipeline code to make it UI-friendly.

---

## 1. Core Principles

### 1.1 Wrapper Requirements
All wrapped functions must:
1. Accept a `ProgressCallback` for UI updates
2. Accept a `CancellationToken` for early termination
3. Return structured results (not just print to stdout)
4. Capture all logging output
5. Handle exceptions gracefully
6. Be stateless (use cache for state management)

### 1.2 Type Definitions

```python
from typing import Callable, Dict, Any, Optional, List
from dataclasses import dataclass
from threading import Event
import numpy as np
import pandas as pd

# Progress callback signature
ProgressCallback = Callable[[float, str], None]
# Args: (progress_percent, status_message)

# Log callback signature
LogCallback = Callable[[str, str, str], None]
# Args: (level, source, message)
# Levels: "DEBUG", "INFO", "WARNING", "ERROR"

@dataclass
class CancellationToken:
    """Thread-safe cancellation token"""
    _event: Event
    
    def is_cancelled(self) -> bool:
        return self._event.is_set()
    
    def cancel(self) -> None:
        self._event.set()
    
    def reset(self) -> None:
        self._event.clear()

@dataclass
class StepResult:
    """Standard result format for all pipeline steps"""
    success: bool
    data: Any  # Step-specific data
    metadata: Dict[str, Any]  # Timing, counts, etc.
    errors: List[str]
    warnings: List[str]
```

---

## 2. Data Loading API

### 2.1 DataLoaderWrapper

```python
class DataLoaderWrapper:
    """Wrapper for data loading with validation"""
    
    def __init__(self, logger: Optional[LogCallback] = None):
        self.logger = logger or self._default_logger
    
    def load_data(
        self,
        path: str,
        progress_callback: Optional[ProgressCallback] = None,
        cancellation_token: Optional[CancellationToken] = None,
        validate: bool = True
    ) -> StepResult:
        """
        Load clinical data from CSV
        
        Args:
            path: Path to unified_clinical_data.csv
            progress_callback: Progress reporting function
            cancellation_token: Cancellation check
            validate: Whether to validate schema
        
        Returns:
            StepResult with:
                success: True if loaded successfully
                data: pd.DataFrame
                metadata: {
                    "rows": int,
                    "columns": int,
                    "completeness": float,
                    "load_time_sec": float
                }
                errors: List of error messages
                warnings: List of warning messages
        
        Raises:
            FileNotFoundError: If path doesn't exist
            ValueError: If data validation fails (when validate=True)
        """
        start_time = time.time()
        errors = []
        warnings = []
        
        try:
            # Check cancellation
            if cancellation_token and cancellation_token.is_cancelled():
                return StepResult(False, None, {}, ["Cancelled"], [])
            
            # Report progress
            if progress_callback:
                progress_callback(0.0, "Reading CSV file...")
            
            # Load data
            self.logger("INFO", "DataLoader", f"Loading data from {path}")
            df = pd.read_csv(path)
            
            if progress_callback:
                progress_callback(50.0, "Validating data...")
            
            # Validate
            if validate:
                validation_result = self._validate_schema(df)
                errors.extend(validation_result.errors)
                warnings.extend(validation_result.warnings)
                if validation_result.errors:
                    return StepResult(False, None, {}, errors, warnings)
            
            # Calculate metadata
            rows, cols = df.shape
            completeness = 1.0 - (df.isna().sum().sum() / (rows * cols))
            load_time = time.time() - start_time
            
            metadata = {
                "rows": rows,
                "columns": cols,
                "completeness": completeness,
                "load_time_sec": load_time
            }
            
            if progress_callback:
                progress_callback(100.0, f"Loaded {rows} rows successfully")
            
            self.logger("INFO", "DataLoader", f"✓ Loaded {rows} rows, {cols} columns")
            
            return StepResult(True, df, metadata, errors, warnings)
            
        except Exception as e:
            error_msg = f"Failed to load data: {str(e)}"
            self.logger("ERROR", "DataLoader", error_msg)
            return StepResult(False, None, {}, [error_msg], warnings)
    
    def _validate_schema(self, df: pd.DataFrame) -> StepResult:
        """Validate required columns and data types"""
        required_cols = [
            "patient_id", "age", "sex", "diagnosis",
            # ... add all required columns
        ]
        errors = []
        warnings = []
        
        # Check required columns
        missing = set(required_cols) - set(df.columns)
        if missing:
            errors.append(f"Missing required columns: {missing}")
        
        # Check data types
        if "age" in df.columns and not pd.api.types.is_numeric_dtype(df["age"]):
            warnings.append("'age' column is not numeric")
        
        # Check for duplicates
        if df.duplicated(subset=["patient_id"]).any():
            warnings.append("Duplicate patient_ids found")
        
        return StepResult(True, None, {}, errors, warnings)
    
    def _default_logger(self, level: str, source: str, message: str):
        print(f"[{level}] {source}: {message}")
```

---

## 3. Target Derivation API

### 3.1 TargetDerivationWrapper

```python
class TargetDerivationWrapper:
    """Wrapper for target derivation logic"""
    
    def __init__(self, logger: Optional[LogCallback] = None):
        self.logger = logger or self._default_logger
    
    def derive_targets(
        self,
        df: pd.DataFrame,
        progress_callback: Optional[ProgressCallback] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> StepResult:
        """
        Derive target variables from raw data
        
        Args:
            df: Input DataFrame with raw clinical data
            progress_callback: Progress reporting
            cancellation_token: Cancellation check
        
        Returns:
            StepResult with:
                success: True if successful
                data: pd.DataFrame with derived columns
                metadata: {
                    "targets_created": List[str],
                    "gates_created": List[str],
                    "derive_time_sec": float
                }
                errors: List of errors
                warnings: List of warnings
        """
        from current_state.pipeline import derive_targets
        
        start_time = time.time()
        errors = []
        warnings = []
        
        try:
            if progress_callback:
                progress_callback(0.0, "Deriving targets...")
            
            self.logger("INFO", "TargetDerivation", "Starting target derivation")
            
            # Call existing function
            df_derived = derive_targets(df.copy())
            
            if cancellation_token and cancellation_token.is_cancelled():
                return StepResult(False, None, {}, ["Cancelled"], [])
            
            # Identify new columns
            original_cols = set(df.columns)
            new_cols = set(df_derived.columns) - original_cols
            
            gates = [c for c in new_cols if c.endswith("_evaluable_gate")]
            targets = [c for c in new_cols if not c.endswith("_evaluable_gate")]
            
            self.logger("INFO", "TargetDerivation", f"Created {len(gates)} gates")
            self.logger("INFO", "TargetDerivation", f"Created {len(targets)} targets")
            
            # Check for inevaluable records
            for gate in gates:
                ineval_count = (df_derived[gate] == 0).sum()
                if ineval_count > 0:
                    pct = 100 * ineval_count / len(df_derived)
                    warnings.append(f"{gate}: {ineval_count} ({pct:.1f}%) inevaluable")
            
            metadata = {
                "targets_created": targets,
                "gates_created": gates,
                "derive_time_sec": time.time() - start_time
            }
            
            if progress_callback:
                progress_callback(100.0, f"Created {len(targets)} targets")
            
            return StepResult(True, df_derived, metadata, errors, warnings)
            
        except Exception as e:
            error_msg = f"Target derivation failed: {str(e)}"
            self.logger("ERROR", "TargetDerivation", error_msg)
            return StepResult(False, None, {}, [error_msg], warnings)
    
    def _default_logger(self, level: str, source: str, message: str):
        print(f"[{level}] {source}: {message}")
```

---

## 4. Feature Engineering API

### 4.1 FeatureEngineeringWrapper

```python
class FeatureEngineeringWrapper:
    """Wrapper for feature preparation"""
    
    def __init__(self, trainer, logger: Optional[LogCallback] = None):
        self.trainer = trainer  # EnhancedNeuralNetworkTrainer instance
        self.logger = logger or self._default_logger
    
    def prepare_features(
        self,
        df: pd.DataFrame,
        phase: str,
        progress_callback: Optional[ProgressCallback] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> StepResult:
        """
        Prepare features for a specific phase
        
        Args:
            df: DataFrame with all data
            phase: Phase identifier (e.g., "phase_-6")
            progress_callback: Progress reporting
            cancellation_token: Cancellation check
        
        Returns:
            StepResult with:
                success: True if successful
                data: Dict {
                    "X": np.ndarray (feature matrix),
                    "feature_names": List[str],
                    "indices": np.ndarray (row indices used)
                }
                metadata: {
                    "n_samples": int,
                    "n_features": int,
                    "feature_types": Dict[str, int],
                    "prep_time_sec": float
                }
                errors: List of errors
                warnings: List of warnings
        """
        start_time = time.time()
        errors = []
        warnings = []
        
        try:
            if progress_callback:
                progress_callback(0.0, f"Preparing features for {phase}...")
            
            self.logger("INFO", "FeatureEngineering", f"Preparing features for {phase}")
            
            # Call trainer's feature preparation
            X, feature_names = self.trainer.prepare_features(df, phase)
            
            if cancellation_token and cancellation_token.is_cancelled():
                return StepResult(False, None, {}, ["Cancelled"], [])
            
            # Analyze features
            n_samples, n_features = X.shape
            
            feature_types = {}
            for name in feature_names:
                if "_onehot_" in name:
                    feature_types["one_hot"] = feature_types.get("one_hot", 0) + 1
                elif "_interaction_" in name:
                    feature_types["interaction"] = feature_types.get("interaction", 0) + 1
                else:
                    feature_types["base"] = feature_types.get("base", 0) + 1
            
            self.logger("INFO", "FeatureEngineering", 
                       f"Created {n_features} features from {n_samples} samples")
            
            data = {
                "X": X,
                "feature_names": feature_names,
                "indices": np.arange(len(df))
            }
            
            metadata = {
                "n_samples": n_samples,
                "n_features": n_features,
                "feature_types": feature_types,
                "prep_time_sec": time.time() - start_time
            }
            
            if progress_callback:
                progress_callback(100.0, f"Created {n_features} features")
            
            return StepResult(True, data, metadata, errors, warnings)
            
        except Exception as e:
            error_msg = f"Feature preparation failed: {str(e)}"
            self.logger("ERROR", "FeatureEngineering", error_msg)
            return StepResult(False, None, {}, [error_msg], warnings)
    
    def _default_logger(self, level: str, source: str, message: str):
        print(f"[{level}] {source}: {message}")
```

---

## 5. Model Training API

### 5.1 ModelTrainerWrapper

```python
from enum import Enum

class ModelFamily(Enum):
    NEURAL_NETWORK = "NN"
    LOGISTIC_REGRESSION = "LR"
    XGBOOST = "XGB"
    RANDOM_FOREST = "RF"
    CATBOOST = "CB"

@dataclass
class ModelTrainingResult:
    """Result from training a single model"""
    model_family: ModelFamily
    trained_model: Any  # The actual model object
    training_time_sec: float
    training_history: Optional[Dict[str, List[float]]]  # For NN: loss/acc per epoch
    hyperparameters: Dict[str, Any]

class ModelTrainerWrapper:
    """Wrapper for model training"""
    
    def __init__(self, logger: Optional[LogCallback] = None):
        self.logger = logger or self._default_logger
    
    def train_model(
        self,
        model_family: ModelFamily,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        hyperparams: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[ProgressCallback] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> StepResult:
        """
        Train a single model
        
        Args:
            model_family: Which model type to train
            X_train, y_train: Training data
            X_val, y_val: Validation data (optional, for early stopping)
            hyperparams: Model-specific hyperparameters
            progress_callback: Progress reporting (especially for NN epochs)
            cancellation_token: Cancellation check
        
        Returns:
            StepResult with:
                success: True if training succeeded
                data: ModelTrainingResult
                metadata: {
                    "final_train_metric": float,
                    "final_val_metric": float,
                    "converged": bool,
                    "epochs_trained": int (NN only)
                }
                errors: List of errors
                warnings: List of warnings
        """
        start_time = time.time()
        errors = []
        warnings = []
        
        try:
            self.logger("INFO", "ModelTrainer", 
                       f"Training {model_family.value} model")
            
            if model_family == ModelFamily.NEURAL_NETWORK:
                result = self._train_nn(X_train, y_train, X_val, y_val, 
                                       hyperparams, progress_callback, 
                                       cancellation_token)
            elif model_family == ModelFamily.LOGISTIC_REGRESSION:
                result = self._train_lr(X_train, y_train, hyperparams)
            elif model_family == ModelFamily.XGBOOST:
                result = self._train_xgb(X_train, y_train, hyperparams)
            elif model_family == ModelFamily.RANDOM_FOREST:
                result = self._train_rf(X_train, y_train, hyperparams)
            elif model_family == ModelFamily.CATBOOST:
                result = self._train_cb(X_train, y_train, hyperparams)
            else:
                raise ValueError(f"Unknown model family: {model_family}")
            
            if cancellation_token and cancellation_token.is_cancelled():
                return StepResult(False, None, {}, ["Cancelled"], [])
            
            train_time = time.time() - start_time
            result.training_time_sec = train_time
            
            self.logger("INFO", "ModelTrainer", 
                       f"✓ Training complete ({train_time:.1f}s)")
            
            metadata = {
                "training_time_sec": train_time
            }
            
            if progress_callback:
                progress_callback(100.0, "Training complete")
            
            return StepResult(True, result, metadata, errors, warnings)
            
        except Exception as e:
            error_msg = f"Training {model_family.value} failed: {str(e)}"
            self.logger("ERROR", "ModelTrainer", error_msg)
            return StepResult(False, None, {}, [error_msg], warnings)
    
    def _train_nn(
        self, 
        X_train, y_train, X_val, y_val, 
        hyperparams, progress_callback, cancellation_token
    ) -> ModelTrainingResult:
        """Train neural network with epoch-level progress"""
        from sklearn.neural_network import MLPClassifier
        from sklearn.preprocessing import StandardScaler
        
        # Default hyperparameters
        params = {
            "hidden_layer_sizes": (128, 64, 32),
            "learning_rate_init": 0.001,
            "max_iter": 500,
            "alpha": 0.0001,
            "random_state": 42
        }
        if hyperparams:
            params.update(hyperparams)
        
        # Scale data
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        
        # For progress tracking, we'd need to use a custom callback
        # or periodically check partial_fit if available
        # For now, use standard fit (no epoch-level progress)
        model = MLPClassifier(**params)
        model.fit(X_train_scaled, y_train)
        
        # Mock training history (sklearn doesn't expose this easily)
        history = {
            "loss": model.loss_curve_ if hasattr(model, "loss_curve_") else [],
            "iterations": model.n_iter_
        }
        
        return ModelTrainingResult(
            model_family=ModelFamily.NEURAL_NETWORK,
            trained_model={"model": model, "scaler": scaler},
            training_time_sec=0.0,  # Will be set by caller
            training_history=history,
            hyperparameters=params
        )
    
    def _train_lr(self, X_train, y_train, hyperparams) -> ModelTrainingResult:
        """Train logistic regression"""
        from sklearn.linear_model import LogisticRegression
        from sklearn.multiclass import OneVsRestClassifier
        
        params = {
            "max_iter": 1000,
            "solver": "liblinear",
            "random_state": 42
        }
        if hyperparams:
            params.update(hyperparams)
        
        base = LogisticRegression(**params)
        model = OneVsRestClassifier(base)
        model.fit(X_train, y_train)
        
        return ModelTrainingResult(
            model_family=ModelFamily.LOGISTIC_REGRESSION,
            trained_model=model,
            training_time_sec=0.0,
            training_history=None,
            hyperparameters=params
        )
    
    def _train_xgb(self, X_train, y_train, hyperparams) -> ModelTrainingResult:
        """Train XGBoost"""
        from xgboost import XGBClassifier
        
        params = {
            "n_estimators": 400,
            "max_depth": 6,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "n_jobs": -1,
            "random_state": 42,
            "tree_method": "hist"
        }
        if hyperparams:
            params.update(hyperparams)
        
        # Determine objective
        n_classes = len(np.unique(y_train))
        if n_classes == 2:
            params["objective"] = "binary:logistic"
            params["eval_metric"] = "logloss"
        else:
            params["objective"] = "multi:softmax"
            params["eval_metric"] = "mlogloss"
        
        model = XGBClassifier(**params)
        model.fit(X_train, y_train)
        
        return ModelTrainingResult(
            model_family=ModelFamily.XGBOOST,
            trained_model=model,
            training_time_sec=0.0,
            training_history=None,
            hyperparameters=params
        )
    
    def _train_rf(self, X_train, y_train, hyperparams) -> ModelTrainingResult:
        """Train Random Forest"""
        from sklearn.ensemble import RandomForestClassifier
        
        params = {
            "n_estimators": 400,
            "class_weight": "balanced",
            "n_jobs": -1,
            "random_state": 42
        }
        if hyperparams:
            params.update(hyperparams)
        
        model = RandomForestClassifier(**params)
        model.fit(X_train, y_train)
        
        return ModelTrainingResult(
            model_family=ModelFamily.RANDOM_FOREST,
            trained_model=model,
            training_time_sec=0.0,
            training_history=None,
            hyperparameters=params
        )
    
    def _train_cb(self, X_train, y_train, hyperparams) -> ModelTrainingResult:
        """Train CatBoost"""
        try:
            from catboost import CatBoostClassifier
        except ImportError:
            raise ImportError("CatBoost not installed")
        
        params = {
            "iterations": 300,
            "depth": 6,
            "learning_rate": 0.05,
            "verbose": False,
            "random_state": 42
        }
        if hyperparams:
            params.update(hyperparams)
        
        # Determine loss function
        n_classes = len(np.unique(y_train))
        if n_classes == 2:
            params["loss_function"] = "Logloss"
        else:
            params["loss_function"] = "MultiClass"
        
        model = CatBoostClassifier(**params)
        model.fit(X_train, y_train)
        
        return ModelTrainingResult(
            model_family=ModelFamily.CATBOOST,
            trained_model=model,
            training_time_sec=0.0,
            training_history=None,
            hyperparameters=params
        )
    
    def _default_logger(self, level: str, source: str, message: str):
        print(f"[{level}] {source}: {message}")
```

---

## 6. Evaluation API

### 6.1 ModelEvaluatorWrapper

```python
@dataclass
class EvaluationMetrics:
    """Standard metrics for model evaluation"""
    accuracy: float
    balanced_accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc: Optional[float]  # Only for binary classification
    confusion_matrix: np.ndarray
    classification_report: Dict[str, Any]

class ModelEvaluatorWrapper:
    """Wrapper for model evaluation"""
    
    def __init__(self, logger: Optional[LogCallback] = None):
        self.logger = logger or self._default_logger
    
    def evaluate_model(
        self,
        model: Any,
        X_test: np.ndarray,
        y_test: np.ndarray,
        threshold: Optional[float] = None,
        model_family: Optional[ModelFamily] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> StepResult:
        """
        Evaluate a trained model on test data
        
        Args:
            model: Trained model object
            X_test, y_test: Test data
            threshold: Decision threshold for binary classification
            model_family: Model type (for family-specific handling)
            progress_callback: Progress reporting
        
        Returns:
            StepResult with:
                success: True if evaluation succeeded
                data: EvaluationMetrics
                metadata: {
                    "n_samples": int,
                    "n_classes": int,
                    "is_binary": bool
                }
                errors: List of errors
                warnings: List of warnings
        """
        from sklearn.metrics import (
            accuracy_score, balanced_accuracy_score, precision_score,
            recall_score, f1_score, confusion_matrix, classification_report,
            roc_auc_score
        )
        
        errors = []
        warnings = []
        
        try:
            if progress_callback:
                progress_callback(0.0, "Evaluating model...")
            
            self.logger("INFO", "ModelEvaluator", "Evaluating model on test set")
            
            # Get predictions
            if model_family == ModelFamily.NEURAL_NETWORK:
                # NN wrapper includes scaler
                X_test_scaled = model["scaler"].transform(X_test)
                y_pred = model["model"].predict(X_test_scaled)
                y_proba = model["model"].predict_proba(X_test_scaled)
            else:
                y_pred = model.predict(X_test)
                if hasattr(model, "predict_proba"):
                    y_proba = model.predict_proba(X_test)
                else:
                    y_proba = None
            
            # Apply threshold for binary classification
            is_binary = len(np.unique(y_test)) == 2
            if is_binary and threshold is not None and y_proba is not None:
                y_pred = (y_proba[:, 1] > threshold).astype(int)
            
            # Calculate metrics
            acc = accuracy_score(y_test, y_pred)
            bal_acc = balanced_accuracy_score(y_test, y_pred)
            
            # For multiclass, use weighted averages
            avg = "binary" if is_binary else "weighted"
            prec = precision_score(y_test, y_pred, average=avg, zero_division=0)
            rec = recall_score(y_test, y_pred, average=avg, zero_division=0)
            f1 = f1_score(y_test, y_pred, average=avg, zero_division=0)
            
            # AUC only for binary
            auc = None
            if is_binary and y_proba is not None:
                try:
                    auc = roc_auc_score(y_test, y_proba[:, 1])
                except Exception as e:
                    warnings.append(f"Could not calculate AUC: {str(e)}")
            
            cm = confusion_matrix(y_test, y_pred)
            cr = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
            
            metrics = EvaluationMetrics(
                accuracy=acc,
                balanced_accuracy=bal_acc,
                precision=prec,
                recall=rec,
                f1_score=f1,
                auc=auc,
                confusion_matrix=cm,
                classification_report=cr
            )
            
            self.logger("INFO", "ModelEvaluator", 
                       f"Accuracy: {acc:.4f}, Balanced Acc: {bal_acc:.4f}")
            
            metadata = {
                "n_samples": len(y_test),
                "n_classes": len(np.unique(y_test)),
                "is_binary": is_binary
            }
            
            if progress_callback:
                progress_callback(100.0, "Evaluation complete")
            
            return StepResult(True, metrics, metadata, errors, warnings)
            
        except Exception as e:
            error_msg = f"Evaluation failed: {str(e)}"
            self.logger("ERROR", "ModelEvaluator", error_msg)
            return StepResult(False, None, {}, [error_msg], warnings)
    
    def tune_threshold(
        self,
        model: Any,
        X_val: np.ndarray,
        y_val: np.ndarray,
        metric: str = "balanced_accuracy",
        model_family: Optional[ModelFamily] = None
    ) -> StepResult:
        """
        Find optimal threshold for binary classification
        
        Args:
            model: Trained model
            X_val, y_val: Validation data
            metric: Metric to optimize ("accuracy", "balanced_accuracy", "f1")
            model_family: Model type
        
        Returns:
            StepResult with:
                success: True if successful
                data: float (optimal threshold)
                metadata: {
                    "best_metric_value": float,
                    "metric_optimized": str
                }
        """
        from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
        
        try:
            # Get probabilities
            if model_family == ModelFamily.NEURAL_NETWORK:
                X_val_scaled = model["scaler"].transform(X_val)
                y_proba = model["model"].predict_proba(X_val_scaled)[:, 1]
            else:
                y_proba = model.predict_proba(X_val)[:, 1]
            
            # Grid search thresholds
            best_thr = 0.5
            best_metric_val = 0.0
            
            for thr in np.linspace(0.1, 0.9, 41):
                y_pred = (y_proba > thr).astype(int)
                
                if metric == "accuracy":
                    val = accuracy_score(y_val, y_pred)
                elif metric == "balanced_accuracy":
                    val = balanced_accuracy_score(y_val, y_pred)
                elif metric == "f1":
                    val = f1_score(y_val, y_pred, zero_division=0)
                else:
                    raise ValueError(f"Unknown metric: {metric}")
                
                if val > best_metric_val:
                    best_metric_val = val
                    best_thr = thr
            
            self.logger("INFO", "ModelEvaluator", 
                       f"Optimal threshold: {best_thr:.3f} ({metric}={best_metric_val:.4f})")
            
            metadata = {
                "best_metric_value": best_metric_val,
                "metric_optimized": metric
            }
            
            return StepResult(True, best_thr, metadata, [], [])
            
        except Exception as e:
            error_msg = f"Threshold tuning failed: {str(e)}"
            self.logger("ERROR", "ModelEvaluator", error_msg)
            return StepResult(False, 0.5, {}, [error_msg], [])
    
    def _default_logger(self, level: str, source: str, message: str):
        print(f"[{level}] {source}: {message}")
```

---

## 7. Visualization API

### 7.1 VisualizationGenerator

```python
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import seaborn as sns

class VisualizationGenerator:
    """Generate matplotlib figures for embedding in Qt"""
    
    def generate_roc_curve(
        self,
        results: Dict[str, Dict[str, np.ndarray]],
        title: str = "ROC Curves"
    ) -> Figure:
        """
        Generate ROC curve plot
        
        Args:
            results: Dict mapping model names to {"y_true": ..., "y_proba": ...}
            title: Plot title
        
        Returns:
            matplotlib Figure object
        """
        from sklearn.metrics import roc_curve, auc
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        for model_name, data in results.items():
            y_true = data["y_true"]
            y_proba = data["y_proba"]
            
            fpr, tpr, _ = roc_curve(y_true, y_proba)
            roc_auc = auc(fpr, tpr)
            
            ax.plot(fpr, tpr, label=f"{model_name} (AUC={roc_auc:.3f})", linewidth=2)
        
        ax.plot([0, 1], [0, 1], 'k--', label="Random")
        ax.set_xlabel("False Positive Rate", fontsize=12)
        ax.set_ylabel("True Positive Rate", fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.legend(loc="lower right")
        ax.grid(alpha=0.3)
        
        return fig
    
    def generate_confusion_matrix(
        self,
        cm: np.ndarray,
        class_names: Optional[List[str]] = None,
        title: str = "Confusion Matrix"
    ) -> Figure:
        """Generate confusion matrix heatmap"""
        fig, ax = plt.subplots(figsize=(6, 5))
        
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=class_names or range(len(cm)),
            yticklabels=class_names or range(len(cm)),
            ax=ax
        )
        
        ax.set_xlabel("Predicted", fontsize=12)
        ax.set_ylabel("True", fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")
        
        return fig
    
    def generate_heatmap(
        self,
        data: pd.DataFrame,
        title: str = "Performance Heatmap",
        cmap: str = "RdYlGn",
        vmin: float = 0.6,
        vmax: float = 0.95
    ) -> Figure:
        """Generate generic heatmap (e.g., accuracy across phases/targets)"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        sns.heatmap(
            data,
            annot=True,
            fmt=".3f",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            ax=ax,
            cbar_kws={"label": "Metric Value"}
        )
        
        ax.set_title(title, fontsize=14, fontweight="bold")
        plt.tight_layout()
        
        return fig
    
    def generate_feature_importance(
        self,
        feature_names: List[str],
        importance_scores: np.ndarray,
        top_n: int = 20,
        title: str = "Feature Importance"
    ) -> Figure:
        """Generate feature importance bar chart"""
        # Sort by importance
        indices = np.argsort(importance_scores)[-top_n:]
        
        fig, ax = plt.subplots(figsize=(8, 10))
        
        ax.barh(range(top_n), importance_scores[indices])
        ax.set_yticks(range(top_n))
        ax.set_yticklabels([feature_names[i] for i in indices])
        ax.set_xlabel("Importance Score", fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.grid(axis="x", alpha=0.3)
        
        plt.tight_layout()
        
        return fig
```

---

## 8. Orchestrator API

### 8.1 PipelineOrchestrator

```python
class PipelineOrchestrator:
    """High-level orchestration of pipeline execution"""
    
    def __init__(self, config: Dict[str, Any], logger: LogCallback):
        self.config = config
        self.logger = logger
        self.cancellation_token = CancellationToken(Event())
        self.results_cache = {}
    
    def run_pipeline(
        self,
        progress_callback: ProgressCallback
    ) -> Dict[str, StepResult]:
        """
        Run complete pipeline
        
        Returns:
            Dict mapping step names to StepResult objects
        """
        results = {}
        
        try:
            # Step 1: Load data
            data_loader = DataLoaderWrapper(self.logger)
            result = data_loader.load_data(
                self.config["data"]["path"],
                lambda p, m: progress_callback(p * 0.1, m),
                self.cancellation_token
            )
            results["load_data"] = result
            if not result.success:
                return results
            df = result.data
            
            # Step 2: Derive targets
            target_deriver = TargetDerivationWrapper(self.logger)
            result = target_deriver.derive_targets(
                df,
                lambda p, m: progress_callback(10 + p * 0.1, m),
                self.cancellation_token
            )
            results["derive_targets"] = result
            if not result.success:
                return results
            df = result.data
            
            # Step 3: Feature engineering (per phase)
            # ... continue with remaining steps
            
            return results
            
        except Exception as e:
            self.logger("ERROR", "Orchestrator", f"Pipeline failed: {str(e)}")
            return results
    
    def cancel(self):
        """Request cancellation of running pipeline"""
        self.cancellation_token.cancel()
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-18  
**Status**: Draft for Review
