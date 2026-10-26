"""Tenant edits, owner decisions, history, exact destinations and idempotency."""

from copy import deepcopy
import pytest
from core_apps.features.planning_models import (
    HousingOffer,
    HousingRequestChange,
    PlanningEvent,
)
from core_apps.features.services.planning_parts.selection_payload import (
    selection_payload,
)
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from core_apps.features.services.housing_request_notifications import notification_copy
from .test_funded_settlement import command
from .test_planning_cycles import API, configured_planning_offer, criteria_for, post
from .test_rental_phase2 import authenticated, rental_participants
from .test_housing_offer_eligibility import another_property
from core_apps.features.services.request_counts import pending_request_counts

pytestmark = pytest.mark.django_db


@pytest.fixture
def cycle(rental_participants):
    owner, tenant, other, prop, offer_id = rental_participants
    criteria = criteria_for(prop)
    parent = post(
        tenant,
        "housing-requests/",
        command(action="publish", title="My home", criteria=criteria),
        201,
    ).data["resource"]
    _, selected = resolve_offer_snapshot(prop, offer_id, 2)
    body = command(
        request_id=parent["id"],
        request_revision=parent["revision"],
        selection=selection_payload(selected),
    )
    offer = post(owner, f'housing-requests/{parent["id"]}/offers/', body, 201).data[
        "resource"
    ]
    return owner, tenant, other, parent, offer, criteria, body


def edit(cycle, **changes):
    owner, tenant, _, parent, _, criteria, _ = cycle
    body = command(
        parent["revision"],
        action="edit",
        title="My home",
        criteria={**criteria, **changes},
    )
    return (
        post(tenant, f'housing-requests/{parent["id"]}/edit/', body).data["resource"],
        body,
    )


def read(offer, user):
    response = authenticated(user).get(API + f'housing-offers/{offer["id"]}/')
    assert response.status_code == 200, response.data
    return response.data


@pytest.mark.parametrize(
    "changes, field, label",
    [
        ({"area_note": "Near campus"}, "area_note", "Near campus"),
        (
            {"budget_max": {"amount_minor": 3000000, "currency": "EGP", "exponent": 2}},
            "budget_max",
            "30000",
        ),
    ],
)
def test_compatible_edit_requires_owner_confirmation_and_preserves_terms(
    cycle, changes, field, label
):
    owner, tenant, _, parent, offer, _, _ = cycle
    updated, body = edit(cycle, **changes)
    stale = read(offer, owner)
    assert stale["status"] == "pending_reconfirm"
    assert stale["allowed_actions"] == ["withdraw", "replace", "reconfirm"]
    assert stale["request_changes"][0]["field"] == field
    assert "review" not in read(offer, tenant)["allowed_actions"]
    decision = command(
        stale["revision"],
        decision="reconfirm",
        request_revision=updated["revision"],
        request_content_revision=updated["content_revision"],
    )
    url = f'housing-offers/{offer["id"]}/reconfirm/'
    response = post(owner, url, decision)
    current = response.data["resource"]
    assert current["status"] == "sent"
    assert current["selection"] == offer["selection"]
    assert current["request_changes"] == []
    assert post(owner, url, decision).data == response.data
    assert HousingRequestChange.objects.count() == 1
    notice = PlanningEvent.objects.get(
        destination__event_kind="housing_request_changed"
    )
    assert notice.recipient == owner
    assert notice.destination["workspace"] == "owner"
    assert notice.destination["target_id"] == parent["id"]
    assert label in notification_copy(notice)["body"]
    confirmed = PlanningEvent.objects.get(
        destination__event_kind="housing_offer_reconfirmed"
    )
    assert confirmed.recipient == tenant
    assert confirmed.destination["housing_offer_id"] == offer["id"]


@pytest.mark.parametrize(
    "change",
    [
        {"rental_scope": "room"},
        {"people": 20},
        {"budget_max": {"amount_minor": 100001, "currency": "EGP", "exponent": 2}},
    ],
)
def test_incompatible_offer_is_history_and_cannot_be_reconfirmed(cycle, change):
    owner, tenant, _, parent, offer, _, _ = cycle
    updated, _ = edit(cycle, **change)
    item = read(offer, owner)
    assert item["status"] == "incompatible"
    assert item["review_reasons"]
    assert "reconfirm" not in item["allowed_actions"]
    for scope, count in [("current", 0), ("pending", 0), ("history", 1)]:
        result = authenticated(tenant).get(
            API + f'housing-requests/{parent["id"]}/offers/', {"scope": scope}
        )
        assert result.data["count"] == count
    post(
        owner,
        f'housing-offers/{offer["id"]}/reconfirm/',
        command(
            item["revision"],
            decision="reconfirm",
            request_revision=updated["revision"],
            request_content_revision=updated["content_revision"],
        ),
        403,
    )


