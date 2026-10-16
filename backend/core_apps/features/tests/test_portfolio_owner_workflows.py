"""Synthetic owner workflows: protection, recovery, exact previews and lineage."""

import hashlib
import io
import uuid
import pytest
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import PermissionDenied
from core_apps.properties.models import Property, ResidentialComplex, ResidentialMedia
from core_apps.properties.services.property import PropertyService
from core_apps.features.services.company import (
    portfolio,
    portfolio_changes as changes,
    portfolio_topology as topology,
    portfolio_media as media,
)
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.features.tests.test_company_housing import (
    company_setup,
    command,
    approved,
    rental_participants,
    policy,
    API,
)
from core_apps.features.tests.test_rental_phase2 import authenticated
from core_apps.features.services.company import bookings
from core_apps.features.company_serializers import ContainerBody
from core_apps.features.portfolio_serializers import (
    BulkPreviewBody,
    TopologyPreviewBody,
)
from core_apps.virtual_tours.models import PropertyVirtualTour
from core_apps.virtual_tours.policy import scope_policy
from core_apps.virtual_tours.errors import TourError

pytestmark = pytest.mark.django_db


def versions(props):
    return [{"id": str(p.id), "version": changes.unit_version(p)} for p in props]


def bulk(building, props, **extra):
    return command(
        expected_revision=building.revision,
        units=versions(props),
        changes={"is_furnished": True},
        inherit_fields=[],
        reset_overrides=False,
        reason="Synthetic owner review",
        **extra,
    )


def test_edit_asset_facts_private_fields_and_mode_validation(company_setup):
    owner, _, _, _, building, props, *_ = company_setup
    body = command(
        expected_revision=building.revision,
        kind="building",
        name=building.name,
        code=building.code,
        address=building.address,
        declared_units=2,
        floors=None,
        facts={
            "latitude": "30.000000",
            "longitude": "31.000000",
            "private_access": "Private synthetic instruction",
            "utilities": {"water": "Metered"},
            "unit_defaults": {"has_wifi": True},
        },
    )
    serializer = ContainerBody(data=body)
    assert serializer.is_valid(), serializer.errors
    result = changes.update_container(
        owner, "building", building.id, serializer.validated_data
    )
    assert result.private_access == body["facts"]["private_access"]
    assert result.unit_defaults == {"has_wifi": True}
    props[0].refresh_from_db()
    assert not props[0].has_wifi
    invalid = ContainerBody(data={**body, "declared_buildings": 1})
    assert not invalid.is_valid()
    with pytest.raises(RentalConflict):
        changes.update_container(
            owner, "building", building.id, serializer.validated_data
        )


def test_bulk_inheritance_preserves_explicit_values_and_tracks_resets(company_setup):
    owner, _, _, _, building, props, *_ = company_setup
    building.unit_defaults = {"has_wifi": True}
    building.save()
    data = bulk(building, props)
    data.update(changes={}, inherit_fields=["has_wifi"])
    preview = changes.preview_bulk(owner, "building", building.id, data)
    assert all(r["status"] == "unchanged" for r in preview.preview["rows"])
    data["reset_overrides"] = True
    preview = changes.preview_bulk(owner, "building", building.id, data)
    result = changes.apply_bulk(owner, preview.id, command(expected_revision=1))
    assert all(r["status"] == "updated" for r in result.results)
    prop = Property.objects.get(pk=props[0].pk)
    assert prop.has_wifi and prop.portfolio_inheritance["has_wifi"]["source_id"] == str(
        building.id
    )
    prop = PropertyService.update_property(prop, {"has_wifi": False})
    assert prop.portfolio_inheritance["has_wifi"] == {"mode": "override"}
    building.unit_defaults = {"has_wifi": False}
    building.save()
    prop.refresh_from_db()
    assert not prop.has_wifi
    other = Property.objects.get(pk=props[1].pk)
    assert other.has_wifi  # Parent defaults never rewrite children automatically.


