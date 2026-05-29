"""Dispatch batch pipeline commands (same behavior as run_*.py scripts)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Ensure biomarkers_app/ is importable when launched as python -m biomarkers_app.cli
_APP = Path(__file__).resolve().parent.parent
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(
        prog="python -m biomarkers_app.cli",
        description="Batch pipeline commands (run from repository root: parent of biomarkers_app/).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_train_all = sub.add_parser("train-all", help="Full pipeline (nested CV or --fast holdout)")
    p_train_all.add_argument("--fast", action="store_true", help="Repeated holdout 2x instead of nested CV")

    p_train_lr = sub.add_parser("train-lr", help="LR-only training; optional merge pickle path")
    p_train_lr.add_argument("merge_into", nargs="?", default=None, help="Existing .pkl to merge LR into")

    sub.add_parser("quick-compare", help="Single holdout phase_-6, all models (fast)")

    sub.add_parser("compare-runs", help="Compare last N training runs (one per day)")

    sub.add_parser("pipeline-check", help="Phase_-6 train smoke check; writes CSV to results/runs/")

    args = p.parse_args(argv)

    if args.cmd == "train-all":
        sys.argv = ["run_all_models.py"] + (["--fast"] if args.fast else [])
        from run_all_models import main as run_main

        return run_main()

    if args.cmd == "train-lr":
        from app.core.repo_paths import results_runs_dir
        from run_lr_only import main as run_main

        merge = args.merge_into
        if merge and not Path(merge).is_absolute():
            merge = str(results_runs_dir() / merge)
        return run_main(merge_into=merge)

    if args.cmd == "quick-compare":
        from run_quick_compare import main as run_main

        return run_main()

    if args.cmd == "compare-runs":
        from compare_runs import main as run_main

        return run_main()

    if args.cmd == "pipeline-check":
        from run_pipeline_check import main as run_main

        return run_main()

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
