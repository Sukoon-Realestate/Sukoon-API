"""Request/value workflows over local PostgreSQL; fixture authority is synthetic."""

import uuid
import pytest
from core_apps.features.models import RentalOperationalCase, CompanyMembership
from core_apps.features.services.company import discovery, bookings
from .test_company_housing import company_setup, command, API
from .test_rental_phase2 import rental_participants, authenticated
from .test_rental_lifecycle import policy
from .test_rental_lifecycle_safety import operator
from .test_company_service_requests import case_action, assign

pytestmark = pytest.mark.django_db


def request_body(requirement, **changes):
    return command(
        **{
            **{key: getattr(requirement, key) for key in bookings.REQUEST_FIELDS},
            "expected_revision": requirement.revision,
            **changes,
        }
    )


def test_request_worksite_catalog_and_full_term_budget(company_setup):
    _, user, _, company, _, _, _, requirement = company_setup
    client = authenticated(user)
    body = request_body(
        requirement,
        project_code="SITE-10",
        worksite_latitude="30.044400",
        worksite_longitude="31.235700",
        requirements=["wifi", "furnished"],
    )
    result = client.post(
        API + f"company-housing-requests/{requirement.id}/", body, format="json"
    )
    assert result.status_code == 200, result.data
    data = result.data["resource"]
    assert data["project_code"] == "SITE-10"
    assert data["requirements"] == ["wifi", "furnished"]
    assert data["commitment_ceiling_minor"] == body["commitment_ceiling_minor"]
    assert data["deposit_limit_minor"] == body["deposit_limit_minor"]
    catalog = client.get(API + "company-requirements/")
    assert catalog.status_code == 200
    assert {"wifi", "furnished"} <= {
        row["value"] for row in catalog.data["requirements"]
    }


@pytest.mark.parametrize(
    "changes",
    [
        {"worksite_latitude": "30", "worksite_longitude": None},
        {"worksite_latitude": "91", "worksite_longitude": "31"},
        {"requirements": ["invented_service"]},
        {"requirements": ["wifi", "wifi"]},
    ],
)
def test_request_rejects_unsupported_structured_values(company_setup, changes):
    requirement = company_setup[-1]
    result = authenticated(company_setup[1]).post(
        API + f"company-housing-requests/{requirement.id}/",
        request_body(requirement, **changes),
        format="json",
    )
    assert result.status_code == 400, result.data


def test_request_suitability_preserves_unknowns_and_distance(company_setup):
    _, user, _, company, _, units, offer, requirement = company_setup
    requirement.worksite_latitude, requirement.worksite_longitude = 30, 31
    requirement.requirements = ["wifi"]
    requirement.save()
    for prop in units:
        prop.latitude, prop.longitude, prop.has_wifi = 30, 31, True
        prop.save()
    row = discovery.suitability(offer, requirement)
    assert row["full_term_rent_minor"] == offer.monthly_rent_minor
    assert row["locations"][0]["straight_line_km"] == 0
    assert row["meets_requirements"]
    assert row["quote_expires_at"] is None
    assert row["other_costs_status"] == "not_established"
    units[0].occupancy_capacity = None
    units[0].save()
    row = discovery.suitability(offer, requirement)
    assert row["capacity"] is None and "capacity_unknown" in row["suitability_reasons"]
    result = authenticated(user).get(
        API + "portfolio-offers/",
        {
            "company_id": str(company.id),
            "request_id": str(requirement.id),
            "suitable_only": "true",
        },
    )
    assert result.status_code == 200, result.data
    assert result.data["count"] == 0


def test_offer_over_budget_reasons_and_request_context(company_setup):
    _, user, _, company, _, _, offer, requirement = company_setup
    requirement.commitment_ceiling_minor = 0
    requirement.deposit_limit_minor = 0
    requirement.save()
    row = discovery.suitability(offer, requirement)
    assert {"rent_over_ceiling", "deposit_over_ceiling"} <= set(
        row["suitability_reasons"]
    )
    result = authenticated(user).get(
        API + "portfolio-offers/",
        {
            "company_id": str(uuid.uuid4()),
            "request_id": str(requirement.id),
        },
    )
    assert result.status_code == 404


def assistance(setup):
    requirement, user = setup[-1], setup[1]
    requirement.refresh_from_db()
    body = command(
        expected_revision=requirement.revision,
        reason="Help source suitable accommodation.",
    )
    url = API + f"company-housing-requests/{requirement.id}/assistance/"
    result = authenticated(user).post(url, body, format="json")
    assert result.status_code == 200, result.data
    assert authenticated(user).post(url, body, format="json").data == result.data
    return RentalOperationalCase.objects.get(housing_request=requirement), result


def test_assistance_deduplicates_and_never_reserves(company_setup):
    requirement = company_setup[-1]
    case, first = assistance(company_setup)
    assistance(company_setup)
    assert requirement.assistance_cases.count() == 1
    assert requirement.items.count() == 0
    assert first.data["resource"]["assistance_cases"][0]["id"] == str(case.id)
    result = case_action(case, company_setup[1], "withdraw_sourcing")
    assert result.status_code == 200, result.data
    case.refresh_from_db()
    assert case.status == "resolved" and case.resolution_code == "withdrawn"


