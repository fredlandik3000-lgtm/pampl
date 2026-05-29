"""Run LR-only training (full pipeline: load data, engineer all phases, train LR). Optionally merge into existing results."""
import sys
import pickle
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Same as main.py
import os
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
from joblib import parallel_backend
parallel_backend("threading", n_jobs=1)

from app.pipeline.wrappers.data_loader_wrapper import DataLoaderWrapper
from app.pipeline.wrappers.target_derivation_wrapper import TargetDerivationWrapper
from app.pipeline.wrappers.feature_engineering_wrapper import FeatureEngineeringWrapper
from app.pipeline.wrappers.model_training_wrapper import ModelTrainingWrapper
from app.pipeline.types import PipelineStep, StepResult, PipelineConfig
from app.core.config_manager import ConfigManager
from app.core.repo_paths import copy_run_to_latest, repo_root, results_runs_dir

REPO_ROOT = repo_root()
RESULTS_DIR = results_runs_dir()
ALL_PHASES = ["phase_-6", "phase_0", "phase_15", "phase_30"]


def main(merge_into: str | None = None):
    """Run LR-only training. If merge_into is a path to a .pkl file, merge new LR into it and save."""
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

    # 1. Load data
    print("Loading data...")
    loader = DataLoaderWrapper()
    load_result = loader.load_data(config.data_path)
    if not load_result.success:
        print("Data load failed:", load_result.errors)
        return 1
    df = load_result.data

    # 2. Derive targets
    print("Deriving targets...")
    target_derivation = TargetDerivationWrapper()
    derive_result = target_derivation.derive_targets(df)
    if not derive_result.success:
        print("Target derivation failed:", derive_result.errors)
        return 1
    derived_df = derive_result.data

    # 3. Engineer + train LR for each phase
    fe_wrapper = FeatureEngineeringWrapper()
    trainer = ModelTrainingWrapper()
    all_results = []
    all_roc, all_cm = [], []

    for i, phase in enumerate(ALL_PHASES):
        print(f"[{i+1}/4] {phase}: engineering...")
        fe_result = fe_wrapper.engineer_features(
            derived_df, phase=phase, fit_scalers=True,
            use_feature_selection=config.use_feature_selection,
            feature_selection_method=getattr(config, "feature_selection_method", "mutual_info"),
            feature_selection_top_k=getattr(config, "feature_selection_top_k", 50),
        )
        if not fe_result.success or fe_result.data is None:
            print(f"  Skip {phase} (no features)")
            continue
        print(f"  {phase}: training LR...")
        train_result = trainer.train_models_nested_cv(
            fe_result.data,
            phase,
            fe_result.metadata,
            n_outer_splits=5,
            n_inner_splits=3,
            random_seed=config.random_seed,
            model_families_filter=["LR"],
        )
        if train_result.success and train_result.data:
            all_results.extend(train_result.data)
            for tup in train_result.metadata.get("roc_curves", []):
                all_roc.append(tup)
            for tup in train_result.metadata.get("confusion_matrices", []):
                all_cm.append(tup)

    if merge_into:
        path = Path(merge_into)
        if path.exists():
            print(f"\nMerging LR into {path.name}...")
            with open(path, "rb") as f:
                payload = pickle.load(f)
            loaded = payload.get("data", [])
            meta = payload.get("metadata", {})
            merged = [r for r in loaded if r.model_family != "LR"]
            merged.extend([r for r in all_results if r.model_family == "LR"])
            meta["roc_curves"] = [t for t in meta.get("roc_curves", []) if t[2] != "LR"]
            meta["roc_curves"].extend(all_roc)
            meta["confusion_matrices"] = [t for t in meta.get("confusion_matrices", []) if t[2] != "LR"]
            meta["confusion_matrices"].extend(all_cm)
            data_to_save = merged
            meta_to_save = meta
        else:
            print(f"Merge target not found: {merge_into}")
            merge_into = None

    if not merge_into:
        meta_to_save = {
            "phases_run": ALL_PHASES,
            "model_results_count": len(all_results),
            "roc_curves": all_roc,
            "confusion_matrices": all_cm,
        }
        data_to_save = all_results

    # Save
    from datetime import datetime
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    suffix = "_lr_merge" if merge_into else "_lr_only"
    out_path = RESULTS_DIR / f"training_results{suffix}_{stamp}.pkl"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        pickle.dump({"data": data_to_save, "metadata": meta_to_save}, f)
    copy_run_to_latest(out_path)
    print(f"\nSaved: {out_path}")
    print(f"  {len(data_to_save)} model results" + (" (merged)" if merge_into else " (LR only)"))
    return 0


if __name__ == "__main__":
    merge = sys.argv[1] if len(sys.argv) > 1 else None
    if merge and not Path(merge).is_absolute():
        merge = str(RESULTS_DIR / merge)
    sys.exit(main(merge_into=merge))
