"""How this pipeline works, and, critically, which numbers to trust.

Renders `validation_status_table` output directly rather than a written
summary, so this page can never drift out of sync with what is actually
in data/validation/. If a category's precision file regresses, this page
reflects that on the next reload, no manual edit required.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from app.utils.definitions import DEFINITIONS
from app.utils.formatting import format_count, issue_label, validation_tone
from app.utils.theme import COLORS, breadcrumb, ledger_table, pipeline_flow, stamp

PIPELINE_STEPS = [
    ("Reviews", "Google Play reviews for the BCA Mobile app, collected via google-play-scraper."),
    ("Preprocessing", "Dedup, text normalization, rating_group and review_length computed."),
    ("Classification", "Each review tagged against 10 issue categories with hand-written, auditable regex rules. Not a black-box model."),
    ("Issue signals", "Frequency, share of negative reviews, and monthly trend direction per category."),
    ("Prioritization", "Frequency, trend, and validation status combined into a plain, auditable priority tier."),
]

PRECISION_THRESHOLD = 0.80


def render(tables: dict) -> None:
    validation_df = tables["validation"]

    st.markdown(breadcrumb("Methodology"), unsafe_allow_html=True)
    st.title("How this was built, and what to trust")
    st.markdown(
        '<p class="lg-subtitle">Raw reviews become issue signals, issue signals become '
        'priorities. Every stage below is inspectable, not a black box, and every claim '
        'this dashboard makes can be traced back to one of the five entries in this flow.</p>',
        unsafe_allow_html=True,
    )
    st.write("")

    pipeline_flow(PIPELINE_STEPS)

    st.divider()
    st.subheader("Pipeline, in detail")
    st.markdown(
        """
1. **Collection.** Google Play reviews for the BCA Mobile app, scraped via
   `google-play-scraper` (`src/data_collection.py`).
2. **Cleaning.** Dedup, text normalization, `rating_group` (positive,
   neutral, negative) and `review_length` computed (`src/cleaning.py`).
3. **Classification.** Each review tagged against 10 issue categories using
   hand-written Indonesian-language regex rules, not an ML model
   (`src/issue_classification.py`). Chosen deliberately: with an ~5,000-review
   dataset, transparent regex a reader can inspect line by line beats a
   black-box classifier nobody on the team can audit.
4. **Validation.** For each category, a random sample of matched reviews is
   manually annotated as correct or incorrect to compute precision
   (`src/validation.py`, `notebooks/04_validation.ipynb`). Categories under
   0.80 precision are flagged for a regex rework, not shipped as-is.
5. **Prioritization.** Frequency, trend direction, and validation status are
   combined into a priority tier with plain, auditable rules, not a single
   opaque score (`src/prioritization.py`).
        """
    )

    st.divider()
    st.subheader("Category definitions")
    st.markdown(
        '<p class="lg-subtitle">What each label in this dashboard is actually supposed '
        'to mean. These are the same definitions the manual validation tool shows an '
        'annotator, so "correct" in the precision numbers below means "matches this '
        'sentence," nothing looser.</p>',
        unsafe_allow_html=True,
    )
    st.write("")
    _definitions_table(validation_df)

    st.divider()
    st.subheader("Validation status, live from data/validation/")
    st.markdown(
        '<p class="lg-subtitle">This table is computed directly from the annotated CSVs '
        'in the repo every time this page loads. If a category shows a red '
        '<code>needs_regex_fix</code> stamp here, treat its frequency numbers elsewhere '
        'in this dashboard as provisional until that is resolved.</p>',
        unsafe_allow_html=True,
    )
    st.write("")

    needs_fix = validation_df[validation_df["validation_status"] == "needs_regex_fix"]
    if len(needs_fix):
        names = ", ".join(issue_label(i) for i in needs_fix["issue"])
        st.warning(
            f"**{len(needs_fix)} categor{'y' if len(needs_fix) == 1 else 'ies'} below the "
            f"0.80 precision threshold right now:** {names}. Their counts elsewhere in "
            "this dashboard may be inflated by false positives. Do not quote them "
            "externally until the regex is reworked and re-validated."
        )
        st.write("")

    _precision_chart(validation_df)
    st.write("")
    _validation_ledger(validation_df)

    st.divider()
    st.subheader("Known limitations")
    st.markdown(
        """
- Categories under 0.80 precision (flagged above, if any) need another
  regex round before their counts should be treated as reliable.
- `ui_ux_regression` has only 2 total matches in the whole dataset. That is
  too small a base to judge precision meaningfully either way.
- Trend direction compares first-half versus second-half of the collection
  window, not a fitted slope. Read it as direction only, not a precise
  rate of change.
- `share_of_negative_reviews` is a share of *tagged* mentions, and a single
  review can carry more than one issue tag, so category shares do not sum
  to 100 percent of negative reviews.
        """
    )


def _definitions_table(validation_df) -> None:
    headers = ["Category", "Definition"]
    rows = []
    for issue in validation_df.sort_values("issue")["issue"]:
        definition = DEFINITIONS.get(issue, "No definition recorded for this category yet.")
        rows.append([f"<strong>{issue_label(issue)}</strong>", definition])
    ledger_table(headers, rows)


def _precision_chart(validation_df) -> None:
    scored = validation_df[validation_df["precision"].notna()].sort_values("precision")
    if scored.empty:
        return

    colors = [
        COLORS["success"] if p >= PRECISION_THRESHOLD else COLORS["danger"]
        for p in scored["precision"]
    ]
    fig = go.Figure(
        go.Bar(
            x=scored["precision"],
            y=[issue_label(i) for i in scored["issue"]],
            orientation="h",
            marker_color=colors,
            text=[f"{p:.2f}" for p in scored["precision"]],
            textposition="outside",
        )
    )
    fig.add_vline(
        x=PRECISION_THRESHOLD,
        line_dash="dash",
        line_color=COLORS["muted"],
        annotation_text="0.80 threshold",
        annotation_font_color=COLORS["muted"],
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans, sans-serif", color=COLORS["ink"], size=12),
        margin=dict(l=10, r=40, t=10, b=10),
        xaxis=dict(range=[0, 1.08], tickformat=".0%", gridcolor=COLORS["rule"], title="Precision"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        height=380,
    )
    st.plotly_chart(fig, width="stretch")


def _validation_ledger(validation_df) -> None:
    headers = ["Category", "Status", "Precision", "Annotated"]
    rows = []
    for _, row in validation_df.sort_values("issue").iterrows():
        status = row["validation_status"]
        precision = row["precision"]
        precision_txt = f"{precision:.3f}" if precision is not None and precision == precision else "n/a"
        rows.append([
            f"<strong>{issue_label(row['issue'])}</strong>",
            stamp(status, validation_tone(status)),
            precision_txt,
            f'{format_count(row["precision_annotated"])} / {format_count(row["precision_sample_size"])}',
        ])
    ledger_table(headers, rows, col_classes=["", "", "lg-right", "lg-right"])