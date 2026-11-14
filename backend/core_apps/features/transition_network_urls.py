from django.urls import path
from . import transition_network_views as views

urlpatterns = [
    path("leases/<uuid:lease_id>/move-planning-context/", views.ContextView.as_view()),
    path("move-intents/", views.IntentsView.as_view()),
    path("move-intents/<uuid:intent_id>/", views.IntentDetailView.as_view()),
    path("move-intents/<uuid:intent_id>/runs/", views.RunsView.as_view()),
    path(
        "move-intents/<uuid:intent_id>/<slug:action>/", views.IntentActionView.as_view()
    ),
    path("transition-match-runs/<uuid:run_id>/", views.RunDetailView.as_view()),
    path("transition-candidates/", views.CandidatesView.as_view()),
    path(
        "transition-candidates/<uuid:candidate_id>/",
        views.CandidateDetailView.as_view(),
    ),
    path(
        "transition-candidates/<uuid:candidate_id>/interest/",
        views.CandidateInterestView.as_view(),
    ),
    path("transition-plans/<uuid:candidate_id>/prepare/", views.PrepareView.as_view()),
]
