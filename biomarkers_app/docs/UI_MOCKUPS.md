# UI Mockups and Wireframes
## Biomarkers Pipeline Tool v1.0

---

## 1. Main Window - Pipeline Flow View (Default)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║ 🧬 Biomarkers Pipeline Tool                                  [−] [□] [×]      ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ File   Edit   View   Run   Tools   Help                                      ║
╠══════════════╦════════════════════════════════════════════════════════════════╣
║              ║  ┌─ Pipeline Flow ─────────────────────────────────────────┐  ║
║ Pipeline     ║  │                                                          │  ║
║ Steps        ║  │    ┌──────────────┐                                      │  ║
║ ────────     ║  │    │ 1. Load Data │  ✅ Complete (0.5s)                  │  ║
║              ║  │    └──────┬───────┘                                      │  ║
║ ✅ Load Data ║  │           │                                              │  ║
║  252 rows    ║  │           ▼                                              │  ║
║              ║  │    ┌─────────────────┐                                   │  ║
║ ✅ Derive    ║  │    │ 2. Derive       │  ✅ Complete (1.2s)               │  ║
║  19 targets  ║  │    │    Targets      │                                   │  ║
║              ║  │    └────────┬────────┘                                   │  ║
║ 🔵 Features  ║  │             │                                            │  ║
║  Running...  ║  │             ▼                                            │  ║
║              ║  │    ┌─────────────────┐                                   │  ║
║ ⚪ Split     ║  │    │ 3. Prepare      │  🔵 Running... (8.3s)             │  ║
║              ║  │    │    Features     │  ████████░░░░░░░ 60%              │  ║
║ ⚪ Train     ║  │    └────────┬────────┘  Processing phase_0...            │  ║
║              ║  │             │                                            │  ║
║ ⚪ Evaluate  ║  │             ▼                                            │  ║
║              ║  │    ┌─────────────────┐                                   │  ║
║ ⚪ Registry  ║  │    │ 4. Split Data   │  ⚪ Pending                        │  ║
║              ║  │    └────────┬────────┘                                   │  ║
║ ⚪ Aggregate ║  │             │                                            │  ║
║              ║  │             ▼                                            │  ║
║              ║  │    ┌─────────────────┐                                   │  ║
║ [▶ Run All]  ║  │    │ 5. Train Models │  ⚪ Pending                        │  ║
║              ║  │    │  • NN           │  (Est: 15 min)                    │  ║
║ [▶ Run Step] ║  │    │  • LR           │                                   │  ║
║              ║  │    │  • XGBoost      │                                   │  ║
║ [⏸ Pause]    ║  │    │  • RF           │                                   │  ║
║              ║  │    │  • CatBoost     │                                   │  ║
║ [⏹ Stop]     ║  │    └────────┬────────┘                                   │  ║
║              ║  │             │                                            │  ║
║ ─────────    ║  │             ▼                                            │  ║
║              ║  │    ┌─────────────────┐                                   │  ║
║ Parameters   ║  │    │ 6. Evaluate     │  ⚪ Pending                        │  ║
║ ─────────    ║  │    │    Models       │                                   │  ║
║              ║  │    └────────┬────────┘                                   │  ║
║ Data Path:   ║  │             │                                            │  ║
║  unified_... ║  │             ▼                                            │  ║
║              ║  │    ┌─────────────────┐                                   │  ║
║ Split: 70/15 ║  │    │ 7. Update       │  ⚪ Pending                        │  ║
║ /15          ║  │    │    Registry     │                                   │  ║
║              ║  │    └────────┬────────┘                                   │  ║
║ Models: 5/5  ║  │             │                                            │  ║
║              ║  │             ▼                                            │  ║
║ [⚙ Edit...]  ║  │    ┌─────────────────┐                                   │  ║
║              ║  │    │ 8. Aggregate    │  ⚪ Pending                        │  ║
║ [📁 Presets▼]║  │    │    Results      │                                   │  ║
║              ║  │    └─────────────────┘                                   │  ║
║  • Quick     ║  │                                                          │  ║
║  • Full      ║  │  [Click any step for details]                           │  ║
║  • Demo      ║  └──────────────────────────────────────────────────────────┘  ║
║              ║                                                                ║
║              ║  ┌─ Debug Console ────────────────────────────────────────┐  ║
║              ║  │ [All▼] [Clear] [Export] [Search: ____________] [🔍]    │  ║
║              ║  ├─────────────────────────────────────────────────────────┤  ║
║              ║  │ [INFO] 14:30:15 - Loading data from unified_clinical... │  ║
║              ║  │ [INFO] 14:30:16 - ✓ Loaded 252 rows, 47 columns        │  ║
║              ║  │ [INFO] 14:30:16 - Deriving targets...                   │  ║
║              ║  │ [INFO] 14:30:17 - Created 5 gate columns                │  ║
║              ║  │ [INFO] 14:30:18 - Created 14 derived target columns     │  ║
║              ║  │ [INFO] 14:30:18 - ✓ Target derivation complete          │  ║
║              ║  │ [INFO] 14:30:18 - Preparing features for phase_-6...    │  ║
║              ║  │ [INFO] 14:30:20 - Created 124 features (phase_-6)       │  ║
║              ║  │ [INFO] 14:30:20 - Preparing features for phase_0...     │  ║
║              ║  │ [INFO] 14:30:23 - Created 156 features (phase_0) ⚙      │  ║
║              ║  └─────────────────────────────────────────────────────────┘  ║
╠══════════════╩════════════════════════════════════════════════════════════════╣
║ ⚙ Status: Running Step 3/8 │ Progress: 37% │ Elapsed: 00:02:15 │ ETA: 00:03:45 ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Dimensions: 1920 × 1080 recommended
Left Panel: 200px fixed width
Console: 200px height (resizable)
```

---

## 2. Main Window - Model Comparison View

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║ 🧬 Biomarkers Pipeline Tool                                  [−] [□] [×]      ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ [Pipeline Flow] [Model Comparison] [Visualizations] [Data] [Features] [...]  ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ ┌─ Filters ─────────────────────────────────────────────────────────────────┐ ║
║ │ Phase: [All ▼]  Target: [All ▼]  Model: [All ▼]  Metric: [Accuracy ▼]   │ ║
║ │ Show: [☑ Best per target] [☑ Color code] [☐ Show difference from best]   │ ║
║ └───────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║ ┌─ Model Comparison Table ──────────────────────────────────────────────────┐ ║
║ │ Target              │ phase_-6              │ phase_0               │...  │ ║
║ │                     │ NN   LR  XGB  RF  CB  │ NN   LR  XGB  RF  CB  │     │ ║
║ ├─────────────────────┼───────────────────────┼───────────────────────┼─────┤ ║
║ │ D30_response_3class │ 0.82 0.75 0.79 0.76 🏆│ 0.85 0.78 0.81 0.77 ⚫│ ... │ ║
║ │ D90_is_cr           │ 0.88 0.84 🏆 0.85 0.86│ 0.90 0.87 🏆 0.88 0.89│ ... │ ║
║ │ crs_grade_ge2       │ 0.76 🏆 0.72 0.73 0.71│ 0.78 🏆 0.74 0.75 0.73│ ... │ ║
║ │ icans_grade_ge2     │ 0.71 0.68 0.69 🏆 0.70│ 0.73 0.70 0.71 🏆 0.72│ ... │ ║
║ │ infection_100days   │ 0.79 0.76 0.78 0.77 🏆│ 0.81 0.78 0.80 0.79 🏆│ ... │ ║
║ │ relapse_or_progress │ 0.84 0.81 0.83 🏆 0.82│ 0.86 0.83 0.85 🏆 0.84│ ... │ ║
║ │ survival_status_lfu │ 0.77 0.74 0.76 0.75 🏆│ 0.79 0.76 0.78 0.77 🏆│ ... │ ║
║ │ ...                 │ ...                   │ ...                   │ ... │ ║
║ └───────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║ Color Legend:  🟢 Best (>0.85)  🟡 Good (0.75-0.85)  🟠 Fair (0.65-0.75)     ║
║                🔴 Poor (<0.65)  🏆 Champion (best in row)                     ║
║                                                                               ║
║ ┌─ Statistics ──────────────────────────────────────────────────────────────┐ ║
║ │ Selected Cell: XGBoost, D90_is_cr, phase_-6                               │ ║
║ │ ────────────────────────────────────────────────────────────────────────  │ ║
║ │ Accuracy:          0.8834                                                 │ ║
║ │ Balanced Accuracy: 0.8756                                                 │ ║
║ │ AUC:               0.9123                                                 │ ║
║ │ F1 Score:          0.8645                                                 │ ║
║ │ Precision:         0.8912                                                 │ ║
║ │ Recall:            0.8401                                                 │ ║
║ │ ────────────────────────────────────────────────────────────────────────  │ ║
║ │ Train Time:        12.3s                                                  │ ║
║ │ Threshold:         0.48                                                   │ ║
║ │ Sample Size:       252 (train: 176, val: 44, test: 32)                   │ ║
║ │ ────────────────────────────────────────────────────────────────────────  │ ║
║ │ [View ROC] [View CM] [View Details]                                       │ ║
║ └───────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║ [📊 Export Table] [📈 Plot Comparison] [📄 Generate Report]                  ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ ✓ Ready │ Last run: 2026-01-18 14:32:45 │ 76 models trained                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 3. Main Window - Visualizations Tab

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║ 🧬 Biomarkers Pipeline Tool                                  [−] [□] [×]      ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ [Pipeline Flow] [Model Comparison] [Visualizations] [Data] [Features] [...]  ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ ┌────────────────────────────────────────────────────────────────────────────┐ ║
║ │ [ROC Curves] [Confusion Matrix] [Heatmaps] [Feature Imp] [Training] [...]│ ║
║ └────────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║ ┌─ ROC Curve Configuration ─────────────────────────────────────────────────┐ ║
║ │ Target: [D90_is_cr ▼]  Phase: [phase_-6 ▼]  Models: [☑All ☐NN ☐LR ...]  │ ║
║ └───────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║ ┌─ ROC Curves: D90_is_cr (phase_-6) ───────────────────────────────────────┐ ║
║ │ 1.0 ┤                                                    ▓▓▓▓▓▓▓          │ ║
║ │     │                                              ▓▓▓▓▓▓                 │ ║
║ │ 0.8 ┤                                         ▓▓▓▓▓                       │ ║
║ │     │                                    ▓▓▓▓▓                            │ ║
║ │ 0.6 ┤                              ▓▓▓▓▓    NN (AUC=0.91) ──────         │ ║
║ │ T   │                         ▓▓▓▓▓         LR (AUC=0.87) ─ ─ ─         │ ║
║ │ P   │                    ▓▓▓▓▓              XGB (AUC=0.88) ······         │ ║
║ │ R   │              ▓▓▓▓▓▓                   RF (AUC=0.86) ──··──         │ ║
║ │ 0.4 ┤         ▓▓▓▓▓                         CB (AUC=0.89) ─────         │ ║
║ │     │    ▓▓▓▓▓                                                            │ ║
║ │ 0.2 ┤ ▓▓▓                                                                 │ ║
║ │     │▓                                                                    │ ║
║ │ 0.0 ┼─────────────────────────────────────────────────────────────────── │ ║
║ │     0.0    0.2    0.4    0.6    0.8    1.0                              │ ║
║ │                   False Positive Rate                                    │ ║
║ └───────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║ ┌─ Plot Options ────────────────────────────────────────────────────────────┐ ║
║ │ [☑ Show legend] [☑ Show AUC values] [☐ Show CI bands] [☐ Show threshold] │ ║
║ │ DPI: [300 ▼]  Size: [Large ▼]  Style: [Publication ▼]                    │ ║
║ │                                                                            │ ║
║ │ [💾 Save PNG] [💾 Save PDF] [💾 Save SVG] [📋 Copy to Clipboard]          │ ║
║ └───────────────────────────────────────────────────────────────────────────┘ ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ ✓ Ready                                                                       ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 4. Parameter Editor Dialog - Main

```
╔════════════════════════════════════════════════════════════════════╗
║ ⚙ Pipeline Parameters                                         [×] ║
╠════════════════════════════════════════════════════════════════════╣
║ [General] [Models] [Data Splitting] [Targets] [Evaluation]        ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║ ┌─ Data Source ────────────────────────────────────────────────┐  ║
║ │                                                              │  ║
║ │ Data File:                                                   │  ║
║ │  [data/unified_clinical_data.csv            ] [Browse...]   │  ║
║ │                                                              │  ║
║ │ ☑ Validate data on load                                      │  ║
║ │ ☑ Show warnings for missing values                           │  ║
║ │ ☐ Use cached preprocessed data (if available)               │  ║
║ │                                                              │  ║
║ └──────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║ ┌─ Pipeline Execution ─────────────────────────────────────────┐  ║
║ │                                                              │  ║
║ │ Phases to Process:                                           │  ║
║ │  ☑ phase_-6  ☑ phase_0  ☑ phase_15  ☑ phase_30              │  ║
║ │                                                              │  ║
║ │ Random Seed: [42        ]  (for reproducibility)            │  ║
║ │                                                              │  ║
║ │ Parallel Execution:                                          │  ║
║ │  ☑ Enable parallel training (use multiple CPU cores)        │  ║
║ │  Max Workers: [4  ▼]  (0 = auto-detect)                     │  ║
║ │                                                              │  ║
║ └──────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║ ┌─ Output & Logging ───────────────────────────────────────────┐  ║
║ │                                                              │  ║
║ │ Results Directory:                                           │  ║
║ │  [results_nn_enhanced/                      ] [Browse...]   │  ║
║ │                                                              │  ║
║ │ Log Level: [INFO ▼]  (DEBUG, INFO, WARNING, ERROR)          │  ║
║ │                                                              │  ║
║ │ ☑ Save detailed logs to file                                │  ║
║ │ ☑ Auto-save results after each step                         │  ║
║ │                                                              │  ║
║ └──────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║                                                                    ║
║    [Reset to Defaults]     [Save as Preset...]     [OK] [Cancel]  ║
╚════════════════════════════════════════════════════════════════════╝

