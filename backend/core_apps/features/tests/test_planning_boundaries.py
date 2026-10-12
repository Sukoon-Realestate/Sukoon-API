"""State-machine, privacy and real catalog checks for the remaining planning APIs."""

import json
import os
from copy import deepcopy
from datetime import timedelta
from pathlib import Path

import pytest
from django.test import override_settings
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from core_apps.chat.services.message_service import (
    get_or_create_direct_conversation,
    send_message,
)
from core_apps.features.models import (
    IdempotencyRecord,
    Lease,
    RentalInterest,
    RentInvoice,
)
from core_apps.features.planning_models import (
    CommuteSearch,
    ConditionReport,
    TenancyTransition,
    TenantAssistantTurn,
)
from core_apps.features.planning_transition_views import reconcile_transitions
from core_apps.features.services.planning import (
    purge_expired_discovery,
    selection_payload,
)
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from .test_current_cycle_contract import awaiting_signatures
from .test_funded_settlement import command, funded_exit
from .test_planning_cycles import (
    API,
    configured_planning_offer,
    create_group,
    join_group,
    planning_grant,
    post,
)
from .test_rental_phase2 import authenticated, rental_participants


def artifact(name, value):
    if directory := os.environ.get("SOKOUN_PLANNING_ARTIFACT_DIR"):
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        (target / name).write_text(json.dumps(value, indent=2))


@pytest.fixture
def current_lease(funded_exit):
    owner, tenant, stranger, lease, _ = funded_exit
    lease.status = "active"
    lease.occupancy_status = "occupied"
    lease.offer_snapshot = selection_payload(
        resolve_offer_snapshot(lease.property, lease.offer_id, 2)[1]
    )
    lease.save()
    return owner, tenant, stranger, lease


def report_body(report, action="submit", **extra):
    return command(
        report["revision"],
        action=action,
        lease_id=report["lease_id"],
        kind=report["kind"],
        inspected_on=report["inspected_on"],
        selection=report["selection"],
        items=deepcopy(report["items"]),
        baseline_id=report["baseline_id"],
        baseline_revision=report["baseline_revision"],
        evidence_ids=[x["id"] for x in report["evidence"]],
        **extra,
    )


@pytest.mark.django_db
def test_condition_objection_reapproval_immutable_baseline_and_private_evidence(
    current_lease,
):
    owner, tenant, stranger, lease = current_lease
    path = f"leases/{lease.id}/condition-report-context/?kind=move_in"
    draft = authenticated(owner).get(API + path).data
    draft["items"][0]["condition"] = "good"
    body = report_body(draft)
    created = post(owner, f"leases/{lease.id}/condition-reports/", body, 201)
    item = created.data["resource"]
    assert (
        post(owner, f"leases/{lease.id}/condition-reports/", body, 201).data
        == created.data
    )
    record_path = f"condition-reports/{item['id']}/"
    assert authenticated(stranger).get(API + record_path).status_code == 404
    bad = report_body(item, "acknowledge")
    bad["items"][0]["condition"] = "damaged"
    post(tenant, record_path + "acknowledge/", bad, 409)
    objection = post(
        tenant,
        record_path + "object/",
        report_body(item, "object", objection="The key is missing"),
    ).data["resource"]
    post(owner, record_path + "finalize/", report_body(objection, "finalize"), 403)
    revised = report_body(objection)
    revised["items"][0]["condition"] = "worn"
    item = post(owner, record_path + "submit/", revised).data["resource"]
    post(
        tenant,
        record_path + "acknowledge/",
        report_body(created.data["resource"], "acknowledge"),
        409,
    )
    item = post(
        tenant, record_path + "acknowledge/", report_body(item, "acknowledge")
    ).data["resource"]
    assert item["status"] == "acknowledged"
    item = post(owner, record_path + "finalize/", report_body(item, "finalize")).data[
        "resource"
    ]
    assert item["status"] == "final" and item["allowed_actions"] == ["addendum"]
    post(owner, record_path + "submit/", report_body(item), 403)
    assert ConditionReport.objects.get().versions
    move_out = (
        authenticated(tenant)
        .get(API + f"leases/{lease.id}/condition-report-context/?kind=move_out")
        .data
    )
    assert (
        move_out["baseline_id"] == item["id"]
        and move_out["baseline_items"] == item["items"]
    )
    wrong_baseline = report_body(move_out)
    wrong_baseline["baseline_revision"] = 1
    post(tenant, f"leases/{lease.id}/condition-reports/", wrong_baseline, 409)
    wrong_evidence = report_body(move_out)
    wrong_evidence["evidence_ids"] = [str(stranger.id)]
    post(tenant, f"leases/{lease.id}/condition-reports/", wrong_evidence, 400)
    lease.refresh_from_db()
    assert lease.status == "active" and lease.occupancy_status == "occupied"
    assert not RentInvoice.objects.filter(invoice_type="adjustment").exists()
    artifact(
        "django-condition-contract.json",
        {
            "draft": draft,
            "created": created.json()["data"],
            "final": item,
            "move_out": move_out,
            "create_body": body,
            "actor_id": str(owner.id),
            "grant": planning_grant(owner, "condition_reports", "submit"),
        },
    )


