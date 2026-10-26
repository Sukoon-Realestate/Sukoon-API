"""Actual API/state-machine tests; provider HTTP is replaced at its boundary."""

import json
from copy import deepcopy
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.db import connection
from django.test import override_settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core_apps.features.models import Lease, RentalChange
from core_apps.features.planning_models import (
    CommuteSearch,
    ConditionReport,
    HousingGroup,
    PlanningEvent,
)
from core_apps.features.services.commute_jobs import (
    destination_constraints,
    run_commute,
)
from core_apps.features.services.planning_providers import (
    DiscoveryUnavailable,
    extract_criteria,
    route_matrix,
)
from core_apps.features.services.planning import offer_money
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from .test_funded_settlement import command, funded_exit
from .test_current_cycle_contract import awaiting_signatures
from .test_planning_boundaries import current_lease, report_body, transition_body
from .test_planning_cycles import (
    API,
    configured_planning_offer,
    create_group,
    criteria_for,
    post,
)
from .test_rental_phase2 import authenticated, rental_participants
from .test_rental_phase5 import phase5_lease


@pytest.fixture(autouse=True)
def clear_provider_counters():
    cache.clear()


def journey(prop):
    when = (
        (timezone.now() + timedelta(days=1))
        .astimezone()
        .replace(tzinfo=None)
        .isoformat(timespec="minutes")
    )
    return command(
        destinations=[
            {
                "label": "Private destination",
                "location": {"latitude": 30.04, "longitude": 31.23},
                "mode": "walking",
                "limit_minutes": 20,
                "local_time": when,
                "time_kind": "depart_at",
            }
        ],
        local_time=when,
        timezone="Africa/Cairo",
        time_kind="depart_at",
        hard_limits=True,
        balance=True,
        filters={},
    )


@override_settings(PLANNING_ROUTES_API_KEY="test-only", PLANNING_MOCK_DISCOVERY=False)
@pytest.mark.django_db
def test_real_route_job_is_durable_filters_hard_limits_and_is_private(
    rental_participants,
):
    _, tenant, stranger, prop, _ = rental_participants
    prop.latitude, prop.longitude = 30.04, 31.23
    prop.save()
    body = journey(prop)
    body["destinations"].append(
        {
            **body["destinations"][0],
            "label": "Second",
            "mode": "transit",
            "limit_minutes": 5,
            "time_kind": "arrive_by",
        }
    )
    item = post(tenant, "commute-searches/", body, 201).data["resource"]
    assert item["status"] == "queued" and item["coverage"] == "pending"
    assert "query" not in item and "destinations" not in item
    assert (
        post(tenant, "commute-searches/", body, 201).data["resource"]["id"]
        == item["id"]
    )
    seen = []

    def provider(origins, destination):
        seen.append(destination)
        return [
            {
                "duration_seconds": 100 if destination["mode"] == "walking" else 301,
                "status": "ok",
            }
            for _ in origins
        ]

    with patch("core_apps.features.services.commute_jobs.route_matrix", provider):
        run_commute(item["id"])
        run_commute(item["id"])
    stored = CommuteSearch.objects.get(id=item["id"])
    assert stored.status == "succeeded" and stored.matches == []
    assert [x["time_kind"] for x in seen] == ["depart_at", "arrive_by"]
    assert stored.processed_count == stored.total_count == 1
    assert (
        authenticated(stranger).get(API + f"commute-searches/{item['id']}/").status_code
        == 404
    )


@override_settings(PLANNING_ROUTES_API_KEY="test-only", PLANNING_MOCK_DISCOVERY=False)
@pytest.mark.django_db
def test_route_failure_and_cancel_are_terminal_and_never_fabricate_results(
    rental_participants,
):
    _, tenant, _, prop, _ = rental_participants
    prop.latitude, prop.longitude = 30.04, 31.23
    prop.save()
    item = post(tenant, "commute-searches/", journey(prop), 201).data["resource"]
    with patch(
        "core_apps.features.services.commute_jobs.route_matrix",
        side_effect=DiscoveryUnavailable(code="provider_quota"),
    ):
        run_commute(item["id"])
    saved = CommuteSearch.objects.get(id=item["id"])
    assert saved.status == "failed" and saved.failure_code == "provider_quota"
    assert (
        authenticated(tenant)
        .get(API + f"commute-searches/{item['id']}/results/")
        .status_code
        == 409
    )
    other = post(tenant, "commute-searches/", journey(prop), 201).data["resource"]
    cancel = command(other["revision"], decision="cancel")
    post(tenant, f"commute-searches/{other['id']}/cancel/", cancel)
    with patch("core_apps.features.services.commute_jobs.route_matrix") as provider:
        run_commute(other["id"])
        provider.assert_not_called()
    assert CommuteSearch.objects.get(id=other["id"]).query == {}
    post(tenant, f"commute-searches/{other['id']}/cancel/", cancel)


