import io
import json
import uuid
from datetime import timedelta

import pytest
from django.core.management import call_command, CommandError
from django.test import override_settings
from django.utils import timezone

from core_apps.features.management.commands.prepare_owner_tenant_cycle_qa import (
    OWNER_ID,
    TENANT_ID,
    PROPERTY_ID,
    PENDING_VISIT_ID,
)
from core_apps.features.models import Lease, OwnerPaymentProfile, RentInvoice
from core_apps.properties.models import Property, PropertyVisit
from core_apps.users.models import User
from .test_rental_phase2 import authenticated


def prepare(**options):
    output = io.StringIO()
    call_command("prepare_owner_tenant_cycle_qa", stdout=output, **options)
    return json.loads(output.getvalue())


@pytest.mark.django_db
@override_settings(
    RENTAL_RUNTIME_ENVIRONMENT="production", OWNER_TENANT_QA_ENABLED=True
)
def test_setup_is_refused_in_production():
    before = User.objects.count()
    with pytest.raises(CommandError, match="nonproduction"):
        prepare()
    assert User.objects.count() == before


@pytest.mark.django_db
def test_fixture_manifest_is_executable_and_uses_a_separate_legacy_property():
    manifest = prepare()
    owner, tenant = User.objects.get(id=OWNER_ID), User.objects.get(id=TENANT_ID)
    legacy = manifest["legacy"]
    assert legacy["property_id"] != PROPERTY_ID
    structured = manifest["structured"]
    prop = Property.objects.get(id=PROPERTY_ID)
    offer = next(
        x for x in prop.rental_inventory["offers"] if x["id"] == structured["offer_id"]
    )
    assert structured["expected_offer_revision"] == offer["revision"]
    assert structured["rent"]["amount_minor"] == 150000
    assert (
        offer["terms"]["rental_period"] > 0 and len(offer["terms"]["description"]) >= 10
    )
    assert offer["terms"]["suitable_for"] == "all"
    assert not Lease.objects.exists() and not RentInvoice.objects.exists()
    assert manifest["test_enablement"]["full_cycles_verified"] is False
    assert OwnerPaymentProfile.objects.get(owner=owner).payout_ready is False
    client = authenticated(owner)
    invited = client.post(
        "/api/v1/features/v1/tenancy-invitations/",
        {
            "property_id": legacy["property_id"],
            "tenant_id": TENANT_ID,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert invited.status_code == 201, invited.data
    invitation = invited.data
    accepted = authenticated(tenant).post(
        f"/api/v1/features/v1/tenancy-invitations/{invitation['id']}/respond/",
        {
            "decision": "accepted",
            "revision": invitation["revision"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert accepted.status_code == 200
    draft = client.post(
        "/api/v1/features/v1/leases/",
        {
            "property_id": legacy["property_id"],
            "tenant_id": TENANT_ID,
            **legacy["draft"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert draft.status_code == 201, draft.data
    assert draft.data["status"] == "draft"
    cancelled = client.post(
        f"/api/v1/features/v1/leases/{draft.data['id']}/cancel/",
        {
            "revision": draft.data["revision"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert cancelled.status_code == 200
    assert cancelled.data["financial_closure_status"] == "closed"
    assert not RentInvoice.objects.exists()


@pytest.mark.django_db
def test_rerun_preserves_password_rejection_and_paid_records(tmp_path):
    original = prepare()
    owner, tenant = User.objects.get(id=OWNER_ID), User.objects.get(id=TENANT_ID)
    owner.set_password("local-test-password")
    owner.save()
    password_hash = owner.password
    PropertyVisit.objects.filter(id=PENDING_VISIT_ID).update(status="rejected")
    prop = Property.objects.get(id=PROPERTY_ID)
    start = timezone.localdate()
    lease = Lease.objects.create(
        id="c0400000-0000-0000-0000-000000000001",
        property=prop,
        owner=owner,
        tenant=tenant,
        template_id="eg-residential-v1",
        template_version="1",
        start_date=start,
        end_date=start + timedelta(days=30),
        rent_amount_minor=150000,
        status="active",
        revision=15,
        legacy_read_only=False,
    )
    invoice = RentInvoice.objects.create(
        lease=lease,
        reference="QA-PAID",
        due_date=start,
        amount_minor=300000,
        charges_minor=300000,
        applied_minor=300000,
        status="paid",
        revision=7,
    )
    rerun = prepare(output=str(tmp_path / "new-fixtures.json"))
    owner.refresh_from_db()
    lease.refresh_from_db()
    invoice.refresh_from_db()
    assert owner.password == password_hash
    assert PropertyVisit.objects.get(id=PENDING_VISIT_ID).status == "rejected"
    assert (
        lease.status,
        lease.revision,
        invoice.status,
        invoice.revision,
        invoice.applied_minor,
    ) == ("active", 15, "paid", 7, 300000)
    assert rerun["legacy"] == original["legacy"]
    assert rerun["test_enablement"]["visits"]["rejection"]["status"] == "rejected"
    with pytest.raises(CommandError, match="new output"):
        prepare(output=str(tmp_path / "new-fixtures.json"))


@pytest.mark.django_db
def test_missing_offer_terms_are_repaired_once_with_revision_increment():
    prepare()
    prop = Property.objects.get(id=PROPERTY_ID)
    prop.rental_inventory["offers"][0]["terms"] = {
        "price": "1700.00",
        "price_period": "monthly",
    }
    prop.rental_inventory["offers"][0]["revision"] = 8
    prop.save()
    result = prepare()
    assert result["structured"]["expected_offer_revision"] == 9
    assert result["structured"]["rent"]["amount_minor"] == 170000
    again = prepare()
    assert again["structured"] == result["structured"]
