# Publication Readiness — Validation Summary

**Date:** 2026-02-26

## Blocks implemented

| Block | Deliverables | Status |
|-------|--------------|--------|
| **A** | Nested CV / 5-fold evaluation; bootstrap 95% CI; ANALYSIS_PLAN.md; ModelResult std/CI and get_metric_display | Done |
| **B** | Baselines in pipeline; Model vs baseline table (Validation Results); CSV: Majority_BA, Beat_Majority, Primary_Target | Done |
| **C** | Evaluable gate filter per target; PRIMARY_TARGETS; target_summary and Class balance table | Done |
| **D** | METHODS.md (class balancing, stratification, simpler-model preference) | Done |
| **E** | TRIPOD_CHECKLIST.md; LIMITATIONS.md; CIs in export and UI | Done |
| **F** | Framing as internal validation only; external validation needed (in LIMITATIONS.md) | Done |

## Tests

- **Publication readiness checks:** `biomarkers_app/tests/validate_publication_readiness.py` — 10 tests (documents exist, PRIMARY_TARGETS, ModelResult CV fields, gate filter, bootstrap helper). **All pass.**
- **Full test suite:** `pytest biomarkers_app/tests/` — **165 tests passed** (unit + integration), including Block A/B/C unit and integration tests and the two fixed feature-engineering tests.

## How to re-validate

From repo root or `biomarkers_app`:

```bash
# Publication readiness only
python -m pytest biomarkers_app/tests/validate_publication_readiness.py -v

# Full suite
python -m pytest biomarkers_app/tests/ -q
```

## Documents (dev_progress)

- ANALYSIS_PLAN.md — primary metric and primary targets; no post hoc selection
- BLOCK_A_PLAN.md — Block A plan and acceptance
- BLOCK_B_C_SUMMARY.md — Block B and C implementation summary
- METHODS.md — class balancing, stratification, model comparison, simpler-model preference
- TRIPOD_CHECKLIST.md — TRIPOD (and TRIPOD+AI) checklist filled
- LIMITATIONS.md — single center, n, no external validation, model vs baseline, framing
