"""Student discovery and progression against real local persistence, no providers."""

from datetime import timedelta
import pytest
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIClient
from core_apps.properties.models import Property
from core_apps.properties.filters import PropertyFilter
from core_apps.features.models import (
    Campus,
    University,
    RentalInventoryDayLock,
    RentalInventoryUnit,
    AcademicHousingPlan,
)
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from core_apps.features.services.rental_lifecycle.decisions import decision_summary
from .test_student_housing import (
    API,
    student_capabilities,
    rental_participants,
    group,
    create_plan,
    requirements,
    review,
    read,
    post,
)
from .test_rental_phase2 import authenticated
from .test_rental_lifecycle import command

pytestmark = pytest.mark.django_db


def search(prop, **values):
    query = {"student_search": "true", "price_period": "monthly", **values}
    filters = PropertyFilter(query, queryset=Property.objects.filter(pk=prop.pk))
    assert filters.is_valid(), filters.errors
    return list(filters.qs)


def test_guest_catalog_does_not_require_planning_or_disclose_profiles(
    rental_participants, settings
):
    _, tenant, _, prop, _ = rental_participants
    university = University.objects.create(name_en="University", name_ar="University")
    campus = Campus.objects.create(
        university=university, city=prop.city, name_en="Campus"
    )
    settings.STUDENT_ENABLED_SERVICES = []
    response = APIClient().get(API + "campuses/")
    assert response.status_code == 200
    assert response.data["results"][0]["id"] == str(campus.id)
    assert "student_profile" not in str(response.data)
    assert APIClient().get(API + "student-profile/").status_code in {401, 403}


def test_search_prices_use_selected_scope_and_explicit_basis(rental_participants):
    _, _, _, prop, _ = rental_participants
    assert search(
        prop,
        rental_scope="entire_property",
        price_max="6000",
        student_people=2,
        budget_basis="per_person",
    )
    assert not search(
        prop, price_max="6000", student_people=2, budget_basis="whole_group"
    )
    assert not search(prop, price_min="11000", budget_basis="whole_group")
    assert (
        PropertyFilter(
            {"price_max": "6000"}, queryset=Property.objects.all()
        ).qs.count()
        == 0
    )


def test_search_is_read_only_and_conflicts_with_canonical_whole_inventory(
    rental_participants,
):
    _, _, _, prop, offer_id = rental_participants
    start = timezone.localdate() + timedelta(days=10)
    end = start + timedelta(days=45)
    args = {"available_from": str(start), "available_until": str(end)}
    assert search(prop, **args)
    assert not RentalInventoryUnit.objects.exists()
    unit = RentalInventoryUnit.objects.create(
        property=prop, physical_key=f"property:{prop.id}", topology_digest="test"
    )
    RentalInventoryDayLock.objects.create(
        property=prop, unit=unit, stay_on=start, kind="occupied"
    )
    assert not search(prop, **args)
    # Half-open boundary: another stay can begin at the queried departure date.
    RentalInventoryDayLock.objects.update(stay_on=end)
    assert search(prop, **args)
    assert RentalInventoryDayLock.objects.count() == 1


def test_expired_but_unreconciled_hold_is_not_released_by_search(rental_participants):
    _, _, _, prop, _ = rental_participants
    day = timezone.localdate() + timedelta(days=10)
    unit = RentalInventoryUnit.objects.create(
        property=prop, physical_key=f"property:{prop.id}", topology_digest="test"
    )
    RentalInventoryDayLock.objects.create(
        property=prop,
        unit=unit,
        stay_on=day,
        kind="hold",
        expires_at=timezone.now() - timedelta(minutes=1),
    )
    assert not search(
        prop, available_from=str(day), available_until=str(day + timedelta(days=40))
    )
    assert RentalInventoryDayLock.objects.count() == 1


