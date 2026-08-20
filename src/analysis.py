"""
Reusable analysis functions for turning the classified dataset into the
inputs a business prioritization decision actually needs:

    - how big is each issue (share of negative reviews)?
    - is it getting more or less common over time?

Deliberately NOT doing a regression/ML trend model here. With 5 months of
data and categories as small as 5-30 tagged reviews, a fitted slope would
carry more noise than signal and would be hard for a non-technical reader to
sanity-check. Comparing the first half of the window to the second half is
coarser, but every number in it is directly inspectable - "was it more common
in the earlier months or the later months" is a claim anyone can verify by
re-reading the monthly table themselves.
"""

from __future__ import annotations

import pandas as pd


def issue_frequency_table(df: pd.DataFrame, issues_col: str = "issues") -> pd.DataFrame:
    """One row per issue category: how often it appears and how it skews.

    - n_mentions: reviews tagged with this category (a review can carry more
      than one tag, so columns don't sum to len(df))
    - share_of_all_reviews: n_mentions / total reviews in the dataset
    - share_of_negative_reviews: n_mentions / total NEGATIVE reviews - this is
      the more useful denominator for prioritization, since it answers "of
      customers who are already unhappy, what fraction hit this problem"
    - pct_from_1_2_star: of the reviews tagged with this issue, what share are
      1-2 stars - a sanity check that low ratings, not incidental mentions in
      positive reviews, are driving the count
    """
    total_reviews = len(df)
    negative_reviews = (df["rating_group"] == "negative").sum()

    all_categories = set()
    for issue_str in df[issues_col].fillna(""):
        if issue_str:
            all_categories.update(issue_str.split(","))

    rows = []
    for category in sorted(all_categories):
        tagged = df[df[issues_col].fillna("").str.contains(category, regex=False)]
        n_mentions = len(tagged)
        low_star = (tagged["rating"] <= 2).sum()

        rows.append({
            "issue": category,
            "n_mentions": n_mentions,
            "share_of_all_reviews": round(n_mentions / total_reviews, 4) if total_reviews else 0,
            "share_of_negative_reviews": round(n_mentions / negative_reviews, 4) if negative_reviews else 0,
            "pct_from_1_2_star": round(low_star / n_mentions, 3) if n_mentions else 0,
        })

    return pd.DataFrame(rows).sort_values("n_mentions", ascending=False).reset_index(drop=True)


def monthly_issue_share(df: pd.DataFrame, issues_col: str = "issues",
                         date_col: str = "review_date") -> pd.DataFrame:
    """Month x category table: what share of THAT MONTH's reviews mentioned
    each issue.

    Uses share of that month's total reviews (not raw counts) so a category
    isn't judged "growing" just because review volume itself grew that month
    - a known risk flagged back in 01_data_audit given how Play Store scraping
    skews toward recent months.
    """
    working = df.copy()
    working["month"] = working[date_col].dt.to_period("M").astype(str)
    monthly_totals = working.groupby("month").size()

    all_categories = set()
    for issue_str in working[issues_col].fillna(""):
        if issue_str:
            all_categories.update(issue_str.split(","))

    records = []
    for month, month_df in working.groupby("month"):
        month_total = monthly_totals[month]
        for category in sorted(all_categories):
            n = month_df[issues_col].fillna("").str.contains(category, regex=False).sum()
            records.append({
                "month": month,
                "issue": category,
                "n_mentions": int(n),
                "share_of_month": round(n / month_total, 4) if month_total else 0,
            })

    return pd.DataFrame(records)


def issue_trend_direction(monthly_share_df: pd.DataFrame, min_months: int = 4) -> pd.DataFrame:
    """Classify each issue as increasing / decreasing / stable by comparing
    the average monthly share in the first half of the window vs the second
    half.

    Returns 'insufficient_data' rather than guessing when there are fewer
    than `min_months` distinct months - a 2-3 month trend read is not
    trustworthy enough to hand to a business stakeholder as a direction.

    Threshold for "stable": within +/-20% relative change. This is a judgment
    call, stated explicitly here rather than buried in a magic number, so it
    can be revisited if the categorized results look wrong on inspection.
    """
    months = sorted(monthly_share_df["month"].unique())
    if len(months) < min_months:
        issues = sorted(monthly_share_df["issue"].unique())
        return pd.DataFrame({
            "issue": issues,
            "trend": ["insufficient_data"] * len(issues),
            "first_half_avg_share": [None] * len(issues),
            "second_half_avg_share": [None] * len(issues),
            "relative_change": [None] * len(issues),
        })

    midpoint = len(months) // 2
    first_half = set(months[:midpoint])
    second_half = set(months[midpoint:])

    rows = []
    for category, cat_df in monthly_share_df.groupby("issue"):
        first_avg = cat_df[cat_df["month"].isin(first_half)]["share_of_month"].mean()
        second_avg = cat_df[cat_df["month"].isin(second_half)]["share_of_month"].mean()

        if pd.isna(first_avg) or pd.isna(second_avg):
            trend = "insufficient_data"
            relative_change = None
        elif first_avg == 0:
            trend = "increasing" if second_avg > 0 else "stable"
            relative_change = None
        else:
            relative_change = round((second_avg - first_avg) / first_avg, 3)
            if relative_change > 0.2:
                trend = "increasing"
            elif relative_change < -0.2:
                trend = "decreasing"
            else:
                trend = "stable"

        rows.append({
            "issue": category,
            "trend": trend,
            "first_half_avg_share": round(first_avg, 4) if pd.notna(first_avg) else None,
            "second_half_avg_share": round(second_avg, 4) if pd.notna(second_avg) else None,
            "relative_change": relative_change,
        })

    return pd.DataFrame(rows).sort_values("issue").reset_index(drop=True)
