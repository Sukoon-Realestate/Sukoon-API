"""Visit: owner visit request detail serializer."""

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from ...phone_disclosure import counterpart_phone_payload
from ...models import PropertyVisit
from .property_visit_serializer import get_visit_language, PostVisitContextMixin
from .tenant_visit_request_serializer import _format_time_clock, _format_full_date
from .owner_visit_request_card_serializer import (
    _OWNER_DETAIL_STATUS_LABEL_AR,
    _OWNER_DETAIL_STATUS_LABEL_EN,
)


class OwnerVisitRequestDetailSerializer(
    PostVisitContextMixin, serializers.ModelSerializer
):
    """
    Detailed serializer for the Owner Visit Request Details screen (Screen 2).
    """

    tenant = serializers.SerializerMethodField()
    property = serializers.SerializerMethodField()
    day_label = serializers.SerializerMethodField()
    time_label = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    class Meta:
        model = PropertyVisit
        fields = [
            "id",
            "tenant",
            "property",
            "visit_date",
            "visit_time",
            "day_label",
            "time_label",
            "note",
            "status",
            "status_label",
            "actions",
            "created_at",
        ]
        read_only_fields = fields

    def _lang(self) -> str:
        return get_visit_language(self.context)

    def get_tenant(self, obj: PropertyVisit):
        tenant = obj.tenant
        profile = getattr(tenant, "profile", None)
        avatar_url = (
            profile.avatar.url if profile and getattr(profile, "avatar", None) else None
        )
        member_year = tenant.date_joined.year if tenant.date_joined else 2024
        lang = self._lang()
        if lang == "en":
            verification_prefix = "Verified Tenant · " if tenant.is_verified else ""
            membership_label = f"{verification_prefix}Member since {member_year}"
        else:
            verification_prefix = "مستأجر موثّق · " if tenant.is_verified else ""
            membership_label = f"{verification_prefix}عضو منذ {member_year}"

        contact = counterpart_phone_payload(
            viewer=getattr(self.context.get("request"), "user", None),
            counterpart=tenant,
            request=self.context.get("request"),
            visit=obj,
        )

        return {
            "id": str(tenant.id),
            "name": tenant.get_full_name,
            "avatar": avatar_url,
            "is_verified": tenant.is_verified,
            "member_since_year": member_year,
            "membership_label": membership_label,
            **contact,
        }

    def get_property(self, obj: PropertyVisit):
        return {
            "id": str(obj.property.id),
            "title": obj.property.title,
            "district": obj.property.district,
            "display_name": f"{obj.property.title} – {obj.property.district}",
        }

    def get_day_label(self, obj: PropertyVisit) -> str:
        return _format_full_date(obj.visit_date, lang=self._lang())

    def get_time_label(self, obj: PropertyVisit) -> str:
        return _format_time_clock(obj.visit_time, lang=self._lang())

    def get_status_label(self, obj: PropertyVisit) -> str:
        lang = self._lang()
        table = (
            _OWNER_DETAIL_STATUS_LABEL_EN
            if lang == "en"
            else _OWNER_DETAIL_STATUS_LABEL_AR
        )
        return table.get(obj.status, obj.status)

    def get_actions(self, obj: PropertyVisit):
        is_pending = obj.status == PropertyVisit.Status.PENDING
        is_confirmed = obj.status == PropertyVisit.Status.CONFIRMED
        return {
            "can_accept": is_pending,
            "can_reject": is_pending,
            "can_chat": is_confirmed,
        }


class OwnerVisitRejectSerializer(serializers.Serializer):
    """
    Serializer for rejecting a visit request (Screen 3 modal).
    """

    REJECTION_REASONS = [
        ("timing_not_suitable", _("الموعد غير مناسب")),
        ("property_currently_rented", _("العقار مؤجر حالياً")),
        ("tenant_not_eligible", _("المستأجر لا يستوفي الشروط")),
        ("other", _("سبب آخر")),
    ]

    reason = serializers.ChoiceField(
        choices=REJECTION_REASONS, default="timing_not_suitable"
    )
    custom_reason = serializers.CharField(required=False, allow_blank=True, default="")