@override_settings(PLANNING_ROUTE_MODES=["walking", "transit"])
def test_route_adapter_rejects_malformed_and_missing_is_unknown():
    destination = {
        "mode": "walking",
        "time_kind": "depart_at",
        "at": "2027-01-01T08:00:00Z",
        "location": {"latitude": 30, "longitude": 31},
    }
    origins = [{"latitude": 30, "longitude": 31}]
    with patch(
        "core_apps.features.services.planning_providers_parts.route_matrix.post_json",
        return_value=[],
    ):
        assert route_matrix(origins, destination)[0]["duration_seconds"] is None
    for malformed in [
        {"status": "oops"},
        {"originIndex": -1},
        {"condition": "ROUTE_EXISTS", "duration": "NaNs"},
    ]:
        with patch(
            "core_apps.features.services.planning_providers_parts.route_matrix.post_json",
            return_value=[malformed],
        ):
            with pytest.raises(DiscoveryUnavailable):
                route_matrix(origins, destination)


@pytest.mark.parametrize(
    "local,mode,kind",
    [
        ("2026-04-24T00:30", "walking", "depart_at"),
        ("2026-10-29T23:30", "transit", "arrive_by"),
        ("2027-01-01T08:00", "walking", "arrive_by"),
    ],
)
def test_invalid_civil_time_or_unsupported_arrival_is_rejected(local, mode, kind):
    with pytest.raises(ValidationError):
        destination_constraints(
            {
                "destinations": [
                    {"mode": mode, "local_time": local, "time_kind": kind}
                ],
                "timezone": "Africa/Cairo",
            }
        )


@override_settings(
    PLANNING_GEMINI_API_KEY="test-only",
    PLANNING_GEMINI_MODEL="configured-model",
    PLANNING_MOCK_DISCOVERY=False,
)
@pytest.mark.django_db
def test_gemini_grounding_exact_offer_refinement_replay_and_no_raw_prompt(
    rental_participants,
):
    _, tenant, _, prop, offer_id = rental_participants
    text = "Private request do not persist this text"
    body = command(
        text=text,
        session_id="assistant-private",
        language="en",
        retain_history=False,
        context={"property_id": str(prop.id), "offer_id": offer_id},
    )
    response = {
        "filters": {"city": str(prop.city.id), "price_period": "monthly"},
        "questions": ["Is internet included?"],
        "unresolved_requirements": ["Utility costs are unknown"],
    }
    with patch(
        "core_apps.features.planning_discovery_views_parts.tenant_assistant_turns.extract_criteria",
        return_value=response,
    ) as provider:
        item = post(tenant, "tenant-assistant/turns/", body, 201).data["resource"]
        post(tenant, "tenant-assistant/turns/", body, 201)
        assert provider.call_count == 1
        second = {
            **body,
            **command(),
            "previous_turn_id": item["id"],
            "context": {"property_id": str(prop.id), "offer_id": offer_id},
        }
        post(tenant, "tenant-assistant/turns/", second, 201)
        assert provider.call_args.args[3]["filters"]["city"] == str(prop.city.id)
    assert (
        item["provider"] == "gemini"
        and item["costs"][0]["money"]["amount_minor"] == 1_000_000
    )
    assert all(x["property_id"] == str(prop.id) for x in item["grounded_offers"])
    assert any(x["kind"] == "messageDraft" for x in item["actions"])
    assert text not in json.dumps(item)


@pytest.mark.parametrize(
    "value",
    [
        {
            "filters": {"city": "invented"},
            "questions": [],
            "unresolved_requirements": [],
        },
        {
            "filters": {"endpoint": "delete"},
            "questions": [],
            "unresolved_requirements": [],
        },
        {"filters": {}, "questions": "not an array", "unresolved_requirements": []},
    ],
)
def test_gemini_output_is_untrusted(value):
    raw = {"candidates": [{"content": {"parts": [{"text": json.dumps(value)}]}}]}
    with patch(
        "core_apps.features.services.planning_providers_parts.extract_criteria.post_json",
        return_value=raw,
    ):
        with pytest.raises(DiscoveryUnavailable):
            extract_criteria("text", "en", {"cities": [], "amenities": []}, {})


