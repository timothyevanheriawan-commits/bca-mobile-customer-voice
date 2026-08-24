"""Drill into a single issue category and read the actual reviews behind it.

This is the "customer voice" part of customer voice - the other pages are
all aggregates, this one exists so a reader can sanity-check a category by
reading real complaints, not just trust the regex. Reviews render as
compact evidence records (rating, date, helpfulness, then text) with the
left rail colored by the same rating-severity tones used everywhere else
in the app.

Every card's inline color is set directly on `border-left`, not through a
CSS custom property (`--rail-color` + `var()`). An earlier pass used the
custom-property version and it produced a real bug: a stray literal
"</div>" rendering as its own card underneath the review it belonged to.
The likely cause is that Streamlit's HTML sanitizer does not reliably
preserve custom-property declarations inside an inline `style` attribute,
which can leave the attribute's quoting malformed and break the parser's
tag matching for the rest of that markdown block. Setting the color
directly removes the indirection entirely, which is both the simpler code
and the actual fix.
"""

from __future__ import annotations

import html
from collections import Counter

import plotly.graph_objects as go
import streamlit as st

from app.utils.definitions import get_definition
from app.utils.formatting import format_count, format_pct, issue_label
from app.utils.theme import COLORS, breadcrumb, callout, metric_row, rating_tone, tone_colors
from src.text_utils import tokenize

PAGE_SIZE = 25


