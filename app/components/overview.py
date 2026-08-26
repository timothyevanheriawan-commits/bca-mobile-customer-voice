"""Landing page: how big is the problem, and what should get worked on first.

The priority table here is rendered directly from
`src.prioritization.build_priority_table` - not a hardcoded summary - so a
category sitting at "needs_regex_fix" shows up as exactly that, stamped
red, with its caveat text, rather than silently looking as solid as a
validated one. The top row of that same table drives the hero callout, so
the page's single most important claim can never drift out of sync with
the table underneath it.
"""

from __future__ import annotations

import html

import plotly.graph_objects as go
import streamlit as st

from app.utils.formatting import (
    format_count,
    format_idr,
    format_pct,
    issue_label,
    tier_color,
    tier_tone,
    trend_arrow,
    validation_tone,
)
from app.utils.theme import COLORS, breadcrumb, callout, ledger_table, metric_row, quote_card, stamp, tag
from src.prioritization import MONEY_AFFECTING_CATEGORIES, estimate_financial_exposure

# Placeholder assumption, not a measured figure - see
# src.prioritization.estimate_financial_exposure's docstring. Stated here,
# in one place, so it's easy to find and replace once a real average
# transaction value is available (e.g. from BCA transaction data).
ASSUMED_AVG_TRANSACTION_IDR = 500_000

STAR_COLORS = {
    1: COLORS["danger"], 2: "#C97A64",
    3: COLORS["warning"],
    4: COLORS["faint"], 5: COLORS["success"],
}


