from django.urls import path
from . import advanced_tender_views as views

urlpatterns = [
    path("housing-tender-sources/", views.sources),
    path("housing-tenders/", views.tenders),
    path("housing-tenders/<uuid:tender_id>/", views.tender_detail),
    path("housing-tenders/<uuid:tender_id>/bids/", views.bids),
    path("housing-tenders/<uuid:tender_id>/package-runs/", views.packages),
    path(
        "housing-tenders/<uuid:tender_id>/automatic-package-runs/",
        views.construction_runs,
    ),
    path("housing-tenders/<uuid:tender_id>/<str:action>/", views.tender_action),
    path("housing-bids/<uuid:bid_id>/withdraw/", views.withdraw_bid),
    path("housing-bids/<uuid:bid_id>/clarifications/", views.clarifications),
    path("housing-packages/<uuid:package_id>/", views.package_detail),
    path("housing-packages/<uuid:package_id>/consents/", views.package_consent),
    path("housing-packages/<uuid:package_id>/prepare/", views.prepare_package),
    path("housing-package-runs/<uuid:run_id>/", views.construction_detail),
    path("housing-package-runs/<uuid:run_id>/dispatch/", views.construction_retry),
]
