#!/usr/bin/env python3
# Script to validate unified_clinical_data.csv and assess field fullness
#
# Validates row/column counts, checks JHU duplicates, and computes fullness for each field.
# Outputs:
# 1. Top 20 most completed fields (CSV format for Google Sheets)
# 2. Top 40 least completed fields (CSV format for Google Sheets)
# 3. Full list of columns in original sample order (CSV format for Google Sheets)
# 4. Fullness table saved as fullness_table.csv (CSV format)
#
# Usage: python unified_dataset_validation.py
# Input: unified_clinical_data.csv
# Output: Console output (CSV), fullness_table.csv

import pandas as pd
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('validate_unified_dataset.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def validate_dataset(df, expected_rows=270, expected_cols=192):
    """Validate dataset structure and JHU/UNC row counts."""
    logger.info("Validating dataset structure")

    # Check row count
    actual_rows = df.shape[0]
    if actual_rows != expected_rows:
        logger.warning(f"Row count mismatch: got {actual_rows}, expected {expected_rows}")
    else:
        logger.info(f"Row count validated: {actual_rows} rows")

    # Check column count
    actual_cols = df.shape[1]
    if actual_cols != expected_cols:
        logger.warning(f"Column count mismatch: got {actual_cols}, expected {expected_cols}")
    else:
        logger.info(f"Column count validated: {actual_cols} columns")

    # Check JHU row count if Center exists
    if 'Center' in df.columns:
        jhu_rows = df[df['Center'] == 'JHU'].shape[0]
        expected_jhu_rows = 125
        if jhu_rows != expected_jhu_rows:
            logger.warning(f"JHU row count mismatch: got {jhu_rows}, expected {expected_jhu_rows}")
            jhu_df = df[df['Center'] == 'JHU']
            # Check duplicates
            duplicates = jhu_df[jhu_df['study_id'].duplicated()]['study_id'].tolist()
            if duplicates:
                logger.warning(f"Duplicate study_id in JHU: {duplicates}")
            # Check blank rows
            blank_rows = jhu_df[jhu_df['study_id'].isna()]
            if not blank_rows.empty:
                logger.warning(f"Blank rows in JHU: {len(blank_rows)}")
                logger.debug(f"Sample blank rows:\n{blank_rows.head().to_string()}")
        else:
            logger.info(f"JHU row count validated: {jhu_rows} rows")

        # Check UNC row count
        unc_rows = df[df['Center'] == 'UNC'].shape[0]
        expected_unc_rows = 145
        if unc_rows != expected_unc_rows:
            logger.warning(f"UNC row count mismatch: got {unc_rows}, expected {expected_unc_rows}")
        else:
            logger.info(f"UNC row count validated: {unc_rows} rows")
    else:
        logger.warning("Column 'Center' not found in dataset; skipping JHU/UNC row validation")

    # Validate key fields for NaN values and log patient 51
    key_cols = ['cart_product', 'dx_cart', 'best_response']
    for col in key_cols:
        if col in df.columns:
            # Log raw values for dx_cart to diagnose NaN issue
            if col == 'dx_cart':
                logger.debug(f"Raw {col} values: {df[col].unique()}")
            nan_rows = df[df[col].isna()][['study_id', col]]
            if not nan_rows.empty:
                logger.warning(f"Found {len(nan_rows)} NaN values in {col}")
                logger.debug(f"Rows with NaN in {col}:\n{nan_rows.to_string()}")
            # Check specifically for patient 51
            if 'study_id' in df.columns and '51' in df['study_id'].values:
                patient_51 = df[df['study_id'] == '51'][[col]]
                logger.debug(f"Patient 51 {col} value: {patient_51.to_string()}")
                if patient_51[col].isna().any():
                    logger.warning(f"Patient 51 has NaN in {col}: {patient_51.to_string()}")

def compute_fullness(df):
    """Compute fullness for each column for overall, UNC, and JHU datasets, return tables in original column order with numeration."""
    logger.info("Computing field fullness")
    total_rows = df.shape[0]

    # Overall fullness
    fullness = df.notna().sum() / total_rows * 100

    # UNC and JHU fullness if Center exists
    unc_fullness = pd.Series(0.0, index=df.columns)
    jhu_fullness = pd.Series(0.0, index=df.columns)
    if 'Center' in df.columns:
        unc_df = df[df['Center'] == 'UNC']
        jhu_df = df[df['Center'] == 'JHU']
        unc_total_rows = unc_df.shape[0]
        jhu_total_rows = jhu_df.shape[0]
        if unc_total_rows > 0:
            unc_fullness = unc_df.notna().sum() / unc_total_rows * 100
        if jhu_total_rows > 0:
            jhu_fullness = jhu_df.notna().sum() / jhu_total_rows * 100

    # Round fullness values to 2 decimal places
    fullness = fullness.round(2)
    unc_fullness = unc_fullness.round(2)
    jhu_fullness = jhu_fullness.round(2)

    # Fullness table in original column order
    fullness_df = pd.DataFrame({
        'No.': range(1, len(df.columns) + 1),  # 1-based numeration
        'Column': df.columns,
        'Non-Null Count': df.notna().sum(),
        'Fullness (%)': fullness,
        'UNC Fullness (%)': unc_fullness,
        'JHU Fullness (%)': jhu_fullness
    })

    # Sorted fullness table for top/bottom reports
    sorted_fullness_df = fullness_df.sort_values('Fullness (%)', ascending=False).reset_index(drop=True)
    sorted_fullness_df['No.'] = range(1, len(sorted_fullness_df) + 1)  # Reassign numbers for sorted order

    return fullness_df, sorted_fullness_df

def main():
    logger.info("Starting validation and fullness analysis")
    try:
        # Load dataset
        logger.debug("Loading unified_clinical_data.csv")
        df = pd.read_csv('unified_clinical_data.csv', sep=',', low_memory=False)

        # Validate structure
        validate_dataset(df)

        # Compute fullness
        fullness_df, sorted_fullness_df = compute_fullness(df)

        # Output top 20 most completed fields (CSV)
        logger.info("\nTop 20 Most Completed Fields:")
        print("\nTop 20 Most Completed Fields:")
        print(sorted_fullness_df.head(20)[['No.', 'Column', 'Non-Null Count', 'Fullness (%)']].to_csv(sep=',', index=False))

        # Output top 40 least completed fields (CSV)
        logger.info("\nTop 40 Least Completed Fields:")
        print("\nTop 40 Least Completed Fields:")
        print(sorted_fullness_df.tail(40)[['No.', 'Column', 'Non-Null Count', 'Fullness (%)']].to_csv(sep=',', index=False))

        # Output full list in original sample order (CSV)
        logger.info("\nFull List of Columns in Original Sample Order:")
        print("\nFull List of Columns in Original Sample Order:")
        print(fullness_df[['No.', 'Column', 'Non-Null Count', 'Fullness (%)', 'UNC Fullness (%)', 'JHU Fullness (%)']].to_csv(sep=',', index=False))

        # Save fullness table (CSV)
        output_file = 'fullness_table.csv'
        fullness_df.to_csv(output_file, sep=',', index=False)
        logger.info(f"Fullness table saved to {output_file}")

        # Log sample rows with NaN in key columns
        key_cols = ['dx_cart', 'cart_product', 'best_response']
        for col in key_cols:
            if col in df.columns:
                nan_count = df[col].isna().sum()
                if nan_count > 0:
                    logger.warning(f"Found {nan_count} NaN values in {col}")
                    nan_rows = df[df[col].isna()][['study_id', col]].head(3)
                    logger.debug(f"Sample rows with NaN in {col}:\n{nan_rows.to_string()}")

        logger.info("Validation and fullness analysis completed")
    except Exception as e:
        logger.error(f"Error in validation: {e}")
        raise

if __name__ == "__main__":
    main()