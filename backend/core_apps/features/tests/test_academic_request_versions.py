"""One public request identity across consented academic requirement versions."""

import copy
import pytest
from core_apps.features.models import HousingRequest
from core_apps.features.tests.test_student_housing import (
    create_plan,
    requirements,
    review,
    publish,
)
from core_apps.features.tests import test_student_housing as fixtures

rental_participants = fixtures.rental_participants
student_capabilities = fixtures.student_capabilities


@pytest.mark.django_db
def test_republication_keeps_request_and_preserves_prior_disclosure(
    rental_participants,
):
    _, tenant, _, prop, _ = rental_participants
    plan = publish(
        tenant, review(tenant, requirements(tenant, create_plan(tenant, prop)))
    )
    original = HousingRequest.objects.get(academic_plan__id=plan["id"])
    snapshot = copy.deepcopy(original.academic_snapshot)
    updated = requirements(tenant, plan, internet="Current participant requirement")
    original.refresh_from_db()
    assert original.academic_snapshot == snapshot
    updated = publish(tenant, review(tenant, updated))
    current = HousingRequest.objects.get(academic_plan__id=plan["id"])
    assert current.id == original.id
    assert current.academic_revision == updated["requirements_revision"]
    assert current.content_revision == original.content_revision + 1
    change = current.changes.get()
    assert change.before["academic_snapshot"] == snapshot
    assert change.after["academic_revision"] == updated["requirements_revision"]
    assert "participant_ids" not in str(change.after["academic_snapshot"])


@pytest.mark.django_db
def test_republished_compatible_offer_requires_explicit_owner_confirmation(
    rental_participants,
):
    from core_apps.features.models import HousingOffer
    from core_apps.features.tests.test_student_journeys import (
        inventory,
        reviewed_plan,
        response_for,
        criteria_for,
    )

    owner, tenant, _, prop, offer_id = rental_participants
    inventory(prop)
    criteria = {**criteria_for(prop, 1), "rental_scope": "room"}
    plan = reviewed_plan(tenant, prop, [tenant], criteria=criteria)
    plan, offer, _ = response_for(owner, tenant, prop, plan, offer_id)
    original = HousingRequest.objects.get(academic_plan__id=plan["id"])
    # A new participant-reviewed version with the same accommodation requirements.
    plan = review(
        tenant, requirements(tenant, plan, study_space="Individual desk requested")
    )
    publish(tenant, plan)
    updated = HousingOffer.objects.get(id=offer["id"])
    assert updated.request_id == original.pk
    assert updated.review_state == "pending_reconfirm"
