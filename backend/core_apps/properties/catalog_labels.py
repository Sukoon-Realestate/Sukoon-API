"""Localized labels for maintained catalogs; identifiers and user text stay intact."""

from django.utils.translation import get_language
from core_apps.common.locale_middleware import (
    resolve_request_language,
    is_mobile_request,
)

PROPERTY_TYPES = {
    "apartment": ("Apartment", "شقة"),
    "house": ("House", "منزل"),
    "villa": ("Villa", "فيلا"),
    "studio": ("Studio", "استوديو"),
    "penthouse": ("Penthouse", "بنتهاوس"),
    "duplex": ("Duplex", "دوبلكس"),
    "room": ("Room", "غرفة"),
    "roof": ("Roof", "روف"),
}

# Known catalog labels, including the mixed-language records already deployed.
# Unrecognized administrator content is preserved rather than guessed.
LOCATIONS = (
    ("Cairo", "القاهرة"),
    ("Giza", "الجيزة"),
    ("Alexandria", "الإسكندرية"),
    ("Mansoura", "المنصورة"),
    ("6th of October", "6 أكتوبر", "6 اكتوبر", "6 October", "6th October"),
    ("New Cairo", "القاهرة الجديدة"),
    ("Nasr City", "مدينة نصر"),
    ("Maadi", "المعادي"),
    ("Heliopolis", "مصر الجديدة"),
    ("Sheikh Zayed", "الشيخ زايد"),
    ("Smouha", "سموحة"),
    ("El Gouna", "الجونة"),
    ("Hurghada", "الغردقة"),
    ("Red Sea", "البحر الأحمر"),
    ("Dakahlia", "الدقهلية"),
    ("Sharqia", "الشرقية"),
    ("Gharbia", "الغربية"),
    ("Qalyubia", "القليوبية"),
    ("Monufia", "المنوفية"),
    ("Beheira", "البحيرة"),
    ("Kafr El Sheikh", "كفر الشيخ"),
    ("Damietta", "دمياط"),
    ("Port Said", "بورسعيد"),
    ("Ismailia", "الإسماعيلية"),
    ("Suez", "السويس"),
    ("Faiyum", "الفيوم", "Fayoum"),
    ("Beni Suef", "بني سويف"),
    ("Minya", "المنيا"),
    ("Asyut", "أسيوط", "Assiut"),
    ("Sohag", "سوهاج"),
    ("Qena", "قنا"),
    ("Luxor", "الأقصر"),
    ("Aswan", "أسوان"),
    ("Matrouh", "مطروح"),
    ("New Valley", "الوادي الجديد"),
    ("North Sinai", "شمال سيناء"),
    ("South Sinai", "جنوب سيناء"),
)


def _normalized(value):
    return " ".join(
        value.strip().casefold().translate(str.maketrans("أإآى", "اااي")).split()
    )


_LOCATION_LABELS = {
    _normalized(alias): names[:2] for names in LOCATIONS for alias in names
}


def catalog_language(context):
    request = context.get("request")
    if request is not None:
        # The admin manages the source catalog rather than a translated view.
        if not is_mobile_request(request):
            return None
        return resolve_request_language(request)
    return get_language() or "en"


def property_type_label(item, language):
    translated = getattr(
        item, "name_ar" if language and language.startswith("ar") else "name_en", ""
    )
    if language and translated:
        return translated
    names = PROPERTY_TYPES.get(item.slug)
    if names is None or language is None:
        return item.name
    return names[1 if language.startswith("ar") else 0]


def location_label(name, language):
    if not isinstance(name, str):
        item = name
        translated = getattr(
            item, "name_ar" if language and language.startswith("ar") else "name_en", ""
        )
        if language and translated:
            return translated
        name = item.name
    names = _LOCATION_LABELS.get(_normalized(name))
    if names is None or language is None:
        return name
    return names[1 if language.startswith("ar") else 0]
