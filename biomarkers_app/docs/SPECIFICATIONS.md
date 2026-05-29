# Biomarkers Pipeline Visualization & Debug Tool
## Comprehensive Specifications v1.0

---

## 1. Executive Summary

### 1.1 Purpose
A Windows desktop application that provides comprehensive visualization, debugging, and execution capabilities for the biomarkers prediction pipeline. The tool serves three primary purposes:
1. **Academic Review**: Review and present pipeline results and visualizations
2. **Research & Development**: Improve and test pipeline components with full dataset
3. **Clinical Prediction**: Input individual patient data and receive outcome predictions

### 1.2 Target Users
- **Primary**: Researchers and data scientists reviewing pipeline results
- **Secondary**: Clinicians (doctors, oncologists) using predictions for research purposes
- **Tertiary**: Hospital administrators and stakeholders viewing demonstrations

### 1.3 Use Cases

#### Use Case 1: Clinical Prediction (Primary)
**Actor**: Clinician with a patient considering CAR-T therapy  
**Flow**:
1. Launch application in Clinical Prediction mode
2. Input patient's clinical features (age, diagnosis, labs, etc.)
3. Select prediction timepoint (Day 30, Day 90, etc.)
4. Receive probability predictions for all outcomes
5. View confidence intervals and risk stratification
6. Export patient report (anonymized ID) for medical records

#### Use Case 2: Model Development
**Actor**: Researcher improving prediction models  
**Flow**:
1. Load full clinical dataset
2. Modify model hyperparameters
3. Execute training pipeline
4. Compare new results with champion models
5. Analyze feature importance and errors
6. Update model registry if improved

#### Use Case 3: Academic Review
**Actor**: PI presenting to hospital administrators or reviewing results  
**Flow**:
1. Application starts directly in Academic Review mode
2. Load pre-computed results automatically
3. Review performance visualizations
4. Switch to Research mode for detailed analysis if needed
5. Switch to Clinical mode for sample predictions if needed
6. Export presentation-ready figures

### 1.4 Key Success Criteria
- **Immediate Access**: Application starts directly in Academic Review mode without mode selection
- **Fullscreen Startup**: Application launches in fullscreen for maximum workspace
- **Mode Switching**: Easy switching between modes via Mode menu
- **Pipeline Visibility**: Complete pipeline execution visibility (every step traceable)
- **Flexibility**: Real-time parameter modification and re-execution for researchers
- **Professional Output**: Visualizations suitable for publications and presentations
- **Ease of Use**: Intuitive interface for both researchers and clinicians
- **Reliability**: Comprehensive error handling and logging for debugging
- **Deployment**: Easy distribution as standalone .exe

---

## 2. Functional Requirements

### 2.1 Core Capabilities

#### 2.1.1 Pipeline Execution
- **FR-001**: Execute complete pipeline from data loading to final results
- **FR-002**: Execute individual pipeline steps in isolation
- **FR-003**: Execute partial pipeline (from step X to step Y)
- **FR-004**: Pause/resume long-running operations
- **FR-005**: Cancel running operations with cleanup
- **FR-006**: Queue multiple pipeline runs with different parameters
- **FR-007**: Save and restore pipeline execution state

#### 2.1.2 Visualization
- **FR-010**: Display pipeline flow diagram with current step highlighted
- **FR-011**: Show real-time progress for each step
- **FR-012**: Generate ROC curves for all models and phases
- **FR-013**: Display confusion matrices with customizable thresholds
- **FR-014**: Show accuracy/balanced accuracy heatmaps (phase × target)
- **FR-015**: Visualize feature importance across models
- **FR-016**: Display feature correlation matrices
- **FR-017**: Compare models side-by-side (NN, LR, RF, XGB, CB, ET, LGB, SVM)
- **FR-018**: Show training curves (loss, accuracy over epochs for NN)
- **FR-019**: Display class distribution at each phase
- **FR-020**: Visualize data splits (train/val/test proportions)

##### Academic Paper Visualization Standards (TRIPOD+AI / REMARK)

**Design critique (addressed in implementation):**
- **Flat list of views** was dense and mixed purpose; views are now **dispersed by category**: Discrimination (ROC, PR), Calibration, Classification (confusion matrix), Summary (heatmap, class distribution).
- **Multi-phase runs** previously collapsed heatmap by (target, model) and mixed phases; **phase filter** and phase-aware heatmap (rows = phase | target when "All phases") ensure correct interpretation.
- **Confusion matrix** lacked **normalized (%)** option expected in papers; optional row-normalized view added.
- **Class labels** on axes remain generic (Class 0/1) until pipeline provides target-specific labels (e.g. CR/PR/NR); **class_labels** parameter is specified for future use.
- **AUC/confidence intervals** (e.g. bootstrap or DeLong) and **sensitivity/specificity at threshold** are specified as future enhancements; not yet in UI.
- **Export at 300 DPI / PDF** for the **current figure** is implemented in the Visualizations tab (**Export PNG (300 DPI)**, **Export PDF**). Batch “export all figures” (FR-072) remains future.

**Required elements (specific):**
- **ROC**: AUC in title, diagonal reference line, axis labels (FPR, TPR), sample size (n) in title or legend; phase and target in caption when applicable.
- **Calibration**: Predicted vs observed probability; perfect-calibration diagonal; sample size; critical for TRIPOD+AI and clinical deployment.
- **Precision-Recall**: AU-PR in title; preferred for imbalanced outcomes; sample size.
- **Confusion matrix**: Class labels on axes (actual vs predicted); raw counts; optional **normalized (%)** by row.
- **Performance heatmap**: Rows = targets (or phase | target when multi-phase); columns = model family; metric selectable (BA, accuracy, AUC, F1); **phase filter** to restrict to one phase.
- **Class distribution**: Bar chart of outcome counts per phase/target (test set); **phase filter** to restrict.
- **Export**: PNG at 300 DPI, PDF vector via on-tab buttons; titles include phase, target, model, and n where applicable.

#### 2.1.2b Visualizations — training metadata contract (change policy)

The **Visualizations** tab reads **`training_result_full`**: `data` = `List[ModelResult]`, `metadata` = dict. **Curve-based views** (ROC, confusion matrix, calibration, precision–recall) require the following **optional** metadata keys when those plots are expected:

| Key | Typical shape | Produced when |
|-----|----------------|---------------|
| `roc_curves` | `(phase, target, model_family, fpr, tpr)` per curve; legacy 3-tuple `(target, model, fpr, tpr)` supported | Single split; repeated holdout (last repeat); **nested CV / 5-fold CV** per `cv_curve_source` (see below) |
| `confusion_matrices` | `(phase, target, model_family, cm)` or legacy 3-tuple | Same |
| `calibration_curves` | `(phase, target, model_family, frac_pos, mean_pred)` | Binary outcomes; same sources as ROC |
| `pr_curves` | `(phase, target, model_family, precision, recall, auprc)` | Binary; same |

**CV figure curves (`PipelineConfig.cv_curve_source`, Training settings “CV figure curves”):**

- **`last_outer_fold`** (default): Illustrative curves from the **last outer CV fold**; metadata includes **`curve_source`** and **`curve_note`** explaining that figures are not pooled CV ROCs.
- **`refit_holdout`**: After CV, a **separate stratified train/test split** (`test_size`, `random_seed`) generates figures only; **reported CV metrics in `ModelResult` are unchanged**. Metadata includes **`curve_note`** stating this.

**Implementations:** `ModelTrainingWrapper.train_models` (single split), `train_models_repeated_holdout`, `train_models_nested_cv`, `train_models_with_cv`. **Consumers:** `VisualizationsWidget.load_training_result`, saved pickles under `results/runs/` and `results/latest/training_results.pkl`.

**Change policy (agents / maintainers):** Do not remove or rename these metadata keys or tuple shapes without updating **`VisualizationsWidget`**, **`tests/unit/test_visualizations_widget.py`**, and this specification. Adding new plot types should extend metadata in a backward-compatible way (optional keys) or version the pickle contract explicitly.

#### 2.1.3 Model Comparison
- **FR-025**: Compare all 8 model families (NN, LR, RF, XGB, CB, ET, LGB, SVM) ✓ IMPLEMENTED
- **FR-026**: Compare across all 4 phases (phase_-6, 0, 15, 30) ✓ IMPLEMENTED
- **FR-027**: Compare across all ~19 targets ✓ IMPLEMENTED
- **FR-028**: Display performance metrics table (accuracy, BA, AUC, F1) ✓ IMPLEMENTED
  - Interactive table with rows=targets, columns=phase×model combinations
  - Switchable metrics: Balanced Accuracy, Accuracy, AUC, F1 Score
  - Real-time filtering by phase, target, and model
- **FR-029**: Highlight best model per target-phase combination ✓ IMPLEMENTED
  - Champion models marked with asterisk (*)
  - Color-coded performance: [+++] Excellent >0.85, [++] Good 0.75-0.85, [+] Fair 0.65-0.75, [-] Poor <0.65
- **FR-029b**: Display "Best only (champion per cell)" view ✓ IMPLEMENTED — compact table: rows=phases, columns=targets, cell=best metric + model name
- **FR-030**: Show statistical significance of differences (FUTURE)
- **FR-031**: Export comparison results as CSV/Excel ✓ IMPLEMENTED (CSV)

