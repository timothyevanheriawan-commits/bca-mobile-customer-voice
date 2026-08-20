"""Small presentation helpers shared across dashboard pages.

Kept separate from data_loader.py on purpose: this module is pure string/
color formatting with no pandas logic, so it's safe to import into any page
without pulling in caching or file I/O.
"""

from __future__ import annotations

# Manual overrides for acronyms/terms that title-casing would mangle.
_LABEL_OVERRIDES = {
    "otp": "OTP",
    "ui": "UI",
    "ux": "UX",
}

TIER_COLORS = {
    "High": "#B3261E",
    "Medium": "#B8860B",
    "Low": "#2E7D32",
}

VALIDATION_COLORS = {
    "validated": "#2E7D32",
    "partially_validated": "#B8860B",
    "needs_regex_fix": "#B3261E",
    "unvalidated": "#6B7280",
}

TREND_ARROWS = {
    "increasing": "\u2191",
    "decreasing": "\u2193",
    "stable": "\u2192",
    "insufficient_data": "\u2013",
}


def issue_label(category: str) -> str:
    """'transaction_failed_balance_deducted' -> 'Transaction Failed Balance Deducted'"""
    words = category.split("_")
    return " ".join(_LABEL_OVERRIDES.get(w, w.capitalize()) for w in words)


def tier_color(tier: str) -> str:
    return TIER_COLORS.get(tier, "#6B7280")


def validation_color(status) -> str:
    if status is None:
        return VALIDATION_COLORS["unvalidated"]
    return VALIDATION_COLORS.get(status, "#6B7280")


def trend_arrow(trend) -> str:
    if trend is None:
        return TREND_ARROWS["insufficient_data"]
    return TREND_ARROWS.get(trend, "")


def format_pct(value, decimals: int = 1) -> str:
    if value is None:
        return "\u2013"
    try:
        if value != value:  # NaN check without importing math/pandas
            return "\u2013"
    except TypeError:
        return "\u2013"
    return f"{value * 100:.{decimals}f}%"


def format_count(value) -> str:
    if value is None:
        return "\u2013"
    try:
        if value != value:
            return "\u2013"
    except TypeError:
        return "\u2013"
    return f"{int(value):,}"