def test_bulk_stale_unit_partial_results_and_idempotent_api(company_setup):
    owner, _, _, _, building, props, *_ = company_setup
    client = authenticated(owner)
    response = client.post(
        f"{API}residential-assets/building/{building.id}/bulk-edit/preview/",
        bulk(building, props),
        format="json",
    )
    assert response.status_code == 201, response.data
    identity = response.json()["data"]["resource"]["id"]
    PropertyService.update_property(
        props[0], {"description": "Concurrent owner correction"}
    )
    body = command(expected_revision=1)
    applied = client.post(f"{API}residential-changes/{identity}/", body, format="json")
    assert applied.status_code == 200, applied.data
    rows = applied.json()["data"]["resource"]["results"]
    assert sorted(r["status"] for r in rows) == ["failed", "updated"]
    assert (
        client.post(f"{API}residential-changes/{identity}/", body, format="json").data
        == applied.data
    )
    assert (
        client.post(
            f"{API}residential-changes/{identity}/",
            command(expected_revision=1),
            format="json",
        ).status_code
        == 409
    )


def test_bulk_and_topology_cannot_mutate_company_held_inventory(company_setup):
    owner, coordinator, _, _, building, props, *_ = company_setup
    item = approved(company_setup)
    bookings.hold_item(coordinator, item.id, command(expected_revision=item.revision))
    preview = changes.preview_bulk(
        owner, "building", building.id, bulk(building, props)
    )
    assert all(r["status"] == "blocked" for r in preview.preview["rows"])
    data = command(
        expected_revision=building.revision,
        operation="split_unit",
        units=versions(props[:1]),
        replacements=[
            {"unit_code": "A", "title": "A", "occupancy_capacity": 2},
            {"unit_code": "B", "title": "B", "occupancy_capacity": 2},
        ],
        reason="Synthetic split",
    )
    preview = topology.preview_topology(owner, "building", building.id, data)
    assert not preview.preview["allowed"]
    with pytest.raises(RentalConflict):
        topology.apply_topology(owner, preview.id, command(expected_revision=1))
    assert Property.objects.filter(building=building, retired_at=None).count() == 2


def test_split_preserves_history_and_new_ids_and_blocks_legacy_reactivation(
    company_setup,
):
    owner, _, _, _, building, props, *_ = company_setup
    original = props[0]
    data = command(
        expected_revision=building.revision,
        operation="split_unit",
        units=versions([original]),
        replacements=[
            {
                "unit_code": original.unit_code,
                "title": "Split A",
                "occupancy_capacity": 2,
            },
            {"unit_code": "103", "title": "Split B", "occupancy_capacity": None},
        ],
        reason="Synthetic physical subdivision",
    )
    preview = topology.preview_topology(owner, "building", building.id, data)
    result = topology.apply_topology(owner, preview.id, command(expected_revision=1))
    original.refresh_from_db()
    assert original.retired_at and original.status == "hidden"
    new = list(original.successors.all())
    assert len(new) == 2 and len({p.id for p in new} | {original.id}) == 3
    assert all(
        not p.is_verified and not p.is_ownership_verified and p.rental_inventory == {}
        for p in new
    )
    assert portfolio.units_for(building).count() == 3
    with pytest.raises(RentalConflict):
        PropertyService.toggle_property_visibility(original, False)
    with pytest.raises(RentalConflict):
        PropertyService.update_property(original, {"title": "Unsafe resurrection"})
    assert len(result.results) == 3
    # A retired predecessor is never a public listing, including direct links.
    from rest_framework.test import APIClient

    path = f"/api/v1/properties/{original.id}/"
    assert APIClient().get(path).status_code == 404
    assert authenticated(company_setup[1]).get(path).status_code == 404
    assert authenticated(owner).get(path).status_code == 200
    assert str(original.id) not in str(APIClient().get("/api/v1/properties/").json())


