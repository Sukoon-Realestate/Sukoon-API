"""Student recipients keep their own membership and original response identity."""

# flake8: noqa: F401,F811
import pytest
from rest_framework.exceptions import NotFound
from .test_student_housing import group, student_capabilities
from .test_rental_phase2 import rental_participants
from .test_student_journeys import inventory, reviewed_plan, response_for
from core_apps.properties.tests.test_viewing_listing_changes import edit_offer
from core_apps.features.planning_models import PlanningEvent, HousingOffer
from core_apps.features.services.housing_request_notifications import notification_copy

pytestmark = pytest.mark.django_db


def test_source_change_notifies_current_students_without_private_requirements(
    rental_participants, group
):
    owner, tenant, member, prop, _ = rental_participants
    base_id, _ = inventory(prop, people=2)
    plan = reviewed_plan(tenant, prop, [tenant, member], group=group)
    _, response, _ = response_for(owner, tenant, prop, plan, base_id)
    edit_offer(prop, availability="unavailable")
    events = list(
        PlanningEvent.objects.filter(
            destination__event_kind="housing_offer_source_changed"
        )
    )
    assert {row.recipient_id: row.destination["workspace"] for row in events} == {
        owner.pk: "owner",
        tenant.pk: "student",
        member.pk: "student",
    }
    assert all(row.destination["housing_offer_id"] == response["id"] for row in events)
    assert not any("requirements" in str(row.destination) for row in events)
    row = next(row for row in events if row.recipient_id == member.pk)
    assert notification_copy(row)
    group.memberships.filter(user=member).update(status="left")
    with pytest.raises(NotFound):
        notification_copy(row)
    assert len(HousingOffer.objects.get(id=response["id"]).source_changes) == 1
