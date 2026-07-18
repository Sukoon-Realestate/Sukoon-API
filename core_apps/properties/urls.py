from django.urls import path

from .views import (
    MyPropertyListAPIView,
    PropertyCreateAPIView,
    PropertyDeleteAPIView,
    PropertyDetailAPIView,
    PropertyImageDetailAPIView,
    PropertyImageUploadAPIView,
    PropertyListAPIView,
    PropertyUpdateAPIView,
    PropertyVisitCreateAPIView,
    TenantPropertyVisitListAPIView,
    OwnerPropertyVisitListAPIView,
    PropertyVisitDetailAPIView,
    PropertyVisitUpdateAPIView,
)

urlpatterns = [
    path("", PropertyListAPIView.as_view(), name="property-list"),
    path("create/", PropertyCreateAPIView.as_view(), name="property-create"),
    path("owned/", MyPropertyListAPIView.as_view(), name="my-property-list"),
    path("<uuid:id>/", PropertyDetailAPIView.as_view(), name="property-detail"),
    path("<uuid:id>/update/", PropertyUpdateAPIView.as_view(), name="property-update"),
    path("<uuid:id>/delete/", PropertyDeleteAPIView.as_view(), name="property-delete"),
    path(
        "<uuid:property_id>/images/",
        PropertyImageUploadAPIView.as_view(),
        name="property-image-upload",
    ),
    path(
        "images/<uuid:id>/",
        PropertyImageDetailAPIView.as_view(),
        name="property-image-detail",
    ),
    # Property Visits (Bookings) URLs
    path(
        "<uuid:property_id>/visits/",
        PropertyVisitCreateAPIView.as_view(),
        name="property-visit-create",
    ),
    path(
        "visits/",
        TenantPropertyVisitListAPIView.as_view(),
        name="tenant-visit-list",
    ),
    path(
        "visits/received/",
        OwnerPropertyVisitListAPIView.as_view(),
        name="owner-visit-list",
    ),
    path(
        "visits/<uuid:id>/",
        PropertyVisitDetailAPIView.as_view(),
        name="property-visit-detail",
    ),
    path(
        "visits/<uuid:id>/update/",
        PropertyVisitUpdateAPIView.as_view(),
        name="property-visit-update",
    ),
]
