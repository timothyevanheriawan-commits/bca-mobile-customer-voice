"""
Cached loaders that turn the raw pipeline outputs into what the dashboard
pages need.

Deliberately re-computes frequency/trend/validation/priority tables live
from the committed CSVs on every load (cached by Streamlit, not baked into
a static file) - the whole point of `src/prioritization.py`'s caveat system
is that it should reflect whatever is actually sitting in
`data/validation/*.csv` right now. If a category's precision file is stale
or under 0.8, the dashboard should say so, not repeat a number from an old
notebook run or handoff doc.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis import (
    issue_frequency_table,
    issue_trend_direction,
    monthly_issue_share,
)
from src.prioritization import build_priority_table, validation_status_table

PROCESSED_PATH = PROJECT_ROOT / "data" / "processed" / "bca_mobile_reviews_classified.csv"
VALIDATION_DIR = PROJECT_ROOT / "data" / "validation"


@st.cache_data
def load_reviews() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_PATH, parse_dates=["review_date"])
    df["issues"] = df["issues"].fillna("")
    return df


@st.cache_data
def load_frequency(_df: pd.DataFrame) -> pd.DataFrame:
    return issue_frequency_table(_df)


@st.cache_data
def load_monthly_share(_df: pd.DataFrame) -> pd.DataFrame:
    return monthly_issue_share(_df)


@st.cache_data
def load_trend(_monthly_df: pd.DataFrame) -> pd.DataFrame:
    return issue_trend_direction(_monthly_df, min_months=4)


@st.cache_data
def load_validation() -> pd.DataFrame:
    return validation_status_table(VALIDATION_DIR)


@st.cache_data
def load_priority(_freq_df: pd.DataFrame, _trend_df: pd.DataFrame, _val_df: pd.DataFrame) -> pd.DataFrame:
    return build_priority_table(_freq_df, _trend_df, _val_df)


def load_all() -> dict[str, pd.DataFrame]:
    """One call that returns every table a page might need, computed in the
    correct dependency order."""
    df = load_reviews()
    monthly_df = load_monthly_share(df)
    trend_df = load_trend(monthly_df)
    validation_df = load_validation()
    frequency_df = load_frequency(df)
    priority_df = load_priority(frequency_df, trend_df, validation_df)

    return {
        "reviews": df,
        "monthly": monthly_df,
        "trend": trend_df,
        "validation": validation_df,
        "frequency": frequency_df,
        "priority": priority_df,
    }
