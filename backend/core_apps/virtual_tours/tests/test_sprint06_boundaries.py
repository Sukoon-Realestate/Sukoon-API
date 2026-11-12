"""Sprint 06: publication revocation, prepared pages and transport-free receipts."""

import json
from pathlib import Path

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from core_apps.properties.models import Property
from core_apps.users.models import AccountClosureRequest
from core_apps.virtual_tours import sessions
from core_apps.virtual_tours.authoring_commands import create
from core_apps.virtual_tours.models import PropertyVirtualTour, TourRevision
from core_apps.virtual_tours.operations import mutate
from core_apps.virtual_tours.review_reads import review_collection
from core_apps.virtual_tours.selectors import owner_tours
from .test_tours import ready_variant

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("change", ["moderation", "retirement", "closure", "closed"])
def test_issued_public_session_and_signed_bytes_recheck_canonical_publication(
    property_obj, user, change
):
    tour, revision, variant = ready_variant(property_obj)
    opened = sessions.create_session(tour, user, {})
    client = APIClient()
    exchanged = client.post(
        "/api/v1/virtual-tour-viewer/exchange/",
        {"bootstrap_token": opened["bootstrap_token"]},
        format="json",
    )
    assert exchanged.status_code == 200
    base = f"/api/v1/virtual-tour-viewer/sessions/{opened['session_id']}/"
    headers = {"HTTP_X_TOUR_CREDENTIAL": exchanged.data["credential"]}
    resource_id = next(iter(variant.resources))
    access = client.get(base + f"resources/{resource_id}/access/", **headers)
    assert access.status_code == 200
    byte_path = access.data.get("url", access.data.get("url_template"))
    if change == "moderation":
        Property.objects.filter(pk=property_obj.pk).update(moderation_blocked=True)
    elif change == "retirement":
        from django.utils import timezone

        Property.objects.filter(pk=property_obj.pk).update(
            retired_at=timezone.now(), status="hidden"
        )
    elif change == "closed":
        from django.utils import timezone

        type(user).objects.filter(pk=user.pk).update(closed_at=timezone.now())
    else:
        AccountClosureRequest.objects.create(user=user, active=True)
    assert client.get(base + "manifest/", **headers).status_code == 409
    assert client.get(byte_path).status_code == 409
    # Owner previews remain separately authorized from public publication.
    if change in {"moderation", "closure", "retirement"}:
        preview = sessions.create_session(
            tour, user, {"preview": True, "revision_id": str(revision.id)}
        )
        assert preview["session_id"]


@pytest.mark.parametrize("size", [1, 20, 100])
def test_reviewer_page_has_constant_queries_and_no_sql_in_projection(
    property_obj, superuser, size
):
    tour = PropertyVirtualTour.objects.create(
        property=property_obj, kind="panorama_360"
    )
    TourRevision.objects.bulk_create(
        [
            TourRevision(tour=tour, review_state="pending", processing_state="ready")
            for _ in range(size)
        ]
    )
    with CaptureQueriesContext(connection) as queries:
        payload = review_collection(superuser)
        encoded = json.dumps(payload, default=str).encode()
    assert len(payload["items"]) == min(size, 20)
    assert payload["count"] == size
    assert len(queries) <= 10
    assert len(encoded) < 50000
    report = {
        "family": "tour-review",
        "size": size,
        "queries": len(queries),
        "bytes": len(encoded),
    }
    from os import environ

    if environ.get("SPRINT06_METRICS"):
        with Path(environ["SPRINT06_METRICS"]).open("a") as stream:
            stream.write(json.dumps(report) + "\n")


def test_owner_tours_prefetch_latest_assets_and_history(property_obj, user):
    tour = PropertyVirtualTour.objects.create(
        property=property_obj, kind="panorama_360"
    )
    TourRevision.objects.bulk_create(
        [TourRevision(tour=tour, review_state="rejected") for _ in range(100)]
    )
    with CaptureQueriesContext(connection) as queries:
        payload = owner_tours(user, property_obj.id)
    assert len(payload["tours"]) == 1
    assert payload["tours"][0]["latest_revision"]
    assert len(queries) <= 6


def test_domain_create_and_receipt_retry_do_not_require_http(property_obj, user):
    kwargs = dict(
        user=user,
        auth=None,
        key="sprint06-domain-create",
        body={"kind": "panorama_360"},
        etag="",
        action="tour.create",
        resource=property_obj.id,
        execute=lambda actor: create(
            actor, property_obj.id, "property", {"kind": "panorama_360"}
        ),
    )
    first = mutate(**kwargs)
    replay = mutate(**kwargs)
    assert first[:2] == replay[:2]
    assert first[2] is False and replay[2] is True
    assert PropertyVirtualTour.objects.filter(property=property_obj).count() == 1


@pytest.mark.parametrize("size", [1, 20, 100])
def test_capture_collection_batches_nested_jobs_and_revisions(property_obj, user, size):
    from uuid import uuid4
    from core_apps.virtual_tours.capture_models import (
        PropertyCaptureSession,
        CaptureManifestRevision,
        CaptureProcessingJob,
    )
    from core_apps.virtual_tours.capture_reads import collection
    from core_apps.virtual_tours.capture_services import session_payload

    records = []
    tour = PropertyVirtualTour.objects.create(
        property=property_obj, kind="panorama_360"
    )
    for _ in range(size):
        row = PropertyCaptureSession.objects.create(
            property=property_obj, owner=user, client_id=uuid4()
        )
        manifest = CaptureManifestRevision.objects.create(
            session=row,
            revision=1,
            sha256="a" * 64,
            document={"coveragePlan": {"schemaVersion": 1}},
        )
        job = CaptureProcessingJob.objects.create(
            manifest=manifest,
            state="failed",
            outputs={"panorama360": {"status": "failed"}},
        )
        TourRevision.objects.create(tour=tour, capture_job=job)
        records.append(row)
    with CaptureQueriesContext(connection) as queries:
        payload = collection(user, property_obj.id)
        encoded = json.dumps(payload, default=str).encode()
    assert len(payload["sessions"]) == min(size, 20)
    assert len(queries) <= 10
    assert len(encoded) < 50000
    first = payload["sessions"][0]
    ordinary = session_payload(
        PropertyCaptureSession.objects.select_related("property").get(id=first["id"])
    )
    assert first == ordinary
