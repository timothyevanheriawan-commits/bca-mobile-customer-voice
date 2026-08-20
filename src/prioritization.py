"""
Combines issue frequency/trend (from analysis.py) with validation results
(from validation.py output, i.e. the annotated CSVs in data/validation/) into
a single table a business stakeholder can act on.

Deliberately NOT a single weighted composite score. Squashing frequency,
trend, and validation confidence into one number would hide the trade-offs
a real prioritization decision has to make explicit - e.g. a high-frequency
but unvalidated category shouldn't quietly outrank a smaller but confirmed
one just because the composite formula weighted frequency higher. Instead
this produces a small set of clearly-labeled columns and a priority TIER
(High/Medium/Low) derived from readable rules, so anyone reading the table
can see exactly why a category landed where it did.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.issue_classification import ISSUE_RULES

# Categories where a false classification has real financial consequence for
# a customer, not just a labeling inconvenience - matches the priority order
# stated in 04_validation.ipynb. These are treated as High priority whenever
# they clear a minimal frequency bar, regardless of trend direction, because
# "money disappearing" warrants product attention even if it's not growing.
MONEY_AFFECTING_CATEGORIES = {
    "unexplained_deduction",
    "transaction_failed_balance_deducted",
}


def validation_status_table(validation_dir: Path) -> pd.DataFrame:
    """Reads every precision_*.csv in data/validation/ and reports, per
    category: how many rows are annotated, and the resulting precision.

    A category with 0 annotated rows gets precision=None and is flagged
    'unvalidated' - its frequency numbers may be real, may not be; nobody has
    checked yet. A category with a low computed precision (<0.8, the same
    threshold used in 04_validation.ipynb) is flagged 'needs_regex_fix' since
    its frequency count is likely inflated by false positives.

    Only reads files whose name matches a current ISSUE_RULES category exactly
    (e.g. precision_app_performance.csv). Historical archives from earlier
    validation rounds (e.g. precision_app_performance_r1.csv, kept after a
    regex fix so the "before" evidence isn't lost - see 04_validation.ipynb's
    Round 2 section) are intentionally skipped: they aren't a 10th+ category,
    they're a superseded snapshot of one of the 10, and including them here
    would silently double-count / mislabel rows in the table below.
    """
    validation_dir = Path(validation_dir)
    rows = []

    for csv_path in sorted(validation_dir.glob("precision_*.csv")):
        category = csv_path.stem.replace("precision_", "")
        if category not in ISSUE_RULES:
            continue
        df = pd.read_csv(csv_path)

        # normalize whatever is currently in the 'correct' column
        correct_numeric = pd.to_numeric(
            df["correct"].astype(str).str.strip(),
            errors="coerce",
        )
        annotated = correct_numeric.notna()
        n_annotated = int(annotated.sum())
        n_total = len(df)

        if n_annotated == 0:
            precision = None
            status = "unvalidated"
        else:
            precision = round(float(correct_numeric[annotated].mean()), 3)
            if precision < 0.8:
                status = "needs_regex_fix"
            elif n_annotated < n_total:
                status = "partially_validated"
            else:
                status = "validated"

        rows.append({
            "issue": category,
            "precision_sample_size": n_total,
            "precision_annotated": n_annotated,
            "precision": precision,
            "validation_status": status,
        })

    return pd.DataFrame(rows).sort_values("issue").reset_index(drop=True)


def build_priority_table(frequency_df: pd.DataFrame, trend_df: pd.DataFrame,
                          validation_df: pd.DataFrame,
                          min_negative_share: float = 0.03) -> pd.DataFrame:
    """Joins frequency + trend + validation status into one table with a
    Priority tier.

    Tier rules (stated plainly so they're auditable, not a black box):
      - High: money-affecting category with share_of_negative_reviews above
        `min_negative_share`, OR any category that is both above the
        threshold AND trending 'increasing'.
      - Medium: above the threshold but stable/decreasing/insufficient_data,
        and not money-affecting.
      - Low: below the threshold.

    A category with validation_status == 'unvalidated' or 'needs_regex_fix'
    keeps its computed tier but gets flagged in `caveat` - the frequency
    number driving that tier hasn't been confirmed accurate yet, so the tier
    should be read as provisional until validation closes it out.
    """
    merged = (
        frequency_df
        .merge(trend_df, on="issue", how="left")
        .merge(validation_df, on="issue", how="left")
    )

    def assign_tier(row) -> str:
        is_money = row["issue"] in MONEY_AFFECTING_CATEGORIES
        above_threshold = row["share_of_negative_reviews"] >= min_negative_share
        increasing = row.get("trend") == "increasing"

        if above_threshold and (is_money or increasing):
            return "High"
        if above_threshold:
            return "Medium"
        return "Low"

    def assign_caveat(row) -> str:
        status = row.get("validation_status")
        if status == "unvalidated":
            return "Frequency not yet confirmed - no rows validated"
        if status == "partially_validated":
            return f"Precision {row.get('precision')} from {int(row.get('precision_annotated'))}/{int(row.get('precision_sample_size'))} rows - promising but sample incomplete"
        if status == "needs_regex_fix":
            return f"Precision {row.get('precision')} - classifier rule likely over-matching, recheck before quoting this count"
        if pd.isna(status):
            return "No validation sample found for this category"
        return ""

    merged["priority_tier"] = merged.apply(assign_tier, axis=1)
    merged["caveat"] = merged.apply(assign_caveat, axis=1)

    tier_order = {"High": 0, "Medium": 1, "Low": 2}
    merged["_tier_sort"] = merged["priority_tier"].map(tier_order)
    merged = merged.sort_values(
        ["_tier_sort", "share_of_negative_reviews"], ascending=[True, False]
    ).drop(columns="_tier_sort").reset_index(drop=True)

    return merged[[
        "issue", "priority_tier", "n_mentions", "share_of_negative_reviews",
        "trend", "validation_status", "precision", "caveat",
    ]]
