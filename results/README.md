# Results layout (repository root)

All machine-learning **run artifacts** for the Biomarkers app and CLI scripts use one tree under `results/`:

| Path | Purpose |
|------|---------|
| **`runs/`** | Timestamped pipeline pickles: `training_results_YYYY-MM-DD_HH-MM-SS.pkl`, `quick_phase-6_*.pkl`, `training_results_lr_merge_*.pkl`, and ad-hoc CSVs such as `pipeline_check_results.csv`. The app **Load** dropdown scans this folder. |
| **`latest/`** | `training_results.pkl` — copy of the **most recent** run (updated whenever the app or CLI saves a new run). Quick entry point for loading without picking a timestamp. |
| **`_archive/`** | Historical bulk outputs moved here during repo cleanup (e.g. legacy logistic regression tree exports, `results_nn_enhanced`, `results_rf`, old CatBoost metadata). Safe to delete locally if you do not need them. |

**Registry** (champion models per phase × target) remains at **`models/registry.json`** (repo root), not under `results/`.

**Logs** (app, errors, crash) are under **`logs/`** at the repository root (`app_YYYYMMDD.log`, `error.log`, `crash.log`).

**CatBoost** training metadata: prefer a single **`catboost_info/`** at the repository root; it is gitignored.

For command-line comparison of recent runs, use `python biomarkers_app/compare_runs.py` from the repo root (or `cwd` = `biomarkers_app` with the same `results/runs` path).
