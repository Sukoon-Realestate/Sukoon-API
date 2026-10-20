"""Visit: property visit serializer."""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from core_apps.properties.serializers.property import PropertyListSerializer
from ...models import PropertyVisit


_ARABIC_WEEKDAYS = {
    0: "الإثنين",
    1: "الثلاثاء",
    2: "الأربعاء",
    3: "الخميس",
    4: "الجمعة",
    5: "السبت",
    6: "الأحد",
}


_ENGLISH_WEEKDAYS = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}


_ARABIC_MONTHS = {
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


_ENGLISH_MONTHS = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


_ARABIC_VISIT_STATUS = {
    PropertyVisit.Status.PENDING: "بانتظار رد المالك",
    PropertyVisit.Status.CONFIRMED: "مؤكد",
    PropertyVisit.Status.CANCELED: "ملغي",
    PropertyVisit.Status.REJECTED: "مرفوض",
}


_ENGLISH_VISIT_STATUS = {
    PropertyVisit.Status.PENDING: "Pending owner response",
    PropertyVisit.Status.CONFIRMED: "Confirmed",
    PropertyVisit.Status.CANCELED: "Canceled",
    PropertyVisit.Status.REJECTED: "Rejected",
}


_ARABIC_REQUEST_STATUS = {
    PropertyVisit.Status.PENDING: "بانتظار رد المالك",
    PropertyVisit.Status.CONFIRMED: "مقبول",
    PropertyVisit.Status.CANCELED: "ملغي",
    PropertyVisit.Status.REJECTED: "مرفوض",
}


_ENGLISH_REQUEST_STATUS = {
    PropertyVisit.Status.PENDING: "Pending owner response",
    PropertyVisit.Status.CONFIRMED: "Accepted",
    PropertyVisit.Status.CANCELED: "Canceled",
    PropertyVisit.Status.REJECTED: "Rejected",
}


def get_visit_language(request_or_context):
    """Resolve language ('en' or 'ar') for visit labels, defaulting to 'ar'."""
    request = (
        request_or_context.get("request")
        if isinstance(request_or_context, dict)
        else request_or_context
    )
    if request:
        lang_param = getattr(request, "GET", {}).get("lang") or getattr(
            request, "GET", {}
        ).get("language")
        if lang_param:
            clean = lang_param.strip().lower()
            if clean.startswith("en"):
                return "en"
            if clean.startswith("ar"):
                return "ar"
        accept_lang = getattr(request, "headers", {}).get("Accept-Language") or getattr(
            request, "META", {}
        ).get("HTTP_ACCEPT_LANGUAGE", "")
        if accept_lang:
            parts = [
                p.strip().split(";")[0].lower()
                for p in accept_lang.split(",")
                if p.strip()
            ]
            for part in parts:
                if part.startswith("en"):
                    return "en"
                if part.startswith("ar"):
                    return "ar"
        lang_code = getattr(request, "LANGUAGE_CODE", None)
        if lang_code and lang_code.startswith("en") and accept_lang:
            return "en"
    return "ar"


User = get_user_model()


class PostVisitContextMixin:
    def to_representation(self, instance):
        output = super().to_representation(instance)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            from ...services.post_visit_decision import visit_context

            output.update(visit_context(instance, request.user))
            output["stay_preferences"] = instance.stay_preferences
        return output


class PropertyVisitSerializer(PostVisitContextMixin, serializers.ModelSerializer):
    property = PropertyListSerializer(read_only=True)
    tenant_name = serializers.CharField(source="tenant.get_full_name", read_only=True)
    tenant_email = serializers.SerializerMethodField()

    class Meta:
        model = PropertyVisit
        fields = [
            "id",
            "property",
            "tenant_name",
            "tenant_email",
            "visit_date",
            "visit_time",
            "status",
            "note",
            "created_at",
            "updated_at",
            "offer_id",
            "offer_snapshot",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def get_tenant_email(self, obj):
        request = self.context.get("request")
        if request and request.user:
            # Tenant can always see their own email
            if request.user == obj.tenant:
                return obj.tenant.email
            # Owner can only see the tenant's email if the visit is confirmed
            if (
                request.user == obj.property.owner
                and obj.status == PropertyVisit.Status.CONFIRMED
            ):
                return obj.tenant.email
        return ""
