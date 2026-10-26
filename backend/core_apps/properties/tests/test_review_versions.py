from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from django.db import close_old_connections, connection
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.admin_api.models import StaffProfile
from core_apps.admin_api.services.property_service_parts.get_admin_property_detail import (
    get_admin_property_detail,
)
from core_apps.admin_api.services.property_service_parts.get_admin_properties_queryset import (
    get_admin_property_metrics,
)
from core_apps.features.models import RentalAuditEvent
from core_apps.features.planning_models import PlanningEvent
from core_apps.properties.models import (
    Property,
    PropertyImage,
    PropertyModerationDecision,
)
from core_apps.properties.services import PropertyService
from core_apps.properties.services.moderation import decide, version, receipt
from core_apps.properties.services.public_access import public_properties
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.common.idempotency import IdempotencyConflict

pytestmark = pytest.mark.django_db


@pytest.fixture
def listing(user, apartment_type, cairo_governorate, cairo_city):
    return Property.objects.create(
        owner=user,
        title="Original submission",
        price=3000,
        property_type=apartment_type,
        governorate=cairo_governorate,
        city=cairo_city,
        district="Nasr City",
    )


def review(listing, reviewer, action="approve", **kw):
    listing.refresh_from_db()
    return decide(
        listing.id,
        reviewer=reviewer,
        action=action,
        expected_version=kw.pop("expected_version", version(listing)),
        request_key=kw.pop("request_key", str(uuid4())),
        reason=kw.pop("reason", "" if action == "approve" else "Correct the evidence"),
        **kw,
    )


@pytest.mark.parametrize("kind", ["price", "photo", "caption", "delete_photo"])
def test_changed_evidence_rejects_review_of_previous_version(listing, superuser, kind):
    image = PropertyImage.objects.create(
        property=listing, image="properties/original.jpg"
    )
    observed = get_admin_property_detail(listing.id, reviewer=superuser)
    if kind == "price":
        PropertyService.update_property(listing, {"price": 4000})
    elif kind == "photo":
        PropertyImage.objects.create(property=listing, image="properties/new.jpg")
    elif kind == "caption":
        image.name = "Corrected caption"
        image.save()
    else:
        image.delete()
    with pytest.raises(RentalConflict):
        review(listing, superuser, expected_version=observed["review_version"])
    assert not PropertyModerationDecision.objects.exists()
    assert not public_properties().filter(pk=listing.pk).exists()


def test_catalog_translation_does_not_change_reviewed_content(listing, superuser):
    observed = get_admin_property_detail(listing.id)["review_version"]
    listing.city.name = "القاهرة"
    listing.city.save()
    review(listing, superuser, expected_version=observed)
    assert public_properties().filter(pk=listing.pk).exists()


def test_decision_exact_replay_and_changed_payload_conflict(listing, superuser):
    observed = get_admin_property_detail(listing.id)["review_version"]
    args = {"expected_version": observed, "request_key": str(uuid4())}
    first = review(listing, superuser, **args)
    second = review(listing, superuser, **args)
    assert second[:2] == first[:2] and second[2]
    assert PropertyModerationDecision.objects.count() == 1
    assert (
        PlanningEvent.objects.filter(
            event_key__startswith="property.moderation:"
        ).count()
        == 1
    )
    with pytest.raises(IdempotencyConflict):
        review(listing, superuser, internal_note="changed", **args)


def test_rejection_correction_resubmission_preserves_history_and_private_note(
    listing, superuser, auth_client, another_user
):
    review(listing, superuser, "reject", internal_note="private investigation")
    listing.refresh_from_db()
    assert listing.status == "needs_revision"
    with pytest.raises(RentalConflict):
        review(listing, superuser)
    public = auth_client.get(f"/api/v1/properties/{listing.id}/").json()["data"]
    assert public["moderation"]["reason"] == "Correct the evidence"
    assert "private investigation" not in str(public)
    PropertyService.update_property(listing, {"description": "Corrected"})
    review(listing, superuser)
    assert PropertyModerationDecision.objects.count() == 2
    first = PropertyModerationDecision.objects.order_by("created_at").first()
    assert first.snapshot["description"] != "Corrected"
    auth_client.force_authenticate(user=another_user)
    other = auth_client.get(f"/api/v1/properties/{listing.id}/").json()["data"]
    assert other["moderation"] is None


def test_block_requires_independent_lift_even_after_edit(listing, superuser):
    review(listing, superuser, "block")
    PropertyService.update_property(listing, {"title": "Corrected"})
    listing.refresh_from_db()
    assert listing.moderation_blocked and listing.status == "hidden"
    with pytest.raises(RentalConflict):
        PropertyService.toggle_property_visibility(listing, False)
    with pytest.raises(RentalConflict):
        review(listing, superuser)
    review(listing, superuser, "unblock")
    assert not public_properties().filter(pk=listing.pk).exists()
    review(listing, superuser)
    assert public_properties().filter(pk=listing.pk).exists()


def test_current_role_owner_and_missing_version_are_rejected(listing, superuser, user):
    with pytest.raises(ValidationError):
        review(listing, superuser, expected_version=None)
    StaffProfile.objects.create(user=user, role_name="property_reviewer")
    with pytest.raises(PermissionDenied):
        review(listing, user)
    StaffProfile.objects.create(
        user=superuser, role_name="property_reviewer", is_active=False
    )
    superuser.is_superuser = False
    superuser.save(update_fields=["is_superuser"])
    with pytest.raises(PermissionDenied):
        review(listing, superuser)
    assert not PropertyModerationDecision.objects.exists()


