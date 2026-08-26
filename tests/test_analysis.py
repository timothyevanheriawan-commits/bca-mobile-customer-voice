"""Unit tests for src.analysis.

Covers the functions that feed the priority table directly:
issue_frequency_table, monthly_issue_share, issue_trend_direction,
issue_cooccurrence_table, issue_rating_matrix. Built on small, hand-built
DataFrames rather than the committed dataset, so these keep passing (or
fail loudly and specifically) regardless of what's currently in
data/processed/.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.analysis import (
    issue_cooccurrence_table,
    issue_frequency_table,
    issue_rating_matrix,
    issue_trend_direction,
    monthly_issue_share,
)


def _reviews() -> pd.DataFrame:
    return pd.DataFrame([
        {"rating": 1, "rating_group": "negative", "issues": "app_performance,login_otp_access"},
        {"rating": 2, "rating_group": "negative", "issues": "app_performance"},
        {"rating": 1, "rating_group": "negative", "issues": "login_otp_access"},
        {"rating": 5, "rating_group": "positive", "issues": ""},
        {"rating": 5, "rating_group": "positive", "issues": ""},
    ])


# --- issue_frequency_table --------------------------------------------------

def test_frequency_table_counts_mentions_per_category():
    freq = issue_frequency_table(_reviews())
    counts = dict(zip(freq["issue"], freq["n_mentions"]))
    assert counts["app_performance"] == 2
    assert counts["login_otp_access"] == 2


def test_frequency_table_share_of_negative_reviews_uses_negative_denominator():
    freq = issue_frequency_table(_reviews())
    row = freq[freq["issue"] == "app_performance"].iloc[0]
    # 2 mentions / 3 negative reviews
    assert row["share_of_negative_reviews"] == pytest.approx(2 / 3, rel=1e-3)


def test_frequency_table_pct_from_1_2_star():
    freq = issue_frequency_table(_reviews())
    row = freq[freq["issue"] == "login_otp_access"].iloc[0]
    # both tagged reviews are 1-star
    assert row["pct_from_1_2_star"] == 1.0


def test_frequency_table_empty_input_returns_empty_frame():
    empty = pd.DataFrame(columns=["issues", "rating", "rating_group"])
    freq = issue_frequency_table(empty)
    assert freq.empty


# --- monthly_issue_share -----------------------------------------------------

def _monthly_reviews() -> pd.DataFrame:
    return pd.DataFrame([
        {"review_date": pd.Timestamp("2026-05-05"), "issues": "app_performance"},
        {"review_date": pd.Timestamp("2026-05-10"), "issues": ""},
        {"review_date": pd.Timestamp("2026-06-01"), "issues": "app_performance"},
        {"review_date": pd.Timestamp("2026-06-02"), "issues": "app_performance"},
    ])


def test_monthly_share_is_fraction_of_that_months_total():
    monthly = monthly_issue_share(_monthly_reviews())
    may_row = monthly[(monthly["month"] == "2026-05") & (monthly["issue"] == "app_performance")].iloc[0]
    june_row = monthly[(monthly["month"] == "2026-06") & (monthly["issue"] == "app_performance")].iloc[0]
    assert may_row["share_of_month"] == pytest.approx(0.5)
    assert june_row["share_of_month"] == pytest.approx(1.0)


# --- issue_trend_direction ---------------------------------------------------

def test_trend_direction_flags_insufficient_data_below_min_months():
    monthly = monthly_issue_share(_monthly_reviews())  # only 2 distinct months
    trend = issue_trend_direction(monthly, min_months=4)
    assert set(trend["trend"]) == {"insufficient_data"}


def test_trend_direction_detects_increasing_share():
    months = ["2026-01", "2026-02", "2026-03", "2026-04"]
    shares = [0.05, 0.05, 0.30, 0.30]  # second half clearly higher
    monthly = pd.DataFrame({
        "month": months,
        "issue": ["app_performance"] * 4,
        "n_mentions": [1, 1, 1, 1],
        "share_of_month": shares,
    })
    trend = issue_trend_direction(monthly, min_months=4)
    assert trend.iloc[0]["trend"] == "increasing"


def test_trend_direction_detects_stable_within_20_percent():
    months = ["2026-01", "2026-02", "2026-03", "2026-04"]
    shares = [0.10, 0.10, 0.11, 0.11]  # well within +/-20%
    monthly = pd.DataFrame({
        "month": months,
        "issue": ["app_performance"] * 4,
        "n_mentions": [1, 1, 1, 1],
        "share_of_month": shares,
    })
    trend = issue_trend_direction(monthly, min_months=4)
    assert trend.iloc[0]["trend"] == "stable"


# --- issue_cooccurrence_table -------------------------------------------------

def test_cooccurrence_counts_paired_tags_on_same_review():
    co = issue_cooccurrence_table(_reviews())
    assert len(co) == 1
    row = co.iloc[0]
    assert {row["issue_a"], row["issue_b"]} == {"app_performance", "login_otp_access"}
    assert row["n_reviews"] == 1


def test_cooccurrence_empty_when_no_review_has_two_tags():
    single_tag_df = pd.DataFrame([
        {"issues": "app_performance"},
        {"issues": "login_otp_access"},
    ])
    co = issue_cooccurrence_table(single_tag_df)
    assert co.empty


# --- issue_rating_matrix ------------------------------------------------------

def test_rating_matrix_star_columns_sum_to_n_mentions():
    matrix = issue_rating_matrix(_reviews())
    row = matrix[matrix["issue"] == "app_performance"].iloc[0]
    star_sum = sum(row[f"star_{s}"] for s in range(1, 6))
    assert star_sum == row["n_mentions"]