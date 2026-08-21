"""Entry point for the BCA Mobile Customer Voice dashboard.

Run with: streamlit run app/dashboard.py

Follows the same st.navigation/st.Page pattern used in the Retention/RFM
and TransJakarta dashboards - one entry point, thin, all real logic lives
in app/components/*.py and is fed by the cached loaders in
app/utils/data_loader.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.components import issue_explorer, methodology, overview, trends
from app.utils.data_loader import load_all
from app.utils.formatting import format_count
from app.utils.theme import COLORS, inject_css

st.set_page_config(
    page_title="BCA Mobile Customer Voice Ledger",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

TABLES = load_all()


def _overview_page():
    overview.render(TABLES)


def _trends_page():
    trends.render(TABLES)


def _explorer_page():
    issue_explorer.render(TABLES)


def _methodology_page():
    methodology.render(TABLES)


# --- Pages -----------------------------------------------------------------
# position="hidden": Streamlit's built-in nav menu auto-injects itself at
# the very top of the sidebar no matter where in the script it's called,
# which meant the brand block below always rendered UNDER the nav list
# regardless of code order - the opposite of what the layout intended.
# Building the nav list by hand with st.page_link instead means the
# sidebar actually renders in the order it's written: brand -> nav ->
# dataset status.
pages = [
    st.Page(_overview_page, title="Overview", url_path="overview", default=True),
    st.Page(_trends_page, title="Trends", url_path="trends"),
    st.Page(_explorer_page, title="Issue Explorer", url_path="issue-explorer"),
    st.Page(_methodology_page, title="Methodology", url_path="methodology"),
]

nav = st.navigation(pages, position="hidden")

# --- Sidebar: cover-sheet identity block, above the nav list ------------
# Built as single-line fragments on purpose: a multi-line indented HTML
# string gets misread as a markdown code block by the client-side
# renderer, which is what caused a stray literal "</div>" to leak into
# the Issue Explorer cards in an earlier pass. Keeping every fragment on
# one line, and avoiding CSS custom properties inside inline style
# attributes (they can trip the HTML sanitizer the same way), is the
# actual fix - see issue_explorer.py for where that bug lived.
with st.sidebar:
    brand_html = (
        '<div style="display:flex;align-items:center;gap:10px;">'
        f'<div style="width:32px;height:32px;border-radius:2px;background:{COLORS["primary"]};'
        'color:#fff;display:flex;align-items:center;justify-content:center;'
        'font-family:\'Space Grotesk\',sans-serif;font-weight:700;font-size:0.95rem;">B</div>'
        f'<div style="font-family:\'Space Grotesk\',sans-serif;font-weight:700;font-size:0.95rem;'
        f'color:{COLORS["ink"]};line-height:1.15;">BCA Mobile</div>'
        '</div>'
        '<div class="lg-eyebrow" style="margin-top:12px;margin-bottom:0;">Ledger No. CV-2026-08</div>'
        f'<div style="font-family:\'IBM Plex Sans\',sans-serif;font-weight:600;font-size:0.84rem;'
        f'color:{COLORS["muted"]};margin-top:1px;">Customer Voice Audit</div>'
    )
    st.markdown(brand_html, unsafe_allow_html=True)
    st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)

    # Nav list, styled as ledger entries (same "Entry NN" language as the
    # Methodology pipeline flow) instead of bare default page links, so
    # the sidebar reads as part of the same design system rather than a
    # generic widget.
    #
    # The active page is rendered as plain styled text, not a link -
    # deliberately not relying on Streamlit's own active-link styling
    # (its DOM markup for that turns out to use per-session emotion-cache
    # class hashes with no stable attribute to hook a CSS selector to,
    # confirmed by inspecting the rendered page rather than assumed).
    # `nav` is the actual running Page object, so comparing against it is
    # a real signal instead of a guess.
    # All four rows live inside ONE container with an explicit small gap,
    # rather than as four separate top-level st.columns() calls. Each
    # st.columns() call is its own block in the sidebar's vertical stack,
    # and Streamlit adds its default ~1rem gap between every block, not
    # just between columns within a row - four separate calls meant four
    # stacked gaps, which is what was making the nav read as loose/uneven
    # and inflating the empty space before the divider below it.
    with st.container(gap="xsmall"):
        for i, page in enumerate(pages, start=1):
            cols = st.columns([1, 5], gap="small", vertical_alignment="center")
            with cols[0]:
                st.markdown(f'<div class="lg-nav-index">{i:02d}</div>', unsafe_allow_html=True)
            with cols[1]:
                if page is nav:
                    st.markdown(
                        f'<div class="lg-nav-active">{page.title}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.page_link(page, label=page.title)

    st.divider()

    review_count = format_count(len(TABLES["reviews"]))
    status_html = (
        '<div class="lg-eyebrow" style="margin-bottom:2px;">Dataset</div>'
        f'<div style="font-family:\'IBM Plex Sans\',sans-serif;font-weight:600;font-size:0.84rem;'
        f'color:{COLORS["ink"]};">Google Play Reviews</div>'
        f'<div class="lg-mono" style="font-size:0.74rem;color:{COLORS["success"]};margin-top:4px;">'
        f'Ready for review &middot; {review_count} reviews logged</div>'
    )
    st.markdown(status_html, unsafe_allow_html=True)

nav.run()