"""Maintained catalogs; public UUIDs and hierarchy remain stable across edits."""

from core_apps.properties.models import Governorate, City, District, PropertyType
from core_apps.features.student_models import University, Campus

LOCATION_FIELDS = ("name", "name_ar", "name_en", "is_active", "sort_order")
ACADEMIC_FIELDS = (
    "name_ar",
    "name_en",
    "active",
    "sort_order",
    "source_url",
    "checked_on",
)
RELATIONS = {
    "governorate": "governorates",
    "city": "cities",
    "university": "universities",
}
LABELS = {
    "name": "الاسم المرجعي",
    "name_ar": "الاسم بالعربية",
    "name_en": "الاسم بالإنجليزية",
    "is_active": "متاح للاختيار الجديد",
    "governorate": "المحافظة",
    "city": "المدينة",
    "university": "الجامعة",
    "source_url": "رابط مصدر البيانات",
    "checked_on": "تاريخ التحقق من المصدر",
    "latitude": "خط العرض",
    "longitude": "خط الطول",
    "description": "وصف النوع",
}


def catalogs(spec):
    return {
        "property_types": spec(
            PropertyType,
            "أنواع العقارات",
            (
                "name",
                "slug",
                "name_ar",
                "name_en",
                "description",
                "is_active",
                "sort_order",
            ),
            ("name", "slug"),
            "id",
        ),
        "governorates": spec(
            Governorate, "المحافظات", LOCATION_FIELDS, ("name",), "id"
        ),
        "cities": spec(
            City,
            "المدن",
            ("governorate", *LOCATION_FIELDS),
            ("governorate", "name"),
            "id",
        ),
        "districts": spec(
            District, "الأحياء", ("city", *LOCATION_FIELDS), ("city", "name"), "id"
        ),
        "universities": spec(University, "الجامعات", ACADEMIC_FIELDS, (), "id"),
        "campuses": spec(
            Campus,
            "الحُرم الجامعية",
            ("university", "city", *ACADEMIC_FIELDS, "latitude", "longitude"),
            ("university", "city"),
            "id",
        ),
    }


def validate_provenance(kind, values, instance):
    if kind not in {"universities", "campuses"}:
        return
    from datetime import date
    from rest_framework.exceptions import ValidationError
    from core_apps.common.management.commands.audit_release_catalog import (
        https_destination,
    )

    source = values.get("source_url", getattr(instance, "source_url", ""))
    checked = values.get("checked_on", getattr(instance, "checked_on", None))
    if not https_destination(source) or checked is None or checked > date.today():
        raise ValidationError(
            {
                "source_url": "Supply the reviewed HTTPS source and its non-future verification date."
            }
        )
