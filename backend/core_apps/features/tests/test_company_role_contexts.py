"""HTTP negative tests: one active company role, canonical shared resources."""

from datetime import timedelta
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from core_apps.features.models import CompanyMembership, CompanyTenancy, RentInvoice
from core_apps.features.tests.test_company_contract_preparation import (
    cycle,
    company_setup,
    rental_participants,
    policy,
    person,
    command,
    API,
)
from core_apps.features.services.company import (
    contract_preparation as prep,
    tenancy_contracts as contracts,
)


def client(user, company=None, role=None):
    result = APIClient()
    result.force_authenticate(user=user)
    if role:
        result.credentials(
            HTTP_X_SUKOON_COMPANY_ROLE=role, HTTP_X_SUKOON_COMPANY_ID=str(company.id)
        )
    return result


@pytest.fixture
def tenancy(cycle):
    operator = person("role-execution-reviewer")
    operator.is_staff = operator.is_superuser = True
    operator.save()
    for mandate in cycle["mandates"]:
        contracts.verify_mandate(
            operator,
            mandate.id,
            command(
                expected_revision=mandate.revision,
                evidence_reference="synthetic-role-review",
                verified_until=timezone.now() + timedelta(days=20),
                reason="Synthetic role boundary test",
            ),
        )
    item = prep.prepare(cycle["coordinator"], cycle["item"].id, cycle["body"])
    for role in ("owner", "signer", "payer", "employee", "colleague"):
        item.refresh_from_db()
        prep.respond(
            cycle[role],
            item.id,
            command(
                expected_revision=item.revision,
                snapshot_digest=item.snapshot_digest,
                role="employee" if role == "colleague" else role,
                decision="accepted",
                reason="",
            ),
        )
    item.refresh_from_db()
    prep.reserve(
        cycle["coordinator"], item.id, command(expected_revision=item.revision)
    )
    item.refresh_from_db()
    value = contracts.create(
        cycle["coordinator"], item.id, command(expected_revision=item.revision)
    )
    return cycle, value


@pytest.mark.django_db
def test_discovery_does_not_disclose_management_or_financial_data(cycle):
    actor = client(cycle["coordinator"])
    response = actor.get(API + "companies/")
    assert response.status_code == 200
    row = response.data["results"][0]
    assert (
        not {"readiness", "budget_limit_minor", "permissions", "contact_email"}
        & row.keys()
    )
    roles = actor.get(API + f"companies/{cycle['company'].id}/role-contexts/")
    assert roles.status_code == 200
    assert {r["role"] for r in roles.data["roles"]} == {"admin", "coordinator"}


@pytest.mark.django_db
def test_create_second_company_requires_fresh_role_selection(cycle):
    actor = client(cycle["coordinator"], cycle["company"], "admin")
    body = command(
        expected_revision=0,
        name="Second role boundary company",
        registration_number="ROLE-SECOND-COMPANY",
        contact_email="second-role-company@example.test",
    )
    response = actor.post(API + "companies/", body, format="json")
    assert response.status_code == 201, response.data
    resource = response.data["resource"]
    other_id = resource["id"]
    assert other_id != str(cycle["company"].id)
    assert not {"permissions", "budget_limit_minor", "contact_email"} & resource.keys()
    # Discovery creates no implicit switch and no authority in the old context.
    assert actor.get(API + f"companies/{other_id}/").status_code == 403
    contexts = actor.get(API + f"companies/{other_id}/role-contexts/")
    assert contexts.status_code == 200
    assert {row["role"] for row in contexts.data["roles"]} == {"admin"}
    replay = actor.post(API + "companies/", body, format="json")
    assert replay.status_code == 201, replay.data
    assert replay.data["operation_receipt"] == response.data["operation_receipt"]
    assert replay.data["resource"] == {
        "id": other_id,
        "revision": resource["revision"],
    }


