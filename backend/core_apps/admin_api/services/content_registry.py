"""Explicit content and existing product catalogs; no policy or privilege CRUD."""

from dataclasses import dataclass
from django.db import models
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from core_apps.common.content_models import PublicContentPage, ReleaseNote
from core_apps.support.models import HelpContact, HelpArticle
from .catalog_registry import catalogs, RELATIONS, LABELS as CATALOG_LABELS
from . import commerce_catalog_registry as commerce


@dataclass(frozen=True)
class ContentSpec:
    model: type
    label: str
    fields: tuple
    fixed: tuple
    identity_field: str = "pk"
    opaque_revision: bool = False
    allow_create: bool = True


REGISTRY = {
    "pages": ContentSpec(
        PublicContentPage,
        "صفحات التطبيق",
        ("slug", "title_ar", "title_en", "content_ar", "content_en", "active"),
        ("slug",),
    ),
    "contacts": ContentSpec(
        HelpContact,
        "قنوات المساعدة",
        ("workspace", "email", "hours_ar", "hours_en", "active"),
        ("workspace",),
    ),
    "articles": ContentSpec(
        HelpArticle,
        "الأسئلة الشائعة",
        (
            "slug",
            "workspace",
            "question_ar",
            "question_en",
            "answer_ar",
            "answer_en",
            "sort_order",
            "active",
        ),
        ("slug",),
    ),
    "releases": ContentSpec(
        ReleaseNote,
        "تحديثات التطبيق",
        ("version", "workspace", "items_ar", "items_en", "publish_at", "active"),
        ("version", "workspace"),
    ),
}
REGISTRY.update(catalogs(ContentSpec))
REGISTRY.update(commerce.catalogs(ContentSpec))
RELATIONS = {**RELATIONS, **commerce.RELATIONS}
LABELS = {
    **commerce.LABELS,
    **CATALOG_LABELS,
    "slug": "المعرف الثابت",
    "title_ar": "العنوان بالعربية",
    "title_en": "العنوان بالإنجليزية",
    "content_ar": "النص بالعربية",
    "content_en": "النص بالإنجليزية",
    "workspace": "الجمهور",
    "phone": "الهاتف",
    "email": "البريد",
    "hours_ar": "مواعيد التواصل بالعربية",
    "hours_en": "مواعيد التواصل بالإنجليزية",
    "question_ar": "السؤال بالعربية",
    "question_en": "السؤال بالإنجليزية",
    "answer_ar": "الإجابة بالعربية",
    "answer_en": "الإجابة بالإنجليزية",
    "sort_order": "الترتيب",
    "active": "مفعّل",
    "version": "إصدار التطبيق",
    "items_ar": "التحديثات بالعربية — سطر لكل بند",
    "items_en": "التحديثات بالإنجليزية — سطر لكل بند",
    "publish_at": "موعد النشر",
}
CHOICE_LABELS = {
    "tenant": "الأفراد",
    "owner": "الملاك",
    "student": "الطلاب",
    "company": "الشركات",
    "both": "الأفراد والملاك",
    "all": "المساحات الأربع",
    "about-us": "عن سكون",
    "privacy-policy": "الخصوصية",
    "terms": "الشروط",
    "personal": "حساب شخصي",
    "organization": "شركة — اختبار الفوترة الحالية",
    "week": "أسبوع",
    "calendar_month": "شهر تقويمي",
    "calendar_year": "سنة تقويمية",
}


def spec(kind):
    if kind not in REGISTRY:
        raise NotFound()
    return REGISTRY[kind]


def serializer_type(kind):
    entry = spec(kind)

    class Editor(serializers.ModelSerializer):
        def build_relational_field(self, field_name, relation_info):
            from core_apps.properties.serializers.location import PublicUUIDRelatedField

            return PublicUUIDRelatedField, {
                "queryset": relation_info.related_model.objects.all()
            }

        class Meta:
            model = entry.model
            fields = entry.fields
            # Revision and existing-record checks are serialized by the service.

    return Editor


def validated(kind, values, instance=None):
    entry = spec(kind)
    if instance is None and not entry.allow_create:
        raise ValidationError("Only existing approved features can be described here.")
    if not isinstance(values, dict) or set(values) - set(entry.fields):
        raise ValidationError(
            "Only the listed application content fields can be edited."
        )
    if instance and any(
        key in values
        and str(values[key])
        != str(
            getattr(instance, key).id if key in RELATIONS else getattr(instance, key)
        )
        for key in entry.fixed
    ):
        raise ValidationError(
            "The content identity cannot be changed. Create a separate entry."
        )
    serializer = serializer_type(kind)(
        instance=instance, data=values, partial=instance is not None
    )
    serializer.is_valid(raise_exception=True)
    commerce.validate(kind, serializer.validated_data, instance)
    from .catalog_registry import validate_provenance

    validate_provenance(kind, serializer.validated_data, instance)
    if entry.identity_field == "id":
        from core_apps.properties.catalog_access import require_current_selection

        for field in entry.fields:
            if (
                field in RELATIONS
                and field not in commerce.RELATIONS
                and field in serializer.validated_data
            ):
                value = serializer.validated_data[field]
                previous = getattr(instance, field, None) if instance else None
                require_current_selection(value, previous=previous, field=field)
    return serializer.validated_data


def projection(kind, instance):
    entry = spec(kind)
    relations = {}
    for field in entry.fields:
        if entry.model._meta.get_field(field).is_relation:
            related = getattr(instance, field)
            relations[field] = (
                getattr(related, "name_ar", "")
                or getattr(related, "label_ar", "")
                or getattr(related, "name_en", "")
                or getattr(related, "label_en", "")
                or getattr(related, "name", "")
            )
    return {
        "id": str(getattr(instance, entry.identity_field)),
        "revision": instance.revision,
        "values": dict(serializer_type(kind)(instance).data),
        **({"relation_labels": relations} if relations else {}),
        **(
            {"selection_available": instance.available}
            if kind == "commerce_features"
            else {}
        ),
        **(
            {"selection_available": instance.active and instance.audience == "personal"}
            if kind == "subscription_plans"
            else {}
        ),
    }


def field_type(field):
    if field.is_relation:
        return "relation"
    if field.choices:
        return "choice"
    for model_type, category in (
        (models.BooleanField, "boolean"),
        (models.TextField, "multiline"),
        (models.DateTimeField, "datetime"),
        (models.DateField, "date"),
        (models.DecimalField, "decimal"),
        (models.IntegerField, "integer"),
        (models.EmailField, "email"),
    ):
        if isinstance(field, model_type):
            return category
    return "text"


def schema(kind):
    entry = spec(kind)
    fields = []
    for name in entry.fields:
        field = entry.model._meta.get_field(name)
        category = field_type(field)
        fields.append(
            {
                "name": name,
                "label": LABELS[name],
                "type": category,
                "fixed": name in entry.fixed,
                "required": not field.blank and not field.null,
                "nullable": field.null,
                "max_length": field.max_length,
                "relation": RELATIONS.get(name) if field.is_relation else None,
                "choices": [
                    {"value": k, "label": CHOICE_LABELS.get(k, str(v))}
                    for k, v in field.choices or []
                ],
            }
        )
    return {
        "kind": kind,
        "label": entry.label,
        "fields": fields,
        "revision_type": "opaque" if entry.opaque_revision else "integer",
        "guidance": commerce.guidance(kind),
        "allow_create": entry.allow_create,
    }