@pytest.mark.django_db
def test_open_join_replay_capacity_authorization_and_notifications(rental_participants):
    owner, tenant, member, prop, _ = rental_participants
    group = create_group(tenant, prop)
    HousingGroup.objects.filter(id=group["id"]).update(visibility="open")
    body = command(group_revision=group["revision"], note="Would like to join")
    joined = post(
        member, f"housing-groups/{group['id']}/join-requests/", body, 201
    ).data["resource"]
    post(member, f"housing-groups/{group['id']}/join-requests/", body, 201)
    assert PlanningEvent.objects.filter(recipient=tenant).count() == 1
    assert (
        authenticated(owner)
        .get(API + f"group-join-requests/{joined['id']}/")
        .status_code
        == 404
    )
    post(owner, f"group-join-requests/{joined['id']}/approve/", command(1), 403)
    post(tenant, f"group-join-requests/{joined['id']}/approve/", command(1))
    post(
        owner,
        f"housing-groups/{group['id']}/join-requests/",
        command(group_revision=2),
        409,
    )
    assert (
        HousingGroup.objects.get(id=group["id"])
        .memberships.filter(status="active")
        .count()
        == 2
    )


@pytest.mark.django_db
def test_disclosure_grants_stop_after_profile_changes(rental_participants):
    _, tenant, member, _, _ = rental_participants
    for user in (tenant, member):
        post(
            user,
            "lifestyle-profile/",
            command(
                discoverable=True,
                habits={"sleep": "early", "smoking": "no"},
                preferences={},
                disclosed=[],
            ),
        )
    candidate = (
        authenticated(tenant).get(API + "roommate-candidates/").data["results"][0]
    )
    relation = post(
        tenant,
        f"roommate-candidates/{candidate['id']}/request/",
        command(
            candidate_revision=1,
            decision="request",
            share_fields=["smoking"],
            share_profile_revision=1,
        ),
        201,
    ).data["resource"]
    post(
        member,
        f"roommate-connections/{relation['id']}/accept/",
        command(1, decision="accept", share_fields=["sleep"], share_profile_revision=1),
    )
    assert authenticated(tenant).get(API + "roommate-connections/").data["results"][0][
        "disclosures"
    ] == ["sleep: early"]
    post(
        member,
        "lifestyle-profile/",
        command(
            1, discoverable=True, habits={"sleep": "late"}, preferences={}, disclosed=[]
        ),
    )
    assert (
        authenticated(tenant)
        .get(API + "roommate-connections/")
        .data["results"][0]["disclosures"]
        == []
    )


@pytest.mark.django_db
def test_report_objections_versions_addendum_and_exact_evidence(current_lease):
    owner, tenant, _, lease = current_lease
    draft = (
        authenticated(owner)
        .get(API + f"leases/{lease.id}/condition-report-context/?kind=move_in")
        .data
    )
    item = post(
        owner, f"leases/{lease.id}/condition-reports/", report_body(draft), 201
    ).data["resource"]
    path = f"condition-reports/{item['id']}/"
    wrong = report_body(item, "acknowledge")
    wrong["evidence_ids"] = ["invented"]
    post(tenant, path + "acknowledge/", wrong, 409)
    item = post(
        tenant,
        path + "object/",
        report_body(
            item,
            "object",
            objection="Recorded defect",
            objection_item_id=item["items"][0]["id"],
        ),
    ).data["resource"]
    revised = post(owner, path + "submit/", report_body(item)).data["resource"]
    assert (
        revised["objections"][0]["note"] == "Recorded defect"
        and len(revised["versions"]) == 2
    )
    item = post(
        tenant, path + "acknowledge/", report_body(revised, "acknowledge")
    ).data["resource"]
    final = post(owner, path + "finalize/", report_body(item, "finalize")).data[
        "resource"
    ]
    addendum = report_body(
        final, supersedes_id=final["id"], source_revision=final["revision"]
    )
    addendum["expected_revision"] = 0
    addendum["items"][0]["note"] = "Correction"
    created = post(owner, f"leases/{lease.id}/condition-reports/", addendum, 201).data[
        "resource"
    ]
    assert created["supersedes_id"] == final["id"] and created["id"] != final["id"]
    persisted = ConditionReport.objects.get(id=final["id"])
    assert persisted.status == "final" and persisted.items[0]["note"] != "Correction"


