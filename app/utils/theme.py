"""Design tokens, CSS injection, and shared HTML fragments.

Direction: "Audit Ledger". This dashboard is not a product analytics
surface, it is a workpaper: raw complaints get logged, counted, and
checked before anyone is allowed to act on the numbers. The visual
language borrows from two real objects rather than from a generic
dashboard template: a green-bar accounting ledger pad (alternating pale
green row bands in every tabular section) and a rubber ink stamp (the
validation status marker, since "validated" or "needs regex fix" is
literally an auditor's sign-off on a claim). Both are used exactly once
as the signature move; everything else stays quiet paper-and-ink so the
stamp and the ledger bands keep their weight.

Ink and stamp colors are reserved strictly for validation confidence,
priority tier, and trend direction. Nothing else on the page borrows
them, so a red stamp always means the same thing wherever it appears.

Every page pulls colors, spacing, and shared HTML fragments from here
rather than hardcoding hex values or writing one-off markup, so a palette
or spacing change only has to happen in one place.
"""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------

COLORS = {
    # Surfaces - off-white ledger paper, not the warm cream default.
    "bg": "#FAFAF6",
    "surface": "#FFFFFF",
    "band": "#E9F0E1",       # pale ledger-green row band
    "band_strong": "#DCE7D1",
    # Text - deep green-black ink rather than pure black.
    "ink": "#1B2A20",
    "muted": "#5B6B5D",
    "faint": "#93A392",
    # Rule / border - soft green-grey, like ruled ledger lines.
    "rule": "#C9D3C0",
    "rule_strong": "#1B2A20",
    # Brand / interaction - ballpoint-pen blue, used sparingly.
    "primary": "#243F63",
    "interact": "#2E5488",
    "soft_blue": "#E7ECF3",
    # Semantic ink - reserved for stamps, tier, and trend only.
    "danger": "#A23B2C",
    "danger_soft": "#F4E4DF",
    "warning": "#93641C",
    "warning_soft": "#F1E7D2",
    "success": "#2E6B49",
    "success_soft": "#E1EDE2",
    "neutral_soft": "#EEF1EA",
}

FONT_HEADING = "'Space Grotesk', sans-serif"
FONT_BODY = "'IBM Plex Sans', sans-serif"
FONT_MONO = "'IBM Plex Mono', monospace"

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

# 1-2 stars read as risk signal, 3 as caution, 4-5 as settled. The one
# place star rating maps to color, reused by the rating filter and the
# evidence cards so they never drift apart.
RATING_TONES = {
    1: "danger", 2: "danger",
    3: "warning",
    4: "neutral", 5: "neutral",
}


def rating_tone(rating: int) -> str:
    return RATING_TONES.get(int(rating), "neutral")