def test_sourcing_operator_recommendation_revision_and_role_revocation(company_setup):
    _, user, _, company, _, _, offer, requirement = company_setup
    case, _ = assistance(company_setup)
    support = operator("support")
    assign(case, support)
    requirement.refresh_from_db()
    result = case_action(
        case,
        support,
        "recommend_offers",
        housing_request_revision=requirement.revision,
        recommended_offer_ids=[str(offer.id)],
    )
    assert result.status_code == 200, result.data
    assert result.data["resource"]["sourcing"]["offer_ids"] == [str(offer.id)]
    requirement.revision += 1
    requirement.save()
    stale = case_action(
        case, support, "resolve", resolution_code="recommendations_delivered"
    )
    assert stale.status_code == 409
    CompanyMembership.objects.filter(company=company, user=user).update(is_active=False)
    assert authenticated(user).get(API + f"rental-cases/{case.id}/").status_code == 404
    denied = case_action(
        case,
        support,
        "recommend_offers",
        housing_request_revision=requirement.revision,
        recommended_offer_ids=[str(offer.id)],
    )
    assert denied.status_code == 409


def test_sourcing_cannot_close_as_financial_result_or_be_reopened(company_setup):
    case, _ = assistance(company_setup)
    support = operator("support")
    assign(case, support)
    assert (
        case_action(case, support, "resolve", resolution_code="corrected").status_code
        == 400
    )
    result = case_action(case, support, "resolve", resolution_code="no_suitable_offer")
    assert result.status_code == 200
    assert case_action(case, support, "reopen").status_code == 400


def test_csv_preview_no_records_activation_or_privileged_roles(company_setup):
    _, user, approver, company, *_ = company_setup
    url = API + f"companies/{company.id}/staff-batches/import-preview/"
    text = 'display_name,work_email,employee_code\n"A, B",a@example.invalid,E1\nOther,a@example.invalid,E2\n'
    result = authenticated(user).post(url, {"csv_text": text}, format="json")
    assert result.status_code == 200, result.data
    assert result.data["rows"][0]["valid"]
    assert not result.data["rows"][1]["valid"]
    assert result.data["rows"][0]["values"]["roles"] == ["employee"]
    assert not company.staff_records.exists()
    assert not result.data["persisted"] and not result.data["activation_sent"]
    assert (
        authenticated(approver).post(url, {"csv_text": text}, format="json").status_code
        == 403
    )
    assert (
        authenticated(user)
        .post(
            url,
            {
                "csv_text": "display_name,work_email,roles\nA,a@example.invalid,admin",
            },
            format="json",
        )
        .status_code
        == 400
    )


@pytest.mark.parametrize(
    "text",
    [
        "display_name,work_email\n",
        "display_name,work_email,work_email\nA,a@b.test,a@b.test",
        "display_name,work_email\n" + "".join(f"A,a{i}@b.test\n" for i in range(51)),
        "display_name,work_email\nA,a@b.test,unexpected",
    ],
)
def test_csv_preview_rejects_unbounded_or_malformed_files(company_setup, text):
    result = authenticated(company_setup[1]).post(
        API + f"companies/{company_setup[3].id}/staff-batches/import-preview/",
        {"csv_text": text},
        format="json",
    )
    assert result.status_code == 400, result.data


def test_sourcing_admin_form_displays_requirements_and_commits_canonical_recommendation(
    company_setup, settings
):
    from django.test import Client
    from django.urls import reverse

    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    case, _ = assistance(company_setup)
    agent = operator("support")
    assign(case, agent)
    requirement, offer = company_setup[-1], company_setup[-2]
    requirement.refresh_from_db()
    case.refresh_from_db()
    client = Client()
    client.force_login(agent)
    queue = reverse("admin:features_rentaloperationalcase_changelist")
    assert client.get(queue).status_code == 200
    assert client.get(queue, {"q": "__no_matching_sourcing_case__"}).status_code == 200
    url = reverse("admin:features_rentaloperationalcase_change", args=[case.pk])
    page = client.get(url)
    assert page.status_code == 200 and b"sourcing_requirements" in page.content
    result = client.post(
        url,
        {
            "command_action": "recommend_offers",
            "decision_reason": "Reviewed exact current capacity and declared amenities",
            "housing_request_revision": requirement.revision,
            "recommended_offers": [str(offer.pk)],
            "expected_revision": case.revision,
            "request_key": str(uuid.uuid4()),
            "_save": "Save",
        },
    )
    assert result.status_code == 302
    case.refresh_from_db()
    assert case.status == "waiting_for_company"
    assert case.baseline["recommended_offer_ids"] == [str(offer.id)]
    assert requirement.items.count() == 0


@pytest.mark.django_db(transaction=True)
def test_concurrent_assistance_creates_one_case_and_rejects_stale_intent(company_setup):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import close_old_connections

    user, requirement = company_setup[1], company_setup[-1]
    barrier = Barrier(2)

    def submit(_):
        close_old_connections()
        try:
            body = command(
                expected_revision=requirement.revision, reason="Source accommodation"
            )
            barrier.wait(timeout=10)
            return (
                authenticated(user)
                .post(
                    API + f"company-housing-requests/{requirement.id}/assistance/",
                    body,
                    format="json",
                )
                .status_code
            )
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(submit, range(2))) == [200, 409]
    assert requirement.assistance_cases.count() == 1
    assert requirement.items.count() == 0


def test_csv_unterminated_header_is_rejected_without_server_error(company_setup):
    result = authenticated(company_setup[1]).post(
        API + f"companies/{company_setup[3].id}/staff-batches/import-preview/",
        {"csv_text": '"display_name,work_email\nA,a@b.test'},
        format="json",
    )
    assert result.status_code == 400
