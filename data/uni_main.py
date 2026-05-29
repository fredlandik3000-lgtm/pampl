import pandas as pd
from uni_config import logger, UNC_FILE, JHU_FILE, OUTPUT_FILE
from uni_load import prepare_unc_data, prepare_jhu_data
from uni_standardize import clean_column_values, standardize_categorical_values
from uni_standardize_helpers import backfill_dx_cart
from uni_unify import unify_datasets

def main():
    logger.info("Starting dataset unification process")
    try:
        unc_df = prepare_unc_data(UNC_FILE)
        jhu_df = prepare_jhu_data(JHU_FILE)

        if unc_df.empty or jhu_df.empty:
            logger.error("Failed to load data. Exiting.")
            return

        logger.info(f"UNC dataset: {unc_df.shape[0]} rows, {unc_df.shape[1]} variables")
        logger.info(f"JHU dataset: {jhu_df.shape[0]} rows, {jhu_df.shape[1]} variables")

        # Apply standardization
        unc_df = clean_column_values(unc_df)
        unc_df = standardize_categorical_values(unc_df)
        unc_df = backfill_dx_cart(unc_df, logger=logger)
        jhu_df = clean_column_values(jhu_df)
        jhu_df = standardize_categorical_values(jhu_df)
        jhu_df = backfill_dx_cart(jhu_df, logger=logger)

        unified_df = unify_datasets(unc_df, jhu_df)
        if "dx_cart_source" in unc_df.columns and "dx_cart_source" in jhu_df.columns:
            unified_df["dx_cart_source"] = pd.concat(
                [unc_df["dx_cart_source"], jhu_df["dx_cart_source"]],
                ignore_index=True,
            )

        logger.info("\nDataset Summary:")
        logger.info(f"Total patients: {unified_df.shape[0]}")
        logger.info(f"Total columns: {unified_df.shape[1]}")

        if 'dx_cart' in unified_df.columns:
            logger.info("\nDiagnosis Distribution:")
            dx_counts = unified_df['dx_cart'].value_counts(dropna=False)
            for dx, count in dx_counts.items():
                logger.info(f"  {dx}: {count} patients")

        if 'cart_product' in unified_df.columns:
            logger.info("\nCAR-T Product Distribution:")
            product_counts = unified_df['cart_product'].value_counts(dropna=False)
            for product, count in product_counts.items():
                logger.info(f"  {product}: {count} patients")

        if 'best_response' in unified_df.columns:
            logger.info("\nBest Response Distribution:")
            response_counts = unified_df['best_response'].value_counts()
            for response, count in response_counts.items():
                logger.info(f"  {response}: {count} patients")

        if 'race' in unified_df.columns:
            logger.info("\nRace Distribution:")
            race_counts = unified_df['race'].value_counts(dropna=False)
            for race, count in race_counts.items():
                logger.info(f"  Race: {race}: {count} patients")

        if 'survival_status_lfu' in unified_df.columns:
            logger.info("\nSurvival Status Distribution:")
            survival_counts = unified_df['survival_status_lfu'].value_counts(dropna=False)
            for status, count in survival_counts.items():
                logger.info(f"  {status}: {count} patients")

        logger.debug(f"Saving unified dataset to {OUTPUT_FILE}")
        unified_df.to_csv(OUTPUT_FILE, sep=',', index=False)
        logger.info(f"Unified dataset saved to {OUTPUT_FILE}")

        logger.info("Dataset unification process completed successfully")
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()