Size: 700 × 600 px
Modal dialog
Tabbed interface for organization
```

---

## 5. Parameter Editor - Models Tab

```
╔════════════════════════════════════════════════════════════════════╗
║ ⚙ Pipeline Parameters                                         [×] ║
╠════════════════════════════════════════════════════════════════════╣
║ [General] [Models] [Data Splitting] [Targets] [Evaluation]        ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║ ┌─ Model Selection ────────────────────────────────────────────┐  ║
║ │                                                              │  ║
║ │  ☑ Neural Network (NN)          [Configure...] [Test]       │  ║
║ │  ☑ Logistic Regression (LR)     [Configure...] [Test]       │  ║
║ │  ☑ XGBoost (XGB)                [Configure...] [Test]       │  ║
║ │  ☑ Random Forest (RF)           [Configure...] [Test]       │  ║
║ │  ☑ CatBoost (CB)                [Configure...] [Test]       │  ║
║ │                                                              │  ║
║ │  [Select All]  [Select None]                                │  ║
║ │                                                              │  ║
║ └──────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║ ┌─ Training Options ───────────────────────────────────────────┐  ║
║ │                                                              │  ║
║ │ Ensemble Strategy:                                           │  ║
║ │  ○ Train individual models only                             │  ║
║ │  ○ Train + average ensemble                                 │  ║
║ │  ○ Train + stacked ensemble (meta-learner)                  │  ║
║ │                                                              │  ║
║ │ ☑ Enable early stopping (when supported)                    │  ║
║ │ ☑ Use class weighting for imbalanced targets                │  ║
║ │ ☑ Enable calibration (Platt scaling)                        │  ║
║ │                                                              │  ║
║ └──────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║ ┌─ Model Registry ─────────────────────────────────────────────┐  ║
║ │                                                              │  ║
║ │ Registry Update Policy:                                      │  ║
║ │  ○ Always update (overwrite champion)                       │  ║
║ │  ● Only if better (champion-challenger)                     │  ║
║ │  ○ Never update (evaluation only)                           │  ║
║ │  ○ Manual approval required                                 │  ║
║ │                                                              │  ║
║ │ Registry Path:                                               │  ║
║ │  [models/registry.json                      ] [Browse...]   │  ║
║ │                                                              │  ║
║ └──────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║                                                                    ║
║    [Reset to Defaults]     [Save as Preset...]     [OK] [Cancel]  ║
╚════════════════════════════════════════════════════════════════════╝
```

---

## 6. Neural Network Configuration Dialog

```
╔════════════════════════════════════════════════════════════════════╗
║ 🧠 Neural Network Configuration                               [×] ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║ ┌─ Network Architecture ───────────────────────────────────────┐  ║
║ │                                                              │  ║
║ │  Input Layer:    [AUTO] (determined by feature count)       │  ║
║ │                                                              │  ║
║ │  Hidden Layers:                                              │  ║
║ │    Layer 1:  [128   ] neurons   Activation: [ReLU ▼]        │  ║
║ │    Layer 2:  [64    ] neurons   Activation: [ReLU ▼]        │  ║
║ │    Layer 3:  [32    ] neurons   Activation: [ReLU ▼]        │  ║
║ │                                                              │  ║
║ │    [+ Add Layer]  [− Remove Layer]                           │  ║
║ │                                                              │  ║
║ │  Output Layer:   [AUTO] (determined by target type)         │  ║
║ │                                                              │  ║
║ │  ☐ Use batch normalization                                  │  ║
║ │  ☑ Use dropout (rate: [0.3    ])                            │  ║
║ │                                                              │  ║
║ └──────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║ ┌─ Training Hyperparameters ───────────────────────────────────┐  ║
║ │                                                              │  ║
║ │  Optimizer:        [Adam ▼]  (Adam, SGD, RMSprop, AdamW)    │  ║
║ │  Learning Rate:    [0.001   ]                               │  ║
║ │  Batch Size:       [32      ]                               │  ║
║ │  Max Epochs:       [500     ]                               │  ║
║ │                                                              │  ║
║ │  Early Stopping:                                             │  ║
║ │    ☑ Enable   Patience: [50  ]   Monitor: [val_loss ▼]      │  ║
║ │                                                              │  ║
║ │  Learning Rate Schedule:                                     │  ║
║ │    ○ None                                                    │  ║
║ │    ● ReduceLROnPlateau (factor: [0.5], patience: [10])      │  ║
║ │    ○ CosineAnnealing                                         │  ║
║ │    ○ StepLR                                                  │  ║
║ │                                                              │  ║
║ └──────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║ ┌─ Regularization ─────────────────────────────────────────────┐  ║
║ │                                                              │  ║
║ │  L2 Regularization (weight decay): [0.0001]                 │  ║
║ │  Dropout Rate:                     [0.3   ]                 │  ║
║ │                                                              │  ║
║ │  ☑ Use gradient clipping (max norm: [1.0  ])                │  ║
║ │                                                              │  ║
║ └──────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║ ┌─ Loss Function ──────────────────────────────────────────────┐  ║
║ │                                                              │  ║
║ │  ○ Auto (CrossEntropy for classification)                   │  ║
║ │  ○ Focal Loss (gamma: [2.0], alpha: [0.25])                │  ║
║ │  ○ Weighted CrossEntropy                                     │  ║
║ │                                                              │  ║
║ └──────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║ Estimated Parameters: ~45,000                                      ║
║                                                                    ║
║        [Test Configuration]  [Load Preset▼]  [OK]  [Cancel]       ║
╚════════════════════════════════════════════════════════════════════╝