@pytest.mark.django_db
def test_renewal_blocks_competing_departure(current_lease):
    owner, tenant, _, lease = current_lease
    RentalChange.objects.create(
        lease=lease, requester=owner, kind="renewal", terms={}, reason="Renewal"
    )
    post(
        tenant,
        f"leases/{lease.id}/move-out-notices/",
        transition_body(lease, "moveOutNotice", "submit"),
        409,
    )
    post(
        tenant,
        f"leases/{lease.id}/replacement-requests/",
        transition_body(lease, "replacement", "submit"),
        409,
    )
    lease.refresh_from_db()
    assert lease.status == "active" and lease.occupancy_status == "occupied"


@override_settings(
    PLANNING_GEMINI_API_KEY="test-only", PLANNING_GEMINI_MODEL="configured-model"
)
def test_gemini_request_uses_rest_schema_enum_types_and_safe_provider_url():
    value = {"filters": {}, "questions": [], "unresolved_requirements": []}

    def http(url, body, headers):
        assert (
            url
            == "https://generativelanguage.googleapis.com/v1beta/models/configured-model:generateContent"
        )
        config = body["generationConfig"]
        assert config["responseMimeType"] == "application/json"
        schema = config["responseSchema"]
        assert schema["type"] == "OBJECT"
        assert schema["properties"]["questions"]["type"] == "ARRAY"
        assert schema["properties"]["questions"]["items"]["type"] == "STRING"
        assert headers["x-goog-api-key"] == "test-only"
        return {"candidates": [{"content": {"parts": [{"text": json.dumps(value)}]}}]}

    with patch(
        "core_apps.features.services.planning_providers_parts.extract_criteria.post_json",
        http,
    ):
        assert (
            extract_criteria("Private text", "en", {"cities": [], "amenities": []}, {})
            == value
        )


def test_unknown_deposit_stays_unknown_and_explicit_zero_stays_zero():
    assert offer_money({"terms": {"price": "1000", "deposit": ""}}) == (100000, None)
    assert offer_money({"terms": {"price": "1000", "deposit": "none"}}) == (100000, 0)


@pytest.mark.django_db(transaction=True)
def test_postgres_concurrent_join_approvals_cannot_exceed_capacity(rental_participants):
    if connection.vendor != "postgresql":
        pytest.skip("Row-lock race requires PostgreSQL")
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import close_old_connections

    owner, tenant, member, prop, _ = rental_participants
    group = create_group(tenant, prop)
    HousingGroup.objects.filter(id=group["id"]).update(visibility="open")
    ids = [
        post(
            user,
            f"housing-groups/{group['id']}/join-requests/",
            command(group_revision=1),
            201,
        ).data["resource"]["id"]
        for user in (owner, member)
    ]
    barrier = Barrier(2)

    def approve(identifier):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            response = authenticated(tenant).post(
                API + f"group-join-requests/{identifier}/approve/",
                command(1),
                format="json",
            )
            return response.status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(approve, ids)) == [200, 409]
    assert (
        HousingGroup.objects.get(id=group["id"])
        .memberships.filter(status="active")
        .count()
        == 2
    )


@override_settings(PLANNING_ROUTES_API_KEY="test-only", PLANNING_MOCK_DISCOVERY=False)
@pytest.mark.django_db(transaction=True)
def test_route_http_occurs_after_database_transaction(rental_participants):
    _, tenant, _, prop, _ = rental_participants
    prop.latitude, prop.longitude = 30.04, 31.23
    prop.save()
    with patch("core_apps.features.tasks.process_commute_search.delay"):
        item = post(tenant, "commute-searches/", journey(prop), 201).data["resource"]

    def provider(origins, destination):
        assert connection.in_atomic_block is False
        return [{"duration_seconds": 60, "status": "ok"} for _ in origins]

    with patch("core_apps.features.services.commute_jobs.route_matrix", provider):
        run_commute(item["id"])
    assert CommuteSearch.objects.get(id=item["id"]).status == "succeeded"


