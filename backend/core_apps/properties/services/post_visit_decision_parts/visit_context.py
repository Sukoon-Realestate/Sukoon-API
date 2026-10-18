"""Post visit decision: visit context."""

from .linked_invitation import (
    decision_for,
    linked_invitation,
    historical_agreement,
    eligibility,
)
from .continuation import continuation, reason_visible


def visit_context(visit, actor):
    from ..viewing_access import participant, context_payload

    decision_actor = actor if participant(visit, actor) else visit.tenant
    decision = decision_for(visit, decision_actor)
    invitation, ambiguous = linked_invitation(visit, decision_actor)
    if invitation and actor.pk not in {invitation.owner_id, invitation.tenant_id}:
        # A later property owner does not acquire another owner's contract or
        # invitation permissions merely by viewing the property's old visit.
        invitation = None
    legacy_lease, legacy_ambiguous = (
        historical_agreement(visit) if not invitation else (None, False)
    )
    ambiguous = ambiguous or legacy_ambiguous
    actions = eligibility(
        visit,
        actor,
        decision=decision,
        invitation=invitation or legacy_lease,
        ambiguous=ambiguous,
    )
    serialized = None
    if decision:
        serialized = {
            "id": str(decision.id),
            "visit_id": str(visit.id),
            "value": decision.value,
            "attended": decision.attended,
            "attendance_source": decision.attendance_source,
            "attested_at": decision.attested_at.isoformat(),
            "created_at": decision.created_at.isoformat(),
            "visit_revision": decision.visit_revision,
        }
        if reason_visible(actor, visit) and decision.value == "decline":
            serialized["reason"] = decision.reason
    return {
        "revision": visit.revision,
        "viewing_context": context_payload(visit, actor),
        "offer_id": visit.offer_id,
        "offer_snapshot": visit.offer_snapshot,
        "post_visit_decision": serialized,
        "post_visit_actions": actions,
        "rental_continuation": continuation(
            visit, actor, decision, invitation, ambiguous, actions, legacy_lease
        ),
    }


def record_event(visit, decision):
    from core_apps.features.planning_models import PlanningEvent
    from core_apps.notifications.services.notification_service import (
        NotificationService,
    )

    data = {
        "action_type": "view_visit",
        "workspace": "owner",
        "target_id": str(visit.id),
        "visit_id": str(visit.id),
        "property_id": str(visit.property.id),
        "source_decision_id": str(decision.id),
        "event_kind": "visit_post_decision",
        "schema_version": "1",
    }
    event = PlanningEvent.objects.create(
        recipient=visit.property.owner,
        event_key=f"visit.post_visit_decision:{decision.id}",
        destination=data,
    )
    data["event_id"] = str(event.id)
    event.notification = NotificationService.create_notification(
        user=visit.property.owner,
        title="قرار المستأجر بعد المعاينة / Tenant visit decision",
        body=(
            "يرغب المستأجر في المتابعة / The tenant would like to proceed."
            if decision.value == "proceed"
            else "اختار المستأجر عدم المتابعة / The tenant chose not to continue."
        ),
        category="visit_post_decision",
        data=data,
        send_push=False,
    )
    event.save(update_fields=["notification", "updated_at"])
