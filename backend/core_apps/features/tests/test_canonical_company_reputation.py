"""Canonical corporate parties, possession and current delegated review authority."""

from datetime import timedelta
from unittest.mock import patch
import pytest
from core_apps.features.tests.test_company_tenancy import (
    cycle,
    person,
    company_setup,
    rental_participants,
    policy,
    command,
    authenticated,
    API,
    agreement,
    signed_agreement,
    active_agreement,
    act,
    handover,
    presence,
    expose_unexpected_exceptions,
)
from core_apps.features.tests.test_company_continuations import (
    proposal,
    reviews,
    signatures,
)
from core_apps.features.tests.test_reputation import body
from core_apps.features.models import (
    CompanyLeaseBinding,
    CompanyReviewAuthority,
    CompanyMembership,
    ReviewOpportunity,
)
from core_apps.features.services.reputation import (
    generation,
    company_generation,
    eligibility,
)
from core_apps.features.services.reputation.policy import ReviewError
from core_apps.features.services.reputation.tasks import reconcile


def returned(cycle, item, *, employee=False):
    day = item.lease.start_date
    with patch("django.utils.timezone.localdate", return_value=day + timedelta(days=2)):
        handover(cycle, item, "move_in", day)
        if employee:
            row = item.preparation.booking.assignments.get(employee=cycle["employee"])
            presence(cycle, item, row, "arrival", day)
            presence(cycle, item, row, "departure", day + timedelta(days=2))
        handover(cycle, item, "move_out", day + timedelta(days=2))
    item.lease.refresh_from_db()
    return day + timedelta(days=2)


@pytest.mark.django_db
def test_company_pair_is_not_a_fake_person_and_requires_explicit_authority(
    active_agreement, settings
):
    settings.REVIEWS_ENABLED = True
    cycle, item = active_agreement
    day = returned(cycle, item)
    with patch("django.utils.timezone.localdate", return_value=day):
        counts = reconcile()
        assert counts["tenancies"] == 1
        case = generation.generate_tenancy(item.lease)
        assert case.party_a_id is None and case.company_id == cycle["company"].pk
        assert eligibility.valid_source(case)
        assert case.opportunities.count() == 2
        assert generation.generate_tenancy(item.lease).id == case.id
        company_opp = case.opportunities.get(reviewer_company=cycle["company"])
        assert not case.opportunities.filter(reviewer=cycle["coordinator"]).exists()
        path = API + f"reviews/opportunities/{company_opp.id}/submit/"
        denied = authenticated(cycle["coordinator"]).post(
            path, body(company_opp), format="json"
        )
        assert denied.status_code == 404
        binding = CompanyLeaseBinding.objects.get(lease=item.lease)
        member = CompanyMembership.objects.get(
            company=cycle["company"], user=cycle["coordinator"]
        )
        grant = authenticated(cycle["coordinator"]).post(
            API + f"reviews/company-bindings/{binding.id}/authorities/",
            command(
                membership_id=str(member.id),
                is_active=True,
                can_submit=True,
                can_view_reputation=True,
            ),
            format="json",
        )
        assert grant.status_code == 200, grant.data
        response = authenticated(cycle["coordinator"]).post(
            path, body(company_opp), format="json"
        )
        assert response.status_code == 201, response.data
        member.is_active = False
        member.save()
        denied = authenticated(cycle["coordinator"]).get(
            API + f"reviews/opportunities/{company_opp.id}/"
        )
        assert denied.status_code == 404


@pytest.mark.django_db
def test_company_employee_ballot_remains_independent(active_agreement):
    cycle, item = active_agreement
    day = returned(cycle, item, employee=True)
    row = item.preparation.booking.assignments.get(employee=cycle["employee"])
    with patch("django.utils.timezone.localdate", return_value=day):
        corporate = generation.generate_tenancy(item.lease)
        personal = company_generation.generate_employee(row)
        assert corporate.pk != personal.pk
        assert personal.party_a_id == row.employee_id
        assert personal.release_mode == "deadline"
        assert eligibility.valid_source(personal)
        assert personal.opportunities.get().reviewer_id == row.employee_id


