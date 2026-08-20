"""Design tokens, CSS injection, and small shared HTML components.

Direction: "Customer Intelligence Console" — a cool-neutral banking
analytics workspace, not a report or a generic Streamlit dashboard. Reviews
become issue signals, signals become priorities, priorities become evidence
a reader can check for themselves. Blue carries navigation/identity, red /
amber / green are reserved strictly for severity, trend, and validation
confidence so they keep real meaning instead of decorating every element.

Every page pulls its colors, spacing, and shared HTML fragments (metric
rows, tags, the pipeline flow) from here rather than hardcoding hex values
or writing one-off markup — that's the point of centralizing this module.
"""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------

COLORS = {
    # Surfaces
    "bg": "#F5F7FA",
    "surface": "#FFFFFF",
    "surface_soft": "#F8FAFC",
    # Text
    "ink": "#172033",
    "muted": "#667085",
    "faint": "#98A2B3",
    # Border
    "border": "#E1E7EF",
    # Brand / interaction
    "primary": "#0A4FA3",
    "interact": "#1677D2",
    "soft_blue": "#EAF2FB",
    "navy": "#102A43",
    # Semantic — reserved for severity / trend / confidence, nothing else
    "danger": "#C1352E",
    "danger_soft": "#FBEAEA",
    "warning": "#B7791F",
    "warning_soft": "#FBF3E3",
    "success": "#1E8E5A",
    "success_soft": "#E9F6EF",
    "neutral_soft": "#EEF1F5",
}

FONT_HEADING = "'Inter', sans-serif"
FONT_BODY = "'Inter', sans-serif"
FONT_MONO = "'IBM Plex Mono', monospace"

# Backwards-compatible aliases (formatting.py and components read these).
TIER_COLORS = {
    "High": COLORS["danger"],
    "Medium": COLORS["warning"],
    "Low": COLORS["success"],
}

VALIDATION_COLORS = {
    "validated": COLORS["success"],
    "partially_validated": COLORS["warning"],
    "needs_regex_fix": COLORS["danger"],
    "unvalidated": COLORS["faint"],
}

# 1-2 stars read as risk signal, 3 as a caution signal, 4-5 as settled —
# this is the one place star rating maps to color, reused by the segmented
# rating filter and the evidence cards so they never drift apart.
RATING_TONES = {
    1: "danger", 2: "danger",
    3: "warning",
    4: "neutral", 5: "neutral",
}


def rating_tone(rating: int) -> str:
    return RATING_TONES.get(int(rating), "neutral")


