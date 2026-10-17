from django.urls import path
from . import living_lab_views as views

urlpatterns = [
    path(
        "living-labs/<uuid:lab_id>/configuration/",
        views.living_lab_action,
        {"action": "configure"},
    ),
    path(
        "living-labs/<uuid:lab_id>/disclosures/",
        views.living_lab_action,
        {"action": "disclose"},
    ),
    path(
        "living-labs/<uuid:lab_id>/scenario-runs/",
        views.living_lab_action,
        {"action": "scenario"},
    ),
    path(
        "living-labs/<uuid:lab_id>/amendments/",
        views.living_lab_action,
        {"action": "scenario"},
    ),
    path(
        "living-labs/<uuid:lab_id>/prepare-application/",
        views.living_lab_action,
        {"action": "prepare_application"},
    ),
    path(
        "living-labs/<uuid:lab_id>/prepare-tender/",
        views.living_lab_action,
        {"action": "prepare_tender"},
    ),
    path("housing-groups/<uuid:group_id>/living-labs/", views.living_labs),
    path("living-labs/<uuid:lab_id>/", views.living_lab_detail),
    path("living-labs/<uuid:lab_id>/my-requirements/", views.living_lab_requirements),
    path("living-labs/<uuid:lab_id>/runs/", views.living_lab_action, {"action": "run"}),
    path(
        "living-labs/<uuid:lab_id>/responses/",
        views.living_lab_action,
        {"action": "respond"},
    ),
    path(
        "living-labs/<uuid:lab_id>/withdraw/",
        views.living_lab_action,
        {"action": "withdraw"},
    ),
    path(
        "living-labs/<uuid:lab_id>/close/", views.living_lab_action, {"action": "close"}
    ),
    path(
        "living-labs/<uuid:lab_id>/prepare-cost-proposal/",
        views.living_lab_action,
        {"action": "prepare_cost_proposal"},
    ),
]
