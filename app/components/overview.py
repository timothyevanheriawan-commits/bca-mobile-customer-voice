"""Landing page: how big is the problem, and what should get worked on first.

The priority table here is rendered directly from
`src.prioritization.build_priority_table` - not a hardcoded summary - so a
category sitting at "needs_regex_fix" shows up as exactly that, in red, with
its caveat text, rather than silently looking as solid as a validated one.
The top row of that same table drives the hero signal banner, so the page's
single most important claim can never drift out of sync with the table
underneath it.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from app.utils.formatting import (
    format_count,
    format_pct,
    issue_label,
    tier_color,
    tier_tone,
    trend_arrow,
    validation_color,
    validation_tone,
)
from app.utils.theme import COLORS, breadcrumb, metric_row, signal_banner, tag


def render(tables: dict) -> None:
    df = tables["reviews"]
    priority_df = tables["priority"]

    st.markdown(breadcrumb("Overview"), unsafe_allow_html=True)
    st.title("Customer Voice")
    st.markdown(
        '<p class="ci-subtitle">What customers are hitting, ranked by what to fix first.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="ci-context">Google Play Reviews &middot; {len(df):,} analyzed &middot; '
        f'{df["review_date"].min().strftime("%b %Y")}&ndash;{df["review_date"].max().strftime("%b %Y")}</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    # --- Top priority signal --------------------------------------------
    top = priority_df.iloc[0]
    top_arrow = trend_arrow(top["trend"])
    detail = (
        f"{format_pct(top['share_of_negative_reviews'])} of negative reviews &middot; "
        f"{format_count(top['n_mentions'])} mentions &middot; trend {top_arrow} {top['trend']}"
    )
    if top["caveat"]:
        detail += f" &mdash; {top['caveat']}"
    signal_banner(
        label=f"Top priority signal &middot; {top['priority_tier']}",
        title=issue_label(top["issue"]),
        detail=detail,
        tone=tier_tone(top["priority_tier"]),
    )

    st.write("")

    # --- Key metrics -------------------------------------------------------
    negative = (df["rating_group"] == "negative").sum()
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

    st.divider()
    st.subheader("Priority table")
    st.markdown(
        '<p class="ci-subtitle">Ranked High &rarr; Low. A category is High if it\u2019s a '
        'money-affecting issue above the frequency floor, or any issue above the floor '
        'that\u2019s trending up. See <code>src/prioritization.py</code> for the exact rule.</p>',
        unsafe_allow_html=True,
    )
    st.write("")

    for _, row in priority_df.iterrows():
        status = row["validation_status"]
        status_label = status if isinstance(status, str) else "unvalidated"
        arrow = trend_arrow(row["trend"])
        precision_txt = (
            f" ({row['precision']:.2f})"
            if row.get("precision") == row.get("precision") and row.get("precision") is not None
            else ""
        )

        cols = st.columns([2.8, 1, 1.2, 1.3, 1.4, 1.7])
        cols[0].markdown(f"**{issue_label(row['issue'])}**")
        cols[1].markdown(tag(row["priority_tier"], tier_tone(row["priority_tier"])), unsafe_allow_html=True)
        cols[2].markdown(f'<span class="ci-mono">{format_count(row["n_mentions"])}</span> mentions', unsafe_allow_html=True)
        cols[3].markdown(f'<span class="ci-mono">{format_pct(row["share_of_negative_reviews"])}</span> negatives', unsafe_allow_html=True)
        cols[4].markdown(f"trend {arrow} {row['trend']}")
        cols[5].markdown(
            tag(f"{status_label}{precision_txt}", validation_tone(status_label)),
            unsafe_allow_html=True,
        )
        if row["caveat"]:
            cols[0].markdown(
                f'<div style="font-size:0.78rem;color:{COLORS["warning"]};margin-top:2px;">&#9888; {row["caveat"]}</div>',
                unsafe_allow_html=True,
            )
        st.markdown(f'<hr style="margin:6px 0;border-color:{COLORS["border"]};">', unsafe_allow_html=True)

    st.write("")
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
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=COLORS["ink"], size=12),
        margin=dict(l=10, r=40, t=10, b=10),
        xaxis=dict(tickformat=".0%", gridcolor=COLORS["border"]),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        height=420,
    )
    st.plotly_chart(fig, width="stretch")