def test_merge_retains_both_originals(company_setup):
    owner, _, _, _, building, props, *_ = company_setup
    data = command(
        expected_revision=building.revision,
        operation="merge_units",
        units=versions(props),
        replacements=[{"unit_code": "M", "title": "Merged", "occupancy_capacity": 6}],
        reason="Synthetic merge",
    )
    preview = topology.preview_topology(owner, "building", building.id, data)
    result = topology.apply_topology(owner, preview.id, command(expected_revision=1))
    new = Property.objects.get(
        id=next(r["id"] for r in result.results if r["status"] == "created")
    )
    assert set(new.replaces.values_list("id", flat=True)) == {p.id for p in props}
    assert portfolio.units_for(building).count() == 1


def test_move_preserves_ids_and_requires_destination_authority(company_setup):
    owner, coordinator, _, _, building, props, *_ = company_setup
    target = ResidentialComplex.objects.create(
        manager=owner,
        name="Destination",
        code="D",
        address="Test",
        declared_standalone_units=2,
    )
    data = command(
        expected_revision=building.revision,
        operation="move_units",
        units=versions(props),
        replacements=[],
        target_kind="complex",
        target_id=str(target.id),
        target_revision=target.revision,
        reason="Synthetic move",
    )
    preview = topology.preview_topology(owner, "building", building.id, data)
    topology.apply_topology(owner, preview.id, command(expected_revision=1))
    assert set(target.standalone_units.values_list("id", flat=True)) == {
        p.id for p in props
    }
    assert all(p.building_id is None for p in target.standalone_units.all())
    assert (
        authenticated(coordinator)
        .get(f"{API}residential-changes/{preview.id}/")
        .status_code
        == 404
    )


def test_new_hold_after_preview_blocks_apply(company_setup):
    owner, coordinator, _, _, building, props, *_ = company_setup
    target = ResidentialComplex.objects.create(
        manager=owner, name="Target", code="T", address="Test", declared_buildings=1
    )
    data = command(
        expected_revision=building.revision,
        operation="move_building",
        units=[],
        replacements=[],
        target_kind="complex",
        target_id=str(target.id),
        target_revision=target.revision,
        reason="Synthetic move",
    )
    preview = topology.preview_topology(owner, "building", building.id, data)
    item = approved(company_setup)
    bookings.hold_item(coordinator, item.id, command(expected_revision=item.revision))
    with pytest.raises(RentalConflict):
        topology.apply_topology(owner, preview.id, command(expected_revision=1))
    building.refresh_from_db()
    assert building.complex_id is None


def test_media_intent_resume_digest_private_evidence_and_review(
    company_setup, settings, tmp_path
):
    owner, coordinator, _, _, building, *_ = company_setup
    settings.VIRTUAL_TOUR_PRIVATE_ROOT = str(tmp_path)
    image = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(image, "PNG")
    raw = image.getvalue()
    body = command(
        expected_revision=building.revision,
        purpose="authority",
        caption="Synthetic proof",
        representative=False,
        sha256=hashlib.sha256(raw).hexdigest(),
        byte_size=len(raw),
        content_type="image/png",
    )
    item = media.create_intent(owner, "building", building.id, body)
    assert media.media_for(owner, item.id).state == "pending"
    uploaded = media.upload(
        owner, item.id, SimpleUploadedFile("proof.png", raw, content_type="image/png")
    )
    assert uploaded.state == "ready"
    assert (
        media.upload(owner, item.id, SimpleUploadedFile("proof.png", raw)).id == item.id
    )
    assert ResidentialMedia.objects.filter(request_key=body["request_key"]).count() == 1
    assert (
        authenticated(owner).get(f"{API}residential-media/{item.id}/bytes/").status_code
        == 200
    )
    assert (
        authenticated(coordinator)
        .get(f"{API}residential-media/{item.id}/bytes/")
        .status_code
        == 403
    )
    with pytest.raises(PermissionDenied):
        media.review(
            owner,
            item.id,
            command(
                expected_revision=uploaded.revision,
                status="approved",
                reason="self review",
            ),
        )


