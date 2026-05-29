"""Mock data generation for Model Comparison Widget"""

import random
from typing import List

from app.pipeline.types import ModelResult
from app.ui.widgets.model_comparison_constants import PHASES, MODEL_FAMILIES


def generate_mock_results() -> tuple[List[ModelResult], List[str]]:
    """
    Generate mock model results for testing UI.
    
    Returns:
        Tuple of (results list, targets list)
    """
    # Mock targets (common biomarker targets)
    targets = [
        "D30_response_3class",
        "D90_is_cr",
        "crs_grade_ge2",
        "icans_grade_ge2",
        "infection_100days",
        "relapse_or_progress",
        "survival_status_lfu"
    ]
    
    # Generate mock results
    random.seed(42)  # For reproducibility
    results = []
    
    for target in targets:
        for phase in PHASES:
            for model in MODEL_FAMILIES:
                # Generate realistic-looking metrics
                if model == "Baseline-Random":
                    # Random baseline: around 0.50 for balanced accuracy (chance level)
                    base_acc = 0.48 + random.random() * 0.04  # 0.48-0.52
                elif model == "Baseline-Majority":
                    # Majority baseline: accuracy depends on class imbalance
                    # For balanced accuracy, should be ~0.50 (only predicts one class)
                    base_acc = 0.50  # Always 0.50 for balanced accuracy
                elif model == "Neural Network":
                    base_acc = 0.65 + random.random() * 0.25  # 0.65-0.90
                elif model == "Logistic Regression":
                    base_acc = 0.62 + random.random() * 0.22  # 0.62-0.84
                elif model == "XGBoost":
                    base_acc = 0.68 + random.random() * 0.22  # 0.68-0.90
                elif model == "Random Forest":
                    base_acc = 0.66 + random.random() * 0.23  # 0.66-0.89
                elif model == "CatBoost":
                    base_acc = 0.67 + random.random() * 0.23  # 0.67-0.90
                else:
                    base_acc = 0.65 + random.random() * 0.25  # Default
                
                result = ModelResult(
                    target=target,
                    phase=phase,
                    model_family=model,
                    accuracy=base_acc + random.uniform(-0.02, 0.02),
                    balanced_accuracy=base_acc,
                    auc=max(0.50, min(0.95, base_acc + random.uniform(0.02, 0.08))),
                    f1_score=max(0.0, base_acc - random.uniform(0.01, 0.03)),
                    precision=max(0.0, base_acc + random.uniform(-0.03, 0.03)),
                    recall=max(0.0, base_acc + random.uniform(-0.03, 0.03)),
                    train_time=random.uniform(5.0, 30.0) if not model.startswith("Baseline") else 0.01,
                    threshold=0.45 + random.random() * 0.1,
                    sample_size=252
                )
                results.append(result)
    
    return results, targets