#### 2.1.4 Parameter Tuning
- **FR-035**: Modify NN hyperparameters (hidden layers, learning rate, epochs)
- **FR-036**: Modify model-specific parameters (XGB depth, RF trees, etc.)
- **FR-037**: Adjust data split ratios (train/val/test)
- **FR-038**: Select subset of targets for focused training
- **FR-039**: Select subset of phases for focused analysis
- **FR-040**: Enable/disable specific model families
- **FR-041**: Save parameter presets with names
- **FR-042**: Load and apply parameter presets
- **FR-043**: Reset to default parameters

#### 2.1.5 Feature Analysis
- **FR-050**: Display feature importance for each model type ✓ PARTIAL (variability/std table after feature engineering; model-based post-training deferred)
- **FR-051**: Show feature correlation heatmap ✓ IMPLEMENTED (top pairwise correlations table, numeric features)
- **FR-052**: Highlight top-N most important features
- **FR-053**: Filter features by importance threshold
- **FR-054**: Compare feature importance across models
- **FR-055**: Show feature distributions by class
- **FR-056**: Display missing value patterns
- **FR-057**: Show categorical feature encodings

#### 2.1.6 Data Inspection
- **FR-060**: Load and display unified_clinical_data.csv
- **FR-061**: Show dataset statistics (rows, columns, completeness)
- **FR-062**: Display sample records (anonymized if needed)
- **FR-063**: Show target distribution for each phase
- **FR-064**: Validate data integrity before pipeline run
- **FR-065**: Display derived target creation logic
- **FR-066**: Show evaluable gate statistics

#### 2.1.7 Results Management
- **FR-070**: Cache pipeline results for quick re-visualization
- **FR-071**: Compare current run with historical runs
- **FR-072**: Export all visualizations as PNG/PDF
- **FR-073**: Export metrics as CSV/Excel/JSON
- **FR-074**: Generate comprehensive HTML report
- **FR-075**: Export model registry state
- **FR-076**: Save complete experiment configuration
- **FR-077**: Archive runs with timestamps and descriptions

#### 2.1.8 Debugging & Logging
- **FR-080**: Display real-time console output
- **FR-081**: Show step-by-step execution trace
- **FR-082**: Capture and display errors with stack traces
- **FR-083**: Show warnings and validation messages
- **FR-084**: Display timing information per step
- **FR-085**: Show memory usage per step
- **FR-086**: Export debug logs as text files
- **FR-087**: Filter logs by severity (INFO, WARNING, ERROR)
- **FR-088**: Search logs with keyword highlighting

#### 2.1.9 Validation & Testing
- **FR-090**: Run nested CV evaluation
- **FR-091**: Run holdout validation
- **FR-092**: Run stratified K-fold CV
- **FR-093**: Display CV fold results individually
- **FR-094**: Show aggregated CV statistics (mean, std)
- **FR-095**: Compare validation methods

#### 2.1.10 Clinical Prediction Mode (PRIMARY USE CASE)
- **FR-100**: Launch application in Clinical Prediction mode (simplified interface)
- **FR-101**: Display patient input form with all required clinical features
- **FR-102**: Validate patient data in real-time (ranges, required fields, data types)
- **FR-103**: Auto-calculate derived features from input (e.g., ratios, interactions)
- **FR-104**: Select prediction timepoint (Day 30, Day 90, Month 6, Year 1, Best Response)
- **FR-105**: Select which outcomes to predict (response, toxicity, survival, etc.)
- **FR-106**: Load champion models automatically from registry
- **FR-107**: Generate predictions using all trained model families
- **FR-108**: Display probability predictions for all outcomes
- **FR-109**: Show confidence intervals for each prediction
- **FR-110**: Display risk stratification (low, medium, high risk)
- **FR-111**: Show model performance metrics (accuracy, AUC from validation)
- **FR-112**: Compare prediction across different timepoints
- **FR-113**: Highlight most important features contributing to prediction (SHAP-like explanation)
- **FR-114**: Show similar historical patients from training data (privacy-preserved)
- **FR-115**: Generate patient-specific report (PDF with predictions and explanations)
- **FR-116**: Export predictions to EMR-compatible format (HL7/FHIR optional, CSV required)
- **FR-117**: Support batch prediction (upload CSV with multiple patients)
- **FR-118**: Anonymize patient data (no PHI in logs or exports except designated report)
- **FR-119**: Track prediction history with timestamps (audit log)
- **FR-120**: Display disclaimer about clinical decision support tool status

### 2.2 Clinical Prediction Input Requirements

The following clinical features must be collectible via the input form:

#### Demographics & Baseline
- Patient ID (optional, anonymized)
- Age (years)
- Sex (M/F)
- Weight (kg)
- Height (cm) - auto-calculate BSA

#### Disease Characteristics
- Diagnosis (DLBCL, ALL, CLL, MCL, FL, etc.)
- Disease stage
- Prior lines of therapy (count)
- Refractory status (yes/no)
- Bulky disease (yes/no)
- CNS involvement (yes/no)
- Bone marrow involvement (%)

#### Laboratory Values (Phase-specific)
- Complete Blood Count (WBC, ANC, Hemoglobin, Platelets)
- Metabolic panel (Creatinine, Bilirubin, ALT, AST)
- LDH
- Ferritin
- CRP
- Albumin
- Immunoglobulins (IgG, IgA, IgM)

#### CAR-T Specific
- CAR-T product (if applicable)
- Lymphodepletion regimen
- Cell dose (if known)

#### Phase-Specific Data Entry
- **Phase -6**: Baseline values before lymphodepletion
- **Phase 0**: Day of CAR-T infusion
- **Phase 15**: Day 15 post-infusion
- **Phase 30**: Day 30 post-infusion

#### Calculated/Derived Features (Auto)
- BMI
- BSA
- Lab ratios (e.g., neutrophil/lymphocyte ratio)
- Risk scores (if applicable)

### 2.3 Clinical Prediction Output Requirements

#### Primary Output: Risk Probabilities
For selected timepoint and outcomes, display:
```
Day 30 Response Prediction (Patient ID: 12345)
─────────────────────────────────────────────────────
Complete Response (CR):        68% [95% CI: 52-81%]  ✓ LIKELY
Partial Response (PR):         24% [95% CI: 15-36%]
Minimal/No Response (NR):       8% [95% CI: 3-18%]
─────────────────────────────────────────────────────
Overall Response Rate (CR+PR): 92% [95% CI: 82-97%]

Model Performance (Validation):
  Accuracy: 83%  |  Balanced Accuracy: 81%  |  AUC: 0.89
  Based on 252 patients, validated with 5-fold CV
```

#### Secondary Output: Toxicity Predictions
```
Toxicity Risk Assessment
─────────────────────────────────────────────────────
CRS Grade ≥2:                  35% [95% CI: 21-52%]  ⚠ MODERATE
ICANS Grade ≥2:                18% [95% CI: 9-31%]   ✓ LOW
Infection (100 days):          42% [95% CI: 28-58%]  ⚠ MODERATE
```

#### Tertiary Output: Long-term Outcomes
```
Long-term Outcome Predictions
─────────────────────────────────────────────────────
6-Month Response:              72% [95% CI: 58-84%]
1-Year Response:               65% [95% CI: 50-78%]
Relapse/Progression Risk:      28% [95% CI: 16-43%]
```

#### Explanation Section
- Top 5 features driving the prediction
- Comparison to similar patients (anonymized)
- Uncertainty factors (missing data, extrapolation warnings)

---

## 3. Scope Boundaries - What IS and ISN'T Included

### 3.1 IN SCOPE (Version 1.0)

#### Core Functionality ✓
- **Clinical prediction for individual patients** (primary use case)
- **Full pipeline execution** for model training and evaluation
- **All 8 model families** (NN, LR, RF, XGB, CB, Extra Trees, LightGBM, SVM)
- **All 4 phases** (Day -6, 0, 15, 30)
- **All ~19 targets** (response, toxicity, survival outcomes)
- **Comprehensive visualizations** (ROC, heatmaps, confusion matrices, feature importance)
- **Parameter tuning** with preset management
- **Model registry** with champion-challenger tracking
- **Export functionality** (HTML/PDF reports, CSV/Excel data, PNG/PDF figures)
- **Debug console** with full logging
- **Windows .exe packaging** for clinic deployment

#### Data Handling ✓
- Load existing clinical dataset (unified_clinical_data.csv)
- Input single patient data via form
- Batch prediction from CSV upload
- Data validation and quality checks
- Missing value handling
- Feature engineering and derivation

#### Privacy & Security ✓
- No PHI in logs (except designated patient reports)
- Local-only operation (no cloud, no network)
- Anonymized patient IDs
- Audit logging of predictions

#### User Modes ✓
- Clinical Prediction Mode (simplified for clinicians)
- Research Mode (full pipeline access)
- Academic Review Mode (default startup mode)

### 3.2 OUT OF SCOPE (Version 1.0)

#### Excluded Features ✗
- **Electronic Medical Record (EMR) integration** - No direct HL7/FHIR connectivity (manual CSV export only)
- **Real-time model updating** - Models are static per version; no online learning
- **Multi-user/collaborative features** - Single-user desktop application only
- **Cloud deployment** - No web version, no cloud storage
- **Mobile version** - Windows desktop only
- **Database backend** - SQLite cache only, no production database
- **User authentication/roles** - No login system, no role-based access
- **Regulatory compliance certification** - Not certified as medical device (research use disclaimer required)
- **Automatic model retraining** - Manual retraining only
- **SHAP values** - Feature importance only (SHAP deferred to v1.1)
- **Survival curves** - Kaplan-Meier plots deferred to v1.1
- **Subgroup analysis** - Stratified analysis deferred to v1.1
- **Automated hyperparameter tuning** - Manual tuning only (Optuna deferred to v1.1)
- **Model ensembling UI** - Individual models only (ensemble deferred to v1.1)
- **Multi-language support** - English only
- **Accessibility features** - Standard Windows accessibility only
- **Network capabilities** - Fully offline application