def test_no_op_pause_resume_and_terminal_offers_do_not_require_reconfirmation(cycle):
    owner, tenant, _, parent, offer, _, _ = cycle
    updated, _ = edit(cycle)
    assert updated["content_revision"] == parent["content_revision"]
    assert not HousingRequestChange.objects.exists()
    assert not PlanningEvent.objects.filter(
        destination__event_kind="housing_request_changed"
    ).exists()
    paused = post(
        tenant,
        f'housing-requests/{parent["id"]}/pause/',
        command(updated["revision"], action="pause"),
    ).data["resource"]
    post(
        tenant,
        f'housing-requests/{parent["id"]}/publish/',
        command(paused["revision"], action="publish"),
    )
    assert read(offer, owner)["status"] == "sent"


def test_replacement_is_atomic_and_only_replaces_its_owned_offer(cycle):
    owner, tenant, other, parent, offer, _, original = cycle
    updated, _ = edit(cycle, area_note="New area")
    old = read(offer, owner)
    body = {
        **command(),
        **{
            k: v
            for k, v in original.items()
            if k not in {"request_key", "expected_revision"}
        },
        "request_revision": updated["revision"],
        "replaces_offer_id": offer["id"],
        "replaced_offer_revision": old["revision"],
    }
    broken = deepcopy(body)
    broken["selection"]["offer_revision"] += 1
    result = authenticated(owner).post(
        API + f'housing-requests/{parent["id"]}/offers/', broken, format="json"
    )
    assert result.status_code == 409
    assert read(offer, owner)["status"] == "pending_reconfirm"
    replacement = post(
        owner, f'housing-requests/{parent["id"]}/offers/', body, 201
    ).data["resource"]
    assert replacement["replaces_offer_id"] == offer["id"]
    assert read(offer, owner)["status"] == "superseded"
    assert read(offer, owner)["allowed_actions"] == []
    assert (
        post(owner, f'housing-requests/{parent["id"]}/offers/', body, 201).data[
            "resource"
        ]["id"]
        == replacement["id"]
    )
    assert HousingOffer.objects.count() == 2


def test_stale_confirm_foreign_history_and_role_specific_withdrawal(cycle):
    owner, tenant, other, parent, offer, criteria, _ = cycle
    updated, _ = edit(cycle, area_note="First")
    old = read(offer, owner)
    next_cycle = (
        *cycle[:3],
        updated,
        offer,
        {**criteria, "area_note": "First"},
        cycle[-1],
    )
    edit(next_cycle, area_note="Second")
    post(
        owner,
        f'housing-offers/{offer["id"]}/reconfirm/',
        command(
            old["revision"],
            decision="reconfirm",
            request_revision=updated["revision"],
            request_content_revision=updated["content_revision"],
        ),
        409,
    )
    assert (
        authenticated(other)
        .get(API + f'housing-requests/{parent["id"]}/changes/')
        .status_code
        == 404
    )
    current = read(offer, owner)
    post(
        tenant,
        f'housing-offers/{offer["id"]}/withdraw/',
        command(current["revision"], decision="withdraw"),
        403,
    )
    post(
        owner,
        f'housing-offers/{offer["id"]}/withdraw/',
        command(current["revision"], decision="withdraw"),
    )
    assert read(offer, tenant)["status"] == "withdrawn"
    assert (
        authenticated(tenant)
        .get(API + f'housing-requests/{parent["id"]}/')
        .data["status"]
        == "published"
    )


