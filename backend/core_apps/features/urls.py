from django.urls import path

from . import views

urlpatterns = [
    path("configuration/", views.configuration, name="feature-configuration"),
    path("boost-campaigns/", views.boost_campaigns, name="boost-campaigns"),
    path("search-alerts/", views.search_alerts, name="search-alerts"),
    path(
        "search-alerts/<uuid:alert_id>/",
        views.search_alert_detail,
        name="search-alert-detail",
    ),
    path(
        "owner-analytics/<uuid:property_id>/",
        views.owner_analytics,
        name="owner-analytics",
    ),
    path("listing-suggestions/", views.listing_suggestions, name="listing-suggestions"),
    path("lease-configuration/", views.lease_configuration, name="lease-configuration"),
    path("lease-tenants/", views.lease_tenants, name="lease-tenants"),
    path("tenancy-invitations/", views.tenancy_invitations, name="tenancy-invitations"),
    path(
        "tenancy-invitations/<uuid:invitation_id>/",
        views.tenancy_invitation_detail,
        name="tenancy-invitation-detail",
    ),
    path(
        "tenancy-invitations/<uuid:invitation_id>/respond/",
        views.tenancy_invitation_respond,
        name="tenancy-invitation-respond",
    ),
    path("leases/", views.leases, name="leases"),
    path("leases/<uuid:lease_id>/", views.lease_detail, name="lease-detail"),
    path(
        "leases/<uuid:lease_id>/signing-session/",
        views.lease_signing_session,
        name="lease-signing-session",
    ),
    path("leases/<uuid:lease_id>/cancel/", views.lease_cancel, name="lease-cancel"),
    path("rent-invoices/", views.rent_invoices, name="rent-invoices"),
    path(
        "rent-invoices/<uuid:invoice_id>/",
        views.rent_invoice_detail,
        name="rent-invoice-detail",
    ),
    path(
        "rent-invoices/<uuid:invoice_id>/checkout/",
        views.rent_invoice_checkout,
        name="rent-invoice-checkout",
    ),
]
