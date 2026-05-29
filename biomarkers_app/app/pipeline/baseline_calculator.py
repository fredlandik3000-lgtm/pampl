"""
Baseline Calculator for Model Comparison

Computes academically sound baseline classifiers:
- Random Baseline: Predicts according to training set class distribution (chance level)
- Majority Baseline: Always predicts the most frequent class in training set

These baselines validate that ML models provide genuine predictive value beyond
trivial strategies. If a model doesn't beat these baselines, it's not learning anything useful.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from collections import Counter
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import balanced_accuracy_score, accuracy_score, roc_auc_score
from sklearn.preprocessing import label_binarize

from app.core.logger_manager import LoggerManager


class BaselineCalculator:
    """Calculates baseline performance metrics for model validation"""
    
    def __init__(self, logger: LoggerManager, n_splits: int = 5, random_state: int = 42):
        """
        Initialize baseline calculator
        
        Args:
            logger: Logger instance
            n_splits: Number of cross-validation folds
            random_state: Random seed for reproducibility
        """
        self.logger = logger
        self.n_splits = n_splits
        self.random_state = random_state
    
    def compute_random_baseline(self, y: np.ndarray) -> Dict[str, float]:
        """
        Compute random baseline: predict according to class distribution
        
        This represents chance-level performance. A model that doesn't beat this
        is essentially guessing randomly.
        
        Args:
            y: Target labels
            
        Returns:
            Dictionary with metrics (balanced_accuracy, accuracy, auc)
        """
        if len(y) < self.n_splits * 2:
            self.logger.warning(
                f"Insufficient samples ({len(y)}) for {self.n_splits}-fold CV",
                "BaselineCalculator"
            )
            return {'balanced_accuracy': 0.0, 'accuracy': 0.0, 'auc': 0.0}
        
        skf = StratifiedKFold(n_splits=self.n_splits, shuffle=True, random_state=self.random_state)
        
        bal_accs = []
        accs = []
        aucs = []
        
        for fold_idx, (train_idx, test_idx) in enumerate(skf.split(np.zeros_like(y), y)):
            y_train, y_test = y[train_idx], y[test_idx]
            
            # Get class distribution from training set
            classes, counts = np.unique(y_train, return_counts=True)
            probs = counts / counts.sum()
            
            # Generate random predictions according to training distribution
            rng = np.random.default_rng(self.random_state + fold_idx)
            y_pred = rng.choice(classes, size=len(y_test), p=probs)
            
            # Compute metrics
            try:
                bal_accs.append(balanced_accuracy_score(y_test, y_pred))
                accs.append(accuracy_score(y_test, y_pred))
                
                # AUC for random is ~0.50
                if len(classes) == 2:
                    # Binary: use random probabilities
                    y_pred_proba = rng.random(len(y_test))
                    aucs.append(roc_auc_score(y_test, y_pred_proba))
                else:
                    # Multi-class: one-vs-rest
                    y_test_bin = label_binarize(y_test, classes=classes)
                    y_pred_proba = rng.random((len(y_test), len(classes)))
                    y_pred_proba /= y_pred_proba.sum(axis=1, keepdims=True)
                    aucs.append(roc_auc_score(y_test_bin, y_pred_proba, multi_class='ovr', average='macro'))
            except Exception as e:
                self.logger.warning(f"Error computing random baseline metrics: {str(e)}", "BaselineCalculator")
                bal_accs.append(0.0)
                accs.append(0.0)
                aucs.append(0.5)
        
        return {
            'balanced_accuracy': float(np.mean(bal_accs)),
            'accuracy': float(np.mean(accs)),
            'auc': float(np.mean(aucs))
        }
    
    def compute_majority_baseline(self, y: np.ndarray) -> Dict[str, float]:
        """
        Compute majority class baseline: always predict most frequent class
        
        This represents the simplest non-random strategy. A good model should
        significantly outperform this baseline.
        
        For balanced accuracy:
        - Binary: If 70/30 split, predicting all majority gives:
          * Sensitivity (majority class): 100% = 1.0
          * Specificity (minority class): 0% = 0.0
          * Balanced Accuracy: (1.0 + 0.0) / 2 = 0.50
        - Multi-class: Varies by number of classes and distribution
        
        Args:
            y: Target labels
            
        Returns:
            Dictionary with metrics (balanced_accuracy, accuracy, auc)
        """
        if len(y) < self.n_splits * 2:
            self.logger.warning(
                f"Insufficient samples ({len(y)}) for {self.n_splits}-fold CV",
                "BaselineCalculator"
            )
            return {'balanced_accuracy': 0.0, 'accuracy': 0.0, 'auc': 0.0}
        
        skf = StratifiedKFold(n_splits=self.n_splits, shuffle=True, random_state=self.random_state)
        
        bal_accs = []
        accs = []
        aucs = []
        
        for train_idx, test_idx in skf.split(np.zeros_like(y), y):
            y_train, y_test = y[train_idx], y[test_idx]
            
            # Find majority class in training set
            majority_class = Counter(y_train).most_common(1)[0][0]
            
            # Predict all majority
            y_pred = np.full_like(y_test, majority_class)
            
            # Compute metrics
            try:
                bal_accs.append(balanced_accuracy_score(y_test, y_pred))
                accs.append(accuracy_score(y_test, y_pred))
                
                # AUC: predict all one class = 0.50 (no discrimination)
                classes = np.unique(y_train)
                if len(classes) == 2:
                    # Binary: all predictions same = AUC 0.50
                    aucs.append(0.5)
                else:
                    # Multi-class: all predictions same = AUC 0.50
                    aucs.append(0.5)
            except Exception as e:
                self.logger.warning(f"Error computing majority baseline metrics: {str(e)}", "BaselineCalculator")
                bal_accs.append(0.0)
                accs.append(0.0)
                aucs.append(0.5)
        
        return {
            'balanced_accuracy': float(np.mean(bal_accs)),
            'accuracy': float(np.mean(accs)),
            'auc': float(np.mean(aucs))
        }
    
    def compute_baselines_for_target(
        self,
        df: pd.DataFrame,
        target: str,
        features: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """
        Compute both baselines for a specific target
        
        Args:
            df: DataFrame with features and target
            target: Target column name
            features: List of feature column names (not used for baselines, but needed for consistency)
            
        Returns:
            Dictionary with 'random' and 'majority' baseline metrics
        """
        # Check if target exists
        if target not in df.columns:
            self.logger.error(f"Target '{target}' not found in dataframe", "BaselineCalculator")
            return {
                'random': {'balanced_accuracy': 0.0, 'accuracy': 0.0, 'auc': 0.0},
                'majority': {'balanced_accuracy': 0.0, 'accuracy': 0.0, 'auc': 0.0}
            }
        
        # Get target values (drop NaN)
        y = df[target].dropna().values
        
        if len(y) < self.n_splits * 2:
            self.logger.warning(
                f"Insufficient samples for target '{target}' ({len(y)} samples)",
                "BaselineCalculator"
            )
            return {
                'random': {'balanced_accuracy': 0.0, 'accuracy': 0.0, 'auc': 0.0},
                'majority': {'balanced_accuracy': 0.0, 'accuracy': 0.0, 'auc': 0.0}
            }
        
        # Check class distribution
        classes, counts = np.unique(y, return_counts=True)
        self.logger.debug(
            f"Target '{target}': {len(y)} samples, {len(classes)} classes, "
            f"distribution: {dict(zip(classes, counts))}",
            "BaselineCalculator"
        )
        
        # Compute baselines
        random_metrics = self.compute_random_baseline(y)
        majority_metrics = self.compute_majority_baseline(y)
        
        self.logger.info(
            f"Baselines for '{target}': "
            f"Random Bal.Acc={random_metrics['balanced_accuracy']:.3f}, "
            f"Majority Bal.Acc={majority_metrics['balanced_accuracy']:.3f}",
            "BaselineCalculator"
        )
        
        return {
            'random': random_metrics,
            'majority': majority_metrics
        }
