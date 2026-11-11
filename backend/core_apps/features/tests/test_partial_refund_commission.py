"""A4-01 failing-before case: a partial rent refund after commission is earned must account additively.

After evaluate_owner_payables() records the immutable `commission-earned:{payable}` source,
execute_refund() re-evaluates payables and tries to post that same source with the reduced
commission, which previously raised financial_source_conflict. Sprint 03 keeps the original
recognition and posts the reversal additively; this is now an ordinary regression test.
"""

import pytest

from core_apps.features.models import LedgerTransaction, OwnerPayable
from .test_current_cycle_contract import awaiting_signatures  # noqa: F401
from .test_funded_settlement import approved_refund, funded_exit  # noqa: F401
from .test_rental_phase2 import rental_participants  # noqa: F401


@pytest.mark.django_db
@pytest.mark.mvp_deferred  # funded rental cycle is an MVP-deferred workflow
def test_partial_rent_refund_after_commission_recognition_is_additive(funded_exit):  # noqa: F811
    from core_apps.features.rental_phase4_views import evaluate_owner_payables

    _, tenant, _, lease, attempt = funded_exit
    evaluate_owner_payables(lease)
    payable = OwnerPayable.objects.get(payment_attempt=attempt)
    earned = LedgerTransaction.objects.get(reference=f"commission-earned:{payable.id}")
    original = list(earned.entries.values_list("account", "direction", "amount_minor"))

    refund = approved_refund(tenant, lease, attempt, 200_000, 0)  # before any owner payout

    refund.refresh_from_db()
    assert refund.status == "succeeded"
    earned.refresh_from_db()
    assert list(earned.entries.values_list("account", "direction", "amount_minor")) == original
    assert LedgerTransaction.objects.filter(reference=f"commission-earned:{payable.id}").count() == 1