def transition_body(lease, kind, action, revision=0, **extra):
    return command(
        revision,
        lease_id=str(lease.id),
        kind=kind,
        action=action,
        requested_on=str(lease.end_date),
        reason="Leaving after the current lease",
        **extra,
    )


@pytest.mark.django_db
def test_notice_does_not_release_possession_or_change_legal_terms(current_lease):
    owner, tenant, stranger, lease = current_lease
    body = transition_body(lease, "moveOutNotice", "submit")
    created = post(tenant, f"leases/{lease.id}/move-out-notices/", body, 201)
    item = created.data["resource"]
    path = f"move-out-notices/{item['id']}/"
    post(
        tenant,
        path + "acknowledge/",
        transition_body(lease, "moveOutNotice", "acknowledge", item["revision"]),
        403,
    )
    post(
        stranger,
        path + "acknowledge/",
        transition_body(lease, "moveOutNotice", "acknowledge", item["revision"]),
        404,
    )
    item = post(
        owner,
        path + "acknowledge/",
        transition_body(lease, "moveOutNotice", "acknowledge", item["revision"]),
    ).data["resource"]
    assert reconcile_transitions() == 0
    lease.refresh_from_db()
    assert lease.status == "active" and lease.occupancy_status == "occupied"
    lease.status = "ended"
    lease.occupancy_status = "returned"
    lease.save()
    # Future dates still prevent a transition becoming effective.
    assert reconcile_transitions() == 0
    lease.end_date = timezone.localdate()
    lease.save()
    TenancyTransition.objects.filter(id=item["id"]).update(
        requested_on=timezone.localdate()
    )
    assert reconcile_transitions() == 1 and reconcile_transitions() == 0
    effective = authenticated(tenant).get(API + path).data
    assert effective["status"] == "effective" and effective["allowed_actions"] == []
    artifact(
        "django-notice-contract.json",
        {
            "created": created.json()["data"],
            "effective": effective,
            "create_body": body,
            "actor_id": str(tenant.id),
            "grant": planning_grant(tenant, "move_out_notices", "submit"),
        },
    )


