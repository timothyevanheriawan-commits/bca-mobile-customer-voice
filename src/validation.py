"""
Manual validation scaffolding for the rule-based issue classifier.

The classifier in issue_classification.py reports its own match counts, but
those numbers are only trustworthy once a human has actually read a sample of
tagged (and untagged) reviews and confirmed the rules are catching the right
thing. This module handles the mechanical parts (sampling, exporting for
annotation, scoring the annotations) — the actual judgment calls belong to
whoever reads the sampled reviews, not to any code here.

Two separate checks, because they answer different questions:

- PRECISION (per category): of reviews tagged with category X, how many
  actually are about X? Sampled per-category since each category needs its
  own accuracy check.
- RECALL / COVERAGE GAP (pooled across categories): of the negative reviews
  the classifier tagged with nothing, how many actually describe a real issue
  it missed, vs. a genuine one-off/vague complaint? Sampled once from the
  unclassified-negative pool rather than per-category, because most
  categories are too rare for a blind per-category recall sample to be an
  efficient use of reading time — this pooled sample answers recall for every
  category from a single reading pass.
"""

from pathlib import Path

import pandas as pd


def sample_for_precision(df: pd.DataFrame, category: str, n: int = 30,
                          seed: int = 42, text_col: str = "review_text") -> pd.DataFrame:
    """Random sample of reviews tagged with `category`, for a precision check.

    Returns fewer than n rows if the category has fewer than n total matches
    (rather than erroring or padding) — some categories are genuinely rare.
    """
    tagged = df[df["issues"].fillna("").str.contains(category, regex=False)]
    sample_n = min(n, len(tagged))
    sample = tagged.sample(n=sample_n, random_state=seed) if sample_n else tagged.iloc[0:0]

    out = sample[["review_id", "rating", text_col]].copy()
    out["tagged_issue"] = category
    out["correct"] = ""  # to be filled in manually: 1 = correctly tagged, 0 = wrong
    return out.reset_index(drop=True)


def sample_for_recall_gaps(df: pd.DataFrame, n: int = 50, seed: int = 42,
                            text_col: str = "review_text") -> pd.DataFrame:
    """Random sample of unclassified negative reviews, for a coverage/recall check.

    Pulls from reviews where rating_group == 'negative' and has_issue == False.
    Annotator fills in `actual_issue` per row: either one of the existing
    category names (a real miss — the classifier should have caught this) or
    'none' (a genuine one-off/vague complaint that doesn't fit any category).
    """
    unclassified = df[(df["rating_group"] == "negative") & (~df["has_issue"])]
    sample_n = min(n, len(unclassified))
    sample = unclassified.sample(n=sample_n, random_state=seed)

    out = sample[["review_id", "rating", text_col]].copy()
    out["actual_issue"] = ""  # fill with a category name, or "none"
    return out.reset_index(drop=True)


def export_for_annotation(sample_df: pd.DataFrame, path: Path) -> None:
    """Write a sample to CSV for manual annotation (in Excel or any editor)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_df.to_csv(path, index=False)


def load_annotations(path: Path) -> pd.DataFrame:
    """Read an annotated sample back in."""
    return pd.read_csv(Path(path))


def compute_precision(annotated: pd.DataFrame) -> dict:
    """Compute precision from an annotated precision sample.

    Expects a 'correct' column with 1/0 values. Rows left blank (not yet
    annotated) are excluded from the count and flagged, rather than silently
    treated as correct or incorrect.
    """
    total = len(annotated)
    filled = annotated["correct"].notna() & (annotated["correct"] != "")
    n_annotated = filled.sum()

    if n_annotated == 0:
        return {"total_sampled": total, "n_annotated": 0, "precision": None,
                "note": "No rows annotated yet."}

    correct_values = pd.to_numeric(annotated.loc[filled, "correct"], errors="coerce")
    precision = correct_values.mean()

    return {
        "total_sampled": total,
        "n_annotated": int(n_annotated),
        "n_unannotated": int(total - n_annotated),
        "precision": round(float(precision), 3),
    }


def compute_recall_gap_summary(annotated: pd.DataFrame) -> pd.DataFrame:
    """Tally what the unclassified-negative sample actually turned out to be.

    Expects an 'actual_issue' column filled with either a category name (a
    real miss) or 'none' (genuine one-off complaint, not a taxonomy gap).
    Returns a count/share table, sorted by frequency.
    """
    filled = annotated[annotated["actual_issue"].notna() & (annotated["actual_issue"] != "")]

    if len(filled) == 0:
        return pd.DataFrame(columns=["actual_issue", "count", "share_of_annotated"])

    counts = filled["actual_issue"].str.strip().str.lower().value_counts()
    summary = counts.reset_index()
    summary.columns = ["actual_issue", "count"]
    summary["share_of_annotated"] = summary["count"] / len(filled)
    return summary
