# How to Run the Biomarkers Pipeline Tool

## Quick Start

From the repo root or from `biomarkers_app`:

```powershell
cd biomarkers_app
python main.py
```

**Note:** The app uses **PyQt6**. If you see import errors, install: `pip install PyQt6`. Your tests ran with PySide6; the app entry point is PyQt6.

**Data:** The app looks for `data/unified_clinical_data.csv` at the **repository root** by default (see `data/README.md` — clinical CSV is not shipped with this repo). Use **Browse** in the Pipeline Flow tab to pick another CSV if needed.

**Logs:** Written under the **repository root** `logs/` (`app_YYYYMMDD.log`, `error.log`, `crash.log`), not under `biomarkers_app/logs/`.

**Saved runs:** Pipeline pickles are stored under **`../results/runs/`** (timestamped `.pkl` files). A copy of the latest run is always at **`../results/latest/training_results.pkl`**. Use the **Load** dropdown on the Pipeline Flow tab to reload a previous run into Model Comparison / Visualizations.

## Batch CLI (unified)

From the **repository root** (the folder that contains `biomarkers_app/`):

```powershell
# repository root (parent of biomarkers_app/)
python -m biomarkers_app.cli --help
python -m biomarkers_app.cli train-all
python -m biomarkers_app.cli train-all --fast
python -m biomarkers_app.cli train-lr
python -m biomarkers_app.cli quick-compare
python -m biomarkers_app.cli compare-runs
python -m biomarkers_app.cli pipeline-check
```

The scripts `run_all_models.py`, `run_lr_only.py`, `run_quick_compare.py`, `compare_runs.py`, and `run_pipeline_check.py` in `biomarkers_app/` are unchanged and call the same code paths.

## What We've Implemented

### ✅ **Logging System**

**3 Types of Logs:**

1. **Console Output** - Shows in terminal (INFO level and above)
2. **Application Log** - `logs/app_YYYYMMDD.log` (repository root) - All events
3. **Error Log** - `logs/error.log` - Only errors
4. **Crash Log** - `logs/crash.log` - Uncaught exceptions

### ✅ **Exception Handling**

- **Global Exception Hook** - Catches ALL uncaught exceptions
- **Try-Catch in Data Inspector** - Prevents UI crashes
- **Detailed Stack Traces** - Full traceback in crash.log

## If App Crashes

###  Check the logs in this order:

1. **Terminal Output** - Shows immediate crash info
2. **`logs/crash.log`** (under the repository root) - Full stack trace of uncaught exceptions
3. **`logs/error.log`** - Logged errors
4. **`logs/app_YYYYMMDD.log`** - Complete activity log

### Example crash.log format:
```
================================================================================
Crash at 2026-01-18 17:20:00
================================================================================
Traceback (most recent call last):
  File "...", line X, in function_name
    problematic_code()
TypeError: some error message
================================================================================
```

## Testing the App

### Full pipeline (Load → Engineer → Train → Visualize)
1. Run `python main.py` (from `biomarkers_app`).
2. Choose **Research & Development** (or Academic Review) and launch.
3. **Pipeline Flow** tab:
   - Click **Load Data**. Wait until progress completes and status shows "[OK] Data loaded successfully".
   - Choose **Phase:** e.g. `phase_-6`.
   - Click **Run Feature Engineering**. Wait until "Feature engineering completed" and **Run Model Training** is enabled.
   - Click **Run Model Training**. Wait for "Training complete: N model results" (can take 1–2 minutes).
4. **Model Comparison** tab: Table should show targets × phases × models with metrics (accuracy, BA, AUC, F1). Change phase/target/model filters and metric dropdown.
5. **Visualizations** tab:
   - **View:** ROC Curve → pick a "Target / Model" → ROC plot should appear.
   - **View:** Confusion Matrix → pick a series → confusion heatmap should appear.
   - **View:** Performance Heatmap → heatmap of balanced accuracy (targets × models) should appear.
6. **Data Inspector**: After load, check Overview / Column Details / Derived Columns.
7. **Feature Analysis**: After feature engineering, check Feature Summary and other sub-tabs.

### Load Data only
1. Run `python main.py`
2. Go to "Pipeline Flow" tab
3. Click "Load Data" (or Browse to select a CSV)
4. Data loads → Data Inspector tab populates

### If it crashes during data loading:
```bash
# Check crash log
cat logs/crash.log

# Or on Windows
type logs\crash.log

# Check last 50 lines of app log
Get-Content logs\app_20260118.log -Tail 50
```

## Current Implementation Status

### ✅ **Phase 1: Foundation** (Complete)
- Configuration system
- Logging system
- Main window with tabs
- Mode selection (Clinical, Research, Academic Review)

### ✅ **Phase 2: Pipeline Integration** (Complete)
- Data loading with progress bar
- Browse button for file selection
- Background thread execution
- Cancellation support
- **Data Inspector tab** with 4 sub-tabs:
  - Data View (table with missing value highlighting)
  - Column Info (detailed column analysis)
  - Statistics (numeric stats + correlations)
  - Missing Data (comprehensive analysis)

### 📝 **Placeholders** (Not Yet Implemented):
- Model Comparison
- Visualizations
- Feature Analysis
- Validation Results  
- Registry Viewer

## Known Issues

### Issue: App crashes when loading data
**Status:** Investigating  
**Logs Added:** 
- ✅ Global exception hook
- ✅ Try-catch in data inspector
- ✅ crash.log file created automatically

**Next Steps:** Run app, try to load data, check `logs/crash.log` for full error

## Log File Locations

```
biomarkers_app/
├── logs/
│   ├── app_20260118.log    ← All application events
│   ├── error.log            ← Errors only
│   └── crash.log            ← Uncaught exceptions (NEW!)
```

## Debugging Tips

1. **Always check crash.log first** - it has the most detailed info
2. **Look for the last logged message** in app_20260118.log - shows where it stopped
3. **Run in foreground** (not background) to see print statements
4. **Check terminal output** for immediate errors

## Development Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/integration/test_pipeline_basic.py -v

# Run app in foreground (see all output)
python main.py

# Check git status
git status

# View recent commits
git log --oneline -10
```

## Need Help?

If the app crashes:
1. Copy the contents of `logs/crash.log`
2. Copy the last 50 lines of `logs/app_20260118.log`
3. Share the error message from terminal
4. Describe what you clicked when it crashed