#### Data Limitations ✗
- **Longitudinal tracking** - Predictions are point-in-time, no patient follow-up tracking
- **External validation datasets** - Single institution data only
- **Genetic/molecular data** - Clinical features only, no genomics integration
- **Imaging data** - No DICOM or radiology integration
- **Free-text notes** - Structured data only, no NLP

#### Clinical Decision Support ✗
- **Treatment recommendations** - Predictions only, no prescriptive guidance
- **Drug dosing** - No pharmacokinetic calculations
- **Adverse event reporting** - No FDA adverse event submission
- **Clinical trial matching** - No trial eligibility screening
- **Insurance billing codes** - No ICD/CPT code generation

#### Technical Limitations ✗
- **Distributed computing** - Single machine only
- **GPU acceleration** - CPU training only (models are small enough)
- **Streaming data** - Batch processing only
- **API endpoints** - No REST API (desktop app only)
- **Version control for models** - Simple registry only, no MLOps platform

### 3.3 Explicitly NOT a Medical Device

**IMPORTANT DISCLAIMER (must be displayed in application):**

```
⚠ RESEARCH USE ONLY - NOT FOR CLINICAL DIAGNOSIS ⚠

This software is a Clinical Decision Support Tool for research and 
educational purposes. It is NOT an FDA-approved medical device and 
should NOT be used as the sole basis for clinical decisions.

Predictions are probabilistic estimates based on historical data and 
should be interpreted by qualified healthcare professionals in the 
context of complete clinical information.

Always follow institutional protocols and consult with multidisciplinary
teams for CAR-T therapy decisions.
```

This disclaimer must appear:
1. On application launch (splash screen)
2. In Clinical Prediction Mode (top of input form)
3. On every patient report (header and footer)
4. In Help → About dialog

### 3.4 Future Enhancements (Roadmap)

#### Version 1.1 (Post-Launch)
- SHAP value explanations
- Kaplan-Meier survival curves
- Subgroup analysis by diagnosis
- Automated hyperparameter tuning (Optuna)

#### Version 1.2
- Web-based version for remote access
- Multi-user support with audit trails
- External validation dataset support

#### Version 2.0
- EMR integration (HL7 FHIR)
- Real-time model updates
- Genomic/molecular data integration
- NLP for clinical notes

---

## 4. Pipeline Integration

### 3.1 Pipeline Steps (In Order)

#### Step 1: Data Loading
- **Input**: `data/unified_clinical_data.csv`
- **Output**: DataFrame with 252 rows, clinical features
- **Configurable**: File path selection
- **Visualization**: Data preview table, statistics summary

#### Step 2: Target Derivation
- **Process**: Run `derive_targets()` from pipeline.py
- **Output**: DataFrame with added gate columns and response columns
- **Configurable**: Which targets to derive
- **Visualization**: Before/after column comparison, target distributions

#### Step 3: Feature Engineering (Per Phase)
- **Process**: `prepare_features()` from EnhancedNeuralNetworkTrainer
- **Output**: Feature matrix X, feature names
- **Configurable**: Phase selection, feature selection rules
- **Visualization**: Feature correlation, distributions, missing values

#### Step 4: Data Splitting
- **Process**: Stratified train/val/test split
- **Output**: Train/val/test indices
- **Configurable**: Split ratios, stratification strategy, random seed
- **Visualization**: Split proportions, class balance per split

#### Step 5: Model Training (Per Target, Per Phase, Per Model Family)
- **Process**: Train NN, LR, RF, XGB, CB, Extra Trees (ET), LightGBM (LGB), SVM
- **Output**: Trained models, training curves
- **Configurable**: All hyperparameters per model family
- **Visualization**: Training curves, convergence plots, time per model

#### Step 6: Threshold Tuning (Binary Targets)
- **Process**: Optimize threshold on validation set
- **Output**: Optimal threshold per model
- **Configurable**: Metric to optimize (accuracy, BA, F1)
- **Visualization**: Threshold vs metric curve, selected threshold

#### Step 7: Evaluation (Per Target, Per Phase, Per Model)
- **Process**: Calculate metrics on test set
- **Output**: Accuracy, balanced accuracy, AUC, F1, confusion matrix
- **Configurable**: Which metrics to calculate
- **Visualization**: ROC curves, confusion matrices, metric tables

#### Step 8: Model Registry Update
- **Process**: Champion-challenger comparison
- **Output**: Updated registry.json
- **Configurable**: Registry update policy (always, only if better, manual)
- **Visualization**: Champion vs challenger comparison, registry history

#### Step 9: Results Aggregation
- **Process**: Combine all results across phases/targets
- **Output**: CSV and JSON summary files
- **Configurable**: Output format, canonical column order
- **Visualization**: Heatmaps, summary tables, best model highlights

### 3.2 Integration Points

#### 3.2.1 Existing Code Reuse
- **pipeline.py**: Core training logic, target derivation
- **nn_module_enhanced_fixed_v6.py**: Neural network trainer
- **report_phase_minus6_balacc.py**: Balanced accuracy evaluation logic
- **nested_cv_phase_minus6_balacc.py**: Cross-validation logic
- **holdout_phase_minus6_balacc.py**: Holdout validation logic

#### 3.2.2 Wrapper Requirements
All existing functions must be wrapped to:
1. Accept progress callback for UI updates
2. Return structured results (not just print)
3. Support cancellation via threading events
4. Capture stdout/stderr for debug console
5. Handle exceptions gracefully with detailed messages

#### 3.2.3 Configuration Mapping
```python
# Example configuration structure
{
  "data": {
    "path": "data/unified_clinical_data.csv",
    "validate_on_load": true
  },
  "pipeline": {
    "phases": ["phase_-6", "phase_0", "phase_15", "phase_30"],
    "targets": ["D30_response_3class", "D90_is_cr", ...],
    "random_seed": 42
  },
  "models": {
    "enable_nn": true,
    "enable_lr": true,
    "enable_xgb": true,
    "enable_rf": true,
    "enable_catboost": true,
    "nn": {
      "hidden_dims": [128, 64, 32],
      "learning_rate": 0.001,
      "epochs": 500,
      "batch_size": 32
    },
    "xgb": {
      "n_estimators": 400,
      "max_depth": 6,
      "learning_rate": 0.05
    },
    "rf": {
      "n_estimators": 400,
      "max_depth": null
    }
  },
  "splitting": {
    "test_size": 0.3,
    "val_size": 0.25,
    "stratify": true,
    "group_col": null
  },
  "evaluation": {
    "metrics": ["accuracy", "balanced_accuracy", "auc", "f1"],
    "threshold_optimization": "balanced_accuracy"
  },
  "registry": {
    "update_policy": "if_better",
    "path": "models/registry.json"
  }
}
Registry path is the base; when saving, the app writes a timestamped file (e.g. `registry_YYYY-MM-DD_HH-MM-SS.json`) in the same directory.

---

## 4. User Interface Specifications

**All settings in the interface:** All pipeline and training settings are always available in the UI. There is **no Settings or Preferences item in the File or Edit menu** for evaluation, feature selection, or training parameters. The only place to change these is **Pipeline Flow → Settings…** (button next to Load Data). Defaults are publication-oriented (5-fold CV, etc.) and are defined in config; the same options are visible and editable in the Settings dialog. This keeps a single, visible place for configuration and avoids hidden or duplicate settings.

### 4.0 Mode Selection (Startup)

On application launch, user chooses operating mode:

```
╔═══════════════════════════════════════════════════════════════════╗
║ 🧬 Biomarkers CAR-T Prediction Tool                              ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║   Select Mode:                                                    ║
║                                                                   ║
║   ┌─────────────────────────────────────────────────────────┐   ║
║   │  🏥 CLINICAL PREDICTION MODE                            │   ║
║   │                                                          │   ║
║   │  Enter patient data and receive outcome predictions     │   ║
║   │  → For clinicians making treatment decisions            │   ║
║   │                                                          │   ║
║   │            [Launch Clinical Mode]                       │   ║
║   └─────────────────────────────────────────────────────────┘   ║
║                                                                   ║
║   ┌─────────────────────────────────────────────────────────┐   ║
║   │  🔬 RESEARCH & DEVELOPMENT MODE                         │   ║
║   │                                                          │   ║
║   │  Full pipeline access for model training & analysis     │   ║
║   │  → For researchers and data scientists                  │   ║
║   │                                                          │   ║
║   │            [Launch Research Mode]                       │   ║
║   └─────────────────────────────────────────────────────────┘   ║
║                                                                   ║
║   Application starts directly in Academic Review Mode          ║
║   No mode selection dialog - immediate access to interface     ║
║   Switch modes via Mode menu: Clinical | Research | Academic   ║
║                                                                   ║
║   ⚠ RESEARCH USE ONLY - NOT FOR CLINICAL DIAGNOSIS ⚠            ║
║   This tool provides probabilistic predictions for research      ║
║   purposes. Always consult complete clinical information.        ║
║                                                                   ║
║                         [Help]  [Exit]                            ║
╚═══════════════════════════════════════════════════════════════════╝

