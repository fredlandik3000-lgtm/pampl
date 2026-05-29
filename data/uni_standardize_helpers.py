"""Helper functions and constants for uni_standardize.py"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple

# Categorical columns that need special handling
CATEGORICAL_COLUMNS = [
    'dx_cart', 'race', 'survival_status_lfu', 'cart_product', 'performance_status',
    'cat_cause_death', 'cns_involvement', 'cns_status', 'cns_involvement_level',
    'bridging_tx', 'bridging_type', 'burden_before_cart', 'best_response',
    'cart_response_category_D30', 'cart_response_90_days',
    'cart_response_6_mos', 'cart_response_1_yr', 'relapse_or_progression',
    'cd19_post_relapse', 'ethnicity', 'lymphodep_regimen', 'icans', 'iec-hs',
    'icu_admission', 'prbc_infusion', 'plt_transfusion', 'infection_30days',
    'infection_type_30days', 'infection_type_100_days', 'pt_transfusion', 'bridging_other'
]


def clean_bridging_other_value(row):
    """
    Clean bridging_other column by removing redundant duplicates of bridging_type.
    
    Args:
        row: DataFrame row with 'bridging_other' and 'bridging_type' columns
        
    Returns:
        Cleaned bridging_other value or np.nan if redundant
    """
    other_val = row['bridging_other']
    type_val = row['bridging_type']
    
    if pd.isna(other_val):
        return np.nan
    
    other_str = str(other_val).strip()
    type_str = str(type_val).strip() if pd.notna(type_val) else ''
    
    # Remove if exact duplicate of bridging_type
    if other_str == type_str:
        return np.nan
    
    # Standardize abbreviations
    if other_str.upper() == 'RT':
        other_str = 'Radiation therapy'
        # If bridging_type is already Radiation therapy, remove duplicate
        if type_str == 'Radiation therapy':
            return np.nan
    
    # If it's just "Chemo" and bridging_type is "Chemo-based regimen", remove
    if other_str.lower() == 'chemo' and type_str == 'Chemo-based regimen':
        return np.nan
    
    # Keep specific drug regimens (they provide valuable detail beyond the category)
    return other_str


DX_CART_REDCAP_HEADER = "1, Lymphoma | 2, ALL | 3, MM | 4, Other"

DX_CART_LABEL_BY_CODE = {
    "1": "Lymphoma",
    "2": "ALL",
    "3": "MM",
    "4": "Other",
}

DX_CART_STRING_MAP = {
    "Lymphoma": "Lymphoma",
    "1. Lymphoma": "Lymphoma",
    "1": "Lymphoma",
    "ALL": "ALL",
    "2. ALL": "ALL",
    "2": "ALL",
    "MM": "MM",
    "3. MM": "MM",
    "3": "MM",
    "Other": "Other",
    "4. Other": "Other",
    "4": "Other",
    DX_CART_REDCAP_HEADER: np.nan,
}

# Observed lymphoma histology labels (JHU/UNC); not used for MM (see backfill rules).
LYMPHOMA_SUBTYPE_ALLOWLIST = frozenset({
    "DLBCL, n.o.s.",
    "DLBCL, n.o.s",
    "MCL",
    "tFL",
    "FL",
    "PMBCL",
    "PCNSL",
    "MZL",
    "Double-hit lymphoma",
    "Triple-hit lymphoma",
    "Double expressor lymphoma",
})


def normalize_dx_cart_value(value) -> object:
    """Map REDCap dx_cart codes/labels to Lymphoma | ALL | MM | Other."""
    if pd.isna(value):
        return np.nan
    if isinstance(value, str):
        stripped = value.strip()
        if stripped == "" or stripped.lower() == "nan":
            return np.nan
        if stripped == DX_CART_REDCAP_HEADER:
            return np.nan
        if stripped in DX_CART_STRING_MAP:
            return DX_CART_STRING_MAP[stripped]
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        code = int(value)
        if 1 <= code <= 4:
            return DX_CART_LABEL_BY_CODE[str(code)]
    text = str(value).strip()
    if text in DX_CART_STRING_MAP:
        return DX_CART_STRING_MAP[text]
    try:
        code = int(float(text))
        if 1 <= code <= 4:
            return DX_CART_LABEL_BY_CODE[str(code)]
    except (ValueError, TypeError):
        pass
    return np.nan


def _nonempty_field(value) -> bool:
    if pd.isna(value):
        return False
    text = str(value).strip()
    return text != "" and text.lower() != "nan"


def infer_dx_cart_from_subtype_fields(row) -> Tuple[object, Optional[str]]:
    """
    Infer dx_cart only from disease-specific subtype columns.
    Returns (dx_cart, source_tag) or (nan, None) when ambiguous.
    """
    rules = []
    if _nonempty_field(row.get("all_subtype")):
        rules.append(("ALL", "backfill:all_subtype"))
    if _nonempty_field(row.get("mm_risk_stratification")):
        rules.append(("MM", "backfill:mm_risk_stratification"))
    lymphoma = row.get("lymphoma_subtype")
    if _nonempty_field(lymphoma):
        label = str(lymphoma).strip()
        if label.upper() == "MM":
            rules.append(("MM", "backfill:lymphoma_subtype"))
        elif label in LYMPHOMA_SUBTYPE_ALLOWLIST:
            rules.append(("Lymphoma", "backfill:lymphoma_subtype"))
    if not rules:
        return np.nan, None
    categories = {rule[0] for rule in rules}
    if len(categories) > 1:
        return np.nan, "backfill:conflict"
    return rules[0]


def backfill_dx_cart(df: pd.DataFrame, logger=None) -> pd.DataFrame:
    """
    Fill missing dx_cart from subtype fields. Never overwrites existing dx_cart.
    Adds/overwrites dx_cart_source: redcap | backfill:* | backfill:conflict.
    """
    if "dx_cart" not in df.columns:
        return df

    if df["dx_cart"].dtype != object:
        df["dx_cart"] = df["dx_cart"].astype(object)

    if "dx_cart_source" not in df.columns:
        df["dx_cart_source"] = pd.Series(pd.NA, index=df.index, dtype="object")
        df.loc[df["dx_cart"].notna(), "dx_cart_source"] = "redcap"
    else:
        has_dx = df["dx_cart"].notna()
        df.loc[has_dx, "dx_cart_source"] = df.loc[has_dx, "dx_cart_source"].fillna("redcap")

    missing_mask = df["dx_cart"].isna()
    if not missing_mask.any():
        return df

    filled = 0
    conflicts = 0
    for idx in df.index[missing_mask]:
        row = df.loc[idx]
        inferred_dx, source = infer_dx_cart_from_subtype_fields(row)
        if source == "backfill:conflict":
            conflicts += 1
            df.at[idx, "dx_cart_source"] = source
            if logger is not None:
                logger.warning(
                    "dx_cart backfill conflict study_id=%s",
                    row.get("study_id", "?"),
                )
            continue
        if pd.isna(inferred_dx) or source is None:
            continue
        df.at[idx, "dx_cart"] = inferred_dx
        df.at[idx, "dx_cart_source"] = source
        filled += 1
        if logger is not None:
            logger.info(
                "dx_cart backfill study_id=%s -> %s (%s)",
                row.get("study_id", "?"),
                inferred_dx,
                source,
            )

    if logger is not None:
        logger.info(
            "dx_cart backfill: filled=%s conflicts=%s still_missing=%s",
            filled,
            conflicts,
            df["dx_cart"].isna().sum(),
        )
    return df