def activate_replacement_interest(owner, candidate, interest):
    from .test_rental_phase2 import agreement_terms
    from .test_current_cycle_contract import create_checkout, capture

    starts = interest.desired_start
    terms = agreement_terms(starts, starts + timedelta(days=31))
    proposal = post(
        owner,
        "terms-proposals/",
        command(
            interest_id=str(interest.id),
            interest_revision=interest.revision,
            offer_id=interest.offer_id,
            offer_revision=interest.offer_revision,
            terms=terms,
        ),
        201,
    ).data["resource"]
    proposal = post(
        candidate,
        f"terms-proposals/{proposal['id']}/respond/",
        command(proposal["revision"], decision="accept"),
    ).data["resource"]
    interest.refresh_from_db()
    invitation = post(
        owner,
        "tenancy-invitations/",
        command(
            interest_id=str(interest.id),
            interest_revision=interest.revision,
            property_id=str(interest.property.id),
            tenant_id=str(candidate.id),
            offer_id=interest.offer_id,
            offer_revision=interest.offer_revision,
            terms_proposal_id=proposal["id"],
        ),
        201,
    ).data["resource"]
    invitation = post(
        candidate,
        f"tenancy-invitations/{invitation['id']}/respond/",
        {
            "decision": "accepted",
            "revision": invitation["revision"],
            "request_key": command()["request_key"],
        },
    ).data
    lease = post(
        owner,
        "leases/",
        command(
            invitation_id=invitation["id"],
            invitation_revision=invitation["revision"],
            property_id=str(interest.property.id),
            tenant_id=str(candidate.id),
            offer_id=interest.offer_id,
            offer_revision=interest.offer_revision,
            terms=terms,
        ),
        201,
    ).data["resource"]
    for actor in (owner, candidate):
        lease = post(
            actor,
            f"leases/{lease['id']}/review/",
            command(lease["revision"], decision="accept_review"),
        ).data["resource"]
    lease = post(
        owner,
        f"leases/{lease['id']}/submit-for-signature/",
        command(lease["revision"], decision="submit_for_signature"),
    ).data["resource"]
    for actor in (owner, candidate):
        session = post(
            actor,
            f"leases/{lease['id']}/signing-session/",
            command(
                lease["revision"],
                document_id=lease["document_id"],
                document_hash=lease["document_hash"],
            ),
            201,
        ).data["resource"]
        descriptor = session["mock_completion"]
        result = authenticated(actor).post(
            descriptor["path"], command(descriptor["expected_revision"]), format="json"
        )
        assert result.status_code == 200, result.data
    incoming = Lease.objects.get(id=lease["id"])
    assert incoming.status == "signed"
    assert reconcile_transitions() == 0
    attempt = create_checkout(candidate, incoming.invoices.get())
    assert capture(attempt).status_code == 200
    incoming.refresh_from_db()
    assert incoming.status == "active"
    return incoming