def tone_colors(tone: str) -> tuple[str, str]:
    """(foreground, soft-background) for a semantic tone name."""
    return {
        "danger": (COLORS["danger"], COLORS["danger_soft"]),
        "warning": (COLORS["warning"], COLORS["warning_soft"]),
        "success": (COLORS["success"], COLORS["success_soft"]),
        "neutral": (COLORS["ink"], COLORS["neutral_soft"]),
        "primary": (COLORS["interact"], COLORS["soft_blue"]),
    }.get(tone, (COLORS["muted"], COLORS["neutral_soft"]))


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

        html, body, [class*="css"] {{
            font-family: {FONT_BODY};
            color: {COLORS['ink']};
        }}

        .stApp {{
            background-color: {COLORS['bg']};
        }}

        .block-container {{
            padding-top: 2.2rem;
            max-width: 1180px;
        }}

        h1, h2, h3, h4 {{
            font-family: {FONT_HEADING};
            color: {COLORS['ink']};
            letter-spacing: -0.015em;
        }}

        h1 {{ font-size: 1.9rem; font-weight: 800; margin-bottom: 0.15rem; }}
        h2 {{ font-size: 1.25rem; font-weight: 700; }}
        h3 {{ font-size: 1.1rem; font-weight: 700; }}

        p, span, div, label {{ font-family: {FONT_BODY}; }}

        code, .ci-mono {{
            font-family: {FONT_MONO} !important;
        }}

        hr {{
            border-color: {COLORS['border']};
            margin: 1.1rem 0;
        }}

        /* ---------------------------------------------------------- */
        /* Sidebar / product shell                                    */
        /* ---------------------------------------------------------- */

        [data-testid="stSidebar"] {{
            background-color: {COLORS['surface']};
            border-right: 1px solid {COLORS['border']};
        }}

        [data-testid="stSidebar"] .block-container {{
            padding-top: 1.6rem;
        }}

        [data-testid="stSidebarNav"] {{
            padding-top: 0.4rem;
        }}

        [data-testid="stSidebarNavLink"] {{
            border-radius: 8px;
            font-family: {FONT_HEADING};
            font-weight: 600;
            font-size: 0.88rem;
            color: {COLORS['muted']};
            padding: 0.4rem 0.6rem;
            margin-bottom: 2px;
            transition: background-color 0.12s ease;
        }}

        [data-testid="stSidebarNavLink"]:hover {{
            background-color: {COLORS['surface_soft']};
        }}

        [data-testid="stSidebarNavLink"][aria-current="page"] {{
            background-color: {COLORS['soft_blue']};
            color: {COLORS['interact']};
        }}

        [data-testid="stSidebarNavLink"][aria-current="page"] span {{
            color: {COLORS['interact']};
        }}

        /* ---------------------------------------------------------- */
        /* Metric widgets (used sparingly; most metrics use ci-metric) */
        /* ---------------------------------------------------------- */

        [data-testid="stMetric"] {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
            padding: 12px 16px;
        }}

        [data-testid="stMetricLabel"] {{
            font-family: {FONT_HEADING};
            font-weight: 600;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: {COLORS['muted']};
        }}

        [data-testid="stMetricValue"] {{
            font-family: {FONT_MONO};
            font-weight: 600;
            color: {COLORS['ink']};
        }}

        /* ---------------------------------------------------------- */
        /* Controls — pull selects / multiselects / segmented control */
        /* toward one consistent, compact visual language              */
        /* ---------------------------------------------------------- */

        [data-baseweb="select"] > div {{
            border-radius: 8px;
            border-color: {COLORS['border']};
            background-color: {COLORS['surface']};
            font-family: {FONT_BODY};
        }}

        [data-testid="stMultiSelectTagsContainer"] span[data-tag] {{
            background-color: {COLORS['soft_blue']} !important;
            color: {COLORS['interact']} !important;
            border-radius: 6px !important;
        }}

        [data-testid="stMultiSelectTagsContainer"] span[data-tag] button {{
            color: {COLORS['interact']} !important;
        }}

        [data-testid="stButtonGroup"] button {{
            font-family: {FONT_HEADING} !important;
            font-size: 0.82rem !important;
            border-radius: 999px !important;
            border-color: {COLORS['border']} !important;
            color: {COLORS['muted']} !important;
            background-color: {COLORS['surface']} !important;
        }}

        [data-testid="stButtonGroup"] button[data-selected="true"] {{
            background-color: {COLORS['soft_blue']} !important;
            border-color: {COLORS['soft_blue']} !important;
            color: {COLORS['interact']} !important;
        }}

        [data-testid="stButtonGroup"] button[data-selected="true"] p {{
            color: {COLORS['interact']} !important;
        }}

        button[kind="secondary"], button[kind="primary"] {{
            border-radius: 8px;
            font-family: {FONT_HEADING};
            font-weight: 600;
        }}

        [data-testid="stAlert"] {{
            border-radius: 10px;
            font-size: 0.88rem;
        }}

        /* ---------------------------------------------------------- */
        /* Shared HTML fragments (see helper functions below)         */
        /* ---------------------------------------------------------- */

        .ci-breadcrumb {{
            font-family: {FONT_HEADING};
            font-weight: 600;
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: {COLORS['faint']};
            margin-bottom: 6px;
        }}

        .ci-subtitle {{
            color: {COLORS['muted']};
            font-size: 0.92rem;
            margin-top: 2px;
            margin-bottom: 0;
            max-width: 62ch;
        }}

        .ci-context {{
            font-family: {FONT_MONO};
            font-size: 0.78rem;
            color: {COLORS['faint']};
            margin-top: 6px;
        }}

        .ci-panel {{
            background-color: {COLORS['surface_soft']};
            border-radius: 12px;
            padding: 16px 18px;
        }}

        .ci-card {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
            padding: 14px 16px;
        }}

        .ci-tag {{
            display: inline-flex;
            align-items: center;
            font-family: {FONT_HEADING};
            font-weight: 600;
            font-size: 0.7rem;
            padding: 3px 9px;
            border-radius: 999px;
            letter-spacing: 0.01em;
        }}

        .ci-metric-row {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}

        .ci-metric {{
            flex: 1 1 140px;
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
            padding: 12px 16px;
        }}

        .ci-metric.ci-metric-hero {{
            background-color: {COLORS['soft_blue']};
            border-color: {COLORS['soft_blue']};
        }}

        .ci-metric-value {{
            font-family: {FONT_MONO};
            font-weight: 600;
            font-size: 1.55rem;
            color: {COLORS['ink']};
            line-height: 1.15;
        }}

        .ci-metric-label {{
            font-family: {FONT_HEADING};
            font-weight: 600;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: {COLORS['muted']};
            margin-top: 3px;
        }}

        .ci-metric-sub {{
            font-family: {FONT_MONO};
            font-size: 0.74rem;
            color: {COLORS['faint']};
            margin-top: 2px;
        }}

        .ci-signal {{
            display: flex;
            gap: 14px;
            align-items: flex-start;
            border-radius: 12px;
            padding: 16px 18px;
            border-left: 4px solid transparent;
        }}

        .ci-signal-label {{
            font-family: {FONT_HEADING};
            font-weight: 700;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}

        .ci-signal-title {{
            font-family: {FONT_HEADING};
            font-weight: 700;
            font-size: 1.05rem;
            color: {COLORS['ink']};
            margin-top: 2px;
        }}

        .ci-signal-detail {{
            font-size: 0.86rem;
            color: {COLORS['muted']};
            margin-top: 3px;
        }}

        /* Pipeline flow — Methodology page signature element */
        .ci-flow {{
            display: flex;
            align-items: stretch;
            gap: 0;
            flex-wrap: wrap;
        }}

        .ci-flow-step {{
            flex: 1 1 160px;
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
            padding: 12px 14px;
            position: relative;
        }}

        .ci-flow-index {{
            font-family: {FONT_MONO};
            font-size: 0.7rem;
            color: {COLORS['interact']};
            font-weight: 600;
        }}

        .ci-flow-title {{
            font-family: {FONT_HEADING};
            font-weight: 700;
            font-size: 0.92rem;
            color: {COLORS['ink']};
            margin-top: 2px;
        }}

        .ci-flow-desc {{
            font-size: 0.78rem;
            color: {COLORS['muted']};
            margin-top: 4px;
            line-height: 1.35;
        }}

        .ci-flow-arrow {{
            display: flex;
            align-items: center;
            justify-content: center;
            color: {COLORS['faint']};
            font-size: 1.1rem;
            padding: 0 4px;
            flex: 0 0 auto;
        }}

        /* Evidence cards — Issue Explorer */
        .ci-evidence {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-left: 3px solid var(--rail-color, {COLORS['border']});
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 8px;
        }}

        .ci-evidence-meta {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-family: {FONT_MONO};
            font-size: 0.75rem;
            color: {COLORS['faint']};
        }}

        .ci-evidence-stars {{
            font-size: 0.85rem;
            letter-spacing: 1px;
        }}

        .ci-evidence-text {{
            font-size: 0.9rem;
            color: {COLORS['ink']};
            margin-top: 7px;
            line-height: 1.5;
        }}

        .ci-evidence-tags {{
            margin-top: 8px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Shared HTML fragments — every page builds tags/metrics/flow through these
# so color and spacing decisions live in one place.
# ---------------------------------------------------------------------------

def breadcrumb(section: str) -> str:
    return f'<div class="ci-breadcrumb">Customer Voice / {section}</div>'


def page_header(section: str, title: str, subtitle: str, context: str | None = None) -> None:
    html = breadcrumb(section)
    html += f'<h1>{title}</h1>'
    html += f'<p class="ci-subtitle">{subtitle}</p>'
    if context:
        html += f'<div class="ci-context">{context}</div>'
    st.markdown(html, unsafe_allow_html=True)


def tag(text: str, tone: str) -> str:
    fg, bg = tone_colors(tone)
    return f'<span class="ci-tag" style="color:{fg};background-color:{bg};">{text}</span>'


def metric_row(items: list[dict]) -> None:
    """items: [{"label": str, "value": str, "sub": str|None, "hero": bool}]"""
    cells = []
    for item in items:
        cls = "ci-metric ci-metric-hero" if item.get("hero") else "ci-metric"
        sub = f'<div class="ci-metric-sub">{item["sub"]}</div>' if item.get("sub") else ""
        cells.append(
            f'<div class="{cls}">'
            f'<div class="ci-metric-value">{item["value"]}</div>'
            f'<div class="ci-metric-label">{item["label"]}</div>'
            f'{sub}'
            f'</div>'
        )
    st.markdown(f'<div class="ci-metric-row">{"".join(cells)}</div>', unsafe_allow_html=True)


def signal_banner(label: str, title: str, detail: str, tone: str) -> None:
    # Built as one unindented line on purpose - a multi-line indented HTML
    # string here previously got misread as a markdown code block by the
    # client-side renderer (see issue_explorer.py for the same fix and the
    # full explanation). Every fragment builder below follows the same rule.
    fg, bg = tone_colors(tone)
    html = (
        f'<div class="ci-signal" style="background-color:{bg}; border-left-color:{fg};">'
        f'<div>'
        f'<div class="ci-signal-label" style="color:{fg};">{label}</div>'
        f'<div class="ci-signal-title">{title}</div>'
        f'<div class="ci-signal-detail">{detail}</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def pipeline_flow(steps: list[tuple[str, str]]) -> None:
    """steps: [(title, description), ...] rendered as a connected flow."""
    parts = []
    for i, (title, desc) in enumerate(steps, start=1):
        parts.append(
            f'<div class="ci-flow-step">'
            f'<div class="ci-flow-index">{i:02d}</div>'
            f'<div class="ci-flow-title">{title}</div>'
            f'<div class="ci-flow-desc">{desc}</div>'
            f'</div>'
        )
        if i < len(steps):
            parts.append('<div class="ci-flow-arrow">&rarr;</div>')
    st.markdown(f'<div class="ci-flow">{"".join(parts)}</div>', unsafe_allow_html=True)