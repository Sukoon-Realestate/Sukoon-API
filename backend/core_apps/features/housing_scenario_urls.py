from django.urls import path
from . import housing_scenario_views as views

urlpatterns = [
    path(
        "companies/<uuid:company_id>/housing-scenario-decisions/",
        views.DecisionInboxView.as_view(),
    ),
    path(
        "housing-scenario-comparisons/<uuid:comparison_id>/",
        views.ComparisonDetailView.as_view(),
    ),
    path("housing-scenario-runs/<uuid:run_id>/", views.ScenarioRunView.as_view()),
    path(
        "housing-scenario-runs/<uuid:run_id>/cancel/", views.ScenarioRunView.as_view()
    ),
    path(
        "housing-scenario-decisions/<uuid:decision_id>/",
        views.ScenarioDecisionView.as_view(),
    ),
    path(
        "housing-scenario-decisions/<uuid:decision_id>/<str:action>/",
        views.ScenarioDecisionView.as_view(),
    ),
    path(
        "companies/<uuid:company_id>/housing-scenarios/", views.ScenariosView.as_view()
    ),
    path(
        "companies/<uuid:company_id>/housing-scenario-sources/<str:kind>/",
        views.ScenarioSourcesView.as_view(),
    ),
    path("housing-scenarios/<uuid:scenario_id>/", views.ScenarioDetailView.as_view()),
    path(
        "housing-scenarios/<uuid:scenario_id>/<str:action>/",
        views.ScenarioActionView.as_view(),
    ),
]