@pytest.mark.django_db
def test_home_preview_is_private_bounded_and_capability_scoped(current_lease):
    owner, tenant, stranger, lease = current_lease
    lease.end_date = timezone.localdate() + timedelta(days=7)
    lease.save()
    group = create_group(tenant, lease.property)
    response = authenticated(tenant).get(API + "planning-home/")
    assert response.status_code == 200
    assert {x["id"] for x in response.data["entries"]} == {str(lease.id), group["id"]}
    assert authenticated(stranger).get(API + "planning-home/").data["entries"] == []
    assert (
        authenticated(tenant)
        .get(API + "planning-home/?workspace=owner")
        .data["entries"]
        == []
    )
    assert authenticated(owner).get(API + "planning-home/?workspace=owner").data[
        "entries"
    ][0]["id"] == str(lease.id)
    with override_settings(PLANNING_ENABLED_SERVICES=[]):
        assert all(
            x["kind"] != "group"
            for x in authenticated(tenant).get(API + "planning-home/").data["entries"]
        )
    assert (
        authenticated(tenant).get(API + "planning-home/?workspace=admin").status_code
        == 400
    )


@pytest.mark.django_db(transaction=True)
def test_reminders_and_event_delivery_deduplicate_and_recheck_access(current_lease):
    from core_apps.notifications.models import DeviceToken
    from core_apps.notifications.services.push_delivery import dispatch
    from core_apps.features.services.planning_notifications import (
        record_lease_reminders,
        deliver_planning_events,
    )

    owner, tenant, _, lease = current_lease
    for recipient in [owner, tenant]:
        DeviceToken.objects.create(
            user=recipient, token=f"synthetic-reminder-{recipient.pk}"
        )
    PlanningEvent.objects.all().delete()
    lease.end_date = timezone.localdate() + timedelta(days=7)
    lease.save()
    assert record_lease_reminders() == 2
    assert record_lease_reminders() == 0

    sent = []

    def push(**kwargs):
        assert connection.in_atomic_block is False
        assert "lease_id" in kwargs["data"]
        sent.append(kwargs["token"])
        return 1

    with patch(
        "core_apps.notifications.services.fcm_service.FCMService.send_push_to_device",
        push,
    ):
        assert deliver_planning_events() == 2
        assert deliver_planning_events() == 0
        assert sent == []
        assert dispatch() == 2
        assert dispatch() == 0
        assert len(sent) == 2
    assert PlanningEvent.objects.exclude(notification=None).count() == 2
    group = create_group(tenant, lease.property)
    event = PlanningEvent.objects.create(
        recipient=owner,
        event_key="removed-membership",
        destination={
            "action_type": "open_housing_group",
            "target_id": group["id"],
            "workspace": "tenant",
        },
    )
    with patch(
        "core_apps.notifications.services.fcm_service.FCMService.send_push_to_user"
    ) as provider:
        assert deliver_planning_events() == 0
        provider.assert_not_called()
    event.refresh_from_db()
    assert event.delivered_at and event.notification_id is None


@pytest.mark.django_db
def test_notification_retry_does_not_duplicate_in_app_record(current_lease):
    from core_apps.features.services.planning_notifications import (
        record_lease_reminders,
        deliver_planning_events,
    )

    from core_apps.notifications.models import DeviceToken, PushDelivery
    from core_apps.notifications.services.push_delivery import dispatch

    owner, tenant, _, lease = current_lease
    for recipient in [owner, tenant]:
        DeviceToken.objects.create(user=recipient, token=f"synthetic-{recipient.pk}")
    PlanningEvent.objects.all().delete()
    lease.end_date = timezone.localdate() + timedelta(days=7)
    lease.save()
    record_lease_reminders()
    with patch(
        "core_apps.notifications.services.fcm_service.FCMService.send_push_to_device",
        side_effect=OSError(),
    ):
        assert deliver_planning_events() == 2
        assert dispatch() == 0
    original = set(PlanningEvent.objects.values_list("notification_id", flat=True))
    assert len(original) == 2 and None not in original
    PushDelivery.objects.update(next_attempt_at=timezone.now() - timedelta(minutes=3))
    with patch(
        "core_apps.notifications.services.fcm_service.FCMService.send_push_to_device",
        return_value=1,
    ):
        assert deliver_planning_events() == 0
        assert dispatch() == 2
        assert dispatch() == 0
    assert (
        set(PlanningEvent.objects.values_list("notification_id", flat=True)) == original
    )


