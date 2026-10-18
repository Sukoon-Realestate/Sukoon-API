from django.urls import path
from . import billing_views as billing
from . import subscription_views as subscriptions

from .purchase_routing_views import purchase_route

urlpatterns = [
    path("billing/purchase-routing/", purchase_route),
    path("subscription-plans/", subscriptions.plans, name="subscription-plans"),
    path("subscriptions/current/", subscriptions.current, name="current-subscription"),
    path("billing/invoices/", billing.invoices, name="billing-invoices"),
    path(
        "billing/invoice-operations/<uuid:request_key>/",
        billing.invoice_operation,
        name="billing-invoice-operation",
    ),
    path(
        "billing/invoices/<uuid:invoice_id>/",
        billing.invoice_detail,
        name="billing-invoice",
    ),
    path(
        "billing/invoices/<uuid:invoice_id>/quote/",
        billing.invoice_quote,
        name="billing-quote",
    ),
    path(
        "billing/invoices/<uuid:invoice_id>/checkout/",
        billing.invoice_checkout,
        name="billing-checkout",
    ),
    path(
        "billing/invoices/<uuid:invoice_id>/cancel/",
        billing.invoice_cancel,
        name="billing-cancel",
    ),
]
