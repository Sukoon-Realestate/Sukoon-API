"""Profile service: arabic months."""

import logging
from typing import Any
from django.contrib.auth import get_user_model


logger = logging.getLogger(__name__)


User = get_user_model()


ARABIC_MONTHS = {
    1: "يناير",
    2: "فبراير",
    3: "مارس",
    4: "أبريل",
    5: "مايو",
    6: "يونيو",
    7: "يوليو",
    8: "أغسطس",
    9: "سبتمبر",
    10: "أكتوبر",
    11: "نوفمبر",
    12: "ديسمبر",
}


def mask_phone_number(raw_number: Any) -> str:
    """Mask phone number in format 010****432."""
    if not raw_number:
        return ""
    digits = str(raw_number).strip()
    clean = digits.replace("+2", "").strip() if digits.startswith("+2") else digits
    if len(clean) >= 7:
        return f"{clean[:3]}****{clean[-3:]}"
    return clean


def format_arabic_month_year(dt, prefix: str = "عضو منذ") -> str:
    """Format datetime/date as e.g. 'عضو منذ يناير 2026'."""
    if not dt:
        return f"{prefix} يناير 2026"
    month_name = ARABIC_MONTHS.get(dt.month, "")
    if prefix:
        return f"{prefix} {month_name} {dt.year}".strip()
    return f"{month_name} {dt.year}".strip()


def format_arabic_date(dt) -> str:
    """Format date as e.g. '15 مارس 1995'."""
    if not dt:
        return ""
    month_name = ARABIC_MONTHS.get(dt.month, "")
    return f"{dt.day} {month_name} {dt.year}".strip()


def format_arabic_count(count: int, singular: str, plural: str) -> str:
    """Format count with appropriate singular or plural Arabic noun."""
    if 3 <= count <= 10:
        return f"{count} {plural}"
    return f"{count} {singular}"
