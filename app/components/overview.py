"""Landing page: how big is the problem, and what should get worked on first.

The priority table here is rendered directly from
`src.prioritization.build_priority_table` - not a hardcoded summary - so a
category sitting at "needs_regex_fix" shows up as exactly that, in red, with
its caveat text, rather than silently looking as solid as a validated one.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from app.utils.formatting import (
    format_count,
    format_pct,
    issue_label,
    tier_color,
    trend_arrow,
    validation_color,
)
from app.utils.theme import COLORS


def render(tables: dict) -> None:
    df = tables["reviews"]
    priority_df = tables["priority"]

    st.markdown('<div class="fr-eyebrow">BCA Mobile &middot; Customer Voice</div>', unsafe_allow_html=True)
    st.title("What customers are hitting, ranked by what to fix first")
    st.markdown(
        f'<p class="fr-muted">{len(df):,} Play Store reviews collected '
        f'{df["review_date"].min().strftime("%b %Y")} &ndash; '
        f'{df["review_date"].max().strftime("%b %Y")}. '
        f'Every number below is computed live from the current classifier and '
        f'validation data \u2014 see the Methodology page for how.</p>',
        unsafe_allow_html=True,
    )

    st.divider()

    negative = (df["rating_group"] == "negative").sum()
    tagged = int(df["has_issue"].sum())
    n_high = int((priority_df["priority_tier"] == "High").sum())
    n_needs_fix = int((priority_df["validation_status"] == "needs_regex_fix").sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total reviews", format_count(len(df)))
    c2.metric("Negative reviews", format_count(negative), format_pct(negative / len(df)))
    c3.metric("High priority issues", format_count(n_high))
    c4.metric("Categories needing regex fix", format_count(n_needs_fix),
              delta=None if n_needs_fix == 0 else "check before quoting",
              delta_color="inverse")

    st.divider()
    st.subheader("Priority table")
    st.markdown(
        '<p class="fr-muted">Ranked High &rarr; Low. A category is High if it\u2019s a '
        'money-affecting issue above the frequency floor, or any issue above the '
        'floor that\u2019s trending up. See <code>src/prioritization.py</code> for the exact rule.</p>',
        unsafe_allow_html=True,
    )

    for _, row in priority_df.iterrows():
        tier = row["priority_tier"]
        status = row["validation_status"]
        arrow = trend_arrow(row["trend"])

        cols = st.columns([3, 1.1, 1.3, 1.3, 1.6, 3.2])
        cols[0].markdown(f"**{issue_label(row['issue'])}**")
        cols[1].markdown(
            f'<span class="fr-tag" style="background-color:{tier_color(tier)}">{tier}</span>',
            unsafe_allow_html=True,
        )
        cols[2].markdown(f"{format_count(row['n_mentions'])} mentions")
        cols[3].markdown(f"{format_pct(row['share_of_negative_reviews'])} of negatives")
        cols[4].markdown(f"trend {arrow} {row['trend']}")
        status_label = status if isinstance(status, str) else "unvalidated"
        precision_txt = f" ({row['precision']:.2f})" if row.get("precision") == row.get("precision") and row.get("precision") is not None else ""
        cols[5].markdown(
            f'<span class="fr-tag" style="background-color:{validation_color(status_label)}">'
            f'{status_label}{precision_txt}</span>',
            unsafe_allow_html=True,
        )
        if row["caveat"]:
            st.markdown(f'<div class="fr-caveat">&#9888; {row["caveat"]}</div>', unsafe_allow_html=True)
        st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)

    st.divider()
    st.subheader("Share of negative reviews, by issue")

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
        plot_bgcolor=COLORS["surface"],
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Mono", color=COLORS["ink"]),
        margin=dict(l=10, r=40, t=10, b=10),
        xaxis=dict(tickformat=".0%", gridcolor=COLORS["border"]),
        height=420,
    )
    st.plotly_chart(fig, width="stretch")