Size: 800 × 600 px (centered on screen)
```

### 4.1 Clinical Prediction Mode Interface (PRIMARY)

#### 4.1.1 Clinical Prediction Main Window

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║ 🏥 Clinical Prediction Mode                         [Mode: Clinical] [−] [×]  ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ File  Patient  Predict  Export  Help                                          ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ ⚠ RESEARCH USE ONLY - Predictions are for research purposes. Not FDA approved.║
╠═══════════════╦═══════════════════════════════════════════════════════════════╣
║               ║  ┌─ Patient Information ────────────────────────────────┐     ║
║ 📋 Patient    ║  │                                                       │     ║
║    Input      ║  │  Patient ID: [______] (optional, anonymized)         │     ║
║               ║  │  Date: 2026-01-18                                    │     ║
║ ─────────     ║  └───────────────────────────────────────────────────────┘     ║
║ Demographics  ║                                                               ║
║ Disease       ║  ┌─ Demographics ──────────────────────────────────────┐     ║
║ Labs          ║  │  Age:        [___] years                            │     ║
║ Phase Data    ║  │  Sex:        [● Male  ○ Female]                     │     ║
║               ║  │  Weight:     [___] kg                                │     ║
║ ─────────     ║  │  Height:     [___] cm  →  BSA: 1.85 m² (auto)       │     ║
║ 🎯 Predict    ║  └───────────────────────────────────────────────────────┘     ║
║               ║                                                               ║
║ ─────────     ║  ┌─ Disease Characteristics ─────────────────────────────┐     ║
║ 📊 Results    ║  │  Diagnosis:      [DLBCL ▼]                           │     ║
║               ║  │  Stage:          [III ▼]                             │     ║
║ ─────────     ║  │  Prior Lines:    [2 ▼]                               │     ║
║ 📄 Report     ║  │  Refractory:     [☑] Yes  [☐] No                     │     ║
║               ║  │  Bulky Disease:  [☐] Yes  [☑] No                     │     ║
║ ─────────     ║  │  CNS Involvement:[☐] Yes  [☑] No                     │     ║
║ [New Patient] ║  │  BM Involvement: [15 ] %                             │     ║
║ [Save]        ║  └───────────────────────────────────────────────────────┘     ║
║ [Load...]     ║                                                               ║
║ [Clear]       ║  ┌─ Laboratory Values (Phase: [Day -6 ▼]) ──────────────┐     ║
║               ║  │  WBC:       [8.5  ] × 10⁹/L    [✓ Normal]            │     ║
║               ║  │  ANC:       [4.2  ] × 10⁹/L    [✓ Normal]            │     ║
║               ║  │  Hemoglobin:[12.3 ] g/dL       [✓ Normal]            │     ║
║               ║  │  Platelets: [180  ] × 10⁹/L    [✓ Normal]            │     ║
║               ║  │  Creatinine:[0.9  ] mg/dL      [✓ Normal]            │     ║
║               ║  │  LDH:       [245  ] U/L        [⚠ Elevated]          │     ║
║               ║  │  Ferritin:  [420  ] ng/mL      [⚠ Elevated]          │     ║
║               ║  │  CRP:       [8.5  ] mg/L       [⚠ Elevated]          │     ║
║               ║  │  Albumin:   [3.8  ] g/dL       [✓ Normal]            │     ║
║               ║  └───────────────────────────────────────────────────────┘     ║
║               ║                                                               ║
║               ║  [✓] All required fields complete                             ║
║               ║                                                               ║
║               ║                [Generate Predictions]                         ║
╠═══════════════╩═══════════════════════════════════════════════════════════════╣
║ Status: Ready for prediction | Models loaded: NN, LR, XGB, RF, CB            ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Left Panel: 180px fixed width (navigation)
Main Area: Scrollable form
```

#### 4.1.2 Prediction Results View

After clicking "Generate Predictions":

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║ 🏥 Prediction Results - Patient ID: 12345               [Print] [Export] [×]  ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  ┌─ Day 30 Response Prediction ────────────────────────────────────────────┐ ║
║  │                                                                           │ ║
║  │  🟢 Complete Response (CR)                                               │ ║
║  │     Probability: 68%  [95% CI: 52-81%]                                   │ ║
║  │     ████████████████████████████████████░░░░░░░░░░░░░░                   │ ║
║  │     ✓ LIKELY - This patient has a high probability of CR                 │ ║
║  │                                                                           │ ║
║  │  🟡 Partial Response (PR)                                                │ ║
║  │     Probability: 24%  [95% CI: 15-36%]                                   │ ║
║  │     ███████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                   │ ║
║  │                                                                           │ ║
║  │  🔴 Minimal/No Response (NR)                                             │ ║
║  │     Probability: 8%   [95% CI: 3-18%]                                    │ ║
║  │     ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                     │ ║
║  │     ✓ UNLIKELY                                                            │ ║
║  │                                                                           │ ║
║  │  ──────────────────────────────────────────────────────────────────────  │ ║
║  │  Overall Response Rate (CR + PR): 92% [95% CI: 82-97%]                   │ ║
║  │                                                                           │ ║
║  │  Model Performance (from validation):                                    │ ║
║  │    Accuracy: 83% | Balanced Accuracy: 81% | AUC: 0.89                    │ ║
║  │    Validated on 252 patients with 5-fold cross-validation                │ ║
║  └───────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║  ┌─ Toxicity Risk Assessment ──────────────────────────────────────────────┐ ║
║  │                                                                           │ ║
║  │  ⚠ CRS Grade ≥2:              35% [95% CI: 21-52%]   MODERATE RISK       │ ║
║  │  ✓ ICANS Grade ≥2:            18% [95% CI: 9-31%]    LOW RISK            │ ║
║  │  ⚠ Infection (100 days):      42% [95% CI: 28-58%]   MODERATE RISK       │ ║
║  │                                                                           │ ║
║  └───────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║  ┌─ Key Factors Influencing Predictions ───────────────────────────────────┐ ║
║  │                                                                           │ ║
║  │  Top 5 contributing features:                                            │ ║
║  │    1. LDH level (elevated) → ↓ CR probability                            │ ║
║  │    2. Prior lines of therapy (2) → ↓ CR probability                      │ ║
║  │    3. Ferritin level → ↑ toxicity risk                                   │ ║
║  │    4. Age (52 years) → neutral                                           │ ║
║  │    5. BM involvement (15%) → ↓ CR probability                            │ ║
║  │                                                                           │ ║
║  │  [View Detailed Feature Analysis]                                        │ ║
║  └───────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║  ┌─ Similar Patients (Training Data) ──────────────────────────────────────┐ ║
║  │  8 similar patients found with comparable features:                      │ ║
║  │    • 6/8 (75%) achieved Complete Response at Day 30                      │ ║
║  │    • 2/8 (25%) experienced CRS Grade ≥2                                  │ ║
║  │    • Median follow-up: 18 months                                         │ ║
║  └───────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║  [View Other Timepoints]  [Generate PDF Report]  [New Prediction]            ║
║                                                                               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ Prediction completed in 2.3 seconds | Models: Ensemble of NN, XGB, RF        ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### 4.2 Research Mode Interface (Full Pipeline Access)

#### 4.2.1 Main Window Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🔬 Research Mode - Biomarkers Pipeline Tool      [Mode] [−] [□] [×] │
├─────────────────────────────────────────────────────────────────────┤
│ File  Edit  View  Run  Tools  Help                                  │
├──────────────┬──────────────────────────────────────────────────────┤
│              │  ┌────────────────────────────────────────────┐      │
│  Pipeline    │  │                                            │      │
│  Steps       │  │                                            │      │
│  ─────────   │  │         MAIN CONTENT AREA                  │      │
│  □ Load Data │  │         (Tab-based views)                  │      │
│  □ Derive    │  │                                            │      │
│  □ Features  │  │                                            │      │
│  □ Split     │  │                                            │      │
│  □ Train     │  │                                            │      │
│  □ Evaluate  │  │                                            │      │
│  □ Registry  │  │                                            │      │
│  □ Export    │  │                                            │      │
│              │  └────────────────────────────────────────────┘      │
│  [Run All]   │                                                      │
│  [Run Step]  │  ┌─────────────────────────────────────────┐        │
│  [Stop]      │  │  Debug Console                          │        │
│              │  │  > Loading data... ✓ (0.5s)             │        │
│  Parameters  │  │  > Deriving targets... ✓ (1.2s)         │        │
│  ──────────  │  │  > Training NN phase_-6... ⚙ (15.3s)    │        │
│  [Edit...]   │  └─────────────────────────────────────────┘        │
│  [Presets▼]  │                                                      │
├──────────────┴──────────────────────────────────────────────────────┤
│ Status: Ready  │  Progress: 45% (3/7 steps) │  Elapsed: 00:02:15   │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Tab Structure (Research Mode)

**In-app section help:** Every tab and every logical section (group box or table) within it has a **?** button that opens explanation text for that section and its terms (e.g. metrics, baselines, evaluation mode, export columns). This is implemented across Pipeline Flow, Model Comparison, Visualizations, Data Inspector, Feature Analysis, Validation Results, and Registry Viewer.