@pytest.mark.django_db
def test_replacement_requires_incoming_consent_owner_approval_and_separate_active_lease(
    current_lease,
    monkeypatch,
):
    owner, tenant, candidate, lease = current_lease
    interest = RentalInterest.objects.create(
        property=lease.property,
        tenant=candidate,
        offer_id=lease.offer_id,
        offer_revision=2,
        offer_snapshot=lease.offer_snapshot,
        desired_start=lease.end_date,
        months=1,
        occupants=1,
    )
    created = post(
        tenant,
        f"leases/{lease.id}/replacement-requests/",
        transition_body(lease, "replacement", "submit"),
        201,
    )
    item = created.data["resource"]
    path = f"replacement-requests/{item['id']}/"
    assert (
        authenticated(tenant)
        .get(API + f"leases/{lease.id}/replacement-candidates/")
        .data["results"]
        == []
    )
    post(
        tenant,
        path + "nominate/",
        transition_body(
            lease,
            "replacement",
            "nominate",
            item["revision"],
            candidate_id=str(interest.id),
            candidate_revision=1,
        ),
        403,
    )
    item = post(
        owner,
        path + "nominate/",
        transition_body(
            lease,
            "replacement",
            "nominate",
            item["revision"],
            candidate_id=str(interest.id),
            candidate_revision=1,
        ),
    ).data["resource"]
    post(
        owner,
        path + "approve_candidate/",
        transition_body(lease, "replacement", "approve_candidate", item["revision"]),
        403,
    )
    assert authenticated(candidate).get(API + path).status_code == 404
    invitations = (
        authenticated(candidate).get(API + "replacement-invitations/").data["results"]
    )
    assert len(invitations) == 1 and "reason" not in invitations[0]
    consent_body = command(item["revision"], decision="accept")
    consent_grant = planning_grant(
        candidate, "replacements", "accept_candidate_nomination", item["id"]
    )
    consent = post(candidate, path + "candidate-consent/", consent_body)
    assert (
        post(candidate, path + "candidate-consent/", consent_body).data == consent.data
    )
    recovered = authenticated(candidate).get(
        API
        + f"rental-operations/{consent_body['request_key']}/?subject_id={item['id']}"
    )
    assert recovered.status_code == 200 and recovered.data["status"] == "confirmed"
    item = authenticated(owner).get(API + path).data
    for action in ("approve_candidate", "approve_availability"):
        item = post(
            owner,
            path + action + "/",
            transition_body(lease, "replacement", action, item["revision"]),
        ).data["resource"]
    assert item["incoming_agreement_status"] == "not_started"
    assert reconcile_transitions() == 0
    assert Lease.objects.count() == 1
    # The outgoing possession boundary is covered by the full HTTP journey.
    # The incoming agreement is created, reviewed, signed and captured via API.
    lease.status = "ended"
    lease.occupancy_status = "returned"
    lease.save()
    incoming = activate_replacement_interest(owner, candidate, interest)
    interest.refresh_from_db()
    assert (
        interest.revision > item["candidate_revision"]
    )  # Normal proposed/invited progression.
    assert reconcile_transitions() == 0  # The agreed date has not arrived.
    from datetime import datetime, timezone as dt_timezone

    due_now = datetime.combine(
        lease.end_date, datetime.min.time(), dt_timezone.utc
    ) + timedelta(hours=12)
    monkeypatch.setattr(timezone, "now", lambda: due_now)
    assert reconcile_transitions() == 1 and reconcile_transitions() == 0
    effective = authenticated(tenant).get(API + path).data
    assert effective["status"] == "effective" and effective["incoming_lease_id"] == str(
        incoming.id
    )
    artifact(
        "django-replacement-contract.json",
        {
            "created": created.json()["data"],
            "effective": effective,
            "invitation": invitations[0],
            "consent": consent.json()["data"],
            "consent_body": consent_body,
            "actor_id": str(candidate.id),
            "grant": consent_grant,
        },
    )


def commute_body(prop):
    return command(
        destinations=[
            {
                "label": "Work",
                "location": {"latitude": 30.04, "longitude": 31.23},
                "mode": "walking",
                "limit_minutes": 60,
            }
        ],
        local_time="2026-12-01T08:30",
        time_kind="arrive_by",
        timezone="Africa/Cairo",
        balance=False,
        hard_limits=True,
        filters={
            "city": str(prop.city.id),
            "price_max": "15000",
            "price_period": "monthly",
        },
    )