@pytest.mark.django_db
def test_employee_preparation_excludes_other_responsibilities(cycle):
    item = prep.prepare(cycle["coordinator"], cycle["item"].id, cycle["body"])
    # Even when another delegate blocks preparation, that person's task is not
    # part of the employee's housing/consent response.
    item.signer_mandate.state = "revoked"
    item.signer_mandate.save()
    response = client(cycle["employee"], cycle["company"], "employee").get(
        API + f"company-contract-preparations/{item.id}/"
    )
    assert response.status_code == 200, response.data
    assert (
        not {
            "provider_available",
            "blocking_reasons",
            "payer_kind",
            "renter_kind",
            "employees_are_debtors",
            "signer_name",
            "payer_name",
            "package",
            "full_term_rent_minor",
            "deposit_minor",
            "booking_id",
        }
        & response.data.keys()
    )
    assert all(
        row["actor_id"] == str(cycle["employee"].id) for row in response.data["reviews"]
    )
    assert str(cycle["colleague"].id) not in str(response.data)
    assert all(row["role"] == "employee" for row in response.data["responses"])


@pytest.mark.django_db
@pytest.mark.parametrize(
    "actor,role,forbidden",
    [
        (
            "coordinator",
            "coordinator",
            {"terms", "invoices", "refunds", "signing_sessions", "signing_document"},
        ),
        (
            "employee",
            "employee",
            {
                "terms",
                "invoices",
                "package",
                "full_term_rent_minor",
                "signing_document",
                "document_hash",
            },
        ),
        (
            "payer",
            "payer",
            {
                "terms",
                "signing_document",
                "signing_sessions",
                "document_hash",
                "assignments",
            },
        ),
        ("signer", "signer", {"invoices", "refunds", "chargebacks", "maintenance"}),
    ],
)
def test_role_payload_omits_other_role_data(tenancy, actor, role, forbidden):
    actors, item = tenancy
    response = client(actors[actor], actors["company"], role).get(
        API + f"company-tenancies/{item.id}/"
    )
    assert response.status_code == 200, response.data
    assert not forbidden & response.data.keys()
    assert response.data["roles"] == [role]
    if role == "employee":
        assert str(actors["colleague"].id) not in str(response.data)
    if role == "payer":
        assert response.data["contract_summary"]["kind"] == "summary"


@pytest.mark.django_db
def test_missing_role_admin_role_and_spoofed_company_do_not_reveal_tenancy(tenancy):
    actors, item = tenancy
    path = API + f"company-tenancies/{item.id}/"
    assert client(actors["coordinator"]).get(path).status_code == 404
    assert (
        client(actors["coordinator"], actors["company"], "admin").get(path).status_code
        == 404
    )
    assert (
        client(actors["employee"], actors["company"], "payer").get(path).status_code
        == 404
    )
    spoofed = client(actors["payer"], actors["company"], "payer")
    spoofed.credentials(
        HTTP_X_SUKOON_COMPANY_ROLE="payer",
        HTTP_X_SUKOON_COMPANY_ID="00000000-0000-0000-0000-000000000000",
    )
    assert spoofed.get(path).status_code == 404
    assert client(actors["owner"]).get(path).status_code == 200


@pytest.mark.django_db
def test_multi_role_switch_does_not_inherit_management_or_signing(tenancy):
    actors, item = tenancy
    member = CompanyMembership.objects.get(
        user=actors["coordinator"], company=actors["company"]
    )
    url = API + f"companies/{actors['company'].id}/members/"
    assert (
        client(actors["coordinator"], actors["company"], "admin").get(url).status_code
        == 200
    )
    assert (
        client(actors["coordinator"], actors["company"], "coordinator")
        .get(url)
        .status_code
        == 403
    )
    result = client(actors["coordinator"], actors["company"], "coordinator").post(
        API + f"company-tenancies/{item.id}/review/",
        command(
            expected_revision=item.lease.revision,
            role="signer",
            digest=item.terms_digest,
        ),
        format="json",
    )
    assert result.status_code == 403
    member.is_active = False
    member.save()
    assert (
        client(actors["coordinator"], actors["company"], "coordinator")
        .get(API + f"company-tenancies/{item.id}/")
        .status_code
        == 404
    )


