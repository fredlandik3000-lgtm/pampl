"""Compare training results across the last N successful runs (one per day)."""
import pickle
import re
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from app.core.repo_paths import results_runs_dir

RESULTS_DIR = results_runs_dir()
PREFIX = "training_results_"
PATTERN = re.compile(r"training_results_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})\.pkl")


def discover_runs() -> list[tuple[Path, str, datetime]]:
    """Discover all training result files, return (path, label, dt) sorted by dt desc."""
    runs = []
    for p in RESULTS_DIR.glob(f"{PREFIX}*.pkl"):
        m = PATTERN.match(p.name)
        if m:
            date_str, time_str = m.group(1), m.group(2)
            dt = datetime.strptime(f"{date_str}_{time_str}", "%Y-%m-%d_%H-%M-%S")
            label = f"{date_str} {time_str.replace('-', ':')}"
            runs.append((p, label, dt))
    runs.sort(key=lambda x: x[2], reverse=True)
    return runs


def one_per_day(runs: list[tuple[Path, str, datetime]], max_runs: int = 4) -> list[tuple[Path, str, datetime]]:
    """Keep only the most recent run per calendar day, up to max_runs."""
    seen_dates = set()
    selected = []
    for p, label, dt in runs:
        d = dt.date()
        if d in seen_dates:
            continue
        seen_dates.add(d)
        selected.append((p, label, dt))
        if len(selected) >= max_runs:
            break
    return selected


def load_results(path: Path) -> dict:
    with open(path, "rb") as f:
        return pickle.load(f)


def summarize(data: list) -> dict:
    """Summarize by model_family and target, excluding baselines."""
    by_model = defaultdict(list)
    for r in data:
        if r.model_family in ("Baseline-Majority", "Baseline-Random"):
            continue
        by_model[r.model_family].append(r)

    metrics = ["balanced_accuracy", "auc", "f1_score"]
    model_avg = {}
    for mf, rows in by_model.items():
        model_avg[mf] = {k: sum(getattr(r, k) for r in rows) / len(rows) for k in metrics}

    return {
        "n_models": len(data),
        "n_ml_models": sum(1 for r in data if r.model_family not in ("Baseline-Majority", "Baseline-Random")),
        "phases": sorted(set(r.phase for r in data)),
        "targets": sorted(set(r.target for r in data)),
        "model_families": sorted(set(r.model_family for r in data)),
        "by_model_avg": model_avg,
    }


def main():
    all_runs = discover_runs()
    runs = one_per_day(all_runs, max_runs=4)

    print("=" * 85)
    print("TRAINING RUNS COMPARISON (last 4 successful runs, one per day)")
    print("=" * 85)
    print(f"\nFound {len(all_runs)} total successful run(s); {len(runs)} unique day(s) selected.")
    if len(runs) < 4:
        print(f"(Only {len(runs)} distinct days have successful runs; showing all available.)")
    print()

    summaries = []
    for path, label, dt in runs:
        if not path.exists():
            print(f"  {label}: FILE NOT FOUND")
            continue
        payload = load_results(path)
        data = payload.get("data", [])
        s = summarize(data)
        summaries.append((label, s, data))

        print(f"### {label}")
        print(f"  Total model results: {s['n_models']}")
        print(f"  ML models (excl. baselines): {s['n_ml_models']}")
        print(f"  Phases: {s['phases']}")
        print(f"  Targets: {s['targets']}")
        print(f"  Model families: {s['model_families']}")
        print()
        print("  Mean by model family (bal_acc, auc, f1):")
        for mf in sorted(s["by_model_avg"].keys()):
            vals = s["by_model_avg"][mf]
            print(f"    {mf:20s}  bal_acc={vals['balanced_accuracy']:.4f}  auc={vals['auc']:.4f}  f1={vals['f1_score']:.4f}")
        print()

    # Model-family comparison across runs
    if len(summaries) >= 2:
        print("=" * 85)
        print("MODEL FAMILY COMPARISON ACROSS RUNS (mean balanced_accuracy)")
        print("=" * 85)
        all_mfs = sorted(set().union(*(s["by_model_avg"].keys() for _, s, _ in summaries)))
        header = "Model".ljust(14) + "".join(f" {label[:18]:>18}" for label, _, _ in summaries)
        print(header)
        for mf in all_mfs:
            row = mf.ljust(14)
            for _, s, _ in summaries:
                v = s["by_model_avg"].get(mf, {}).get("balanced_accuracy", 0)
                row += f" {v:>18.4f}"
            print(row)
        print()

    # Best/worst per run
    def top_bottom(rows, metric="balanced_accuracy", n=5):
        ml = [r for r in rows if r.model_family not in ("Baseline-Majority", "Baseline-Random")]
        sorted_r = sorted(ml, key=lambda r: getattr(r, metric), reverse=True)
        return sorted_r[:n], sorted_r[-n:]

    for label, s, data in summaries:
        ml = [r for r in data if r.model_family not in ("Baseline-Majority", "Baseline-Random")]
        if not ml:
            continue
        top, bot = top_bottom(data)
        print(f"### BEST/WORST — {label}")
        print("  Best 5 (balanced_accuracy):")
        for r in top:
            print(f"    {r.model_family:12s} {r.target:25s} {r.phase:10s} bal_acc={r.balanced_accuracy:.4f} auc={r.auc:.4f}")
        print("  Worst 5:")
        for r in bot:
            print(f"    {r.model_family:12s} {r.target:25s} {r.phase:10s} bal_acc={r.balanced_accuracy:.4f} auc={r.auc:.4f}")
        print()

    # If we have multiple runs from same day, show all-4 comparison
    if len(all_runs) > len(runs) and len(all_runs) <= 4:
        print("=" * 85)
        print("ALL RUNS (including same-day; for run-to-run variability)")
        print("=" * 85)
        all_summaries = []
        for path, label, dt in all_runs[:4]:
            if not path.exists():
                continue
            payload = load_results(path)
            data = payload.get("data", [])
            s = summarize(data)
            all_summaries.append((label, s))
        if all_summaries:
            all_mfs = sorted(set().union(*(s["by_model_avg"].keys() for _, s in all_summaries)))
            header = "Model".ljust(14) + "".join(f" {label[:16]:>16}" for label, _ in all_summaries)
            print(header)
            for mf in all_mfs:
                row = mf.ljust(14)
                for _, s in all_summaries:
                    v = s["by_model_avg"].get(mf, {}).get("balanced_accuracy", 0)
                    row += f" {v:>16.4f}"
                print(row)
        print()


if __name__ == "__main__":
    main()
