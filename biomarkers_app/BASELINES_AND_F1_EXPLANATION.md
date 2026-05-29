# F1 Score and Baseline Comparisons

**Date:** January 18, 2026  
**Topic:** Understanding F1 Score and Baseline Comparisons  
**Status:** Implemented in Model Comparison Tab

---

## What is F1 Score?

### Definition

**F1 Score** = Harmonic mean of Precision and Recall

```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

### Components

**Precision:** Of all predicted positives, how many are actually positive?
```
Precision = True Positives / (True Positives + False Positives)
```

**Recall (Sensitivity):** Of all actual positives, how many did we correctly identify?
```
Recall = True Positives / (True Positives + False Negatives)
```

---

## Why F1 Score?

### Use Cases

1. **Imbalanced Classes**
   - When one class is much more common than another
   - Example: 90% non-responders, 10% responders
   - Accuracy alone can be misleading (predicting all "non-responder" = 90% accuracy!)

2. **Balance Precision and Recall**
   - Some models are high precision, low recall (conservative)
   - Some models are low precision, high recall (aggressive)
   - F1 balances both concerns

3. **Clinical Relevance**
   - High precision: Don't waste resources on false positives
   - High recall: Don't miss true positives (patients who need treatment)
   - F1: Optimize both

---

## F1 in Mock Data

### Current Implementation

```python
f1_score=base_acc - random.uniform(0.01, 0.03)
```

**For Mock Data:**
- Base accuracy: 0.65-0.90 (for ML models)
- F1: Base accuracy minus 0.01-0.03
- **Result:** F1 ranges from ~0.62 to ~0.87 (not zero!)

### Why F1 < Accuracy?

In reality, F1 is often lower than accuracy because:
- F1 focuses on the positive class only
- Accuracy includes true negatives
- For imbalanced data, getting true negatives is "easier"

---

## Baseline Comparisons - YES, We Show Them!

### Why Baselines Are Critical

Machine learning models MUST be compared to baselines to prove they're useful:
- Is 0.75 accuracy good? Only if it beats baseline!
- A model worse than random guessing is useless
- A model barely better than majority class needs more work

---

## Baseline Types Implemented

### 1. Baseline-Random (Random-Prior)

**Strategy:** Predict class labels randomly according to training set class distribution

**Example:**
- Training set: 70% non-responders, 30% responders
- Random baseline predicts: 70% non-responder, 30% responder
- **Expected Balanced Accuracy: ~0.50** (by chance)

**When Useful:**
- Absolute minimum performance bar
- Shows "chance level" performance
- Model must beat this or it's worthless

### 2. Baseline-Majority (Dominant Class)

**Strategy:** Always predict the most common class

**Example:**
- Training set: 70% non-responders, 30% responders
- Majority baseline always predicts: non-responder
- **Accuracy: 0.70** (correct for 70% of cases)
- **Balanced Accuracy: 0.50** (only correct for one class)

**When Useful:**
- Shows naive "always predict dominant class" strategy
- For imbalanced data, can have high accuracy but low balanced accuracy
- Model must beat this for clinical utility

---

## Current Implementation in Model Comparison

### Model List (7 Total)

1. **Baseline-Random** - Random guessing (chance level)
2. **Baseline-Majority** - Always predict dominant class
3. **NN** - Neural Network
4. **LR** - Logistic Regression
5. **XGB** - XGBoost
6. **RF** - Random Forest
7. **CB** - CatBoost

### Mock Data Performance Ranges

| Model | Balanced Accuracy Range | Notes |
|-------|------------------------|-------|
| Baseline-Random | 0.48-0.52 | Chance level |
| Baseline-Majority | 0.50 | Always 0.50 for balanced accuracy |
| NN, LR, XGB, RF, CB | 0.65-0.90 | Actual ML performance |

### Filter Options

**Model Filter Dropdown:**
- **All** - Show everything (baselines + ML models)
- **All Models (no baselines)** - Hide baselines, show only ML
- **Baseline-Random** - Show only random baseline
- **Baseline-Majority** - Show only majority baseline
- **NN, LR, XGB, RF, CB** - Show specific model

---

## Visual Example in Model Comparison Tab

### Table Layout (Transposed)

```
┌──────────────────┬──────────────┬──────────────┬──────────────┐
│ Phase/Model      │ D30_resp_3c  │ D90_is_cr    │ crs_gr_ge2   │
├──────────────────┼──────────────┼──────────────┼──────────────┤
│ phase_-6/        │              │              │              │
│ Baseline-Random  │ 0.49 (red)   │ 0.51 (red)   │ 0.50 (red)   │
│ Baseline-Majority│ 0.50 (red)   │ 0.50 (red)   │ 0.50 (red)   │
│ NN               │ 0.82 (yel)   │ 0.88 (grn)   │ 0.76 (yel)   │
│ LR               │ 0.75 (yel) * │ 0.84 (yel)   │ 0.72 (yel) * │
│ XGB              │ 0.79 (yel)   │ 0.85 (yel)   │ 0.73 (yel)   │
│ RF               │ 0.76 (yel)   │ 0.86 (yel)   │ 0.71 (yel)   │
│ CB               │ 0.81 (yel)   │ 0.83 (yel)   │ 0.70 (yel)   │
└──────────────────┴──────────────┴──────────────┴──────────────┘
```

**Key Points:**
- Baselines show at top (clearly worse performance)
- ML models show meaningful improvement over baselines
- Color coding makes baseline (red) vs ML (yellow/green) obvious
- Champion markers (*) show best ML model (not baselines)

---

## Interpretation Guidelines

### Minimum Bar: Beat Random
- Model **must** be significantly better than 0.50 balanced accuracy
- If not, model is no better than random guessing
- Example: 0.55 balanced accuracy → Only 5% better than random → Marginal

### Good Bar: Beat Majority + Margin
- Model should be at least 0.10-0.15 better than majority baseline
- Example: Majority = 0.50, Model = 0.65 → Good improvement
- Example: Majority = 0.50, Model = 0.52 → Not useful

### Clinical Utility Threshold
- **Balanced Accuracy ≥ 0.70** - Potentially clinically useful
- **Balanced Accuracy ≥ 0.80** - Good clinical utility
- **Balanced Accuracy ≥ 0.90** - Excellent clinical utility

---

## Real-World Example

### Scenario: Predicting CR at Day 30

**Dataset:**
- 270 patients
- 180 non-CR (66.7%)
- 90 CR (33.3%)

**Baselines:**
- **Random:** Predict 66.7% non-CR, 33.3% CR randomly
  - Balanced Accuracy: ~0.50
  
- **Majority:** Always predict non-CR
  - Accuracy: 0.667 (looks good!)
  - Balanced Accuracy: 0.50 (not useful - misses all CR cases)

**ML Models:**
- **Logistic Regression:** Balanced Accuracy = 0.75
  - 25% better than baselines
  - Clinically useful

- **Neural Network:** Balanced Accuracy = 0.85
  - 35% better than baselines
  - Very good clinical utility

### Conclusion
The NN model provides real predictive value beyond simple heuristics!

---

## Why Show Baselines in Comparison Table?

### 1. Context for Performance
- "Is 0.70 good?" → Yes, if baseline is 0.50
- "Is 0.70 good?" → No, if baseline is 0.68

### 2. Justify Model Complexity
- Neural network (1000s of parameters) must beat majority baseline (0 parameters)
- If model barely beats baseline, use simpler model

### 3. Catch Model Failures
- Model accidentally worse than baseline? Bug or data leak!
- Model same as baseline? Feature engineering needed

### 4. Publication/Review Requirements
- Academic papers require baseline comparisons
- Clinical validation studies require demonstrating improvement
- Regulatory approval may require beating established baselines

---

## In Clinical Pipeline (`current_state/`)

### Baseline Calculation Scripts

1. **`export_baseline_single_split.py`**
   - Single-split baseline evaluation
   - Exports: `baseline_random_single_accuracy_summary.csv`
   - Exports: `baseline_majority_single_accuracy_summary.csv`

2. **`export_xgb_summary.py`**
   - Cross-validation baseline evaluation
   - Exports: `baseline_random_cv_accuracy_summary.csv`
   - Exports: `baseline_random_cv_balanced_accuracy_summary.csv`
   - Exports: `baseline_majority_cv_accuracy_summary.csv`
   - Exports: `baseline_majority_cv_balanced_accuracy_summary.csv`

### Integration with Model Comparison

**Current:** Mock data includes baselines  
**Future (Phase 4):** Real baseline results from training pipeline

---

## Filter Usage Examples

### Example 1: Compare All Models
```
Model Filter: "All"
→ Shows: 2 baselines + 5 ML models = 7 rows per phase
→ Use case: Full comparison with context
```

### Example 2: Focus on ML Models
```
Model Filter: "All Models (no baselines)"
→ Shows: Only 5 ML models
→ Use case: Compare ML approaches without baseline clutter
```

### Example 3: Check Baseline Performance
```
Model Filter: "Baseline-Majority"
→ Shows: Only majority baseline
→ Use case: Understand minimum bar for each target
```

### Example 4: Neural Network vs Random
```
Model Filter: "NN"
Phase Filter: "phase_-6"
→ Then compare with "Baseline-Random"
→ Use case: Quantify NN improvement over chance
```

---

## Statistics: Mock Data with Baselines

### Counts
- Targets: 7
- Phases: 4
- Models: 7 (2 baselines + 5 ML)
- **Total Results: 196** (7 × 4 × 7)

### Distribution
- Baseline results: 56 (28.6%)
- ML model results: 140 (71.4%)

---

## Future Enhancements

### Statistical Comparison (Planned)

1. **Significance Testing**
   - Is model significantly better than baseline?
   - McNemar's test for paired predictions
   - Bootstrap confidence intervals

2. **Effect Size**
   - How much better is model than baseline?
   - Cohen's d or similar
   - Clinical significance assessment

3. **Net Benefit Analysis**
   - Decision curve analysis
   - Net reclassification improvement (NRI)
   - Integrated discrimination improvement (IDI)

### Additional Baselines (Future)

1. **Baseline-Stratified**
   - Random guessing with stratification
   
2. **Baseline-Clinical**
   - Simple clinical rule (e.g., age > 60)
   
3. **Baseline-Ridge**
   - L2-regularized linear model (simple ML baseline)

---

## Summary

**F1 Score:**
- Harmonic mean of precision and recall
- Balances false positives and false negatives
- Critical for imbalanced classification
- In mock data: ranges 0.62-0.87 (not zero)

**Baseline Comparisons:**
- **YES, we show them!**
- 2 baselines: Random-Prior and Majority
- Mock data: Baselines at 0.48-0.52 balanced accuracy
- ML models: 0.65-0.90 balanced accuracy
- Clear performance gap demonstrates model value

**Implementation:**
- Model Comparison tab includes baselines
- Filter option to show/hide baselines
- Color coding makes baseline vs ML obvious
- Future: Real baseline results from training pipeline

**Clinical Importance:**
- Proves model adds value beyond heuristics
- Required for publication and validation
- Justifies model complexity
- Guides model selection decisions

---

**Status:** Baselines implemented in Model Comparison tab  
**Tests:** 79/79 passing  
**Committed:** Phase 3.2 complete with baseline support  
**Next:** Phase 3.3 - Feature Engineering

---

**Questions Answered:**
1. ✓ What is F1? → Harmonic mean of precision and recall
2. ✓ Why F1 zero? → It's not! Mock data: 0.62-0.87
3. ✓ Do we compare to baselines? → YES! 2 baselines implemented
4. ✓ Where shown? → Model Comparison tab, filterable
5. ✓ Tests passing? → 79/79 passing
6. ✓ Committed? → Yes, all changes committed
