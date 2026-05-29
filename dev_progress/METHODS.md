# Methods (for manuscript / reporting)

**Block D — Model choice and class imbalance**

## Class balancing and stratification

- **Stratified splits:** All train/test and K-fold splits are stratified by the outcome (when each class has at least 2 samples) to preserve class proportions.
- **Class weights:** Random Forest and Extra Trees use `class_weight='balanced'`. Logistic regression, XGBoost, CatBoost, and LightGBM use their default handling of imbalanced classes (e.g. class_weight or scale_pos_weight where applicable). SVM uses `class_weight='balanced'`. The neural network uses class-balanced loss where implemented.
- **Primary metric:** Balanced accuracy (BA) is used as the primary metric for model selection and reporting so that performance is not dominated by the majority class.

## Model comparison and preference for simpler models

- We compared eight model families: neural network (NN), logistic regression (LR), random forest (RF), XGBoost (XGB), CatBoost (CB), Extra Trees (ET), LightGBM (LGB), and support vector machine with RBF kernel (SVM). Evaluation used either a single stratified train/test split or 5-fold stratified cross-validation (CV); when CV was used, we report mean ± standard deviation and 95% CI (from fold percentiles) for balanced accuracy, AUC, and F1.
- **Preference for simpler models:** For a given target and phase, when a simpler model (e.g. LR or RF) was within 1–2% balanced accuracy of the best complex model (e.g. NN or XGB) and 95% CIs overlapped, we prefer and report the simpler model for interpretability and robustness, given the limited sample size (n ≈ 252).
