# Agent orientation (PAMPL)

Read this first. **PAMPL** (Phase-Aware Machine Learning Pipeline) ships as the `biomarkers_app/` package. The **repository root** is the folder that contains `biomarkers_app/` (not `biomarkers_app` itself). Public URL: https://github.com/fredlandik3000-lgtm/pampl

## Canonical paths (use code, not guesses)

All repo-relative paths should go through **`biomarkers_app/app/core/repo_paths.py`**:

| Helper | Points to |
|--------|-----------|
| `repo_root()` | Git repo root (parent of `biomarkers_app/`) |
| `biomarkers_app_root()` | `biomarkers_app/` |
| `data_dir()` | `data/` |
| `results_runs_dir()` | `results/runs/` (timestamped `*.pkl` training dumps) |
| `results_latest_dir()` | `results/latest/` (copy `training_results.pkl` = most recent run) |
| `logs_dir()` | `logs/` |
| `catboost_info_dir()` | `catboost_info/` (CatBoost training metadata; gitignored) |
| `copy_run_to_latest(path)` | After saving a run pickle, mirror to `latest/training_results.pkl` |

**Config** (`default_params.json`): `logging.log_dir` and `data.path` are resolved from **repository root** in `main.py` / loaders—not from cwd.

**Registry** (champions per phase×target): `models/registry.json` at repo root.

## Layout (what lives where)

- **`biomarkers_app/`** — PyQt6 app: `app/`, `config/`, `tests/`, `docs/`, CLI scripts, `python -m biomarkers_app.cli`.
- **`results/`** — `runs/` (all saved runs), `latest/` (newest snapshot), `_archive/` (legacy bulk outputs). Details: `results/README.md`.
- **`logs/`** — `app_YYYYMMDD.log`, `error.log`, `crash.log` (not under `biomarkers_app/logs/`).
- **`data/`** — clinical CSV and preprocessing helpers.
- **`dev_progress/`** — roadmaps and status narratives.
- **`papers/`** — manuscript sources. To pull the **live Google Doc** (plain text + comments) into `papers/arxiv/`, from repo root: `python papers/google_drive_oauth/sync_google_manuscript.py` (details: `papers/google_drive_oauth/AGENT_FETCH.txt`). **ArXiv figure style** (canvas, typography, palette, naming): `papers/arxiv/figures/README.md`; Matplotlib helpers: `papers/arxiv/figures/figure_style.py`. **Manuscript figure renumbering:** any add/remove of a figure requires a **full-repo pass** (rename `figN_*` under `papers/arxiv/figures/`, update SVG metadata, update all markdown/script references, regenerate `manuscript_from_run.py` outputs, refresh the inventory in `papers/arxiv/figures/README.md`); see the **Renumbering rule** section there. **Captions:** do not put **“Figure N.”** inside the artwork or add in-image subtitle/legend paragraphs; use **short `alt`**, then a **substantial `Figure N.`** block below the embed (the sole figure legend). Prefer **left-to-right** flow in schematics; see **Layout** and **Captions** in `papers/arxiv/figures/README.md`.
- **`current_state/`**, **`versions/`** — research / alternate NN code.
- **`scripts/`** — ad-hoc utilities (e.g. dataset audit, phase reports).

## Documentation map

- **`biomarkers_app/docs/DOCUMENTATION.md`** — index of specs and design docs.
- **`biomarkers_app/HOW_TO_RUN.md`** — app launch, **batch CLI** (`python -m biomarkers_app.cli`), logs.
- **`results/README.md`** — results tree and archives.

Session-style notes were moved to **`biomarkers_app/docs/archive/session_notes/`** (historical).

## Visualizations tab (do not break without updating docs/tests)

The **Visualizations** UI depends on a **stable contract** between model training and the UI:

- **Signal:** `training_result_full` → `(List[ModelResult], metadata dict)` (see `main_window.py`, `pipeline_runner_widget.py`).
- **Curve plots** need metadata keys: `roc_curves`, `confusion_matrices`, `calibration_curves`, `pr_curves` (tuple shapes documented in **`biomarkers_app/docs/SPECIFICATIONS.md`** §**2.1.2b** and **Tab 3**).
- **Nested CV / 5-fold CV:** Figures are tied to **`PipelineConfig.cv_curve_source`** (`last_outer_fold` vs `refit_holdout`); training wrapper must keep emitting **`curve_source`** and **`curve_note`** when applicable.
- **Code paths:** `app/pipeline/wrappers/model_training_wrapper.py`, `app/ui/widgets/visualizations_widget.py`.
- **After changing training metadata or widget loading logic:** update **SPECIFICATIONS.md** §2.1.2b / Tab 3 and run **`pytest biomarkers_app/tests/unit/test_visualizations_widget.py`** (and relevant integration tests under `tests/integration/test_model_training.py`).

## Batch jobs (from repository root)

```text
python -m biomarkers_app.cli --help
python -m biomarkers_app.cli train-all
python -m biomarkers_app.cli train-all --fast
python -m biomarkers_app.cli train-lr
python -m biomarkers_app.cli quick-compare
python -m biomarkers_app.cli compare-runs
python -m biomarkers_app.cli pipeline-check
```

Equivalent scripts still live under `biomarkers_app/*.py`.

## Tests

```text
cd biomarkers_app
pytest tests/
```

## Google Doc editing format (mandatory)

When preparing manuscript edits for Google Doc insertion/review, present each change in this exact 3-block structure:

1) **Original paragraph** (current text)
2) **Proposed paragraph** (revised text)
3) **What changed and why** (brief rationale: content change + purpose)

Rules:
- Use paragraph-level chunks (not sentence-by-sentence unless requested).
- Keep one logical change per block to simplify review comments.
- Preserve numeric values, run IDs, and claims exactly unless intentionally updated from canonical sources.
- If a claim is changed, explicitly state the evidence source (e.g., latest `training_results.pkl`, section alignment, reviewer thread).