def test_http_search_and_stale_campus_validation(rental_participants):
    _, _, _, prop, _ = rental_participants
    university = University.objects.create(name_en="University", name_ar="University")
    campus = Campus.objects.create(
        university=university, city=prop.city, name_en="Campus"
    )
    query = {
        "student_search": "true",
        "campus_id": str(campus.id),
        "student_people": 2,
        "price_max": 6000,
    }
    response = APIClient().get(reverse("property-list"), query)
    assert response.status_code == 200, response.data
    assert response.data["count"] == 1
    assert response.data["student_search_version"] == 1
    campus.active = False
    campus.save()
    assert APIClient().get(reverse("property-list"), query).status_code == 400


def test_eligibility_is_explained_without_private_evidence_or_false_zero(
    rental_participants,
):
    owner, tenant, _, prop, offer_id = rental_participants
    start = timezone.localdate() + timedelta(days=10)
    post(
        owner,
        f"properties/{prop.id}/student-policies/",
        command(
            offer_id=offer_id,
            offer_revision=2,
            eligibility="current_enrollment",
            period_kinds=["semester"],
            starts_on=str(start),
            ends_on_exclusive=str(start + timedelta(days=150)),
            expires_at=(timezone.now() + timedelta(days=2)).isoformat(),
        ),
    )
    decision = decision_summary(
        prop, {"offer_id": offer_id, "offer_revision": 2}, tenant
    )
    assert decision["student_eligibility"]["state"] == "verification_required"
    assert (
        decision_summary(prop, {"offer_id": offer_id, "offer_revision": 2}, owner)[
            "student_eligibility"
        ]["state"]
        == "owner_review"
    )
    assert "evidence_id" not in str(decision["student_eligibility"])
    assert decision["complete_total"] is False
    assert (
        next(row for row in decision["lines"] if row["code"] == "deposit")["amount"]
        is None
    )
    decision = decision_summary(
        prop,
        {
            "offer_id": offer_id,
            "offer_revision": 2,
            "starts_on": start,
            "ends_on_exclusive": start + timedelta(days=151),
        },
        tenant,
    )
    assert decision["student_eligibility"]["state"] == "dates_unavailable"


def test_next_step_tracks_each_person_and_preserves_consent(rental_participants, group):
    _, tenant, member, prop, _ = rental_participants
    plan = create_plan(tenant, prop, group=group, people=[tenant, member])
    assert plan["next_step"]["action"] == "requirements"
    plan = requirements(tenant, plan)
    assert plan["next_step"]["action"] == "review"
    plan = review(tenant, plan)
    assert plan["next_step"]["waiting_for"] == "participants"
    other = read(member, plan["id"])
    assert other["next_step"]["action"] == "requirements"
    plan = requirements(member, other)
    plan = review(member, plan)
    # Requirements revision changes invalidate earlier approval.
    assert read(tenant, plan["id"])["next_step"]["action"] == "review"
    review(tenant, read(tenant, plan["id"]))
    assert read(tenant, plan["id"])["next_step"]["action"] == "browse"


def test_completed_plan_is_not_a_rental_closure(rental_participants):
    _, tenant, _, prop, _ = rental_participants
    plan = create_plan(tenant, prop)
    plan = post(
        tenant, f"academic-plans/{plan['id']}/complete/", command(plan["revision"])
    ).data["resource"]
    assert plan["next_step"]["reason"] == "plan_only_completed"
    assert AcademicHousingPlan.objects.get(id=plan["id"]).status == "completed"


def test_exact_requested_end_survives_retry_without_creating_a_plan(
    rental_participants,
):
    _, tenant, _, prop, offer_id = rental_participants
    start = timezone.localdate() + timedelta(days=10)
    body = command(
        property_id=str(prop.id),
        offer_id=offer_id,
        offer_revision=2,
        desired_start=str(start),
        desired_end=str(start + timedelta(days=45)),
        months=1,
        occupants=1,
    )
    first = authenticated(tenant).post(API + "rental-interests/", body, format="json")
    assert first.status_code == 201, first.data
    again = authenticated(tenant).post(API + "rental-interests/", body, format="json")
    assert again.data["resource"]["id"] == first.data["resource"]["id"]
    assert first.data["resource"]["desired_end"] == body["desired_end"]
    assert not AcademicHousingPlan.objects.exists()
    invalid = {**body, **command(), "desired_end": str(start + timedelta(days=3))}
    assert (
        authenticated(tenant)
        .post(API + "rental-interests/", invalid, format="json")
        .status_code
        == 400
    )


