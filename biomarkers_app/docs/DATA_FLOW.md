# Data Flow & System Architecture
## Biomarkers Pipeline Tool v1.0

---

## 1. High-Level Data Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION LAYER                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │  Main      │  │  Parameter │  │  Pipeline  │  │  Debug     │       │
│  │  Window    │◄─┤  Editor    │◄─┤  Controls  │◄─┤  Console   │       │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘       │
│         ▲ │                                               ▲              │
└─────────┼─┼───────────────────────────────────────────────┼──────────────┘
          │ │                                               │
          │ │  UI Events (clicks, parameter changes)        │  Log Messages
          │ │                                               │
          │ ▼                                               │
┌─────────┼─────────────────────────────────────────────────┼──────────────┐
│         │             APPLICATION LOGIC LAYER             │              │
│  ┌──────▼──────┐  ┌──────────────┐  ┌──────────────┐  ┌──▼───────────┐ │
│  │ Pipeline    │  │ Config       │  │ Results      │  │ Logger       │ │
│  │ Orchestrator├─►│ Manager      │  │ Cache Mgr    │  │ Manager      │ │
│  └──────┬──────┘  └──────┬───────┘  └──────▲───────┘  └──────────────┘ │
│         │                │                  │                            │
│         │ Step Execution │ Params           │ Results                    │
│         ▼                ▼                  │                            │
│  ┌─────────────────────────────────────────┼───────────────────────┐   │
│  │              Step Runners (Workers)      │                       │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │                       │   │
│  │  │ Load │ │Derive│ │ Prep │ │Train │───┘                       │   │
│  │  │ Data │→│Target│→│ Feat │→│Models│                           │   │
│  │  └──────┘ └──────┘ └──────┘ └──────┘                           │   │
│  └───────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────┬────────────────────────────────┘
                                       │ Wrapped Function Calls
                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         DOMAIN LAYER (Your Code)                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │  pipeline.py   │  │  nn_trainer.py │  │  evaluators.py │            │
│  │                │  │                │  │                │            │
│  │ • derive_      │  │ • Enhanced     │  │ • Metrics      │            │
│  │   targets()    │  │   NN Trainer   │  │   calculation  │            │
│  │ • train_       │  │ • prepare_     │  │ • ROC, CM      │            │
│  │   target_      │  │   features()   │  │                │            │
│  │   phase()      │  │                │  │                │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
└──────────────────────────────────────┬────────────────────────────────┘
                                       │ Data I/O
                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                            DATA LAYER                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ unified_     │  │ registry.    │  │ results_     │  │ cache.db   │ │
│  │ clinical_    │  │ json         │  │ nn_enhanced/ │  │ (SQLite)   │ │
│  │ data.csv     │  │              │  │ *.csv, *.json│  │            │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Pipeline Execution Flow

### 2.1 Initialization Phase

```
User Action: Click "Run All"
      │
      ▼
┌─────────────────────────────────────┐
│ Orchestrator.run_pipeline()         │
│ • Validate configuration            │
│ • Check data file exists            │
│ • Initialize results collectors     │
│ • Set up progress tracking          │
│ • Create worker thread              │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Load Configuration                  │
│ • Read user_params.json             │
│ • Merge with default_params.json    │
│ • Validate all parameters           │
│ • Create Config object              │
└────────────┬────────────────────────┘
             │
             ▼
      [Start Worker Thread]
```

### 2.2 Step 1: Data Loading

```
Step: Load Data
      │
      ▼
┌──────────────────────────────────────┐
│ StepRunner.run_data_loading()        │
│ Input:  config.data.path             │
│ Output: DataFrame                    │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ DataLoaderWrapper.load()             │
│ • Read CSV file                      │
│ • Validate schema                    │
│ • Check for required columns         │
│ • Report statistics                  │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ pd.read_csv(path)                    │
│ → DataFrame(252 rows × 47 cols)      │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Validation                           │
│ • Row count > 0                      │
│ • Required columns present           │
│ • Data types correct                 │
└─────────────┬────────────────────────┘
              │
              ├─ Progress Update → UI (10%)
              ├─ Log → Debug Console
              │
              ▼
┌──────────────────────────────────────┐
│ Cache Results                        │
│ • Store DataFrame in memory          │
│ • Update results_cache["data"]       │
│ • Mark step as complete              │
└─────────────┬────────────────────────┘
              │
              ▼
        [Next Step]
```