def test_container_tours_reuse_canonical_records_and_do_not_expose_child_rooms(
    company_setup, settings
):
    owner, _, _, _, building, *_ = company_setup
    settings.VIRTUAL_TOUR_VIEWER_URL = "https://test.example/tours/"
    settings.VIRTUAL_TOUR_KINDS = {"panorama_360": {"read": True, "write": True}}
    ResidentialMedia.objects.create(
        owner=owner,
        building=building,
        purpose="photo",
        state="ready",
        request_key=uuid.uuid4(),
        sha256="a" * 64,
        byte_size=1,
        content_type="image/png",
    )
    client = authenticated(owner)
    response = client.post(
        f"/api/v1/residential-assets/building/{building.id}/virtual-tours/",
        {"kind": "panorama_360"},
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )
    assert response.status_code == 201, response.data
    tour = PropertyVirtualTour.objects.get(building=building)
    assert tour.property is None and tour.target == building
    from jsonschema import Draft202012Validator
    from core_apps.virtual_tours.openapi import document

    contract = document()
    schema = {**contract, "$ref": "#/components/schemas/Tour"}
    Draft202012Validator(schema).validate(response.json()["data"])
    fingerprint = scope_policy(
        building, "overview", [{"id": "entrance", "space_kind": "entrance"}]
    )
    building.topology_revision += 1
    assert fingerprint != scope_policy(
        building, "overview", [{"id": "entrance", "space_kind": "entrance"}]
    )
    with pytest.raises(TourError):
        scope_policy(
            building,
            "overview",
            [{"id": "private", "space_kind": "bedroom", "room_id": str(uuid.uuid4())}],
        )


def test_changed_child_defaults_invalidate_complex_bulk_preview(company_setup):
    owner, _, _, _, building, props, *_ = company_setup
    complex = ResidentialComplex.objects.create(
        manager=owner, name="Root", code="R", address="Test", declared_buildings=1
    )
    building.complex = complex
    building.unit_defaults = {"has_wifi": True}
    building.save()
    data = bulk(complex, props)
    data.update(changes={}, inherit_fields=["has_wifi"], reset_overrides=True)
    preview = changes.preview_bulk(owner, "complex", complex.id, data)
    building.unit_defaults = {"has_wifi": False}
    building.revision += 1
    building.save()
    result = changes.apply_bulk(owner, preview.id, command(expected_revision=1))
    assert all(
        row["status"] == "failed" and row["code_reason"] == "stale_revision"
        for row in result.results
    )


def test_private_asset_edits_do_not_change_commercial_approval(company_setup):
    owner, coordinator, _, _, building, *_ = company_setup
    item = approved(company_setup)
    changes.update_container(
        owner,
        "building",
        building.id,
        command(
            expected_revision=building.revision,
            kind="building",
            name=building.name,
            code=building.code,
            address=building.address,
            declared_units=2,
            facts={
                "private_access": "Private instruction",
                "contact_name": "Local contact",
            },
        ),
    )
    held = bookings.hold_item(
        coordinator, item.id, command(expected_revision=item.revision)
    )
    assert held.hold_id
    assert "Private instruction" not in str(held.snapshot)


def test_public_scope_fact_changes_require_new_approval(company_setup):
    owner, coordinator, _, _, building, *_ = company_setup
    item = approved(company_setup)
    original = item.snapshot.copy()
    changes.update_container(
        owner,
        "building",
        building.id,
        command(
            expected_revision=building.revision,
            kind="building",
            name=building.name,
            code=building.code,
            address=building.address,
            declared_units=2,
            facts={"included_services": ["Laundry"]},
        ),
    )
    with pytest.raises(RentalConflict):
        bookings.hold_item(
            coordinator, item.id, command(expected_revision=item.revision)
        )
    item.refresh_from_db()
    assert item.snapshot == original


