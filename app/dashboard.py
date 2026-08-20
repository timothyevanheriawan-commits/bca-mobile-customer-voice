"""Entry point for the BCA Mobile Customer Voice dashboard.

Run with: streamlit run app/dashboard.py

Follows the same st.navigation/st.Page pattern used in the Retention/RFM
and TransJakarta dashboards - one entry point, thin, all real logic lives in
app/components/*.py and is fed by the cached loaders in app/utils/data_loader.py.
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
from app.utils.theme import inject_css

st.set_page_config(
    page_title="BCA Mobile — Customer Voice",
    page_icon="\U0001F4EC",
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


pages = [
    st.Page(_overview_page, title="Overview & Priority", icon="\U0001F4CB", default=True),
    st.Page(_trends_page, title="Trends", icon="\U0001F4C8"),
    st.Page(_explorer_page, title="Issue Explorer", icon="\U0001F50D"),
    st.Page(_methodology_page, title="Methodology", icon="\U0001F4D0"),
]

nav = st.navigation(pages)

with st.sidebar:
    st.markdown(
        '<div class="fr-eyebrow" style="margin-top:4px;">BCA Mobile</div>'
        '<h3 style="margin-top:0;">Customer Voice</h3>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="fr-muted">Play Store review analysis: what customers are '
        'hitting, how often, and how confident we are in the count.</p>',
        unsafe_allow_html=True,
    )
    st.divider()

nav.run()
