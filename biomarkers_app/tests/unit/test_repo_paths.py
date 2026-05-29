"""Unit tests for repository path helpers."""

import pickle
from pathlib import Path
from app.core import repo_paths
from app.core.repo_paths import (
    LATEST_TRAINING_FILENAME,
    biomarkers_app_root,
    copy_run_to_latest,
    current_state_dir,
    data_dir,
    repo_root,
    results_latest_dir,
    results_runs_dir,
    versions_dir,
)


def test_repo_root_contains_biomarkers_app():
    root = repo_root()
    assert (root / "biomarkers_app").is_dir()
    assert biomarkers_app_root() == root / "biomarkers_app"


def test_results_layout():
    assert results_runs_dir().name == "runs"
    assert results_runs_dir().parent.name == "results"
    assert results_latest_dir().name == "latest"
    assert results_latest_dir().parent == results_runs_dir().parent


def test_data_versions_current_state():
    assert data_dir().name == "data"
    assert versions_dir().name == "versions"
    assert current_state_dir().name == "current_state"


def test_copy_run_to_latest_uses_tmp_path(monkeypatch, tmp_path: Path):
    runs = tmp_path / "results" / "runs"
    latest = tmp_path / "results" / "latest"
    runs.mkdir(parents=True)
    src = runs / "training_results_2099-01-01_12-00-00.pkl"
    payload = {"data": [1], "metadata": {}}
    with open(src, "wb") as f:
        pickle.dump(payload, f)

    monkeypatch.setattr(repo_paths, "results_runs_dir", lambda: runs)
    monkeypatch.setattr(repo_paths, "results_latest_dir", lambda: latest)

    dest = copy_run_to_latest(src)
    assert dest == latest / LATEST_TRAINING_FILENAME
    assert dest.exists()
    with open(dest, "rb") as f:
        assert pickle.load(f) == payload


def test_config_manager_has_repo_root():
    from app.core.config_manager import ConfigManager

    cm = ConfigManager()
    assert cm.repo_root == repo_root()
    assert cm.project_root == biomarkers_app_root()
