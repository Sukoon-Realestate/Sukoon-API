"""Settlements: apply credit."""

from ...models import InvoiceLine, RentInvoice
from ..rental_phase2 import RentalConflict
from ..rental_phase3 import invoice_balance_minor, post_ledger_transaction


def _apply_credit(lease, item, credit, index):
    invoice = RentInvoice.objects.select_for_update().get(
        id=credit["invoice_id"], lease=lease
    )
    amount = credit["amount_minor"]
    if amount > invoice_balance_minor(invoice):
        raise RentalConflict(
            "Invoice balance changed after settlement consent.",
            code="settlement_financial_state_changed",
        )
    invoice.credits_minor += amount
    invoice.status = (
        "written_off"
        if credit["type"] == "write_off" and invoice_balance_minor(invoice) == 0
        else ("paid" if invoice_balance_minor(invoice) == 0 else invoice.status)
    )
    invoice.revision += 1
    invoice.save()
    InvoiceLine.objects.create(
        invoice=invoice,
        line_type=credit["type"],
        description="Agreed final settlement credit",
        amount_minor=-amount,
        source={"settlement_id": str(item.id), "line_id": credit["line_id"]},
    )
    post_ledger_transaction(
        reference=f"settlement-credit:{item.id}:{index}",
        kind="settlement_credit",
        lease=lease,
        invoice=invoice,
        entries=[
            ("unearned_rent_liability", "debit", amount),
            ("tenant_receivable", "credit", amount),
        ],
    )
