from django.urls import path
from . import billing_views as billing
from . import subscription_views as subscriptions

from . import commerce_views as commerce

from .purchase_routing_views import PurchaseRouteView

urlpatterns = [
    path(
        "billing/store/notifications/<str:platform>/",
        commerce.StoreNotificationView.as_view(),
        name="billing-store-notification",
    ),
    path(
        "billing/store/context/",
        commerce.StoreContextView.as_view(),
        name="billing-store-context",
    ),
    path(
        "billing/store/verify/",
        commerce.StoreVerifyView.as_view(),
        name="billing-store-verify",
    ),
    path(
        "billing/entitlements/",
        commerce.EntitlementsView.as_view(),
        name="billing-entitlements",
    ),
    path("billing/purchase-routing/", PurchaseRouteView.as_view()),
    path(
        "subscription-plans/",
        subscriptions.PlansView.as_view(),
        name="subscription-plans",
    ),
    path(
        "subscriptions/current/",
        subscriptions.CurrentView.as_view(),
        name="current-subscription",
    ),
    path("billing/invoices/", billing.InvoicesView.as_view(), name="billing-invoices"),
    path(
        "billing/invoice-operations/<uuid:request_key>/",
        billing.InvoiceOperationView.as_view(),
        name="billing-invoice-operation",
    ),
    path(
        "billing/invoices/<uuid:invoice_id>/",
        billing.InvoiceDetailView.as_view(),
        name="billing-invoice",
    ),
    path(
        "billing/invoices/<uuid:invoice_id>/quote/",
        billing.InvoiceQuoteView.as_view(),
        name="billing-quote",
    ),
    path(
        "billing/invoices/<uuid:invoice_id>/checkout/",
        billing.InvoiceCheckoutView.as_view(),
        name="billing-checkout",
    ),
    path(
        "billing/invoices/<uuid:invoice_id>/cancel/",
        billing.InvoiceCancelView.as_view(),
        name="billing-cancel",
    ),
]