@pytest.mark.django_db
def test_renewal_preserves_original_company_signatures_and_employee_arrival(
    active_agreement,
):
    cycle, item = active_agreement
    day = item.lease.start_date
    with patch("django.utils.timezone.localdate", return_value=day):
        handover(cycle, item, "move_in", day)
        row = item.preparation.booking.assignments.get(employee=cycle["employee"])
        presence(cycle, item, row, "arrival", day)
        original = dict(row.occupancy_confirmations.get(kind="arrival").source_snapshot)
        change = proposal(cycle, item)
        reviews(item, change)
        signatures(item, change)
    with patch("django.utils.timezone.localdate", return_value=day + timedelta(days=2)):
        row.refresh_from_db()
        presence(cycle, item, row, "departure", day + timedelta(days=2))
        handover(cycle, item, "move_out", day + timedelta(days=2))
        item.lease.refresh_from_db()
        corporate = generation.generate_tenancy(item.lease)
        personal = company_generation.generate_employee(row)
        assert eligibility.valid_source(corporate) and eligibility.valid_source(
            personal
        )
        assert (
            row.occupancy_confirmations.get(kind="arrival").source_snapshot == original
        )


@pytest.mark.django_db
def test_company_review_rejects_fabricated_possession_approval(active_agreement):
    cycle, item = active_agreement
    day = returned(cycle, item)
    change = item.changes.get(kind="move_out")
    change.decisions = {}
    change.save()
    with patch("django.utils.timezone.localdate", return_value=day), pytest.raises(
        ReviewError
    ):
        generation.generate_tenancy(item.lease)
    assert not ReviewOpportunity.objects.exists()


@pytest.mark.django_db
def test_signed_ownership_splits_company_experience_without_reassigning_history(
    active_agreement,
):
    from datetime import datetime, time
    from django.utils import timezone
    from core_apps.features.models import ReviewCase

    cycle, item = active_agreement
    day = item.lease.start_date
    with patch("django.utils.timezone.localdate", return_value=day):
        handover(cycle, item, "move_in", day)
    incoming = person("reputation-incoming-owner")
    for prop in cycle["units"]:
        prop.owner = incoming
        prop.is_ownership_verified = True
        prop.save()
    moment = timezone.make_aware(datetime.combine(day + timedelta(days=1), time(12)))
    # Synthetic mandates cover the deliberately advanced ownership date.
    for mandate in cycle["mandates"]:
        mandate.refresh_from_db()
        mandate.execution_verified_until = moment + timedelta(days=20)
        mandate.valid_until = moment + timedelta(days=30)
        mandate.save()
    with patch("django.utils.timezone.now", return_value=moment):
        result = act(
            item,
            cycle["owner"],
            "ownership_change",
            new_owner_id=str(incoming.id),
            reason="Verified signed transfer",
        )
        assert result.status_code == 200, result.data
        change = item.changes.get(kind="ownership")
        reviews(item, change)
        signatures(item, change)
    new_cycle = {**cycle, "owner": incoming}
    with patch("django.utils.timezone.localdate", return_value=day + timedelta(days=3)):
        handover(new_cycle, item, "move_out", day + timedelta(days=3))
        item.lease.refresh_from_db()
        generation.generate_tenancy(item.lease)
        cases = list(
            ReviewCase.objects.filter(company=cycle["company"]).order_by(
                "source_snapshot__starts_on"
            )
        )
        assert len(cases) == 2
        assert cases[0].party_b_id == cycle["owner"].pk
        assert cases[0].source_snapshot["ends_on"] == str(day + timedelta(days=1))
        assert cases[1].party_b_id == incoming.pk
        assert cases[1].source_snapshot["starts_on"] == str(day + timedelta(days=1))
        assert all(eligibility.valid_source(case) for case in cases)
        change.rental_change.signed_by = []
        change.rental_change.save()
        assert not eligibility.valid_source(cases[1])
