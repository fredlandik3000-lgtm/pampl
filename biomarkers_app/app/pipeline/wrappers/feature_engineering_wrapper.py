"""Feature Engineering Wrapper for preparing features for model training"""

import time
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Tuple
from sklearn.preprocessing import StandardScaler

from app.pipeline.types import (
    ProgressCallback, LogCallback, CancellationToken, StepResult, PRIMARY_TARGETS
)


class FeatureEngineeringWrapper:
    """Wrapper for feature engineering and preparation.
    Uses the same feature groups and phase mapping as the command-line NN trainer
    (versions/nn_module_enhanced_fixed_v6.py) so app results match CLI results.
    """

    # NN-aligned feature groups (same as nn_module_enhanced_fixed_v6.prepare_features)
    NN_FEATURE_GROUPS = {
        'baseline': [
            'age_cart', 'performance_status', 'dx_cart', 'lymphoma_subtype',
            'number_of_prior_treatments', 'prior_autotransplantation', 'prior_allotransplantation',
            'bridging_tx', 'burden_before_cart', 'lymphoma_number_of_lesions', 'lymphoma_greatest_diameter',
            'all_blast_percentage', 'lymphodep_regimen', 'lymphodep_dose', 'cart_product',
            'days_lymphodep', 'pre_ld_wbc', 'pre_ld_anc', 'pre_ld_aec', 'pre_ld_abc', 'pre_ld_hgb',
            'pre_ld_pt', 'pre_ld_alc', 'pre_ld_amc', 'pre_ld_crp', 'pre_ld_fer', 'pre_ld_il_6',
            'pre_car_wbc', 'pre_car_hgb', 'pre_car_anc', 'pre_car_pt', 'pre_car_alc', 'pre_car_amc',
            'pre_car_ldh', 'pre_car_crt', 'pre_car_lgg', 'pre_car_crp', 'pre_car_fer', 'pre_car_il_6',
            'ebv_status', 'lm_rearrangement', 'dlbcl_subtype', 'extranodal_disease', 'bulky_disease',
            'marrow_involvement', 'marrow_fibrosis', 'hiv_status'
        ],
        'daily': [
            'post_car_daily_wbc', 'post_car_daily_aec', 'post_car_daily_abc', 'post_car_daily_anc',
            'post_car_daily_hgb', 'post_car_daily_pt', 'post_car_daily_alc', 'post_car_daily_amc',
            'post_car_daily_ldh', 'post_car_daily_il_6', 'post_car_daily_crp_base', 'post_car_daily_crp_peak',
            'post_car_daily_fer_base', 'post_car_daily_fer_peak'
        ],
        'monthly': [
            'post_car_montly_wbc', 'post_car_montly_aec', 'post_car_montly_abc', 'post_car_montly_anc',
            'post_car_montly_hgb', 'post_car_montly_pt', 'post_car_montly_alc', 'post_car_montly_amc',
            'post_car_montly_ldh', 'post_car_montly_crt', 'post_car_montly_lgg', 'post_car_montly_crp',
            'post_car_montly_fer', 'post_car_montly_il_6'
        ],
        'specific_days': [
            'Day 30 ANC', 'Day 30 ALC', 'Day 30 Creatinine', 'Day 90 ANC', 'Day 90 ALC', 'Day 90 Creatinine',
            'Day 180 ANC', 'Day 180 ALC', 'Day 180 Creatinine', 'IgG day 30-60', 'IgG day 90-120',
            'IgG 180-210', 'IgG 1 year'
        ],
        'nadir': [
            'nadir_wbc', 'rec_time_wbc', 'norm_time_wbc', 'nadir_neutrophil', 'rec_time_neutrophil',
            'norm_time_neutrophil', 'nadir_pt', 'rec_time_pt', 'norm_time_pt', 'nadir_hgb', 'rec_time_hgb',
            'norm_time_hgb'
        ]
    }

    # Phase -> cumulative feature groups (matches nn_module_enhanced_fixed_v6 phase mapping)
    NN_PHASE_FEATURES = {
        'phase_-6': ['baseline'],
        'phase_0': ['baseline'],
        'phase_15': ['baseline', 'daily'],
        'phase_30': ['baseline', 'daily', 'monthly', 'specific_days'],
    }
    
    def __init__(self, logger: Optional[LogCallback] = None):
        """
        Initialize feature engineering wrapper.
        
        Args:
            logger: Optional logging callback
        """
        self.logger = logger or self._default_logger
        self.scalers: Dict[str, StandardScaler] = {}
        self.feature_names: Dict[str, List[str]] = {}
    
    def _default_logger(self, level: str, source: str, message: str) -> None:
        """Default logger that prints to console"""
        print(f"[{level}] {source}: {message}")
    
    def engineer_features(
        self,
        df: pd.DataFrame,
        phase: str = 'phase_-6',
        fit_scalers: bool = True,
        progress_callback: Optional[ProgressCallback] = None,
        cancellation_token: Optional[CancellationToken] = None,
        use_feature_selection: bool = False,
        feature_selection_method: str = "mutual_info",
        feature_selection_top_k: int = 50,
    ) -> StepResult:
        """
        Engineer features for a specific phase.
        
        Args:
            df: Input dataframe with raw/standardized data
            phase: Phase identifier (phase_-6, phase_0, phase_15, phase_30)
            fit_scalers: Whether to fit scalers (True for training, False for inference)
            progress_callback: Optional progress reporting callback
            cancellation_token: Optional cancellation token
            use_feature_selection: If True, reduce features by method (variance or mutual_info)
            feature_selection_method: "none" | "variance" | "mutual_info"
            feature_selection_top_k: Keep top K features when using variance or mutual_info
            
        Returns:
            StepResult with engineered features
        """
        start_time = time.time()
        self.logger('info', 'FeatureEngineering', f'Starting feature engineering for {phase}')
        
        try:
            # Check cancellation
            if cancellation_token and cancellation_token.is_cancelled():
                return StepResult(
                    success=False,
                    data=None,
                    metadata={"engineering_time_sec": time.time() - start_time},
                    errors=["Feature engineering cancelled by user"]
                )
            
            # Report initial progress
            if progress_callback:
                progress_callback(0.0, "Selecting phase-specific features...")
            
            # Select features for this phase
            selected_features = self._select_features_for_phase(df, phase)
            
            if progress_callback:
                progress_callback(0.2, f"Selected {len(selected_features)} features")
            
            # Check cancellation
            if cancellation_token and cancellation_token.is_cancelled():
                return StepResult(
                    success=False,
                    data=None,
                    metadata={"engineering_time_sec": time.time() - start_time},
                    errors=["Feature engineering cancelled by user"]
                )
            
            # Prepare features
            if progress_callback:
                progress_callback(0.3, "Processing categorical features...")
            
            engineered_df = self._prepare_features(
                df, 
                selected_features, 
                phase,
                fit_scalers
            )
            
            # Optional feature selection (after scaling so variance/mutual_info are on same scale)
            if use_feature_selection and feature_selection_method and feature_selection_method != "none":
                if progress_callback:
                    progress_callback(0.5, f"Feature selection ({feature_selection_method})...")
                kept_features = self._apply_feature_selection(
                    engineered_df,
                    selected_features,
                    feature_selection_method,
                    feature_selection_top_k,
                    phase,
                )
                if kept_features and len(kept_features) < len(selected_features):
                    to_drop = [c for c in selected_features if c not in kept_features and c in engineered_df.columns]
                    if to_drop:
                        engineered_df = engineered_df.drop(columns=to_drop)
                    selected_features = kept_features
            
            if progress_callback:
                progress_callback(0.7, "Applying feature transformations...")
            
            # Check cancellation
            if cancellation_token and cancellation_token.is_cancelled():
                return StepResult(
                    success=False,
                    data=None,
                    metadata={"engineering_time_sec": time.time() - start_time},
                    errors=["Feature engineering cancelled by user"]
                )
            
            # Add metadata
            engineered_df.attrs['phase'] = phase
            engineered_df.attrs['feature_count'] = len(selected_features)
            engineered_df.attrs['engineered_features'] = selected_features
            
            if progress_callback:
                progress_callback(1.0, "Feature engineering complete")
            
            engineering_time = time.time() - start_time
            self.logger('info', 'FeatureEngineering', 
                       f'Completed in {engineering_time:.2f}s - {len(selected_features)} features')
            
            return StepResult(
                success=True,
                data=engineered_df,
                metadata={
                    'phase': phase,
                    'feature_count': len(selected_features),
                    'selected_features': selected_features,
                    'categorical_count': sum(1 for col in selected_features if engineered_df[col].dtype == 'object'),
                    'numeric_count': sum(1 for col in selected_features if engineered_df[col].dtype != 'object'),
                    'engineering_time_sec': engineering_time
                }
            )
            
        except Exception as e:
            engineering_time = time.time() - start_time
            error_msg = f"Feature engineering failed: {str(e)}"
            self.logger('error', 'FeatureEngineering', error_msg)
            
            import traceback
            traceback.print_exc()
            
            return StepResult(
                success=False,
                data=None,
                metadata={"engineering_time_sec": engineering_time},
                errors=[error_msg]
            )
    
    def _select_features_for_phase(self, df: pd.DataFrame, phase: str) -> List[str]:
        """
        Select features available at the given phase using NN-aligned groups
        (same as command-line nn_module_enhanced_fixed_v6).
        """
        if phase not in self.NN_PHASE_FEATURES:
            self.logger('warning', 'FeatureEngineering',
                        f'Unknown phase {phase}, defaulting to phase_-6')
            phase = 'phase_-6'

        available_groups = self.NN_PHASE_FEATURES[phase]
        selected_features = []
        for group_name in available_groups:
            if group_name in self.NN_FEATURE_GROUPS:
                group_features = self.NN_FEATURE_GROUPS[group_name]
                existing_features = [f for f in group_features if f in df.columns]
                selected_features.extend(existing_features)

        self.logger('info', 'FeatureEngineering',
                    f'Selected {len(selected_features)} features from {len(available_groups)} groups')
        return selected_features

    def _apply_feature_selection(
        self,
        engineered_df: pd.DataFrame,
        selected_features: List[str],
        method: str,
        top_k: int,
        phase: str,
    ) -> List[str]:
        """
        Reduce features to top_k by variance or mutual information.
        Returns the list of feature names to keep (subset of selected_features).
        """
        existing = [c for c in selected_features if c in engineered_df.columns]
        if not existing or top_k <= 0:
            return selected_features
        # Build numeric matrix (numeric columns only; categoricals skipped for selection)
        numeric_cols = [c for c in existing if engineered_df[c].dtype in (np.floating, np.int64, np.int32)]
        if not numeric_cols:
            return selected_features
        X = engineered_df[numeric_cols].fillna(0).astype(np.float64)
        if method == "variance":
            variances = np.var(X, axis=0)
            order = np.argsort(variances)[::-1]
            k = min(top_k, len(numeric_cols))
            kept_numeric = [numeric_cols[i] for i in order[:k]]
            # Keep all non-numeric selected features plus top numeric
            return [c for c in selected_features if c not in numeric_cols] + kept_numeric
        if method == "mutual_info":
            try:
                from sklearn.feature_selection import mutual_info_classif
            except ImportError:
                return selected_features
            # Use first primary target present in df with at least 2 classes
            target = None
            for t in PRIMARY_TARGETS:
                if t not in engineered_df.columns:
                    continue
                ser = engineered_df[t].dropna().astype(str).str.strip()
                ser = ser[ser != ""]
                if len(ser) < 20 or ser.nunique() < 2:
                    continue
                target = t
                break
            if target is None:
                return selected_features
            valid_idx = engineered_df[target].notna() & (engineered_df[target].astype(str).str.strip() != "")
            X_valid = engineered_df.loc[valid_idx, numeric_cols].fillna(0).astype(np.float64)
            from sklearn.preprocessing import LabelEncoder
            y_valid = LabelEncoder().fit_transform(engineered_df.loc[valid_idx, target].astype(str))
            if len(X_valid) < 20 or len(np.unique(y_valid)) < 2:
                return selected_features
            mi = mutual_info_classif(X_valid, y_valid, random_state=42)
            order = np.argsort(mi)[::-1]
            k = min(top_k, len(numeric_cols))
            kept_numeric = [numeric_cols[i] for i in order[:k]]
            return [c for c in selected_features if c not in numeric_cols] + kept_numeric
        return selected_features
    
    def _prepare_features(
        self, 
        df: pd.DataFrame, 
        features: List[str],
        phase: str,
        fit_scalers: bool
    ) -> pd.DataFrame:
        """
        Prepare features with encoding and scaling.
        
        Args:
            df: Input dataframe
            features: List of feature names to prepare
            phase: Phase identifier
            fit_scalers: Whether to fit scalers
            
        Returns:
            DataFrame with prepared features
        """
        result_df = df.copy()
        
        # Separate categorical and numeric features
        categorical_features = []
        numeric_features = []
        
        for feature in features:
            if feature in df.columns:
                if df[feature].dtype == 'object' or df[feature].dtype.name == 'category':
                    categorical_features.append(feature)
                else:
                    numeric_features.append(feature)
        
        self.logger('info', 'FeatureEngineering',
                   f'Processing {len(numeric_features)} numeric and {len(categorical_features)} categorical features')
        
        # Handle numeric features
        if numeric_features:
            # Fill missing values with 0 (common for lab values)
            for feature in numeric_features:
                result_df[feature] = result_df[feature].fillna(0)
            
            # Apply log1p transform for highly skewed features (like LDH, ferritin)
            skewed_features = [f for f in numeric_features if 'ldh' in f.lower() or 'ferritin' in f.lower()]
            for feature in skewed_features:
                result_df[feature] = np.log1p(result_df[feature].clip(lower=0))
            
            # Scale numeric features
            if fit_scalers:
                self.scalers[phase] = StandardScaler()
                result_df[numeric_features] = self.scalers[phase].fit_transform(result_df[numeric_features])
            elif phase in self.scalers:
                result_df[numeric_features] = self.scalers[phase].transform(result_df[numeric_features])
        
        # Handle categorical features - convert to string and fill missing
        for feature in categorical_features:
            result_df[feature] = result_df[feature].astype(str).fillna('Unknown')
        
        # Store feature names for this phase
        self.feature_names[phase] = features
        
        return result_df
    
    def get_feature_names(self, phase: str) -> List[str]:
        """
        Get feature names for a specific phase.
        
        Args:
            phase: Phase identifier
            
        Returns:
            List of feature names
        """
        return self.feature_names.get(phase, [])