@pytest.mark.django_db
def test_mandate_revocation_removes_context_and_direct_access(tenancy):
    actors, item = tenancy
    actor = client(actors["signer"], actors["company"], "signer")
    path = API + f"company-tenancies/{item.id}/"
    assert actor.get(path).status_code == 200
    item.signer_mandate.state = "revoked"
    item.signer_mandate.save()
    assert actor.get(path).status_code == 404
    context = actor.get(API + f"companies/{actors['company'].id}/role-contexts/").data
    assert "signer" not in {r["role"] for r in context["roles"]}


@pytest.mark.django_db
def test_two_real_companies_never_share_role_resource_authority(tenancy):
    from core_apps.features.models import Company

    actors, item = tenancy
    other = Company.objects.create(
        name="Second synthetic company",
        registration_number="synthetic-second-company",
        contact_email="second@company-test.invalid",
    )
    CompanyMembership.objects.create(
        company=other, user=actors["coordinator"], is_admin=True, is_coordinator=True
    )
    actor = client(actors["coordinator"], other, "coordinator")
    contexts = actor.get(API + f"companies/{other.id}/role-contexts/")
    assert contexts.status_code == 200
    assert {row["role"] for row in contexts.data["roles"]} == {"admin", "coordinator"}
    assert actor.get(API + f"company-tenancies/{item.id}/").status_code == 404
    assert actor.get(API + f"companies/{actors['company'].id}/").status_code == 403
    assert actor.get(API + "company-tenancies/").data["results"] == []


@pytest.mark.django_db
def test_same_person_signing_and_payment_roles_remain_separate(tenancy):
    actors, item = tenancy
    # An explicitly synthetic multi-role person; the canonical tenancy is shared.
    item.payer_mandate.membership = item.signer_mandate.membership
    item.payer_mandate.save()
    path = API + f"company-tenancies/{item.id}/"
    signer = client(actors["signer"], actors["company"], "signer").get(path)
    payer = client(actors["signer"], actors["company"], "payer").get(path)
    assert signer.status_code == payer.status_code == 200
    assert signer.data["roles"] == ["signer"]
    assert payer.data["roles"] == ["payer"]
    assert "terms" in signer.data and "invoices" not in signer.data
    assert "invoices" in payer.data and "terms" not in payer.data
    assert "signing_document" not in payer.data
    assert client(actors["signer"]).get(path).status_code == 404


@pytest.mark.django_db
def test_company_viewing_assignment_and_counters_exclude_other_work(cycle):
    from django.urls import reverse
    from core_apps.properties.models import PropertyVisit
    from core_apps.properties.services.viewing_access import for_user, can_read
    from core_apps.features.services.company.role_context import bound_role

    company = cycle["company"]
    now = timezone.localtime()
    visit = PropertyVisit.objects.create(
        property=cycle["units"][0],
        tenant=cycle["employee"],
        requested_by=cycle["coordinator"],
        company=company,
        context_kind="company",
        status="confirmed",
        visit_date=now.date(),
        visit_time=now.time(),
    )
    PropertyVisit.objects.create(
        property=cycle["units"][0],
        tenant=cycle["coordinator"],
        status="confirmed",
        visit_date=now.date(),
        visit_time=now.time(),
    )
    representative = client(cycle["employee"], company, "coordinator")
    response = representative.get(API + f"companies/{company.id}/role-contexts/")
    assert {r["role"] for r in response.data["roles"]} == {"coordinator", "employee"}
    assert (
        representative.get(API + f"companies/{company.id}/").data["permissions"][
            "coordinate"
        ]
        is False
    )
    with bound_role(cycle["coordinator"], company.id, "coordinator"):
        assert list(for_user(cycle["coordinator"]).values_list("id", flat=True)) == [
            visit.id
        ]
    other = person("unassigned-role-coordinator")
    CompanyMembership.objects.create(company=company, user=other, is_coordinator=True)
    with bound_role(other, company.id, "coordinator"):
        assert not can_read(visit, other) and not for_user(other).exists()
    counts = (
        client(cycle["coordinator"], company, "coordinator")
        .get(reverse("tenant-unread-counts"), {"workspace": "company"})
        .json()["data"]
    )
    assert counts["visit_requests_count"] == 1
    assert counts["request_counts"] == {} and counts["favorites_count"] == 0
    employee_counts = (
        client(cycle["employee"], company, "employee")
        .get(reverse("tenant-unread-counts"), {"workspace": "company"})
        .json()["data"]
    )
    assert employee_counts["visit_requests_count"] == 0


