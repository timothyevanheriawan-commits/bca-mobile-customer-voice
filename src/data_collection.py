import time

import pandas as pd
from google_play_scraper import reviews, Sort

from src.config import (
    APP_ID,
    LANGUAGE,
    COUNTRY,
    MAX_REVIEWS,
    BATCH_SIZE,
    REQUEST_DELAY,
    RAW_REVIEWS_FILE,
)


def collect_reviews() -> pd.DataFrame:
    """
    Collect BCA Mobile reviews from Google Play.

    Returns
    -------
    pd.DataFrame
        Raw review dataset.
    """

    all_reviews = []

    continuation_token = None
    fetched = 0

    print("=" * 60)
    print("BCA MOBILE REVIEW COLLECTION")
    print("=" * 60)

    while MAX_REVIEWS is None or fetched < MAX_REVIEWS:

        if MAX_REVIEWS is None:
            batch_size = BATCH_SIZE
        else:
            batch_size = min(
                BATCH_SIZE,
                MAX_REVIEWS - fetched,
            )

        batch, continuation_token = reviews(
            APP_ID,
            lang=LANGUAGE,
            country=COUNTRY,
            sort=Sort.NEWEST,
            count=batch_size,
            continuation_token=continuation_token,
        )

        if not batch:
            print("No more reviews returned.")
            break

        all_reviews.extend(batch)
        fetched += len(batch)

        print(f"Collected: {fetched:,} reviews")

        if continuation_token is None:
            print("No continuation token returned.")
            break

        time.sleep(REQUEST_DELAY)

    df = pd.DataFrame(
        [
            {
                "review_id": review.get("reviewId"),
                "rating": review.get("score"),
                "review_date": review.get("at"),
                "review_text": review.get("content"),
                "thumbs_up": review.get("thumbsUpCount"),
            }
            for review in all_reviews
        ]
    )

    return df


def save_raw_reviews(df: pd.DataFrame) -> None:
    """Save the raw dataset to the project's raw data directory."""

    RAW_REVIEWS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        RAW_REVIEWS_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(f"Saved {len(df):,} reviews to:")
    print(RAW_REVIEWS_FILE)


if __name__ == "__main__":

    reviews_df = collect_reviews()

    save_raw_reviews(reviews_df)

    print()
    print("=" * 60)
    print("COLLECTION SUMMARY")
    print("=" * 60)

    print(f"Total reviews: {len(reviews_df):,}")

    if not reviews_df.empty:

        print(
            f"Date range: "
            f"{reviews_df['review_date'].min()} "
            f"→ "
            f"{reviews_df['review_date'].max()}"
        )

        print("\nRating distribution:")

        print(
            reviews_df["rating"]
            .value_counts()
            .sort_index()
        )