Size: 600 × 700 px
```

---

## 7. Heatmap Visualization

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║ 🧬 Biomarkers Pipeline Tool - Heatmap View                   [−] [□] [×]      ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ [Pipeline Flow] [Model Comparison] [Visualizations] [Data] [Features] [...]  ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ ┌────────────────────────────────────────────────────────────────────────────┐ ║
║ │ [ROC Curves] [Confusion Matrix] [Heatmaps] [Feature Imp] [Training] [...]│ ║
║ └────────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║ ┌─ Heatmap Configuration ───────────────────────────────────────────────────┐ ║
║ │ Metric: [Balanced Accuracy ▼]  Model: [XGBoost ▼]  Colormap: [RdYlGn ▼]  │ ║
║ │ [☑ Show values] [☑ Annotate best] [☐ Transpose] [☐ Cluster rows/cols]    │ ║
║ └───────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║ ┌─ XGBoost Balanced Accuracy Heatmap ──────────────────────────────────────┐ ║
║ │                                                                            │ ║
║ │                   phase_-6  phase_0  phase_15  phase_30                   │ ║
║ │                                                                            │ ║
║ │ D30_response_3class    0.82     0.85     0.87      0.88     █████████     │ ║
║ │ D90_is_cr              0.88     0.90     0.91      0.92     ███████████   │ ║
║ │ crs_grade_ge2          0.72     0.74     0.76      0.77     ██████        │ ║
║ │ icans_grade_ge2        0.69     0.71     0.73      0.74     █████         │ ║
║ │ max_crs_grade          0.75     0.77     0.79      0.80     ███████       │ ║
║ │ icans_max_grade        0.71     0.73     0.75      0.76     ██████        │ ║
║ │ infection_100days      0.78     0.81     0.83      0.84     ████████      │ ║
║ │ relapse_or_progress    0.83     0.85     0.87      0.88     █████████     │ ║
║ │ survival_status_lfu    0.76     0.79     0.81      0.82     ███████       │ ║
║ │ cat_cause_death        0.70     0.72     0.74      0.75     ██████        │ ║
║ │ cart_response_6_mos    0.80     0.82     0.84      0.85     ████████      │ ║
║ │ cart_response_1_yr     0.81     0.83     0.85      0.86     ████████      │ ║
║ │ best_response          0.84     0.86     0.88      0.89     █████████     │ ║
║ │                                                                            │ ║
║ │           Color Scale: 0.60 ■■■■■■■■■■■■■■■■■■■■ 0.95                     │ ║
║ │                        Poor ◄──────────────────► Excellent                │ ║
║ └───────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║ ┌─ Insights ────────────────────────────────────────────────────────────────┐ ║
║ │ • Best overall performance: D90_is_cr @ phase_30 (BA = 0.92)              │ ║
║ │ • Weakest performance: icans_grade_ge2 @ phase_-6 (BA = 0.69)             │ ║
║ │ • Average improvement from phase_-6 to phase_30: +7.2%                     │ ║
║ │ • Most predictive phase: phase_30 (avg BA = 0.82)                         │ ║
║ └───────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║ [📊 Compare with Other Models] [💾 Export] [📄 Add to Report]                 ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ ✓ Ready                                                                       ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 8. Data Inspector View

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║ 🧬 Biomarkers Pipeline Tool - Data Inspector                [−] [□] [×]      ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ [...] [Data Inspector] [...]                                                 ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ ┌─ Dataset Overview ────────────────────────────────────────────────────────┐ ║
║ │ Rows: 252  │  Columns: 47 (base)  │  Derived: 19  │  Total: 66           │ ║
║ │ Completeness: 87.3%  │  Missing cells: 2,143 / 16,632                     │ ║
║ └───────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║ [Summary] [Data Preview] [Missing Values] [Distributions] [Correlations]     ║
║                                                                               ║
║ ┌─ Data Preview ────────────────────────────────────────────────────────────┐ ║
║ │ [Search: ____________] [Filter▼] [Columns▼]      Page 1 of 11  [◄] [►]  │ ║
║ ├───┬─────────┬──────────┬──────────┬──────────┬──────────┬──────────┬─────┤ ║
║ │ # │ Patient │ Age      │ Sex      │ Diagnosis│ Phase    │ D30_resp │ ... │ ║
║ ├───┼─────────┼──────────┼──────────┼──────────┼──────────┼──────────┼─────┤ ║
║ │ 0 │ PT_001  │ 56       │ M        │ DLBCL    │ -6       │ CR       │ ... │ ║
║ │ 1 │ PT_002  │ 42       │ F        │ ALL      │ -6       │ PR       │ ... │ ║
║ │ 2 │ PT_003  │ 61       │ M        │ DLBCL    │ -6       │ NR       │ ... │ ║
║ │ 3 │ PT_004  │ 38       │ F        │ MCL      │ -6       │ CR       │ ... │ ║
║ │ 4 │ PT_005  │ 55       │ M        │ FL       │ -6       │ PR       │ ... │ ║
║ │...│ ...     │ ...      │ ...      │ ...      │ ...      │ ...      │ ... │ ║
║ │ 24│ PT_025  │ 47       │ F        │ ALL      │ -6       │ InEval   │ ... │ ║
║ └───┴─────────┴──────────┴──────────┴──────────┴──────────┴──────────┴─────┘ ║
║                                                                               ║
║ ┌─ Column Statistics (Selected: Age) ──────────────────────────────────────┐ ║
║ │ Type: Numeric (continuous)                                                │ ║
║ │ ────────────────────────────────────────────────────────────────────────  │ ║
║ │ Count:  252                                                               │ ║
║ │ Mean:   48.3                                                              │ ║
║ │ Std:    12.7                                                              │ ║
║ │ Min:    18                                                                │ ║
║ │ 25%:    39                                                                │ ║
║ │ 50%:    47                                                                │ ║
║ │ 75%:    56                                                                │ ║
║ │ Max:    78                                                                │ ║
║ │ Missing: 0 (0.0%)                                                         │ ║
║ │ ────────────────────────────────────────────────────────────────────────  │ ║
║ │ Distribution:  [mini histogram visualization]                             │ ║
║ │   18-28: ▅▅▅▅ (12)                                                        │ ║
║ │   28-38: ▅▅▅▅▅▅▅▅ (28)                                                    │ ║
║ │   38-48: ▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅ (64)                                             │ ║
║ │   48-58: ▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅ (82)                                          │ ║
║ │   58-68: ▅▅▅▅▅▅▅▅▅▅▅ (48)                                                 │ ║
║ │   68-78: ▅▅▅▅ (18)                                                        │ ║
║ └───────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║ [📤 Export Data] [🔄 Reload] [⚙ Data Validation Report]                      ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ ✓ Data loaded                                                                 ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 9. Export/Report Generation Dialog

```
╔════════════════════════════════════════════════════════════════════╗
║ 📄 Generate Report                                            [×] ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║ ┌─ Report Type ────────────────────────────────────────────────┐  ║
║ │                                                              │  ║
║ │  ● Comprehensive Report (all results, full analysis)        │  ║
║ │  ○ Executive Summary (key findings only)                    │  ║
║ │  ○ Model Comparison Report (models vs metrics)              │  ║
║ │  ○ Phase Analysis Report (temporal progression)             │  ║
║ │  ○ Target-Specific Report (single target deep dive)         │  ║
║ │  ○ Custom Report (select components)                        │  ║
║ │                                                              │  ║
║ └──────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║ ┌─ Report Components ──────────────────────────────────────────┐  ║
║ │                                                              │  ║
║ │  ☑ Executive Summary                                         │  ║
║ │  ☑ Model Comparison Table                                    │  ║
║ │  ☑ ROC Curves (all phases, all targets)                     │  ║
║ │  ☑ Confusion Matrices (best models only)                    │  ║
║ │  ☑ Accuracy Heatmaps (all models)                           │  ║
║ │  ☑ Feature Importance Analysis                              │  ║
║ │  ☐ Feature Correlation Matrix                               │  ║
║ │  ☑ Training Convergence Plots (NN only)                     │  ║
║ │  ☑ Statistical Tests Results                                │  ║
║ │  ☑ Model Registry Summary                                   │  ║
║ │  ☑ Parameter Configuration                                  │  ║
║ │  ☐ Debug Logs (full)                                        │  ║
║ │  ☑ Debug Logs (errors & warnings only)                      │  ║
║ │                                                              │  ║
║ │  [Select All]  [Select None]  [Select Preset▼]              │  ║
║ │                                                              │  ║
║ └──────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║ ┌─ Output Formats ─────────────────────────────────────────────┐  ║
║ │                                                              │  ║
║ │  ☑ HTML (standalone with embedded images)                   │  ║
║ │  ☑ PDF (multi-page, formatted)                              │  ║
║ │  ☐ Markdown (.md with separate images)                      │  ║
║ │  ☑ Excel Workbook (tables in sheets)                        │  ║
║ │  ☑ CSV Files (all metrics tables)                           │  ║
║ │  ☑ JSON (structured data export)                            │  ║
║ │  ☑ PNG Images (all visualizations, 300dpi)                  │  ║
║ │                                                              │  ║
║ └──────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║ ┌─ Report Details ─────────────────────────────────────────────┐  ║
║ │                                                              │  ║
║ │  Report Title:                                               │  ║
║ │   [Biomarkers Pipeline Results - January 2026________]       │  ║
║ │                                                              │  ║
║ │  Author(s):                                                  │  ║
║ │   [Research Team______________________________]              │  ║
║ │                                                              │  ║
║ │  Description/Notes:                                          │  ║
║ │   ┌──────────────────────────────────────────────────────┐  │  ║
║ │   │ Complete pipeline evaluation including all phases,   │  │  ║
║ │   │ targets, and model families. Focus on balanced      │  │  ║
║ │   │ accuracy metric.                                     │  │  ║
║ │   └──────────────────────────────────────────────────────┘  │  ║
║ │                                                              │  ║
║ └──────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║ ┌─ Output Location ────────────────────────────────────────────┐  ║
║ │                                                              │  ║
║ │  Directory:                                                  │  ║
║ │   [exports/report_20260118_143022/          ] [Browse...]   │  ║
║ │                                                              │  ║
║ │  ☑ Create timestamped subdirectory                          │  ║
║ │  ☑ Open report after generation                             │  ║
║ │                                                              │  ║
║ └──────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║                                                                    ║
║           [Preview] [Save Template]  [Generate] [Cancel]          ║
╚════════════════════════════════════════════════════════════════════╝

