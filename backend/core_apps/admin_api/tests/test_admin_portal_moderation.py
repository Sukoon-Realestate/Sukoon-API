import uuid
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from core_apps.admin_api.models import StaffProfile
from core_apps.properties.models import Property, PropertyModerationDecision
from core_apps.features.models import RentalAuditEvent
from core_apps.features.planning_models import PlanningEvent

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def property_moderator(django_user_model):
    u = django_user_model.objects.create_user(
        email="moderator@sukoon.com",
        password="ValidPassword123!",
        first_name="Property",
        last_name="Moderator",
        is_staff=True,
    )
    StaffProfile.objects.create(user=u, role_name="property_reviewer", is_active=True)
    return u


class TestAdminPortalModeration:
    def test_moderation_list_and_metrics(self, api_client, property_moderator, make_property):
        api_client.force_authenticate(user=property_moderator)
        owner = User.objects.create_user(email="owner_mod@test.com", password="Password123!")

        p1 = make_property(
            owner=owner,
            title="Flagged Listing 1",
            status=Property.Status.UNDER_REVIEW,
        )
        p2 = make_property(
            owner=owner,
            title="Flagged Listing 2",
            status=Property.Status.NEEDS_REVISION,
        )

        list_url = reverse("admin-moderation-list")
        res = api_client.get(list_url)
        assert res.status_code == status.HTTP_200_OK
        ids = [item["property_id"] for item in res.data["results"]]
        assert str(p1.id) in ids
        assert str(p2.id) in ids

        metrics_url = reverse("admin-moderation-metrics")
        m_res = api_client.get(metrics_url)
        assert m_res.status_code == status.HTTP_200_OK
        assert "suspiciousImages" in m_res.data
        assert "misleadingDesc" in m_res.data
        assert "phoneNumInPhotos" in m_res.data
        assert "inappropriateContent" in m_res.data

    def test_moderation_delete_canonical_invariants(self, api_client, property_moderator, make_property):
        api_client.force_authenticate(user=property_moderator)
        owner = User.objects.create_user(email="prop_owner@test.com", password="Password123!")
        prop = make_property(
            owner=owner,
            title="Inappropriate Content Listing",
            status=Property.Status.UNDER_REVIEW,
            is_verified=False,
        )

        delete_url = reverse("admin-moderation-delete", kwargs={"property_id": prop.id})
        res = api_client.post(delete_url)
        assert res.status_code == status.HTTP_200_OK
        assert "تم حذف المحتوى المخالف بنجاح" in res.data["message"]

        prop.refresh_from_db()
        assert prop.status == Property.Status.HIDDEN
        assert not prop.is_verified
        assert prop.moderation_blocked is True

        # Invariant 1: PropertyModerationDecision created
        decision = PropertyModerationDecision.objects.filter(property=prop, action="block").first()
        assert decision is not None
        assert decision.reviewer == property_moderator

        # Invariant 2: RentalAuditEvent created
        audit_event = RentalAuditEvent.objects.filter(subject_id=prop.id, action="property.moderation.block").first()
        assert audit_event is not None
        assert audit_event.actor == property_moderator

        # Invariant 3: PlanningEvent created for owner
        planning = PlanningEvent.objects.filter(recipient=owner, event_key=f"property.moderation:{decision.id}").first()
        assert planning is not None

    def test_moderator_cannot_moderate_own_property(self, api_client, property_moderator, make_property):
        api_client.force_authenticate(user=property_moderator)
        own_prop = make_property(
            owner=property_moderator,
            title="My Own Listing",
            status=Property.Status.UNDER_REVIEW,
        )

        delete_url = reverse("admin-moderation-delete", kwargs={"property_id": own_prop.id})
        res = api_client.post(delete_url)
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert "independent moderation" in str(res.data).lower()

    def test_non_reviewer_cannot_delete(self, api_client, make_property):
        ordinary_user = User.objects.create_user(email="ordinary@test.com", password="Password123!")
        api_client.force_authenticate(user=ordinary_user)

        owner = User.objects.create_user(email="other_owner@test.com", password="Password123!")
        prop = make_property(
            owner=owner,
            title="Listing",
            status=Property.Status.UNDER_REVIEW,
        )

        delete_url = reverse("admin-moderation-delete", kwargs={"property_id": prop.id})
        res = api_client.post(delete_url)
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_nonexistent_property_returns_404(self, api_client, property_moderator):
        api_client.force_authenticate(user=property_moderator)
        delete_url = reverse("admin-moderation-delete", kwargs={"property_id": uuid.uuid4()})
        res = api_client.post(delete_url)
        assert res.status_code == status.HTTP_404_NOT_FOUND
