"""C11-T02/T03/T06: expired consent cannot become a timeless entry permit."""

import uuid
from datetime import timedelta
from unittest.mock import patch
import pytest
from django.utils import timezone
from core_apps.features.models import MaintenanceRequest
from core_apps.features.tests.test_rental_phase5 import phase5_lease, client_for

pytestmark = pytest.mark.django_db


def send(actor, item, action, **extra):
    return client_for(actor).post(
        f"/api/v1/features/v1/maintenance-requests/{item.id}/actions/",
        {
            "action": action,
            "note": "Reviewed appointment",
            "expected_revision": item.revision,
            "request_key": str(uuid.uuid4()),
            **extra,
        },
        format="json",
    )


@pytest.fixture
def approved_window(phase5_lease):
    owner, tenant, lease = phase5_lease
    start = timezone.now() + timedelta(days=1)
    item = MaintenanceRequest.objects.create(
        lease=lease,
        reporter=tenant,
        title="Leak",
        description="Repair the pipe",
        category="plumbing",
        priority="normal",
    )
    response = send(
        owner,
        item,
        "propose_appointment",
        appointment_at=start.isoformat(),
        appointment_ends_at=(start + timedelta(hours=1)).isoformat(),
    )
    assert response.status_code == 200, response.data
    item.refresh_from_db()
    assert send(tenant, item, "accept_appointment").status_code == 200
    item.refresh_from_db()
    return owner, tenant, item, start


@pytest.mark.parametrize(
    "minutes,allowed", [(-1, False), (0, True), (59, True), (60, False), (1440, False)]
)
def test_start_requires_current_exact_window(approved_window, minutes, allowed):
    owner, tenant, item, start = approved_window
    with patch(
        "django.utils.timezone.now", return_value=start + timedelta(minutes=minutes)
    ):
        detail = (
            client_for(owner)
            .get(f"/api/v1/features/v1/maintenance-requests/{item.id}/")
            .data
        )
        assert ("start_work" in detail["allowed_actions"]) is allowed
        response = send(owner, item, "start_work")
    assert response.status_code == (200 if allowed else 409)
    item.refresh_from_db()
    assert item.status == ("in_progress" if allowed else "scheduled")


def test_missed_window_reproposal_needs_new_consent(approved_window):
    owner, tenant, item, start = approved_window
    with patch("django.utils.timezone.now", return_value=start + timedelta(hours=2)):
        response = send(tenant, item, "report_missed", request_key="stable-missed")
        assert response.status_code == 200
        # Replay the original revision/key yields exactly the same event.
        assert (
            send(tenant, item, "report_missed", request_key="stable-missed").data
            == response.data
        )
        item.refresh_from_db()
        assert item.status == "acknowledged" and item.access_approved_version is None
        assert item.events.filter(action="report_missed").count() == 1
        response = send(
            owner,
            item,
            "propose_appointment",
            appointment_at=(start + timedelta(days=1)).isoformat(),
            appointment_ends_at=(start + timedelta(days=1, hours=1)).isoformat(),
        )
        assert response.status_code == 200
        item.refresh_from_db()
        assert item.appointment_version == 2 and item.access_approved_version is None
        assert send(owner, item, "start_work").status_code == 409


def test_legacy_or_unbounded_window_never_invents_end(phase5_lease):
    owner, tenant, lease = phase5_lease
    item = MaintenanceRequest.objects.create(
        lease=lease,
        reporter=tenant,
        title="Legacy",
        description="Old appointment",
        category="plumbing",
        priority="normal",
        status="scheduled",
        appointment_at=timezone.now() - timedelta(days=1),
        appointment_version=1,
        access_approved_version=1,
    )
    assert send(owner, item, "start_work").status_code == 409
    item.refresh_from_db()
    assert item.appointment_ends_at is None
    assert (
        send(
            owner,
            item,
            "propose_appointment",
            appointment_at=(timezone.now() + timedelta(days=1)).isoformat(),
        ).status_code
        == 400
    )
    assert item.events.count() == 0


def test_provider_disable_keeps_existing_maintenance_authorized(
    approved_window, settings
):
    owner, tenant, item, start = approved_window
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = False
    settings.RENTAL_PROVIDER_BACKEND = "disabled"
    with patch("django.utils.timezone.now", return_value=start):
        for subject, action in [
            (item.id, "start_work"),
            (item.lease.id, "create_maintenance_request"),
        ]:
            response = client_for(owner).get(
                "/api/v1/features/v1/rental-capabilities/",
                {"subject_id": str(subject), "action": action},
            )
            assert response.status_code == 200
            assert "rental_maintenance" in response.data["enabled_capabilities"]
            assert action in response.data["allowed_actions"]
            assert "checkout" not in response.data["allowed_actions"]
        assert send(owner, item, "start_work").status_code == 200
        owner.is_verified = False
        owner.save()
        item.refresh_from_db()
        assert send(owner, item, "report_resolved").status_code == 403


@pytest.mark.django_db(transaction=True)
def test_concurrent_same_access_command_is_replayed_once(approved_window):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import connection, connections

    if connection.vendor != "postgresql":
        pytest.skip("Requires independent PostgreSQL connections")
    owner, tenant, item, start = approved_window
    barrier = Barrier(2)
    key = str(uuid.uuid4())

    def execute(_):
        connections.close_all()
        try:
            barrier.wait(timeout=10)
            response = send(owner, item, "start_work", request_key=key)
            return response.status_code, response.data
        finally:
            connections.close_all()

    with patch("django.utils.timezone.now", return_value=start):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(execute, range(2)))
    assert [status for status, _ in results] == [200, 200], results
    assert results[0][1] == results[1][1]
    assert item.events.filter(action="start_work").count() == 1
    item.refresh_from_db()
    assert item.status == "in_progress"
