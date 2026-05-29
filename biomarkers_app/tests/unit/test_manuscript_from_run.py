"""Smoke tests for manuscript figure helpers (repo root papers/arxiv/tools)."""
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_manuscript_module():
    repo = Path(__file__).resolve().parents[3]
    path = repo / "papers" / "arxiv" / "tools" / "manuscript_from_run.py"
    spec = importlib.util.spec_from_file_location("manuscript_from_run", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, repo


def test_write_ba_figures_smoke(tmp_path):
    mod, repo = _load_manuscript_module()
    champs = [
        {
            "target": "t_bin_a",
            "label": "A",
            "task": "Bin",
            "phase": "phase_0",
            "model": "LR",
            "ba": 0.72,
            "ci_lo": 0.65,
            "ci_hi": 0.78,
            "maj": 0.5,
            "delta": 0.22,
            "n": 100,
            "auc": 0.7,
        },
        {
            "target": "t_bin_b",
            "label": "B",
            "task": "Bin",
            "phase": "phase_0",
            "model": "RF",
            "ba": 0.55,
            "ci_lo": 0.0,
            "ci_hi": 0.0,
            "maj": 0.5,
            "delta": 0.05,
            "n": 80,
            "auc": None,
        },
        {
            "target": "t_mc",
            "label": "C",
            "task": "MC",
            "phase": "phase_15",
            "model": "NN",
            "ba": 0.48,
            "ci_lo": 0.4,
            "ci_hi": 0.55,
            "maj": 0.33,
            "delta": 0.15,
            "n": 60,
            "auc": 0.55,
        },
        {
            "target": "t_ord",
            "label": "D",
            "task": "ORD",
            "phase": "phase_30",
            "model": "XGB",
            "ba": 0.41,
            "ci_lo": 0.35,
            "ci_hi": 0.48,
            "maj": 0.25,
            "delta": 0.16,
            "n": 40,
            "auc": None,
        },
    ]
    png, svg = mod.write_ba_figures(champs, tmp_path)
    assert "fig8" in png.name and png.exists() and svg.exists()
    assert png.stat().st_size > 500 and svg.stat().st_size > 500
    d1, d2 = mod.write_delta_figures(champs, tmp_path)
    assert "fig9" in d1.name and d1.exists()
    r1, r2 = mod.write_roc_figure(champs, tmp_path)
    assert "fig10" in r1.name and r1.exists()
    csv_path = repo / "data" / "unified_clinical_data.csv"
    if csv_path.is_file():
        c1, c2 = mod.write_cohort_figure(csv_path, tmp_path)
        assert "fig7" in c1.name and c1.exists()