@pytest.mark.django_db
def test_commute_mock_filters_rank_before_paging_unknown_exclusion_expiry_and_privacy(
    rental_participants,
):
    owner, tenant, stranger, prop, _ = rental_participants
    prop.latitude, prop.longitude = 30.04, 31.23
    prop.save()
    body = commute_body(prop)
    created = post(tenant, "commute-searches/", body, 201)
    item = created.data["resource"]
    assert item["coverage"] == "full_catalog" and item["provider"] == "mock_haversine"
    path = f"commute-searches/{item['id']}/"
    result = authenticated(tenant).get(API + path + "results/").data
    assert result["results"][0]["property_id"] == str(prop.id)
    assert result["results"][0]["estimates"][0]["duration_seconds"] == 0
    assert "mock" in result["results"][0]["estimates"][0]["explanation"]
    assert authenticated(stranger).get(API + path + "results/").status_code == 404
    with override_settings(PLANNING_MOCK_DISCOVERY=False, PLANNING_ROUTES_API_KEY=""):
        post(tenant, "commute-searches/", {**body, **command()}, 403)
    expensive = post(
        tenant,
        "commute-searches/",
        {**body, **command(), "filters": {"price_max": "5", "price_period": "monthly"}},
        201,
    ).data["resource"]
    assert (
        authenticated(tenant)
        .get(API + f"commute-searches/{expensive['id']}/results/")
        .data["results"]
        == []
    )
    prop.status = "rejected"
    prop.save()
    assert authenticated(tenant).get(API + path + "results/").data["results"] == []
    CommuteSearch.objects.filter(id=item["id"]).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert authenticated(tenant).get(API + path).status_code == 409
    purge_expired_discovery()
    assert CommuteSearch.objects.get(id=item["id"]).query == {}
    post(tenant, "commute-searches/", body, 410)
    artifact(
        "django-commute-contract.json",
        {
            "created": created.json()["data"],
            "results": result,
            "create_body": body,
            "actor_id": str(tenant.id),
            "grant": planning_grant(tenant, "commute", "search"),
        },
    )


@pytest.mark.django_db
def test_assistant_grounded_catalog_actions_no_raw_prompt_and_account_scoped_history(
    rental_participants,
):
    owner, tenant, stranger, prop, _ = rental_participants
    body = command(
        session_id="private-test",
        previous_turn_id="",
        language="en",
        text=f"An apartment in {prop.city.name} under 15000 near my workplace",
        retain_history=False,
    )
    created = post(tenant, "tenant-assistant/turns/", body, 201)
    reply = created.data["resource"]
    assert reply["grounded_property_ids"] == [str(prop.id)]
    assert reply["provider"] == "catalog_rules" and reply["unresolved_requirements"]
    assert "price_max" not in reply["filters"]
    assert any("price period" in reason for reason in reply["unresolved_requirements"])
    assert all(
        x["kind"] in {"search", "property", "compare"} and "endpoint" not in x
        for x in reply["actions"]
    )
    assert reply["costs"] == []  # Prices require an explicitly selected offer.
    turn = TenantAssistantTurn.objects.get(id=reply["id"])
    assert body["text"] not in json.dumps(turn.reply)
    assert body["text"] not in json.dumps(
        IdempotencyRecord.objects.get(operation="assistant.turn").response_data
    )
    post(
        stranger,
        "tenant-assistant/turns/",
        {**body, **command(), "previous_turn_id": reply["id"]},
        404,
    )
    post(
        tenant,
        "tenant-assistant/turns/",
        {
            **body,
            **command(),
            "session_id": "different",
            "previous_turn_id": reply["id"],
        },
        404,
    )
    TenantAssistantTurn.objects.filter(pk=turn.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    purge_expired_discovery()
    turn.refresh_from_db()
    assert turn.reply == {} and turn.session_id == ""
    post(tenant, "tenant-assistant/turns/", body, 410)
    artifact(
        "django-assistant-contract.json",
        {
            "created": created.json()["data"],
            "create_body": body,
            "actor_id": str(tenant.id),
            "grant": planning_grant(tenant, "tenant_assistant", "ask"),
            "catalog": authenticated(tenant)
            .get("/api/v1/properties/filter-options/")
            .json()["data"],
        },
    )


@pytest.mark.django_db
def test_departure_replays_and_recovers_without_disclosing_current_group(
    rental_participants,
):
    _, tenant, member, prop, _ = rental_participants
    group, _, _ = join_group(tenant, member, create_group(tenant, prop))
    body = command(
        group["revision"], action="leave", roster_revision=group["roster_revision"]
    )
    path = f"housing-groups/{group['id']}/leave/"
    left = post(member, path, body)
    assert left.data["resource"]["members"] == []
    assert post(member, path, body).data == left.data
    recovery = authenticated(member).get(
        API + f"rental-operations/{body['request_key']}/?subject_id={group['id']}"
    )
    assert recovery.status_code == 200 and recovery.data["status"] == "confirmed"
    assert (
        authenticated(member).get(API + f"housing-groups/{group['id']}/").status_code
        == 404
    )


@pytest.mark.django_db
def test_chat_send_uses_current_mutual_roommate_consent(rental_participants):
    _, tenant, member, _, _ = rental_participants
    post(
        tenant,
        "lifestyle-profile/",
        command(discoverable=True, habits={}, preferences={}, disclosed=[]),
    )
    profile = post(
        member,
        "lifestyle-profile/",
        command(discoverable=True, habits={}, preferences={}, disclosed=[]),
    ).data["resource"]
    connection = post(
        tenant,
        f"roommate-candidates/{profile['id']}/request/",
        command(decision="request", candidate_revision=1),
        201,
    ).data["resource"]
    with pytest.raises(PermissionDenied):
        get_or_create_direct_conversation(user=tenant, other_user=member)
    post(
        member,
        f"roommate-connections/{connection['id']}/accept/",
        command(1, decision="accept"),
    )
    conversation = get_or_create_direct_conversation(user=tenant, other_user=member)
    send_message(conversation=conversation, sender=tenant, content="Hello")
    post(
        member,
        f"roommate-connections/{connection['id']}/block/",
        command(2, decision="block"),
    )
    for sender in (tenant, member):
        with pytest.raises(PermissionDenied):
            send_message(
                conversation=conversation, sender=sender, content="No longer permitted"
            )
    assert conversation.messages.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path,values",
    [
        (
            "housing-requests/",
            {"action": "publish", "criteria": {"city_id": "invalid"}},
        ),
        (
            "housing-groups/",
            {
                "action": "create",
                "roster_revision": 0,
                "capacity": 2,
                "name": "Test",
                "visibility": [],
            },
        ),
        ("lifestyle-profile/", {"discoverable": True, "habits": {"sleep": []}}),
        ("lifestyle-profile/", {"discoverable": True, "disclosed": [{}]}),
        ("commute-searches/", {"destinations": [{"label": "Bad", "mode": []}]}),
        (
            "tenant-assistant/turns/",
            {
                "language": {},
                "text": "Test",
                "session_id": "test",
                "retain_history": False,
            },
        ),
    ],
)
def test_malformed_commands_are_validation_errors_not_server_errors(
    rental_participants, path, values
):
    post(rental_participants[1], path, command(**values), 400)