def render(tables: dict) -> None:
    df = tables["reviews"]
    priority_df = tables["priority"]

    st.markdown(breadcrumb("Overview"), unsafe_allow_html=True)
    st.title("Customer Voice")
    st.markdown(
        '<p class="lg-subtitle">A working ledger of what BCA Mobile customers are '
        'hitting on Google Play, tallied by issue and ranked by what to fix first.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="lg-context">Google Play Reviews &middot; {len(df):,} logged &middot; '
        f'{df["review_date"].min().strftime("%b %Y")} to '
        f'{df["review_date"].max().strftime("%b %Y")}</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        '<p class="lg-body">Every entry below comes from a real review, tagged by a '
        'plain regex rule a person can read (see Methodology), then checked by hand '
        'before it is trusted. This is not a sentiment score. It is a count of specific, '
        'named problems, so the question this page answers is narrow and concrete: '
        'of everything customers complained about, what shows up most, and is it '
        'getting worse.</p>',
        unsafe_allow_html=True,
    )

    st.write("")

    # --- Top priority signal --------------------------------------------
    top = priority_df.iloc[0]
    top_arrow = trend_arrow(top["trend"])
    detail = (
        f"{format_pct(top['share_of_negative_reviews'])} of negative reviews, "
        f"{format_count(top['n_mentions'])} mentions, trend {top_arrow} {top['trend']}."
    )
    if top["caveat"]:
        detail += f" Note: {top['caveat']}"
    callout(
        label=f"Top priority signal &middot; {top['priority_tier']}",
        title=issue_label(top["issue"]),
        detail=detail,
        tone=tier_tone(top["priority_tier"]),
    )

    st.write("")

    # --- Key metrics -------------------------------------------------------
    negative = int((df["rating_group"] == "negative").sum())
    tagged = int((df["issue_count"] > 0).sum())
    multi_issue = int((df["issue_count"] > 1).sum())
    n_high = int((priority_df["priority_tier"] == "High").sum())
    n_needs_fix = int((priority_df["validation_status"] == "needs_regex_fix").sum())

    metric_row([
        {"label": "Total reviews", "value": format_count(len(df))},
        {"label": "Negative reviews", "value": format_count(negative), "sub": format_pct(negative / len(df))},
        {"label": "High priority issues", "value": format_count(n_high)},
        {
            "label": "Need regex rework",
            "value": format_count(n_needs_fix),
            "sub": "check before quoting" if n_needs_fix else "none right now",
        },
    ])

    st.write("")
    st.markdown(
        '<p class="lg-body">Ratings here are polarized rather than mediocre: most '
        f'reviews land at either end of the scale, not the middle. {format_pct(negative / len(df))} '
        'of all reviews are negative (1 to 2 stars), and roughly one in ten tagged reviews '
        f'names more than one problem at once ({format_count(multi_issue)} of {format_count(tagged)} '
        'tagged reviews), which is why the issue counts below do not sum to the negative '
        'review total.</p>',
        unsafe_allow_html=True,
    )

    st.write("")
    st.subheader("In their own words")
    st.markdown(
        '<p class="lg-subtitle">Real reviews behind the top priority issue, unedited '
        'except for whitespace. Numbers above tell you how big the problem is; these tell '
        'you what it actually sounds like. See every review for any category in Issue '
        'Explorer.</p>',
        unsafe_allow_html=True,
    )
    st.write("")
    _pull_quotes(df, top["issue"])

    st.write("")
    st.subheader("Ratings, at a glance")
    st.markdown(
        '<p class="lg-subtitle">Count of reviews at each star rating. The dip in the '
        'middle is the tell: customers who show up to leave a review are mostly either '
        'satisfied or actively stuck on something, not lukewarm.</p>',
        unsafe_allow_html=True,
    )
    _rating_distribution_chart(df)

    st.divider()
    st.subheader("Priority ledger")
    st.markdown(
        '<p class="lg-subtitle">Ranked high to low. A category is High if it is a '
        'money-affecting issue above the frequency floor, or any issue above the floor '
        'that is trending up. See <code>src/prioritization.py</code> for the exact rule. '
        'A red validation stamp means the count next to it is provisional: read the caveat '
        'before repeating the number elsewhere.</p>',
        unsafe_allow_html=True,
    )
    st.write("")

    _priority_ledger(priority_df)

    st.write("")
    st.subheader("Recommended actions")
    st.markdown(
        '<p class="lg-subtitle">What to actually do about the ledger above, derived '
        'directly from each row\'s tier, trend, and validation status - not a separate '
        'judgment call. See <code>src.prioritization.recommend_action</code> for the exact '
        'rule behind each sentence.</p>',
        unsafe_allow_html=True,
    )
    st.write("")
    _recommended_actions(priority_df)

    exposure_df = estimate_financial_exposure(tables["frequency"], ASSUMED_AVG_TRANSACTION_IDR)
    if not exposure_df.empty:
        st.write("")
        st.subheader("Estimated financial exposure")
        st.markdown(
            '<p class="lg-subtitle">Order-of-magnitude only, not a reconciled figure: '
            f'mentions &times; an assumed average transaction value of '
            f'{format_idr(ASSUMED_AVG_TRANSACTION_IDR)}, stated here as a placeholder '
            'assumption. Replace with a real average transaction value before quoting this '
            'externally - it exists to make the scale of "money affecting" issues '
            'concrete, not to be a precise total.</p>',
            unsafe_allow_html=True,
        )
        st.write("")
        _financial_exposure(exposure_df)

    st.write("")
    st.subheader("Share of negative reviews, by issue")
    st.markdown(
        '<p class="lg-subtitle">What fraction of unhappy reviews mention each problem. '
        'Bars are colored by priority tier, the same as the ledger above, so the two '
        'views read as one argument rather than two separate charts.</p>',
        unsafe_allow_html=True,
    )

    chart_df = priority_df.sort_values("share_of_negative_reviews", ascending=True)
    bar_colors = [tier_color(t) for t in chart_df["priority_tier"]]

    fig = go.Figure(
        go.Bar(
            x=chart_df["share_of_negative_reviews"],
            y=[issue_label(i) for i in chart_df["issue"]],
            orientation="h",
            marker_color=bar_colors,
            text=[format_pct(v) for v in chart_df["share_of_negative_reviews"]],
            textposition="outside",
        )
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans, sans-serif", color=COLORS["ink"], size=12),
        margin=dict(l=10, r=40, t=10, b=10),
        xaxis=dict(tickformat=".0%", gridcolor=COLORS["rule"]),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        height=420,
    )
    st.plotly_chart(fig, width="stretch")

    st.divider()
    st.subheader("Rating composition, by issue")
    st.markdown(
        '<p class="lg-subtitle">Same issues, split by the star rating attached to each '
        'mention. This is the shape behind the single "% from 1-2 stars" number on the '
        'ledger above: an issue concentrated at 1 star reads as more urgent than one '
        'spread evenly across 1 and 2, even when both hit the same overall share.</p>',
        unsafe_allow_html=True,
    )
    _rating_composition_chart(tables["rating_matrix"])

    st.divider()
    st.subheader("Where problems overlap")
    st.markdown(
        '<p class="lg-subtitle">The 10 issue pairs tagged together most often on the '
        'same review. A high count here usually means one underlying incident is '
        'surfacing as two labels, not two independent problems - worth reading before '
        'scoping a fix as if each issue were separate.</p>',
        unsafe_allow_html=True,
    )
    _cooccurrence_ledger(tables["cooccurrence"])


