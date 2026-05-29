import pandas as pd
import numpy as np
from uni_config import logger, JHU_FILE

def unify_datasets(unc_df, jhu_df):
    """Unify the two datasets by combining all columns in JHU/UNC column order"""
    logger.info("Unifying UNC and JHU datasets")
    try:
        # Use JHU column order to ensure output matches input datasets
        jhu_columns = pd.read_csv(JHU_FILE, sep=',', nrows=0).columns.tolist()
        logger.info(f"Using column order from JHU dataset: {len(jhu_columns)} columns")

        # Align columns for both datasets
        logger.debug("Aligning columns for UNC dataset")
        for col in jhu_columns:
            if col not in unc_df.columns:
                unc_df[col] = np.nan

        logger.debug("Aligning columns for JHU dataset")
        for col in jhu_columns:
            if col not in jhu_df.columns:
                jhu_df[col] = np.nan

        # Ensure only columns from jhu_columns are kept
        logger.debug("Reindexing datasets to match JHU column order")
        unc_df = unc_df.reindex(columns=jhu_columns)
        jhu_df = jhu_df.reindex(columns=jhu_columns)

        # Concatenate datasets
        logger.debug("Concatenating datasets")
        combined_df = pd.concat([unc_df, jhu_df], ignore_index=True)

        # Create a copy to avoid fragmentation
        logger.debug("Creating a de-fragmented copy of combined_df")
        combined_df = combined_df.copy()

        # Ensure numeric columns, but skip performance_status to preserve values
        numeric_cols = ['age_at_dx', 'age_cart', 'number_of_prior_treatments',
                        'pre_ld_wbc', 'pre_ld_anc', 'pre_car_wbc', 'pre_car_anc',
                        'days_lymphodep', 'days_of_last_followup',
                        'crs_grade', 'icans_grade']
        logger.debug(f"Converting numeric columns: {numeric_cols}")
        for col in numeric_cols:
            if col in combined_df.columns:
                combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce')
                logger.debug(f"Ensured {col} is numeric")

        logger.info("Datasets unified successfully")
        return combined_df
    except Exception as e:
        logger.error(f"Error in unifying datasets: {e}")
        raise