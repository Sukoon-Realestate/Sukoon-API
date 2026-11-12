"""Prepared advertising proof checks; no private facts cached across requests."""

from django.db.models import Exists, OuterRef
from core_apps.common.db_expressions import CanonicalUUIDText
from django.db.models.fields.json import KeyTextTransform

from core_apps.features.models import PaymentFulfillment


def with_fulfillment(rows):
    proof = PaymentFulfillment.objects.annotate(
        proof_subject=KeyTextTransform("subject_id", "invoice__purchase_snapshot")
    ).filter(
        invoice__purpose="advertising",
        proof_subject=CanonicalUUIDText(OuterRef("id")),
        invoice__payer_id=OuterRef("owner_id"),
        invoice__status="paid",
        status="fulfilled",
        attempt__payment_status="captured",
    )
    return rows.annotate(prepared_fulfillment=Exists(proof))