def test_whole_topology_change_rolls_back_on_duplicate_target_code(company_setup):
    from django.db import IntegrityError

    owner, _, _, _, building, props, *_ = company_setup
    data = command(
        expected_revision=building.revision,
        operation="split_unit",
        units=versions(props[:1]),
        replacements=[
            {"unit_code": "NEW", "title": "First", "occupancy_capacity": 2},
            {
                "unit_code": props[1].unit_code,
                "title": "Conflicting",
                "occupancy_capacity": 2,
            },
        ],
        reason="Synthetic atomic change",
    )
    preview = topology.preview_topology(owner, "building", building.id, data)
    with pytest.raises(IntegrityError):
        topology.apply_topology(owner, preview.id, command(expected_revision=1))
    props[0].refresh_from_db()
    preview.refresh_from_db()
    assert props[0].retired_at is None and preview.applied_at is None
    assert not Property.objects.filter(building=building, unit_code="NEW").exists()


def test_preview_history_is_owner_scoped_and_recoverable(company_setup):
    owner, other, _, _, building, props, *_ = company_setup
    change = changes.preview_bulk(owner, "building", building.id, bulk(building, props))
    path = f"{API}residential-assets/building/{building.id}/changes/"
    response = authenticated(owner).get(path)
    assert response.status_code == 200
    assert str(change.id) in str(response.json())
    assert authenticated(other).get(path).status_code == 404
    assert (
        authenticated(other)
        .post(
            f"{API}residential-changes/{change.id}/",
            command(expected_revision=1),
            format="json",
        )
        .status_code
        == 404
    )


@pytest.mark.django_db(transaction=True)
def test_concurrent_move_and_whole_building_hold_cannot_both_succeed(company_setup):
    from core_apps.features.tests.test_cycle_concurrency import parallel_calls

    owner, coordinator, _, _, building, props, *_ = company_setup
    destination = ResidentialComplex.objects.create(
        manager=owner, name="Target", code="T", address="Test", declared_buildings=1
    )
    preview = topology.preview_topology(
        owner,
        "building",
        building.id,
        command(
            expected_revision=building.revision,
            operation="move_building",
            units=[],
            replacements=[],
            target_kind="complex",
            target_id=str(destination.id),
            target_revision=1,
            reason="Concurrent synthetic move",
        ),
    )
    item = approved(company_setup)

    def action(index):
        try:
            if index:
                topology.apply_topology(owner, preview.id, command(expected_revision=1))
                return "moved"
            bookings.hold_item(
                coordinator, item.id, command(expected_revision=item.revision)
            )
            return "held"
        except RentalConflict:
            return "blocked"

    results = parallel_calls(action)
    assert results.count("blocked") == 1, results
    building.refresh_from_db()
    item.refresh_from_db()
    assert not (building.complex_id and item.hold_id)


@pytest.mark.django_db(transaction=True)
def test_competing_bulk_apply_cannot_overwrite_twice(company_setup):
    from core_apps.features.tests.test_cycle_concurrency import parallel_calls
    from core_apps.features.models import RentalAuditEvent

    owner, _, _, _, building, props, *_ = company_setup
    preview = changes.preview_bulk(
        owner, "building", building.id, bulk(building, props)
    )

    def action(index):
        try:
            changes.apply_bulk(owner, preview.id, command(expected_revision=1))
            return "applied"
        except RentalConflict:
            return "blocked"

    assert sorted(parallel_calls(action)) == ["applied", "blocked"]
    assert (
        RentalAuditEvent.objects.filter(
            subject_id=preview.id, action="portfolio_bulk_applied"
        ).count()
        == 1
    )


