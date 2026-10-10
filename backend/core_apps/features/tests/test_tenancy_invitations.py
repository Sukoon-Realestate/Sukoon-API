import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import time, timedelta
from threading import Barrier

import pytest
from django.db import connection, connections
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.features.models import (
    IdempotencyRecord,
    Lease,
    RentInvoice,
    TenancyInvitation,
)
from core_apps.notifications.models import Notification
from core_apps.properties.models import (
    City,
    Governorate,
    Property,
    PropertyType,
    PropertyVisit,
)
from core_apps.users.models import User


@pytest.fixture
def participants(db):
    owner = User.objects.create_user(
        email="invitation-owner@example.com",
        password="pass",
        first_name="Owner",
        last_name="One",
        is_verified=True,
    )
    tenant = User.objects.create_user(
        email="invitation-tenant@example.com",
        password="pass",
        first_name="Tenant",
        last_name="One",
        is_verified=True,
    )
    stranger = User.objects.create_user(
        email="invitation-stranger@example.com",
        password="pass",
        first_name="Stranger",
        last_name="One",
        is_verified=True,
    )
    return owner, tenant, stranger


@pytest.fixture
def owned_property(participants):
    owner, tenant, _ = participants
    governorate = Governorate.objects.create(name="Invitation Cairo")
    city = City.objects.create(name="Invitation City", governorate=governorate)
    property_type = PropertyType.objects.create(
        name="Invitation Apartment", slug="invitation-apartment"
    )
    property_obj = Property.objects.create(
        owner=owner,
        title="Invitation home",
        price=5000,
        property_type=property_type,
        governorate=governorate,
        city=city,
        district="District",
        status=Property.Status.VERIFIED,
        is_verified=True,
    )
    PropertyVisit.objects.create(
        property=property_obj,
        tenant=tenant,
        visit_date=timezone.localdate() + timedelta(days=1),
        visit_time=time(12),
        status=PropertyVisit.Status.CONFIRMED,
    )
    return property_obj