def test_request_withdrawal_closes_offers_and_retires_selection_commands(cycle):
    owner, tenant, _, parent, offer, _, _ = cycle
    for action in ("shortlist", "select_to_proceed"):
        post(
            tenant,
            f'housing-offers/{offer["id"]}/{action}/',
            command(offer["revision"], decision=action),
            409,
        )
    post(
        tenant,
        f'housing-requests/{parent["id"]}/close/',
        command(parent["revision"], action="close"),
    )
    assert read(offer, owner)["status"] == "request_closed"
    assert read(offer, owner)["allowed_actions"] == []
    notice = PlanningEvent.objects.get(destination__event_kind="housing_request_status")
    assert notice.destination["workspace"] == "owner"
    assert "سحب المستأجر" in notification_copy(notice)["title"]


def test_each_owner_receives_one_change_even_with_multiple_offers(cycle):
    owner, tenant, other, parent, offer, _, original = cycle
    source = HousingOffer.objects.get(id=offer["id"]).property
    for recipient in (owner, other):
        prop = another_property(source, owner=recipient)
        _, selected = resolve_offer_snapshot(prop, original["selection"]["offer_id"], 2)
        post(
            recipient,
            f'housing-requests/{parent["id"]}/offers/',
            command(
                request_id=parent["id"],
                request_revision=parent["revision"],
                selection=selection_payload(selected),
            ),
            201,
        )
    updated, body = edit(cycle, area_note="New requirements")
    # Retrying the edit must not duplicate changes, outbox rows, or revision bumps.
    post(tenant, f'housing-requests/{parent["id"]}/edit/', body)
    events = PlanningEvent.objects.filter(
        destination__event_kind="housing_request_changed"
    )
    assert set(events.values_list("recipient_id", flat=True)) == {owner.pk, other.pk}
    assert events.count() == 2
    assert HousingRequestChange.objects.count() == 1
    assert pending_request_counts(owner, owner=True)["housing_offers"] == 2
    assert pending_request_counts(other, owner=True)["housing_offers"] == 1
    assert pending_request_counts(tenant)["housing_offers"] == 0
    current = read(offer, owner)
    post(
        owner,
        f'housing-offers/{offer["id"]}/withdraw/',
        command(current["revision"], decision="withdraw"),
    )
    assert pending_request_counts(owner, owner=True)["housing_offers"] == 1


@pytest.mark.parametrize("decision", ["withdraw", "decline"])
def test_content_changes_do_not_revive_terminal_offers(cycle, decision):
    owner, tenant, _, parent, offer, _, _ = cycle
    actor = owner if decision == "withdraw" else tenant
    post(
        actor,
        f'housing-offers/{offer["id"]}/{decision}/',
        command(offer["revision"], decision=decision),
    )
    previous = read(offer, owner)
    edit(cycle, area_note="Edited after response")
    current = read(offer, owner)
    assert current["status"] == previous["status"]
    assert current["revision"] == previous["revision"]
    assert current["allowed_actions"] == []
    assert not PlanningEvent.objects.filter(
        destination__event_kind="housing_request_changed"
    ).exists()


def test_live_inventory_change_cannot_be_reconfirmed_or_break_reads(cycle):
    owner, _, _, _, offer, _, _ = cycle
    updated, _ = edit(cycle, area_note="Please review")
    pending = read(offer, owner)
    prop = HousingOffer.objects.get(id=offer["id"]).property
    prop.rental_inventory["offers"][0]["revision"] += 1
    prop.save(update_fields=["rental_inventory"])
    current = read(offer, owner)
    assert current["status"] == "unavailable"
    assert "reconfirm" not in current["allowed_actions"]
    post(
        owner,
        f'housing-offers/{offer["id"]}/reconfirm/',
        command(
            pending["revision"],
            decision="reconfirm",
            request_revision=updated["revision"],
            request_content_revision=updated["content_revision"],
        ),
        403,
    )


def test_history_keeps_localized_before_after_and_normalizes_sets(cycle):
    from core_apps.features.services.housing_request_reviews import differences

    assert (
        differences(
            {"criteria": {"amenities": ["wifi", "elevator"]}},
            {"criteria": {"amenities": ["elevator", "wifi"]}},
        )
        == []
    )
    owner, tenant, _, parent, _, _, _ = cycle
    edit(cycle, rental_scope="room")
    history = authenticated(owner).get(
        API + f'housing-requests/{parent["id"]}/changes/', HTTP_ACCEPT_LANGUAGE="ar"
    )
    change = history.data["results"][0]["fields"][0]
    assert change["before_label"] == "عقار كامل"
    assert change["after_label"] == "غرفة"
    assert (
        authenticated(tenant)
        .get(API + f'housing-requests/{parent["id"]}/')
        .data["can_read_changes"]
    )