Size: 700 × 800 px
```

---

## 10. Debug Console (Expanded View)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║ 🐛 Debug Console                                             [−] [□] [×]      ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ Level: [All ▼] [DEBUG] [INFO] [WARNING] [ERROR]     [Clear] [Export] [Find] ║
║ Search: [____________________________________________]  [🔍]  [☑ Regex]       ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ Time     │ Level   │ Source              │ Message                            ║
╟──────────┼─────────┼─────────────────────┼────────────────────────────────────╢
║ 14:30:15 │ INFO    │ DataLoader          │ Loading data from unified_clinic...║
║ 14:30:16 │ DEBUG   │ DataLoader          │ Read 252 rows, 47 columns          ║
║ 14:30:16 │ INFO    │ DataLoader          │ ✓ Data loaded successfully         ║
║ 14:30:16 │ INFO    │ TargetDerivation    │ Deriving targets...                ║
║ 14:30:17 │ DEBUG   │ TargetDerivation    │ Processing D30 evaluable gate      ║
║ 14:30:17 │ DEBUG   │ TargetDerivation    │ Found 238 evaluable D30 records    ║
║ 14:30:17 │ DEBUG   │ TargetDerivation    │ Creating D30_response_3class       ║
║ 14:30:17 │ WARNING │ TargetDerivation    │ 14 records marked as inevaluable   ║
║ 14:30:18 │ DEBUG   │ TargetDerivation    │ Processing D90 evaluable gate      ║
║ 14:30:18 │ DEBUG   │ TargetDerivation    │ Creating D90_is_cr binary target   ║
║ 14:30:18 │ INFO    │ TargetDerivation    │ ✓ Derived 19 targets successfully  ║
║ 14:30:18 │ INFO    │ FeatureEngineering  │ Preparing features for phase_-6... ║
║ 14:30:19 │ DEBUG   │ FeatureEngineering  │ Base features: 47                  ║
║ 14:30:19 │ DEBUG   │ FeatureEngineering  │ One-hot encoded features: 68       ║
║ 14:30:19 │ DEBUG   │ FeatureEngineering  │ Interaction features: 9            ║
║ 14:30:20 │ INFO    │ FeatureEngineering  │ ✓ Created 124 features (phase_-6)  ║
║ 14:30:20 │ INFO    │ FeatureEngineering  │ Preparing features for phase_0...  ║
║ 14:30:22 │ DEBUG   │ FeatureEngineering  │ Base features: 47                  ║
║ 14:30:22 │ DEBUG   │ FeatureEngineering  │ One-hot encoded features: 89       ║
║ 14:30:22 │ DEBUG   │ FeatureEngineering  │ Interaction features: 20           ║
║ 14:30:23 │ INFO    │ FeatureEngineering  │ ✓ Created 156 features (phase_0)   ║
║ 14:30:23 │ INFO    │ DataSplitter        │ Splitting data (70/15/15)...       ║
║ 14:30:23 │ DEBUG   │ DataSplitter        │ Train: 176 samples                 ║
║ 14:30:23 │ DEBUG   │ DataSplitter        │ Val: 44 samples                    ║
║ 14:30:23 │ DEBUG   │ DataSplitter        │ Test: 32 samples                   ║
║ 14:30:23 │ INFO    │ DataSplitter        │ ✓ Data split complete              ║
║ 14:30:23 │ INFO    │ ModelTrainer        │ Training NN for D30_response_3c... ║
║ 14:30:24 │ DEBUG   │ ModelTrainer.NN     │ Network: [124, 128, 64, 32, 3]     ║
║ 14:30:24 │ DEBUG   │ ModelTrainer.NN     │ Total parameters: 45,387           ║
║ 14:30:25 │ DEBUG   │ ModelTrainer.NN     │ Epoch 10/500: loss=0.8234, acc=... ║
║ 14:30:26 │ DEBUG   │ ModelTrainer.NN     │ Epoch 20/500: loss=0.7123, acc=... ║
║ 14:30:28 │ DEBUG   │ ModelTrainer.NN     │ Epoch 30/500: loss=0.6456, acc=... ║
║ ...      │ ...     │ ...                 │ ...                                ║
║ 14:32:14 │ INFO    │ ModelTrainer.NN     │ ✓ Training complete (epochs: 152)  ║
║ 14:32:14 │ INFO    │ ModelTrainer        │ Training LR for D30_response_3c... ║
║ 14:32:15 │ INFO    │ ModelTrainer.LR     │ ✓ Training complete (12.3s)        ║
║ 14:32:15 │ INFO    │ ModelTrainer        │ Training XGB for D30_response_3c...║
║ 14:32:27 │ INFO    │ ModelTrainer.XGB    │ ✓ Training complete (11.8s)        ║
║ 14:32:27 │ ERROR   │ ModelTrainer.CB     │ CatBoost not available             ║
║ 14:32:27 │ WARNING │ ModelTrainer        │ Skipping CatBoost (import error)   ║
║ 14:32:27 │ INFO    │ ModelTrainer        │ Training RF for D30_response_3c... ║
║ 14:32:39 │ INFO    │ ModelTrainer.RF     │ ✓ Training complete (11.9s)        ║
║ ...      │ ...     │ ...                 │ ...                                ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Features:
- Auto-scroll (toggleable)
- Color-coded levels (ERROR=red, WARNING=yellow, INFO=blue, DEBUG=gray)
- Clickable rows for detailed view
- Export to .log file
- Copy selected lines
- Timestamp filtering
```