### 2.3 Step 2: Target Derivation

```
Step: Derive Targets
      │
      ▼
┌──────────────────────────────────────┐
│ StepRunner.run_target_derivation()   │
│ Input:  DataFrame (from cache)       │
│ Output: DataFrame + derived columns  │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ pipeline.derive_targets(df)          │
│ • Create artificial columns          │
│ • Build evaluable gates              │
│ • Derive response targets            │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ For each target in DERIVED_CONFIG:   │
│   1. Build gate column               │
│      (evaluable vs inevaluable)      │
│   2. Apply transformation            │
│      (3class / binary_cr / etc.)     │
│   3. Add to DataFrame                │
└─────────────┬────────────────────────┘
              │
              ├─ Progress Updates → UI (20%)
              ├─ Logs per target → Console
              │
              ▼
┌──────────────────────────────────────┐
│ Validation                           │
│ • Expected targets created           │
│ • No unexpected nulls                │
│ • Class distributions reasonable     │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Cache Results                        │
│ • Update DataFrame in cache          │
│ • Store target metadata              │
│ • Mark step as complete              │
└─────────────┬────────────────────────┘
              │
              ▼
        [Next Step]
```

### 2.4 Step 3: Feature Engineering (Per Phase)

```
Step: Prepare Features
      │
      ▼
┌──────────────────────────────────────┐
│ For each phase in config.phases:     │
│   run_feature_engineering(phase)     │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ trainer.prepare_features(df, phase)  │
│ • Filter to phase-appropriate data   │
│ • One-hot encode categoricals        │
│ • Create interaction terms           │
│ • Scale/normalize if needed          │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Feature Matrix Creation              │
│ Base features:       47              │
│ One-hot encoded:     68              │
│ Interactions:        9               │
│ ────────────────────────             │
│ Total:               124 (phase_-6)  │
└─────────────┬────────────────────────┘
              │
              ├─ Progress Update → UI (30%)
              ├─ Log feature counts → Console
              │
              ▼
┌──────────────────────────────────────┐
│ Store in Cache                       │
│ cache["features"][phase] = {         │
│   "X": np.ndarray,                   │
│   "feature_names": List[str],        │
│   "timestamp": datetime              │
│ }                                    │
└─────────────┬────────────────────────┘
              │
              ▼
      [Repeat for next phase]
              │
              ▼
        [All phases done]
              │
              ▼
        [Next Step]
```

### 2.5 Step 4: Data Splitting

```
Step: Split Data
      │
      ▼
┌──────────────────────────────────────┐
│ StepRunner.run_data_splitting()      │
│ For each target:                     │
│   Split train/val/test               │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ trainer.prepare_target(df, target)   │
│ • Get valid indices for target       │
│ • Encode target labels               │
│ • Determine if binary/multiclass     │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ split_indices(y, test_size=0.3)      │
│ • Stratified split if possible       │
│ • Nested split for train/val/test    │
│ • Return indices arrays              │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Split Result (example)               │
│ Train indices:  [176 samples]        │
│ Val indices:    [44 samples]         │
│ Test indices:   [32 samples]         │
└─────────────┬────────────────────────┘
              │
              ├─ Progress Update → UI (40%)
              ├─ Log split sizes → Console
              │
              ▼
┌──────────────────────────────────────┐
│ Store in Cache                       │
│ cache["splits"][target] = {          │
│   "train_idx": np.ndarray,           │
│   "val_idx": np.ndarray,             │
│   "test_idx": np.ndarray,            │
│   "y_encoded": np.ndarray            │
│ }                                    │
└─────────────┬────────────────────────┘
              │
              ▼
      [Repeat for all targets]
              │
              ▼
        [Next Step]
```

