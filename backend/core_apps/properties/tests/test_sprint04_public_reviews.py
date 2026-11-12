"""Mixed public review pagination stays SQL-bounded and excludes stale sources."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.urls import reverse
from django.utils import timezone

from core_apps.features.models import ReviewCase, ReviewOpportunity, ReviewSubmission, ReviewSection
from core_apps.features.services.reputation.visibility import subject_rows
from core_apps.properties.models import PropertyVisit, PropertyVisitDecision, PropertyVisitReview
from core_apps.properties.services.public_review_reads import public_visit_sections
from core_apps.properties.tests.test_views import _create_property
from tools.qa.performance import measured

pytestmark = pytest.mark.django_db


def section(prop, owner, tenant, *, context="viewing", score=5):
    now = timezone.now()
    visit = PropertyVisit.objects.create(property=prop, tenant=tenant, status="confirmed")
    decision = PropertyVisitDecision.objects.create(
        visit=visit,
        tenant=tenant,
        owner=owner,
        value="proceed",
        attested_at=now,
        visit_revision=visit.revision,
        request_key=uuid4(),
        property_id_snapshot=prop.id,
    )
    case = ReviewCase.objects.create(
        experience_key=str(uuid4()),
        context_type=context,
        property=prop,
        party_a=tenant,
        party_b=owner,
        visit=visit,
        source_snapshot={"decision_id": str(decision.id)},
        eligible_recorded_at=now,
        opens_at=now - timedelta(days=3),
        closes_at=now - timedelta(days=1),
    )
    opportunity = ReviewOpportunity.objects.create(case=case, reviewer=tenant, reviewer_role="tenant")
    submission = ReviewSubmission.objects.create(
        opportunity=opportunity, acting_user=tenant, request_key=str(uuid4()), payload_hash="synthetic"
    )
    item = ReviewSection.objects.create(
        submission=submission,
        target_key="property",
        subject_kind="property_visit",
        subject_id=prop.id,
        audience="public",
        overall_score=score,
        original_comment="Synthetic",
        public_comment="Synthetic",
        content_state="approved",
        verification_basis="confirmed_viewing",
    )
    return item, case, visit, decision


def legacy(prop, tenant):
    visit = PropertyVisit.objects.create(property=prop, tenant=tenant, status="confirmed")
    return PropertyVisitReview.objects.create(
        visit=visit,
        overall_rating=4,
        cleanliness_rating=4,
        listing_accuracy_rating=4,
        owner_interaction_rating=4,
        comment="Historical",
    )


@pytest.mark.parametrize("size", [1, 10, 100])
def test_public_review_page_uses_sql_union_before_projection(size, user, another_user, auth_client):
    prop = _create_property(owner=user)
    ids = []
    timestamp = timezone.now() - timedelta(days=2)
    for _ in range(size):
        row, _, _, _ = section(prop, user, another_user)
        old = legacy(prop, another_user)
        ReviewSection.objects.filter(pk=row.pk).update(created_at=timestamp)
        PropertyVisitReview.objects.filter(pk=old.pk).update(created_at=timestamp)
        ids.extend([str(row.id), str(old.id)])
    response, report = measured(
        "public-property-reviews",
        size,
        lambda: auth_client.get(reverse("property-review-list", kwargs={"property_id": prop.id}), {"page_size": 5}),
    )
    assert response.status_code == 200
    assert response.data["count"] == 2 * size
    assert [row["id"] for row in response.data["results"]] == sorted(ids, reverse=True)[:5]
    assert response.data["summary"] == {"total_reviews": size, "average_rating": 5.0, "context_type": "viewing"}
    assert all(row["reviewer"] == {"name": "", "avatar": ""} for row in response.data["results"])
    assert report["queries"] <= 6
    assert report["http_calls"] == 0
    assert response["Cache-Control"] == "private, no-store"


@pytest.mark.parametrize(
    "change",
    [
        "unreleased",
        "revoked",
        "private",
        "pending",
        "visit_cancelled",
        "future_revision",
        "wrong_decision",
        "wrong_property",
        "owner_changed",
    ],
)
def test_sql_source_rules_match_existing_current_visibility(change, user, another_user):
    prop = _create_property(owner=user)
    item, case, visit, decision = section(prop, user, another_user)
    assert list(public_visit_sections(prop.id).values_list("pk", flat=True)) == [item.pk]
    if change == "unreleased":
        case.closes_at = timezone.now() + timedelta(days=1)
        case.save()
    elif change == "revoked":
        case.revocation_reason = "Source revoked"
        case.save()
    elif change in {"private", "pending"}:
        setattr(item, "audience" if change == "private" else "content_state", change)
        item.save()
    elif change == "visit_cancelled":
        PropertyVisit.objects.filter(pk=visit.pk).update(status="cancelled")
    elif change == "future_revision":
        PropertyVisitDecision.objects.filter(pk=decision.pk).update(visit_revision=visit.revision + 1)
    elif change == "wrong_decision":
        case.source_snapshot = {"decision_id": str(uuid4())}
        case.save()
    elif change == "wrong_property":
        PropertyVisitDecision.objects.filter(pk=decision.pk).update(property_id_snapshot=uuid4())
    else:
        # Keep the historical decision owner, but change the case's source party.
        from core_apps.users.models import User

        case.party_b = User.objects.create_user(email="other-review-owner@example.invalid", password=None)
        case.save()
    expected = {row.pk for row in subject_rows("property_visit", prop.id)}
    actual = set(public_visit_sections(prop.id).values_list("pk", flat=True))
    assert actual == expected == set()


def test_imported_legacy_is_not_duplicated_and_does_not_enter_verified_summary(user, another_user, auth_client):
    prop = _create_property(owner=user)
    old = legacy(prop, another_user)
    item, _, _, _ = section(prop, user, another_user, context="legacy", score=4)
    item.legacy_source, item.legacy_id, item.verification_basis = "property_visit_review", old.id, "legacy_unverified"
    item.save()
    response = auth_client.get(reverse("property-review-list", kwargs={"property_id": prop.id}))
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == str(item.id)
    assert response.data["summary"]["average_rating"] is None
    assert response.data["summary"]["total_reviews"] == 0


def test_summary_rounds_half_up_without_binary_average_errors(user, another_user, auth_client):
    prop = _create_property(owner=user)
    for score in [5] * 3 + [4] * 17:
        section(prop, user, another_user, score=score)
    response = auth_client.get(reverse("property-review-list", kwargs={"property_id": prop.id}))
    assert response.status_code == 200
    assert response.data["summary"]["average_rating"] == 4.2
    assert response.data["summary"]["total_reviews"] == 20


def test_exceptional_historical_context_keeps_its_existing_source_validator(settings):
    from core_apps.features.tests.test_reputation import actors as actors_fixture, stay
    from core_apps.features.services.reputation import generation

    actors = actors_fixture.__wrapped__(None, settings)
    owner, tenant, *_, prop = actors
    case = generation.generate_tenancy(stay(actors))
    case.gate_released_at = timezone.now()
    case.save()
    opportunity = case.opportunities.get(reviewer=tenant)
    submission = ReviewSubmission.objects.create(
        opportunity=opportunity, acting_user=tenant, request_key=str(uuid4()), payload_hash="synthetic"
    )
    item = ReviewSection.objects.create(
        submission=submission,
        target_key="historical-property",
        subject_kind="property_visit",
        subject_id=prop.id,
        audience="public",
        overall_score=4,
        content_state="approved",
        verification_basis="historical_confirmed",
    )
    assert {row.pk for row in subject_rows("property_visit", prop.id)} == {item.pk}
    assert set(public_visit_sections(prop.id).values_list("pk", flat=True)) == {item.pk}
    case.revocation_reason = "Source withdrawn"
    case.save()
    assert not public_visit_sections(prop.id).exists()
