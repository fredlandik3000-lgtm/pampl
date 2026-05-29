# PAMPL — Phase-Aware Machine Learning Pipeline

**PAMPL** is a phase-aware machine learning pipeline and PyQt6 desktop application for CAR-T outcome prediction. It supports logistic regression, tree ensembles, and neural networks; derives labels with **evaluable gates**; compares models with **balanced accuracy (BA)** as the primary metric; and exposes uncertainty-aware diagnostics through an interactive interface.

This repository accompanies the manuscript preprint. It contains **software only** — not the clinical dataset.

## Repository layout

| Path | Purpose |
|------|---------|
| `biomarkers_app/` | Application, pipeline, CLI, tests |
| `data/` | Preprocessing scripts + `CATEGORICAL_MAPPINGS.md` (CSV **not** included — see `data/README.md`) |
| `papers/arxiv/tools/` | Regenerate manuscript figures from a local training pickle |
| `dev_progress/` | Methods, limitations, TRIPOD checklist (publication transparency) |
| `results/` | Run artifacts layout (`runs/`, `latest/`) — empty until you train locally |
| `models/registry.json` | Champion model metadata schema (metrics only; retrain locally for your data) |

See **`AGENTS.md`** for paths, CLI, and conventions.

## Requirements

- Python 3.11+
- Windows 10/11 (primary target; core pipeline may run on Linux/macOS with PyQt6 available)

```powershell
pip install -r requirements.txt
pip install -r biomarkers_app/requirements_app.txt
```

Optional: `xgboost`, `catboost` (enabled in default config when installed).

## Quick start

```powershell
# GUI
cd biomarkers_app
python main.py

# Batch training (from repository root, after placing data — see data/README.md)
python -m biomarkers_app.cli train-all
python -m biomarkers_app.cli --help
```

Details: **`biomarkers_app/HOW_TO_RUN.md`**.

## Manuscript figure regeneration

After training and saving `results/latest/training_results.pkl` (and with your local clinical CSV for cohort demographics):

```powershell
python papers/arxiv/tools/manuscript_from_run.py --figures
```

Figure styling: `papers/arxiv/figures/figure_style.py`.

## Tests

```powershell
cd biomarkers_app
pytest tests/ -q --ignore=tests/validate_publication_readiness.py
```

(`validate_publication_readiness.py` expects full `dev_progress/` paths — included here for transparency.)

## Data and ethics

Clinical data are **not** public in this release. See **`data/README.md`** and **`dev_progress/LIMITATIONS.md`**.

## License

MIT — see **`LICENSE`**.

## Citation

If you use this software, cite the accompanying manuscript (preprint DOI **TBD**).

Repository: https://github.com/fredlandik3000-lgtm/pampl
