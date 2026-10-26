"""Visit requests need notes only; the parties agree on timing in chat."""

from .viewing_support import response_body

import uuid
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from core_apps.properties.models import PropertyVisit, OwnerAvailabilitySlot
from .test_mobile_api_updates import create_property

pytestmark = pytest.mark.django_db


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.parametrize("note", ["", "أرغب في معاينة الغرفة والتواصل لتنسيق الزيارة"])
@pytest.mark.parametrize("decision", ["accept", "reject"])
def test_request_notes_owner_decision_and_chat(
    user, another_user, apartment_type, note, decision
):
    prop = create_property(another_user, apartment_type)
    tenant = client_for(user)
    owner = client_for(another_user)
    key = str(uuid.uuid4())
    url = reverse("property-visit-create", kwargs={"property_id": prop.id})
    created = tenant.post(url, {"note": note}, format="json", HTTP_IDEMPOTENCY_KEY=key)
    assert created.status_code == 201, created.data
    visit = PropertyVisit.objects.get()
    assert visit.note == note and visit.visit_date is None and visit.visit_time is None
    assert visit.status == "pending" and not OwnerAvailabilitySlot.objects.exists()
    assert (
        tenant.post(
            url, {"note": note}, format="json", HTTP_IDEMPOTENCY_KEY=key
        ).status_code
        == 201
    )
    assert PropertyVisit.objects.count() == 1
    detail_url = reverse("owner-visit-request-detail", kwargs={"id": visit.id})
    detail = owner.get(detail_url).json()["data"]
    assert detail["note"] == note
    assert not {"day_label", "time_label", "visit_date", "visit_time"} & detail.keys()
    assert (
        detail["actions"]["can_accept"]
        and detail["actions"]["can_reject"]
        and not detail["actions"]["can_chat"]
    )
    action_url = reverse(f"owner-visit-request-{decision}", kwargs={"id": visit.id})
    result = owner.post(
        action_url,
        response_body(
            visit.revision,
            **({"reason": "visit_unavailable"} if decision == "reject" else {}),
        ),
        format="json",
    )
    assert result.status_code == 200, result.data
    visit.refresh_from_db()
    assert visit.status == ("confirmed" if decision == "accept" else "rejected")
    tenant_detail = tenant.get(
        reverse("tenant-visit-request-detail", kwargs={"id": visit.id})
    ).json()["data"]
    assert tenant_detail["actions"]["can_chat"] == (decision == "accept")
    assert tenant_detail["note"] == note
    assert (
        not {"day_label", "time_label", "visit_date", "visit_time"}
        & tenant_detail.keys()
    )
    assert owner.get(detail_url).json()["data"]["actions"]["can_chat"] == (
        decision == "accept"
    )


def test_duplicate_request_and_note_limit(user, another_user, apartment_type):
    prop = create_property(another_user, apartment_type)
    tenant = client_for(user)
    url = reverse("property-visit-create", kwargs={"property_id": prop.id})
    assert tenant.post(url, {"note": "a" * 1001}, format="json").status_code == 400
    assert tenant.post(url, {}, format="json").status_code == 201
    assert tenant.post(url, {}, format="json").status_code == 400
    assert PropertyVisit.objects.count() == 1
    visit = PropertyVisit.objects.get()
    tenant.post(
        reverse("property-visit-cancel", kwargs={"id": visit.id}),
        response_body(visit.revision),
        format="json",
    )
    assert tenant.post(url, {}, format="json").status_code == 201


def test_personal_and_group_requests_do_not_block_each_other(
    user, another_user, apartment_type
):
    from core_apps.features.planning_models import HousingGroup, GroupProcess
    from core_apps.properties.services import PropertyVisitService
    from rest_framework.exceptions import ValidationError

    prop = create_property(another_user, apartment_type)
    personal = PropertyVisitService.create_visit(user, prop, {"note": "Personal"})
    group = HousingGroup.objects.create(name="Visiting group")
    grouped = PropertyVisitService.create_visit(
        user, prop, {"note": "Group"}, group=group
    )
    GroupProcess.objects.create(
        group=group,
        property=prop,
        initiated_by=user,
        kind="visit",
        roster_revision=group.roster_revision,
        visit=grouped,
    )
    assert personal.context_kind == "personal" and grouped.context_kind == "group"
    with pytest.raises(ValidationError):
        PropertyVisitService.create_visit(
            user, prop, {"note": "Duplicate"}, group=group
        )
    other = HousingGroup.objects.create(name="Other group")
    assert (
        PropertyVisitService.create_visit(user, prop, {}, group=other).context_kind
        == "group"
    )
