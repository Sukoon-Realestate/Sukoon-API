from django.urls import path
from . import views
from .capture_urls import urlpatterns as capture_patterns

app_name = "virtual_tours"
property_base = "properties/<uuid:property_id>/virtual-tours/"
tour_base = property_base + "<uuid:tour_id>/"
revision_base = tour_base + "revisions/<uuid:revision_id>/"
upload_base = "virtual-tour-uploads/<uuid:upload_id>/"
session_base = "virtual-tour-viewer/sessions/<uuid:session_id>/"
resource_base = session_base + "resources/<str:resource_id>/"
urlpatterns = [
    *capture_patterns,
    path("properties/virtual-tours/capabilities/", views.capabilities),
    path(property_base, views.tours),
    path(property_base + "available/", views.availability),
    path(tour_base, views.delete_tour),
    path(tour_base + "unpublish/", views.unpublish_tour),
    path(tour_base + "revisions/", views.revisions),
    path(revision_base, views.revision),
    *[
        path(revision_base + action + "/", views.revision_action, {"action": action})
        for action in ("uploads", "process", "submit-review")
    ],
    path(tour_base + "viewer-sessions/", views.viewer_sessions),
    path(upload_base, views.upload_detail),
    path(upload_base + "parts/", views.upload_parts),
    path(upload_base + "parts/<int:part>/", views.upload_part_bytes),
    path(upload_base + "complete/", views.upload_complete),
    path("virtual-tour-operations/by-key/<str:key>/", views.operation),
    path("virtual-tour-operations/<uuid:operation_id>/", views.operation),
    path("virtual-tour-viewer/exchange/", views.exchange),
    path(session_base + "manifest/", views.manifest),
    path(session_base + "renew/", views.renew_session),
    path(session_base, views.revoke_session),
    path(resource_base + "access/", views.resource_access),
    path(resource_base + "bytes/", views.resource_bytes),
    path(
        resource_base + "bytes/<str:face>/<int:level>/<int:x>/<int:y>/",
        views.resource_bytes,
    ),
    path("admin/" + revision_base + "review-decisions/", views.review_decision),
]

# Reuse the same authoring, processing, upload, review and viewer lifecycle.
for asset_kind in ("building", "complex"):
    base = "residential-assets/" + asset_kind + "/<uuid:property_id>/virtual-tours/"
    tour = base + "<uuid:tour_id>/"
    revision = tour + "revisions/<uuid:revision_id>/"
    kwargs = {"asset_kind": asset_kind}
    urlpatterns += [
        path(base, views.tours, kwargs),
        path(base + "available/", views.availability, kwargs),
        path(tour, views.delete_tour, kwargs),
        path(tour + "unpublish/", views.unpublish_tour, kwargs),
        path(tour + "revisions/", views.revisions, kwargs),
        path(revision, views.revision, kwargs),
        *[
            path(
                revision + action + "/",
                views.revision_action,
                {**kwargs, "action": action},
            )
            for action in ("uploads", "process", "submit-review")
        ],
        path(tour + "viewer-sessions/", views.viewer_sessions, kwargs),
        path("admin/" + revision + "review-decisions/", views.review_decision, kwargs),
    ]
