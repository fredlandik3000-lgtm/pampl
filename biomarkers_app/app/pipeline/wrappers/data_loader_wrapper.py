"""Data Loader Wrapper for loading and validating clinical data"""

import time
import pandas as pd
from pathlib import Path
from typing import Optional, List, Set

from app.pipeline.types import (
    ProgressCallback, LogCallback, CancellationToken, StepResult
)


class DataLoaderWrapper:
    """Wrapper for data loading with validation and progress tracking"""
    
    # No required columns - accept any CSV structure
    REQUIRED_COLUMNS: Set[str] = set()
    
    def __init__(self, logger: Optional[LogCallback] = None):
        """
        Initialize data loader wrapper.
        
        Args:
            logger: Optional logging callback
        """
        self.logger = logger or self._default_logger
    
    def _default_logger(self, level: str, source: str, message: str) -> None:
        """Default logger that prints to console"""
        print(f"[{level}] {source}: {message}")
    
    def load_data(
        self,
        path: str,
        progress_callback: Optional[ProgressCallback] = None,
        cancellation_token: Optional[CancellationToken] = None,
        validate: bool = True
    ) -> StepResult:
        """
        Load clinical data from CSV.
        
        Args:
            path: Path to unified_clinical_data.csv
            progress_callback: Progress reporting function
            cancellation_token: Cancellation check
            validate: Whether to validate schema
        
        Returns:
            StepResult with loaded DataFrame and metadata
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
            
            # Report progress
            if progress_callback:
                progress_callback(0.0, "Checking file path...")
            
            # Validate path exists
            file_path = Path(path)
            if not file_path.exists():
                error_msg = f"Data file not found: {path}"
                self.logger("ERROR", "DataLoader", error_msg)
                return StepResult(
                    success=False,
                    data=None,
                    metadata={},
                    errors=[error_msg]
                )
            
            # Report progress
            if progress_callback:
                progress_callback(10.0, "Reading CSV file...")
            
            # Load data
            self.logger("INFO", "DataLoader", f"Loading data from {path}")
            df = pd.read_csv(path)
            
            # Check cancellation after loading
            if cancellation_token and cancellation_token.is_cancelled():
                return StepResult(
                    success=False,
                    data=None,
                    metadata={},
                    errors=["Operation cancelled after loading"]
                )
            
            if progress_callback:
                progress_callback(50.0, "Validating data schema...")
            
            # Validate schema if requested
            if validate:
                validation_errors, validation_warnings = self._validate_schema(df)
                errors.extend(validation_errors)
                warnings.extend(validation_warnings)
                
                if validation_errors:
                    return StepResult(
                        success=False,
                        data=None,
                        metadata={},
                        errors=errors,
                        warnings=warnings
                    )
            
            if progress_callback:
                progress_callback(80.0, "Analyzing data quality...")
            
            # Calculate metadata
            rows, cols = df.shape
            
            # Calculate completeness (% of non-null values)
            total_values = rows * cols
            missing_values = df.isna().sum().sum()
            completeness = 1.0 - (missing_values / total_values) if total_values > 0 else 0.0
            
            # Get column types
            column_types = df.dtypes.value_counts().to_dict()
            column_types_str = {str(k): int(v) for k, v in column_types.items()}
            
            load_time = time.time() - start_time
            
            metadata = {
                "rows": rows,
                "columns": cols,
                "completeness": float(completeness),
                "missing_values": int(missing_values),
                "file_size_bytes": file_path.stat().st_size,
                "column_types": column_types_str,
                "load_time_sec": load_time
            }
            
            if progress_callback:
                progress_callback(100.0, f"Successfully loaded {rows:,} rows, {cols} columns")
            
            self.logger(
                "INFO",
                "DataLoader",
                f"[OK] Loaded {rows:,} rows, {cols} columns ({completeness*100:.1f}% complete)"
            )
            
            return StepResult(
                success=True,
                data=df,
                metadata=metadata,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            error_msg = f"Failed to load data: {str(e)}"
            self.logger("ERROR", "DataLoader", error_msg)
            return StepResult(
                success=False,
                data=None,
                metadata={"load_time_sec": time.time() - start_time},
                errors=[error_msg]
            )
    
    def _validate_schema(self, df: pd.DataFrame) -> tuple[List[str], List[str]]:
        """
        Validate DataFrame schema.
        
        Args:
            df: DataFrame to validate
        
        Returns:
            Tuple of (errors, warnings)
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        # No specific column requirements - accept any CSV structure
        
        # Check for empty DataFrame
        if df.empty:
            error_msg = "DataFrame is empty (no rows)"
            errors.append(error_msg)
            self.logger("ERROR", "DataLoader", error_msg)
            return errors, warnings
        
        # Check for duplicate patient IDs if column exists
        if 'patient_id' in df.columns:
            duplicates = df['patient_id'].duplicated().sum()
            if duplicates > 0:
                warning_msg = f"Found {duplicates} duplicate patient IDs"
                warnings.append(warning_msg)
                self.logger("WARNING", "DataLoader", warning_msg)
        
        # Check for columns with all missing values
        all_null_cols = df.columns[df.isna().all()].tolist()
        if all_null_cols:
            warning_msg = f"Columns with all missing values: {', '.join(all_null_cols)}"
            warnings.append(warning_msg)
            self.logger("WARNING", "DataLoader", warning_msg)
        
        # Log validation summary
        if not errors:
            self.logger("INFO", "DataLoader", "[OK] Schema validation passed")
        
        return errors, warnings
