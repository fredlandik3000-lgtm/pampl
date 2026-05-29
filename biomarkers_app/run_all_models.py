"""Run full pipeline: load, derive, engineer, train ALL models. Save and optionally run compare_runs.

Usage:
  python run_all_models.py           # nested CV (thorough, ~1-2 hr) - verbose progress
  python run_all_models.py --fast    # repeated holdout 2x (quicker, ~5-10 min)
"""
import sys
import pickle
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import os
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
from joblib import parallel_backend
parallel_backend("threading", n_jobs=1)

_last_progress_time = [0.0]  # mutable for closure


def log(level: str, tag: str, msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{ts} [{level}] {tag}: {msg}", flush=True)


def progress_cb(pct: float, msg: str) -> None:
    """Print progress periodically so terminal is never silent."""
    ts = datetime.now().strftime("%H:%M:%S")
    pct_str = f"{pct*100:.1f}%" if pct < 1.0 else "100%"
    print(f"  {ts} [{pct_str}] {msg}", flush=True)


def main():
    fast = "--fast" in sys.argv
    from app.pipeline.wrappers.data_loader_wrapper import DataLoaderWrapper
    from app.pipeline.wrappers.target_derivation_wrapper import TargetDerivationWrapper
    from app.pipeline.wrappers.feature_engineering_wrapper import FeatureEngineeringWrapper
    from app.pipeline.wrappers.model_training_wrapper import ModelTrainingWrapper
    from app.pipeline.types import PipelineConfig
    from app.core.config_manager import ConfigManager
    from app.core.repo_paths import copy_run_to_latest, repo_root, results_runs_dir

    REPO_ROOT = repo_root()
    RESULTS_DIR = results_runs_dir()
    ALL_PHASES = ["phase_-6", "phase_0", "phase_15", "phase_30"]

    config_mgr = ConfigManager()
    data_path = config_mgr.get("data.path", "data/unified_clinical_data.csv")
    if not Path(data_path).is_absolute():
        data_path = str(REPO_ROOT / data_path)

    config = PipelineConfig(
        data_path=data_path,
        phases=ALL_PHASES,
        targets=config_mgr.get("pipeline.targets", []),
        random_seed=config_mgr.get("pipeline.random_seed", 42),
        test_size=config_mgr.get("pipeline.test_size", 0.3),
        evaluation_mode=config_mgr.get("pipeline.evaluation_mode", "nested_cv"),
        use_feature_selection=config_mgr.get("pipeline.use_feature_selection", False),
    )

    print("=" * 60)
    mode = "repeated holdout 2x (fast)" if fast else "nested CV (5 outer x 3 inner)"
    print(f"RUNNING FULL PIPELINE (all models, {mode})")
    print("=" * 60)

    # 1. Load data
    t0 = datetime.now()
    log("INFO", "Pipeline", "[1/4] Loading data...")
    loader = DataLoaderWrapper(logger=log)
    load_result = loader.load_data(config.data_path)
    if not load_result.success:
        log("ERROR", "Pipeline", f"Data load failed: {load_result.errors}")
        return 1
    df = load_result.data
    log("INFO", "Pipeline", f"Loaded {len(df)} rows in {(datetime.now()-t0).total_seconds():.1f}s")

    # 2. Derive targets
    t0 = datetime.now()
    log("INFO", "Pipeline", "[2/4] Deriving targets...")
    target_derivation = TargetDerivationWrapper(logger=log)
    derive_result = target_derivation.derive_targets(df)
    if not derive_result.success:
        log("ERROR", "Pipeline", f"Target derivation failed: {derive_result.errors}")
        return 1
    derived_df = derive_result.data
    log("INFO", "Pipeline", f"Derived targets in {(datetime.now()-t0).total_seconds():.1f}s")

    # 3 & 4. Engineer + train all models for each phase
    fe_wrapper = FeatureEngineeringWrapper()
    trainer = ModelTrainingWrapper(logger=log)
    all_results = []
    all_roc, all_cm = [], []

    for i, phase in enumerate(ALL_PHASES):
        t_phase = datetime.now()
        log("INFO", "Pipeline", f"[3-4/4] Phase {i+1}/4: {phase} — engineering features...")
        fe_result = fe_wrapper.engineer_features(
            derived_df, phase=phase, fit_scalers=True,
            use_feature_selection=config.use_feature_selection,
            feature_selection_method=getattr(config, "feature_selection_method", "mutual_info"),
            feature_selection_top_k=getattr(config, "feature_selection_top_k", 50),
        )
        if not fe_result.success or fe_result.data is None:
            log("WARN", "Pipeline", f"Skip {phase} (no features)")
            continue

        n_feat = fe_result.metadata.get("feature_count", 0)
        log("INFO", "Pipeline", f"  {phase}: {n_feat} features, starting training...")

        if fast:
            train_result = trainer.train_models_repeated_holdout(
                fe_result.data,
                phase,
                fe_result.metadata,
                n_repeats=2,
                test_size=0.3,
                progress_callback=progress_cb,
                random_seed=config.random_seed,
                model_families_filter=None,
            )
        else:
            print(f"  Training all models (nested CV, 5 outer x 3 inner)...")
            train_result = trainer.train_models_nested_cv(
                fe_result.data,
                phase,
                fe_result.metadata,
                n_outer_splits=5,
                n_inner_splits=3,
                progress_callback=progress_cb,
                random_seed=config.random_seed,
                model_families_filter=None,  # all models
            )
        if train_result.success and train_result.data:
            all_results.extend(train_result.data)
            for tup in train_result.metadata.get("roc_curves", []):
                all_roc.append(tup)
            for tup in train_result.metadata.get("confusion_matrices", []):
                all_cm.append(tup)
            models = sorted(set(r.model_family for r in train_result.data))
            elapsed = (datetime.now() - t_phase).total_seconds()
            log("INFO", "Pipeline", f"  {phase} DONE in {elapsed:.0f}s: {len(train_result.data)} results, models: {models}")
        else:
            log("ERROR", "Pipeline", f"  Training failed: {getattr(train_result, 'errors', 'no data')}")

    if not all_results:
        print("\nNo results to save.")
        return 1

    # Save (format matching compare_runs: training_results_YYYY-MM-DD_HH-MM-SS.pkl)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_path = RESULTS_DIR / f"training_results_{stamp}.pkl"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    meta = {
        "phases_run": ALL_PHASES,
        "model_results_count": len(all_results),
        "roc_curves": all_roc,
        "confusion_matrices": all_cm,
    }
    with open(out_path, "wb") as f:
        pickle.dump({"data": all_results, "metadata": meta}, f)
    copy_run_to_latest(out_path)

    print("\n" + "=" * 60)
    print(f"Saved: {out_path}")
    print(f"  {len(all_results)} model results")
    print("=" * 60)

    # Quick summary by model
    from collections import defaultdict
    by_model = defaultdict(list)
    for r in all_results:
        if r.model_family not in ("Baseline-Majority", "Baseline-Random"):
            by_model[r.model_family].append(r.balanced_accuracy)
    print("\nMean balanced accuracy by model:")
    for mf in sorted(by_model.keys()):
        vals = by_model[mf]
        print(f"  {mf:12s} {sum(vals)/len(vals):.4f} (n={len(vals)})")

    # Run compare_runs if it exists
    compare_script = project_root / "compare_runs.py"
    if compare_script.exists():
        print("\n" + "=" * 60)
        print("COMPARISON WITH PREVIOUS RUNS")
        print("=" * 60)
        import subprocess
        subprocess.run([sys.executable, str(compare_script)], cwd=str(project_root))

    return 0


if __name__ == "__main__":
    sys.exit(main())
