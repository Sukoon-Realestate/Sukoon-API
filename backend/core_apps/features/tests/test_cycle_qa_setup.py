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
from core_apps.admin_api.models import StaffProfile
from core_apps.features.management.cycle_qa import ACTORS, BRANCHES, resource_id


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


@pytest.mark.django_db
def test_isolated_run_has_private_accounts_and_independent_scenario_inventory(tmp_path):
    secret_file = tmp_path / "private.json"
    manifest = prepare(run_id="joined-20261013", credentials_output=str(secret_file))
    secrets = json.loads(secret_file.read_text())
    assert secret_file.stat().st_mode & 0o777 == 0o600
    assert set(secrets["actors"]) == set(ACTORS)
    assert len({manifest[name]["property_id"] for name in BRANCHES}) == len(BRANCHES)
    assert not Lease.objects.exists() and not RentInvoice.objects.exists()
    assert len({account["password"] for account in secrets["actors"].values()}) == len(
        ACTORS
    )
    for alias, account in secrets["actors"].items():
        actor = User.objects.get(id=account["id"])
        assert actor.check_password(account["password"])
        assert account["password"] not in json.dumps(manifest)
        assert (
            actor.is_verified
            and actor.is_active
            and not actor.is_staff
            and not actor.is_superuser
        )
        if ACTORS[alias]:
            assert StaffProfile.objects.get(user=actor).role_name == ACTORS[alias]
        else:
            assert not StaffProfile.objects.filter(user=actor).exists()
    for branch, scope in (
        ("structured", "entire_property"),
        ("room", "room"),
        ("room_group", "room_group"),
        ("bed", "bed"),
    ):
        item = manifest[branch]
        assert item["selection"]["rental_scope"] == scope
        assert item["selection"]["property_id"] == item["property_id"]
        assert item["selection"]["offer_id"] == item["offer_id"]
        assert item["terms"]["monthly_rent"] == item["rent"]
    assert manifest["legacy"]["property_id"] != manifest["structured"]["property_id"]
    assert manifest["group"]["selection"]["capacity"] == 2


@pytest.mark.django_db
def test_isolated_rerun_preserves_account_access_inventory_visits_and_secrets(tmp_path):
    secret_file = tmp_path / "private.json"
    first = prepare(run_id="preserved", credentials_output=str(secret_file))
    owner = User.objects.get(id=first["actors"]["owner_a"]["id"])
    before_password = owner.password
    owner.is_verified = False
    owner.save(update_fields=["is_verified"])
    prop = Property.objects.get(id=first["structured"]["property_id"])
    prop.status = Property.Status.UNDER_REVIEW
    prop.rental_inventory["offers"][0]["terms"]["price"] = "12000.00"
    prop.rental_inventory["offers"][0]["revision"] = 4
    prop.save()
    PropertyVisit.objects.filter(id=first["structured"]["source_visit_id"]).update(
        status="rejected"
    )
    before_credentials = secret_file.read_bytes()
    second = prepare(run_id="preserved")
    owner.refresh_from_db()
    prop.refresh_from_db()
    assert owner.password == before_password and owner.is_verified is False
    assert prop.status == Property.Status.UNDER_REVIEW
    assert second["structured"]["expected_offer_revision"] == 4
    assert second["structured"]["rent"]["amount_minor"] == 1200000
    assert (
        PropertyVisit.objects.get(id=first["structured"]["source_visit_id"]).status
        == "rejected"
    )
    assert second["structured"]["start_date"] == first["structured"]["start_date"]
    assert secret_file.read_bytes() == before_credentials
    assert second["test_enablement"]["actors"]["owner_a"]["verified"] is False
    with pytest.raises(CommandError, match="new credentials"):
        prepare(run_id="preserved", credentials_output=str(secret_file))


@pytest.mark.django_db
def test_run_preflight_failures_do_not_create_or_mutate_accounts(tmp_path):
    with pytest.raises(CommandError, match="credentials-output"):
        prepare(run_id="missing-private-file")
    assert not User.objects.exists()
    path = tmp_path / "same.json"
    with pytest.raises(CommandError, match="separate"):
        prepare(run_id="same-path", output=str(path), credentials_output=str(path))
    assert not User.objects.exists()
    with pytest.raises(CommandError, match="1-40"):
        prepare(run_id="bad/slash", credentials_output=str(path))
    assert not User.objects.exists()


@pytest.mark.django_db
def test_run_cannot_promote_an_existing_account_or_replace_an_operator_role(tmp_path):
    owner = User.objects.create_user(
        id=resource_id("collision", "actor:owner_a"),
        email="existing@example.test",
        password="preserved",
    )
    with pytest.raises(CommandError, match="does not match"):
        prepare(run_id="collision", credentials_output=str(tmp_path / "collision.json"))
    owner.refresh_from_db()
    assert owner.email == "existing@example.test" and owner.check_password("preserved")
    assert User.objects.count() == 1 and not (tmp_path / "collision.json").exists()
    prepare(run_id="role-change", credentials_output=str(tmp_path / "first.json"))
    profile = StaffProfile.objects.get(
        user__id=resource_id("role-change", "actor:payout_operator")
    )
    profile.role_name = StaffProfile.RoleName.SUPPORT
    profile.save(update_fields=["role_name"])
    with pytest.raises(CommandError, match="changed roles"):
        prepare(run_id="role-change")
    profile.refresh_from_db()
    assert profile.role_name == StaffProfile.RoleName.SUPPORT


@pytest.mark.django_db
def test_rerun_keeps_exact_offer_after_reordering_and_reports_unavailable(tmp_path):
    import copy

    first = prepare(
        run_id="offer-identity", credentials_output=str(tmp_path / "accounts.json")
    )
    prop = Property.objects.get(id=first["structured"]["property_id"])
    duplicate = copy.deepcopy(prop.rental_inventory["offers"][0])
    duplicate["id"] = str(uuid.uuid4())
    prop.rental_inventory["offers"][0]["archived"] = True
    prop.rental_inventory["offers"].insert(0, duplicate)
    prop.save(update_fields=["rental_inventory"])
    second = prepare(run_id="offer-identity")
    assert second["structured"]["offer_id"] == first["structured"]["offer_id"]
    assert second["structured"]["selection"] is None
    assert "not available" in second["structured"]["blocked_reason"]
    prop.refresh_from_db()
    assert prop.rental_inventory["offers"][1]["archived"] is True
