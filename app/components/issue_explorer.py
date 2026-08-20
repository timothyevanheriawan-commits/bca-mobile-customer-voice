"""Drill into a single issue category and read the actual reviews behind it.

This is the "customer voice" part of customer voice - the other pages are
all aggregates, this one exists so a reader can sanity-check a category by
reading real complaints, not just trust the regex. Reviews render as compact
evidence records (rating, date, helpfulness, then text) rather than blog-
style cards, with the left rail colored by the same rating-severity tones
used everywhere else in the app.
"""

from __future__ import annotations

import html

import streamlit as st

from app.utils.formatting import format_count, format_pct, issue_label
from app.utils.theme import COLORS, tone_colors, breadcrumb, metric_row, rating_tone


def render(tables: dict) -> None:
    df = tables["reviews"]
    frequency_df = tables["frequency"]

    st.markdown(breadcrumb("Issue Explorer"), unsafe_allow_html=True)
    st.title("Issue Explorer")
    st.markdown(
        '<p class="ci-subtitle">Read the customer evidence behind each detected issue.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="ci-context">Google Play Reviews &middot; {len(df):,} analyzed</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    all_issues = frequency_df["issue"].tolist()
    issue = st.selectbox(
        "Issue category",
        options=all_issues,
        format_func=issue_label,
        label_visibility="collapsed",
    )

    row = frequency_df[frequency_df["issue"] == issue].iloc[0]
    metric_row([
        {"label": "Total mentions", "value": format_count(row["n_mentions"]), "hero": True},
        {"label": "Share of negative reviews", "value": format_pct(row["share_of_negative_reviews"])},
        {"label": "From 1-2 star reviews", "value": format_pct(row["pct_from_1_2_star"])},
    ])

    st.write("")
    st.markdown(
        '<div class="ci-breadcrumb" style="margin-bottom:6px;">Filters</div>',
        unsafe_allow_html=True,
    )
    col_a, col_b = st.columns([2, 1])
    with col_a:
        rating_filter = st.segmented_control(
            "Rating",
            options=[1, 2, 3, 4, 5],
            selection_mode="multi",
            default=[1, 2, 3, 4, 5],
            format_func=lambda r: f"{r}\u2605",
        )
    with col_b:
        sort_order = st.segmented_control(
            "Sort",
            options=["Most recent", "Most helpful"],
            default="Most recent",
        )

    rating_filter = rating_filter or [1, 2, 3, 4, 5]
    sort_order = sort_order or "Most recent"

    tagged = df[df["issues"].str.contains(issue, regex=False)]
    tagged = tagged[tagged["rating"].isin(rating_filter)]

    if sort_order == "Most recent":
        tagged = tagged.sort_values("review_date", ascending=False)
    else:
        tagged = tagged.sort_values("thumbs_up", ascending=False)

    st.markdown(
        f'<p class="ci-subtitle" style="margin-top:14px;">'
        f'<strong style="color:{COLORS["ink"]};">{len(tagged):,} reviews</strong> match this filter.</p>',
        unsafe_allow_html=True,
    )
    st.write("")

    for _, r in tagged.head(25).iterrows():
        stars = "\u2605" * int(r["rating"]) + "\u2606" * (5 - int(r["rating"]))
        rail_color, _ = tone_colors(rating_tone(r["rating"]))
        date_str = r["review_date"].strftime("%d %b %Y")
        other_issues = [i for i in r["issues"].split(",") if i and i != issue]
        tags_html = "".join(
            f'<span class="ci-tag" style="color:{COLORS["interact"]};background-color:{COLORS["soft_blue"]};margin-right:4px;">{issue_label(i)}</span>'
            for i in other_issues
        )
        tags_block = f'<div class="ci-evidence-tags">{tags_html}</div>' if other_issues else ""

        # Escape raw review text (arbitrary user input) and collapse any
        # embedded newlines to <br> - built as one unindented line on
        # purpose, since a multi-line indented HTML string here previously
        # got misread as a markdown code block, leaking a literal "</div>".
        text = html.escape(str(r["review_text"])).replace("\r\n", "\n").replace("\n", "<br>")

        card_html = (
            f'<div class="ci-evidence" style="--rail-color:{rail_color};">'
            f'<div class="ci-evidence-meta">'
            f'<span class="ci-evidence-stars" style="color:{rail_color};">{stars}</span>'
            f'<span>{date_str}</span><span>&middot;</span>'
            f'<span>{int(r["thumbs_up"])} found helpful</span>'
            f'</div>'
            f'<div class="ci-evidence-text">{text}</div>'
            f'{tags_block}'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

    if len(tagged) > 25:
        st.markdown(
            f'<p class="ci-subtitle">Showing 25 of {len(tagged):,} matching reviews.</p>',
            unsafe_allow_html=True,
        )