@pytest.mark.django_db
def test_shared_invoice_and_contract_urls_are_separate(tenancy):
    actors, item = tenancy
    invoice = RentInvoice.objects.create(
        lease=item.lease,
        purpose="rent",
        amount_minor=100,
        charges_minor=100,
        due_date=timezone.localdate(),
        reference="ROLE-TEST",
    )
    from core_apps.features.services.billing_invoices import authorized_invoice
    from core_apps.features.services.company.role_context import _request
    from rest_framework.exceptions import NotFound
    from django.test import RequestFactory

    for role, actor in [
        ("signer", actors["signer"]),
        ("coordinator", actors["coordinator"]),
        ("payer", actors["payer"]),
    ]:
        request = RequestFactory().get(
            "/",
            HTTP_X_SUKOON_COMPANY_ROLE=role,
            HTTP_X_SUKOON_COMPANY_ID=str(actors["company"].id),
        )
        request.user = actor
        token = _request.set(request)
        try:
            if role == "payer":
                assert authorized_invoice(actor, invoice.id).id == invoice.id
            else:
                with pytest.raises(NotFound):
                    authorized_invoice(actor, invoice.id)
        finally:
            _request.reset(token)


@pytest.mark.django_db
def test_notifications_hide_other_roles_legacy_and_revoked_membership(cycle):
    from django.urls import reverse
    from core_apps.notifications.models import Notification

    user, company = cycle["coordinator"], cycle["company"]

    def notice(role=None):
        return Notification.objects.create(
            user=user,
            title="Private task",
            body="not lock-screen copy",
            data={
                "workspace": "company",
                "company_id": str(company.id),
                **({"company_role": role} if role else {}),
            },
        )

    own, other, legacy = notice("coordinator"), notice("admin"), notice()
    actor = client(user, company, "coordinator")
    for value, status in [(own, 200), (other, 404), (legacy, 404)]:
        assert (
            actor.get(reverse("notification-detail", args=[value.id])).status_code
            == status
        )
    member = CompanyMembership.objects.get(company=company, user=user)
    member.is_active = False
    member.save()
    assert actor.get(reverse("notification-detail", args=[own.id])).status_code == 404


@pytest.mark.django_db
def test_document_collection_and_signed_download_are_role_bound(tenancy):
    import hashlib
    from django.urls import reverse
    from core_apps.features.models import RentalDocument

    actors, item = tenancy

    def document(kind):
        content = b"role-scoped-fixture-document"
        return RentalDocument.objects.create(
            lease=item.lease,
            requested_by=actors["owner"],
            document_type=kind,
            title="Synthetic document",
            status="ready",
            private_content=content,
            sha256=hashlib.sha256(content).hexdigest(),
        )

    contract, receipt = document("contract"), document("receipt")
    signer = client(actors["signer"], actors["company"], "signer")
    payer = client(actors["payer"], actors["company"], "payer")
    # Use canonical URL names; direct download checks are independent of UI.
    contract_url = reverse("rental-document-download", args=[contract.id])
    receipt_url = reverse("rental-document-download", args=[receipt.id])
    assert payer.get(contract_url).status_code == 404
    assert signer.get(receipt_url).status_code == 404
    response = signer.get(contract_url)
    assert response.status_code == 200
    from urllib.parse import urlsplit

    url = urlsplit(response.data["url"])
    assert client(actors["signer"]).get(url.path + "?" + url.query).status_code == 200
    item.signer_mandate.state = "revoked"
    item.signer_mandate.save()
    assert client(actors["signer"]).get(url.path + "?" + url.query).status_code == 404