### 2.6 Step 5: Model Training (Per Target, Per Phase, Per Model)

```
Step: Train Models
      │
      ▼
┌──────────────────────────────────────┐
│ For phase in phases:                 │
│   For target in targets:             │
│     For model in enabled_models:     │
│       train_model(phase,target,model)│
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Example: Train NN                    │
│ ModelTrainer.train_nn(...)           │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Get Data from Cache                  │
│ • X_train, X_val, X_test             │
│ • y_train, y_val, y_test             │
│ • feature_names                      │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Initialize Model                     │
│ MLPClassifier(                       │
│   hidden_layer_sizes=(128,64,32),    │
│   learning_rate_init=0.001,          │
│   ...                                │
│ )                                    │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Training Loop                        │
│ For each epoch:                      │
│   • Forward pass                     │
│   • Calculate loss                   │
│   • Backward pass                    │
│   • Update weights                   │
│   • Log metrics                      │
│   • Check early stopping             │
└─────────────┬────────────────────────┘
              │
              ├─ Progress Updates → UI (50-70%)
              ├─ Epoch logs → Console
              │
              ▼
┌──────────────────────────────────────┐
│ Training Complete                    │
│ • Best epoch: 152                    │
│ • Best val loss: 0.3456              │
│ • Training time: 2m 15s              │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Store Trained Model                  │
│ cache["models"][phase][target][model]│
│ = {                                  │
│   "model": model_object,             │
│   "training_history": {...},         │
│   "best_epoch": 152,                 │
│   "train_time": 135.2                │
│ }                                    │
└─────────────┬────────────────────────┘
              │
              ▼
      [Repeat: LR, XGB, RF, CB]
              │
              ▼
      [Repeat for all targets]
              │
              ▼
      [Repeat for all phases]
              │
              ▼
        [Next Step]
```

### 2.7 Step 6: Threshold Tuning (Binary Targets Only)

```
Step: Tune Thresholds
      │
      ▼
┌──────────────────────────────────────┐
│ For each binary target:              │
│   For each model:                    │
│     tune_threshold()                 │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Get Validation Predictions           │
│ probs = model.predict_proba(X_val)   │
│ → Array of probabilities [0-1]       │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Grid Search Over Thresholds          │
│ For thr in [0.1, 0.12, ..., 0.9]:    │
│   preds = (probs > thr)              │
│   metric = balanced_accuracy(y, pred)│
│   if metric > best:                  │
│     best = metric                    │
│     best_thr = thr                   │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Optimal Threshold Found              │
│ threshold = 0.48                     │
│ val_balanced_accuracy = 0.876        │
└─────────────┬────────────────────────┘
              │
              ├─ Log threshold → Console
              │
              ▼
┌──────────────────────────────────────┐
│ Store Threshold                      │
│ cache["thresholds"][phase][target]   │
│   [model] = 0.48                     │
└─────────────┬────────────────────────┘
              │
              ▼
      [Repeat for all binary targets]
              │
              ▼
        [Next Step]
```

### 2.8 Step 7: Model Evaluation

```
Step: Evaluate Models
      │
      ▼
┌──────────────────────────────────────┐
│ For phase, target, model:            │
│   evaluate_model()                   │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Get Test Predictions                 │
│ If binary:                           │
│   probs = model.predict_proba(X_test)│
│   preds = (probs > threshold)        │
│ Else:                                │
│   preds = model.predict(X_test)      │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Calculate Metrics                    │
│ • accuracy                           │
│ • balanced_accuracy                  │
│ • precision, recall, f1              │
│ • AUC (if binary)                    │
│ • confusion matrix                   │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Metrics Result                       │
│ {                                    │
│   "accuracy": 0.883,                 │
│   "balanced_accuracy": 0.876,        │
│   "auc": 0.912,                      │
│   "f1": 0.865,                       │
│   "confusion_matrix": [[...]]        │
│ }                                    │
└─────────────┬────────────────────────┘
              │
              ├─ Progress Update → UI (80%)
              ├─ Log metrics → Console
              │
              ▼
┌──────────────────────────────────────┐
│ Store Evaluation Results             │
│ cache["evaluations"][phase][target]  │
│   [model] = metrics_dict             │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Save to SQLite Cache                 │
│ INSERT INTO model_results VALUES(...) │
└─────────────┬────────────────────────┘
              │
              ▼
      [Repeat for all combinations]
              │
              ▼
        [Next Step]
```