def _rating_distribution_chart(df) -> None:
    counts = df["rating"].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)
    star_colors = {
        1: COLORS["danger"], 2: COLORS["danger"],
        3: COLORS["warning"],
        4: COLORS["faint"], 5: COLORS["faint"],
    }
    fig = go.Figure(
        go.Bar(
            x=[f"{s} star" for s in counts.index],
            y=counts.values,
            marker_color=[star_colors[s] for s in counts.index],
            text=[f"{v:,}" for v in counts.values],
            textposition="outside",
        )
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans, sans-serif", color=COLORS["ink"], size=12),
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(gridcolor=COLORS["rule"], title="Reviews"),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        height=280,
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch")


def _rating_composition_chart(rating_matrix_df) -> None:
    ordered = rating_matrix_df.sort_values("n_mentions", ascending=True)
    fig = go.Figure()
    for star in [1, 2, 3, 4, 5]:
        fig.add_trace(
            go.Bar(
                name=f"{star} star",
                x=ordered[f"star_{star}"],
                y=[issue_label(i) for i in ordered["issue"]],
                orientation="h",
                marker_color=STAR_COLORS[star],
            )
        )
    fig.update_layout(
        barmode="stack",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans, sans-serif", color=COLORS["ink"], size=12),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor=COLORS["rule"], title="Reviews"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=420,
    )
    st.plotly_chart(fig, width="stretch")


def _cooccurrence_ledger(cooccurrence_df) -> None:
    if cooccurrence_df.empty:
        st.info("No two issues were tagged together often enough to report.")
        return

    headers = ["Issue A", "Issue B", "Reviews tagged with both"]
    rows = [
        [
            f"<strong>{issue_label(row['issue_a'])}</strong>",
            f"<strong>{issue_label(row['issue_b'])}</strong>",
            format_count(row["n_reviews"]),
        ]
        for _, row in cooccurrence_df.iterrows()
    ]
    ledger_table(headers, rows, col_classes=["", "", "lg-right"])


def _priority_ledger(priority_df) -> None:
    headers = ["No.", "Issue", "Tier", "Mentions", "Share of negatives", "Trend", "Validation"]
    rows = []
    for i, (_, row) in enumerate(priority_df.iterrows(), start=1):
        status = row["validation_status"]
        status_label = status if isinstance(status, str) else "unvalidated"
        arrow = trend_arrow(row["trend"])
        precision_txt = (
            f" ({row['precision']:.2f})"
            if row.get("precision") == row.get("precision") and row.get("precision") is not None
            else ""
        )
        issue_cell = f"<strong>{issue_label(row['issue'])}</strong>"
        if row.get("low_sample"):
            issue_cell += tag("insufficient sample", "neutral")
        if row["caveat"]:
            issue_cell += f'<span class="lg-caveat">{row["caveat"]}</span>'

        rows.append([
            f"{i:02d}",
            issue_cell,
            tag(row["priority_tier"], tier_tone(row["priority_tier"])),
            format_count(row["n_mentions"]),
            format_pct(row["share_of_negative_reviews"]),
            f"{arrow} {row['trend']}",
            stamp(f"{status_label}{precision_txt}", validation_tone(status_label)),
        ])

    ledger_table(
        headers, rows,
        col_classes=["lg-num", "", "", "lg-right", "lg-right", "lg-right", ""],
    )


def _recommended_actions(priority_df) -> None:
    """The 3 highest-tier rows, restated as an instruction rather than a
    ranking. Deliberately capped at 3 - this is meant to be read in full,
    not scanned like the ledger above it, so it stays short on purpose."""
    top_rows = priority_df.head(3)
    for _, row in top_rows.iterrows():
        callout(
            label=f"{row['priority_tier']} priority · {issue_label(row['issue'])}",
            title=row["recommended_action"],
            detail=(
                f"{format_count(row['n_mentions'])} mentions, "
                f"{format_pct(row['share_of_negative_reviews'])} of negative reviews."
            ),
            tone=tier_tone(row["priority_tier"]),
        )
        st.write("")


def _financial_exposure(exposure_df) -> None:
    headers = ["Issue", "Mentions", "Assumed avg. transaction", "Estimated exposure"]
    rows = [
        [
            f"<strong>{issue_label(row['issue'])}</strong>",
            format_count(row["n_mentions"]),
            format_idr(row["assumed_avg_transaction_idr"]),
            format_idr(row["estimated_exposure_idr"]),
        ]
        for _, row in exposure_df.iterrows()
    ]
    ledger_table(headers, rows, col_classes=["", "lg-right", "lg-right", "lg-right"])


def _pull_quotes(df, top_issue: str, n: int = 3) -> None:
    """2-3 real, short reviews from the top-priority category, so the
    landing page carries at least a little of the actual customer voice
    instead of being aggregates end to end. Picked from short (readable at
    a glance), low-star, high-helpfulness reviews tagged with the top
    issue - not cherry-picked for content, just for length and visibility,
    the same way a human skimming for a representative quote would filter.
    """
    candidates = df[
        df["issues"].str.contains(top_issue, regex=False)
        & (df["rating"] <= 2)
        & (df["review_length"].between(25, 220))
    ].sort_values("thumbs_up", ascending=False)

    if candidates.empty:
        st.info("No short, representative review found for this category yet.")
        return

    for _, r in candidates.head(n).iterrows():
        text = html.escape(str(r["review_text"])).replace("\r\n", "\n").replace("\n", "<br>")
        date_str = r["review_date"].strftime("%d %b %Y")
        st.markdown(quote_card(text, r["rating"], date_str), unsafe_allow_html=True)