def test_company_push_contains_no_financial_or_contract_content():
    from types import SimpleNamespace
    from core_apps.features.services.company.role_notifications import push_content

    title, body, data = push_content(
        SimpleNamespace(
            scope="company",
            title="Pay 100",
            body="Original terms",
            data={
                "company_id": "id",
                "company_role": "payer",
                "amount_minor": 100,
                "contract": "secret",
                "target_id": "invoice",
            },
        )
    )
    assert "100" not in title + body
    assert not {"amount_minor", "contract"} & data.keys()


@pytest.mark.django_db
def test_events_are_sent_only_to_the_responsibility_and_named_resident(tenancy):
    from core_apps.features.services.company.tenancy_events import record
    from core_apps.features.planning_models import PlanningEvent

    actors, item = tenancy
    people = [
        actors[name].pk
        for name in ("owner", "coordinator", "signer", "payer", "employee", "colleague")
    ]
    PlanningEvent.objects.filter(destination__target_id=str(item.id)).delete()
    record(item, people, "company_signature_requested", actor=actors["owner"])
    events = list(PlanningEvent.objects.filter(destination__target_id=str(item.id)))
    assert {e.destination["company_role"] for e in events} == {"owner", "signer"}
    assert all(
        not e.destination["actor_id"]
        for e in events
        if e.recipient_id != actors["owner"].pk
    )
    PlanningEvent.objects.filter(destination__target_id=str(item.id)).delete()
    assignment = item.preparation.booking.assignments.get(employee=actors["employee"])
    record(
        item,
        people,
        "company_employee_possession_proposed",
        metadata={"assignment_id": str(assignment.id)},
    )
    events = list(PlanningEvent.objects.filter(destination__target_id=str(item.id)))
    assert {e.destination["company_role"] for e in events} == {
        "owner",
        "coordinator",
        "employee",
    }
    assert {
        e.recipient_id for e in events if e.destination["company_role"] == "employee"
    } == {actors["employee"].pk}


@pytest.mark.django_db
def test_role_work_invoices_and_tasks_cannot_cross_roles(tenancy):
    actors, item = tenancy
    invoice = RentInvoice.objects.create(
        lease=item.lease,
        purpose="rent",
        amount_minor=125,
        charges_minor=125,
        due_date=timezone.localdate(),
        reference="ROLE-FEED",
    )
    base = API + f"companies/{actors['company'].id}/role-work/"
    payer = client(actors["payer"], actors["company"], "payer")
    response = payer.get(base, {"section": "invoices"})
    assert response.status_code == 200
    assert response.data["results"][0]["target_id"] == str(invoice.id)
    assert response.data["results"][0]["amount_minor"] == 125
    for actor, role in [
        ("coordinator", "admin"),
        ("coordinator", "coordinator"),
        ("signer", "signer"),
        ("employee", "employee"),
    ]:
        assert (
            client(actors[actor], actors["company"], role)
            .get(base, {"section": "invoices"})
            .status_code
            == 403
        )
    employee = client(actors["employee"], actors["company"], "employee")
    tasks = employee.get(base, {"section": "tasks"})
    assert tasks.status_code == 200
    assert "amount_minor" not in str(tasks.data)


@pytest.mark.django_db
def test_company_evidence_does_not_inherit_signer_or_payer_access(tenancy):
    from core_apps.features.models import RentalEvidence
    from core_apps.features.services.company.role_evidence import can_read
    from core_apps.features.services.company.role_context import bound_role
    import uuid

    actors, item = tenancy
    evidence = RentalEvidence.objects.create(
        lease=item.lease,
        uploader=actors["coordinator"],
        request_key=uuid.uuid4(),
        original_name="inspection.png",
        content_type="image/png",
        size_bytes=20,
        sha256="a" * 64,
        storage_key="role-evidence",
        media_metadata={"company_role": "coordinator"},
    )
    for name in ["coordinator", "payer", "signer", "employee"]:
        with bound_role(actors[name], actors["company"].id, name):
            assert can_read(evidence, actors[name]) is (name == "coordinator")
    with bound_role(actors["coordinator"], actors["company"].id, "admin"):
        assert not can_read(evidence, actors["coordinator"])


