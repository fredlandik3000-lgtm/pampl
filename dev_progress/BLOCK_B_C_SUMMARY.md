# Blocks B and C — Implementation Summary

**Done:** 2026-02-26

---

## Block B: Baseline comparisons

- **B1:** Random and majority baselines were already computed in the same pipeline (single-split and CV) and included in results; no change.
- **B2 — Formal comparison:**
  - **Validation Results tab:** "Model vs baseline" table shows per (target, phase): Majority BA, Best Model, Best BA, Beat Majority (Yes/No). Populated from training results when they include Baseline-Majority and at least one model.
  - **Model Comparison CSV export:** Added columns `Primary_Target`, `Majority_BA`, `Beat_Majority`, and (from Block A) `BA_std`, `BA_CI_low`, `BA_CI_high`. Export builds a lookup of majority BA from Baseline-Majority results and sets Beat_Majority for non-baseline rows.

---

## Block C: Data and target definition

- **C1 — Evaluable gate:** For each target that has a timepoint gate (D30, D90, M6, Y1, BEST), training and CV now restrict to rows with the corresponding `*_evaluable_gate == 1`. Mapping: `TARGET_TO_GATE` in `model_training_wrapper.py`; helper `_filter_by_evaluable_gate(df, target)` applied before `_prepare_target` in both `train_models` and `train_models_with_cv`.
- **C2 — Primary targets:** `PRIMARY_TARGETS` list in `app/pipeline/types.py` (aligned with ANALYSIS_PLAN.md). Model Comparison CSV export includes `Primary_Target` (Yes/No) per row.
- **C3 — Class balance and missingness:** Training metadata includes `target_summary`: per target, `n_total`, `n_train`, `n_test`, `train_class_counts`, `test_class_counts` (single-split) or `class_counts` (CV), and `gate_filtered`. Validation Results tab has "Class balance (target summary)" table; populated via `set_target_summary(metadata.get("target_summary", []))` from main window when training completes.

---

## Tests

- **Unit:** `test_block_a_validation.py`: gate column lookup, filter by gate, PRIMARY_TARGETS. `test_validation_results_widget.py`: baseline comparison table populated from results with Baseline-Majority + model; target summary table populated from `set_target_summary`.
- **Integration:** Existing model training tests still pass (gate filter and target_summary are additive).
