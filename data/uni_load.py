import pandas as pd
import numpy as np
import re
import csv
from uni_config import logger

def prepare_unc_data(file_path):
    """Load and prepare UNC dataset"""
    logger.info(f"Preparing UNC data from {file_path}")
    try:
        # Read the first few lines to inspect
        logger.debug("Reading first 5 lines of UNC CSV")
        with open(file_path, 'r', encoding='utf-8') as f:
            first_lines = [next(f).strip() for _ in range(5)]
        logger.info(f"First 5 lines of UNC CSV: {first_lines}")

        # Parse header using csv.reader to handle quoted fields
        logger.debug("Parsing header with csv.reader")
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL, skipinitialspace=True)
            header = next(reader)
        expected_columns = len(header)
        expected_column_names = header
        logger.info(f"Expected number of columns: {expected_columns}")
        logger.debug(f"Expected column names: {expected_column_names}")

        # Load CSV with strict quoting, force dtype for categorical columns
        logger.debug("Loading UNC CSV with pandas")
        try:
            df = pd.read_csv(
                file_path, sep=',', header=0, skiprows=[1], quoting=csv.QUOTE_ALL,
                low_memory=False, encoding='utf-8', on_bad_lines='warn',
                dtype={'survival_status_lfu': str, 'cart_product': str, 'performance_status': str,
                       'cns_involvement': str, 'cns_status': str, 'cns_involvement_level': str}
            )
        except Exception as e:
            logger.warning(f"Failed to load UNC CSV with quoting: {e}. Trying without strict quoting.")
            df = pd.read_csv(
                file_path, sep=',', header=0, skiprows=[1],
                low_memory=False, encoding='utf-8', on_bad_lines='warn',
                dtype={'survival_status_lfu': str, 'cart_product': str, 'performance_status': str,
                       'cns_involvement': str, 'cns_status': str, 'cns_involvement_level': str}
            )
        logger.info(f"Loaded UNC data: {df.shape[0]} rows, {df.shape[1]} columns")
        logger.debug(f"Loaded UNC columns: {list(df.columns)}")

        # Check for column count mismatch and identify missing/extra columns
        if df.shape[1] != expected_columns:
            logger.warning(f"Column count mismatch: loaded {df.shape[1]} columns, expected {expected_columns}")
            missing_cols = [col for col in expected_column_names if col not in df.columns]
            extra_cols = [col for col in df.columns if col not in expected_column_names]
            logger.warning(f"Missing columns: {missing_cols}")
            logger.warning(f"Extra columns: {extra_cols}")

        # Log first few rows for inspection
        logger.debug(f"First 3 rows of UNC data:\n{df.head(3).to_string()}")

        # Check for survival_status_lfu column
        if 'survival_status_lfu' in df.columns:
            logger.debug(f"Raw UNC survival_status_lfu values: {df['survival_status_lfu'].unique()}")
            logger.debug(f"First 5 survival_status_lfu values:\n{df[['study_id', 'survival_status_lfu']].head().to_string()}")
            nan_count = df['survival_status_lfu'].isna().sum()
            if nan_count > 0:
                logger.warning(f"Found {nan_count} nan values in survival_status_lfu")
                nan_rows = df[df['survival_status_lfu'].isna()].head(3)[['study_id', 'survival_status_lfu']].to_string()
                logger.debug(f"Sample rows with nan in survival_status_lfu:\n{nan_rows}")
        else:
            logger.error("survival_status_lfu column not found in UNC dataset")
            similar_cols = [col for col in df.columns if 'survival' in col.lower() or 'status' in col.lower()]
            logger.debug(f"Similar column names: {similar_cols}")
            if similar_cols:
                logger.warning(f"Renaming {similar_cols[0]} to survival_status_lfu")
                df.rename(columns={similar_cols[0]: 'survival_status_lfu'}, inplace=True)

        # Validate essential columns
        required_cols = ['study_id', 'age_at_dx', 'gender', 'dx_cart', 'cart_product', 'best_response']
        logger.debug(f"Validating required columns: {required_cols}")
        missing_required = [col for col in required_cols if col not in df.columns]
        if missing_required:
            logger.error(f"Missing required columns in UNC dataset: {missing_required}")
            raise ValueError(f"Missing required columns in UNC dataset: {missing_required}")

        # Filter valid rows
        logger.debug("Filtering rows with non-null study_id")
        df = df[df['study_id'].notna()]
        logger.info(f"UNC after filtering: {df.shape[0]} rows")

        # Log rows with nan in key columns
        logger.debug("Checking for nan in key columns")
        for col in required_cols:
            nan_count = df[col].isna().sum()
            if nan_count > 0:
                logger.warning(f"Found {nan_count} nan values in {col}")
                nan_rows = df[df[col].isna()].head(3)[['study_id', col]].to_string()
                logger.debug(f"Sample rows with nan in {col}:\n{nan_rows}")

        # Clean performance_status
        if 'performance_status' in df.columns:
            logger.debug("Cleaning performance_status for UNC dataset")
            logger.debug(f"Raw UNC performance_status values: {df['performance_status'].unique()}")
            mask = df['performance_status'].notna()
            if mask.any():
                # Convert to string and strip whitespace
                df.loc[mask, 'performance_status'] = df.loc[mask, 'performance_status'].astype(str).str.strip()
                # Map values: extract number if it's 0, 1, 2, 3; else NaN
                def map_performance_status(x):
                    if re.match(r'^(0|1|2|3)(\s*,.*)?$', x):
                        return float(x[0])
                    return np.nan
                df.loc[mask, 'performance_status'] = df.loc[mask, 'performance_status'].apply(map_performance_status)
                logger.debug(f"Cleaned performance_status values: {df['performance_status'].unique()}")

        # Clean number_of_prior_treatments
        if 'number_of_prior_treatments' in df.columns:
            logger.debug("Cleaning number_of_prior_treatments for UNC dataset")
            logger.debug(f"Raw UNC number_of_prior_treatments values: {df['number_of_prior_treatments'].unique()}")
            mask = df['number_of_prior_treatments'].notna()
            if mask.any():
                # Convert to string and strip whitespace
                df.loc[mask, 'number_of_prior_treatments'] = df.loc[mask, 'number_of_prior_treatments'].astype(str).str.strip()
                # Map values: handle numeric, '3+ lines', '2 lines', etc.
                def map_prior_treatments(x):
                    x = x.strip()
                    # Handle '3+' and variants
                    if re.match(r'^3\+(\s*lines)?$', x, re.IGNORECASE) or x in ['3+ lines', '3 + lines', '3+lines']:
                        return 4
                    # Handle '2 lines'
                    if re.match(r'^2(\s*lines)?$', x, re.IGNORECASE):
                        return 2
                    # Handle '1 lines'
                    if re.match(r'^1(\s*lines)?$', x, re.IGNORECASE):
                        return 1
                    # Handle numeric values
                    if re.match(r'^\d+$', x):
                        try:
                            return int(x)
                        except ValueError:
                            return np.nan
                    # Handle '+lines' or invalid
                    logger.debug(f"Unmapped UNC number_of_prior_treatments value: '{x}'")
                    return np.nan
                df.loc[mask, 'number_of_prior_treatments'] = df.loc[mask, 'number_of_prior_treatments'].apply(map_prior_treatments)
                logger.debug(f"Cleaned number_of_prior_treatments values: {df['number_of_prior_treatments'].unique()}")
                logger.debug(f"First 5 number_of_prior_treatments values:\n{df[['study_id', 'number_of_prior_treatments']].head().to_string()}")

        # Add metadata column
        logger.debug("Adding unified_id column")
        df['unified_id'] = 'U' + df['study_id'].astype(str).str.zfill(3)

        # Convert numeric columns
        numeric_cols = ['age_at_dx', 'age_cart', 'number_of_prior_treatments',
                        'pre_ld_wbc', 'pre_ld_anc', 'pre_car_wbc', 'pre_car_anc',
                        'days_lymphodep', 'days_of_last_followup',
                        'crs_grade', 'icans_grade']
        logger.debug(f"Converting numeric columns: {numeric_cols}")
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                logger.debug(f"Converted {col} to numeric")

        logger.info("UNC data preparation completed successfully")
        return df
    except Exception as e:
        logger.error(f"Error loading UNC data: {e}")
        return pd.DataFrame()

