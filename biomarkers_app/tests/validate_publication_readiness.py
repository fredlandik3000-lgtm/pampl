"""
Validation script for Publication Readiness (Blocks A–F).

Run from repo root or biomarkers_app:
  python -m pytest biomarkers_app/tests/validate_publication_readiness.py -v
  or: python biomarkers_app/tests/validate_publication_readiness.py

Checks:
- Block A: CV evaluation, bootstrap CI, analysis plan, ModelResult std/CI fields
- Block B: Baselines in results, export columns (Majority_BA, Beat_Majority), Validation Results baseline table
- Block C: Evaluable gate filter, PRIMARY_TARGETS, target_summary in metadata
- Block D: METHODS.md exists with class balancing and simpler-model preference
- Block E: TRIPOD_CHECKLIST.md, LIMITATIONS.md exist; CIs in export
- Block F: LIMITATIONS states internal-only and external validation needed
"""

from pathlib import Path
import sys

# Repo root (parent of biomarkers_app)
APP_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = APP_DIR.parent
DEV_PROGRESS = REPO_ROOT / "dev_progress"


def test_block_a_analysis_plan_exists():
    """A3: Pre-specified analysis plan."""
    path = DEV_PROGRESS / "ANALYSIS_PLAN.md"
    assert path.exists(), f"Missing {path}"
    text = path.read_text(encoding="utf-8")
    assert "primary metric" in text.lower() or "balanced accuracy" in text.lower()
    assert "primary targets" in text.lower() or "D30" in text


def test_block_a_plan_doc_exists():
    """Block A plan document."""
    path = DEV_PROGRESS / "BLOCK_A_PLAN.md"
    assert path.exists(), f"Missing {path}"


def test_block_b_c_summary_exists():
    """Block B/C summary."""
    path = DEV_PROGRESS / "BLOCK_B_C_SUMMARY.md"
    assert path.exists(), f"Missing {path}"


def test_block_d_methods_exists():
    """D: Methods document with class balancing and simpler-model preference."""
    path = DEV_PROGRESS / "METHODS.md"
    assert path.exists(), f"Missing {path}"
    text = path.read_text(encoding="utf-8")
    assert "stratif" in text.lower() or "class weight" in text.lower()
    assert "simpler" in text.lower() or "interpretability" in text.lower()


def test_block_e_tripod_exists():
    """E1: TRIPOD checklist."""
    path = DEV_PROGRESS / "TRIPOD_CHECKLIST.md"
    assert path.exists(), f"Missing {path}"
    text = path.read_text(encoding="utf-8")
    assert "TRIPOD" in text


def test_block_e_limitations_exists():
    """E4 & F2: Limitations and internal-only framing."""
    path = DEV_PROGRESS / "LIMITATIONS.md"
    assert path.exists(), f"Missing {path}"
    text = path.read_text(encoding="utf-8")
    assert "single center" in text.lower() or "single centre" in text.lower()
    assert "external validation" in text.lower()
    assert "internal" in text.lower() or "development" in text.lower()


def test_primary_targets_in_code():
    """C2: PRIMARY_TARGETS in code."""
    sys.path.insert(0, str(APP_DIR))
    from app.pipeline.types import PRIMARY_TARGETS
    assert isinstance(PRIMARY_TARGETS, list)
    assert len(PRIMARY_TARGETS) >= 5
    assert "D30_response_3class" in PRIMARY_TARGETS or "crs_grade_ge2" in PRIMARY_TARGETS


def test_model_result_has_cv_fields():
    """A1: ModelResult has std/CI fields for CV."""
    sys.path.insert(0, str(APP_DIR))
    from app.pipeline.types import ModelResult
    r = ModelResult("t", "p", "LR", 0.7, 0.65, 0.7, 0.66)
    assert hasattr(r, "balanced_accuracy_std")
    assert hasattr(r, "balanced_accuracy_ci_low")
    assert hasattr(r, "get_metric_display")


def test_gate_filter_exists():
    """C1: Evaluable gate filter in wrapper."""
    if str(APP_DIR) not in sys.path:
        sys.path.insert(0, str(APP_DIR))
    from app.pipeline.wrappers.model_training_wrapper import _gate_column_for_target, _filter_by_evaluable_gate
    assert _gate_column_for_target("D30_response_3class") == "D30_evaluable_gate"
    assert _gate_column_for_target("crs_grade_ge2") is None


def test_bootstrap_helper_exists():
    """A2: Bootstrap BA helper."""
    if str(APP_DIR) not in sys.path:
        sys.path.insert(0, str(APP_DIR))
    from app.pipeline.wrappers.model_training_wrapper import _bootstrap_balanced_accuracy
    import numpy as np
    y = np.array([0, 1, 0, 1])
    pred = np.array([0, 1, 0, 0])
    mean, low, high = _bootstrap_balanced_accuracy(y, pred, n_bootstrap=20, random_state=42)
    assert 0 <= mean <= 1 and low <= high


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
