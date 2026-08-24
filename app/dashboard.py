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
from app.utils.theme import COLORS, inject_css, sidebar_tier_counts

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
# Icons are Streamlit's built-in Material set - picked to read as ledger
# actions (scan / chart / search / ruler) rather than generic app-nav
# icons, so the nav keeps the "workpaper" character instead of looking
# like a stock sidebar.
pages = [
    st.Page(_overview_page, title="Overview", icon=":material/receipt_long:", url_path="overview", default=True),
    st.Page(_trends_page, title="Trends", icon=":material/show_chart:", url_path="trends"),
    st.Page(_explorer_page, title="Issue Explorer", icon=":material/manage_search:", url_path="issue-explorer"),
    st.Page(_methodology_page, title="Methodology", icon=":material/rule:", url_path="methodology"),
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

    # Trimmed to the one thing the sidebar can say that the nav links
    # can't: how many issues are open at each priority tier, right now,
    # from any page. Dataset status, the validation coverage strip, and
    # the footer tagline all either repeated what the Overview/Methodology
    # pages already say in full, or were pure branding - cut rather than
    # kept as dead weight next to the nav.
    st.markdown(sidebar_tier_counts(TABLES["priority"]), unsafe_allow_html=True)

nav.run()