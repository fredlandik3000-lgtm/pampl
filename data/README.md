# Data (not included in this repository)

The unified clinical table used in the manuscript case study is **not** redistributed here. Access depends on **center approval** and **ethics constraints**.

## Expected layout

Place your approved CSV at:

```text
data/unified_clinical_data.csv
```

Or point the app to another path via **Browse** in the Pipeline Flow tab, or edit `biomarkers_app/config/default_params.json` (`data.path`).

## Preprocessing scripts (included)

Python helpers for building and standardizing the unified table (run locally when source exports are available):

| Script | Role |
|--------|------|
| `uni_main.py` | Main unify pipeline entry |
| `uni_load.py`, `uni_unify.py`, `uni_standardize.py` | Load, merge, standardize |
| `uni_standardize_helpers.py`, `uni_config.py` | Shared helpers and config |
| `unified_dataset_validation.py` | Post-unify validation |
| `derive_3class_responses.py` | Response label derivation |
| `CATEGORICAL_MAPPINGS.md` | Documented categorical mappings |

## Synthetic / demo data

A public demo dataset may be added in a future release. Until then, use your own CSV with compatible columns or run the unit/integration tests (they use temporary fixtures).
