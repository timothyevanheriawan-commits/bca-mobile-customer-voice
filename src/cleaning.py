import pandas as pd


def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform basic cleaning on the raw review dataset.
    """

    df = df.copy()

    # Standardize column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
    )

    # Clean review text
    df["review_text"] = (
        df["review_text"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

    # Convert data types
    df["rating"] = pd.to_numeric(
        df["rating"],
        errors="coerce",
    )

    df["review_date"] = pd.to_datetime(
        df["review_date"],
        errors="coerce",
    )

    # Remove empty reviews
    df = df[
        df["review_text"].str.len() > 0
    ]

    # Remove invalid ratings
    df = df[
        df["rating"].isin([1, 2, 3, 4, 5])
    ]

    # Remove duplicate review IDs
    if "review_id" in df.columns:
        df = df.drop_duplicates(
            subset="review_id",
            keep="first",
        )

    # Remove exact duplicate reviews
    df = df.drop_duplicates(
        subset=["review_text", "review_date"],
        keep="first",
    )

    # Sort chronologically
    df = (
        df.sort_values("review_date")
        .reset_index(drop=True)
    )

    return df