def test_absence_fence_blocks_delayed_decision(listing, superuser):
    key = str(uuid4())
    assert receipt(superuser, listing.id, key)["status"] == "unknown"
    assert receipt(superuser, listing.id, key, close=True)["status"] == "absent_final"
    with pytest.raises(IdempotencyConflict):
        review(listing, superuser, request_key=key)
    assert not PropertyModerationDecision.objects.exists()


def test_metrics_use_decisions_and_do_not_invent_activity(listing, superuser):
    assert get_admin_property_metrics()["acceptedToday"] == 0
    review(listing, superuser)
    PropertyService.update_property(listing, {"description": "new review"})
    assert get_admin_property_metrics()["acceptedToday"] == 1
    assert get_admin_property_metrics()["pending"] == 1


def test_api_requires_version_and_retains_receipt(listing, superuser, api_client):
    api_client.force_authenticate(user=superuser)
    path = f"/api/v1/admin/properties/{listing.id}/"
    assert api_client.post(path + "approve/", {}, format="json").status_code == 400
    detail = api_client.get(path).json()["data"]
    key = str(uuid4())
    result = api_client.post(
        path + "approve/",
        {"expected_version": detail["review_version"]},
        format="json",
        HTTP_IDEMPOTENCY_KEY=key,
    )
    assert result.status_code == 200, result.data
    recovered = api_client.get(path + f"receipts/{key}/").json()["data"]
    assert recovered["status"] == "confirmed"
    assert recovered["receipt"]["decision_id"] == result.json()["data"]["decision_id"]


@pytest.mark.django_db(transaction=True)
def test_concurrent_reviewers_only_one_decision(listing, superuser, another_user):
    if connection.vendor != "postgresql":
        pytest.skip("Requires real row locks")
    StaffProfile.objects.create(user=another_user, role_name="property_reviewer")
    observed = get_admin_property_detail(listing.id)["review_version"]
    barrier = Barrier(2)

    def worker(actor):
        close_old_connections()
        barrier.wait()
        try:
            decide(
                listing.id,
                reviewer=actor,
                action="approve",
                expected_version=observed,
                request_key=str(uuid4()),
            )
            return "saved"
        except RentalConflict:
            return "changed"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, [superuser, another_user]))
    assert sorted(results) == ["changed", "saved"]
    assert PropertyModerationDecision.objects.count() == 1
    assert RentalAuditEvent.objects.filter(subject_id=listing.id).count() == 1


def test_owner_filters_distinguish_hidden_correction_and_block(
    listing, auth_client, superuser
):
    path = "/api/v1/properties/owned/"
    assert len(auth_client.get(path, {"status": "under_review"}).json()["data"]) == 1
    assert auth_client.get(path, {"status": "rejected"}).json()["data"] == []
    review(listing, superuser, "reject")
    corrected = auth_client.get(path, {"status": "rejected"}).json()["data"]
    assert len(corrected) == 1 and corrected[0]["moderation_reason"]
    review(listing, superuser, "block")
    assert auth_client.get(path, {"status": "hidden"}).json()["data"] == []
    assert len(auth_client.get(path, {"status": "blocked"}).json()["data"]) == 1


def test_old_review_notification_delivers_current_property_without_private_note(
    listing, superuser
):
    from core_apps.features.services.planning_notifications import (
        deliver_planning_events,
    )

    review(listing, superuser, "reject", internal_note="secret reviewer note")
    PropertyService.update_property(
        listing, {"description": "corrected since decision"}
    )
    deliver_planning_events(event_kinds=["property_review_changed"])
    event = PlanningEvent.objects.get(event_key__startswith="property.moderation:")
    assert event.notification_id
    assert event.notification.data["property_id"] == str(listing.id)
    assert event.notification.data["workspace"] == "owner"
    assert "secret reviewer note" not in str(event.notification.data)


def test_edit_and_review_preserve_existing_visit_identity(
    listing, superuser, another_user
):
    from datetime import time, timedelta
    from django.utils import timezone
    from core_apps.properties.models import PropertyVisit

    visit = PropertyVisit.objects.create(
        property=listing,
        tenant=another_user,
        status="confirmed",
        visit_date=timezone.localdate() + timedelta(days=1),
        visit_time=time(15),
    )
    review(listing, superuser)
    PropertyService.update_property(listing, {"price": 4500})
    visit.refresh_from_db()
    listing.refresh_from_db()
    assert visit.status == "confirmed" and visit.property_id == listing.pk
    assert listing.status == "under_review" and not listing.is_verified
    review(listing, superuser)
    visit.refresh_from_db()
    assert visit.status == "confirmed"


@pytest.mark.django_db(transaction=True)
def test_owner_edit_racing_decision_always_requires_review_of_edited_content(
    listing, superuser
):
    if connection.vendor != "postgresql":
        pytest.skip("Requires real row locks")
    observed = get_admin_property_detail(listing.id)["review_version"]
    barrier = Barrier(2)

    def edit():
        close_old_connections()
        try:
            barrier.wait()
            PropertyService.update_property(listing, {"description": "new evidence"})
        finally:
            close_old_connections()

    def approve():
        close_old_connections()
        try:
            barrier.wait()
            try:
                decide(
                    listing.id,
                    reviewer=superuser,
                    action="approve",
                    expected_version=observed,
                    request_key=str(uuid4()),
                )
            except RentalConflict:
                pass
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(edit), pool.submit(approve)]
        for job in jobs:
            job.result(timeout=15)
    listing.refresh_from_db()
    assert listing.description == "new evidence"
    assert listing.status == "under_review" and not listing.is_verified
