"""How this pipeline works, and - critically - which numbers to trust.

Renders `validation_status_table` output directly rather than a written
summary, so this page can never drift out of sync with what's actually in
data/validation/. If a category's precision file regresses, this page
reflects that on the next reload, no manual edit required.
"""

from __future__ import annotations

import streamlit as st

from app.utils.formatting import format_count, issue_label, validation_tone
from app.utils.theme import breadcrumb, pipeline_flow, tag

PIPELINE_STEPS = [
    ("Reviews", "Google Play reviews for the BCA Mobile app, collected via google-play-scraper."),
    ("Preprocessing", "Dedup, text normalization, rating_group and review_length computed."),
    ("Classification", "Each review tagged against 10 issue categories with hand-written, auditable regex rules \u2014 not a black-box model."),
    ("Issue signals", "Frequency, share of negative reviews, and monthly trend direction per category."),
    ("Prioritization", "Frequency + trend + validation status combined into a plain, auditable priority tier."),
]


def render(tables: dict) -> None:
    validation_df = tables["validation"]

    st.markdown(breadcrumb("Methodology"), unsafe_allow_html=True)
    st.title("How this was built, and what to trust")
    st.markdown(
        '<p class="ci-subtitle">Raw reviews become issue signals, issue signals become '
        'priorities \u2014 every stage below is inspectable, not a black box.</p>',
        unsafe_allow_html=True,
    )
    st.write("")

    pipeline_flow(PIPELINE_STEPS)

    st.divider()
    st.subheader("Pipeline, in detail")
    st.markdown(
        """
1. **Collection** &mdash; Google Play reviews for the BCA Mobile app, scraped via
   `google-play-scraper` (`src/data_collection.py`).
2. **Cleaning** &mdash; dedup, text normalization, `rating_group` (positive /
   neutral / negative) and `review_length` computed (`src/cleaning.py`).
3. **Classification** &mdash; each review tagged against 10 issue categories using
   hand-written Indonesian-language regex rules, not an ML model
   (`src/issue_classification.py`). Chosen deliberately: with an ~5,000-review
   dataset, transparent regex a reader can inspect line-by-line beats a black-box
   classifier nobody on the team can audit.
4. **Validation** &mdash; for each category, a random sample of matched reviews is
   manually annotated as correct/incorrect to compute precision
   (`src/validation.py`, `notebooks/04_validation.ipynb`). Categories under 0.80
   precision are flagged for a regex rework, not shipped as-is.
5. **Prioritization** &mdash; frequency, trend direction, and validation status are
   combined into a priority tier with plain, auditable rules, not a single
   opaque score (`src/prioritization.py`).
        """
    )

    st.divider()
    st.subheader("Validation status \u2014 live from data/validation/")
    st.markdown(
        '<p class="ci-subtitle">This table is computed directly from the annotated CSVs '
        'in the repo every time this page loads. If a category shows '
        '<code>needs_regex_fix</code> here, treat its frequency numbers elsewhere in '
        'this dashboard as provisional until that\u2019s resolved.</p>',
        unsafe_allow_html=True,
    )
    st.write("")

    needs_fix = validation_df[validation_df["validation_status"] == "needs_regex_fix"]
    if len(needs_fix):
        names = ", ".join(issue_label(i) for i in needs_fix["issue"])
        st.warning(
            f"**{len(needs_fix)} categor{'y' if len(needs_fix)==1 else 'ies'} below the "
            f"0.80 precision threshold right now:** {names}. Their counts elsewhere in "
            f"this dashboard may be inflated by false positives \u2014 don't quote them "
            f"externally until the regex is reworked and re-validated."
        )
        st.write("")

    for _, row in validation_df.sort_values("issue").iterrows():
        status = row["validation_status"]
        cols = st.columns([2.3, 1.6, 1.6, 1.8])
        cols[0].markdown(f"**{issue_label(row['issue'])}**")
        cols[1].markdown(tag(status, validation_tone(status)), unsafe_allow_html=True)
        precision = row["precision"]
        precision_txt = f"precision: {precision:.3f}" if precision is not None and precision == precision else "precision: \u2013"
        cols[2].markdown(f'<span class="ci-mono">{precision_txt}</span>', unsafe_allow_html=True)
        cols[3].markdown(
            f'<span class="ci-mono">{format_count(row["precision_annotated"])}/{format_count(row["precision_sample_size"])} annotated</span>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.subheader("Known limitations")
    st.markdown(
        """
- Categories under 0.80 precision (flagged above, if any) need another
  regex round before their counts should be treated as reliable.
- `ui_ux_regression` has only 2 total matches in the whole dataset &mdash; too
  small a base to judge precision meaningfully either way.
- Trend direction compares first-half vs. second-half of the collection
  window, not a fitted slope &mdash; read it as direction only, not a precise
  rate of change.
- `share_of_negative_reviews` is a share of *tagged* mentions, and a single
  review can carry more than one issue tag, so category shares don't sum to
  100% of negative reviews.
        """
    )