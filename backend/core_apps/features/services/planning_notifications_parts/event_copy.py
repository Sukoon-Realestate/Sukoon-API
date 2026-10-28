"""Current destination authority shared by the event bridge and every push retry."""

from rest_framework.exceptions import NotFound
from ..planning_access import planning_subject


def event_copy(event):
    if not isinstance(event.destination, dict):
        raise NotFound()
    if event.destination.get("workspace") == "company":
        from ..company.role_notifications import audience_current

        if not audience_current(event.recipient, event.destination):
            raise NotFound()
    from ..rent_payment_reminders import (
        EVENT_KINDS,
        authorize,
        notification_copy,
    )

    rent_reminder = event.destination.get("event_kind") in EVENT_KINDS
    from ..student_housing.notifications import (
        EVENT_KINDS as STUDENT_EVENT_KINDS,
        authorize as authorize_student,
    )

    student_event = event.destination.get("event_kind") in STUDENT_EVENT_KINDS
    from ..billing_notifications import (
        EVENT_KIND as PURCHASE_EVENT_KIND,
        authorize as authorize_purchase,
    )

    purchase_event = event.destination.get("event_kind") == PURCHASE_EVENT_KIND
    copy = {}
    if event.destination.get("event_kind") == "company_responsibility_updated":
        from ..company.responsibility_management import get

        if event.destination.get("company_role") != "admin":
            raise NotFound()
        get(
            event.recipient,
            event.destination.get("company_id"),
            event.destination.get("target_id"),
        )
        copy = {
            "title": "مراجعة مسؤوليات السكن / Housing responsibility review",
            "body": "راجع التكليف المسند إليك / Review your assigned responsibility",
        }
    elif event.destination.get("event_kind") == "commerce_service_expired":
        from ..commerce_expiration_notifications import authorize as authorize_expiry

        copy = authorize_expiry(event.recipient, event.destination)
    elif event.destination.get("event_kind") == "advanced_planning_updated":
        from ..advanced_planning_notifications import authorize as authorize_planning

        copy = authorize_planning(event)
    elif event.destination.get("action_type") == "open_advanced_execution":
        from ..advanced_execution.notifications import authorize as authorize_execution

        copy = authorize_execution(event)
    elif event.destination.get("action_type") == "open_owner_payment_profile":
        from ..beneficiary_confirmation import notification_copy as beneficiary_copy

        copy = beneficiary_copy(event)
    elif event.destination.get("event_kind") == "refund_updated":
        from ..refund_notifications import authorize as authorize_refund

        copy = authorize_refund(event)
    elif event.destination.get("action_type") == "open_rental_payout":
        from ..payout_notifications import authorize as authorize_payout

        copy = authorize_payout(event)
    elif event.destination.get("action_type") == "open_tour_update":
        from core_apps.virtual_tours.notifications import notification_copy as tour_copy

        copy = tour_copy(event)
    elif event.destination.get("action_type") == "open_group_booking":
        from ..rental_lifecycle.group_terms import notification_copy as group_copy

        copy = group_copy(event)
    elif event.destination.get("action_type") == "open_living_lab":
        from ..living_lab.notifications import authorize as authorize_lab

        copy = authorize_lab(event)
    elif rent_reminder:
        authorize(event)
        copy = notification_copy(event)
    elif student_event:
        copy = authorize_student(event.recipient, event.destination)
    elif purchase_event:
        copy = authorize_purchase(event.recipient, event.destination)
    elif event.destination.get("action_type") == "open_housing_request":
        from ..housing_request_notifications import notification_copy

        copy = notification_copy(event)
    elif event.destination.get("action_type") == "open_search_alert":
        from ...models import SearchAlert

        if not SearchAlert.objects.filter(
            id=event.destination.get("target_id"),
            user=event.recipient,
            revision=event.destination.get("revision"),
            enabled=True,
            deleted_at__isnull=True,
        ).exists():
            raise NotFound()
    elif event.destination.get("event_kind") == "service_activation_update":
        from ..rental_lifecycle.cases import case_queryset

        if (
            not case_queryset(event.recipient)
            .filter(id=event.destination.get("case_id"), kind="service_activation")
            .exists()
        ):
            raise NotFound()
        copy = {
            "title": "متابعة تفعيل الخدمة / Service activation follow-up",
            "body": "افتح المتابعة للاطلاع على الحالة الحالية للخدمة والفاتورة الأصلية / Open the follow-up for the current service status and original invoice.",
        }
    elif event.destination.get("event_kind") == "group_process_changed":
        from ..group_process_events import authorize as authorize_group_change

        copy = authorize_group_change(event)
    elif event.destination.get("event_kind") == "viewing_changed":
        from core_apps.properties.services.viewing_notifications import (
            authorize as authorize_viewing,
        )

        copy = authorize_viewing(event)
    elif event.destination.get("action_type") == "open_support_ticket":
        from core_apps.support.services import get_ticket_detail
        from core_apps.support.models import Ticket

        try:
            get_ticket_detail(
                event.recipient,
                event.destination["target_id"],
                workspace=event.destination.get("workspace"),
            )
        except Ticket.DoesNotExist as error:
            raise NotFound() from error
    elif event.destination.get("action_type") in {
        "open_reviews",
        "open_review_opportunity",
        "open_review_section",
    }:
        from ..reputation.tasks import authorize_notification

        authorize_notification(event)
    elif event.destination.get("action_type") == "open_company_tenancy":
        from ..company.tenancy_events import authorize as authorize_tenancy

        copy = authorize_tenancy(event)
    elif event.destination.get("action_type") == "open_company_terms":
        from ..company.negotiation_projection import authorize as authorize_terms

        copy = authorize_terms(event)
    elif event.destination.get("action_type") == "open_company_contract":
        from ..company.contract_access import get

        get(event.recipient, event.destination["target_id"])
    elif event.destination.get("action_type") == "open_company_mandates":
        from ..company.mandates import authorize as authorize_mandate

        authorize_mandate(event.recipient, event.destination["mandate_id"])
    elif event.destination.get("action_type") == "open_company_request":
        if event.destination.get("event_kind") in {
            "company_package_source_changed",
            "company_package_offer_visibility",
        }:
            from ..company.listing_changes import notification_copy

            return notification_copy(event)
        from ..company.access import company_subject

        if company_subject(event.recipient, event.destination["target_id"]) is None:
            raise NotFound()
        copy = {
            "title": "تغيّر احتياج السكن / Housing need updated",
            "body": "راجع التغييرات والحزم المتأثرة. العقود القائمة محفوظة. / Review the changes and affected packages. Existing agreements are preserved.",
        }
    elif event.destination.get("action_type") == "open_company_work":
        from ..company.access import company_for
        from ..company.approval_routing import work_items

        company = company_for(event.recipient, event.destination["target_id"])
        if (
            not work_items(event.recipient, company)
            .filter(
                id=event.destination.get("item_id"),
                revision=event.destination.get("revision"),
            )
            .exists()
        ):
            raise NotFound()
    elif event.destination.get("action_type") == "open_rental_terms":
        from ..rental_foundation import get_authorized_rental_subject

        get_authorized_rental_subject(event.recipient, event.destination["target_id"])
        # Keep the recorded change even if a newer decision is already
        # present. Opening the destination reads today's state and history.
        messages = {
            "terms.proposed": "مقترح شروط جديد / New rental terms",
            "terms.changed": "نسخة جديدة من الشروط / Rental terms revised",
            "terms.accept": "قُبلت شروط الإيجار / Rental terms accepted",
            "terms.reject": "رُفض مقترح الشروط / Rental terms rejected",
            "terms.request_changes": "طُلب تعديل الشروط / Changes requested",
            "terms.withdraw": "عدول عن شروط الإيجار / Rental terms withdrawn",
            "terms.expired": "انتهت صلاحية الشروط / Rental terms expired",
        }
        copy = {
            "title": messages.get(
                event.destination.get("event_kind"),
                "تحديث التفاوض / Negotiation updated",
            ),
            "body": "راجع الحالة الحالية وسجل التفاوض. / Review the current state and negotiation history.",
        }
    elif event.destination.get("rental_lifecycle"):
        from ..rental_foundation import get_authorized_rental_subject

        item = get_authorized_rental_subject(
            event.recipient, event.destination["target_id"]
        )
        if getattr(item, "revision", 1) != event.destination.get("revision"):
            raise NotFound()
    elif event.destination.get("event_kind") == "company_viewing_decision":
        from core_apps.properties.models import PropertyVisitDecision
        from core_apps.properties.services.viewing_access import can_read
        from ..company.viewing_handoff import validate_source
        from ..rental_phase2 import RentalConflict

        decision = (
            PropertyVisitDecision.objects.select_related(
                "visit__property", "visit__tenant"
            )
            .filter(
                id=event.destination.get("source_decision_id"),
                visit__id=event.destination.get("target_id"),
                visit__company__id=event.destination.get("company_id"),
                visit__company__memberships__user=event.recipient,
                visit__company__memberships__is_active=True,
                visit__company__memberships__is_coordinator=True,
            )
            .first()
        )
        if not decision or not can_read(decision.visit, event.recipient):
            raise NotFound()
        try:
            validate_source(decision.visit, decision)
        except RentalConflict:
            raise NotFound()
    elif event.destination.get("event_kind") == "visit_post_decision":
        from core_apps.properties.models import PropertyVisitDecision

        if (
            event.destination.get("target_id") != event.destination.get("visit_id")
            or not PropertyVisitDecision.objects.filter(
                id=event.destination.get("source_decision_id"),
                visit__id=event.destination.get("visit_id"),
                owner=event.recipient,
                visit__property__owner=event.recipient,
            ).exists()
        ):
            raise NotFound()
    elif event.destination.get("action_type") == "open_rental_center":
        from ...planning_condition_views import participant_lease

        lease = participant_lease(event.recipient, event.destination["lease_id"])
        if lease.status != "active" or lease.occupancy_status == "returned":
            raise NotFound()
    elif event.destination.get("action_type") == "open_rental_change":
        from ...models import RentalChange
        from ...planning_condition_views import participant_lease

        lease = participant_lease(event.recipient, event.destination["lease_id"])
        if not RentalChange.objects.filter(
            id=event.destination["target_id"], lease=lease
        ).exists():
            raise NotFound()
        copy = {
            "title": "تحديث مقترح العقد / Contract proposal update",
            "body": "افتح المقترح لمراجعة النسخة الحالية والملاحظات والتاريخ / Open the proposal to review its current version, comments and history.",
        }
    elif event.destination.get("action_type") == "open_replacement_invitations":
        from ...planning_models import TenancyTransition

        if not TenancyTransition.objects.filter(
            id=event.destination["target_id"],
            candidate__tenant=event.recipient,
            kind="replacement",
            status="candidate_pending",
        ).exists():
            raise NotFound()
    elif event.destination.get("event_kind") == "property_review_changed":
        from core_apps.properties.models import Property

        if not Property.objects.filter(
            id=event.destination["target_id"], owner=event.recipient
        ).exists():
            raise NotFound()
        copy = {
            "title": "تحديث مراجعة العقار / Property review update",
            "body": "افتح العقار لعرض حالته الحالية وسبب القرار وتاريخه / Open the property for its current status and review history.",
        }
    else:
        planning_subject(event.recipient, event.destination["target_id"])
        if event.destination.get("action_type") == "open_shared_housing_plan":
            copy = {
                "title": "تحديث خطة السكن المشترك / Shared housing update",
                "body": "افتح خطة السكن لمتابعة الخطوة التالية / Open your housing plan for the next step.",
            }
    return copy