#### Tab 1: Pipeline Flow ✓ IMPLEMENTED
- **Sections:** Data Loading, Feature Engineering, Model Training, Results. **Each section has a ? button** that explains the section and its terms.
- **Data Loading:** Path, Browse, Load Data, Settings…, Cancel. ? explains loading CSV, target derivation flow, and that Settings controls evaluation mode and optional feature selection.
- **Settings (Training):** All pipeline/training settings live only in Pipeline Flow (see **all settings in the interface**, above; no File or Edit menu Settings). Open via **Settings…** next to Load Data. Dialog: Random seed, Test fraction, **Evaluation mode:** Single split | 5-fold CV | 3× repeated holdout | Nested CV (5-fold outer). **Default is 5-fold CV** (publication-ready). Single split = one train/test split with bootstrap 95% CI; 5-fold CV = stratified 5-fold cross-validation (mean ± std and 95% CI); 3× repeated holdout = multiple independent 70/30 splits (configurable repeats) for stability; Nested CV = outer 5-fold for evaluation, inner 3-fold for hyperparameter tuning (LR, RF, XGB). **Repeats (holdout):** number of splits for repeated holdout (2–10). **Optional feature selection:** checkbox "Use feature selection", method (mutual_info | variance), Top K features (5–500); applied during feature engineering before training. ? in dialog explains each option.
- **Phase dropdown:** All phases (default), phase_-6, phase_0, phase_15, phase_30
  - "All phases" selected + Run Feature Engineering → engineers all four phases
  - Specific phase selected + Run Feature Engineering → engineers that phase only
  - "Run Model Training" enabled only when a specific phase is selected (use "Run all phases" for full pipeline)
- **Feature Engineering:** Phase selector, Run Feature Engineering. Optional feature selection (when enabled in Settings): top K features by variance or mutual information before training. ? explains phase-specific features, data leakage avoidance, and optional feature selection.
- **Model Training:** Run Model Training, Run all phases. Evaluation mode (Single split, 5-fold CV, 3× repeated holdout, Nested CV) is set in Settings…; 5-fold CV is the default. ? explains algorithms, baselines, and evaluation modes.
- **Results:** Short log of latest steps. ? explains what appears here vs Validation Results / Model Comparison.
- Visual flowchart of all pipeline steps; current step highlighted; step status indicators; click step for detailed view; hover for quick stats.

#### Tab 2: Model Comparison ✓ IMPLEMENTED (Phase 3.2)
- **Interactive Comparison Table**
  - Grid layout: Rows = Targets, Columns = Phase × Model combinations
  - Color-coded performance: Light green (>0.85), Light yellow (0.75-0.85), Light orange (0.65-0.75), Light pink (<0.65)
  - Champion markers: Asterisk (*) for best model per target-phase
  - Auto-resizing columns for optimal viewing
  
- **Filter Panel**
  - Phase filter: All, phase_-6, phase_0, phase_15, phase_30
  - Target filter: All, or specific biomarker target
  - Model filter: All, NN, LR, XGB, RF, CB
  - Metric selector: Balanced Accuracy, Accuracy, AUC, F1 Score
  - Display options: Highlight best per target (checkbox), Color code (checkbox)
  
- **Color Legend**
  - Visual key showing performance ranges
  - [+++] Excellent (>0.85), [++] Good (0.75-0.85), [+] Fair (0.65-0.75), [-] Poor (<0.65)
  - [BEST] Champion marker explanation
  
- **Details Panel**
  - Click any cell to view complete metrics
  - Shows: Accuracy, Balanced Accuracy, AUC, F1 Score, Precision, Recall
  - Training metadata: Train time, threshold, sample size
  
- **Export Functionality**
  - Export to CSV with all metrics for filtered results
  - CSV columns include: Phase, Target, Model, metric columns; when available: **Primary_Target**, **Majority_BA**, **Beat_Majority**, **BA_std**, **BA_CI_low**, **BA_CI_high** (Block B / 5-fold CV)
  - Preserves all performance data, not just displayed metric
- **Help (?):** Each section has a ? button: **Filters** (phase/target/model/metric, display mode, primary targets), **Model Comparison table** (grid meaning, color coding, champions, export columns), **Selected Cell Details** (click cell for metric/model/sample size and CI when CV), **Metrics** (Balanced Accuracy, Accuracy, AUC, F1; CV mean ± std and export columns).
  
- **Implementation Details**
  - Widget class: `ModelComparisonWidget` (520 lines)
  - Data type: `ModelResult` dataclass with 6 metrics + metadata
  - Mock data: 140 sample results (7 targets × 4 phases × 5 models) for UI testing
  - Test coverage: 31 unit tests, all passing

#### Tab 3: Visualizations (Phase 5 - IMPLEMENTED)

**Dispersed structure (by purpose):**
- **Status line (top):** Summarizes **`curve_source`**, **`curve_note`**, and outer-fold count when present in training metadata so reviewers see how figures were produced (especially under nested CV or refit holdout).
- **Phase filter:** All phases | phase_-6 | phase_0 | phase_15 | phase_30 (populated from results); applies to heatmap, class distribution, and context in single-figure views.
- **Category → View:**
  - **Discrimination:** ROC Curve, Precision-Recall Curve (target/model selector).
  - **Calibration:** Calibration Curve (binary targets only; target/model selector).
  - **Classification:** Confusion Matrix (target/model selector; optional Normalized (%) checkbox).
  - **Summary:** Performance Heatmap, Class Distribution.

**Per-view specifics:**
- **ROC:** FPR vs TPR; AUC and sample size (n) in title; diagonal reference; phase/target/model in caption.
- **Confusion Matrix:** Rows = actual, columns = predicted; class labels (Class 0/1 or future target-specific); raw counts or row-normalized %.
- **Calibration:** Mean predicted probability vs fraction of positives; perfect-calibration diagonal; n in title.
- **Precision-Recall:** AU-PR and n in title.
- **Performance Heatmap:** Rows = targets (or "phase | target" when multi-phase and no phase filter); columns = model family; selectable metric (balanced_accuracy, accuracy, auc, f1_score); **optional “Hide baselines on heatmap”** to drop Baseline-Majority / Baseline-Random for clearer model-only comparison; phase filter in title when applied.
- **Class Distribution:** Bar chart of test-set class counts per phase/target; phase filter applies; requires confusion matrices in metadata (if missing, an explanatory message is shown instead of a blank plot).

**Data source:** Training step metadata (`roc_curves`, `confusion_matrices`, `calibration_curves`, `pr_curves` — see **§2.1.2b**); **Performance Heatmap** and tables use `List[ModelResult]` even when curve lists are empty (e.g. legacy saved runs). **Load order:** Series options for ROC/CM/cal/PR are built from metadata before repopulating Category/View so selectors stay in sync.

**Empty states:** If results exist but a view cannot be drawn (no curve metadata, wrong phase, matplotlib unavailable), the tab shows a **dedicated message panel** with guidance (e.g. use Summary → Performance Heatmap, re-run training with CV figure settings), not an empty plot area.

**Export:** **Export PNG (300 DPI)** and **Export PDF** save the **currently displayed** figure (`Figure.savefig`). User picks path via file dialog.

**Pipeline alignment:** Default evaluation mode is **Nested CV**; curve figures depend on **Training settings → CV figure curves** (`cv_curve_source` in `default_params.json` / `PipelineConfig`): *Last outer CV fold* (fast, illustrative) or *Refit stratified holdout* (figures-only split). Documented in **§2.1.2b**.

**Help (?):** View type (Phase, Category, View) has ? explaining ROC, Confusion Matrix, Calibration, PR, Heatmap, Class Distribution. Target/Model row has ? explaining series selector, heatmap metric, Normalized (%) for confusion matrix, and heatmap baseline filter.

**Future (specified, not yet implemented):** AUC 95% CI (bootstrap/DeLong); sensitivity/specificity at threshold on ROC or table; target-specific class labels (e.g. CR/PR/NR) from pipeline; batch export of all figures (FR-072).

- **Widget:** `app/ui/widgets/visualizations_widget.py` — `VisualizationsWidget`; receives **`training_result_full`** from Pipeline Runner (`main_window.py`).
- **Tests:** `tests/unit/test_visualizations_widget.py`; training metadata contract: `tests/integration/test_model_training.py` (e.g. nested CV emits curve metadata).

#### Tab 4: Data Inspector ✓ IMPLEMENTED
- **Sections/tabs:** Data Controls, Data View, Column Info, Statistics, Missing Data, Derived Columns. **Each section has a ? button** explaining the section and terms (rows to display, show all columns, refresh; data view content; column type/mappings; statistics summary; missing counts; gates, binary indicators, targets).
- Data preview table (paginated), statistics summary, missing value visualization, derived columns table.
- Column Info: select column for type, sample values, categorical mappings.

#### Tab 5: Feature Analysis ✓ IMPLEMENTED
- **Sections:** Feature Analysis Controls, Feature Summary, Statistics, Missing Values, Feature correlations, Feature importance. **Each section has a ? button** (controls, summary, stats, missing, correlations, importance).
- Feature summary, statistics, and missing-value views ✓
- Feature correlation table (top pairwise correlations, numeric features) ✓
- Feature importance (variability/std table after feature engineering) ✓; model-based importance post-training (deferred)
- Feature selection recommendations (future); feature distribution plots (future); SHAP values (if implemented)

#### Tab 6: Validation Results (IMPLEMENTED)
- **Current validation:** Train/test split details (%, seed, stratification); populated from pipeline config and after Model Training or Run all phases.
- **Validation strategy:** Short description of train/test, k-fold CV, bootstrap CI, **3× repeated holdout** (multiple 70/30 splits), and **Nested CV** (outer 5-fold, inner 3-fold tuning for LR/RF/XGB); planned: temporal/cohort holdout.
- **Validation metrics:**
  - **Train/test split:** Aggregated metrics (Accuracy, Balanced Accuracy, AUC, F1) mean ± std across all trained models; filled when training completes.
  - **K-fold CV summary:** When you run Model Training or Run all phases with 5-fold CV, repeated holdout, or Nested CV (Settings), the Validation Results tab shows an aggregate mean ± std across models/targets. Per-target metrics are in the Model vs baseline table.
  - **Bootstrap CI:** 95% confidence intervals for balanced accuracy on the test set; computed automatically during Model Training; table shows mean and [low – high] per (phase, target, model).
  - **Model vs baseline (per target/phase):** Table: Target, Phase, Majority BA, Best Model, Best BA, **Δ vs Majority** (Best − Majority, with ± std when from CV), Beat Majority. ? explains terms including Δ vs Majority (transparent reporting, Block B).
  - **Class balance (target summary):** Table: Target, Phase, N total, Class counts, Gate filtered. ? explains N total, class counts, and gate filtered (evaluable-only training, Block C).