def test_media_reviews_are_independent_and_removed_evidence_stays_in_history(
    company_setup, settings, tmp_path
):
    from core_apps.users.models import User

    owner, employee, _, _, building, *_ = company_setup
    settings.VIRTUAL_TOUR_PRIVATE_ROOT = str(tmp_path)
    image = io.BytesIO()
    Image.new("RGB", (4, 4), "blue").save(image, "PNG")
    raw = image.getvalue()
    body = command(
        expected_revision=building.revision,
        purpose="photo",
        caption="Synthetic common area",
        representative=True,
        sha256=hashlib.sha256(raw).hexdigest(),
        byte_size=len(raw),
        content_type="image/png",
    )
    item = media.create_intent(owner, "building", building.id, body)
    item = media.upload(owner, item.id, SimpleUploadedFile("photo.png", raw))
    path = f"{API}residential-media/{item.id}/bytes/"
    assert authenticated(employee).get(path).status_code == 403
    owner.is_superuser = True
    owner.save()
    with pytest.raises(PermissionDenied):
        media.review(
            owner,
            item.id,
            command(
                expected_revision=item.revision, status="approved", reason="Self review"
            ),
        )
    reviewer = User.objects.create_user(
        email="portfolio-reviewer@example.com",
        password="test",
        is_verified=True,
        is_superuser=True,
    )
    review_body = command(
        expected_revision=item.revision,
        status="approved",
        reason="Inspected common area",
    )
    reviewer_client = authenticated(reviewer)
    review = reviewer_client.post(
        f"{API}residential-media/{item.id}/review/", review_body, format="json"
    )
    assert review.status_code == 200, review.data
    recovery = (
        f"{API}rental-operations/{review_body['request_key']}/?subject_id={item.id}"
    )
    assert reviewer_client.get(recovery).status_code == 200
    assert authenticated(employee).get(recovery).status_code == 404
    reviewer.is_superuser = False
    reviewer.save()
    assert reviewer_client.get(recovery).status_code == 404
    item.refresh_from_db()
    assert authenticated(employee).get(path).status_code == 200
    media.remove(owner, item.id, command(expected_revision=item.revision))
    assert authenticated(employee).get(path).status_code == 404
    item.refresh_from_db()
    assert item.blob and item.reviewed_by == reviewer and item.state == "removed"


def test_unsupported_bulk_money_and_hidden_topology_fields_rejected():
    body = BulkPreviewBody(
        data=command(
            units=[{"id": str(uuid.uuid4()), "version": "v1"}],
            changes={"price": "100"},
            reason="Invalid",
        )
    )
    assert not body.is_valid()
    body = TopologyPreviewBody(
        data=command(
            operation="split_unit",
            units=[{"id": str(uuid.uuid4()), "version": "v1"}],
            replacements=[],
            target_id=str(uuid.uuid4()),
            reason="Invalid",
        )
    )
    assert not body.is_valid()


def test_admin_media_inspection_checks_reviewer_role(company_setup, settings, tmp_path):
    from django.test import Client
    from django.urls import reverse
    from core_apps.users.models import User

    owner, _, _, _, building, *_ = company_setup
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    settings.VIRTUAL_TOUR_PRIVATE_ROOT = str(tmp_path)
    image = io.BytesIO()
    Image.new("RGB", (4, 4), "blue").save(image, "PNG")
    raw = image.getvalue()
    body = command(
        expected_revision=building.revision,
        purpose="authority",
        caption="Synthetic historical evidence",
        representative=False,
        sha256=hashlib.sha256(raw).hexdigest(),
        byte_size=len(raw),
        content_type="image/png",
    )
    item = media.create_intent(owner, "building", building.id, body)
    item = media.upload(owner, item.id, SimpleUploadedFile("proof.png", raw))
    staff = User.objects.create_user(
        email="unassigned-staff@example.com",
        password="test",
        is_verified=True,
        is_staff=True,
    )
    client = Client()
    client.force_login(staff)
    path = reverse("admin:portfolio-media-review", args=[item.pk])
    byte_path = reverse("admin:portfolio-media-image", args=[item.pk])
    assert client.get(path).status_code == 403
    assert client.get(byte_path).status_code == 403
    staff.is_superuser = True
    staff.save()
    assert client.get(path).status_code == 200
    media.remove(owner, item.id, command(expected_revision=item.revision))
    history = client.get(byte_path)
    assert history.status_code == 200
    assert {"private", "no-store"} <= set(history["Cache-Control"].split(", "))
    history.close()
