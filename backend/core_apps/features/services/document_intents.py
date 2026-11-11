"""Idempotent catalog intents emitted by signing and capture transitions."""

from ..models import PaymentReceipt, RentalDocument


def contract(lease):
    if lease.document_id:
        return RentalDocument.objects.get_or_create(
            lease=lease,
            document_type="contract",
            source_reference=str(lease.document_id),
            defaults={"title": "Rental agreement"},
        )[0]


def receipt(invoice, identity):
    return RentalDocument.objects.get_or_create(
        lease=invoice.lease,
        document_type="receipt",
        source_reference=str(identity),
        defaults={"title": f"Receipt record {invoice.reference} (JSON)"},
    )[0]


def change(item):
    if item.status in {"signed", "applied"}:
        return RentalDocument.objects.get_or_create(
            lease=item.lease,
            document_type="change",
            source_reference=str(item.id),
            defaults={"title": f"{item.get_kind_display()} {item.id}"},
        )[0]


def backfill(lease):
    """Explicit maintenance operation for historical sources; never called by GET."""
    contract(lease)
    for source in (
        PaymentReceipt.objects.filter(payment_attempt__invoice__lease=lease)
        .select_related("payment_attempt__invoice")
        .iterator()
    ):
        receipt(source.payment_attempt.invoice, source.id)
    for item in lease.rental_changes.filter(status__in=["signed", "applied"]).iterator():
        change(item)
