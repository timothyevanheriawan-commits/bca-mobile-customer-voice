"""Month-by-month view of how each issue's share of reviews is moving.

Mirrors notebook 05's approach on purpose: first-half vs second-half
comparison, not a fitted regression line - see src/analysis.py docstring
for why (too few months, too much noise for a trend line to mean anything).
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from app.utils.formatting import format_pct, issue_label, trend_arrow
from app.utils.theme import COLORS


def render(tables: dict) -> None:
    monthly_df = tables["monthly"]
    trend_df = tables["trend"]

    st.markdown('<div class="fr-eyebrow">Over Time</div>', unsafe_allow_html=True)
    st.title("Is each issue getting more or less common?")
    st.markdown(
        '<p class="fr-muted">Share of that month\u2019s reviews mentioning each issue '
        '\u2014 not raw counts, so a category isn\u2019t read as "growing" just because '
        'total review volume grew that month.</p>',
        unsafe_allow_html=True,
    )
    st.divider()

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
    palette = ["#2453A6", "#B3261E", "#B8860B", "#2E7D32", "#6B4EA0", "#1C2541"]
    for i, issue in enumerate(selected):
        sub = monthly_df[monthly_df["issue"] == issue].sort_values("month")
        fig.add_trace(
            go.Scatter(
                x=sub["month"],
                y=sub["share_of_month"],
                mode="lines+markers",
                name=issue_label(issue),
                line=dict(color=palette[i % len(palette)], width=2.5),
            )
        )

    fig.update_layout(
        plot_bgcolor=COLORS["surface"],
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Mono", color=COLORS["ink"]),
        margin=dict(l=10, r=10, t=20, b=10),
        yaxis=dict(tickformat=".0%", gridcolor=COLORS["border"], title="Share of month's reviews"),
        xaxis=dict(gridcolor=COLORS["border"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=440,
    )
    st.plotly_chart(fig, width="stretch")

    st.divider()
    st.subheader("Trend direction, all categories")

    for _, row in trend_df.sort_values("issue").iterrows():
        arrow = trend_arrow(row["trend"])
        cols = st.columns([2.5, 1, 1.3, 1.3, 1.3])
        cols[0].markdown(f"**{issue_label(row['issue'])}**")
        cols[1].markdown(f"{arrow} {row['trend']}")
        if row["trend"] == "insufficient_data":
            cols[2].markdown("&mdash;", unsafe_allow_html=True)
            cols[3].markdown("&mdash;", unsafe_allow_html=True)
            cols[4].markdown("&mdash;", unsafe_allow_html=True)
        else:
            cols[2].markdown(f"1st half: {format_pct(row['first_half_avg_share'])}")
            cols[3].markdown(f"2nd half: {format_pct(row['second_half_avg_share'])}")
            rel = row["relative_change"]
            rel_txt = f"{rel*100:+.0f}%" if rel == rel and rel is not None else "\u2013"
            cols[4].markdown(f"rel. change: {rel_txt}")

    st.markdown(
        '<p class="fr-muted" style="margin-top:10px;">Read direction only, not magnitude '
        '\u2014 a -66% relative change means the second half of the window had noticeably '
        'fewer mentions, not a rigorous "66% improvement."</p>',
        unsafe_allow_html=True,
    )
