"""Helpers for listing and labeling saved pipeline run pickles (results/runs, results/latest)."""

from __future__ import annotations

from pathlib import Path
from typing import List

from app.core.repo_paths import (
    LATEST_TRAINING_FILENAME,
    results_latest_dir,
    results_runs_dir,
)

TRAINING_RESULTS_PREFIX = "training_results_"


def format_saved_result_label(path: Path) -> str:
    """Build UI label from filename, e.g. training_results_YYYY-MM-DD_HH-MM-SS.pkl."""
    stem = path.stem
    if stem == "training_results" and path.parent.name == "latest":
        return "Latest snapshot (results/latest)"
    if not stem.startswith(TRAINING_RESULTS_PREFIX):
        return path.name
    suffix = stem[len(TRAINING_RESULTS_PREFIX) :]
    parts = suffix.replace("_", " ", 1).split(" ")
    if len(parts) == 2:
        return f"{parts[0]} {parts[1].replace('-', ':')}"
    return path.name


def iter_saved_run_paths_ordered() -> List[Path]:
    """Paths for Load dropdown: latest snapshot first, then runs/*.pkl by mtime desc, deduped."""
    runs_dir = results_runs_dir()
    latest_path = results_latest_dir() / LATEST_TRAINING_FILENAME
    if not runs_dir.exists() and not latest_path.exists():
        return []
    runs_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(
        runs_dir.glob("*.pkl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    extra: List[Path] = []
    if latest_path.exists():
        extra.append(latest_path)
    merged = extra + [p for p in files if p.resolve() != latest_path.resolve()]
    seen: set[str] = set()
    out: List[Path] = []
    for p in merged:
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out
