"""Student group consent changes retain evidence and current destinations."""
# flake8: noqa: F401,F811 -- imported pytest fixtures are injected by name.

import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from django.db import connections
from django.utils import timezone
from core_apps.features.planning_models import GroupProcess, HousingGroup, PlanningEvent
from core_apps.features.planning_group_views_parts.process_payload import (
    invalidate_process,
)
from core_apps.features.services.group_process_events import authorize
from core_apps.features.services.planning_notifications import deliver_planning_events
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from core_apps.properties.models import PropertyVisitDecision
from core_apps.properties.services.viewing_access import (
    participant,
    for_user,
    context_payload,
)
from rest_framework.exceptions import NotFound
from .test_rental_phase2 import authenticated, rental_participants
from .test_funded_settlement import command
from .test_planning_cycles import (
    API,
    configured_planning_offer,
    create_group,
    join_group,
    group_action,
    post,
)

pytestmark = pytest.mark.django_db


def consent(actor, state, action, **values):
    return post(
        actor,
        f"housing-groups/{state['id']}/{action}/",
        command(
            state["revision"],
            roster_revision=state["roster_revision"],
            action=action,
            consent=True,
            **values,
        ),
    ).data["resource"]


def reviewed_visit(parties):
    _, tenant, member, prop, offer_id = parties
    state = create_group(tenant, prop)
    state, _, _ = join_group(tenant, member, state)
    group = HousingGroup.objects.get(id=state["id"])
    # These are independent counters; a late join must still be able to attend.
    group.revision = 40
    group.save()
    group.memberships.filter(user=member).update(joined_revision=30)
    state = authenticated(tenant).get(API + f"housing-groups/{group.id}/").data
    _, selection = resolve_offer_snapshot(prop, offer_id, 2)
    selection["bed_id"] = selection["bed_name"] = ""
    state = consent(
        tenant,
        state,
        "request_visit",
        selection=selection,
        participant_ids=[str(tenant.id), str(member.id)],
    )
    process = state["visits"][0]
    state = consent(
        member,
        state,
        "consent_visit",
        item_id=process["id"],
        item_revision=process["revision"],
    )
    process = GroupProcess.objects.get(id=process["id"])
    return state, process


def test_roster_change_cancels_same_visit_once_and_notifies_owner(rental_participants):
    owner, tenant, member, _, _ = rental_participants
    state, process = reviewed_visit(rental_participants)
    visit = process.visit
    assert process.access_group_revision == 40
    assert participant(visit, member) and for_user(member).filter(pk=visit.pk).exists()
    body = command(
        state["revision"], roster_revision=state["roster_revision"], action="leave"
    )
    path = f"housing-groups/{state['id']}/leave/"
    result = post(member, path, body).data
    assert post(member, path, body).data == result
    process.refresh_from_db()
    visit.refresh_from_db()
    assert process.visit_id == visit.pk and visit.status == "canceled"
    assert visit.revision == 2 and len(process.history) == 1
    assert process.history[0]["reason_code"] == "roster_changed"
    assert set(process.history[0]["previous_consented_ids"]) == {
        str(tenant.id),
        str(member.id),
    }
    assert process.consented_ids == []
    owner_event = PlanningEvent.objects.get(
        recipient=owner,
        destination__event_kind="group_process_changed",
    )
    assert owner_event.destination["target_id"] == str(visit.id)
    assert owner_event.destination["workspace"] == "owner"
    assert not PlanningEvent.objects.filter(
        recipient=member,
        destination__event_kind="group_process_changed",
    ).exists()
    payload = authenticated(tenant).get(API + f"housing-groups/{state['id']}/").data
    assert payload["visits"][0]["history"][0]["to_status"] == "withdrawn"
    assert "previous_consented_ids" not in str(payload)
    assert (
        context_payload(visit, owner)["group_history"]
        == payload["visits"][0]["history"]
    )
    deliver_planning_events(event_kinds=["group_process_changed"])
    owner_event.refresh_from_db()
    assert owner_event.notification.scope == "owner"
    assert owner_event.notification.data["target_id"] == str(visit.id)


def test_old_event_opens_current_history_but_rejoin_cannot_restore_access(
    rental_participants,
):
    owner, tenant, member, _, _ = rental_participants
    state, process = reviewed_visit(rental_participants)
    invalidate_process(process, "consent_withdrawn")
    old = PlanningEvent.objects.get(
        recipient=member, destination__event_kind="group_process_changed"
    )
    process.revision += 1
    process.save()
    assert authorize(old)["body"]
    group_action(member, state, "leave")
    with pytest.raises(NotFound):
        authorize(old)
    state = authenticated(tenant).get(API + f"housing-groups/{state['id']}/").data
    join_group(tenant, member, state)
    with pytest.raises(NotFound):
        authorize(old)
    assert (
        authenticated(member).get(API + f"housing-groups/{state['id']}/").data["visits"]
        == []
    )
    deliver_planning_events(event_kinds=["group_process_changed"])
    old.refresh_from_db()
    assert (
        old.delivery_status == "stale_or_unauthorized" and old.notification_id is None
    )


