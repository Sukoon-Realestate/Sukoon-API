from django.urls import path
from . import advanced_tender_views as views

urlpatterns = [
    path("housing-tender-sources/", views.SourcesView.as_view()),
    path("housing-tenders/", views.TendersView.as_view()),
    path("housing-tenders/<uuid:tender_id>/", views.TenderDetailView.as_view()),
    path("housing-tenders/<uuid:tender_id>/bids/", views.BidsView.as_view()),
    path(
        "housing-tenders/<uuid:tender_id>/package-runs/", views.PackagesView.as_view()
    ),
    path(
        "housing-tenders/<uuid:tender_id>/automatic-package-runs/",
        views.ConstructionRunsView.as_view(),
    ),
    path(
        "housing-tenders/<uuid:tender_id>/<str:action>/",
        views.TenderActionView.as_view(),
    ),
    path("housing-bids/<uuid:bid_id>/withdraw/", views.WithdrawBidView.as_view()),
    path(
        "housing-bids/<uuid:bid_id>/clarifications/", views.ClarificationsView.as_view()
    ),
    path("housing-packages/<uuid:package_id>/", views.PackageDetailView.as_view()),
    path(
        "housing-packages/<uuid:package_id>/consents/",
        views.PackageConsentView.as_view(),
    ),
    path(
        "housing-packages/<uuid:package_id>/prepare/",
        views.PreparePackageView.as_view(),
    ),
    path("housing-package-runs/<uuid:run_id>/", views.ConstructionDetailView.as_view()),
    path(
        "housing-package-runs/<uuid:run_id>/dispatch/",
        views.ConstructionRetryView.as_view(),
    ),
]
