from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .billing_serializers import (
    IssueInvoiceSerializer,
    InvoiceActionSerializer,
    PurchaseCheckoutSerializer,
)
from .pagination import FeaturePagination
from .renderers import FeatureJsonRenderer
from .services.billing_catalog import workspace_for
from .services.billing_invoices import (
    authorized_invoice,
    invoice_queryset,
    issue_purchase,
    cancel_invoice,
)
from .services.billing_payments import quote_purchase, checkout_purchase
from .services.billing_projection import (
    invoice_payload,
    purchase_quote_payload,
    purchase_attempt_payload,
)
from .models import IdempotencyRecord


def validated(serializer, request):
    value = serializer(
        data=request.data, context={"mobile_contract": mobile_projection(request)}
    )
    value.is_valid(raise_exception=True)
    return value.validated_data


def mobile_projection(request):
    return request.query_params.get("projection") == "mobile_v1"


def language(request):
    return "ar" if getattr(request, "LANGUAGE_CODE", "en").startswith("ar") else "en"


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def invoices(request):
    if request.method == "POST":
        invoice, created = issue_purchase(
            request.user, validated(IssueInvoiceSerializer, request)
        )
        return Response(
            invoice_payload(
                invoice,
                request.user,
                language(request),
                mobile=mobile_projection(request),
            ),
            status=201 if created else 200,
        )
    workspace = workspace_for(request.query_params.get("workspace", "tenant"))
    query = invoice_queryset(request.user, workspace).prefetch_related("lines")
    if request.query_params.get("status"):
        status = request.query_params["status"]
        if status not in {choice[0] for choice in query.model.Status.choices}:
            raise ValidationError({"status": "Unknown invoice status."})
        query = query.filter(status=status)
    if request.query_params.get("purpose"):
        purpose = request.query_params["purpose"]
        if purpose not in {"rent", "subscription", "advertising"}:
            raise ValidationError({"purpose": "Unknown invoice purpose."})
        query = query.filter(purpose=purpose)
    for key, lookup in (
        ("from", "created_at__date__gte"),
        ("to", "created_at__date__lte"),
    ):
        if request.query_params.get(key):
            try:
                day = parse_date(request.query_params[key])
            except ValueError:
                day = None
            if day is None:
                raise ValidationError({key: "Use a valid ISO date."})
            query = query.filter(**{lookup: day})
    pager = FeaturePagination()
    page = pager.paginate_queryset(query, request)
    return pager.get_paginated_response(
        [
            invoice_payload(
                x, request.user, language(request), mobile=mobile_projection(request)
            )
            for x in page
        ]
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def invoice_detail(request, invoice_id):
    invoice = authorized_invoice(request.user, invoice_id)
    return Response(
        invoice_payload(
            invoice, request.user, language(request), mobile=mobile_projection(request)
        )
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def invoice_operation(request, request_key):
    record = IdempotencyRecord.objects.filter(
        user=request.user, operation="billing.issue", request_key=request_key
    ).first()
    invoice = (
        authorized_invoice(request.user, record.result_subject_id) if record else None
    )
    return Response(
        {
            "invoice": (
                invoice_payload(
                    invoice,
                    request.user,
                    language(request),
                    mobile=mobile_projection(request),
                )
                if invoice
                else None
            ),
            "absence_confirmed": record is None,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def invoice_quote(request, invoice_id):
    quote = quote_purchase(
        request.user, invoice_id, validated(InvoiceActionSerializer, request)
    )
    return Response(purchase_quote_payload(quote), status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def invoice_checkout(request, invoice_id):
    attempt = checkout_purchase(
        request.user, invoice_id, validated(PurchaseCheckoutSerializer, request)
    )
    return Response(purchase_attempt_payload(attempt))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def invoice_cancel(request, invoice_id):
    body = validated(InvoiceActionSerializer, request)
    invoice = cancel_invoice(request.user, invoice_id, body)
    return Response(
        invoice_payload(
            invoice, request.user, language(request), mobile=mobile_projection(request)
        )
    )
