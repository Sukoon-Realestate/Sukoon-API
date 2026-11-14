from django.urls import path
from . import living_lab_views as views

urlpatterns = [
    path(
        "living-labs/<uuid:lab_id>/configuration/",
        views.LivingLabActionView.as_view(),
        {"action": "configure"},
    ),
    path(
        "living-labs/<uuid:lab_id>/disclosures/",
        views.LivingLabActionView.as_view(),
        {"action": "disclose"},
    ),
    path(
        "living-labs/<uuid:lab_id>/scenario-runs/",
        views.LivingLabActionView.as_view(),
        {"action": "scenario"},
    ),
    path(
        "living-labs/<uuid:lab_id>/amendments/",
        views.LivingLabActionView.as_view(),
        {"action": "scenario"},
    ),
    path(
        "living-labs/<uuid:lab_id>/prepare-application/",
        views.LivingLabActionView.as_view(),
        {"action": "prepare_application"},
    ),
    path(
        "living-labs/<uuid:lab_id>/prepare-tender/",
        views.LivingLabActionView.as_view(),
        {"action": "prepare_tender"},
    ),
    path("housing-groups/<uuid:group_id>/living-labs/", views.LivingLabsView.as_view()),
    path("living-labs/<uuid:lab_id>/", views.LivingLabDetailView.as_view()),
    path(
        "living-labs/<uuid:lab_id>/my-requirements/",
        views.LivingLabRequirementsView.as_view(),
    ),
    path(
        "living-labs/<uuid:lab_id>/runs/",
        views.LivingLabActionView.as_view(),
        {"action": "run"},
    ),
    path(
        "living-labs/<uuid:lab_id>/responses/",
        views.LivingLabActionView.as_view(),
        {"action": "respond"},
    ),
    path(
        "living-labs/<uuid:lab_id>/withdraw/",
        views.LivingLabActionView.as_view(),
        {"action": "withdraw"},
    ),
    path(
        "living-labs/<uuid:lab_id>/close/",
        views.LivingLabActionView.as_view(),
        {"action": "close"},
    ),
    path(
        "living-labs/<uuid:lab_id>/prepare-cost-proposal/",
        views.LivingLabActionView.as_view(),
        {"action": "prepare_cost_proposal"},
    ),
]