def prepare_jhu_data(file_path):
    """Load and prepare JHU dataset"""
    logger.info(f"Preparing JHU data from {file_path}")
    try:
        # Load CSV, skipping the description row, force dtype for categorical columns
        logger.debug("Loading JHU CSV with pandas, skipping description row")
        df = pd.read_csv(
            file_path, sep=',', skiprows=[1], low_memory=False, encoding='utf-8', on_bad_lines='warn',
            dtype={'performance_status': str, 'survival_status_lfu': str, 'cart_product': str,
                   'cns_involvement': str, 'cns_status': str, 'cns_involvement_level': str}
        )
        logger.info(f"Loaded JHU data: {df.shape[0]} rows, {df.shape[1]} columns")
        logger.debug(f"JHU columns: {list(df.columns)}")

        # Log first few rows for inspection
        logger.debug(f"First 3 rows of JHU data:\n{df.head(3).to_string()}")

        # Check for duplicate study_id
        logger.debug("Checking for duplicate study_id in JHU dataset")
        duplicate_ids = df[df['study_id'].duplicated()]['study_id'].tolist()
        if duplicate_ids:
            logger.warning(f"Duplicate study_id found in JHU dataset: {duplicate_ids}")
        # Check for blank rows
        blank_rows = df[df['study_id'].isna()]
        if not blank_rows.empty:
            logger.warning(f"Found {len(blank_rows)} blank rows in JHU dataset:\n{blank_rows.head(3).to_string()}")

        # Validate essential columns
        required_cols = ['study_id', 'age_at_dx', 'gender', 'dx_cart', 'cart_product', 'best_response']
        logger.debug(f"Validating required columns: {required_cols}")
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing required columns in JHU dataset: {missing_cols}")
            raise ValueError(f"Missing required columns in JHU dataset: {missing_cols}")

        # Filter valid rows
        logger.debug("Filtering rows with non-null study_id")
        df = df[df['study_id'].notna()]
        logger.info(f"JHU after filtering: {df.shape[0]} rows")

        # Check for unexpected row count
        if df.shape[0] != 125:
            logger.warning(f"Unexpected JHU row count: {df.shape[0]}, expected 125")

        # Log rows with nan in key columns
        logger.debug("Checking for nan in key columns")
        for col in required_cols:
            nan_count = df[col].isna().sum()
            if nan_count > 0:
                logger.warning(f"Found {nan_count} nan values in {col}")

        # Check for survival_status_lfu column
        if 'survival_status_lfu' in df.columns:
            logger.debug(f"Raw JHU survival_status_lfu values: {df['survival_status_lfu'].unique()}")
            logger.debug(f"First 5 survival_status_lfu values:\n{df[['study_id', 'survival_status_lfu']].head().to_string()}")
            nan_count = df['survival_status_lfu'].isna().sum()
            if nan_count > 0:
                logger.warning(f"Found {nan_count} nan values in survival_status_lfu")
        else:
            logger.error("survival_status_lfu column not found in JHU dataset")
            similar_cols = [col for col in df.columns if 'survival' in col.lower() or 'status' in col.lower()]
            logger.debug(f"Similar column names: {similar_cols}")
            if similar_cols:
                logger.warning(f"Renaming {similar_cols[0]} to survival_status_lfu")
                df.rename(columns={similar_cols[0]: 'survival_status_lfu'}, inplace=True)

        # Check for performance_status column
        logger.debug("Checking for performance_status column")
        perf_col = None
        if 'performance_status' in df.columns:
            perf_col = 'performance_status'
        else:
            # Search for similar column names
            possible_cols = [col for col in df.columns if 'performance' in col.lower() and 'status' in col.lower()]
            if possible_cols:
                perf_col = possible_cols[0]
                logger.warning(f"performance_status not found; using {perf_col} instead")
                df.rename(columns={perf_col: 'performance_status'}, inplace=True)
            else:
                logger.error("performance_status column not found in JHU dataset")
                logger.debug(f"Available columns: {list(df.columns)}")
                logger.debug(f"Similar column names: {possible_cols}")

        if perf_col:
            logger.debug("Cleaning performance_status for JHU dataset")
            logger.debug(f"Raw JHU performance_status values: {df['performance_status'].unique()}")
            logger.debug(f"First 5 performance_status values:\n{df[['study_id', 'performance_status']].head().to_string()}")
            # Ensure performance_status is string
            df['performance_status'] = df['performance_status'].astype(str).str.strip()
            # Map values: 0, 1, 2, 3 to numeric; N/A to NaN; others to NaN
            def map_performance_status(x):
                if x.lower() in ['nan', 'n/a', '']:
                    return np.nan
                try:
                    val = float(x)
                    if val in [0, 1, 2, 3]:
                        return val
                    logger.debug(f"Unmapped JHU performance_status value: '{x}'")
                    return np.nan
                except (ValueError, TypeError):
                    logger.debug(f"Invalid JHU performance_status value: '{x}'")
                    return np.nan
            df['performance_status'] = df['performance_status'].apply(map_performance_status)
            logger.debug(f"Cleaned performance_status values: {df['performance_status'].unique()}")

        # Add metadata column
        logger.debug("Adding unified_id column")
        df['unified_id'] = 'J' + df['study_id'].str.replace('JH', '', regex=False).str.zfill(3)

        # Convert numeric columns
        numeric_cols = ['age_at_dx', 'age_cart', 'number_of_prior_treatments',
                        'pre_ld_wbc', 'pre_ld_anc', 'pre_car_wbc', 'pre_car_anc',
                        'days_lymphodep', 'days_of_last_followup',
                        'crs_grade', 'icans_grade']
        logger.debug(f"Converting numeric columns: {numeric_cols}")
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                logger.debug(f"Converted {col} to numeric")

        logger.info("JHU data preparation completed successfully")
        return df
    except Exception as e:
        logger.error(f"Error loading JHU data: {e}")
        return pd.DataFrame()