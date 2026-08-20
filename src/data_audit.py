import pandas as pd


def audit_reviews(df: pd.DataFrame) -> dict:
    """
    Perform a basic data-quality audit.

    Parameters
    ----------
    df : pd.DataFrame
        Review dataset.

    Returns
    -------
    dict
        Audit results.
    """

    audit = {}

    # --------------------------------------------------------
    # Dataset size
    # --------------------------------------------------------

    audit["row_count"] = len(df)
    audit["column_count"] = len(df.columns)

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    audit["missing_values"] = (
        df.isna()
        .sum()
        .to_dict()
    )

    # --------------------------------------------------------
    # Duplicate review IDs
    # --------------------------------------------------------

    if "review_id" in df.columns:

        audit["duplicate_review_ids"] = int(
            df["review_id"]
            .duplicated()
            .sum()
        )

    else:

        audit["duplicate_review_ids"] = None

    # --------------------------------------------------------
    # Duplicate review text
    # --------------------------------------------------------

    if "review_text" in df.columns:

        audit["duplicate_review_text"] = int(
            df["review_text"]
            .duplicated()
            .sum()
        )

    else:

        audit["duplicate_review_text"] = None

    # --------------------------------------------------------
    # Empty reviews
    # --------------------------------------------------------

    if "review_text" in df.columns:

        text = (
            df["review_text"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        audit["empty_reviews"] = int(
            (text == "").sum()
        )

    else:

        audit["empty_reviews"] = None

    # --------------------------------------------------------
    # Rating validation
    # --------------------------------------------------------

    if "rating" in df.columns:

        audit["invalid_ratings"] = int(
            (~df["rating"].isin([1, 2, 3, 4, 5]))
            .sum()
        )

        audit["rating_distribution"] = (
            df["rating"]
            .value_counts()
            .sort_index()
            .to_dict()
        )

    else:

        audit["invalid_ratings"] = None
        audit["rating_distribution"] = {}

    # --------------------------------------------------------
    # Date validation
    # --------------------------------------------------------

    if "review_date" in df.columns:

        dates = pd.to_datetime(
            df["review_date"],
            errors="coerce",
        )

        audit["invalid_dates"] = int(
            dates.isna().sum()
        )

        if dates.notna().any():

            audit["earliest_review"] = dates.min()
            audit["latest_review"] = dates.max()

        else:

            audit["earliest_review"] = None
            audit["latest_review"] = None

    else:

        audit["invalid_dates"] = None
        audit["earliest_review"] = None
        audit["latest_review"] = None

    return audit


def print_audit(audit: dict) -> None:
    """Print audit results in a readable format."""

    print()
    print("=" * 60)
    print("DATA QUALITY AUDIT")
    print("=" * 60)

    print(f"Rows: {audit['row_count']:,}")
    print(f"Columns: {audit['column_count']}")

    print()
    print(
        "Duplicate review IDs:",
        audit["duplicate_review_ids"],
    )

    print(
        "Duplicate review text:",
        audit["duplicate_review_text"],
    )

    print(
        "Empty reviews:",
        audit["empty_reviews"],
    )

    print(
        "Invalid ratings:",
        audit["invalid_ratings"],
    )

    print(
        "Invalid dates:",
        audit["invalid_dates"],
    )

    print()
    print("Date range:")

    print(
        f"  {audit['earliest_review']} "
        f"→ "
        f"{audit['latest_review']}"
    )

    print()
    print("Rating distribution:")

    for rating, count in audit[
        "rating_distribution"
    ].items():

        print(
            f"  {rating} star: {count:,}"
        )

    print()
    print("Missing values:")

    for column, count in audit[
        "missing_values"
    ].items():

        print(
            f"  {column}: {count:,}"
        )