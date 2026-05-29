#!/usr/bin/env python3
import pandas as pd
import numpy as np
import os

RESP_FIELDS = [
    'cart_response_category_D30',
    'cart_response_90_days',
    'cart_response_6_mos',
    'cart_response_1_yr',
    'best_response',
]

THREE_CLASS_SUFFIX = '_3class'
SUBCAT_SUFFIX = '_subcategory'

# Mapping helpers

def normalize(val: str) -> str:
    if pd.isna(val):
        return np.nan
    s = str(val).strip().lower()
    return s

def to_three_class(val: str) -> str:
    s = normalize(val)
    # Treat missing/inevaluable/indeterminate as Minimal/No to increase usable labels
    if s is np.nan:
        return 'Minimal/No Response'
    if 'complete' in s and 'response' in s:
        return 'Complete Response'
    if 'partial' in s and 'response' in s:
        return 'Partial Response'
    if any(x in s for x in ['stable disease', 'progressive disease', 'died', 'inevaluable', 'indeterminate']):
        return 'Minimal/No Response'
    return 'Other'

def to_subcategory(val: str) -> str:
    s = normalize(val)
    if s is np.nan:
        return np.nan
    # Complete response subcats
    if 'complete' in s and 'response' in s:
        if 'mrd' in s and 'stringent' in s:
            return 'MRD Negative Stringent Complete Response'
        if 'stringent' in s:
            return 'Stringent Complete Response'
        if 'mrd' in s:
            return 'MRD Positive Complete Response'
        return 'Complete Response'
    # Partial response subcats
    if 'very good partial response' in s:
        return 'Very Good Partial Response'
    if 'partial response' in s:
        return 'Partial Response'
    # Minimal/no response subcats
    if 'stable disease' in s:
        return 'Stable Disease'
    if 'progressive disease' in s:
        return 'Progressive Disease'
    if 'died' in s:
        return 'Died without a response'
    # Other
    if 'inevaluable' in s:
        return 'Inevaluable'
    if 'indeterminate' in s:
        return 'Indeterminate'
    return 'Other'


def main():
    path = os.path.join('data', 'unified_clinical_data.csv')
    df = pd.read_csv(path)

    print('=== PRE-UNIQUE COUNTS ===')
    for f in RESP_FIELDS:
        if f in df.columns:
            print(f'\n{f}')
            print(df[f].value_counts(dropna=False))

    # Derive 3-class and subcategories
    for f in RESP_FIELDS:
        if f in df.columns:
            df[f + THREE_CLASS_SUFFIX] = df[f].apply(to_three_class)
            df[f + SUBCAT_SUFFIX] = df[f].apply(to_subcategory)

    # Save new dataset copy
    out = os.path.join('data', 'unified_clinical_data_with_3class.csv')
    df.to_csv(out, index=False)
    print(f"\nSaved: {out}")

    print('\n=== POST-UNIQUE COUNTS (3-class) ===')
    for f in RESP_FIELDS:
        col = f + THREE_CLASS_SUFFIX
        if col in df.columns:
            print(f'\n{col}')
            print(df[col].value_counts(dropna=False))

if __name__ == '__main__':
    main()