def test_completed_attendance_is_preserved_and_history_does_not_expose_reasons(
    rental_participants,
):
    owner, tenant, member, _, _ = rental_participants
    state, process = reviewed_visit(rental_participants)
    decision = PropertyVisitDecision.objects.create(
        visit=process.visit,
        tenant=tenant,
        owner=owner,
        value="decline",
        reason="Private attendance statement",
        attested_at=timezone.now(),
        request_key=uuid.uuid4(),
        property_id_snapshot=process.property.id,
        visit_revision=process.visit.revision,
    )
    old_revision = process.visit.revision
    group_action(member, state, "leave")
    process.refresh_from_db()
    assert process.status == "completed" and process.visit.revision == old_revision
    assert PropertyVisitDecision.objects.filter(pk=decision.pk).exists()
    assert participant(process.visit, tenant)
    assert "Private attendance statement" not in str(
        context_payload(process.visit, owner)["group_history"]
    )
    assert process.history[0]["to_status"] == "completed"


def test_owner_receives_withdrawn_application_and_stale_review_is_rejected(
    rental_participants,
):
    owner, tenant, member, prop, _ = rental_participants
    state, visit_process = reviewed_visit(rental_participants)
    application = GroupProcess.objects.create(
        group=visit_process.group,
        initiated_by=tenant,
        property=prop,
        kind="application",
        roster_revision=state["roster_revision"],
        access_group_revision=state["revision"],
        status="under_review",
        selection=visit_process.selection,
        participant_ids=visit_process.participant_ids,
        consented_ids=visit_process.participant_ids,
    )
    group_action(
        member,
        state,
        "withdraw_application_consent",
        item_id=str(application.id),
        item_revision=1,
    )
    payload = (
        authenticated(owner).get(API + f"group-applications/{application.id}/").data
    )
    assert payload["status"] == "withdrawn" and payload["allowed_actions"] == []
    assert payload["history"][0]["reason_code"] == "consent_withdrawn"
    event = PlanningEvent.objects.get(
        recipient=owner, destination__process_id=str(application.id)
    )
    assert (
        event.destination["target_id"] == str(application.id)
        and event.destination["workspace"] == "owner"
    )
    post(owner, f"group-applications/{application.id}/approve/", command(1), 409)


@pytest.mark.django_db(transaction=True)
def test_concurrent_review_and_withdrawal_cannot_restore_old_consent(
    rental_participants,
):
    owner, tenant, member, prop, _ = rental_participants
    state, visit_process = reviewed_visit(rental_participants)
    application = GroupProcess.objects.create(
        group=visit_process.group,
        initiated_by=tenant,
        property=prop,
        kind="application",
        roster_revision=state["roster_revision"],
        access_group_revision=state["revision"],
        status="under_review",
        selection=visit_process.selection,
        participant_ids=visit_process.participant_ids,
        consented_ids=visit_process.participant_ids,
    )
    barrier = Barrier(2)

    def act(owner_action):
        try:
            actor = owner if owner_action else member
            path = (
                f"group-applications/{application.id}/approve/"
                if owner_action
                else f"housing-groups/{state['id']}/leave/"
            )
            body = (
                command(1)
                if owner_action
                else command(
                    state["revision"],
                    roster_revision=state["roster_revision"],
                    action="leave",
                )
            )
            barrier.wait(timeout=10)
            return (
                authenticated(actor).post(API + path, body, format="json").status_code
            )
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        reviewed, left = list(pool.map(act, [True, False]))
    assert left == 200 and reviewed in {200, 409}
    application.refresh_from_db()
    assert application.status == "withdrawn" and application.consented_ids == []
    assert application.history[-1]["reason_code"] == "roster_changed"
    assert (
        PlanningEvent.objects.filter(
            recipient=owner,
            destination__process_id=str(application.id),
            destination__event_kind="group_process_changed",
        ).count()
        == 1
    )


def test_membership_migration_only_expands_access_for_unchanged_rosters(
    rental_participants,
):
    from importlib import import_module
    from types import SimpleNamespace
    from django.apps import apps
    from django.db import connection

    _, _, member, _, _ = rental_participants
    _, process = reviewed_visit(rental_participants)
    migrate = import_module(
        "core_apps.features.migrations.0081_group_process_membership_scope"
    ).preserve_access
    GroupProcess.objects.filter(pk=process.pk).update(access_group_revision=0)
    migrate(apps, SimpleNamespace(connection=connection))
    process.refresh_from_db()
    assert process.access_group_revision == process.group.revision
    # A changed roster must never acquire the latest membership epoch.
    process.group.roster_revision += 1
    process.group.revision += 1
    process.group.save()
    process.group.memberships.filter(user=member).update(
        joined_revision=process.group.revision
    )
    migrate(apps, SimpleNamespace(connection=connection))
    process.refresh_from_db()
    assert process.access_group_revision == process.roster_revision
    assert not participant(process.visit, member)