def authenticated(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def create_payload(property_obj, tenant, **extra):
    return {
        "property_id": str(property_obj.id),
        "tenant_id": str(tenant.id),
        "request_key": str(uuid.uuid4()),
        **extra,
    }


def create_invitation(owner, tenant, property_obj, **extra):
    payload = create_payload(property_obj, tenant, **extra)
    response = authenticated(owner).post(
        "/api/v1/features/v1/tenancy-invitations/", payload, format="json"
    )
    return response, payload


@pytest.mark.django_db
def test_create_legacy_invitation_is_idempotent_and_notifies_once(
    participants, owned_property
):
    owner, tenant, _ = participants
    client = authenticated(owner)
    payload = create_payload(owned_property, tenant)

    first = client.post(
        "/api/v1/features/v1/tenancy-invitations/", payload, format="json"
    )
    replay = client.post(
        "/api/v1/features/v1/tenancy-invitations/", payload, format="json"
    )

    assert first.status_code == replay.status_code == 201
    assert first.data["id"] == replay.data["id"]
    assert first.data["status"] == "pending"
    assert first.data["offer_snapshot"] is None
    assert first.data["actions"] == {"can_respond": False}
    assert TenancyInvitation.objects.count() == 1
    notification = Notification.objects.get(
        user=tenant, notification_type="tenancy_invitation"
    )
    assert notification.data == {
        "workspace": "tenant",
        "action_label": "Review invitation",
        "action_type": "open_tenancy_invitation",
        "target_id": first.data["id"],
    }

    duplicate = client.post(
        "/api/v1/features/v1/tenancy-invitations/",
        {**payload, "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert duplicate.status_code == 409


@pytest.mark.django_db
def test_exact_offer_acceptance_picker_and_draft_consumption(
    participants, owned_property
):
    owner, tenant, _ = participants
    offer_id = str(uuid.uuid4())
    room_id = str(uuid.uuid4())
    bed_id = str(uuid.uuid4())
    owned_property.rental_inventory = {
        "schema_version": 1,
        "revision": 1,
        "mode": "partial",
        "rooms": [
            {
                "id": room_id,
                "name": "First room",
                "capacity": 2,
                "beds": [{"id": bed_id, "name": "First bed"}],
            }
        ],
        "offers": [
            {
                "id": offer_id,
                "revision": 7,
                "rental_scope": "bed",
                "name": "Bed offer",
                "room_ids": [room_id],
                "bed_id": bed_id,
                "availability": "available",
                "archived": False,
                "offer_link": "",
                "terms": {"price": "1500", "price_period": "monthly"},
            }
        ],
    }
    owned_property.save(update_fields=["rental_inventory"])
    created, _ = create_invitation(
        owner,
        tenant,
        owned_property,
        offer_id=offer_id,
        expected_offer_revision=7,
    )
    assert created.status_code == 201
    assert created.data["offer_snapshot"]["bed_name"] == "First bed"

    owner_response = authenticated(owner).post(
        f"/api/v1/features/v1/tenancy-invitations/{created.data['id']}/respond/",
        {"decision": "accepted", "revision": 1, "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert owner_response.status_code == 403

    response_key = str(uuid.uuid4())
    response_payload = {
        "decision": "accepted",
        "revision": 1,
        "request_key": response_key,
    }
    tenant_client = authenticated(tenant)
    accepted = tenant_client.post(
        f"/api/v1/features/v1/tenancy-invitations/{created.data['id']}/respond/",
        response_payload,
        format="json",
    )
    accepted_replay = tenant_client.post(
        f"/api/v1/features/v1/tenancy-invitations/{created.data['id']}/respond/",
        response_payload,
        format="json",
    )
    assert accepted.status_code == accepted_replay.status_code == 200
    assert accepted.data["revision"] == 2
    assert accepted.data["eligible_for_lease"] is True
    assert (
        Notification.objects.filter(
            user=owner, notification_type="tenancy_invitation_response"
        ).count()
        == 1
    )

    owner_client = authenticated(owner)
    picker = owner_client.get(
        f"/api/v1/features/v1/lease-tenants/?property_id={owned_property.id}&offer_id={offer_id}"
    )
    assert picker.status_code == 200
    assert picker.data["results"] == [
        {"id": str(tenant.id), "display_name": tenant.get_full_name}
    ]

    lease_payload = {
        "property_id": str(owned_property.id),
        "tenant_id": str(tenant.id),
        "offer_id": offer_id,
        "template_id": "eg-residential-v1",
        "template_version": "1",
        "start_date": str(timezone.localdate() + timedelta(days=3)),
        "end_date": str(timezone.localdate() + timedelta(days=33)),
        "rent": {"amount_minor": 150000, "currency": "EGP", "exponent": 2},
        "request_key": str(uuid.uuid4()),
    }
    lease_response = owner_client.post(
        "/api/v1/features/v1/leases/", lease_payload, format="json"
    )
    lease_replay = owner_client.post(
        "/api/v1/features/v1/leases/", lease_payload, format="json"
    )
    assert lease_response.status_code == lease_replay.status_code == 201
    invitation = TenancyInvitation.objects.get(id=created.data["id"])
    assert invitation.lease_id == Lease.objects.get(id=lease_response.data["id"]).pk

    consumed_picker = owner_client.get(
        f"/api/v1/features/v1/lease-tenants/?property_id={owned_property.id}&offer_id={offer_id}"
    )
    assert consumed_picker.data["results"] == []


@pytest.mark.django_db
def test_expired_and_changed_invitations_cannot_be_accepted(
    participants, owned_property
):
    owner, tenant, _ = participants
    created, _ = create_invitation(owner, tenant, owned_property)
    invitation = TenancyInvitation.objects.get(id=created.data["id"])
    invitation.expires_at = timezone.now() - timedelta(seconds=1)
    invitation.save(update_fields=["expires_at"])

    expired = authenticated(tenant).post(
        f"/api/v1/features/v1/tenancy-invitations/{invitation.id}/respond/",
        {"decision": "accepted", "revision": 1, "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert expired.status_code == 409
    invitation.refresh_from_db()
    assert invitation.status == TenancyInvitation.Status.EXPIRED


@pytest.mark.django_db
def test_participant_privacy_and_rejected_invitation_not_in_picker(
    participants, owned_property
):
    owner, tenant, stranger = participants
    created, _ = create_invitation(owner, tenant, owned_property)
    detail_url = f"/api/v1/features/v1/tenancy-invitations/{created.data['id']}/"
    assert authenticated(stranger).get(detail_url).status_code == 404

    rejected = authenticated(tenant).post(
        f"{detail_url}respond/",
        {"decision": "rejected", "revision": 1, "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert rejected.status_code == 200
    picker = authenticated(owner).get(
        f"/api/v1/features/v1/lease-tenants/?property_id={owned_property.id}"
    )
    assert picker.data["results"] == []


@pytest.mark.django_db
def test_source_relationship_and_offer_revision_are_enforced(
    participants, owned_property
):
    owner, tenant, stranger = participants
    no_source = authenticated(owner).post(
        "/api/v1/features/v1/tenancy-invitations/",
        create_payload(owned_property, stranger),
        format="json",
    )
    assert no_source.status_code == 403

    offer_id = str(uuid.uuid4())
    owned_property.rental_inventory = {
        "schema_version": 1,
        "revision": 1,
        "mode": "whole",
        "rooms": [],
        "offers": [
            {
                "id": offer_id,
                "revision": 3,
                "rental_scope": "entire_property",
                "name": "Whole home",
                "room_ids": [],
                "availability": "available",
                "archived": False,
                "terms": {"price": "5000", "price_period": "monthly"},
            }
        ],
    }
    owned_property.save(update_fields=["rental_inventory"])
    stale, _ = create_invitation(
        owner,
        tenant,
        owned_property,
        offer_id=offer_id,
        expected_offer_revision=2,
    )
    assert stale.status_code == 409


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("scope", "room_count", "with_bed"),
    [
        ("entire_property", 0, False),
        ("room", 1, False),
        ("room_group", 2, False),
        ("bed", 1, True),
    ],
)
def test_all_supported_offer_scopes_are_snapshotted(
    participants, owned_property, scope, room_count, with_bed
):
    owner, tenant, _ = participants
    offer_id = str(uuid.uuid4())
    rooms = []
    for index in range(room_count):
        room_id = str(uuid.uuid4())
        room = {
            "id": room_id,
            "name": f"Room {index + 1}",
            "capacity": 2,
            "bathroom_access": ["shared"],
            "beds": [],
        }
        if with_bed:
            room["beds"] = [{"id": str(uuid.uuid4()), "name": "Bed 1"}]
        rooms.append(room)
    offer = {
        "id": offer_id,
        "revision": 1,
        "rental_scope": scope,
        "name": f"{scope} offer",
        "room_ids": [room["id"] for room in rooms],
        "availability": "available",
        "archived": False,
        "terms": {"price": "2000", "price_period": "monthly"},
    }
    if with_bed:
        offer["bed_id"] = rooms[0]["beds"][0]["id"]
    owned_property.rental_inventory = {
        "schema_version": 1,
        "revision": 1,
        "mode": "whole" if scope == "entire_property" else "partial",
        "rooms": rooms,
        "offers": [offer],
    }
    owned_property.save(update_fields=["rental_inventory"])

    response, _ = create_invitation(
        owner,
        tenant,
        owned_property,
        offer_id=offer_id,
        expected_offer_revision=1,
    )

    assert response.status_code == 201
    assert response.data["offer_snapshot"]["rental_scope"] == scope
    assert response.data["offer_snapshot"]["room_ids"] == offer["room_ids"]
    if with_bed:
        assert response.data["offer_snapshot"]["bed_name"] == "Bed 1"


@pytest.mark.django_db
def test_changed_offer_terms_revoke_before_acceptance(participants, owned_property):
    owner, tenant, _ = participants
    offer_id = str(uuid.uuid4())
    offer = {
        "id": offer_id,
        "revision": 1,
        "rental_scope": "entire_property",
        "name": "Whole home",
        "room_ids": [],
        "availability": "available",
        "archived": False,
        "terms": {"price": "5000", "price_period": "monthly"},
    }
    owned_property.rental_inventory = {
        "schema_version": 1,
        "revision": 1,
        "mode": "whole",
        "rooms": [],
        "offers": [offer],
    }
    owned_property.save(update_fields=["rental_inventory"])
    created, _ = create_invitation(
        owner,
        tenant,
        owned_property,
        offer_id=offer_id,
        expected_offer_revision=1,
    )
    owned_property.rental_inventory["offers"][0]["terms"]["price"] = "6000"
    owned_property.save(update_fields=["rental_inventory"])

    response = authenticated(tenant).post(
        f"/api/v1/features/v1/tenancy-invitations/{created.data['id']}/respond/",
        {"decision": "accepted", "revision": 1, "request_key": str(uuid.uuid4())},
        format="json",
    )

    assert response.status_code == 409
    invitation = TenancyInvitation.objects.get(id=created.data["id"])
    assert invitation.status == TenancyInvitation.Status.REVOKED


@pytest.mark.django_db
def test_list_is_workspace_scoped_and_empty_page_shape(participants, owned_property):
    owner, tenant, stranger = participants
    created, _ = create_invitation(owner, tenant, owned_property)

    tenant_list = authenticated(tenant).get(
        "/api/v1/features/v1/tenancy-invitations/?workspace=tenant"
    )
    assert tenant_list.status_code == 200
    assert tenant_list.data["count"] == 1
    assert tenant_list.data["results"][0]["id"] == created.data["id"]
    assert tenant_list.data["results"][0]["actions"] == {"can_respond": True}

    empty = authenticated(stranger).get(
        "/api/v1/features/v1/tenancy-invitations/?workspace=tenant"
    )
    assert empty.data == {
        "results": [],
        "count": 0,
        "per_page": 20,
        "total_pages": 1,
        "next": None,
        "previous": None,
    }


@pytest.mark.django_db
def test_offer_conflicts_use_arabic_message_when_requested(
    participants, owned_property
):
    owner, tenant, _ = participants
    offer_id = str(uuid.uuid4())
    owned_property.rental_inventory = {
        "schema_version": 1,
        "revision": 1,
        "mode": "whole",
        "rooms": [],
        "offers": [
            {
                "id": offer_id,
                "revision": 4,
                "rental_scope": "entire_property",
                "name": "Whole home",
                "room_ids": [],
                "availability": "available",
                "archived": False,
                "terms": {"price": "5000", "price_period": "monthly"},
            }
        ],
    }
    owned_property.save(update_fields=["rental_inventory"])

    response = authenticated(owner).post(
        "/api/v1/features/v1/tenancy-invitations/",
        create_payload(
            owned_property,
            tenant,
            offer_id=offer_id,
            expected_offer_revision=3,
        ),
        format="json",
        HTTP_ACCEPT_LANGUAGE="ar",
    )

    assert response.status_code == 409
    assert "قديمة" in response.json()["message"]


@pytest.mark.django_db
def test_cancelled_draft_requires_and_allows_a_fresh_invitation(
    participants, owned_property
):
    owner, tenant, _ = participants
    created, _ = create_invitation(owner, tenant, owned_property)
    accepted = authenticated(tenant).post(
        f"/api/v1/features/v1/tenancy-invitations/{created.data['id']}/respond/",
        {"decision": "accepted", "revision": 1, "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert accepted.status_code == 200
    owner_client = authenticated(owner)
    draft = owner_client.post(
        "/api/v1/features/v1/leases/",
        {
            "property_id": str(owned_property.id),
            "tenant_id": str(tenant.id),
            "template_id": "eg-residential-v1",
            "template_version": "1",
            "start_date": str(timezone.localdate() + timedelta(days=3)),
            "end_date": str(timezone.localdate() + timedelta(days=33)),
            "rent": {"amount_minor": 500000, "currency": "EGP", "exponent": 2},
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert draft.status_code == 201
    cancelled = owner_client.post(
        f"/api/v1/features/v1/leases/{draft.data['id']}/cancel/",
        {"revision": 1, "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert cancelled.status_code == 200

    fresh, _ = create_invitation(owner, tenant, owned_property)
    assert fresh.status_code == 201
    old_invitation = TenancyInvitation.objects.get(id=created.data["id"])
    assert old_invitation.lease_id is not None


def followup_lease_payload(property_obj, tenant):
    return {
        "property_id": str(property_obj.id),
        "tenant_id": str(tenant.id),
        "template_id": "eg-residential-v1",
        "template_version": "1",
        "start_date": str(timezone.localdate() + timedelta(days=1)),
        "end_date": str(timezone.localdate() + timedelta(days=182)),
        "rent": {"amount_minor": 6000000000, "currency": "EGP", "exponent": 2},
        "request_key": str(uuid.uuid4()),
    }


@pytest.mark.django_db
@pytest.mark.parametrize("language", ["en", "ar"])
@pytest.mark.parametrize("inventory", [{}, {"offers": []}])
def test_followup_legacy_round_trip(participants, owned_property, language, inventory):
    owner, tenant, stranger = participants
    owned_property.rental_inventory = inventory
    owned_property.save(update_fields=["rental_inventory"])
    owner_client = authenticated(owner)
    owner_client.defaults["HTTP_ACCEPT_LANGUAGE"] = language
    payload = create_payload(owned_property, tenant)
    created = owner_client.post(
        "/api/v1/features/v1/tenancy-invitations/", payload, format="json"
    )
    assert created.status_code == 201
    data = created.json()["data"]
    assert data["status"] == "pending"
    assert data["revision"] == 1
    assert data["expires_at"]
    assert data["offer_id"] in (None, "")
    assert data["offer_snapshot"] is None
    assert data["eligible_for_lease"] is False
    detail = f"/api/v1/features/v1/tenancy-invitations/{data['id']}/"
    picker = f"/api/v1/features/v1/lease-tenants/?property_id={owned_property.id}"
    assert owner_client.get(picker).json()["data"]["results"] == []
    answer = {"decision": "accepted", "revision": 1, "request_key": str(uuid.uuid4())}
    assert (
        authenticated(stranger)
        .post(detail + "respond/", answer, format="json")
        .status_code
        == 404
    )
    assert (
        owner_client.post(detail + "respond/", answer, format="json").status_code == 403
    )
    tenant_client = authenticated(tenant)
    tenant_client.defaults["HTTP_ACCEPT_LANGUAGE"] = language
    accepted = tenant_client.post(detail + "respond/", answer, format="json")
    assert accepted.status_code == 200
    assert accepted.json()["data"]["accepted_at"]
    assert accepted.json()["data"]["revision"] == 2
    assert accepted.json()["data"]["eligible_for_lease"] is True
    assert (
        tenant_client.post(detail + "respond/", answer, format="json").json()
        == accepted.json()
    )
    assert (
        tenant_client.post(
            detail + "respond/", {**answer, "decision": "rejected"}, format="json"
        ).status_code
        == 409
    )
    assert (
        tenant_client.post(
            detail + "respond/",
            {**answer, "request_key": str(uuid.uuid4())},
            format="json",
        ).status_code
        == 409
    )
    assert owner_client.get(picker).json()["data"]["results"][0]["id"] == str(tenant.id)
    lease_payload = followup_lease_payload(owned_property, tenant)
    draft = owner_client.post(
        "/api/v1/features/v1/leases/", lease_payload, format="json"
    )
    assert draft.status_code == 201
    assert (
        owner_client.post(
            "/api/v1/features/v1/leases/", lease_payload, format="json"
        ).json()
        == draft.json()
    )
    lease = Lease.objects.get(id=draft.json()["data"]["id"])
    assert lease.status == "draft"
    assert lease.rent_amount_minor == 6000000000
    assert TenancyInvitation.objects.get(id=data["id"]).lease_id == lease.pk
    assert owner_client.get(picker).json()["data"]["results"] == []
    assert (
        owner_client.post(
            f"/api/v1/features/v1/leases/{lease.id}/cancel/",
            {"revision": lease.revision, "request_key": str(uuid.uuid4())},
            format="json",
        ).status_code
        == 200
    )
    assert tenant_client.get(detail).json()["data"]["eligible_for_lease"] is False
    assert TenancyInvitation.objects.get(id=data["id"]).lease_id == lease.pk
    owned_property.refresh_from_db()
    assert owned_property.rental_inventory == inventory
    assert not RentInvoice.objects.exists()
    assert (
        Notification.objects.filter(notification_type="tenancy_invitation").count() == 1
    )
    assert (
        Notification.objects.filter(
            notification_type="tenancy_invitation_response"
        ).count()
        == 1
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "inventory,extra",
    [
        ({"schema_version": 2, "offers": []}, {}),
        ({"schema_version": 1, "offers": []}, {}),
        ({"offers": [{"id": "unknown"}]}, {}),
        ({"offers": []}, {"offer_id": "unexpected"}),
        ({"offers": []}, {"expected_offer_revision": 1}),
    ],
)
def test_empty_legacy_compatibility_does_not_bypass_offer_validation(
    participants, owned_property, inventory, extra
):
    owner, tenant, _ = participants
    owned_property.rental_inventory = inventory
    owned_property.save(update_fields=["rental_inventory"])
    response, _ = create_invitation(owner, tenant, owned_property, **extra)
    assert response.status_code == 400
    assert response.json()["message"]
    assert not TenancyInvitation.objects.exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("operation", ["create", "respond", "draft"])
def test_concurrent_invitation_mutations_have_one_winner(
    participants, owned_property, operation, monkeypatch
):
    if connection.vendor != "postgresql":
        pytest.skip("Row-lock concurrency requires PostgreSQL")
    monkeypatch.setattr(
        "core_apps.features.services.tenancy_invitations.FCMService.send_push_to_user",
        lambda **kwargs: None,
    )
    owner, tenant, _ = participants
    actor = owner
    url = "/api/v1/features/v1/tenancy-invitations/"
    payload = create_payload(owned_property, tenant)
    if operation != "create":
        created, _ = create_invitation(owner, tenant, owned_property)
        assert created.status_code == 201
        url += f"{created.data['id']}/respond/"
        payload = {"decision": "accepted", "revision": 1}
        actor = tenant
        if operation == "draft":
            accepted = authenticated(tenant).post(
                url, {**payload, "request_key": str(uuid.uuid4())}, format="json"
            )
            assert accepted.status_code == 200
            actor = owner
            url = "/api/v1/features/v1/leases/"
            payload = followup_lease_payload(owned_property, tenant)
    barrier = Barrier(2)

    def submit():
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SET lock_timeout = '5s'")
            client = authenticated(actor)
            barrier.wait(timeout=10)
            return client.post(
                url, {**payload, "request_key": str(uuid.uuid4())}, format="json"
            ).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(submit) for _ in range(2)]
        statuses = sorted(future.result(timeout=20) for future in futures)
    assert statuses == [200 if operation == "respond" else 201, 409]
    assert TenancyInvitation.objects.count() == 1
    assert (
        Notification.objects.filter(notification_type="tenancy_invitation").count() == 1
    )
    if operation != "create":
        assert (
            Notification.objects.filter(
                notification_type="tenancy_invitation_response"
            ).count()
            == 1
        )
    if operation == "draft":
        assert Lease.objects.count() == 1
        assert TenancyInvitation.objects.get().lease_id == Lease.objects.get().pk
    assert not RentInvoice.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("language", ["en", "ar"])
@pytest.mark.parametrize(
    "state",
    ["missing", "pending", "rejected", "expired", "revoked", "consumed", "unavailable"],
)
def test_followup_ineligible_draft_is_json_conflict(
    participants, owned_property, language, state
):
    owner, tenant, _ = participants
    client = authenticated(owner)
    client.defaults["HTTP_ACCEPT_LANGUAGE"] = language
    if state != "missing":
        created, _ = create_invitation(owner, tenant, owned_property)
        assert created.status_code == 201
        invitation = TenancyInvitation.objects.get(id=created.data["id"])
        invitation.status = (
            state if state in {"pending", "rejected", "revoked"} else "accepted"
        )
        if state == "expired":
            invitation.expires_at = timezone.now() - timedelta(seconds=1)
        invitation.save()
        if state == "consumed":
            draft = client.post(
                "/api/v1/features/v1/leases/",
                followup_lease_payload(owned_property, tenant),
                format="json",
            )
            assert draft.status_code == 201
            # Cancellation removes allocation conflict but must not restore consent.
            Lease.objects.filter(id=draft.data["id"]).update(
                status=Lease.Status.CANCELLED
            )
        if state == "unavailable":
            assert client.get(
                f"/api/v1/features/v1/lease-tenants/?property_id={owned_property.id}"
            ).data["results"]
            owned_property.is_verified = False
            owned_property.save(update_fields=["is_verified"])
    before = (Lease.objects.count(), IdempotencyRecord.objects.count())
    payload = followup_lease_payload(owned_property, tenant)
    for _ in range(2):
        response = client.post("/api/v1/features/v1/leases/", payload, format="json")
        assert response.status_code == 409
        assert response["Content-Type"].startswith("application/json")
        message = response.json()["message"]
        assert ("مؤهلاً" if language == "ar" else "no longer eligible") in message
    assert (Lease.objects.count(), IdempotencyRecord.objects.count()) == before
    assert not RentInvoice.objects.exists()
