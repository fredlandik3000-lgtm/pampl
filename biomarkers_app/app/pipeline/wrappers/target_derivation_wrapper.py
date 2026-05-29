"""Target Derivation Wrapper for deriving response targets from clinical data"""

import time
import pandas as pd
import numpy as np
import sys
from typing import Optional, List

from app.core.repo_paths import repo_root

_project_root = repo_root()
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from app.pipeline.types import (
    ProgressCallback, LogCallback, CancellationToken, StepResult
)


class TargetDerivationWrapper:
    """Wrapper for deriving target variables from raw clinical data"""
    
    def __init__(self, logger: Optional[LogCallback] = None):
        """
        Initialize target derivation wrapper.
        
        Args:
            logger: Optional logging callback
        """
        self.logger = logger or self._default_logger
    
    def _default_logger(self, level: str, source: str, message: str) -> None:
        """Default logger that prints to console"""
        print(f"[{level}] {source}: {message}")
    
    def derive_targets(
        self,
        df: pd.DataFrame,
        progress_callback: Optional[ProgressCallback] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> StepResult:
        """
        Derive target variables from raw clinical data.
        
        Derives:
        - Evaluability gates (D30, D90, M6, Y1, BEST)
        - Response targets (3-class and binary CR)
        - Cleans survival status
        
        Args:
            df: Input DataFrame with raw clinical data
            progress_callback: Progress reporting function
            cancellation_token: Cancellation check
        
        Returns:
            StepResult with derived DataFrame and metadata
        """
        start_time = time.time()
        errors: List[str] = []
        warnings: List[str] = []
        
        try:
            # Check cancellation
            if cancellation_token and cancellation_token.is_cancelled():
                return StepResult(
                    success=False,
                    data=None,
                    metadata={},
                    errors=["Operation cancelled by user"]
                )
            
            if progress_callback:
                progress_callback(0.0, "Starting target derivation...")
            
            self.logger("INFO", "TargetDerivation", "Starting target derivation")
            
            # Make a copy to avoid modifying original
            df_derived = df.copy()
            original_cols = set(df.columns)
            
            # Import and call existing derivation function
            if progress_callback:
                progress_callback(20.0, "Cleaning survival status...")
            
            from current_state.pipeline import derive_targets as derive_targets_func
            
            self.logger("INFO", "TargetDerivation", "Calling derive_targets function")
            df_derived = derive_targets_func(df_derived)
            
            # Check cancellation after derivation
            if cancellation_token and cancellation_token.is_cancelled():
                return StepResult(
                    success=False,
                    data=None,
                    metadata={},
                    errors=["Operation cancelled after derivation"]
                )
            
            if progress_callback:
                progress_callback(80.0, "Analyzing derived targets...")
            
            # Identify new columns
            new_cols = set(df_derived.columns) - original_cols
            gates = sorted([c for c in new_cols if c.endswith("_evaluable_gate")])
            targets = sorted([c for c in new_cols if not c.endswith("_evaluable_gate")])
            
            self.logger("INFO", "TargetDerivation", f"Created {len(gates)} evaluability gates")
            self.logger("INFO", "TargetDerivation", f"Created {len(targets)} target variables")
            
            # Analyze evaluability for each gate
            evaluability_stats = {}
            for gate in gates:
                if gate in df_derived.columns:
                    evaluable_count = (df_derived[gate] == 1).sum()
                    inevaluable_count = (df_derived[gate] == 0).sum()
                    total = len(df_derived)
                    eval_pct = (evaluable_count / total * 100) if total > 0 else 0
                    
                    evaluability_stats[gate] = {
                        "evaluable": int(evaluable_count),
                        "inevaluable": int(inevaluable_count),
                        "evaluable_pct": float(eval_pct)
                    }
                    
                    if inevaluable_count > 0:
                        ineval_pct = (inevaluable_count / total * 100)
                        warnings.append(
                            f"{gate}: {inevaluable_count} ({ineval_pct:.1f}%) inevaluable records"
                        )
                        self.logger(
                            "WARNING",
                            "TargetDerivation",
                            f"{gate}: {inevaluable_count} inevaluable"
                        )
            
            # Calculate completeness for target columns
            target_completeness = {}
            for target in targets:
                if target in df_derived.columns:
                    non_null = df_derived[target].notna().sum()
                    total = len(df_derived)
                    completeness_pct = (non_null / total * 100) if total > 0 else 0
                    target_completeness[target] = float(completeness_pct)
            
            derive_time = time.time() - start_time
            
            # Calculate standard data statistics for UI display
            # Use ORIGINAL columns only (before derivation) for completeness calculation
            df_original = df_derived[list(original_cols)]
            rows = len(df_derived)
            columns_original = len(df_original.columns)
            columns_total = len(df_derived.columns)
            total_values = rows * columns_original  # Only original columns
            missing_values = df_original.isna().sum().sum()  # Only original columns
            present_values = total_values - missing_values
            completeness_pct = (present_values / total_values * 100) if total_values > 0 else 0
            
            metadata = {
                # Standard data statistics (for UI display - original data only)
                "rows": rows,
                "columns": columns_total,  # Total columns for display
                "columns_original": columns_original,  # Original columns
                "columns_derived": len(new_cols),  # Derived columns
                "total_values": total_values,
                "missing_values": int(missing_values),
                "present_values": present_values,
                "completeness": float(completeness_pct),  # Completeness of original data
                "load_time": derive_time,  # Total pipeline time
                
                # Target-specific metadata
                "targets_created": targets,
                "gates_created": gates,
                "evaluability_stats": evaluability_stats,
                "target_completeness": target_completeness,
                "total_columns_added": len(new_cols),
                "derive_time_sec": derive_time
            }
            
            if progress_callback:
                progress_callback(
                    100.0,
                    f"Derived {len(targets)} targets, {len(gates)} gates"
                )
            
            self.logger(
                "INFO",
                "TargetDerivation",
                f"[OK] Target derivation completed in {derive_time:.2f}s"
            )
            
            return StepResult(
                success=True,
                data=df_derived,
                metadata=metadata,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            error_msg = f"Target derivation failed: {str(e)}"
            self.logger("ERROR", "TargetDerivation", error_msg)
            
            import traceback
            traceback.print_exc()
            
            return StepResult(
                success=False,
                data=None,
                metadata={"derive_time_sec": time.time() - start_time},
                errors=[error_msg]
            )
