"""Visit: owner visit request card serializer."""

from rest_framework import serializers
from ...phone_disclosure import counterpart_phone_payload
from ...models import PropertyVisit
from .property_visit_serializer import get_visit_language, PostVisitContextMixin
from .tenant_visit_request_serializer import _format_owner_schedule_label


_OWNER_CARD_STATUS_LABEL_AR = {
    PropertyVisit.Status.PENDING: "جديد",
    PropertyVisit.Status.CONFIRMED: "مقبول",
    PropertyVisit.Status.REJECTED: "مرفوض",
    PropertyVisit.Status.CANCELED: "ملغي",
}


_OWNER_CARD_STATUS_LABEL_EN = {
    PropertyVisit.Status.PENDING: "New",
    PropertyVisit.Status.CONFIRMED: "Accepted",
    PropertyVisit.Status.REJECTED: "Rejected",
    PropertyVisit.Status.CANCELED: "Canceled",
}


_OWNER_CARD_STATUS_LABEL = _OWNER_CARD_STATUS_LABEL_AR


_OWNER_DETAIL_STATUS_LABEL_AR = {
    PropertyVisit.Status.PENDING: "بانتظار رد المالك",
    PropertyVisit.Status.CONFIRMED: "مقبول",
    PropertyVisit.Status.REJECTED: "مرفوض",
    PropertyVisit.Status.CANCELED: "ملغي",
}


_OWNER_DETAIL_STATUS_LABEL_EN = {
    PropertyVisit.Status.PENDING: "Pending owner response",
    PropertyVisit.Status.CONFIRMED: "Accepted",
    PropertyVisit.Status.REJECTED: "Rejected",
    PropertyVisit.Status.CANCELED: "Canceled",
}


_OWNER_DETAIL_STATUS_LABEL = _OWNER_DETAIL_STATUS_LABEL_AR


class OwnerVisitRequestCardSerializer(
    PostVisitContextMixin, serializers.ModelSerializer
):
    """
    Card serializer for the Owner Visit Requests list screen (Screen 1).
    """

    tenant = serializers.SerializerMethodField()
    property = serializers.SerializerMethodField()
    subtitle = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()
    is_verified_tenant = serializers.BooleanField(
        source="tenant.is_verified", read_only=True
    )
    verification_warning = serializers.SerializerMethodField()

    class Meta:
        model = PropertyVisit
        fields = [
            "id",
            "tenant",
            "property",
            "subtitle",
            "status",
            "status_label",
            "actions",
            "is_verified_tenant",
            "verification_warning",
            "created_at",
        ]
        read_only_fields = fields

    def _lang(self) -> str:
        return get_visit_language(self.context)

    def get_property(self, obj: PropertyVisit):
        return {
            "id": str(obj.property.id),
            "title": obj.property.title,
            "district": obj.property.district,
        }

    def get_tenant(self, obj):
        tenant = obj.tenant
        profile = getattr(tenant, "profile", None)
        avatar = profile.avatar if profile else None
        avatar_url = (
            avatar.url if avatar and hasattr(avatar, "url") else str(avatar or "")
        )
        contact = counterpart_phone_payload(
            viewer=getattr(self.context.get("request"), "user", None),
            counterpart=tenant,
            request=self.context.get("request"),
            visit=obj,
        )
        return {
            "id": str(tenant.id),
            "name": tenant.get_full_name,
            "avatar": avatar_url or None,
            "is_verified": tenant.is_verified,
            **contact,
        }


    def get_subtitle(self, obj: PropertyVisit) -> str:
        return obj.property.title

    def get_status_label(self, obj: PropertyVisit) -> str:
        lang = self._lang()
        if obj.status == PropertyVisit.Status.PENDING:
            if lang == "en":
                return "New" if obj.tenant.is_verified else "Pending"
            return "جديد" if obj.tenant.is_verified else "انتظار"
        table = (
            _OWNER_CARD_STATUS_LABEL_EN if lang == "en" else _OWNER_CARD_STATUS_LABEL_AR
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

    def get_verification_warning(self, obj: PropertyVisit) -> str:
        if not obj.tenant.is_verified:
            if self._lang() == "en":
                return "This tenant has not verified their identity yet"
            return "هذا المستأجر لم يوثق هويته بعد"
        return ""
