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
pages = [
    st.Page(_overview_page, title="01  Overview", url_path="overview", default=True),
    st.Page(_trends_page, title="02  Trends", url_path="trends"),
    st.Page(_explorer_page, title="03  Issue Explorer", url_path="issue-explorer"),
    st.Page(_methodology_page, title="04  Methodology", url_path="methodology"),
]

nav = st.navigation(pages, position="sidebar")

# --- Sidebar Content -------------------------------------------------------
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

    # Let st.navigation render native links naturally without column loops
    # ...

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