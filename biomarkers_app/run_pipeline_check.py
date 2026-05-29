"""Run app pipeline (load -> derive -> feature eng -> train) and print metrics for comparison."""
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_repo_root / "biomarkers_app"))

import pandas as pd
from app.core.repo_paths import data_dir, results_runs_dir
from app.pipeline.wrappers.target_derivation_wrapper import TargetDerivationWrapper
from app.pipeline.wrappers.feature_engineering_wrapper import FeatureEngineeringWrapper
from app.pipeline.wrappers.model_training_wrapper import ModelTrainingWrapper


def main():
    data_path = data_dir() / "unified_clinical_data.csv"
    if not data_path.exists():
        print("Data not found:", data_path)
        return
    df = pd.read_csv(data_path)
    print("Loaded rows:", len(df))

    # Derive targets (same as app)
    deriv = TargetDerivationWrapper()
    res = deriv.derive_targets(df)
    if not res.success or res.data is None:
        print("Derivation failed:", res.errors)
        return
    derived_df = res.data
    print("Derived targets; columns:", len(derived_df.columns))

    # Feature engineering phase_-6 (same as app)
    fe = FeatureEngineeringWrapper()
    fe_res = fe.engineer_features(derived_df, phase="phase_-6", fit_scalers=True)
    if not fe_res.success or fe_res.data is None:
        print("Feature engineering failed:", fe_res.errors)
        return
    print("Features for phase_-6:", fe_res.metadata.get("feature_count"))

    # Train (same as app)
    trainer = ModelTrainingWrapper()
    meta = fe_res.metadata
    train_res = trainer.train_models(
        fe_res.data, "phase_-6", meta,
        random_seed=42, test_size=0.3
    )
    if not train_res.success or not train_res.data:
        print("Training failed:", getattr(train_res, "errors", "no data"))
        return

    results = train_res.data
    print("\n--- App pipeline results (phase_-6) ---")
    print("Model results count:", len(results))
    # Summary: mean accuracy and BA
    accs = [r.accuracy for r in results]
    bas = [r.balanced_accuracy for r in results]
    print("Accuracy  (mean): %.4f (min=%.4f, max=%.4f)" % (sum(accs)/len(accs), min(accs), max(accs)))
    print("Bal.Acc   (mean): %.4f (min=%.4f, max=%.4f)" % (sum(bas)/len(bas), min(bas), max(bas)))
    # Per-target sample (first 5)
    print("\nSample (first 5): target, model, accuracy, balanced_accuracy")
    for r in results[:5]:
        print("  %s, %s, %.4f, %.4f" % (r.target, r.model_family, r.accuracy, r.balanced_accuracy))
    # Save short CSV for comparison
    runs_dir = results_runs_dir()
    runs_dir.mkdir(parents=True, exist_ok=True)
    out = runs_dir / "pipeline_check_results.csv"
    rows = [{"phase": r.phase, "target": r.target, "model_family": r.model_family,
             "accuracy": r.accuracy, "balanced_accuracy": r.balanced_accuracy} for r in results]
    pd.DataFrame(rows).to_csv(out, index=False)
    print("\nWrote:", out)

if __name__ == "__main__":
    main()
