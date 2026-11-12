from django.urls import path
from . import views, review_views
from .capture_urls import urlpatterns as capture_patterns

app_name = "virtual_tours"
property_base = "properties/<uuid:property_id>/virtual-tours/"
tour_base = property_base + "<uuid:tour_id>/"
revision_base = tour_base + "revisions/<uuid:revision_id>/"
upload_base = "virtual-tour-uploads/<uuid:upload_id>/"
session_base = "virtual-tour-viewer/sessions/<uuid:session_id>/"
resource_base = session_base + "resources/<str:resource_id>/"
urlpatterns = [
    path("admin/virtual-tours/reviews/", review_views.CollectionAPIView.as_view()),
    path(
        "admin/virtual-tours/reviews/<uuid:revision_id>/",
        review_views.DetailAPIView.as_view(),
    ),
    *capture_patterns,
    path("virtual-tour-updates/<uuid:event_id>/", views.OwnerUpdateAPIView.as_view()),
    path("properties/virtual-tours/capabilities/", views.CapabilitiesAPIView.as_view()),
    path(property_base, views.ToursAPIView.as_view()),
    path(property_base + "available/", views.AvailabilityAPIView.as_view()),
    path(tour_base, views.DeleteTourAPIView.as_view()),
    path(tour_base + "unpublish/", views.UnpublishTourAPIView.as_view()),
    path(tour_base + "revisions/", views.RevisionsAPIView.as_view()),
    path(revision_base, views.RevisionAPIView.as_view()),
    *[
        path(
            revision_base + action + "/",
            views.RevisionActionAPIView.as_view(),
            {"action": action},
        )
        for action in ("uploads", "process", "submit-review")
    ],
    path(tour_base + "viewer-sessions/", views.ViewerSessionsAPIView.as_view()),
    path(upload_base, views.UploadDetailAPIView.as_view()),
    path(upload_base + "parts/", views.UploadPartsAPIView.as_view()),
    path(upload_base + "parts/<int:part>/", views.UploadPartBytesAPIView.as_view()),
    path(upload_base + "complete/", views.UploadCompleteAPIView.as_view()),
    path("virtual-tour-operations/by-key/<str:key>/", views.OperationAPIView.as_view()),
    path(
        "virtual-tour-operations/<uuid:operation_id>/", views.OperationAPIView.as_view()
    ),
    path("virtual-tour-viewer/exchange/", views.ExchangeAPIView.as_view()),
    path(session_base + "manifest/", views.ManifestAPIView.as_view()),
    path(
        session_base + "places/<str:place_id>/offer/", views.PlaceOfferAPIView.as_view()
    ),
    path(session_base + "renew/", views.RenewSessionAPIView.as_view()),
    path(session_base, views.RevokeSessionAPIView.as_view()),
    path(resource_base + "access/", views.ResourceAccessAPIView.as_view()),
    path(resource_base + "bytes/", views.ResourceBytesAPIView.as_view()),
    path(
        resource_base + "bytes/<str:face>/<int:level>/<int:x>/<int:y>/",
        views.ResourceBytesAPIView.as_view(),
    ),
    path(
        "admin/" + revision_base + "review-decisions/",
        views.ReviewDecisionAPIView.as_view(),
    ),
]

# Reuse the same authoring, processing, upload, review and viewer lifecycle.
for asset_kind in ("building", "complex"):
    base = "residential-assets/" + asset_kind + "/<uuid:property_id>/virtual-tours/"
    tour = base + "<uuid:tour_id>/"
    revision = tour + "revisions/<uuid:revision_id>/"
    kwargs = {"asset_kind": asset_kind}
    urlpatterns += [
        path(base, views.ToursAPIView.as_view(), kwargs),
        path(base + "available/", views.AvailabilityAPIView.as_view(), kwargs),
        path(tour, views.DeleteTourAPIView.as_view(), kwargs),
        path(tour + "unpublish/", views.UnpublishTourAPIView.as_view(), kwargs),
        path(tour + "revisions/", views.RevisionsAPIView.as_view(), kwargs),
        path(revision, views.RevisionAPIView.as_view(), kwargs),
        *[
            path(
                revision + action + "/",
                views.RevisionActionAPIView.as_view(),
                {**kwargs, "action": action},
            )
            for action in ("uploads", "process", "submit-review")
        ],
        path(tour + "viewer-sessions/", views.ViewerSessionsAPIView.as_view(), kwargs),
        path(
            "admin/" + revision + "review-decisions/",
            views.ReviewDecisionAPIView.as_view(),
            kwargs,
        ),
    ]
