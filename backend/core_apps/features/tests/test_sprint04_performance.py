"""Bound discovery retention work and prove resumable, atomic scrubbing."""

from datetime import timedelta
from uuid import uuid4
from unittest.mock import patch

import pytest
from django.utils import timezone

from core_apps.features.planning_models import CommuteSearch, TenantAssistantTurn
from core_apps.features.services.planning import purge_expired_discovery
from core_apps.features.models import IdempotencyRecord

pytestmark = pytest.mark.django_db


def test_discovery_scrubbing_resumes_and_does_not_reprocess_completed_rows(user):
    expired = timezone.now() - timedelta(seconds=1)
    CommuteSearch.objects.bulk_create(
        [
            CommuteSearch(
                user=user, query={"private": i}, matches=[i], expires_at=expired
            )
            for i in range(503)
        ]
    )
    TenantAssistantTurn.objects.bulk_create(
        [
            TenantAssistantTurn(
                user=user, reply={"private": i}, session_id=str(i), expires_at=expired
            )
            for i in range(503)
        ]
    )
    future = CommuteSearch.objects.create(
        user=user, query={"keep": True}, expires_at=expired + timedelta(days=1)
    )
    assert purge_expired_discovery() == 1000
    assert (
        CommuteSearch.objects.filter(
            private_purged_at__isnull=False, query={}, matches=[]
        ).count()
        == 500
    )
    assert (
        TenantAssistantTurn.objects.filter(
            private_purged_at__isnull=False, reply={}, session_id=""
        ).count()
        == 500
    )
    assert purge_expired_discovery() == 6
    assert purge_expired_discovery() == 0
    future.refresh_from_db()
    assert future.query == {"keep": True} and future.private_purged_at is None


def test_discovery_scrub_receipt_and_marker_are_atomic(user):
    search = CommuteSearch.objects.create(
        user=user, query={"private": True}, expires_at=timezone.now()
    )
    receipt = IdempotencyRecord.objects.create(
        user=user,
        operation="purge-test",
        request_key=str(uuid4()),
        fingerprint="test",
        result_subject_id=search.id,
        response_status=200,
        response_data={"private": True},
    )
    from django.db.models.query import QuerySet

    original = QuerySet.update

    def update(queryset, **kwargs):
        if queryset.model is CommuteSearch and "private_purged_at" in kwargs:
            raise RuntimeError("injected after receipt scrub")
        return original(queryset, **kwargs)

    with patch.object(QuerySet, "update", update):
        with pytest.raises(RuntimeError):
            purge_expired_discovery()
    search.refresh_from_db()
    receipt.refresh_from_db()
    assert receipt.response_status == 200 and receipt.response_data == {"private": True}
    assert search.private_purged_at is None and search.query == {"private": True}
    assert purge_expired_discovery(batch_size=1) == 1
    receipt.refresh_from_db()
    assert receipt.response_status == 410 and "private" not in receipt.response_data


@pytest.mark.parametrize("size", [5, 40, 100])
def test_public_payment_reliability_batch_budget(size, user, another_user):
    from core_apps.features.models import Lease, RentInvoice
    from core_apps.features.services.reputation.public_summary import (
        payment_reliability,
    )
    from core_apps.properties.tests.test_views import _create_published_property
    from core_apps.admin_api.tests.test_sprint04_performance import measured

    prop = _create_published_property(owner=user, price=1000)
    now = timezone.now()
    lease = Lease.objects.create(
        property=prop,
        owner=user,
        tenant=another_user,
        start_date=now.date(),
        end_date=now.date() + timedelta(days=30),
        template_id="test",
        template_version="1",
        rent_amount_minor=1000,
        offer_id=str(uuid4()),
        offer_snapshot={"rental_scope": "entire_property"},
    )
    RentInvoice.objects.bulk_create(
        [
            RentInvoice(
                lease=lease,
                reference=f"performance-{i}",
                due_date=now.date(),
                due_at=now - timedelta(days=1),
                amount_minor=100,
                status="due",
            )
            for i in range(size)
        ]
    )
    result, report = measured(
        "public-payment-reliability",
        size,
        lambda: payment_reliability("person_tenant", another_user.id, now=now),
    )
    assert result["sample_count"] == result["late_count"] == size
    assert result["excluded_count"] == 0 and report["queries"] <= 3
