"""The collection channel is separate from a report about money outside Sokoun."""

from rest_framework.exceptions import NotFound
from rest_framework.response import Response

POLICY = {"mode": "platform_only", "version": "sokoun-collection-v1"}
ISSUE_CODES = frozenset({"off_platform_request", "off_platform_payment"})


def reviewed_terms(terms):
    """Snapshot new/reviewed terms only; never rewrite an executed agreement."""
    return {**terms, "payment_collection": dict(POLICY)}


def reject_external_claim(request, invoice):
    from ..models import PrivateAccessRevocation
    from .company.tenancy_access import commercial_read

    user = request.user
    if (
        not user.is_active
        or not commercial_read(invoice.lease, user)
        or PrivateAccessRevocation.objects.filter(
            lease=invoice.lease, user=user
        ).exists()
    ):
        raise NotFound()
    arabic = getattr(request, "LANGUAGE_CODE", "").startswith(
        "ar"
    ) or request.headers.get("Accept-Language", "").startswith("ar")
    return Response(
        {
            "code": "external_payment_not_supported",
            "message": (
                "السداد يتم عبر فاتورة سكون. يمكنك إبلاغ الدعم عن دفعة خارج المنصة؛ البلاغ لا يسدد الفاتورة."
                if arabic
                else "Pay through your Sokoun invoice. Report any off-platform payment to support; a report does not settle the invoice."
            ),
            "payment_collection": POLICY,
            "support_context": {
                "lease_id": str(invoice.lease.id),
                "invoice_id": str(invoice.id),
                "issue_code": "off_platform_payment",
            },
        },
        status=409,
    )
