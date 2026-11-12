from django.urls import path
from . import capture_views as views

base = "property-captures/<uuid:session_id>/"
asset = base + "uploads/<uuid:asset_id>/"
urlpatterns = [
    path("properties/capture-capabilities/", views.CapabilitiesAPIView.as_view()),
    path(
        "properties/<uuid:property_id>/capture-sessions/",
        views.SessionsAPIView.as_view(),
    ),
    path(base, views.SessionDetailAPIView.as_view()),
    path(base + "rooms/", views.RoomsAPIView.as_view()),
    path(base + "coach-sessions/", views.CoachAPIView.as_view()),
    path(
        base + "coach-sessions/<uuid:coach_id>/close/",
        views.CloseCoachAPIView.as_view(),
    ),
    path(base + "uploads/", views.ReserveAPIView.as_view()),
    path(asset, views.UploadAPIView.as_view()),
    path(asset + "parts/<int:index>/", views.PartAPIView.as_view()),
    path(asset + "complete/", views.CompleteAPIView.as_view()),
    path(base + "manifests/", views.ManifestsAPIView.as_view()),
    path(base + "processing-jobs/", views.JobsAPIView.as_view()),
    path(base + "processing-jobs/<uuid:job_id>/", views.JobAPIView.as_view()),
    path(
        base + "processing-jobs/<uuid:job_id>/retry/", views.RetryJobAPIView.as_view()
    ),
    path(
        base + "processing-jobs/<uuid:job_id>/select-outputs/",
        views.SelectOutputsAPIView.as_view(),
    ),
    path(
        base
        + "processing-jobs/<uuid:job_id>/stations/<uuid:station_id>/<str:resource>/",
        views.StationResourceAPIView.as_view(),
    ),
    path(
        base
        + "processing-jobs/<uuid:job_id>/components/<uuid:component_id>/<str:resource>/",
        views.ComponentResourceAPIView.as_view(),
    ),
]
