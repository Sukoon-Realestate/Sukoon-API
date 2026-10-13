"""VisitDecision operations owned by PropertyVisitService."""

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied, ValidationError
from ....models import PropertyVisit
from ..logger import logger


class VisitDecisionMixin:
    @classmethod
    @transaction.atomic
    def update_visit_status(cls, user, visit_obj, status):
        """
        Updates the status of a property visit request.
        """
        if status == PropertyVisit.Status.CONFIRMED:
            return cls.accept_visit(user=user, visit_obj=visit_obj)

        visit_obj = (
            PropertyVisit.objects.select_for_update()
            .select_related("property", "property__owner", "property__city", "tenant")
            .get(pk=visit_obj.pk)
        )

        if status == PropertyVisit.Status.CANCELED:
            # Only tenant can cancel the visit
            if visit_obj.tenant != user:
                raise PermissionDenied(
                    _("You do not have permission to cancel this visit.")
                )
            if visit_obj.status in [
                PropertyVisit.Status.CANCELED,
                PropertyVisit.Status.REJECTED,
            ]:
                raise ValidationError(
                    _("This visit has already been canceled or rejected.")
                )
            visit_obj.status = status
            visit_obj.save(update_fields=["status", "updated_at"])
            return visit_obj

        elif status == PropertyVisit.Status.REJECTED:
            # Only owner can confirm/reject the visit
            if visit_obj.property.owner != user:
                raise PermissionDenied(
                    _(
                        "You do not have permission to confirm or reject this visit request."
                    )
                )
            if visit_obj.status != PropertyVisit.Status.PENDING:
                raise ValidationError(
                    _(
                        f"Cannot change status from {visit_obj.status} to {status}. "
                        "Only pending requests can be confirmed or rejected."
                    )
                )
            visit_obj.status = status
            visit_obj.save(update_fields=["status", "updated_at"])

            # * Notify tenant on accept (T-NOTIF-01/02) or reject
            try:
                from core_apps.notifications.models import Notification
                from core_apps.notifications.services import NotificationService

                owner_name = visit_obj.property.owner.get_full_name or "المالك"
                NotificationService.create_notification(
                    user=visit_obj.tenant,
                    notification_type=Notification.NotificationType.VISIT_REJECTED,
                    title="تم رفض طلب الزيارة",
                    body=f"نعتذر، لم يتمكن {owner_name} من قبول موعد الزيارة.",
                    category="حجز زيارة",
                    icon_type="cancel",
                    data={
                        "visit_id": str(visit_obj.id),
                        "property_id": str(visit_obj.property.id),
                    },
                )
            except Exception as exc:
                logger.error("Failed to notify tenant of visit status update: %s", exc)

            return visit_obj

        else:
            raise ValidationError(_("Invalid status transition requested."))

    @classmethod
    @transaction.atomic
    def accept_visit(cls, user, visit_obj):
        """Atomically accept a visit and persist its reciprocal contact grant."""
        visit = (
            PropertyVisit.objects.select_for_update()
            .select_related("property", "property__owner", "property__city", "tenant")
            .get(pk=visit_obj.pk)
        )
        if visit.property.owner != user:
            raise PermissionDenied(
                _("You do not have permission to accept this visit.")
            )
        if visit.accepted_at:
            return visit
        if visit.status == PropertyVisit.Status.CONFIRMED:
            raise ValidationError(_("This visit has already been confirmed."))
        if visit.status != PropertyVisit.Status.PENDING:
            raise ValidationError(_("Only pending visit requests can be accepted."))

        visit.status = PropertyVisit.Status.CONFIRMED
        visit.accepted_at = timezone.now()
        visit.save(update_fields=["status", "accepted_at", "updated_at"])

        from core_apps.chat.models import Conversation
        from core_apps.notifications.models import Notification
        from core_apps.notifications.services import NotificationService
        from core_apps.notifications.services.fcm_service import FCMService

        conversation = (
            Conversation.objects.filter(participant_set__user=user)
            .filter(participant_set__user=visit.tenant)
            .first()
        )
        owner_name = visit.property.owner.get_full_name or "المالك"
        notification_data = {
            "visit_id": str(visit.id),
            "property_id": str(visit.property.id),
            "appointment_date": str(visit.visit_date),
            "appointment_time": str(visit.visit_time),
            "address": (
                f"{getattr(visit.property.city, 'name', str(visit.property.city))}"
                f" - {visit.property.district or visit.property.title}"
            ),
            "action_label": "عرض الزيارة",
            "action_type": "view_visit",
            "target_id": str(visit.id),
        }
        if conversation:
            notification_data["conversation_id"] = str(conversation.id)
        title = "تم قبول طلب زيارتك"
        body = f"وافق المالك {owner_name} على موعد الزيارة. يمكنك الآن رؤية رقم هاتف المالك."
        NotificationService.create_notification(
            user=visit.tenant,
            notification_type=Notification.NotificationType.VISIT_ACCEPTED,
            title=title,
            body=body,
            category="حجز زيارة",
            icon_type="check_circle",
            data=notification_data,
            send_push=False,
        )
        transaction.on_commit(
            lambda: FCMService.send_push_to_user(
                user=visit.tenant,
                title=title,
                body=body,
                data=notification_data,
                notification_type=Notification.NotificationType.VISIT_ACCEPTED,
            )
        )
        return visit

    @classmethod
    @transaction.atomic
    def reject_visit(cls, user, visit_obj, reason=None, custom_reason=None):
        """Owner rejects a pending visit request with an optional reason."""
        return cls.update_visit_status(
            user=user,
            visit_obj=visit_obj,
            status=PropertyVisit.Status.REJECTED,
        )
