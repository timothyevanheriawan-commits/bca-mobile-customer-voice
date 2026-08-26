"""Unit tests for src.cleaning.clean_reviews.

These were previously an empty stub. A rule-based, "auditable" pipeline is
undercut if the cleaning step that everything downstream depends on has no
coverage - these tests exist to make that claim actually checkable, not
just to pad a test count.
"""

from __future__ import annotations

import pandas as pd

from src.cleaning import clean_reviews


def _raw(**overrides) -> pd.DataFrame:
    """One valid raw row, with any field overridden per test."""
    row = {
        "review_id": "r1",
        "rating": 5,
        "review_date": "2026-05-01",
        "review_text": "Aplikasi bagus",
        "thumbs_up": 0,
    }
    row.update(overrides)
    return pd.DataFrame([row])


def test_lowercases_and_strips_column_names():
    df = _raw()
    df.columns = [c.upper() + "  " for c in df.columns]
    out = clean_reviews(df)
    assert list(out.columns) == ["review_id", "rating", "review_date", "review_text", "thumbs_up"]


def test_collapses_internal_whitespace_in_review_text():
    df = _raw(review_text="Aplikasi   bagus\n\nsekali")
    out = clean_reviews(df)
    assert out.iloc[0]["review_text"] == "Aplikasi bagus sekali"


def test_drops_rows_with_empty_review_text():
    df = pd.concat([_raw(review_id="r1"), _raw(review_id="r2", review_text="   ")], ignore_index=True)
    out = clean_reviews(df)
    assert list(out["review_id"]) == ["r1"]


def test_drops_rows_with_invalid_rating():
    df = pd.concat([_raw(review_id="r1", rating=5), _raw(review_id="r2", rating=7)], ignore_index=True)
    out = clean_reviews(df)
    assert list(out["review_id"]) == ["r1"]


def test_coerces_non_numeric_rating_to_nan_and_drops_it():
    df = _raw(rating="five")
    out = clean_reviews(df)
    assert len(out) == 0


def test_drops_duplicate_review_ids_keeping_first():
    df = pd.concat([
        _raw(review_id="r1", review_text="first version"),
        _raw(review_id="r1", review_text="different text, same id"),
    ], ignore_index=True)
    out = clean_reviews(df)
    assert len(out) == 1
    assert out.iloc[0]["review_text"] == "first version"


def test_drops_exact_duplicate_text_and_date_without_review_id():
    df = pd.concat([_raw(), _raw()], ignore_index=True).drop(columns="review_id")
    out = clean_reviews(df)
    assert len(out) == 1


def test_review_date_is_parsed_to_datetime():
    df = _raw(review_date="2026-05-01")
    out = clean_reviews(df)
    assert pd.api.types.is_datetime64_any_dtype(out["review_date"])


def test_unparseable_date_becomes_nat_not_an_error():
    df = _raw(review_date="not a date")
    out = clean_reviews(df)
    assert pd.isna(out.iloc[0]["review_date"])


def test_output_sorted_chronologically():
    df = pd.concat([
        _raw(review_id="r1", review_date="2026-06-01", review_text="later"),
        _raw(review_id="r2", review_date="2026-05-01", review_text="earlier"),
    ], ignore_index=True)
    out = clean_reviews(df)
    assert list(out["review_id"]) == ["r2", "r1"]


def test_does_not_mutate_the_input_dataframe():
    df = _raw(review_text="  extra   spaces  ")
    original_text = df.iloc[0]["review_text"]
    clean_reviews(df)
    assert df.iloc[0]["review_text"] == original_text