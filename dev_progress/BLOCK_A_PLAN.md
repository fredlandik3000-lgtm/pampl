# Block A: Validation and Uncertainty — Plan, Tests, Validation

**Goal:** Implement A1 (nested CV / repeated holdout with mean ± std), A2 (bootstrap 95% CI — already implemented, verify and expose), A3 (analysis plan document) so that evaluation produces stable estimates and CIs for publication.

---

## A1: Nested CV / repeated holdout in main evaluation path

### What
- Add **5-fold stratified CV** as an evaluation mode alongside the existing single train/test split.
- When CV mode is used: for each (target, model_family) run training on each of 5 folds, collect test-set metrics (BA, AUC, F1, accuracy) per fold, then report **mean ± std** (and optionally 95% CI from fold percentiles).
- Output: same `List[ModelResult]` structure, with **optional fields** populated: `balanced_accuracy_std`, `auc_std`, `f1_score_std`; primary metrics hold the **mean** across folds. Optionally `balanced_accuracy_ci_low` / `balanced_accuracy_ci_high` from 2.5/97.5 percentiles of fold-wise BA.

### Why
- Single split gives one number per cell; with n≈252 and ~75 in test, variance is high. Reviewers expect mean ± std or 95% CI. Nested CV (or repeated holdout) is the standard for stable estimates.

### Implementation
1. **types.py:** Extend `ModelResult` with optional fields (default 0.0): `balanced_accuracy_std`, `auc_std`, `f1_score_std`, `balanced_accuracy_ci_low`, `balanced_accuracy_ci_high`.
2. **model_training_wrapper.py:** Add `train_models_with_cv(engineered_df, phase, feature_metadata, n_outer_splits=5, ...)` that:
   - For each target: build X, y (same as `train_models`).
   - `StratifiedKFold(n_splits=n_outer_splits, shuffle=True, random_state=random_seed)`.
   - For each fold: train/test indices → X_train, X_test, y_train, y_test. For baselines and each model family, call existing `_train_*` (or inline split + _train_*), collect `balanced_accuracy`, `auc`, `f1_score`, `accuracy` into per-(target, model) lists.
   - Aggregate: mean and std; build one `ModelResult` per (target, model) with mean in main fields and std in new fields; set ci_low/ci_high from `np.percentile(fold_bas, [2.5, 97.5])`.
   - Return `StepResult(success=True, data=results, metadata={'n_outer_splits': n_outer_splits, 'phase': phase, ...})`.
3. **pipeline_runner_widget.py:** Settings: add "Evaluation mode: Single split | 5-fold CV". When "5-fold CV" is selected, `TrainingWorker` and `AllPhasesWorker` call `train_models_with_cv` instead of `train_models`; same signals and UI flow.
4. **Model Comparison / Validation Results:** When displaying a metric, if `balanced_accuracy_std > 0` (or has_std), show e.g. "0.65 ± 0.04" or "0.65 [0.58–0.72]" so reviewers see uncertainty.

### Tests (A1)
- **Unit:** `train_models_with_cv` returns `StepResult`; `result.data` is list of `ModelResult`; each has `balanced_accuracy` in [0,1]; when `n_outer_splits >= 2`, at least one non-baseline result has `balanced_accuracy_std >= 0` and `balanced_accuracy_ci_low <= balanced_accuracy <= balanced_accuracy_ci_high`.
- **Unit:** With synthetic data (one target, 80 rows), run `train_models_with_cv` with `n_outer_splits=3`; check that number of results is consistent (targets × (2 baselines + 5 models)) and metadata has `n_outer_splits=3`.
- **Integration:** Run full pipeline path that triggers `train_models_with_cv` (e.g. from pipeline_runner with use_cv=True) and assert results reach Model Comparison with std fields set (smoke test).

---

## A2: Bootstrap 95% CI for primary metrics

### What
- Bootstrap 95% CI for balanced accuracy is **already implemented** in `model_training_wrapper.py` (`_bootstrap_balanced_accuracy`; all `_train_*` methods return `bootstrap_ba_mean`, `bootstrap_ba_low`, `bootstrap_ba_high`; metadata `bootstrap_cis` is passed to Validation Results and displayed in the Bootstrap CI table).
- Verify: (1) All model families and baselines do not need bootstrap (baselines are deterministic); only trained models get bootstrap. (2) Validation Results tab receives `metadata['bootstrap_cis']` and shows them. (3) Optional: add AUC bootstrap CI in same way for primary metrics (can be follow-up).

### Why
- Point estimates alone are not acceptable; CIs are required by TRIPOD and clinical journals.

### Tests (A2)
- **Unit:** `_bootstrap_balanced_accuracy(y_test, y_pred, n_bootstrap=100, random_state=42)` returns tuple of 3 floats; mean in [0,1]; `ci_low <= mean <= ci_high`; `ci_low <= ci_high`; when y_pred == y_test (perfect), variance is 0 so after many bootstraps still low <= mean <= high.
- **Unit:** With fixed y_test, y_pred, repeated calls with same random_state give same (mean, low, high).
- **Integration:** After `train_models`, `result.metadata.get('bootstrap_cis')` is non-empty and each entry has 6 elements (phase, target, model_family, mean, low, high) with low <= mean <= high.

---

## A3: Pre-specify primary metric and primary targets

### What
- Create **ANALYSIS_PLAN.md** in `dev_progress/` stating: (1) Primary metric for model selection and reporting: **balanced accuracy**. (2) Primary targets (list to be filled; e.g. D30_response_3class, D90_is_cr, crs_grade_ge2, relapse_or_progression, survival_status_lfu). (3) No post hoc target or phase selection for main claims — all primary targets and chosen phases pre-specified.

### Why
- Pre-specification prevents cherry-picking and satisfies methodological standards for prediction papers.

### Tests (A3)
- **Doc/checklist:** ANALYSIS_PLAN.md exists; contains "primary metric" and "primary targets"; contains "no post hoc" or equivalent.

---

## Validation (acceptance)

- [x] Running "Model Training" with **Single split** produces results as before; bootstrap CIs appear in Validation Results tab.
- [x] Running "Model Training" with **5-fold CV** (Settings → Evaluation mode: 5-fold CV) produces results with mean ± std; Model Comparison shows e.g. "0.65 ± 0.04" via `get_metric_display`; metadata has `n_outer_splits=5`.
- [x] All new and existing unit/integration tests pass (test_block_a_validation.py, test_model_training.py CV tests).
- [x] ANALYSIS_PLAN.md is in place (dev_progress/ANALYSIS_PLAN.md) and referenced from ROADMAP.
