from django.urls import path
from . import housing_scenario_views as views

urlpatterns = [
    path(
        "companies/<uuid:company_id>/housing-scenario-decisions/", views.decision_inbox
    ),
    path("housing-scenario-comparisons/<uuid:comparison_id>/", views.comparison_detail),
    path("housing-scenario-runs/<uuid:run_id>/", views.scenario_run),
    path("housing-scenario-runs/<uuid:run_id>/cancel/", views.scenario_run),
    path("housing-scenario-decisions/<uuid:decision_id>/", views.scenario_decision),
    path(
        "housing-scenario-decisions/<uuid:decision_id>/<str:action>/",
        views.scenario_decision,
    ),
    path("companies/<uuid:company_id>/housing-scenarios/", views.scenarios),
    path(
        "companies/<uuid:company_id>/housing-scenario-sources/<str:kind>/",
        views.scenario_sources,
    ),
    path("housing-scenarios/<uuid:scenario_id>/", views.scenario_detail),
    path("housing-scenarios/<uuid:scenario_id>/<str:action>/", views.scenario_action),
]