@override_settings(
    PLANNING_GEMINI_API_KEY="test-only",
    PLANNING_GEMINI_MODEL="configured-model",
    PLANNING_MOCK_DISCOVERY=False,
)
@pytest.mark.django_db
def test_assistant_comparison_keeps_selected_properties_and_rejects_private_context(
    rental_participants,
):
    _, tenant, _, prop, _ = rental_participants
    response = {"filters": {}, "questions": [], "unresolved_requirements": []}
    body = command(
        text="Compare these places",
        session_id="compare-session",
        language="en",
        retain_history=False,
        context={"property_ids": [str(prop.id)]},
    )
    with patch(
        "core_apps.features.planning_discovery_views_parts.tenant_assistant_turns.extract_criteria",
        return_value=response,
    ) as provider:
        item = post(tenant, "tenant-assistant/turns/", body, 201).data["resource"]
        assert item["grounded_property_ids"] == [str(prop.id)] and item["costs"] == []
        prop.status = "pending"
        prop.save()
        post(tenant, "tenant-assistant/turns/", {**body, **command()}, 404)
        assert provider.call_count == 1


@pytest.mark.django_db
def test_signed_renewal_survives_worker_order_and_applies_only_once(phase5_lease):
    from rest_framework.test import APIClient
    from core_apps.features.providers import sign_fake_webhook
    from core_apps.features.models import ChangeSigningSession
    from core_apps.features.services.legal_lifecycle import end_lease_if_due
    from core_apps.features.tasks import process_rental_changes

    owner, tenant, lease = phase5_lease
    today = timezone.localdate()
    lease.start_date, lease.end_date = today - timedelta(days=30), today
    lease.save()
    terms = {
        **lease.terms,
        "starts_on": str(today),
        "ends_on_exclusive": str(today + timedelta(days=60)),
        "handover_on": str(today),
        "billing_anchor_day": today.day,
    }
    body = command(
        lease_revision=lease.revision,
        reason="Continue this tenancy",
        effective_on=str(today),
        terms=terms,
        evidence_ids=[],
    )
    item = post(owner, f"leases/{lease.id}/renewals/", body, 201).data["resource"]
    assert (
        post(owner, f"leases/{lease.id}/renewals/", body, 201).data["resource"]["id"]
        == item["id"]
    )
    item = post(
        tenant,
        f"renewals/{item['id']}/respond/",
        command(item["revision"], action="accept"),
    ).data["resource"]
    item = post(
        owner,
        f"renewals/{item['id']}/submit-for-signature/",
        command(item["revision"], action="submit_for_signature"),
    ).data["resource"]
    for user in (owner, tenant):
        data = post(
            user,
            f"renewals/{item['id']}/signing-session/",
            command(
                item["revision"],
                document_id=item["document_id"],
                document_hash=item["document_hash"],
            ),
            201,
        ).data["resource"]
        session = ChangeSigningSession.objects.get(id=data["session_id"])
        event = {
            "type": "change-signature.completed",
            "provider_session_id": session.provider_session_id,
        }
        assert (
            APIClient()
            .post(
                API + "provider-webhooks/rental/",
                event,
                format="json",
                HTTP_X_RENTAL_SIGNATURE=sign_fake_webhook(event),
            )
            .status_code
            == 200
        )
    lease.refresh_from_db()
    end_lease_if_due(lease)
    assert process_rental_changes()["applied"] == 1
    renewal = RentalChange.objects.get(id=item["id"]).result_lease
    assert (
        renewal.start_date == lease.end_date
        and renewal.tenancy_root_id == lease.tenancy_root_id
    )
    assert renewal.occupancy_status == lease.occupancy_status
    before = renewal.billing_periods.count()
    assert before > 0 and process_rental_changes()["applied"] == 0
    assert renewal.billing_periods.count() == before
    assert Lease.objects.filter(tenancy_root_id=lease.tenancy_root_id).count() == 2