### 2.9 Step 8: Update Model Registry

```
Step: Update Registry
      │
      ▼
┌──────────────────────────────────────┐
│ For each (phase, target):            │
│   champion_challenger_update()       │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Get Current Champion                 │
│ champion = registry[phase][target]   │
│ champion_acc = 0.850                 │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Find Best Challenger                 │
│ best_model = argmax(acc for all      │
│              models this run)        │
│ best_acc = 0.876                     │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Compare                              │
│ if best_acc > champion_acc:          │
│   Replace champion                   │
│ else:                                │
│   Keep existing champion             │
└─────────────┬────────────────────────┘
              │
              ├─ If updated:
              │   Log → Console
              │   Notification → UI
              │
              ▼
┌──────────────────────────────────────┐
│ Update Registry                      │
│ registry[phase][target] = {          │
│   "accuracy": 0.876,                 │
│   "model_family": "XGBoost",         │
│   "timestamp": "20260118_143022",    │
│   "source": "challenger"             │
│ }                                    │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Save Registry                        │
│ save_registry(registry)              │
│ → models/registry.json               │
└─────────────┬────────────────────────┘
              │
              ▼
        [Next Step]
```

### 2.10 Step 9: Aggregate Results & Export

```
Step: Aggregate & Export
      │
      ▼
┌──────────────────────────────────────┐
│ Collect All Results                  │
│ • From cache["evaluations"]          │
│ • From registry.json                 │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Build Summary Tables                 │
│ For each phase:                      │
│   row = {"Phase": phase}             │
│   For each target:                   │
│     row[target] = champion_acc       │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Format to Canonical Order            │
│ Reorder columns to CANONICAL_ORDER   │
│ Fill missing with 0.0                │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Export CSV                           │
│ pd.DataFrame(rows).to_csv(           │
│   "results_nn_enhanced/              │
│    all_targets_summary_YYYYMMDD.csv" │
│ )                                    │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Export JSON                          │
│ json.dump({                          │
│   "summary_table": summary,          │
│   "results": detailed_results        │
│ }, ...)                              │
└─────────────┬────────────────────────┘
              │
              ├─ Progress Update → UI (100%)
              ├─ Log export paths → Console
              │
              ▼
┌──────────────────────────────────────┐
│ Pipeline Complete                    │
│ • Notify user                        │
│ • Show summary stats                 │
│ • Enable export/report generation    │
└──────────────────────────────────────┘
```

---

## 3. Visualization Data Flow

### 3.1 ROC Curve Generation

```
User Action: Select "ROC Curves" tab, choose phase/target
      │
      ▼
┌──────────────────────────────────────┐
│ UI Event Handler                     │
│ on_roc_tab_params_changed()          │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Check Cache                          │
│ If plot exists and data unchanged:   │
│   Load from cache                    │
│ Else:                                │
│   Generate new plot                  │
└─────────────┬────────────────────────┘
              │
              ▼ (generate new)
┌──────────────────────────────────────┐
│ Fetch Data from Results Cache        │
│ For each selected model:             │
│   • y_true (test set)                │
│   • y_probs (predicted probabilities)│
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Calculate ROC Curve Points           │
│ from sklearn.metrics import          │
│   roc_curve, auc                     │
│ For each model:                      │
│   fpr, tpr, _ = roc_curve(y, probs)  │
│   roc_auc = auc(fpr, tpr)            │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Render Plot (Matplotlib)             │
│ fig, ax = plt.subplots()             │
│ For each model:                      │
│   ax.plot(fpr, tpr, label=...)       │
│ ax.set_xlabel("FPR")                 │
│ ax.set_ylabel("TPR")                 │
│ ax.legend()                          │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Embed in Qt Widget                   │
│ canvas = FigureCanvasQTAgg(fig)      │
│ layout.addWidget(canvas)             │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Cache Plot                           │
│ plot_cache["roc"][params_hash] = fig │
└──────────────────────────────────────┘
              │
              ▼
        [Display to User]
```