- **Help (?):** Every section has a ? button: current validation, validation strategy, train/test, k-fold, bootstrap, **Model vs baseline**, **Class balance (target summary)**.
- **Implemented:** Nested CV and repeated holdout produce same ModelResult/Validation Results format as 5-fold CV (mean ± std, 95% CI). **Planned:** Nested CV results table (optional dedicated view), temporal holdout, CV stability plots, statistical tests.

#### Tab 7: Registry Viewer ✓ IMPLEMENTED
- **Sections:** Registry file (path, Browse, Load), Champions (phase × target) table, Update registry from training. **Each section has a ? button** (path/load, champions table meaning, save current results).
- Current champion models table (Phase, Target, Champion model, Metric, Value, Updated).
- Save current training results to registry (from last Model Training or Run all phases).
- Historical performance trends, model provenance (future); registry export/import.

### 4.3 Dialogs & Panels

#### 4.3.1 Parameter Editor Dialog
```
┌─────────────────────────────────────────────┐
│ Pipeline Parameters              [×]        │
├─────────────────────────────────────────────┤
│ ┌─ Data ─────────────────────────────────┐ │
│ │ Data Path: [data/unified...] [Browse] │ │
│ │ □ Validate on load                    │ │
│ └───────────────────────────────────────┘ │
│                                             │
│ ┌─ Models ──────────────────────────────┐ │
│ │ ☑ Neural Network    [Configure...]   │ │
│ │ ☑ Logistic Reg      [Configure...]   │ │
│ │ ☑ XGBoost          [Configure...]   │ │
│ │ ☑ Random Forest     [Configure...]   │ │
│ │ ☑ CatBoost         [Configure...]   │ │
│ │ ☑ Extra Trees       [Configure...]   │ │
│ │ ☑ LightGBM         [Configure...]   │ │
│ │ ☑ SVM (RBF)        [Configure...]   │ │
│ └───────────────────────────────────────┘ │
│                                             │
│ ┌─ Data Splitting ──────────────────────┐ │
│ │ Test Size:       [0.30] (30%)        │ │
│ │ Validation Size: [0.25] (25%)        │ │
│ │ Random Seed:     [42]                │ │
│ │ ☑ Stratify splits                    │ │
│ └───────────────────────────────────────┘ │
│                                             │
│ ┌─ Target Selection ────────────────────┐ │
│ │ ☑ All targets                         │ │
│ │ ☐ Custom selection... [Select]        │ │
│ └───────────────────────────────────────┘ │
│                                             │
│     [Save as Preset...]  [OK]  [Cancel]    │
└─────────────────────────────────────────────┘
```

#### 4.3.2 NN Configuration Dialog
```
┌─────────────────────────────────────────────┐
│ Neural Network Configuration     [×]        │
├─────────────────────────────────────────────┤
│ Hidden Layers:                              │
│   Layer 1: [128 ] neurons                   │
│   Layer 2: [64  ] neurons                   │
│   Layer 3: [32  ] neurons                   │
│   [+ Add Layer]  [− Remove Layer]           │
│                                             │
│ Training:                                   │
│   Learning Rate:    [0.001 ]                │
│   Max Epochs:       [500   ]                │
│   Batch Size:       [32    ]                │
│   Early Stop:       [☑] Patience: [50]      │
│                                             │
│ Regularization:                             │
│   Dropout:          [0.3   ]                │
│   L2 Alpha:         [0.0001]                │
│                                             │
│ Advanced:                                   │
│   Activation:       [ReLU ▼]                │
│   Optimizer:        [Adam ▼]                │
│   Loss Function:    [Auto ▼]                │
│   Focal Loss:       [☐] Gamma: [2.0]        │
│                                             │
│              [Test Config]  [OK]  [Cancel]  │
└─────────────────────────────────────────────┘
```

#### 4.3.3 Export Dialog
```
┌─────────────────────────────────────────────┐
│ Export Results                   [×]        │
├─────────────────────────────────────────────┤
│ Export Type:                                │
│   ○ Current view only                       │
│   ○ All visualizations                      │
│   ● Complete report (HTML + figures)        │
│                                             │
│ Formats:                                    │
│   ☑ PNG (300 dpi)                           │
│   ☑ PDF (vector graphics)                   │
│   ☑ CSV (metrics tables)                    │
│   ☑ JSON (structured data)                  │
│   ☑ Excel (formatted workbook)              │
│                                             │
│ Output Directory:                           │
│   [exports/run_20260118_143022/] [Browse]  │
│                                             │
│ Report Options:                             │
│   Report Title: [Phase -6 Analysis___]      │
│   ☑ Include parameter configuration         │
│   ☑ Include model comparison table          │
│   ☑ Include all visualizations              │
│   ☑ Include debug logs                      │
│                                             │
│                      [Export]    [Cancel]   │
└─────────────────────────────────────────────┘
```

### 4.4 Status Indicators

#### Pipeline Step Status Icons
- ⚪ Pending (not started)
- 🔵 Running (in progress, animated)
- ✅ Complete (finished successfully)
- ❌ Error (failed with error)
- ⚠️ Warning (completed with warnings)
- ⏭️ Skipped (not executed)

#### Progress Feedback
- Overall progress bar (% of total steps)
- Current step progress bar (% of current operation)
- Elapsed time counter
- Estimated time remaining (when available)
- Real-time console output scrolling

---

## 5. Technical Architecture

### 5.1 Application Structure

```
┌────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │   Qt     │  │  Custom  │  │  Plot    │            │
│  │  Widgets │  │  Widgets │  │  Widgets │            │
│  └──────────┘  └──────────┘  └──────────┘            │
└────────────────────────────────────────────────────────┘
                        ↕
┌────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                    │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  Orchestrator│  │  Config Mgr  │  │  Results    │ │
│  │              │  │              │  │  Manager    │ │
│  └──────────────┘  └──────────────┘  └─────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  Step Runner │  │  Viz Engine  │  │  Export Mgr │ │
│  └──────────────┘  └──────────────┘  └─────────────┘ │
└────────────────────────────────────────────────────────┘
                        ↕
┌────────────────────────────────────────────────────────┐
│                    DOMAIN LAYER                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │         Existing Pipeline (wrapped)              │ │
│  │  pipeline.py │ nn_trainer │ evaluators          │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
                        ↕
┌────────────────────────────────────────────────────────┐
│                     DATA LAYER                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │   CSV    │  │   JSON   │  │  SQLite  │            │
│  │   Data   │  │  Config  │  │  Cache   │            │
│  └──────────┘  └──────────┘  └──────────┘            │
└────────────────────────────────────────────────────────┘
```

### 5.2 Threading Model

#### Main Thread (Qt Event Loop)
- Handle all UI interactions
- Update UI elements
- Dispatch work to worker threads

#### Worker Threads (QThread)
- Pipeline execution (one per run)
- Individual step execution (can be parallel)
- Visualization generation (heavy plots)
- Export operations (large file writes)

#### Thread Communication
- Signals/Slots for UI updates
- Thread-safe queue for progress messages
- Thread-safe dict for results collection
- Cancellation tokens for graceful shutdown

### 5.3 Data Management

#### Configuration Files
```
config/
├── default_params.json       # Factory defaults
├── user_params.json          # User modifications
├── presets/                  # Named parameter presets
│   ├── quick_test.json
│   ├── full_run.json
│   └── demo_mode.json
└── pipeline_definition.json  # Step definitions
```

#### Results Cache (SQLite)
```sql
-- Table: runs
CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    timestamp TEXT,
    config_json TEXT,
    status TEXT,
    duration_sec REAL
);

-- Table: step_results
CREATE TABLE step_results (
    run_id TEXT,
    step_name TEXT,
    status TEXT,
    duration_sec REAL,
    result_json TEXT,
    error_msg TEXT,
    PRIMARY KEY (run_id, step_name)
);

-- Table: model_results
CREATE TABLE model_results (
    run_id TEXT,
    phase TEXT,
    target TEXT,
    model_family TEXT,
    accuracy REAL,
    balanced_accuracy REAL,
    auc REAL,
    f1_score REAL,
    threshold REAL,
    PRIMARY KEY (run_id, phase, target, model_family)
);
```

### 5.4 Data Standardization ✓ IMPLEMENTED

#### Overview
Comprehensive standardization of 31 categorical columns to ensure data quality, consistency, and clinical accuracy. All standardizations are applied during data unification (`data/uni_main.py`) and documented in detail.

#### Standardized Categories

**Demographics & Patient Info (5 columns)**
- `gender`: Numeric codes (1/2/3) → Male/Female/Other
- `race`: Numeric codes (1-6) → Race: White/Black or African American/etc.
- `ethnicity`: Numeric codes (0/1) → Not Hispanic or Latino/Hispanic or Latino
- `survival_status_lfu`: Numeric codes (0/1/2) → Alive/Deceased/Lost to FU
- `cat_cause_death`: Numeric codes (1/2) + variants → Disease progression/NRM

