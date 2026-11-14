from django.urls import path

from . import views


app_name = "advertising"

urlpatterns = [
    path("plans/", views.PlanListView.as_view(), name="plan-list"),
    path(
        "owner-advertisements/",
        views.OwnerAdvertisementCollectionView.as_view(),
        name="owner-advertisement-list",
    ),
    path(
        "owner-advertisements/<uuid:advertisement_id>/",
        views.OwnerAdvertisementDetailView.as_view(),
        name="owner-advertisement-detail",
    ),
    path(
        "owner-advertisements/<uuid:advertisement_id>/mock-payment/",
        views.MockPaymentView.as_view(),
        name="mock-payment",
    ),
    path(
        "operations/<str:operation_id>/",
        views.OperationDetailView.as_view(),
        name="operation-detail",
    ),
    path(
        "placements/tenant-home/",
        views.TenantHomePlacementView.as_view(),
        name="tenant-home",
    ),
    path(
        "media/<uuid:advertisement_id>/",
        views.AdvertisementMediaView.as_view(),
        name="advertisement-media",
    ),
]