def test_student_order_and_summary_use_matching_offer_not_legacy_price(
    rental_participants,
):
    import copy
    import uuid

    owner, _, _, prop, _ = rental_participants
    inventory = copy.deepcopy(prop.rental_inventory)
    inventory["offers"][0]["id"] = str(uuid.uuid4())
    inventory["offers"][0]["terms"]["price"] = "8000"
    cheaper = Property.objects.create(
        owner=owner,
        title="Cheaper canonical rent",
        price=20000,
        property_type=prop.property_type,
        city=prop.city,
        governorate=prop.governorate,
        status=Property.Status.VERIFIED,
        rental_inventory=inventory,
    )
    query = {
        "student_search": "true",
        "student_people": 2,
        "price_max": "6000",
        "ordering": "price",
    }
    response = APIClient().get(reverse("property-list"), query)
    assert response.status_code == 200, response.data
    rows = response.data["results"]
    assert [row["id"] for row in rows] == [str(cheaper.id), str(prop.id)]
    assert rows[0]["rental_summary"]["price"] == "8000.00"
    assert rows[0]["rental_summary"]["price_scope"] == "entire_property"
    assert rows[0]["rental_summary"]["price_period"] == "monthly"
    ordinary = APIClient().get(reverse("property-list"), {"ordering": "price"})
    assert [row["id"] for row in ordinary.data["results"]] == [
        str(prop.id),
        str(cheaper.id),
    ]


def test_student_search_detects_short_stay_and_invalid_dates_before_request(
    rental_participants,
):
    _, _, _, prop, _ = rental_participants
    start = timezone.localdate() + timedelta(days=5)
    assert not search(
        prop, available_from=str(start), available_until=str(start + timedelta(days=4))
    )
    for params in [
        {"available_from": str(start), "available_until": str(start)},
        {"available_until": str(start)},
        {"student_people": 0},
        {"price_period": "daily"},
    ]:
        response = APIClient().get(
            reverse("property-list"), {"student_search": "true", **params}
        )
        assert response.status_code == 400, response.data


def test_search_excludes_restricted_inventory_without_mutating_policy(
    rental_participants,
):
    _, _, _, prop, _ = rental_participants
    prop.retired_at = timezone.now()
    prop.status = Property.Status.HIDDEN
    prop.save(update_fields=["retired_at", "status"])
    assert not search(prop)
    prop.refresh_from_db()
    assert prop.retired_at is not None


def test_requested_dates_do_not_accept_conflicting_months_or_stale_plan(
    rental_participants,
):
    _, tenant, _, prop, offer_id = rental_participants
    start = timezone.localdate() + timedelta(days=10)
    response = authenticated(tenant).post(
        API + "rental-interests/",
        command(
            property_id=str(prop.id),
            offer_id=offer_id,
            offer_revision=2,
            desired_start=str(start),
            desired_end=str(start + timedelta(days=45)),
            months=3,
            occupants=1,
        ),
        format="json",
    )
    assert response.status_code == 400
    plan = create_plan(tenant, prop)
    plan = requirements(tenant, plan)
    plan = review(tenant, plan)
    response = authenticated(tenant).post(
        API + "rental-interests/",
        command(
            property_id=str(prop.id),
            offer_id=offer_id,
            offer_revision=2,
            desired_start=plan["starts_on"],
            months=1,
            occupants=1,
            academic_plan_id=plan["id"],
            academic_revision=plan["requirements_revision"] - 1,
        ),
        format="json",
    )
    assert response.status_code == 409


def test_current_tenancy_does_not_hide_next_future_planning_step(rental_participants):
    from core_apps.features.services.student_housing.progress import next_step

    _, tenant, _, prop, _ = rental_participants
    plan = create_plan(tenant, prop)
    payload = {**plan, "current_lease_id": "old-tenancy-still-binding"}
    assert (
        next_step(AcademicHousingPlan.objects.get(id=plan["id"]), tenant, payload)[
            "action"
        ]
        == "requirements"
    )
