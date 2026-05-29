import pandas as pd
import numpy as np
import re
from uni_config import logger
from uni_standardize_helpers import (
    CATEGORICAL_COLUMNS,
    clean_bridging_other_value,
    normalize_dx_cart_value,
)

def clean_column_values(df):
    """Clean column values by removing option numbers in categorical fields"""
    logger.info("Cleaning column values")
    try:
        for col in df.columns:
            if col not in CATEGORICAL_COLUMNS and df[col].dtype == 'object':
                logger.debug(f"Cleaning column: {col}")
                df[col] = df[col].replace('nan', np.nan)
                mask = df[col].notna()
                if mask.any():
                    df.loc[mask, col] = df.loc[mask, col].astype(str).str.strip()
                    df.loc[mask, col] = df.loc[mask, col].replace(r'^\d+\.\s*', '', regex=True)
                    df.loc[mask, col] = df.loc[mask, col].replace(r'^\s*\d+,\s*', '', regex=True)
                    df.loc[mask, col] = df.loc[mask, col].str.strip()
        logger.info("Column values cleaned successfully")
        return df
    except Exception as e:
        logger.error(f"Error cleaning column values: {e}")
        raise

def standardize_categorical_values(df):
    """Standardize categorical values between datasets"""
    logger.info("Standardizing categorical values")
    try:
        # Standardize gender
        if 'gender' in df.columns and df['gender'].notna().any():
            logger.debug("Standardizing gender column")
            gender_mapping = {
                'Male': 'Male', '1. Male': 'Male', '1': 'Male',
                'Female': 'Female', '2. Female': 'Female', '2': 'Female',
                'Other': 'Other', '3. Other': 'Other', '3': 'Other',
                np.nan: np.nan, 'nan': np.nan
            }
            df['gender'] = df['gender'].map(lambda x: gender_mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan)

        # Standardize dx_cart (handles UNC labels and JHU float codes 1.0, 3.0, etc.)
        if 'dx_cart' in df.columns:
            logger.debug("Standardizing dx_cart column")
            logger.debug(f"Raw dx_cart values: {df['dx_cart'].unique()}")
            df['dx_cart'] = df['dx_cart'].apply(normalize_dx_cart_value).astype(object)
            logger.debug(f"Standardized dx_cart values: {df['dx_cart'].unique()}")

        # Standardize cart_product
        if 'cart_product' in df.columns and df['cart_product'].notna().any():
            logger.debug("Standardizing cart_product column")
            logger.debug(f"Raw cart_product values: {df['cart_product'].unique()}")
            product_mapping = {
                'Tisa-cel (Kymriah)': 'Tisa-cel', '1, Tisa-cel (Kymriah)': 'Tisa-cel', '1': 'Tisa-cel',
                'Axi-cel (Yescarta)': 'Axi-cel', '2, Axi-cel (Yescarta)': 'Axi-cel', '2': 'Axi-cel',
                '2, Axi-cel': 'Axi-cel', '2,Axi-cel': 'Axi-cel', '2 , Axi-cel': 'Axi-cel',
                'Brexu-cel (Tecartus)': 'Brexu-cel', '3, Brexu-cel (Tecartus)': 'Brexu-cel', '3': 'Brexu-cel',
                'Liso-cel (Breyanzi)': 'Liso-cel', '4, Liso-cel (Breyanzi)': 'Liso-cel', '4': 'Liso-cel',
                'Ide-cel (Abecma)': 'Ide-cel', '5, Ide-cel (Abecma)': 'Ide-cel', '5': 'Ide-cel',
                'Cilta-cel (Carvykti)': 'Cilta-cel', '6, Cilta-cel (Carvykti)': 'Cilta-cel', '6': 'Cilta-cel',
                '1, Tisa-cel (Kymriah) | 2, Axi-cel (Yescarta) | 3, Brexu-cel (Tecartus) | 4, Liso-cel (Breyanzi) | 5, Ide-cel (Abecma) | 6, Cilta-cel (Carvykti)': np.nan,
                np.nan: np.nan, 'nan': np.nan
            }
            mask = df['cart_product'].notna()
            if mask.any():
                # Ensure cart_product is string type
                df['cart_product'] = df['cart_product'].astype(str)
                # Log values for patient 50 and 51 specifically
                if 'study_id' in df.columns:
                    patient_50_51 = df[df['study_id'].isin(['50', '51'])][['study_id', 'cart_product']]
                    logger.debug(f"cart_product for patients 50 and 51 before mapping:\n{patient_50_51.to_string()}")
                # Apply mapping with regex fallback
                def map_product(x):
                    x = str(x).strip()
                    if x in product_mapping:
                        return product_mapping[x]
                    # Regex for Axi-cel variants
                    if re.match(r'^2\s*[,]\s*Axi-cel\s*$', x, re.IGNORECASE):
                        logger.debug(f"Matched Axi-cel variant: '{x}'")
                        return 'Axi-cel'
                    logger.debug(f"Unmapped cart_product value: '{x}'")
                    return np.nan
                df.loc[mask, 'cart_product'] = df.loc[mask, 'cart_product'].apply(map_product)
                if 'study_id' in df.columns:
                    patient_50_51 = df[df['study_id'].isin(['50', '51'])][['study_id', 'cart_product']]
                    logger.debug(f"cart_product for patients 50 and 51 after mapping:\n{patient_50_51.to_string()}")
            logger.debug(f"Standardized cart_product values: {df['cart_product'].unique()}")

        # Standardize best_response
        if 'best_response' in df.columns and df['best_response'].notna().any():
            logger.debug("Standardizing best_response column")
            response_mapping = {
                'Complete Response': 'Complete Response', 'COMPLETE RESPONSE': 'Complete Response',
                'Complete response': 'Complete Response', 'MRD Negative Stringent Complete Response': 'Complete Response',
                'Partial Response': 'Partial Response', 'PARTIAL RESPONSE': 'Partial Response',
                'Partial response': 'Partial Response', 'Very Good Partial Response': 'Partial Response',
                'Progressive Disease': 'Progressive Disease', 'PROGRESSIVE DISEASE': 'Progressive Disease',
                'Progressive disease': 'Progressive Disease',
                'Stable Disease': 'Stable Disease', 'STABLE DISEASE': 'Stable Disease',
                'Stable disease': 'Stable Disease',
                'Inevaluable': 'Inevaluable', 'died early without response assessment': 'Inevaluable',
                'NA': 'Inevaluable', 'nan': np.nan,
                'min([cart_response_category], [cart_response_90_days], [cart_response_6_mos], [cart_response_1_yr])': np.nan
            }
            mask = df['best_response'].notna()
            if mask.any():
                df.loc[mask, 'best_response'] = df.loc[mask, 'best_response'].map(
                    lambda x: response_mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan
                )

        # Standardize race
        if 'race' in df.columns and df['race'].notna().any():
            logger.debug("Standardizing race column")
            logger.debug(f"Raw race values: {df['race'].unique()}")
            race_mapping = {
                'White': 'White', '1': 'White', '1.0': 'White', '1. White': 'White',
                'Black or African American': 'Black or African American', '2': 'Black or African American', '2.0': 'Black or African American', '2. Black or African American': 'Black or African American',
                'American Indian or Alaska Native': 'American Indian or Alaska Native', '3': 'American Indian or Alaska Native', '3.0': 'American Indian or Alaska Native', '3. American Indian or Alaska Native': 'American Indian or Alaska Native',
                'Asian': 'Asian', '4': 'Asian', '4.0': 'Asian', '4. Asian': 'Asian',
                'Native Hawaiian or Other Pacific Islander': 'Native Hawaiian or Other Pacific Islander', '5': 'Native Hawaiian or Other Pacific Islander', '5.0': 'Native Hawaiian or Other Pacific Islander', '5. Native Hawaiian or Other Pacific Islander': 'Native Hawaiian or Other Pacific Islander',
                'Other': 'Other', '6': 'Other', '6.0': 'Other', '6. Other': 'Other',
                '0': np.nan, '0.0': np.nan, np.nan: np.nan, 'nan': np.nan, '': np.nan
            }
            df['race'] = df['race'].map(lambda x: race_mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan)
            logger.debug(f"Standardized race values: {df['race'].unique()}")

        # Standardize survival_status_lfu
        if 'survival_status_lfu' in df.columns and df['survival_status_lfu'].notna().any():
            logger.debug("Standardizing survival_status_lfu column")
            logger.debug(f"Raw survival_status_lfu values: {df['survival_status_lfu'].unique()}")
            survival_mapping = {
                'Alive': 'Alive', '0': 'Alive', '0.0': 'Alive', '0, Alive': 'Alive', '0. Alive': 'Alive',
                'Deceased': 'Deceased', '1': 'Deceased', '1.0': 'Deceased', '1, Deceased': 'Deceased', '1. Deceased': 'Deceased',
                'Lost to FU': 'Lost to FU', '2': 'Lost to FU', '2.0': 'Lost to FU', '2, Lost to FU': 'Lost to FU', '2. Lost to FU': 'Lost to FU',
                np.nan: np.nan, 'nan': np.nan, '': np.nan, 'N/A': np.nan
            }
            df['survival_status_lfu'] = df['survival_status_lfu'].map(
                lambda x: survival_mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan
            )
            logger.debug(f"Standardized survival_status_lfu values: {df['survival_status_lfu'].unique()}")

        # Standardize cat_cause_death
        if 'cat_cause_death' in df.columns and df['cat_cause_death'].notna().any():
            logger.debug("Standardizing cat_cause_death column")
            logger.debug(f"Raw cat_cause_death values: {df['cat_cause_death'].unique()}")
            cause_mapping = {
                'Disease progression': 'Disease progression',
                '1': 'Disease progression', '1.0': 'Disease progression',
                '1. Disease progression': 'Disease progression', '1, Disease progression': 'Disease progression',
                'NRM': 'NRM',
                '2': 'NRM', '2.0': 'NRM',
                '2. NRM': 'NRM', '2, NRM': 'NRM',
                np.nan: np.nan, 'nan': np.nan, '': np.nan
            }
            df['cat_cause_death'] = df['cat_cause_death'].map(
                lambda x: cause_mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan
            )
            logger.debug(f"Standardized cat_cause_death values: {df['cat_cause_death'].unique()}")

        # Standardize performance_status (ECOG Performance Status)
        if 'performance_status' in df.columns and df['performance_status'].notna().any():
            logger.debug("Standardizing performance_status column")
            logger.debug(f"Raw performance_status values: {df['performance_status'].unique()}")
            # ECOG Performance Status: 0-5 scale
            ecog_mapping = {
                'ECOG 0: Fully active': 'ECOG 0: Fully active',
                'ECOG 1: Restricted in strenuous activity': 'ECOG 1: Restricted in strenuous activity',
                'ECOG 2: Ambulatory, self-care, unable to work': 'ECOG 2: Ambulatory, self-care, unable to work',
                'ECOG 3: Limited self-care, confined >50% of day': 'ECOG 3: Limited self-care, confined >50% of day',
                'ECOG 4: Completely disabled': 'ECOG 4: Completely disabled',
                'ECOG 5: Dead': 'ECOG 5: Dead',
                '0': 'ECOG 0: Fully active', '0.0': 'ECOG 0: Fully active',
                '0. 0': 'ECOG 0: Fully active', '0, 0': 'ECOG 0: Fully active',
                '1': 'ECOG 1: Restricted in strenuous activity', '1.0': 'ECOG 1: Restricted in strenuous activity',
                '1. 1': 'ECOG 1: Restricted in strenuous activity', '1, 1': 'ECOG 1: Restricted in strenuous activity',
                '2': 'ECOG 2: Ambulatory, self-care, unable to work', '2.0': 'ECOG 2: Ambulatory, self-care, unable to work',
                '2. 2': 'ECOG 2: Ambulatory, self-care, unable to work', '2, 2': 'ECOG 2: Ambulatory, self-care, unable to work',
                '3': 'ECOG 3: Limited self-care, confined >50% of day', '3.0': 'ECOG 3: Limited self-care, confined >50% of day',
                '3. 3': 'ECOG 3: Limited self-care, confined >50% of day', '3, 3': 'ECOG 3: Limited self-care, confined >50% of day',
                '4': 'ECOG 4: Completely disabled', '4.0': 'ECOG 4: Completely disabled',
                '4. 4': 'ECOG 4: Completely disabled', '4, 4': 'ECOG 4: Completely disabled',
                '5': 'ECOG 5: Dead', '5.0': 'ECOG 5: Dead',
                '5. 5': 'ECOG 5: Dead', '5, 5': 'ECOG 5: Dead',
                np.nan: np.nan, 'nan': np.nan, '': np.nan, 'N/A': np.nan
            }
            df['performance_status'] = df['performance_status'].map(
                lambda x: ecog_mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan
            )
            logger.debug(f"Standardized performance_status values: {df['performance_status'].unique()}")

        # Standardize cns_involvement (binary: yes/no)
        if 'cns_involvement' in df.columns and df['cns_involvement'].notna().any():
            logger.debug("Standardizing cns_involvement column")
            logger.debug(f"Raw cns_involvement values: {df['cns_involvement'].unique()}")
            cns_inv_mapping = {
                'No': 'No', 'no': 'No', 'NO': 'No',
                'Yes': 'Yes', 'yes': 'Yes', 'YES': 'Yes',
                '0': 'No', '0.0': 'No',
                '1': 'Yes', '1.0': 'Yes',
                np.nan: np.nan, 'nan': np.nan, '': np.nan
            }
            df['cns_involvement'] = df['cns_involvement'].map(
                lambda x: cns_inv_mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan
            )
            logger.debug(f"Standardized cns_involvement values: {df['cns_involvement'].unique()}")

        # Standardize cns_status
        if 'cns_status' in df.columns and df['cns_status'].notna().any():
            logger.debug("Standardizing cns_status column")
            logger.debug(f"Raw cns_status values: {df['cns_status'].unique()}")
            cns_status_mapping = {
                'Prior': 'Prior', 'prior': 'Prior', 'PRIOR': 'Prior',
                'Active': 'Active', 'active': 'Active', 'ACTIVE': 'Active',
                '0': 'Prior', '0.0': 'Prior', '0. Prior': 'Prior', '0, Prior': 'Prior',
                '1': 'Active', '1.0': 'Active', '1. Active': 'Active', '1, Active': 'Active',
                np.nan: np.nan, 'nan': np.nan, '': np.nan
            }
            df['cns_status'] = df['cns_status'].map(
                lambda x: cns_status_mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan
            )
            logger.debug(f"Standardized cns_status values: {df['cns_status'].unique()}")

        # Standardize cns_involvement_level
        if 'cns_involvement_level' in df.columns and df['cns_involvement_level'].notna().any():
            logger.debug("Standardizing cns_involvement_level column")
            logger.debug(f"Raw cns_involvement_level values: {df['cns_involvement_level'].unique()}")
            cns_level_mapping = {
                'CNS-1': 'CNS-1', 'CNS-2': 'CNS-2', 'CNS-3': 'CNS-3',
                '1': 'CNS-1', '1.0': 'CNS-1', '1. CNS-1': 'CNS-1', '1, CNS-1': 'CNS-1',
                '2': 'CNS-2', '2.0': 'CNS-2', '2. CNS-2': 'CNS-2', '2, CNS-2': 'CNS-2',
                '3': 'CNS-3', '3.0': 'CNS-3', '3. CNS-3': 'CNS-3', '3, CNS-3': 'CNS-3',
                np.nan: np.nan, 'nan': np.nan, '': np.nan
            }
            df['cns_involvement_level'] = df['cns_involvement_level'].map(
                lambda x: cns_level_mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan
            )
            logger.debug(f"Standardized cns_involvement_level values: {df['cns_involvement_level'].unique()}")

        # Standardize bridging_tx (binary yes/no, case-insensitive)
        if 'bridging_tx' in df.columns and df['bridging_tx'].notna().any():
            logger.debug("Standardizing bridging_tx column")
            logger.debug(f"Raw bridging_tx values: {df['bridging_tx'].unique()}")
            bridging_mapping = {
                'Yes': 'Yes', 'yes': 'Yes', 'YES': 'Yes',
                'No': 'No', 'no': 'No', 'NO': 'No',
                '1': 'Yes', '1.0': 'Yes',
                '0': 'No', '0.0': 'No',
                np.nan: np.nan, 'nan': np.nan, '': np.nan
            }
            df['bridging_tx'] = df['bridging_tx'].map(
                lambda x: bridging_mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan
            )
            logger.debug(f"Standardized bridging_tx values: {df['bridging_tx'].unique()}")

        # Standardize bridging_type
        if 'bridging_type' in df.columns and df['bridging_type'].notna().any():
            logger.debug("Standardizing bridging_type column")
            logger.debug(f"Raw bridging_type values: {df['bridging_type'].unique()}")
            bridging_type_mapping = {
                'Steroids': 'Steroids', 'steroids': 'Steroids', 'STEROIDS': 'Steroids',
                '1': 'Steroids', '1.0': 'Steroids', '1. Steroids': 'Steroids', '1, Steroids': 'Steroids',
                'Chemo-based regimen': 'Chemo-based regimen', 'chemo-based regimen': 'Chemo-based regimen',
                'Chemo-based': 'Chemo-based regimen', 'chemo-based': 'Chemo-based regimen',
                'Chemo based': 'Chemo-based regimen', 'chemo based': 'Chemo-based regimen',
                'Chemo': 'Chemo-based regimen', 'chemo': 'Chemo-based regimen', 'CHEMO': 'Chemo-based regimen',
                '2': 'Chemo-based regimen', '2.0': 'Chemo-based regimen',
                '2. Chemo-based regimen': 'Chemo-based regimen', '2, Chemo-based regimen': 'Chemo-based regimen',
                'Radiation therapy': 'Radiation therapy', 'radiation therapy': 'Radiation therapy',
                'Radiation': 'Radiation therapy', 'radiation': 'Radiation therapy', 'RADIATION': 'Radiation therapy',
                '3': 'Radiation therapy', '3.0': 'Radiation therapy',
                '3. Radiation therapy': 'Radiation therapy', '3, Radiation therapy': 'Radiation therapy',
                'Other': 'Other', 'other': 'Other', 'OTHER': 'Other',
                '4': 'Other', '4.0': 'Other', '4. Other': 'Other', '4, Other': 'Other',
                np.nan: np.nan, 'nan': np.nan, '': np.nan
            }
            df['bridging_type'] = df['bridging_type'].map(
                lambda x: bridging_type_mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan
            )
            logger.debug(f"Standardized bridging_type values: {df['bridging_type'].unique()}")

        # Standardize burden_before_cart
        if 'burden_before_cart' in df.columns and df['burden_before_cart'].notna().any():
            logger.debug("Standardizing burden_before_cart column")
            logger.debug(f"Raw burden_before_cart values: {df['burden_before_cart'].unique()}")
            burden_mapping = {
                'No burden': 'No burden', 'no burden': 'No burden', 'NO BURDEN': 'No burden',
                'None': 'No burden', 'none': 'No burden', 'NONE': 'No burden',
                '0': 'No burden', '0.0': 'No burden',
                'Bulky': 'Bulky', 'bulky': 'Bulky', 'BULKY': 'Bulky',
                '1': 'Bulky', '1.0': 'Bulky',
                np.nan: np.nan, 'nan': np.nan, '': np.nan
            }
            df['burden_before_cart'] = df['burden_before_cart'].map(
                lambda x: burden_mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan
            )
            logger.debug(f"Standardized burden_before_cart values: {df['burden_before_cart'].unique()}")

        # Create unified response mapping (used for all response columns)
        response_mapping = {
            # Complete Response variants (including MM-specific)
            'Complete Response': 'Complete Response', 'complete response': 'Complete Response', 
            'COMPLETE RESPONSE': 'Complete Response', 'Complete': 'Complete Response',
            'complete': 'Complete Response', 'COMPLETE': 'Complete Response',
            'CR': 'Complete Response', 'cr': 'Complete Response',
            '1': 'Complete Response', '1.0': 'Complete Response',
            '1. Complete Response': 'Complete Response', '1, Complete Response': 'Complete Response',
            # MM-specific complete responses (map to Complete Response for consistency)
            'MRD Negative Stringent Complete Response': 'Complete Response',
            'Minimal Residual Disease Negative Stringent Complete Response': 'Complete Response',
            'Minimal Residual Disease Negative': 'Complete Response',
            'Stringent Complete Response': 'Complete Response',
            'sCR': 'Complete Response', 'scr': 'Complete Response',
            'MRD Negative': 'Complete Response', 'mrd negative': 'Complete Response',
            
            # Partial Response variants (including MM-specific)
            'Partial Response': 'Partial Response', 'partial response': 'Partial Response',
            'PARTIAL RESPONSE': 'Partial Response', 'Partial': 'Partial Response',
            'partial': 'Partial Response', 'PARTIAL': 'Partial Response',
            'PR': 'Partial Response', 'pr': 'Partial Response',
            '2': 'Partial Response', '2.0': 'Partial Response',
            '2. Partial Response': 'Partial Response', '2, Partial Response': 'Partial Response',
            # MM-specific partial response
            'Very Good Partial Response': 'Partial Response',
            'VGPR': 'Partial Response', 'vgpr': 'Partial Response',
            
            # Stable Disease variants
            'Stable Disease': 'Stable Disease', 'stable disease': 'Stable Disease',
            'STABLE DISEASE': 'Stable Disease', 'Stable': 'Stable Disease',
            'stable': 'Stable Disease', 'STABLE': 'Stable Disease',
            'SD': 'Stable Disease', 'sd': 'Stable Disease',
            '3': 'Stable Disease', '3.0': 'Stable Disease',
            '3. Stable Disease': 'Stable Disease', '3, Stable Disease': 'Stable Disease',
            
            # Progressive Disease variants
            'Progressive Disease': 'Progressive Disease', 'progressive disease': 'Progressive Disease',
            'PROGRESSIVE DISEASE': 'Progressive Disease', 'Progressive': 'Progressive Disease',
            'progressive': 'Progressive Disease', 'PROGRESSIVE': 'Progressive Disease',
            'PD': 'Progressive Disease', 'pd': 'Progressive Disease',
            '4': 'Progressive Disease', '4.0': 'Progressive Disease',
            '4. Progressive Disease': 'Progressive Disease', '4, Progressive Disease': 'Progressive Disease',
            
            # Inevaluable variants (group together)
            'Inevaluable': 'Inevaluable', 'inevaluable': 'Inevaluable', 'INEVALUABLE': 'Inevaluable',
            'Indeterminate': 'Inevaluable', 'indeterminate': 'Inevaluable', 'INDETERMINATE': 'Inevaluable',
            'died early without response assessment': 'Inevaluable',
            'Died early without response assessment': 'Inevaluable',
            'died early': 'Inevaluable', 'Died early': 'Inevaluable',
            'Not evaluable': 'Inevaluable', 'not evaluable': 'Inevaluable',
            'NE': 'Inevaluable', 'ne': 'Inevaluable',
            '5': 'Inevaluable', '5.0': 'Inevaluable',
            '5. Inevaluable': 'Inevaluable', '5, Inevaluable': 'Inevaluable',
            
            np.nan: np.nan, 'nan': np.nan, '': np.nan
        }
        
        # Standardize all response columns using the unified mapping
        response_columns = ['best_response', 'cart_response_category_D30', 
                           'cart_response_90_days', 'cart_response_6_mos', 'cart_response_1_yr']
        
        for col in response_columns:
            if col in df.columns and df[col].notna().any():
                logger.debug(f"Standardizing {col} column")
                logger.debug(f"Raw {col} values: {df[col].unique()}")
                df[col] = df[col].map(
                    lambda x: response_mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan
                )
                logger.debug(f"Standardized {col} values: {df[col].unique()}")

        # Standardize relapse_or_progression (case-insensitive Yes/No)
        if 'relapse_or_progression' in df.columns and df['relapse_or_progression'].notna().any():
            logger.debug("Standardizing relapse_or_progression column")
            logger.debug(f"Raw relapse_or_progression values: {df['relapse_or_progression'].unique()}")
            relapse_mapping = {
                'Yes': 'Yes', 'yes': 'Yes', 'YES': 'Yes',
                'No': 'No', 'no': 'No', 'NO': 'No',
                np.nan: np.nan, 'nan': np.nan, '': np.nan
            }
            df['relapse_or_progression'] = df['relapse_or_progression'].map(
                lambda x: relapse_mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan
            )
            logger.debug(f"Standardized relapse_or_progression values: {df['relapse_or_progression'].unique()}")

        # Standardize cd19_post_relapse (case-insensitive Positive/Negative/Unknown)
        if 'cd19_post_relapse' in df.columns and df['cd19_post_relapse'].notna().any():
            logger.debug("Standardizing cd19_post_relapse column")
            logger.debug(f"Raw cd19_post_relapse values: {df['cd19_post_relapse'].unique()}")
            cd19_mapping = {
                'Positive': 'Positive', 'positive': 'Positive', 'POSITIVE': 'Positive', 'pos': 'Positive',
                'Negative': 'Negative', 'negative': 'Negative', 'NEGATIVE': 'Negative', 'neg': 'Negative',
                'Unknown': 'Unknown', 'unknown': 'Unknown', 'UNKNOWN': 'Unknown', 'unk': 'Unknown',
                np.nan: np.nan, 'nan': np.nan, '': np.nan
            }
            df['cd19_post_relapse'] = df['cd19_post_relapse'].map(
                lambda x: cd19_mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan
            )
            logger.debug(f"Standardized cd19_post_relapse values: {df['cd19_post_relapse'].unique()}")

        # Standardize ethnicity (numeric codes and text)
        if 'ethnicity' in df.columns and df['ethnicity'].notna().any():
            logger.debug("Standardizing ethnicity column")
            logger.debug(f"Raw ethnicity values: {df['ethnicity'].unique()}")
            ethnicity_mapping = {
                'Hispanic or Latino': 'Hispanic or Latino', 'hispanic or latino': 'Hispanic or Latino',
                '1': 'Hispanic or Latino', '1.0': 'Hispanic or Latino',
                'Not Hispanic or Latino': 'Not Hispanic or Latino', 'not hispanic or latino': 'Not Hispanic or Latino',
                '0': 'Not Hispanic or Latino', '0.0': 'Not Hispanic or Latino',
                np.nan: np.nan, 'nan': np.nan, '': np.nan
            }
            df['ethnicity'] = df['ethnicity'].map(
                lambda x: ethnicity_mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan
            )
            logger.debug(f"Standardized ethnicity values: {df['ethnicity'].unique()}")

        # Standardize lymphodep_regimen (consolidate Flu/Cy variants)
        if 'lymphodep_regimen' in df.columns and df['lymphodep_regimen'].notna().any():
            logger.debug("Standardizing lymphodep_regimen column")
            logger.debug(f"Raw lymphodep_regimen values: {df['lymphodep_regimen'].unique()}")
            lymphodep_mapping = {
                'Fludarabine, Cyclophosphamide': 'Fludarabine, Cyclophosphamide',
                'Flu/Cy': 'Fludarabine, Cyclophosphamide',
                'Bendamustine': 'Bendamustine',
                'RICE': 'RICE',
                np.nan: np.nan, 'nan': np.nan, '': np.nan
            }
            df['lymphodep_regimen'] = df['lymphodep_regimen'].map(
                lambda x: lymphodep_mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan
            )
            logger.debug(f"Standardized lymphodep_regimen values: {df['lymphodep_regimen'].unique()}")

        # Standardize binary Yes/No columns with mixed numeric/text representations
        yes_no_mapping = {
            'Yes': 'Yes', 'yes': 'Yes', 'YES': 'Yes', '1': 'Yes', '1.0': 'Yes',
            'No': 'No', 'no': 'No', 'NO': 'No', '0': 'No', '0.0': 'No',
            np.nan: np.nan, 'nan': np.nan, '': np.nan
        }
        
        yes_no_columns = ['icans', 'iec-hs', 'icu_admission', 'prbc_infusion', 
                         'plt_transfusion', 'infection_30days', 'pt_transfusion']
        
        for col in yes_no_columns:
            if col in df.columns and df[col].notna().any():
                logger.debug(f"Standardizing {col} column")
                logger.debug(f"Raw {col} values: {df[col].unique()}")
                df[col] = df[col].map(
                    lambda x: yes_no_mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan
                )
                logger.debug(f"Standardized {col} values: {df[col].unique()}")

        # Standardize infection_type columns (remove numeric prefixes, standardize case)
        # Handles formats like: "1, Bacterial", "2, Viral", "bacterial", "CMV", etc.
        for col in ['infection_type_30days', 'infection_type_100_days']:
            if col in df.columns and df[col].notna().any():
                logger.debug(f"Standardizing {col} column")
                logger.debug(f"Raw {col} values: {df[col].unique()}")
                
                def standardize_infection_type(value):
                    if pd.isna(value):
                        return np.nan
                    
                    val_str = str(value).strip()
                    
                    # Remove numeric prefixes like "1, " or "2, "
                    import re
                    val_str = re.sub(r'^\d+[,\s]+', '', val_str)
                    
                    # Standardize common infection categories (case-insensitive)
                    val_lower = val_str.lower()
                    if val_lower == 'bacterial':
                        return 'Bacterial'
                    elif val_lower == 'viral':
                        return 'Viral'
                    elif val_lower == 'fungal':
                        return 'Fungal'
                    else:
                        # Preserve specific infection types like CMV, C diff, etc.
                        return val_str
                
                df[col] = df[col].apply(standardize_infection_type)
                logger.debug(f"Standardized {col} values: {df[col].unique()}")

        # Clean bridging_other column (remove redundant duplicates of bridging_type)
        if 'bridging_other' in df.columns and 'bridging_type' in df.columns:
            logger.debug("Cleaning bridging_other column")
            logger.debug(f"Raw bridging_other values: {df['bridging_other'].unique()}")
            
            df['bridging_other'] = df.apply(clean_bridging_other_value, axis=1)
            logger.debug(f"Cleaned bridging_other - unique values: {df['bridging_other'].nunique()}")
            logger.debug(f"Cleaned bridging_other values: {df['bridging_other'].unique()}")

        logger.info("Categorical values standardized successfully")
        return df
    except Exception as e:
        logger.error(f"Error standardizing categorical values: {e}")
        raise