**Disease Classification (3 columns)**
- `dx_cart`: Numeric codes (1-4) → Lymphoma/ALL/MM/Other
- `cart_product`: Numeric codes (1-6) → Tisa-cel/Axi-cel/Brexu-cel/Liso-cel/Ide-cel/Cilta-cel
- `performance_status`: Numeric ECOG (0-3) → ECOG 0-3 with clinical descriptions

**CNS Involvement (3 columns)**
- `cns_involvement`: Binary (0/1) + text → No/Yes
- `cns_status`: Binary (0/1) + text → Prior/Active
- `cns_involvement_level`: Numeric codes (1-3) → CNS-1/CNS-2/CNS-3

**Bridging Therapy (3 columns)**
- `bridging_tx`: Case variants (yes/Yes/no/No) → Yes/No
- `bridging_type`: 12 variants → Steroids/Chemo-based regimen/Radiation therapy/Other
- `burden_before_cart`: Numeric (0) + text (bulky) → No burden/Bulky

**Response Assessment (6 columns)**
- `best_response`: 14 variants → 5 standard categories
- `cart_response_category_D30`: 14 variants → 5 standard categories
- `cart_response_90_days`: 12 variants → 5 standard categories
- `cart_response_6_mos`: 9 variants → 5 standard categories
- `cart_response_1_yr`: 7 variants → 5 standard categories
- `relapse_or_progression`: Case variants → Yes/No

**Standard Response Categories:** Complete Response, Partial Response, Stable Disease, Progressive Disease, Inevaluable

**Post-Response Variables (2 columns)**
- `cd19_post_relapse`: Case variants → Positive/Negative/Unknown
- `lymphodep_regimen`: Flu/Cy → Fludarabine, Cyclophosphamide

**Toxicity & Adverse Events (7 columns)**
All standardized from mixed numeric (0/1/0.0/1.0) and text (yes/no) to Yes/No:
- `icans`, `iec-hs`, `icu_admission`, `prbc_infusion`, `plt_transfusion`, `infection_30days`, `pt_transfusion`

**Infection Classification (2 columns)**
- `infection_type_30days`: Removed numeric prefixes, case-standardized → Bacterial/Viral/Fungal
- `infection_type_100_days`: Removed numeric prefixes, case-standardized → Bacterial/Viral/Fungal

#### Documentation
- **Mapping Reference**: `data/CATEGORICAL_MAPPINGS.md` - Complete mapping details for all 31 columns
- **Summary Document**: `biomarkers_app/COMPLETE_DATA_STANDARDIZATION_SUMMARY.md` - Overall impact and usage guide
- **In-App Display**: Data Inspector shows standardization info for each column in Column Info tab

#### Data Quality Impact
- **Before**: 100+ unique inconsistencies across 31 columns, mixed data types, case issues
- **After**: All categorical values standardized, consistent format, human-readable, clinically accurate
- **Testing**: 79/79 tests passing ✓

### 5.6 Error Handling

#### Error Levels
1. **Critical**: Application cannot continue (data file missing)
2. **Error**: Step failed but pipeline can continue (one model failed)
3. **Warning**: Issue detected but processing successful (low sample size)
4. **Info**: Normal operation messages

#### Error Recovery
- Automatic retry for transient failures (3 attempts)
- Fallback to default parameters if invalid config
- Graceful degradation (skip failed models, continue with others)
- Save partial results if pipeline interrupted

#### User Notifications
- Modal dialog for critical errors
- Status bar message for errors/warnings
- Debug console for all messages
- Error log file for debugging

---

## 6. Performance Requirements

### 6.1 Responsiveness
- **UI Update**: < 16ms (60 FPS for smooth animations)
- **Step Status Update**: < 100ms from completion
- **Parameter Change**: < 50ms to reflect in UI
- **Visualization Render**: < 2s for complex plots
- **Data Preview Load**: < 500ms for 1000 rows

### 6.2 Throughput
- **Full Pipeline**: Complete within 30 minutes (all phases, all targets, all models)
- **Single Phase**: Complete within 8 minutes
- **Single Target**: Complete within 2 minutes
- **Results Cache Load**: < 1s for recent run

### 6.3 Resource Usage
- **Memory**: < 4 GB under normal operation
- **CPU**: Utilize available cores for training
- **Disk I/O**: Minimize during execution (batch writes)
- **Cache Size**: < 500 MB per cached run

---

## 7. Export & Reporting

### 7.1 Export Formats

#### Individual Visualizations
- PNG (300 dpi, for presentations)
- PDF (vector, for publications)
- SVG (editable, for further customization)

#### Data Tables
- CSV (raw metrics, compatible with Excel)
- Excel (.xlsx with formatting and multiple sheets)
- JSON (structured, for programmatic access)

#### Comprehensive Reports
- HTML (standalone, with embedded images)
- PDF Report (multi-page, professional layout)
- Markdown (for documentation)

### 7.2 Report Contents

#### Executive Summary
- Run metadata (date, time, configuration)
- Overall performance summary
- Best models per phase
- Key findings and warnings

#### Detailed Results
- Model comparison table (all phases × targets × models)
- Performance metrics per model family
- Feature importance rankings
- Statistical significance tests

#### Visualizations
- ROC curves (one per phase-target combination)
- Confusion matrices (best model per target)
- Accuracy heatmaps (all models, all phases)
- Feature correlation heatmap
- Training convergence plots (NN only)

#### Appendix
- Complete parameter configuration
- Data statistics and quality checks
- Debug log summary
- Model registry state

---

## 8. Testing Strategy

### 8.1 Unit Tests
- Configuration manager (load, save, validate)
- Data loader (parsing, validation)
- Each pipeline step wrapper (input/output validation)
- Visualization generators (correct plot types)
- Export functions (file creation, format validation)

### 8.2 Integration Tests
- Full pipeline execution (happy path)
- Partial pipeline execution (specific steps)
- Parameter modification and re-run
- Results caching and retrieval
- Multi-threaded execution stability

### 8.3 UI Tests
- UI element creation and layout
- User interactions (button clicks, parameter changes)
- Dialog workflows (open, modify, save)
- Progress updates during long operations

### 8.4 Performance Tests
- Memory usage under full pipeline run
- Thread safety (concurrent runs)
- Cache efficiency (load times)
- Large dataset handling (scalability)

### 8.5 User Acceptance Tests
- Complete workflow scenarios (load → configure → run → export)
- Error recovery (simulate failures, verify graceful handling)
- Academic Review mode (prepare and present results to stakeholders)
- Distribution test (install on clean Windows machine)

---

## 9. Security & Data Privacy

### 9.1 Data Handling
- No patient identifiers in UI (use row indices only)
- No data transmission (fully offline application)
- No cloud dependencies
- No telemetry or analytics

### 9.2 File System Access
- Read-only access to source data by default
- Write access only to designated output folders
- No modification of original pipeline code
- Configurable data directory (avoid hardcoded paths)

### 9.3 Configuration Security
- Validate all user inputs before execution
- Sanitize file paths (prevent directory traversal)
- No execution of arbitrary code from config files
- No eval() or exec() on user input

---

## 10. Distribution & Deployment

### 10.1 Packaging Requirements
- Single .exe file (with all dependencies bundled)
- Optional: Installer (for Start Menu shortcuts)
- Include sample configuration files
- Include brief user guide (PDF)

### 10.2 PyInstaller Configuration
```python
# build_exe.py specifications
{
    "name": "BiomarkersPipelineTool",
    "version": "1.0.0",
    "icon": "app/assets/icon.ico",
    "console": False,  # Windowed application
    "one_file": True,  # Single .exe
    "hidden_imports": [
        "sklearn", "torch", "xgboost", "catboost",
        "matplotlib", "seaborn", "plotly"
    ],
    "data_files": [
        ("config/", "config"),
        ("app/assets/", "assets")
    ],
    "exclude_modules": [
        "tkinter", "test", "unittest"  # Reduce size
    ]
}
```

### 10.3 Dependencies
- Python 3.11 runtime (embedded)
- PyQt6 (UI framework)
- Existing pipeline dependencies (pandas, numpy, sklearn, torch, xgboost, catboost)
- Matplotlib, Plotly, Seaborn (visualization)
- openpyxl (Excel export)
- Jinja2 (HTML report generation)

### 10.4 System Requirements
- **OS**: Windows 10/11 (64-bit)
- **RAM**: Minimum 8 GB, recommended 16 GB
- **Storage**: 2 GB for application, 5 GB for results/cache
- **CPU**: Multi-core recommended (parallel training)
- **Display**: Minimum 1920×1080 resolution

---

## 11. Future Enhancements (Out of Scope for v1.0)

### 11.1 Advanced Features
- SHAP value explanations for predictions
- Automated hyperparameter tuning (Optuna integration)
- Real-time collaboration (multiple users, shared cache)
- Cloud deployment option (web version)
- Integration with R scripts (rpy2)

### 11.2 Extended Analytics
- Survival analysis visualizations (Kaplan-Meier curves)
- Subgroup analysis (stratified by clinical variables)
- Time-series analysis for longitudinal data
- Meta-analysis across multiple datasets

### 11.3 Enhanced Visualization
- Interactive 3D plots (dimensionality reduction)
- Animated pipeline flow (step-by-step transitions)
- Custom dashboard builder (drag-and-drop widgets)
- Real-time metric streaming during training

---

## 12. Open Questions & Decisions Needed

### 12.1 Data Loading
- **Q**: Should the app package sample/demo data for colleagues without access to full dataset?
- **Decision Needed**: [_______________]

