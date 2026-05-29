"""Canonical paths relative to the repository root (parent of biomarkers_app/)."""

import shutil
from pathlib import Path

LATEST_TRAINING_FILENAME = "training_results.pkl"

_APP_DIR = Path(__file__).resolve().parent.parent.parent  # biomarkers_app/


def biomarkers_app_root() -> Path:
    return _APP_DIR


def repo_root() -> Path:
    """Git repository root: parent of biomarkers_app/."""
    return _APP_DIR.parent


def results_runs_dir() -> Path:
    """Timestamped pipeline pickles: training_results_*.pkl, quick_*.pkl, etc."""
    return repo_root() / "results" / "runs"


def results_latest_dir() -> Path:
    """Contains training_results.pkl (copy of most recent run for quick load)."""
    return repo_root() / "results" / "latest"


def logs_dir() -> Path:
    """Application logs (app_YYYYMMDD.log, error.log, crash.log)."""
    return repo_root() / "logs"


def catboost_info_dir() -> Path:
    """CatBoost training artifacts (single location; ignore in git)."""
    return repo_root() / "catboost_info"


def data_dir() -> Path:
    """Clinical and unified datasets (e.g. unified_clinical_data.csv)."""
    return repo_root() / "data"


def current_state_dir() -> Path:
    """Research scripts and analysis under current_state/."""
    return repo_root() / "current_state"


def versions_dir() -> Path:
    """Historical / alternate model version modules."""
    return repo_root() / "versions"


def copy_run_to_latest(timestamped_pkl: Path) -> Path:
    """Mirror a run pickle to results/latest/training_results.pkl (CLI + app)."""
    dest_dir = results_latest_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / LATEST_TRAINING_FILENAME
    shutil.copy2(timestamped_pkl, dest)
    return dest