### 3.2 Heatmap Generation

```
User Action: Select "Heatmaps" tab, choose metric/model
      │
      ▼
┌──────────────────────────────────────┐
│ Fetch Data                           │
│ matrix = []                          │
│ For phase in phases:                 │
│   row = []                           │
│   For target in targets:             │
│     acc = results[phase][target]     │
│           [model][metric]            │
│     row.append(acc)                  │
│   matrix.append(row)                 │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Convert to DataFrame                 │
│ df = pd.DataFrame(                   │
│   matrix,                            │
│   index=phases,                      │
│   columns=targets                    │
│ )                                    │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Render Heatmap (Seaborn)             │
│ fig, ax = plt.subplots()             │
│ sns.heatmap(                         │
│   df,                                │
│   annot=True,                        │
│   cmap="RdYlGn",                     │
│   vmin=0.6, vmax=0.95,               │
│   ax=ax                              │
│ )                                    │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Add Annotations                      │
│ • Highlight best per row             │
│ • Add border to champion models      │
│ • Show color scale                   │
└─────────────┬────────────────────────┘
              │
              ▼
        [Embed in Qt & Display]
```

---

## 4. Configuration Management Flow

### 4.1 Load Configuration on Startup

```
App Start
    │
    ▼
ConfigManager.__init__()
    │
    ▼
Load default_params.json
    │
    ▼
Check if user_params.json exists
    │
    ├─ Yes: Load and merge with defaults
    │         (user params override defaults)
    │
    └─ No: Use defaults only
    │
    ▼
Validate merged configuration
    │
    ├─ Valid: Return config object
    │
    └─ Invalid: Show error, use defaults
    │
    ▼
Config object available to app
```

### 4.2 Save Configuration When Modified

```
User: Modifies parameters in dialog, clicks "OK"
    │
    ▼
ParameterDialog.on_ok_clicked()
    │
    ▼
Validate all inputs
    │
    ├─ Invalid: Show error, don't save
    │
    └─ Valid: Continue
    │
    ▼
Build new config dict
    │
    ▼
ConfigManager.save_user_config(config)
    │
    ▼
Write to user_params.json
    │
    ▼
Emit signal: config_changed
    │
    ▼
Subscribers update (e.g., UI refreshes param display)
```

### 4.3 Preset Management

```
User: Selects preset from dropdown
    │
    ▼
ConfigManager.load_preset(preset_name)
    │
    ▼
Read config/presets/{preset_name}.json
    │
    ▼
Merge with defaults (preset overrides)
    │
    ▼
Validate
    │
    ▼
Update current config
    │
    ▼
Update UI to reflect preset values
    │
    ▼
User can further modify or run directly
```

---

## 5. Results Caching Strategy

### 5.1 Memory Cache (Fast Access)

```python
# In-memory structure
results_cache = {
    "run_id": "20260118_143022",
    "config_hash": "a7b3c9d2...",  # Hash of configuration
    
    "data": pd.DataFrame,  # Loaded data
    
    "features": {
        "phase_-6": {"X": np.ndarray, "names": [...]},
        "phase_0": {...},
        ...
    },
    
    "splits": {
        "D30_response_3class": {
            "train_idx": np.ndarray,
            "val_idx": np.ndarray,
            "test_idx": np.ndarray
        },
        ...
    },
    
    "models": {
        "phase_-6": {
            "D30_response_3class": {
                "NN": {"model": ..., "history": ...},
                "LR": {...},
                ...
            },
            ...
        },
        ...
    },
    
    "evaluations": {
        "phase_-6": {
            "D30_response_3class": {
                "NN": {"accuracy": 0.82, "balanced_accuracy": 0.80, ...},
                ...
            },
            ...
        },
        ...
    },
    
    "plots": {
        "roc_phase-6_D30_response_3class": matplotlib.Figure,
        ...
    }
}
```