def tone_colors(tone: str) -> tuple[str, str]:
    """(ink color, soft background) for a semantic tone name."""
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
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

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
            letter-spacing: -0.01em;
        }}

        h1 {{ font-size: 1.85rem; font-weight: 700; margin-bottom: 0.15rem; }}
        h2 {{ font-size: 1.2rem; font-weight: 600; }}
        h3 {{ font-size: 1.05rem; font-weight: 600; }}

        p, span, div, label {{ font-family: {FONT_BODY}; }}

        code, .lg-mono {{
            font-family: {FONT_MONO} !important;
        }}

        hr {{
            border-color: {COLORS['rule']};
            margin: 1.1rem 0;
        }}

        /* ---------------------------------------------------------- */
        /* Sidebar                                                    */
        /* ---------------------------------------------------------- */

        [data-testid="stSidebar"] {{
            background-color: {COLORS['surface']};
            border-right: 1px solid {COLORS['rule']};
        }}

        [data-testid="stSidebar"] .block-container {{
            padding-top: 1.6rem;
        }}

        [data-testid="stSidebarNav"] {{
            padding-top: 0.4rem;
        }}

        [data-testid="stSidebarNavLink"] {{
            border-radius: 3px;
            font-family: {FONT_HEADING};
            font-weight: 600;
            font-size: 0.87rem;
            color: {COLORS['muted']};
            padding: 0.4rem 0.6rem;
            margin-bottom: 2px;
            transition: background-color 0.12s ease;
        }}

        [data-testid="stSidebarNavLink"]:hover {{
            background-color: {COLORS['neutral_soft']};
        }}

        [data-testid="stSidebarNavLink"][aria-current="page"] {{
            background-color: {COLORS['band']};
            color: {COLORS['ink']};
            border-left: 3px solid {COLORS['ink']};
        }}

        [data-testid="stSidebarNavLink"][aria-current="page"] span {{
            color: {COLORS['ink']};
        }}

        /* ---------------------------------------------------------- */
        /* Native metric widget                                       */
        /* ---------------------------------------------------------- */

        [data-testid="stMetric"] {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['rule']};
            border-radius: 4px;
            padding: 12px 16px;
        }}

        [data-testid="stMetricLabel"] {{
            font-family: {FONT_HEADING};
            font-weight: 600;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: {COLORS['muted']};
        }}

        [data-testid="stMetricValue"] {{
            font-family: {FONT_MONO};
            font-weight: 600;
            color: {COLORS['ink']};
        }}

        /* ---------------------------------------------------------- */
        /* Controls                                                    */
        /* ---------------------------------------------------------- */

        [data-baseweb="select"] > div {{
            border-radius: 3px;
            border-color: {COLORS['rule']};
            background-color: {COLORS['surface']};
            font-family: {FONT_BODY};
        }}

        [data-testid="stMultiSelectTagsContainer"] span[data-tag] {{
            background-color: {COLORS['soft_blue']} !important;
            color: {COLORS['interact']} !important;
            border-radius: 3px !important;
        }}

        [data-testid="stMultiSelectTagsContainer"] span[data-tag] button {{
            color: {COLORS['interact']} !important;
        }}

        [data-testid="stButtonGroup"] button {{
            font-family: {FONT_HEADING} !important;
            font-size: 0.82rem !important;
            border-radius: 3px !important;
            border-color: {COLORS['rule']} !important;
            color: {COLORS['muted']} !important;
            background-color: {COLORS['surface']} !important;
        }}

        [data-testid="stButtonGroup"] button[data-selected="true"] {{
            background-color: {COLORS['band']} !important;
            border-color: {COLORS['ink']} !important;
            color: {COLORS['ink']} !important;
        }}

        [data-testid="stButtonGroup"] button[data-selected="true"] p {{
            color: {COLORS['ink']} !important;
        }}

        button[kind="secondary"], button[kind="primary"] {{
            border-radius: 3px;
            font-family: {FONT_HEADING};
            font-weight: 600;
        }}

        [data-testid="stAlert"] {{
            border-radius: 4px;
            font-family: {FONT_BODY};
            border: 1px solid {COLORS['rule']};
        }}

        /* ---------------------------------------------------------- */
        /* Ledger typography fragments                                */
        /* ---------------------------------------------------------- */

        .lg-eyebrow {{
            font-family: {FONT_MONO};
            font-weight: 500;
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: {COLORS['muted']};
            margin-bottom: 6px;
        }}

        .lg-subtitle {{
            font-size: 0.98rem;
            color: {COLORS['muted']};
            max-width: 62ch;
            line-height: 1.5;
        }}

        .lg-context {{
            font-family: {FONT_MONO};
            font-size: 0.76rem;
            color: {COLORS['faint']};
            margin-top: 6px;
        }}

        .lg-body {{
            font-size: 0.92rem;
            color: {COLORS['ink']};
            line-height: 1.6;
            max-width: 68ch;
        }}

        .lg-body strong {{ color: {COLORS['ink']}; }}

        /* ---------------------------------------------------------- */
        /* Panels and metrics                                         */
        /* ---------------------------------------------------------- */

        .lg-panel {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['rule']};
            border-radius: 4px;
            padding: 14px 16px;
        }}

        .lg-metric-row {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}

        .lg-metric {{
            flex: 1 1 150px;
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['rule']};
            border-radius: 4px;
            padding: 12px 16px;
        }}

        .lg-metric.lg-metric-hero {{
            background-color: {COLORS['band']};
            border-color: {COLORS['band_strong']};
        }}

        .lg-metric-value {{
            font-family: {FONT_MONO};
            font-weight: 600;
            font-size: 1.5rem;
            color: {COLORS['ink']};
            line-height: 1.15;
        }}

        .lg-metric-label {{
            font-family: {FONT_HEADING};
            font-weight: 600;
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: {COLORS['muted']};
            margin-top: 3px;
        }}

        .lg-metric-sub {{
            font-family: {FONT_MONO};
            font-size: 0.74rem;
            color: {COLORS['faint']};
            margin-top: 2px;
        }}

        /* ---------------------------------------------------------- */
        /* Callout - top priority signal / definition box              */
        /* ---------------------------------------------------------- */

        .lg-callout {{
            display: flex;
            gap: 14px;
            align-items: flex-start;
            border-radius: 3px;
            padding: 16px 18px;
            border-left: 4px solid transparent;
        }}

        .lg-callout-label {{
            font-family: {FONT_MONO};
            font-weight: 600;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.07em;
        }}

        .lg-callout-title {{
            font-family: {FONT_HEADING};
            font-weight: 700;
            font-size: 1.05rem;
            color: {COLORS['ink']};
            margin-top: 3px;
        }}

        .lg-callout-detail {{
            font-size: 0.86rem;
            color: {COLORS['muted']};
            margin-top: 4px;
            line-height: 1.5;
        }}

        /* ---------------------------------------------------------- */
        /* Stamp - the signature validation / status marker            */
        /* ---------------------------------------------------------- */

        .lg-stamp {{
            display: inline-block;
            font-family: {FONT_MONO};
            font-weight: 600;
            font-size: 0.68rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            padding: 3px 8px;
            border: 1.5px solid currentColor;
            border-radius: 2px;
            box-shadow: inset 0 0 0 2px {COLORS['surface']}, inset 0 0 0 3px currentColor;
            transform: rotate(-1.2deg);
            white-space: nowrap;
        }}

        /* ---------------------------------------------------------- */
        /* Ledger tables - alternating green-bar rows, real <table>    */
        /* ---------------------------------------------------------- */

        .lg-ledger {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.86rem;
        }}

        .lg-ledger th {{
            text-align: left;
            font-family: {FONT_MONO};
            font-weight: 500;
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: {COLORS['muted']};
            border-bottom: 2px solid {COLORS['rule_strong']};
            padding: 6px 10px;
        }}

        .lg-ledger td {{
            padding: 10px 10px;
            border-bottom: 1px solid {COLORS['rule']};
            vertical-align: top;
            color: {COLORS['ink']};
        }}

        .lg-ledger tr:nth-child(even) td {{
            background-color: {COLORS['band']};
        }}

        .lg-ledger .lg-num {{
            font-family: {FONT_MONO};
            color: {COLORS['muted']};
            text-align: right;
            width: 2.4em;
        }}

        .lg-ledger .lg-right {{
            font-family: {FONT_MONO};
            text-align: right;
            white-space: nowrap;
        }}

        .lg-ledger .lg-caveat {{
            font-size: 0.78rem;
            color: {COLORS['warning']};
            margin-top: 3px;
            display: block;
        }}

        /* ---------------------------------------------------------- */
        /* Pipeline flow - Methodology signature element                */
        /* ---------------------------------------------------------- */

        .lg-flow {{
            display: flex;
            align-items: stretch;
            gap: 0;
            flex-wrap: wrap;
        }}

        .lg-flow-step {{
            flex: 1 1 160px;
            background-color: {COLORS['surface']};
            border-top: 3px solid {COLORS['ink']};
            border-left: 1px solid {COLORS['rule']};
            border-right: 1px solid {COLORS['rule']};
            border-bottom: 1px solid {COLORS['rule']};
            padding: 12px 14px;
            position: relative;
        }}

        .lg-flow-index {{
            font-family: {FONT_MONO};
            font-size: 0.7rem;
            color: {COLORS['muted']};
            font-weight: 500;
        }}

        .lg-flow-title {{
            font-family: {FONT_HEADING};
            font-weight: 700;
            font-size: 0.92rem;
            color: {COLORS['ink']};
            margin-top: 2px;
        }}

        .lg-flow-desc {{
            font-size: 0.78rem;
            color: {COLORS['muted']};
            margin-top: 4px;
            line-height: 1.4;
        }}

        .lg-flow-arrow {{
            display: flex;
            align-items: center;
            justify-content: center;
            color: {COLORS['faint']};
            font-size: 1.1rem;
            padding: 0 4px;
            flex: 0 0 auto;
        }}

        /* ---------------------------------------------------------- */
        /* Evidence records - Issue Explorer                           */
        /* ---------------------------------------------------------- */

        .lg-evidence {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['rule']};
            border-radius: 3px;
            padding: 12px 16px;
            margin-bottom: 8px;
        }}

        .lg-evidence-meta {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-family: {FONT_MONO};
            font-size: 0.74rem;
            color: {COLORS['faint']};
        }}

        .lg-evidence-stars {{
            font-size: 0.85rem;
            letter-spacing: 1px;
        }}

        .lg-evidence-text {{
            font-size: 0.9rem;
            color: {COLORS['ink']};
            margin-top: 7px;
            line-height: 1.5;
        }}

        .lg-evidence-tags {{
            margin-top: 8px;
        }}

        .lg-tag {{
            display: inline-flex;
            align-items: center;
            font-family: {FONT_HEADING};
            font-weight: 600;
            font-size: 0.68rem;
            padding: 2px 8px;
            border-radius: 2px;
            letter-spacing: 0.01em;
            margin-right: 4px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Shared HTML fragments
# ---------------------------------------------------------------------------

def breadcrumb(section: str) -> str:
    return f'<div class="lg-eyebrow">Customer Voice Ledger / {section}</div>'


def page_header(section: str, title: str, subtitle: str, context: str | None = None) -> None:
    html = breadcrumb(section)
    html += f'<h1>{title}</h1>'
    html += f'<p class="lg-subtitle">{subtitle}</p>'
    if context:
        html += f'<div class="lg-context">{context}</div>'
    st.markdown(html, unsafe_allow_html=True)


def tag(text: str, tone: str) -> str:
    fg, bg = tone_colors(tone)
    return f'<span class="lg-tag" style="color:{fg};background-color:{bg};">{text}</span>'


def stamp(text: str, tone: str) -> str:
    """The signature rubber-stamp marker used for validation status."""
    fg, _ = tone_colors(tone)
    return f'<span class="lg-stamp" style="color:{fg};">{text}</span>'


def metric_row(items: list[dict]) -> None:
    """items: [{"label": str, "value": str, "sub": str|None, "hero": bool}]"""
    cells = []
    for item in items:
        cls = "lg-metric lg-metric-hero" if item.get("hero") else "lg-metric"
        sub = f'<div class="lg-metric-sub">{item["sub"]}</div>' if item.get("sub") else ""
        cells.append(
            f'<div class="{cls}">'
            f'<div class="lg-metric-value">{item["value"]}</div>'
            f'<div class="lg-metric-label">{item["label"]}</div>'
            f'{sub}'
            f'</div>'
        )
    st.markdown(f'<div class="lg-metric-row">{"".join(cells)}</div>', unsafe_allow_html=True)


def callout(label: str, title: str, detail: str, tone: str) -> None:
    fg, bg = tone_colors(tone)
    html = (
        f'<div class="lg-callout" style="background-color:{bg}; border-left-color:{fg};">'
        f'<div>'
        f'<div class="lg-callout-label" style="color:{fg};">{label}</div>'
        f'<div class="lg-callout-title">{title}</div>'
        f'<div class="lg-callout-detail">{detail}</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def pipeline_flow(steps: list[tuple[str, str]]) -> None:
    """steps: [(title, description), ...] rendered as a connected flow."""
    parts = []
    for i, (title, desc) in enumerate(steps, start=1):
        parts.append(
            f'<div class="lg-flow-step">'
            f'<div class="lg-flow-index">Entry {i:02d}</div>'
            f'<div class="lg-flow-title">{title}</div>'
            f'<div class="lg-flow-desc">{desc}</div>'
            f'</div>'
        )
        if i < len(steps):
            parts.append('<div class="lg-flow-arrow">&rarr;</div>')
    st.markdown(f'<div class="lg-flow">{"".join(parts)}</div>', unsafe_allow_html=True)


def ledger_table(headers: list[str], rows: list[list[str]], col_classes: list[str] | None = None) -> None:
    """Render a full ledger table in one HTML block, zebra-striped by CSS.

    Every cell is pre-formatted HTML (already escaped by the caller where
    needed) so this function stays a pure layout helper. Built as one
    st.markdown call per table rather than one call per row, both because
    it renders faster and because it keeps each row's markup fully self
    contained instead of relying on many small sequential calls.

    col_classes, if given, must match len(headers) and assigns a CSS class
    (e.g. "lg-num" or "lg-right") to every cell in that column - used for
    right-aligning the numeric/mono columns without repeating inline style
    on every row.
    """
    classes = col_classes or [""] * len(headers)
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(
            f'<td class="{cls}">{cell}</td>' if cls else f"<td>{cell}</td>"
            for cell, cls in zip(row, classes)
        ) + "</tr>"
        for row in rows
    )
    st.markdown(
        f'<table class="lg-ledger"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>',
        unsafe_allow_html=True,
    )