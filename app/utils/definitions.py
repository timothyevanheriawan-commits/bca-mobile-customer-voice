"""Human-readable definitions for each issue category.

Kept separate from src/issue_classification.py on purpose: that module
defines the regex patterns, not prose descriptions, and the validation
tool (src/generate_validation_tool.py) already needed this exact text for
its own info box. Centralizing it here means the Issue Explorer and
Methodology pages can both show a reader what a category is actually
supposed to mean, in the same words, without re-typing them.
"""

from __future__ import annotations

DEFINITIONS: dict[str, str] = {
    "transaction_failed_balance_deducted": (
        "QRIS, transfer, or top-up reported as failed, but the balance is "
        "still deducted and never refunded."
    ),
    "indicator_light_stuck": (
        "The in-app payment readiness indicator (red, green, or blue light) "
        "gets stuck or is slow to change, blocking or delaying QRIS scans."
    ),
    "unexplained_deduction": (
        "Balance decreases with no matching entry in mutasi (transaction "
        "history), not tied to a specific attempted transaction."
    ),
    "face_verification_failure": (
        "Face or biometric verification for login, registration, or OTP "
        "repeatedly fails, especially on older phones."
    ),
    "login_otp_access": (
        "Cannot log in, or the OTP/access process is broken or overly "
        "burdensome (SIM swap, pulsa-dependent OTP)."
    ),
    "app_performance": (
        "App is slow, errors out, crashes, or will not open. General "
        "technical malfunction not clearly tied to QRIS or the indicator."
    ),
    "maintenance_downtime": (
        "Scheduled maintenance lands at inconvenient times, often "
        "unannounced, and blocks transactions while it runs."
    ),
    "customer_service": (
        "Complaints to CS, branch staff, or the call center go unresolved, "
        "unreachable, or get looped without a real response."
    ),
    "ui_ux_regression": (
        "An update changed the interface in a way that reduces usability: "
        "lost features or a more confusing layout than before."
    ),
    "device_compatibility": (
        "App reports device or version incompatibility, or refuses to "
        "install or update on an otherwise working phone."
    ),
}


def get_definition(category: str) -> str:
    return DEFINITIONS.get(category, "No definition recorded for this category yet.")