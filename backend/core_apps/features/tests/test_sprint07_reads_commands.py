"""Direct commands, current retry authority and prepared housing read budgets."""

from uuid import uuid4

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.exceptions import NotFound, PermissionDenied

from core_apps.features.models import (
    CompanyMembership,
    CompanyMaintenanceScope,
    IdempotencyRecord,
    MaintenanceEvent,
    MaintenanceRequest,
)
from core_apps.features.services.company import tenancy_commands, tenancy_reads
from core_apps.features.services.maintenance_reads import collection_payload
from core_apps.features.tests.test_company_role_contexts import tenancy as tenancy
from core_apps.features.tests.test_company_contract_preparation import (
    cycle as cycle,
    company_setup as company_setup,
    rental_participants as rental_participants,
    policy as policy,
)
from core_apps.features.tests.test_rental_phase5 import phase5_lease as phase5_lease

pytestmark = pytest.mark.django_db


def test_direct_company_command_replays_once_and_rechecks_revoked_signer(tenancy):
    actors, item = tenancy
    body = {
        "request_key": str(uuid4()),
        "expected_revision": item.lease.revision,
        "role": "signer",
        "digest": item.terms_digest,
    }
    first = tenancy_commands.apply_action(
        actors["signer"], item.id, "review", body, body
    )
    assert first[1] == 200
    assert (
        tenancy_commands.apply_action(actors["signer"], item.id, "review", body, body)
        == first
    )
    assert (
        IdempotencyRecord.objects.filter(operation="company.tenancy.review").count()
        == 1
    )
    member = CompanyMembership.objects.get(
        company=actors["company"], user=actors["signer"]
    )
    member.is_active = False
    member.save(update_fields=["is_active"])
    with pytest.raises((NotFound, PermissionDenied)):
        tenancy_commands.apply_action(actors["signer"], item.id, "review", body, body)
    assert (
        IdempotencyRecord.objects.filter(operation="company.tenancy.review").count()
        == 1
    )


@pytest.mark.parametrize("size", [5, 40])
def test_company_maintenance_section_uses_prepared_facts_and_keeps_event_limit(
    tenancy, size
):
    actors, item = tenancy
    item.preparation.booking.assignments.update(occupancy_status="occupied")
    prop = item.preparation.booking.assignments.first().property
    for index in range(size):
        request = MaintenanceRequest.objects.create(
            lease=item.lease,
            reporter=actors["employee"],
            title=f"Synthetic {index}",
            description="Synthetic private description",
            category="other",
            priority="normal",
        )
        CompanyMaintenanceScope.objects.create(
            tenancy=item, request=request, property=prop
        )
        MaintenanceEvent.objects.bulk_create(
            [
                MaintenanceEvent(
                    maintenance_request=request,
                    actor=actors["owner"],
                    action="reply",
                    note=str(n),
                )
                for n in range(35)
            ]
        )
    facts = tenancy_reads.prepare(item, actors["owner"])
    with CaptureQueriesContext(connection) as queries:
        rows = tenancy_reads.maintenance_history(facts)
    assert len(queries) == 0
    assert len(rows) == size
    assert all(len(row["events"]) == 30 for row in rows)


@pytest.mark.parametrize("size", [5, 40])
def test_personal_maintenance_collection_batches_invoice_links(phase5_lease, size):
    owner, tenant, lease = phase5_lease
    MaintenanceRequest.objects.bulk_create(
        [
            MaintenanceRequest(
                lease=lease,
                reporter=tenant,
                title=f"Synthetic {n}",
                description="Synthetic",
                category="other",
                priority="normal",
            )
            for n in range(size)
        ]
    )
    with CaptureQueriesContext(connection) as queries:
        result = collection_payload(lease, owner)
    assert len(queries) == 4
    assert result["count"] == size and len(result["results"]) == size
    assert result["next"] is None and result["previous"] is None
    assert all(row["billing_invoices"] == [] for row in result["results"])


__all__ = [
    "tenancy",
    "cycle",
    "company_setup",
    "rental_participants",
    "policy",
    "phase5_lease",
]
