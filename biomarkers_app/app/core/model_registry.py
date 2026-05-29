"""Model registry: champion per (phase, target) from training results."""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from app.pipeline.types import ModelResult


def champions_from_results(
    results: List[ModelResult],
    metric: str = "balanced_accuracy",
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Build champion map from list of ModelResult.
    Structure: { phase: { target: { "model_family", "metric", "value", "timestamp" } } }
    Champion = best model per (phase, target) by chosen metric.
    """
    from datetime import datetime
    ts = datetime.now().isoformat(timespec="seconds")

    by_phase_target: Dict[str, Dict[str, List[ModelResult]]] = {}
    for r in results:
        if not isinstance(r, ModelResult):
            continue
        by_phase_target.setdefault(r.phase, {}).setdefault(r.target, []).append(r)

    registry: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for phase, targets in by_phase_target.items():
        registry[phase] = {}
        for target, model_results in targets.items():
            if not model_results:
                continue
            best = max(
                model_results,
                key=lambda m: m.get_metric(metric),
            )
            registry[phase][target] = {
                "model_family": best.model_family,
                "metric": metric,
                "value": round(best.get_metric(metric), 4),
                "accuracy": round(best.accuracy, 4),
                "auc": round(best.auc, 4),
                "f1_score": round(best.f1_score, 4),
                "timestamp": ts,
            }
    return registry


def load_registry(path: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Load registry from JSON file. Returns empty dict on missing/invalid file."""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        return {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_registry(path: str, registry: Dict[str, Dict[str, Dict[str, Any]]]) -> None:
    """Save registry to JSON file. Creates parent dirs if needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)


def merge_registry(
    existing: Dict[str, Dict[str, Dict[str, Any]]],
    new_champions: Dict[str, Dict[str, Dict[str, Any]]],
    metric: str = "balanced_accuracy",
    only_if_better: bool = False,
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Merge new champions into existing registry.
    If only_if_better=True, replace only when new value is greater than existing.
    """
    merged = dict(existing)
    for phase, targets in new_champions.items():
        merged.setdefault(phase, {})
        for target, entry in targets.items():
            current = merged[phase].get(target)
            if only_if_better and current is not None:
                try:
                    if entry.get("value", 0) <= current.get("value", 0):
                        continue
                except (TypeError, ValueError):
                    pass
            merged[phase][target] = dict(entry)
    return merged
