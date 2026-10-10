from django.urls import path

from . import views


app_name = "advertising"

urlpatterns = [
    path("plans/", views.plan_list, name="plan-list"),
    path(
        "owner-advertisements/",
        views.owner_advertisement_collection,
        name="owner-advertisement-list",
    ),
    path(
        "owner-advertisements/<uuid:advertisement_id>/",
        views.owner_advertisement_detail,
        name="owner-advertisement-detail",
    ),
    path(
        "owner-advertisements/<uuid:advertisement_id>/mock-payment/",
        views.mock_payment,
        name="mock-payment",
    ),
    path(
        "operations/<str:operation_id>/",
        views.operation_detail,
        name="operation-detail",
    ),
    path("placements/tenant-home/", views.tenant_home_placement, name="tenant-home"),
    path(
        "media/<uuid:advertisement_id>/",
        views.advertisement_media,
        name="advertisement-media",
    ),
]
