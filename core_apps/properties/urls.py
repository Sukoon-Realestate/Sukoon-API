from django.urls import path

from .views import (
    PropertyCreateAPIView,
    PropertyDeleteAPIView,
    PropertyDetailAPIView,
    PropertyImageDetailAPIView,
    PropertyImageUploadAPIView,
    PropertyListAPIView,
    PropertyUpdateAPIView,
)

urlpatterns = [
    path("", PropertyListAPIView.as_view(), name="property-list"),
    path("create/", PropertyCreateAPIView.as_view(), name="property-create"),
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
]
