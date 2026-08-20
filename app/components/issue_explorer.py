"""Drill into a single issue category and read the actual reviews behind it.

This is the "customer voice" part of customer voice - the other pages are
all aggregates, this one exists so a reader can sanity-check a category by
reading real complaints, not just trust the regex.
"""

from __future__ import annotations

import streamlit as st

from app.utils.formatting import format_count, format_pct, issue_label


def render(tables: dict) -> None:
    df = tables["reviews"]
    frequency_df = tables["frequency"]

    st.markdown('<div class="fr-eyebrow">Customer Voice</div>', unsafe_allow_html=True)
    st.title("Read the reviews behind a category")
    st.divider()

    all_issues = frequency_df["issue"].tolist()
    issue = st.selectbox(
        "Issue category",
        options=all_issues,
        format_func=issue_label,
    )

    row = frequency_df[frequency_df["issue"] == issue].iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Mentions", format_count(row["n_mentions"]))
    c2.metric("Share of negative reviews", format_pct(row["share_of_negative_reviews"]))
    c3.metric("From 1-2 star reviews", format_pct(row["pct_from_1_2_star"]))

    st.divider()

    col_a, col_b = st.columns([1, 1])
    with col_a:
        rating_filter = st.multiselect(
            "Filter by star rating", options=[1, 2, 3, 4, 5], default=[1, 2, 3, 4, 5]
        )
    with col_b:
        sort_order = st.radio("Sort by", ["Most recent", "Most helpful (thumbs up)"], horizontal=True)

    tagged = df[df["issues"].str.contains(issue, regex=False)]
    tagged = tagged[tagged["rating"].isin(rating_filter)]

    if sort_order == "Most recent":
        tagged = tagged.sort_values("review_date", ascending=False)
    else:
        tagged = tagged.sort_values("thumbs_up", ascending=False)

    st.markdown(f"**{len(tagged):,} reviews** match this filter.")

    for _, r in tagged.head(25).iterrows():
        stars = "\u2605" * int(r["rating"]) + "\u2606" * (5 - int(r["rating"]))
        date_str = r["review_date"].strftime("%d %b %Y")
        other_issues = [i for i in r["issues"].split(",") if i and i != issue]
        other_txt = ""
        if other_issues:
            other_txt = " &middot; also: " + ", ".join(issue_label(i) for i in other_issues)

        st.markdown(
            f'''<div class="fr-card">
                <div class="fr-muted">{stars} &nbsp;&middot;&nbsp; {date_str}
                &nbsp;&middot;&nbsp; {int(r["thumbs_up"])} found helpful{other_txt}</div>
                <p style="margin-top:6px;">{r["review_text"]}</p>
            </div>''',
            unsafe_allow_html=True,
        )

    if len(tagged) > 25:
        st.markdown(f'<p class="fr-muted">Showing 25 of {len(tagged):,} matching reviews.</p>', unsafe_allow_html=True)
