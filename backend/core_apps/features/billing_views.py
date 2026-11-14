from core_apps.features.http import ActionPolicy, FeatureAPIView

from django.utils.dateparse import parse_date
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
from .services.commerce_access import organization_for


def check_context(request, invoice):
    identity = request.query_params.get("organization_id")
    if identity:
        company = organization_for(request.user, identity)
        if invoice.organization_id != company.pk:
            from rest_framework.exceptions import NotFound

            raise NotFound()
    workspace = request.query_params.get("workspace")
    if workspace and invoice.workspace != workspace_for(workspace):
        from rest_framework.exceptions import NotFound

        raise NotFound()
    return invoice


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


class InvoicesView(FeatureAPIView):
    name = "Invoices"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "billing_views",
            "invoices",
            boundary="standard",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "billing_views",
            "invoices",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        workspace = workspace_for(request.query_params.get("workspace", "tenant"))
        organization = organization_for(
            request.user, request.query_params.get("organization_id")
        )
        query = invoice_queryset(
            request.user, workspace, organization
        ).prefetch_related("lines")
        if request.query_params.get("status"):
            status = request.query_params["status"]
            if status not in {choice[0] for choice in query.model.Status.choices}:
                raise ValidationError({"status": "Unknown invoice status."})
            query = query.filter(status=status)
        if request.query_params.get("purpose"):
            purpose = request.query_params["purpose"]
            if purpose not in {
                "rent",
                "subscription",
                "advertising",
                "maintenance",
                "promotion",
                "settlement",
                "adjustment",
                "deposit",
            }:
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
        from .services.billing_reads import invoice_read_queryset, prepare_invoice_page

        page = prepare_invoice_page(
            pager.paginate_queryset(invoice_read_queryset(query), request)
        )
        return pager.get_paginated_response(
            [
                invoice_payload(
                    x,
                    request.user,
                    language(request),
                    mobile=mobile_projection(request),
                    platform=request.query_params.get("platform", "unknown"),
                )
                for x in page
            ]
        )

    def post(self, request):
        command = validated(IssueInvoiceSerializer, request)
        if request.query_params.get("organization_id"):
            organization = organization_for(
                request.user, request.query_params["organization_id"]
            )
            if str(command.get("organization_id", "")) != str(organization.id):
                raise ValidationError(
                    {"organization_id": "The request and query contexts must match."}
                )
        if request.query_params.get("workspace") and command[
            "workspace"
        ] != workspace_for(request.query_params["workspace"]):
            raise ValidationError(
                {"workspace": "The request and query contexts must match."}
            )
        invoice, created = issue_purchase(request.user, command)
        return Response(
            invoice_payload(
                invoice,
                request.user,
                language(request),
                mobile=mobile_projection(request),
                platform=request.query_params.get("platform", "unknown"),
            ),
            status=201 if created else 200,
        )


# Stable callable import for integrations; URLs use the explicit class.
invoices = InvoicesView.as_view()


class InvoiceDetailView(FeatureAPIView):
    name = "Invoice Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "billing_views",
            "invoice_detail",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, invoice_id):
        invoice = check_context(request, authorized_invoice(request.user, invoice_id))
        return Response(
            invoice_payload(
                invoice,
                request.user,
                language(request),
                mobile=mobile_projection(request),
                platform=request.query_params.get("platform", "unknown"),
            )
        )


# Stable callable import for integrations; URLs use the explicit class.
invoice_detail = InvoiceDetailView.as_view()


class InvoiceOperationView(FeatureAPIView):
    name = "Invoice Operation"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "billing_views",
            "invoice_operation",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, request_key):
        organization_for(request.user, request.query_params.get("organization_id"))
        record = IdempotencyRecord.objects.filter(
            user=request.user, operation="billing.issue", request_key=request_key
        ).first()
        invoice = (
            authorized_invoice(request.user, record.result_subject_id)
            if record
            else None
        )
        if invoice:
            check_context(request, invoice)
        return Response(
            {
                "invoice": (
                    invoice_payload(
                        invoice,
                        request.user,
                        language(request),
                        mobile=mobile_projection(request),
                        platform=request.query_params.get("platform", "unknown"),
                    )
                    if invoice
                    else None
                ),
                "absence_confirmed": False,
            }
        )


# Stable callable import for integrations; URLs use the explicit class.
invoice_operation = InvoiceOperationView.as_view()


class InvoiceQuoteView(FeatureAPIView):
    name = "Invoice Quote"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "billing_views",
            "invoice_quote",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, invoice_id):
        check_context(request, authorized_invoice(request.user, invoice_id))
        quote = quote_purchase(
            request.user,
            invoice_id,
            validated(InvoiceActionSerializer, request),
            platform=request.query_params.get("platform", "unknown"),
        )
        return Response(purchase_quote_payload(quote), status=201)


# Stable callable import for integrations; URLs use the explicit class.
invoice_quote = InvoiceQuoteView.as_view()


class InvoiceCheckoutView(FeatureAPIView):
    name = "Invoice Checkout"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "billing_views",
            "invoice_checkout",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, invoice_id):
        check_context(request, authorized_invoice(request.user, invoice_id))
        attempt = checkout_purchase(
            request.user, invoice_id, validated(PurchaseCheckoutSerializer, request)
        )
        return Response(purchase_attempt_payload(attempt))


# Stable callable import for integrations; URLs use the explicit class.
invoice_checkout = InvoiceCheckoutView.as_view()


class InvoiceCancelView(FeatureAPIView):
    name = "Invoice Cancel"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "billing_views",
            "invoice_cancel",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, invoice_id):
        check_context(request, authorized_invoice(request.user, invoice_id))
        body = validated(InvoiceActionSerializer, request)
        invoice = cancel_invoice(request.user, invoice_id, body)
        return Response(
            invoice_payload(
                invoice,
                request.user,
                language(request),
                mobile=mobile_projection(request),
                platform=request.query_params.get("platform", "unknown"),
            )
        )


# Stable callable import for integrations; URLs use the explicit class.
invoice_cancel = InvoiceCancelView.as_view()
