## 6. Software availability and reproducibility







**Repository.** The PAMPL application and pipeline code live at **https://github.com/fredlandik3000-lgtm/pampl** (package `biomarkers_app/`; see repository root `AGENTS.md` for layout). A **persistent archive** (e.g. Zenodo) with a **citable DOI** will be linked at final preprint submission: **`TBD — Zenodo DOI`**.







**Commit / tag.** Manuscript tables and figures should be regenerated from a **named git tag** or commit hash recorded here at submission: **`TBD — insert tag or SHA after release`**. 







**Canonical results bundle for Supplement S1 and Figures 7–10.** Internal-validation numbers correspond to timestamped export **`results/runs/training_results_2026-04-05_12-18-35.pkl`**, mirrored to **`results/latest/training_results.pkl`** (same file contents). Training used **`evaluation_mode`: `nested_cv`** in `biomarkers_app/config/default_params.json` (**5 outer folds × 3 inner folds** where nested tuning applies; random seed **42**). To refresh manuscript artifacts after a new run, copy the new pickle to `results/latest/` (or use `app.core.repo_paths.copy_run_to_latest`) and run `python papers/arxiv/tools/manuscript_from_run.py --figures` from the repository root with `biomarkers_app` on `PYTHONPATH` (or run from `biomarkers_app/` via `python ../papers/arxiv/tools/manuscript_from_run.py --figures`). That command regenerates **`manuscript_sections/supplement_S01_table1_and_overview.md`** (Supplementary Table 1 + **Figure S1** scatter), **Figure 7** (cohort demographics from `data/unified_clinical_data.csv`), and **Figures 8–10** (performance bar charts from the pickle).







**License.** **MIT License** (recommended for reuse; confirm with institutional policy before release). If a different license is required, replace this sentence and the `LICENSE` file in the repository.







**Data.** The **unified clinical table** used for development is **not** publicly redistributed with the code; **access** depends on **center approval** and **ethics constraints**. Synthetic or public benchmark data may be added later for **demonstration** without changing the **software** description.







**Re-running analyses.** From the repository root, after configuring `biomarkers_app/config/default_params.json` and data paths, batch training may be invoked as documented in `biomarkers_app/HOW_TO_RUN.md` (e.g. `python -m biomarkers_app.cli train-all`). Export **Supplement S1** (table + **Figure S1**) from the saved pickle via `papers/arxiv/tools/manuscript_from_run.py --figures` so that **numbers match** the cited bundle.







