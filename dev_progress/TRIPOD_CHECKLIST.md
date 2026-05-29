# TRIPOD Checklist — Prediction Model Development and Validation

**Study:** CAR-T outcome prediction (development and internal validation)  
**Filled:** 2026-02-26 | **Block E1**

Items marked (D) = development, (V) = validation, (D;V) = both.  
**Done** = completed in this project; **Partial** = partly addressed; **N/A** = not applicable.

---

## Title and Abstract

| # | Item | Status | Notes |
|---|------|--------|--------|
| 1 | Identify as developing and/or validating a prediction model; state target population and outcome | Done | CAR-T therapy outcomes; single-center cohort |
| 2 | Provide a structured abstract: objectives, design, setting, participants, sample size, predictors, outcome, analysis, results, conclusions | Partial | Use LIMITATIONS.md + METHODS.md for wording; state "internal validation only; external validation needed" |

---

## Introduction

| # | Item | Status | Notes |
|---|------|--------|--------|
| 3 | Explain medical context and rationale; reference existing models if any | Done | CAR-T outcome prediction context |
| 4 | State objectives and whether development, validation, or both | Done | Development and internal validation (no external validation) |

---

## Methods

### Source of data

| # | Item | Status | Notes |
|---|------|--------|--------|
| 5 | Describe study design and data source for development (and validation if separate) | Done | Single-center; development and internal validation from same cohort with stratified split or CV |

### Participants

| # | Item | Status | Notes |
|---|------|--------|--------|
| 6 | Describe setting, eligibility, and treatment | Partial | Document in manuscript: CAR-T recipients; eligibility as per local protocol |
| 7 | Explain how participants were selected and flow | Partial | Single cohort; evaluable gates applied per outcome (see ANALYSIS_PLAN, BLOCK_B_C_SUMMARY) |

### Outcome

| # | Item | Status | Notes |
|---|------|--------|--------|
| 8 | Clearly define outcome(s), how and when assessed | Done | Primary targets in ANALYSIS_PLAN.md; response, toxicity, relapse, survival; timepoints D30, D90, etc. |
| 9 | Report blinding of outcome assessment if relevant | N/A | Retrospective; no blinding |

### Predictors

| # | Item | Status | Notes |
|---|------|--------|--------|
| 10 | List all predictors with definitions and timing | Partial | Feature groups in feature_engineering_wrapper; phase-specific (phase_-6, 0, 15, 30) |
| 11 | Report handling of missing predictor data | Done | Imputation/fill in pipeline; documented in wrapper and METHODS.md |

### Sample size, missing data, statistical analysis

| # | Item | Status | Notes |
|---|------|--------|--------|
| 12 | Explain how sample size was determined | Partial | Convenience sample; n≈252; state in LIMITATIONS |
| 13 | Describe handling of missing data | Done | Per predictor and outcome; evaluable gates for outcomes |
| 14 | Describe model type and building procedure | Done | METHODS.md: NN, LR, RF, XGB, CB; stratification; class weights |
| 15 | Describe internal validation (e.g. split, CV) | Done | Single stratified split or 5-fold stratified CV; bootstrap 95% CI for BA |
| 16 | Report performance measures with uncertainty (e.g. CIs) | Done | BA, AUC, F1; mean ± std and 95% CI from CV or bootstrap |

### Risk groups

| # | Item | Status | Notes |
|---|------|--------|--------|
| 17 | If risk groups used, describe how defined | N/A | Optional for manuscript |

---

## Results

| # | Item | Status | Notes |
|---|------|--------|--------|
| 18 | Report participant flow and characteristics | Partial | Use target_summary and class balance tables |
| 19 | Report model performance with CIs | Done | Model Comparison export; Validation Results; bootstrap and CV CIs |
| 20 | Report model vs baseline comparison | Done | Model vs baseline table; Beat_Majority in export |
| 21 | Report calibration if applicable | Partial | Calibration curves in app; report in manuscript |

---

## Discussion

| # | Item | Status | Notes |
|---|------|--------|--------|
| 22 | Discuss limitations (including generalizability) | Done | LIMITATIONS.md: single center, n, no external validation, some outcomes do not beat baseline |
| 23 | Discuss clinical use and next steps | Partial | State external validation needed; no clinical use without validation |

---

## TRIPOD+AI (if ML/AI models reported)

| # | Item | Status | Notes |
|---|------|--------|--------|
| AI-1 | Describe AI/ML model type and training | Done | NN, tree-based; METHODS.md |
| AI-2 | Report hyperparameters and tuning | Partial | Defaults documented; optional tuning deferred |
| AI-3 | Report transparency/interpretability where available | Partial | Feature importance placeholder; baseline comparison and BA reported |

---

**Reference:** Collins et al., TRIPOD statement (BMJ 2015); TRIPOD+AI for prediction models using regression or machine learning.