@pytest.mark.django_db
def test_resident_renewal_consent_keeps_own_role_without_contract_terms(tenancy):
    from core_apps.features.models import CompanyTenancyChange
    from core_apps.features.services.company.role_context import bound_role, narrow

    actors, item = tenancy
    change = CompanyTenancyChange.objects.create(
        tenancy=item,
        kind="renewal",
        proposed_by=actors["signer"],
        snapshot={
            "required": {
                "resident_0": str(actors["employee"].id),
                "resident_1": str(actors["colleague"].id),
            },
            "content": {
                "effective_on": str(item.lease.end_date),
                "ends_on_exclusive": "2027-12-01",
                "terms": {"rent": {"amount_minor": 918273}},
            },
        },
        snapshot_digest="role-consent",
    )
    with bound_role(actors["employee"], actors["company"].id, "employee"):
        assert narrow(actors["employee"], actors["company"], {"resident_0"}) == {
            "resident_0"
        }
    response = client(actors["employee"], actors["company"], "employee").get(
        API + f"company-tenancies/{item.id}/"
    )
    assert response.status_code == 200
    row = next(row for row in response.data["changes"] if row["id"] == str(change.id))
    assert row["roles_to_decide"] == ["resident_0"]
    assert row["content"]["ends_on_exclusive"] == "2027-12-01"
    assert "918273" not in str(response.data)
    assert str(actors["colleague"].id) not in str(response.data)


@pytest.mark.django_db
def test_employee_housing_does_not_disclose_colleague_unit_or_commerce(tenancy):
    actors, item = tenancy
    response = client(actors["employee"], actors["company"], "employee").get(
        API + f"company-tenancies/{item.id}/"
    )
    expected = set(
        item.preparation.booking.assignments.filter(
            employee=actors["employee"]
        ).values_list("property__id", flat=True)
    )
    assert {row["property_id"] for row in response.data["housing"]} == set(
        map(str, expected)
    )
    assert all(
        not {"price", "deposit", "owner", "terms"} & row.keys()
        for row in response.data["housing"]
    )


@pytest.mark.django_db
def test_case_links_cannot_restore_mixed_role_discussions(tenancy):
    from core_apps.features.services.rental_lifecycle.cases import (
        open_system_case,
        case_queryset,
    )
    from core_apps.features.services.company.role_context import bound_role

    actors, item = tenancy
    legacy = open_system_case(
        kind="company_tenancy_review",
        source_key="mixed-case",
        reason="Mixed historic discussion",
        next_action="Review",
        lease=item.lease,
        actor=actors["coordinator"],
        notify=False,
    )
    with bound_role(actors["coordinator"], actors["company"].id, "coordinator"):
        own = open_system_case(
            kind="company_tenancy_review",
            source_key="scoped-case",
            reason="Housing task",
            next_action="Review",
            lease=item.lease,
            actor=actors["coordinator"],
            notify=False,
        )
        assert not case_queryset(actors["coordinator"]).filter(pk=legacy.pk).exists()
        assert case_queryset(actors["coordinator"]).filter(pk=own.pk).exists()
    with bound_role(actors["coordinator"], actors["company"].id, "admin"):
        assert not case_queryset(actors["coordinator"]).filter(pk=own.pk).exists()
    with bound_role(actors["payer"], actors["company"].id, "payer"):
        assert not case_queryset(actors["payer"]).filter(pk=own.pk).exists()


@pytest.mark.django_db
def test_payment_export_does_not_inherit_admin_budget_records(tenancy):
    from core_apps.features.services.company.housing_report import payload
    from core_apps.features.services.company.role_context import bound_role

    actors, item = tenancy
    member = CompanyMembership.objects.get(
        user=actors["payer"], company=actors["company"]
    )
    member.is_admin = True
    member.save(update_fields=["is_admin"])
    with bound_role(actors["payer"], actors["company"].id, "payer"):
        report = payload(actors["payer"], actors["company"], {})
    assert not any(row["kind"].startswith("reserved_") for row in report["rows"])
