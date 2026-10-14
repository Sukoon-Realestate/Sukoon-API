from typing import Optional
from django.utils.translation import get_language, gettext as _


# * Bidirectional dictionary of API response messages, error messages, choice labels, and tags
from .translation_catalog import (
    EN_TO_AR_MESSAGES,
    AR_TO_EN_MESSAGES,
    FIELD_LABELS_AR,
    TAG_TRANSLATIONS,
    CHOICE_TRANSLATIONS,
)


def translate_message(message: str, language: Optional[str] = None) -> str:
    """
    Translates an API message between English and Arabic based on the language.
    If language is not provided, defaults to Django's active language.
    """
    if not isinstance(message, str) or not message.strip():
        return message

    lang = (language or get_language() or "en").lower()

    if lang.startswith("ar"):
        # Target: Arabic
        # Check direct match
        trimmed = message.strip()
        if trimmed in EN_TO_AR_MESSAGES:
            return EN_TO_AR_MESSAGES[trimmed]
        # Check without trailing dot or with trailing dot
        if trimmed.endswith(".") and trimmed[:-1] in EN_TO_AR_MESSAGES:
            return EN_TO_AR_MESSAGES[trimmed[:-1]]
        if f"{trimmed}." in EN_TO_AR_MESSAGES:
            return EN_TO_AR_MESSAGES[f"{trimmed}."]
        # Dynamic templates e.g. "Marked 3 notifications as read."
        if trimmed.startswith("Marked ") and " notifications as read" in trimmed:
            import re

            m = re.search(r"\d+", trimmed)
            count = m.group() if m else ""
            return f"تم تحديد {count} إشعارات كمقروءة."
        # Fallback to gettext
        translated = _(trimmed)
        if translated != trimmed:
            return translated
        return message

    else:
        # Target: English
        trimmed = message.strip()
        if trimmed in AR_TO_EN_MESSAGES:
            return AR_TO_EN_MESSAGES[trimmed]
        if trimmed.endswith(".") and trimmed[:-1] in AR_TO_EN_MESSAGES:
            return AR_TO_EN_MESSAGES[trimmed[:-1]]
        if f"{trimmed}." in AR_TO_EN_MESSAGES:
            return AR_TO_EN_MESSAGES[f"{trimmed}."]
        # If it's already English or unknown, return message
        return message


def translate_field_label(label: str, language: Optional[str] = None) -> str:
    """Translates a field label (e.g. Email -> البريد الإلكتروني)."""
    lang = (language or get_language() or "en").lower()
    if lang.startswith("ar"):
        return FIELD_LABELS_AR.get(label, label)
    return label


def translate_tag(tag: str, language: Optional[str] = None) -> str:
    """Translates a tag label (e.g. عائلات <-> Families)."""
    lang = (language or get_language() or "en").lower()
    target_key = "ar" if lang.startswith("ar") else "en"

    # Search in TAG_TRANSLATIONS
    for key, trans in TAG_TRANSLATIONS.items():
        if tag == key or tag == trans.get("en") or tag == trans.get("ar"):
            return trans.get(target_key, tag)

    return tag


def translate_choice(choice: str, language: Optional[str] = None) -> str:
    """Translates a choice code to its localized label."""
    lang = (language or get_language() or "en").lower()
    target_key = "ar" if lang.startswith("ar") else "en"

    if choice in CHOICE_TRANSLATIONS:
        return CHOICE_TRANSLATIONS[choice].get(target_key, choice)

    return choice