### 12.2 Model Persistence
- **Q**: Should trained models be saved to disk for later inspection/deployment?
- **Decision Needed**: [_______________]

### 12.3 Comparison Baseline
- **Q**: Should we always compare against the July 2025 baseline results?
- **Decision Needed**: [_______________]

### 12.4 Validation Methods
- **Q**: Which validation method should be default (nested CV, holdout, or k-fold)?
- **Decision Needed**: [_______________]

### 12.5 Feature Selection
- **Q**: Should the app support interactive feature selection (enable/disable features)?
- **Decision Needed**: [_______________]

### 12.6 Ensemble Models
- **Q**: Should the app support custom ensemble creation (average of selected models)?
- **Decision Needed**: [_______________]

### 12.7 Branding
- **Q**: Application name, logo, color scheme preferences?
- **Decision Needed**: [_______________]

---

## 13. Implementation Status

### 13.1 Phase 1: Foundation (COMPLETE)
- [x] Application architecture and project structure
- [x] Core logger system with file and console output
- [x] Configuration manager with presets and validation
- [x] Main window with tab structure
- [x] Basic UI framework with PyQt6
- **Test Coverage**: 35 unit tests, all passing

### 13.2 Phase 2: Pipeline Orchestration (COMPLETE)
- [x] Pipeline orchestrator with step tracking
- [x] Data loader wrapper with progress callbacks
- [x] Pipeline runner widget with cancellation support
- [x] Result caching and structured outputs
- [x] Integration tests for data loading
- **Test Coverage**: 48 tests (35 unit + 13 integration), all passing

### 13.3 Phase 3.1: Pipeline Integration (COMPLETE)
- [x] Target derivation wrapper
- [x] Connected Load → Derive Targets pipeline
- [x] Data Inspector widget with 3 tabs (Overview, Column Details, Derived Columns)
- [x] Progress scaling for multi-step operations
- [x] Metadata propagation between pipeline stages
- **Test Coverage**: 58 tests (35 unit + 23 integration), all passing

### 13.4 Phase 3.2: Model Comparison Tab (COMPLETE)
- [x] ModelResult dataclass for performance metrics
- [x] ModelComparisonWidget with interactive table
- [x] Filter panel (phase, target, model, metric)
- [x] Color-coded performance visualization
- [x] Champion marking (best model per target-phase)
- [x] Display mode: "All models" vs "Best only (champion per cell)" — compact view with one row per phase, best value + model name per target
- [x] Details panel with complete metrics
- [x] CSV export functionality
- [x] ASCII-based UI (no emojis for compatibility)
- [x] Mock data system for UI testing
- **Test Coverage**: 79 tests (66 unit + 13 integration), all passing
- **Lines of Code**: 545 new lines (520 widget + 25 types)

### 13.5 Phase 3.3: Feature Engineering (COMPLETE - 2026-01-19)
- [x] Feature engineering wrapper
- [x] Phase-specific feature preparation (NN-aligned: baseline, daily, monthly, specific_days; phases phase_-6, phase_0, phase_15, phase_30)
- [x] Complete Load → Derive → Engineer pipeline
- [x] Integration tests (11 tests passing)
- **Lines of Code**: 302 new lines (wrapper)
- **Features**:
  - NN-aligned feature groups (same as `versions/nn_module_enhanced_fixed_v6.py`) for parity with CLI results
  - Phase-specific feature selection (baseline → baseline+daily → baseline+daily+monthly+specific_days)
  - **Optional feature selection** (Settings): when enabled, keep top K **numeric** features by variance or mutual information (MI uses first suitable primary target); method and Top K configurable in Pipeline Flow → Settings; **default off** in `default_params.json` (`use_feature_selection`: false) for publication-style runs unless explicitly enabled
  - Categorical handling: string levels including **Unknown** for missing; one-hot expansion when assembling **X** in model training (not in the engineered frame)
  - Numeric preprocessing: imputation to zero; log1p after clip for LDH/ferritin-named columns; **StandardScaler per phase**, fit stored on `FeatureEngineeringWrapper`
  - Fit/transform pattern for train/test separation
  - Progress callbacks and cancellation support

### 13.X Code Organization & Token Economy (COMPLETE - 2026-01-19)
- [x] Updated .cursorrules with token economy best practices
- [x] Split data_inspector_widget.py (596→562 lines)
- [x] Split model_comparison_widget.py (506→452 lines)  
- [x] Split uni_standardize.py (518→482 lines)
- [x] Created helper modules for constants and utilities
- [x] All 90 tests passing after refactoring

### 13.6 Phase 4: Model Training (COMPLETE)
- [x] Model training wrapper (`app/pipeline/wrappers/model_training_wrapper.py`)
- [x] Neural Network (via EnhancedNeuralNetworkTrainer when available)
- [x] Logistic Regression (OneVsRestClassifier)
- [x] Random Forest, XGBoost, CatBoost, Extra Trees, LightGBM, SVM
- [x] Build X from engineered DataFrame (numeric + one-hot categorical); prepare_target for y
- [x] Progress callback and cancellation support; returns List[ModelResult] + ROC/confusion in metadata
- [x] Pipeline Runner: "Run Model Training" section; TrainingWorker (QThread); results to Model Comparison and Visualizations
- [x] **Evaluation modes** (Settings): Single split, stratified 5-fold CV, 3× repeated holdout (`train_models_repeated_holdout`), Nested CV (5-fold outer, 3-fold inner tuning for LR/RF/XGB only; other families use fixed hyperparameters in `train_models_nested_cv`); same ModelResult/Validation Results format. **`default_params.json`** sets `evaluation_mode` to **`nested_cv`** for publication-style runs (5-fold CV remains selectable in Settings).
- [x] **Pipeline–CLI alignment**: Feature set matches command-line NN trainer (NN_FEATURE_GROUPS / phase mapping); no target cap (all trainable targets); NN binary targets passed as float to BCEWithLogitsLoss
- [ ] Hyperparameter configuration UI (deferred)

### 13.7 Phase 5: Evaluation & Visualization (COMPLETE)
- [x] Evaluation wrapper (`app/pipeline/wrappers/evaluation_wrapper.py`) structures training result for display
- [x] ROC curve data produced in training wrapper; VisualizationsWidget displays ROC (target/model selector)
- [x] Confusion matrix in training metadata; VisualizationsWidget displays CM heatmap; optional normalized (%)
- [x] Calibration and precision-recall curves (binary) in training metadata; Calibration and PR views
- [x] Performance heatmap (phase-aware: target x model or phase|target x model); phase filter; optional hide baselines on heatmap
- [x] Class distribution from confusion matrix row sums; phase filter
- [x] Dispersed UI: Category (Discrimination / Calibration / Classification / Summary) and Phase filter
- [x] Training result (data + metadata) emitted to Model Comparison and Visualizations via signals
- [x] **CV figure metadata:** Nested CV and 5-fold CV populate curve lists per **`cv_curve_source`** (`last_outer_fold` | `refit_holdout`); metadata includes **`curve_source`**, **`curve_note`** (see **§2.1.2b**)
- [x] **Visualizations UX:** Status line, empty-state messages (no blank canvas), PNG 300 DPI + PDF export for current figure
- [ ] Feature importance plots (data available from training; UI deferred)
- [ ] Training curves for NN (deferred)
- [ ] AUC 95% CI, sensitivity/specificity at threshold (specified in Tab 3); batch export all figures (FR-072)

### 13.8 Phase 6: Model Registry (IMPLEMENTED)
- [x] Registry manager for champion models (load/save; saved files use current datetime in name, e.g. `registry_YYYY-MM-DD_HH-MM-SS.json`)
- [x] Registry Viewer tab: table (phase, target, champion, metric, value), Load/Save current results
- [x] Hyperparameter UI: Settings dialog (random seed, test fraction) in Pipeline Flow
- [x] Feature Analysis: Correlations tab (top pairwise correlations table) and Feature Importance tab (variability/std table) populated after feature engineering
- [x] Validation Results: Train/test metrics, k-fold CV summary (from Model Training or Run all phases when using CV mode), bootstrap 95% CI; ? help on each section
- [ ] Champion-challenger comparison (future)
- [ ] Model versioning and history (future)

---

## Appendix A: Technology Decisions Rationale

### Why PyQt6 over other frameworks?
- **Native look**: Windows-native appearance and feel
- **Maturity**: Stable, well-documented, large community
- **Rich widgets**: Built-in support for tables, trees, plots
- **Threading**: Excellent threading model with signals/slots
- **Packaging**: Works well with PyInstaller for .exe creation
- **Matplotlib integration**: Seamless embedding of plots

### Why SQLite for results cache?
- **Embedded**: No separate database server needed
- **Fast**: Efficient queries for recent runs
- **Portable**: Single file, easy to backup/share
- **Structured**: Better than JSON for complex queries
- **Standard**: Well-supported, cross-platform

### Why not web-based (Flask/Django)?
- User requested Windows Forms style
- No network dependency required
- Better performance for heavy computations
- Easier distribution as .exe
- More responsive UI for data-intensive operations

---

## Appendix B: Glossary

- **BA**: Balanced Accuracy
- **Champion-Challenger**: Registry pattern where new models (challengers) are compared against current best (champion)
- **Gate**: Evaluable_gate target indicating if a response assessment is valid
- **Phase**: Time point relative to CAR-T infusion (day -6, 0, 15, 30)
- **Target**: Outcome variable being predicted
- **Model Family**: Type of model (NN, LR, RF, XGB, CB, ET, LGB, SVM)

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-26  
**Status**: Draft for Review
