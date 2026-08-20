"""Small presentation helpers shared across dashboard pages.

Kept separate from data_loader.py on purpose: this module is pure string/
color formatting with no pandas logic, so it's safe to import into any page
without pulling in caching or file I/O. Color values are sourced from
app.utils.theme (TIER_COLORS / VALIDATION_COLORS / rating_tone) rather than
duplicated here, so the palette lives in exactly one place.
"""

from __future__ import annotations

from app.utils.theme import COLORS, TIER_COLORS, VALIDATION_COLORS

# Manual overrides for acronyms/terms that title-casing would mangle.
_LABEL_OVERRIDES = {
    "otp": "OTP",
    "ui": "UI",
    "ux": "UX",
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
    return TIER_COLORS.get(tier, COLORS["faint"])


def tier_tone(tier: str) -> str:
    """Semantic tone name (for theme.tag / theme.signal_banner) matching a priority tier."""
    return {"High": "danger", "Medium": "warning", "Low": "success"}.get(tier, "neutral")


def validation_color(status) -> str:
    if status is None:
        return VALIDATION_COLORS["unvalidated"]
    return VALIDATION_COLORS.get(status, COLORS["faint"])


def validation_tone(status) -> str:
    """Semantic tone name matching a validation status."""
    return {
        "validated": "success",
        "partially_validated": "warning",
        "needs_regex_fix": "danger",
    }.get(status, "neutral")


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