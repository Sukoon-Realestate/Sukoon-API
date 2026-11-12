"""Capture pages bound nested rows in SQL and preserve the legacy projection."""

from uuid import uuid4

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from core_apps.virtual_tours.capture_models import (
    CaptureManifestRevision,
    CaptureProcessingJob,
    PropertyCaptureSession,
)
from core_apps.virtual_tours.capture_reads import prepare_sessions
from tools.qa.performance import measured
from core_apps.virtual_tours.capture_services import session_payload
from core_apps.virtual_tours.models import PropertyVirtualTour, TourRevision, TourReviewEvent

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("size", [1, 10, 100])
def test_capture_page_prepares_nested_jobs_and_revisions(size, user, property_obj):
    tour = PropertyVirtualTour.objects.create(property=property_obj, kind="panorama_360")
    sessions = [
        PropertyCaptureSession.objects.create(property=property_obj, owner=user, client_id=uuid4()) for _ in range(size)
    ]
    for session in sessions:
        manifest = CaptureManifestRevision.objects.create(
            session=session, revision=1, sha256=str(session.id), document={"coveragePlan": {"v": 1}}
        )
        job = CaptureProcessingJob.objects.create(manifest=manifest)
        rev = TourRevision.objects.create(tour=tour, capture_job=job, review_state="rejected", source_hash="current")
        TourReviewEvent.objects.create(
            revision=rev, reviewer=user, decision="rejected", source_hash="current", public_reason="Public reason"
        )
    # The caller supplies the already-authorized page, never the entire collection.
    query = PropertyCaptureSession.objects.filter(pk__in=[row.pk for row in sessions]).select_related("property")
    rows, report = measured("capture-sessions", size, lambda: [session_payload(row) for row in prepare_sessions(query)])
    assert len(rows) == size
    assert report["queries"] <= 8
    assert report["http_calls"] == 0
    assert all(row["jobs"][0]["selectedRevisions"][0]["review_reason"] == "Public reason" for row in rows)
    legacy = session_payload(query.first())
    assert next(row for row in rows if row["id"] == legacy["id"]) == legacy


def test_capture_job_and_revision_limits_are_per_parent(user, property_obj):
    tour = PropertyVirtualTour.objects.create(property=property_obj, kind="panorama_360")
    sessions = []
    for _ in range(2):
        session = PropertyCaptureSession.objects.create(property=property_obj, owner=user, client_id=uuid4())
        sessions.append(session)
        manifest = CaptureManifestRevision.objects.create(
            session=session, revision=1, sha256=str(session.id), document={}
        )
        for i in range(25):
            job = CaptureProcessingJob.objects.create(manifest=manifest, profile=str(i))
            TourRevision.objects.bulk_create([TourRevision(tour=tour, capture_job=job) for _ in range(3)])
    with CaptureQueriesContext(connection) as queries:
        prepared = prepare_sessions(
            PropertyCaptureSession.objects.filter(pk__in=[row.pk for row in sessions]).select_related("property")
        )
        result = [session_payload(row) for row in prepared]
    assert len(queries) <= 8
    assert all(len(row["jobs"]) == 20 for row in result)
    assert all(len(job["selectedRevisions"]) == 2 for row in result for job in row["jobs"])


def test_capture_list_authorizes_before_preparing(user, another_user, property_obj, auth_client):
    own = PropertyCaptureSession.objects.create(property=property_obj, owner=user, client_id=uuid4())
    PropertyCaptureSession.objects.create(property=property_obj, owner=another_user, client_id=uuid4())
    response = auth_client.get(f"/api/v1/properties/{property_obj.id}/capture-sessions/")
    assert response.status_code == 200
    assert [row["id"] for row in response.data["sessions"]] == [str(own.id)]


def test_compact_sessions_and_jobs_do_not_expand_large_outputs(user, another_user, property_obj, auth_client):
    session = PropertyCaptureSession.objects.create(property=property_obj, owner=user, client_id=uuid4())
    manifest = CaptureManifestRevision.objects.create(
        session=session, revision=1, sha256="synthetic", document={"large": "x" * 100000}
    )
    CaptureProcessingJob.objects.bulk_create(
        [CaptureProcessingJob(manifest=manifest, profile=str(i), outputs={"large": "x" * 100000}) for i in range(31)]
    )
    with CaptureQueriesContext(connection) as queries:
        response, _ = measured(
            "capture-session-summary",
            31,
            lambda: auth_client.get(f"/api/v1/properties/{property_obj.id}/capture-sessions/", {"summary": "true"}),
        )
    assert response.status_code == 200
    assert response.data["results"][0]["jobCount"] == 31
    assert len(response.content) < 2000
    assert len(queries) <= 5
    assert not any('"document"' in query["sql"] or '"outputs"' in query["sql"] for query in queries)
    response, report = measured(
        "capture-job-history",
        31,
        lambda: auth_client.get(
            f"/api/v1/property-captures/{session.id}/processing-jobs/", {"page_size": 10, "page": 3}
        ),
    )
    assert report["http_calls"] == 0
    assert response.status_code == 200
    assert response.data["count"] == 31
    assert len(response.data["results"]) == 10
    assert len(response.content) < 10000
    assert response.data["next"]
    assert response["Cache-Control"] == "private, no-store"
    auth_client.force_authenticate(another_user)
    assert auth_client.get(f"/api/v1/property-captures/{session.id}/processing-jobs/").status_code == 404
