"""VisitBooking operations owned by PropertyVisitService."""

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from ....models import PropertyVisit
from ..logger import logger


class VisitBookingMixin:
    @classmethod
    @transaction.atomic
    def create_visit(cls, tenant, property_obj, validated_data, *, group=None):
        """
        Creates a property visit request.
        """
        from core_apps.chat.moderation.policy import require_new_business
        from core_apps.users.models import User

        list(
            User.objects.select_for_update()
            .filter(pk__in=[tenant.pk, property_obj.owner_id])
            .order_by("pk")
        )
        require_new_business(tenant)
        require_new_business(property_obj.owner)
        from ....models import Property
        from ...viewing_access import prepare_context

        context = prepare_context(tenant, validated_data.pop("viewing_context", {}))
        if group is not None:
            context["context_kind"] = "group"
        tenant = context.pop("tenant", tenant)
        property_obj = Property.objects.select_for_update().get(pk=property_obj.pk)
        validated_data.update(context)
        # Validate that tenant is not the property owner
        if property_obj.owner == tenant:
            raise ValidationError(_("You cannot book a visit for your own property."))

        expected_offer_revision = validated_data.pop("expected_offer_revision", None)
        offer_id = str(validated_data.get("offer_id") or "")
        if offer_id:
            from core_apps.features.services.tenancy_invitations import (
                resolve_offer_snapshot,
            )

            offer = next(
                (
                    item
                    for item in property_obj.rental_inventory.get("offers", [])
                    if str(item.get("id")) == offer_id
                ),
                None,
            )
            if (
                not offer
                or offer.get("archived")
                or offer.get("availability") != "available"
            ):
                raise ValidationError(_("The selected rental offer is unavailable."))
            if expected_offer_revision != offer.get("revision"):
                raise ValidationError(
                    _("The selected rental offer changed. Refresh and review it again.")
                )
            # Capture names, room/bed identity, capacity and terms together at
            # booking time. Never reconstruct an existing visit from inventory.
            offer_id, snapshot = resolve_offer_snapshot(
                property_obj, offer_id, expected_offer_revision
            )
            validated_data["offer_snapshot"] = snapshot
        elif property_obj.rental_inventory:
            raise ValidationError(_("Select a rental offer before requesting a visit."))

        stay = validated_data.get("stay_preferences")
        if stay:
            from ....serializers.visit_parts.visit_request_input_serializer import (
                StayPreferencesSerializer,
            )

            checked = StayPreferencesSerializer(data=stay)
            checked.is_valid(raise_exception=True)
            validated_data["stay_preferences"] = checked.validated_data
            capacity = (validated_data.get("offer_snapshot") or {}).get("capacity")
            if capacity is not None and checked.validated_data["occupants"] > capacity:
                raise ValidationError(
                    "The requested occupants exceed the selected accommodation capacity."
                )

        from core_apps.features.services.rental_lifecycle.habitability import (
            assert_habitable,
        )

        assert_habitable(property_obj, validated_data.get("offer_snapshot", {}))
        # Scheduling is agreed in chat. Ignore legacy appointment fields.
        validated_data.pop("visit_date", None)
        validated_data.pop("visit_time", None)
        if PropertyVisit.objects.filter(
            tenant=tenant,
            property=property_obj,
            offer_id=offer_id,
            context_kind=validated_data.get("context_kind", "personal"),
            company=validated_data.get("company"),
            groupprocess__group=group,
            academic_plan=validated_data.get("academic_plan"),
            renter_workspace=validated_data.get("renter_workspace", "individual"),
            status__in=cls.BOOKED_STATUSES,
            participant_decisions__isnull=True,
        ).exists():
            raise ValidationError(
                _("You already have an open visit request for this accommodation.")
            )

        visit = PropertyVisit.objects.create(
            tenant=tenant, property=property_obj, **validated_data
        )

        from ...viewing_commands import notify

        notification = None

        # * Notify property owner of new visit request (O-NOTIF-01 Item 1)
        try:
            from core_apps.notifications.models import Notification
            from core_apps.notifications.services import NotificationService

            tenant_name = tenant.get_full_name or tenant.email.split("@")[0]
            notification = NotificationService.create_notification(
                user=property_obj.owner,
                send_push=False,
                notification_type=Notification.NotificationType.VISIT_REQUEST,
                title="طلب زيارة جديد!",
                body=f"{tenant_name} يطلب زيارة {property_obj.title}. راجع الطلب والملاحظات.",
                category="حجز زيارة",
                icon_type="calendar",
                data={
                    "workspace": "owner",
                    "visit_id": str(visit.id),
                    "property_id": str(property_obj.id),
                    "address": (
                        f"{getattr(property_obj.city, 'name', str(property_obj.city))}"
                        f" - {property_obj.district or property_obj.title}"
                    ),
                    "tenant_name": tenant_name,
                    "action_label": "عرض الزيارة",
                },
            )
        except Exception as exc:
            logger.error("Failed to notify owner of visit request: %s", exc)

        notify(visit, "requested", notification)
        return visit