### 5.2 Disk Cache (Persistent, SQLite)

```
When pipeline step completes:
    1. Save results to memory cache (fast)
    2. Asynchronously save to SQLite (persistent)
    
On app restart:
    1. Check if recent runs exist in SQLite
    2. If config matches, offer to load cached results
    3. If user accepts, load from SQLite → memory cache
    4. Skip re-execution, go straight to visualization
    
Cache invalidation:
    - Config changes → new run required
    - Data file modified → new run required
    - User explicitly clears cache → force re-run
```

---

## 6. Threading & Concurrency Model

### 6.1 Thread Responsibilities

```
Main Thread (Qt Event Loop)
├─ Handle all UI events
├─ Update UI widgets
├─ Dispatch work to workers
└─ Receive results via signals

Worker Thread 1 (Pipeline Orchestrator)
├─ Run pipeline steps sequentially
├─ Emit progress signals
├─ Emit result signals
└─ Handle cancellation

Worker Thread 2+ (Parallel Training, optional)
├─ Train multiple models in parallel
├─ Report progress per model
└─ Synchronize results
```

### 6.2 Signal/Slot Communication

```
Worker Thread                    Main Thread
     │                               │
     │    Signal: step_started       │
     ├──────────────────────────────►│ Update UI (highlight step)
     │                               │
     │    Signal: progress_update    │
     ├──────────────────────────────►│ Update progress bar
     │                               │
     │    Signal: log_message        │
     ├──────────────────────────────►│ Append to console
     │                               │
     │    Signal: step_completed     │
     ├──────────────────────────────►│ Mark step complete, show ✓
     │                               │
     │    Signal: pipeline_finished  │
     ├──────────────────────────────►│ Enable export, show summary
     │                               │
     │◄──────────────────────────────┤
     │    Signal: cancel_requested   │
     │                               │ User clicks "Stop"
     │ (Check cancellation token)    │
```

### 6.3 Cancellation Flow

```
User: Clicks "Stop" button
    │
    ▼
Set cancellation_token.is_set()
    │
    ▼
Signal propagates to worker thread
    │
    ▼
Worker checks token after each sub-operation
    │
    ├─ Token set: Cleanup and exit early
    │     │
    │     ▼
    │   Save partial results
    │     │
    │     ▼
    │   Emit pipeline_cancelled signal
    │     │
    │     ▼
    │   UI shows "Cancelled" status
    │
    └─ Token not set: Continue
```

---

## 7. Error Propagation

```
Exception occurs in worker thread (e.g., model training fails)
    │
    ▼
Catch exception in step runner
    │
    ▼
Log full traceback to debug console
    │
    ▼
Emit error signal with details
    │
    ▼
Main thread receives error signal
    │
    ├─ Update step status to ❌ Error
    │
    ├─ Show error in console (red)
    │
    └─ Decide: Continue with other models or abort?
        │
        ├─ Continue: Mark this model as failed, proceed
        │
        └─ Abort: Stop pipeline, save partial results
```

---

## 8. Export Data Flow

```
User: Clicks "Generate Report"
    │
    ▼
Show export dialog
    │
    ▼
User selects options (formats, components)
    │
    ▼
Clicks "Generate"
    │
    ▼
ExportManager.generate_report(options)
    │
    ├─ Gather all selected data from cache
    │
    ├─ Generate visualizations (if not cached)
    │
    ├─ Render HTML template (Jinja2)
    │
    ├─ Convert HTML → PDF (if requested)
    │
    ├─ Export tables to CSV/Excel
    │
    ├─ Save all figures as PNG/PDF
    │
    └─ Bundle into output directory
    │
    ▼
Show completion dialog
    │
    ▼
If "Open after export" checked:
    Open report in default viewer/browser
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-18  
**Status**: Draft for Review