def test_change_delivery_reuses_notification_after_push_retry(cycle, monkeypatch):
    from core_apps.notifications.models import DeviceToken, PushDelivery
    from core_apps.notifications.services.push_delivery import dispatch
    from django.utils import timezone
    from datetime import timedelta
    from core_apps.features.services.planning_notifications import (
        deliver_planning_events,
    )
    from core_apps.notifications.services.fcm_service import FCMService

    edit(cycle, area_note="Delivery retry")
    DeviceToken.objects.create(user=cycle[0], token="synthetic-request-device")
    monkeypatch.setattr(
        FCMService,
        "send_push_to_device",
        staticmethod(
            lambda **kwargs: (_ for _ in ()).throw(RuntimeError("temporary outage"))
        ),
    )
    assert deliver_planning_events(event_kinds=["housing_request_changed"]) == 1
    assert dispatch() == 0

    event = PlanningEvent.objects.get(destination__event_kind="housing_request_changed")
    first_notification = event.notification_id
    assert first_notification and event.delivery_status == "push_queued"
    assert not event.provider_accepted_at
    PushDelivery.objects.filter(notification=event.notification).update(
        next_attempt_at=timezone.now() - timedelta(minutes=3)
    )
    monkeypatch.setattr(
        FCMService, "send_push_to_device", staticmethod(lambda **kwargs: True)
    )
    assert deliver_planning_events(event_kinds=["housing_request_changed"]) == 0
    assert dispatch() == 1
    event.refresh_from_db()
    assert event.notification_id == first_notification
    assert event.delivery_status == "provider_accepted"
    assert deliver_planning_events(event_kinds=["housing_request_changed"]) == 0


def test_migration_preserves_legacy_terms_without_inventing_stale_snapshots(cycle):
    from importlib import import_module
    from django.apps import apps

    owner, _, _, _, offer, _, _ = cycle
    current = HousingOffer.objects.get(id=offer["id"])
    original_selection = deepcopy(current.selection)
    current.status = "selected_to_proceed"
    current.reviewed_request_snapshot = {}
    current.save(update_fields=["status", "reviewed_request_snapshot"])
    stale = HousingOffer.objects.create(
        request=current.request,
        owner=owner,
        property=current.property,
        request_revision=0,
        selection=original_selection,
        rent_minor=current.rent_minor,
        deposit_minor=current.deposit_minor,
        price_period=current.price_period,
    )
    import_module(
        "core_apps.features.migrations.0072_housing_request_reviews"
    ).baseline_offers(apps, None)
    current.refresh_from_db()
    stale.refresh_from_db()
    assert current.selection == original_selection
    assert current.reviewed_request_snapshot["criteria"] == current.request.criteria
    assert read(offer, owner)["status"] == "sent"
    assert stale.reviewed_request_snapshot == {}
    assert stale.reviewed_content_revision == 0
    assert stale.review_state == "incompatible"
    assert not HousingRequestChange.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_edit_and_reconfirm_never_confirms_old_requirements(cycle):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import connections

    owner, tenant, _, parent, offer, criteria, _ = cycle
    updated, _ = edit(cycle, area_note="First revision")
    pending = read(offer, owner)
    gate = Barrier(2)

    def run(user, route, body):
        try:
            gate.wait(timeout=10)
            return (
                authenticated(user).post(API + route, body, format="json").status_code
            )
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        editing = pool.submit(
            run,
            tenant,
            f'housing-requests/{parent["id"]}/edit/',
            command(
                updated["revision"],
                action="edit",
                title="My home",
                criteria={**criteria, "area_note": "Latest revision"},
            ),
        )
        confirming = pool.submit(
            run,
            owner,
            f'housing-offers/{offer["id"]}/reconfirm/',
            command(
                pending["revision"],
                decision="reconfirm",
                request_revision=updated["revision"],
                request_content_revision=updated["content_revision"],
            ),
        )
        assert editing.result(timeout=30) == 200
        assert confirming.result(timeout=30) in {200, 409}
    result = read(offer, owner)
    assert result["status"] == "pending_reconfirm"
    assert result["request_changes"][-1]["after_label"] == "Latest revision"
