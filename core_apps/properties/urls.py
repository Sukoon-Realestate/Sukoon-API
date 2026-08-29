from django.urls import path

from .views import (
    CityListAPIView,
    GovernorateListAPIView,
    MyPropertyListAPIView,
    OwnerDashboardAPIView,
    PropertyCreateAPIView,
    PropertyDeleteAPIView,
    PropertyDetailAPIView,
    PropertyImageDetailAPIView,
    PropertyImageUploadAPIView,
    PropertyListAPIView,
    PropertyNewListAPIView,
    PropertyTypeListAPIView,
    PropertyUpdateAPIView,
    PropertyVisitCreateAPIView,
    TenantPropertyVisitListAPIView,
    OwnerPropertyVisitListAPIView,
    PropertyVisitDetailAPIView,
    PropertyVisitUpdateAPIView,
    AvailablePlacesAPIView,
    PropertyAvailableDatesAPIView,
)

urlpatterns = [
    path("governorates/", GovernorateListAPIView.as_view(), name="governorate-list"),
    path("cities/", CityListAPIView.as_view(), name="city-list"),
    path("types/", PropertyTypeListAPIView.as_view(), name="property-type-list"),
    path(
        "available_places/",
        AvailablePlacesAPIView.as_view(),
        name="property-available-places",
    ),
    path("", PropertyNewListAPIView.as_view(), name="property-list"),
    path("create/", PropertyCreateAPIView.as_view(), name="property-create"),
    path("owned/", MyPropertyListAPIView.as_view(), name="my-property-list"),
    path("owner/dashboard/", OwnerDashboardAPIView.as_view(), name="owner-dashboard"),
    path("<uuid:id>/", PropertyDetailAPIView.as_view(), name="property-detail"),
    path(
        "<uuid:property_id>/available_dates/",
        PropertyAvailableDatesAPIView.as_view(),
        name="property-available-dates",
    ),
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
