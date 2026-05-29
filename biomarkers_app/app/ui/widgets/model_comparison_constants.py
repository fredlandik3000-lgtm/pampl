"""Constants for Model Comparison Widget"""

from typing import Dict

# Available phases for comparison
PHASES = ["phase_-6", "phase_0", "phase_15", "phase_30"]

# Model families supported (display names; pipeline uses NN, LR, RF, XGB, CB, ET, LGB, SVM)
MODEL_FAMILIES = [
    "Baseline-Random",
    "Baseline-Majority",
    "Neural Network",
    "Logistic Regression",
    "XGBoost",
    "Random Forest",
    "CatBoost",
    "Extra Trees",
    "LightGBM",
    "SVM",
]

# Display names for model comparison table (e.g. show "Dominant class" for Baseline-Majority)
# Pipeline uses internal codes (NN, LR, RF, XGB, CB, ET, LGB, SVM); map to readable names.
MODEL_DISPLAY_NAMES: Dict[str, str] = {
    "Baseline-Random": "Baseline-Random (Chance)",
    "Baseline-Majority": "Baseline-Majority (Dominant class)",
    "NN": "Neural Network",
    "LR": "Logistic Regression",
    "RF": "Random Forest",
    "XGB": "XGBoost",
    "CB": "CatBoost",
    "ET": "Extra Trees",
    "LGB": "LightGBM",
    "SVM": "SVM (RBF)",
}

# Available metrics for comparison
METRICS = ["Balanced Accuracy", "Accuracy", "AUC", "F1 Score"]

# Performance thresholds for color coding
PERFORMANCE_EXCELLENT = 0.85
PERFORMANCE_GOOD = 0.75
PERFORMANCE_FAIR = 0.65

# Color values for performance indicators
COLOR_EXCELLENT = (200, 255, 200)  # Light green
COLOR_GOOD = (255, 255, 200)  # Light yellow
COLOR_FAIR = (255, 230, 200)  # Light orange
COLOR_POOR = (255, 200, 200)  # Light red