@pytest.mark.django_db
def test_renewal_flutter_optional_dates_are_normalized_and_start_is_authoritative(
    phase5_lease,
):
    owner, _, lease = phase5_lease
    terms = {
        **lease.terms,
        "starts_on": str(lease.end_date),
        "handover_on": str(lease.end_date),
        "ends_on_exclusive": str(lease.end_date + timedelta(days=31)),
        "billing_anchor_day": lease.end_date.day,
    }
    body = command(
        lease_revision=lease.revision,
        invoice_id="",
        requested_date="",
        effective_on="",
        reason="Renew with reviewed terms",
        method="",
        amount={"amount_minor": None, "currency": "", "exponent": 2},
        terms=terms,
        evidence_ids=[],
    )
    result = post(owner, f"leases/{lease.id}/renewals/", body, 201).data["resource"]
    saved = RentalChange.objects.get(id=result["id"])
    assert saved.effective_on == lease.end_date and saved.requested_date is None
    assert (
        post(owner, f"leases/{lease.id}/renewals/", body, 201).data["resource"]["id"]
        == result["id"]
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field,value",
    [
        ("effective_on", "invalid"),
        ("effective_on", "2026-01-01"),
        ("requested_date", []),
    ],
)
def test_invalid_renewal_dates_are_validation_errors(phase5_lease, field, value):
    owner, _, lease = phase5_lease
    terms = {
        **lease.terms,
        "starts_on": str(lease.end_date),
        "handover_on": str(lease.end_date),
        "ends_on_exclusive": str(lease.end_date + timedelta(days=31)),
    }
    post(
        owner,
        f"leases/{lease.id}/renewals/",
        command(lease_revision=lease.revision, terms=terms, **{field: value}),
        400,
    )
    assert not RentalChange.objects.filter(lease=lease).exists()


def test_matching_is_bilateral_unknowns_are_not_agreements_and_importance_weights():
    from types import SimpleNamespace
    from core_apps.features.services.lifestyle_matching import match_facts

    def profile(habit, preference, importance="flexible"):
        return SimpleNamespace(
            habits={"sleep": habit},
            preferences={"sleep": preference},
            importance={"sleep": importance},
            reason_categories=["sleep"],
            search_context={},
        )

    viewer = profile("early", "early", "important")
    candidate = profile("early", "unspecified")
    blocked, agreements, differences, facts = match_facts(viewer, candidate, ["sleep"])
    assert not blocked and facts == [{"category": "sleep", "kind": "unknown"}]
    assert agreements == 2 and differences == 0
    candidate = profile("early", "early")
    assert match_facts(viewer, candidate, ["sleep"])[3] == [
        {"category": "sleep", "kind": "agreement"}
    ]
    candidate.preferences["sleep"] = "late"
    candidate.importance["sleep"] = "deal_breaker"
    assert match_facts(viewer, candidate, ["sleep"])[0] is True
    candidate.reason_categories = []
    assert match_facts(viewer, candidate, ["sleep"])[3] == []


@pytest.mark.django_db
def test_discovery_opt_in_is_required_for_direct_connection_request(
    rental_participants,
):
    _, tenant, member, _, _ = rental_participants
    profile = post(
        member,
        "lifestyle-profile/",
        command(discoverable=True, habits={}, preferences={}, disclosed=[]),
    ).data["resource"]
    post(
        tenant,
        f"roommate-candidates/{profile['id']}/request/",
        command(decision="request", candidate_revision=1),
        403,
    )


@pytest.mark.django_db
def test_historical_report_backfill_uses_exact_old_baseline_revision(current_lease):
    from importlib import import_module
    from django.apps import apps

    _, tenant, _, lease = current_lease
    old = [{"id": "wall", "note": "Reviewed original"}]
    baseline = ConditionReport.objects.create(
        lease=lease,
        author=tenant,
        kind="move_in",
        status="final",
        inspected_on=timezone.localdate(),
        revision=4,
        content_revision=2,
        items=[{"id": "wall", "note": "Later text"}],
        versions=[{"revision": 2, "items": old}],
    )
    moveout = ConditionReport.objects.create(
        lease=lease,
        author=tenant,
        kind="move_out",
        inspected_on=timezone.localdate(),
        baseline=baseline,
        baseline_revision=2,
    )
    import_module(
        "core_apps.features.migrations.0016_planning_snapshot_backfill"
    ).backfill(apps, None)
    moveout.refresh_from_db()
    assert moveout.baseline_snapshot["items"] == old
    baseline.items[0]["note"] = "Changed again"
    baseline.save()
    moveout.refresh_from_db()
    assert moveout.baseline_snapshot["items"] == old
