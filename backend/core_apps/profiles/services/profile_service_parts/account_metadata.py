"""Localized server-owned My Account labels; never translate user content."""

from datetime import date

from django.utils.formats import date_format
from django.utils.translation import get_language, override

from .arabic_months import ARABIC_MONTHS, format_arabic_count, format_arabic_month_year


def account_text(english: str, arabic: str) -> str:
    """Use the language already resolved by MobileLocaleMiddleware."""
    return arabic if (get_language() or "en").lower().startswith("ar") else english


def format_account_count(count, singular, plural, arabic_singular, arabic_plural):
    return account_text(
        f"{count} {singular if count == 1 else plural}",
        format_arabic_count(count, arabic_singular, arabic_plural),
    )


def membership_labels(joined):
    # Preserve the existing missing-date fallback and stored calendar fields.
    # Display localization must not shift the date or change membership data.
    joined = joined or date(2026, 1, 1)
    if (get_language() or "en").lower().startswith("ar"):
        return joined.year, ARABIC_MONTHS[joined.month], format_arabic_month_year(joined)
    # Explicit locale avoids relying on the host's LC_TIME for English months.
    with override("en"):
        month = date_format(joined, "F")
    return joined.year, month, f"Member since {month} {joined.year}"