@pytest.mark.django_db
def test_replacement_does_not_use_an_unrelated_incoming_lease(current_lease):
    from core_apps.features.planning_transition_views import transition_projection

    owner, tenant, candidate, lease = current_lease
    interest = RentalInterest.objects.create(
        property=lease.property,
        tenant=candidate,
        offer_id=lease.offer_id,
        offer_revision=2,
        offer_snapshot=lease.offer_snapshot,
        desired_start=lease.end_date,
        months=1,
        occupants=1,
        status="invited",
    )
    replacement = TenancyTransition.objects.create(
        lease=lease,
        author=tenant,
        kind="replacement",
        requested_on=lease.end_date,
        candidate=interest,
        candidate_revision=1,
        candidate_consented=True,
        candidate_approved=True,
        availability_approved=True,
    )
    Lease.objects.create(
        property=lease.property,
        owner=owner,
        tenant=candidate,
        offer_id=lease.offer_id,
        offer_snapshot=lease.offer_snapshot,
        start_date=lease.end_date,
        end_date=lease.end_date + timedelta(days=31),
        status="active",
        rent_amount_minor=lease.rent_amount_minor,
        legacy_read_only=False,
    )
    projection = transition_projection(replacement)
    assert projection["incoming_agreement_status"] == "not_started"
    assert projection["incoming_lease_id"] == ""
