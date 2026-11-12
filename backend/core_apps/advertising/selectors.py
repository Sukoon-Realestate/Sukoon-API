"""Prepared advertising proof checks; no private facts cached across requests."""

from django.db.models import CharField, Exists, Func, OuterRef
from django.db.models.fields.json import KeyTextTransform

from core_apps.features.models import PaymentFulfillment


class CanonicalUUIDText(Func):
    arity = 1
    output_field = CharField()

    def as_postgresql(self, compiler, connection, **extra):
        sql, params = compiler.compile(self.source_expressions[0])
        return f"({sql})::text", params

    def as_sqlite(self, compiler, connection, **extra):
        sql, params = compiler.compile(self.source_expressions[0])
        parts = [f"substr({sql}, {start}, {size})" for start, size in ((1, 8), (9, 4), (13, 4), (17, 4), (21, 12))]
        return "(" + " || '-' || ".join(parts) + ")", params * 5


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
