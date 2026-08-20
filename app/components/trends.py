"""Month-by-month view of how each issue's share of reviews is moving.

Mirrors notebook 05's approach on purpose: first-half vs second-half
comparison, not a fitted regression line. See src/analysis.py's docstring
for why (too few months, too much noise for a trend line to mean
anything). This page also plots raw review volume per month before the
per-issue chart, since a "growing" share can be an artifact of the
scraper pulling more recent reviews rather than a real shift in customer
behavior, and that context is easy to miss if it only lives in a caveat.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from app.utils.formatting import format_pct, issue_label, trend_arrow
from app.utils.theme import COLORS, breadcrumb, ledger_table

# Chart line palette derived from the token set, reused across every
# selected issue so trend color never repeats accidentally within one
# chart.
LINE_PALETTE = [
    COLORS["interact"], COLORS["danger"], COLORS["warning"],
    COLORS["success"], "#6B4E9C", COLORS["ink"],
]


def render(tables: dict) -> None:
    df = tables["reviews"]
    monthly_df = tables["monthly"]
    trend_df = tables["trend"]

    st.markdown(breadcrumb("Trends"), unsafe_allow_html=True)
    st.title("Trends")
    st.markdown(
        '<p class="lg-subtitle">Is each issue getting more or less common, month over '
        'month, and is the underlying review volume stable enough to trust that read?</p>',
        unsafe_allow_html=True,
    )
    st.write("")

    n_months = df["review_date"].dt.to_period("M").nunique()
    st.markdown(
        f'<p class="lg-body">The dataset spans {n_months} months. Trend direction below '
        'compares the average monthly share in the first half of that window against the '
        'second half. It is a coarser read than a fitted slope on purpose: with categories '
        'as small as 5 to 30 tagged reviews some months, a regression line would carry more '
        'noise than signal, and "first half versus second half" is a claim anyone can check '
        'by re-reading the monthly table themselves.</p>',
        unsafe_allow_html=True,
    )

    st.write("")
    st.subheader("Review volume, by month")
    st.markdown(
        '<p class="lg-subtitle">Total reviews collected each month, before any issue '
        'tagging. Read the per-issue trend chart below against this: a month with fewer '
        'reviews overall makes every share in it noisier, and Play Store scraping tends to '
        'skew toward recent months rather than sampling evenly across the whole window.</p>',
        unsafe_allow_html=True,
    )
    _volume_chart(df)

    st.divider()
    st.subheader("Share of month's reviews, by issue")
    st.markdown(
        '<p class="lg-subtitle">Pick a few categories to compare directly. Values are '
        'share of that month\'s total reviews, not raw counts, so a category is not read '
        'as "growing" just because overall review volume grew that month.</p>',
        unsafe_allow_html=True,
    )

    all_issues = sorted(monthly_df["issue"].unique())
    default_issues = (
        trend_df.sort_values("relative_change", ascending=False, na_position="last")
        ["issue"].head(4).tolist()
    )

    selected = st.multiselect(
        "Issues to plot",
        options=all_issues,
        default=default_issues,
        format_func=issue_label,
    )

    if not selected:
        st.info("Pick at least one issue above to see its monthly trend.")
        return

    fig = go.Figure()
    for i, issue in enumerate(selected):
        sub = monthly_df[monthly_df["issue"] == issue].sort_values("month")
        fig.add_trace(
            go.Scatter(
                x=sub["month"],
                y=sub["share_of_month"],
                mode="lines+markers",
                name=issue_label(issue),
                line=dict(color=LINE_PALETTE[i % len(LINE_PALETTE)], width=2.5),
                marker=dict(size=5),
            )
        )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans, sans-serif", color=COLORS["ink"], size=12),
        margin=dict(l=10, r=10, t=20, b=10),
        yaxis=dict(tickformat=".0%", gridcolor=COLORS["rule"], title="Share of month's reviews"),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=420,
    )
    st.plotly_chart(fig, width="stretch")

    st.divider()
    st.subheader("Trend direction, all categories")
    st.markdown(
        '<p class="lg-subtitle">Every category, not just the ones plotted above. '
        '"Insufficient data" means fewer than 4 distinct months had enough tagged reviews '
        'to compare halves. Read relative change as direction only, not a precise rate: a '
        '-66% relative change means the second half of the window had noticeably fewer '
        'mentions, not a rigorous "66% improvement."</p>',
        unsafe_allow_html=True,
    )
    st.write("")

    _trend_ledger(trend_df)


def _volume_chart(df) -> None:
    working = df.copy()
    working["month"] = working["review_date"].dt.to_period("M").astype(str)
    monthly_counts = working.groupby("month").size().sort_index()

    fig = go.Figure(
        go.Bar(
            x=monthly_counts.index,
            y=monthly_counts.values,
            marker_color=COLORS["interact"],
            text=[f"{v:,}" for v in monthly_counts.values],
            textposition="outside",
        )
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans, sans-serif", color=COLORS["ink"], size=12),
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(gridcolor=COLORS["rule"], title="Reviews collected"),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        height=260,
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch")


def _trend_ledger(trend_df) -> None:
    headers = ["Issue", "Trend", "1st half avg.", "2nd half avg.", "Relative change"]
    rows = []
    for _, row in trend_df.sort_values("issue").iterrows():
        arrow = trend_arrow(row["trend"])
        if row["trend"] == "insufficient_data":
            first_txt = second_txt = rel_txt = f'<span style="color:{COLORS["faint"]};">not enough months</span>'
        else:
            first_txt = format_pct(row["first_half_avg_share"])
            second_txt = format_pct(row["second_half_avg_share"])
            rel = row["relative_change"]
            rel_txt = f"{rel * 100:+.0f}%" if rel == rel and rel is not None else "n/a"

        rows.append([
            f"<strong>{issue_label(row['issue'])}</strong>",
            f"{arrow} {row['trend']}",
            first_txt,
            second_txt,
            rel_txt,
        ])

    ledger_table(headers, rows, col_classes=["", "", "lg-right", "lg-right", "lg-right"])