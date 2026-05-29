"""Tests for data/ dx_cart normalization and conservative backfill."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_DATA_DIR = Path(__file__).resolve().parents[3] / "data"
if str(_DATA_DIR) not in sys.path:
    sys.path.insert(0, str(_DATA_DIR))

from uni_standardize_helpers import (  # noqa: E402
    backfill_dx_cart,
    infer_dx_cart_from_subtype_fields,
    normalize_dx_cart_value,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        (1.0, "Lymphoma"),
        (3.0, "MM"),
        ("1. Lymphoma", "Lymphoma"),
        ("3. MM", "MM"),
        ("1, Lymphoma | 2, ALL | 3, MM | 4, Other", np.nan),
        (np.nan, np.nan),
    ],
)
def test_normalize_dx_cart_value(raw, expected):
    result = normalize_dx_cart_value(raw)
    if pd.isna(expected):
        assert pd.isna(result)
    else:
        assert result == expected


def test_backfill_does_not_overwrite_existing():
    df = pd.DataFrame(
        {
            "study_id": ["1"],
            "dx_cart": ["ALL"],
            "lymphoma_subtype": ["DLBCL, n.o.s."],
        }
    )
    out = backfill_dx_cart(df)
    assert out.loc[0, "dx_cart"] == "ALL"
    assert out.loc[0, "dx_cart_source"] == "redcap"


def test_backfill_lymphoma_subtype_allowlist():
    df = pd.DataFrame(
        {
            "study_id": ["JH1"],
            "dx_cart": [np.nan],
            "lymphoma_subtype": ["MCL"],
        }
    )
    out = backfill_dx_cart(df)
    assert out.loc[0, "dx_cart"] == "Lymphoma"
    assert out.loc[0, "dx_cart_source"] == "backfill:lymphoma_subtype"


def test_backfill_mm_in_lymphoma_subtype_column():
    df = pd.DataFrame(
        {
            "study_id": ["JH2"],
            "dx_cart": [np.nan],
            "lymphoma_subtype": ["MM"],
        }
    )
    out = backfill_dx_cart(df)
    assert out.loc[0, "dx_cart"] == "MM"
    assert out.loc[0, "dx_cart_source"] == "backfill:lymphoma_subtype"


def test_backfill_conflict_leaves_nan():
    row = pd.Series(
        {
            "all_subtype": "Ph-negative",
            "lymphoma_subtype": "MCL",
        }
    )
    dx, source = infer_dx_cart_from_subtype_fields(row)
    assert pd.isna(dx)
    assert source == "backfill:conflict"
