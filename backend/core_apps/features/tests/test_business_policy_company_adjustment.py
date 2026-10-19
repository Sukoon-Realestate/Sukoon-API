"""Accepted policy is carried from package to contract and late correction case."""

import pytest
from datetime import timedelta
from django.utils import timezone
from core_apps.features.tests.test_business_policies import policy_admin, body
from core_apps.features.tests.test_company_continuations import (
    cycle,
    company_setup,
    rental_participants,
    policy,
    agreement,
    signed_agreement,
    active_agreement,
    expose_unexpected_exceptions,
    test_settlement_adjustment_additive_independent_and_replay_safe as exercise_adjustment,
)
from core_apps.features.services import business_policies as policies
from core_apps.features.services.company import tenancy_adjustments
from core_apps.features.models import FinalSettlement, RentalOperationalCase

pytestmark = pytest.mark.django_db


def test_exact_package_policy_survives_later_publication_and_opens_late_review(
    policy_admin, request, monkeypatch
):
    original_policy = body("D09", late_review_days=30)
    policies.publish(policy_admin, original_policy)
    cycle, tenancy = request.getfixturevalue("active_agreement")
    accepted = policies.bound(tenancy.lease.terms, "D09")
    assert accepted["version"] == original_policy["version"]
    policies.publish(policy_admin, body("D09", revision=1, late_review_days=365))
    from core_apps.features.services.company import tenancy_closure

    original_execute = tenancy_closure.execute_settlement

    def historical_settlement(item):
        result = original_execute(item)
        if isinstance(item, FinalSettlement):
            FinalSettlement.objects.filter(pk=item.pk).update(
                executed_at=timezone.now() - timedelta(days=31)
            )
        return result

    monkeypatch.setattr(tenancy_closure, "execute_settlement", historical_settlement)
    exercise_adjustment((cycle, tenancy))
    cases = RentalOperationalCase.objects.filter(
        lease=tenancy.lease, source_key__startswith="late-company-adjustment:"
    )
    assert cases.count() == 1
    assert "elapsed time" in cases.get().next_action.lower()
    change = tenancy.changes.get(kind="settlement_adjustment")
    assert (
        change.snapshot["content"]["correction_policy"]["version"]
        == original_policy["version"]
    )
    assert str(change.id) in cases.get().source_key
