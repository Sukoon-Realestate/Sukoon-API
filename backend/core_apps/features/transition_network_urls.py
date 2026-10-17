from django.urls import path
from . import transition_network_views as views

urlpatterns = [
    path("leases/<uuid:lease_id>/move-planning-context/", views.context),
    path("move-intents/", views.intents),
    path("move-intents/<uuid:intent_id>/", views.intent_detail),
    path("move-intents/<uuid:intent_id>/runs/", views.runs),
    path("move-intents/<uuid:intent_id>/<slug:action>/", views.intent_action),
    path("transition-match-runs/<uuid:run_id>/", views.run_detail),
    path("transition-candidates/", views.candidates),
    path("transition-candidates/<uuid:candidate_id>/", views.candidate_detail),
    path(
        "transition-candidates/<uuid:candidate_id>/interest/", views.candidate_interest
    ),
    path("transition-plans/<uuid:candidate_id>/prepare/", views.prepare),
]
