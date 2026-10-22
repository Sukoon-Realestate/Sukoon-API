from django.urls import path
from . import capture_views as views

base = "property-captures/<uuid:session_id>/"
asset = base + "uploads/<uuid:asset_id>/"
urlpatterns = [
    path("properties/capture-capabilities/", views.capabilities),
    path("properties/<uuid:property_id>/capture-sessions/", views.sessions),
    path(base, views.session_detail),
    path(base + "rooms/", views.rooms),
    path(base + "coach-sessions/", views.coach),
    path(base + "coach-sessions/<uuid:coach_id>/close/", views.close_coach),
    path(base + "uploads/", views.reserve),
    path(asset, views.upload),
    path(asset + "parts/<int:index>/", views.part),
    path(asset + "complete/", views.complete),
    path(base + "manifests/", views.manifests),
    path(base + "processing-jobs/", views.jobs),
    path(base + "processing-jobs/<uuid:job_id>/", views.job),
    path(base + "processing-jobs/<uuid:job_id>/select-outputs/", views.select_outputs),
    path(
        base
        + "processing-jobs/<uuid:job_id>/stations/<uuid:station_id>/<str:resource>/",
        views.station_resource,
    ),
    path(
        base
        + "processing-jobs/<uuid:job_id>/components/<uuid:component_id>/<str:resource>/",
        views.component_resource,
    ),
]
