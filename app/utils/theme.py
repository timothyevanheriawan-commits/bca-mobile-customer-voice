"""Design tokens and the single CSS block injected once from dashboard.py.

Direction: "field report" - this app is turning raw customer complaints into
something a product team reads like a briefing, not a generic BI tool. Warm
paper background, navy ink for text, a restrained accent blue, and signal
colors reserved for priority/validation status so they carry real meaning
rather than decorating everything.
"""

from __future__ import annotations

import streamlit as st

COLORS = {
    "bg": "#FAF8F4",
    "surface": "#FFFFFF",
    "ink": "#1C2541",
    "muted": "#6B7280",
    "accent": "#2453A6",
    "border": "#E5E1D8",
    "danger": "#B3261E",
    "warning": "#B8860B",
    "success": "#2E7D32",
}

FONT_HEADING = "'Manrope', sans-serif"
FONT_MONO = "'IBM Plex Mono', monospace"


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@500;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

        html, body, [class*="css"] {{
            font-family: {FONT_MONO};
            color: {COLORS['ink']};
        }}

        .stApp {{
            background-color: {COLORS['bg']};
        }}

        h1, h2, h3, h4 {{
            font-family: {FONT_HEADING};
            font-weight: 800;
            color: {COLORS['ink']};
            letter-spacing: -0.01em;
        }}

        [data-testid="stSidebar"] {{
            background-color: {COLORS['surface']};
            border-right: 1px solid {COLORS['border']};
        }}

        [data-testid="stMetric"] {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: 14px 16px 10px 16px;
        }}

        [data-testid="stMetricLabel"] {{
            font-family: {FONT_HEADING};
            font-weight: 700;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: {COLORS['muted']};
        }}

        [data-testid="stMetricValue"] {{
            font-family: {FONT_MONO};
            font-weight: 600;
        }}

        .fr-eyebrow {{
            font-family: {FONT_HEADING};
            font-weight: 700;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: {COLORS['accent']};
            margin-bottom: 2px;
        }}

        .fr-tag {{
            display: inline-block;
            font-family: {FONT_MONO};
            font-weight: 600;
            font-size: 0.72rem;
            padding: 2px 8px;
            border-radius: 4px;
            color: #fff;
            letter-spacing: 0.02em;
        }}

        .fr-card {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 16px 18px;
            margin-bottom: 10px;
        }}

        .fr-caveat {{
            font-family: {FONT_MONO};
            font-size: 0.82rem;
            color: {COLORS['warning']};
            margin-top: 4px;
        }}

        .fr-muted {{
            color: {COLORS['muted']};
            font-size: 0.85rem;
        }}

        hr {{
            border-color: {COLORS['border']};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