def render(tables: dict) -> None:
    df = tables["reviews"]
    frequency_df = tables["frequency"]

    st.markdown(breadcrumb("Issue Explorer"), unsafe_allow_html=True)
    st.title("Issue Explorer")
    st.markdown(
        '<p class="lg-subtitle">Read the customer evidence behind each detected issue, '
        'one review at a time, before trusting the aggregate numbers elsewhere.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="lg-context">Google Play Reviews &middot; {len(df):,} analyzed</div>',
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

    callout(
        label="Category definition",
        title=issue_label(issue),
        detail=get_definition(issue),
        tone="primary",
    )
    st.write("")

    row = frequency_df[frequency_df["issue"] == issue].iloc[0]
    metric_row([
        {"label": "Total mentions", "value": format_count(row["n_mentions"]), "hero": True},
        {"label": "Share of negative reviews", "value": format_pct(row["share_of_negative_reviews"])},
        {"label": "From 1-2 star reviews", "value": format_pct(row["pct_from_1_2_star"])},
    ])

    issue_all = df[df["issues"].str.contains(issue, regex=False)]

    st.write("")
    col_ratings, col_terms = st.columns(2)
    with col_ratings:
        st.markdown(
            '<div class="lg-eyebrow" style="margin-bottom:6px;">Ratings for this issue</div>',
            unsafe_allow_html=True,
        )
        _rating_breakdown_chart(issue_all)
    with col_terms:
        st.markdown(
            '<div class="lg-eyebrow" style="margin-bottom:6px;">Frequent terms in matched reviews</div>',
            unsafe_allow_html=True,
        )
        _keyword_chart(issue_all)

    st.write("")
    st.markdown(
        '<div class="lg-eyebrow" style="margin-bottom:6px;">Filters</div>',
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

    tagged = issue_all[issue_all["rating"].isin(rating_filter)]

    if sort_order == "Most recent":
        tagged = tagged.sort_values("review_date", ascending=False)
    else:
        tagged = tagged.sort_values("thumbs_up", ascending=False)

    # Reset to page 1 whenever the issue or filters change, so switching
    # categories never leaves the reader stranded on an empty page 3.
    filter_signature = (issue, tuple(sorted(rating_filter)), sort_order)
    if st.session_state.get("_explorer_signature") != filter_signature:
        st.session_state["_explorer_page"] = 0
        st.session_state["_explorer_signature"] = filter_signature
    page = st.session_state.get("_explorer_page", 0)

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_df = tagged.iloc[start:end]

    range_end = min(end, len(tagged))
    range_label = f"{start + 1:,}-{range_end:,}" if len(tagged) else "0"
    st.markdown(
        f'<p class="lg-subtitle" style="margin-top:14px;">'
        f'Showing <strong style="color:{COLORS["ink"]};">{range_label}</strong> of '
        f'<strong style="color:{COLORS["ink"]};">{len(tagged):,}</strong> matching reviews.</p>',
        unsafe_allow_html=True,
    )
    st.write("")

    for _, r in page_df.iterrows():
        stars = "\u2605" * int(r["rating"]) + "\u2606" * (5 - int(r["rating"]))
        # tone_colors("neutral") resolves to near-black ink, which is fine
        # as a small-text default elsewhere (tags, stamps) but is actually
        # the highest-contrast color in the set at full-card-rail scale -
        # louder than the red/amber danger and warning rails next to it.
        # That inverts this page's own point: a 5-star review would visually
        # outshout a 1-star one. Route the "nothing wrong here" case (4-5
        # star) to a quiet, receded rail instead of the shared ink default.
        tone = rating_tone(r["rating"])
        rail_color = COLORS["rule"] if tone == "neutral" else tone_colors(tone)[0]
        date_str = r["review_date"].strftime("%d %b %Y")
        other_issues = [i for i in r["issues"].split(",") if i and i != issue]
        tags_html = "".join(
            f'<span class="lg-tag" style="color:{COLORS["interact"]};background-color:{COLORS["soft_blue"]};">{issue_label(i)}</span>'
            for i in other_issues
        )
        tags_block = f'<div class="lg-evidence-tags">{tags_html}</div>' if other_issues else ""

        # Escape raw review text (arbitrary user input) and collapse any
        # embedded newlines to <br>. Built as one unindented line on
        # purpose: a multi-line indented HTML string here previously got
        # misread as a markdown code block by the client-side renderer.
        text = html.escape(str(r["review_text"])).replace("\r\n", "\n").replace("\n", "<br>")

        card_html = (
            f'<div class="lg-evidence" style="border-left:3px solid {rail_color};">'
            f'<div class="lg-evidence-meta">'
            f'<span class="lg-evidence-stars" style="color:{rail_color};">{stars}</span>'
            f'<span>{date_str}</span><span>&middot;</span>'
            f'<span>{int(r["thumbs_up"])} found helpful</span>'
            f'</div>'
            f'<div class="lg-evidence-text">{text}</div>'
            f'{tags_block}'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

    st.write("")
    col_prev, col_page, col_next = st.columns([1, 2, 1])
    total_pages = max(1, -(-len(tagged) // PAGE_SIZE))  # ceil division
    with col_prev:
        if st.button("\u2190 Previous", disabled=(page == 0), width="stretch"):
            st.session_state["_explorer_page"] = page - 1
            st.rerun()
    with col_page:
        st.markdown(
            f'<p class="lg-subtitle" style="text-align:center;margin-top:6px;">'
            f'Page {page + 1} of {total_pages}</p>',
            unsafe_allow_html=True,
        )
    with col_next:
        if st.button("Next \u2192", disabled=(end >= len(tagged)), width="stretch"):
            st.session_state["_explorer_page"] = page + 1
            st.rerun()


def _rating_breakdown_chart(issue_df) -> None:
    counts = issue_df["rating"].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)
    star_colors = {
        1: COLORS["danger"], 2: COLORS["danger"],
        3: COLORS["warning"],
        4: COLORS["faint"], 5: COLORS["faint"],
    }
    fig = go.Figure(
        go.Bar(
            x=[f"{s}\u2605" for s in counts.index],
            y=counts.values,
            marker_color=[star_colors[s] for s in counts.index],
            text=[f"{v:,}" for v in counts.values],
            textposition="outside",
        )
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans, sans-serif", color=COLORS["ink"], size=11),
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(gridcolor=COLORS["rule"]),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        height=240,
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch")


def _keyword_chart(issue_df, top_k: int = 10) -> None:
    """Top terms actually present in the reviews matched to this category -
    lets a reader sanity-check the regex against real vocabulary rather
    than just the rule pattern in Methodology."""
    counter = Counter()
    for text in issue_df["review_text"]:
        counter.update(tokenize(text))
    top_terms = counter.most_common(top_k)

    if not top_terms:
        st.info("Not enough matched reviews to extract terms.")
        return

    terms, counts = zip(*top_terms)
    fig = go.Figure(
        go.Bar(
            x=counts[::-1],
            y=terms[::-1],
            orientation="h",
            marker_color=COLORS["interact"],
            text=[f"{c:,}" for c in counts[::-1]],
            textposition="outside",
        )
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans, sans-serif", color=COLORS["ink"], size=11),
        margin=dict(l=10, r=30, t=10, b=10),
        xaxis=dict(gridcolor=COLORS["rule"]),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        height=240,
    )
    st.plotly_chart(fig, width="stretch")