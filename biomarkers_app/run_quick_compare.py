"""Quick run: single holdout, phase_-6 only. For fast comparison of model improvements."""
import sys
import pickle
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import os
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
from joblib import parallel_backend
parallel_backend("threading", n_jobs=1)


def main():
    from app.pipeline.wrappers.data_loader_wrapper import DataLoaderWrapper
    from app.pipeline.wrappers.target_derivation_wrapper import TargetDerivationWrapper
    from app.pipeline.wrappers.feature_engineering_wrapper import FeatureEngineeringWrapper
    from app.pipeline.wrappers.model_training_wrapper import ModelTrainingWrapper
    from app.core.config_manager import ConfigManager
    from app.core.repo_paths import copy_run_to_latest, repo_root, results_runs_dir

    config_mgr = ConfigManager()
    data_path = config_mgr.get("data.path", "data/unified_clinical_data.csv")
    if not Path(data_path).is_absolute():
        data_path = str(repo_root() / data_path)

    print("Quick run: phase_-6, single holdout, all models...")
    loader = DataLoaderWrapper()
    load_result = loader.load_data(data_path)
    if not load_result.success:
        print("Load failed:", load_result.errors)
        return 1

    deriv = TargetDerivationWrapper()
    derive_result = deriv.derive_targets(load_result.data)
    if not derive_result.success:
        print("Derive failed:", derive_result.errors)
        return 1

    fe = FeatureEngineeringWrapper()
    fe_result = fe.engineer_features(derive_result.data, phase="phase_-6", fit_scalers=True)
    if not fe_result.success:
        print("Feature eng failed:", fe_result.errors)
        return 1

    def log(lvl, tag, msg): print(f"  [{tag}] {msg}")

    trainer = ModelTrainingWrapper(logger=log)
    train_result = trainer.train_models(
        fe_result.data, "phase_-6", fe_result.metadata,
        random_seed=42, test_size=0.3
    )

    if not train_result.success or not train_result.data:
        print("Training failed")
        return 1

    # Summary
    from collections import defaultdict
    by_model = defaultdict(list)
    for r in train_result.data:
        if r.model_family not in ("Baseline-Majority", "Baseline-Random"):
            by_model[r.model_family].append(r.balanced_accuracy)

    print("\n" + "=" * 50)
    print("Phase -6 single holdout - Mean balanced accuracy:")
    print("=" * 50)
    for mf in sorted(by_model.keys()):
        vals = by_model[mf]
        print(f"  {mf:15s} {sum(vals)/len(vals):.4f}")

    # Save for compare
    runs = results_runs_dir()
    runs.mkdir(parents=True, exist_ok=True)
    out = runs / f"quick_phase-6_{__import__('datetime').datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pkl"
    with open(out, "wb") as f:
        pickle.dump({"data": train_result.data, "metadata": {"phase": "phase_-6"}}, f)
    copy_run_to_latest(out)
    print(f"\nSaved: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