---

## 11. Color Scheme & Styling

### Primary Colors
- **Primary Blue**: #0078D4 (Microsoft blue, for accents and primary actions)
- **Success Green**: #107C10 (for completed steps, positive metrics)
- **Warning Orange**: #FF8C00 (for warnings, medium performance)
- **Error Red**: #D13438 (for errors, poor performance)
- **Background**: #F3F3F3 (light gray, easy on eyes)
- **Panel Background**: #FFFFFF (pure white for content areas)
- **Text**: #212121 (near black for readability)
- **Border**: #D1D1D1 (subtle gray borders)

### Performance Color Scale (Heatmaps)
- **0.00-0.50**: #D13438 (Dark Red) - Poor
- **0.50-0.65**: #FF8C00 (Orange) - Fair
- **0.65-0.75**: #FFEB3B (Yellow) - Good
- **0.75-0.85**: #9CCC65 (Light Green) - Very Good
- **0.85-1.00**: #4CAF50 (Green) - Excellent

### Icons & Status
- Use emoji for quick visual recognition (✓ ✗ ⚙ ⚠ 🔵 etc.)
- Animated spinner for "running" state
- Checkmark bounce animation on completion
- Subtle pulse for active selection

### Typography
- **Headings**: Segoe UI Semibold, 14pt
- **Body**: Segoe UI Regular, 10pt
- **Code/Data**: Consolas, 9pt (monospace for alignment)
- **Buttons**: Segoe UI Semibold, 10pt

---

## 12. Keyboard Shortcuts

### Global
- `Ctrl+R`: Run all steps
- `Ctrl+Shift+R`: Run current step
- `Ctrl+Shift+S`: Stop execution
- `Ctrl+P`: Open parameters dialog
- `Ctrl+E`: Export current view
- `Ctrl+F`: Focus search/find
- `F5`: Refresh/reload
- `F11`: Toggle fullscreen
- `Esc`: Close dialogs/cancel operations

### Navigation
- `Ctrl+1` to `Ctrl+7`: Switch to tab 1-7
- `Ctrl+Tab`: Next tab
- `Ctrl+Shift+Tab`: Previous tab
- `Alt+←`: Previous view
- `Alt+→`: Next view

### Debug Console
- `Ctrl+L`: Clear console
- `Ctrl+Shift+L`: Export logs
- `Ctrl+Shift+F`: Find in logs
- `Ctrl+C`: Copy selected lines

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-18  
**Status**: Draft for Review
