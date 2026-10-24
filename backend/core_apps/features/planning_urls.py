from django.urls import path
from core_apps.chat.views.group_history import GroupChatSummaryAPIView

from . import planning_condition_views as conditions
from . import planning_discovery_views as discovery
from . import planning_group_views as groups
from . import planning_housing_views as housing
from . import planning_roommate_views as roommates
from . import planning_transition_views as transitions
from .planning_home_views import planning_home


urlpatterns = [
    path("housing-groups/<uuid:group_id>/chat/", GroupChatSummaryAPIView.as_view()),
    path("planning-home/", planning_home),
    path("open-housing-groups/", groups.open_groups),
    path("group-join-requests/", groups.my_group_join_requests),
    path("group-join-requests/<uuid:join_id>/", groups.group_join_detail),
    path("housing-groups/<uuid:group_id>/join-requests/", groups.group_join_request),
    path(
        "group-join-requests/<uuid:join_id>/<slug:action>/", groups.group_join_decision
    ),
    path("owner-group-applications/", groups.owner_group_applications),
    path(
        "group-applications/<uuid:application_id>/",
        groups.owner_group_application_detail,
    ),
    path(
        "group-applications/<uuid:application_id>/<slug:action>/",
        groups.owner_group_application_action,
    ),
    path("lifestyle-profile/", roommates.lifestyle_profile),
    path("roommate-candidates/", roommates.roommate_candidates),
    path("roommate-connections/", roommates.roommate_connections),
    path(
        "roommate-candidates/<uuid:candidate_id>/<slug:action>/",
        roommates.roommate_candidate_action,
    ),
    path(
        "roommate-connections/<uuid:connection_id>/<slug:action>/",
        roommates.roommate_connection_action,
    ),
    path("housing-groups/", groups.housing_groups),
    path("housing-groups/<uuid:group_id>/", groups.housing_group_detail),
    path("housing-groups/<uuid:group_id>/invitations/", groups.group_invitation_create),
    path("housing-groups/<uuid:group_id>/<slug:action>/", groups.housing_group_action),
    path("group-invitations/preview/", groups.group_invitation_preview),
    path("group-invitations/join/", groups.group_invitation_join),
    path("group-invitations/<uuid:invitation_id>/", groups.group_invitation_detail),
    path("housing-requests/", housing.housing_requests),
    path("housing-demand/", housing.housing_demand),
    path("owner-housing-offers/", housing.owner_housing_offers),
    path("housing-requests/<uuid:request_id>/", housing.housing_request_detail),
    path("housing-requests/<uuid:request_id>/offers/", housing.housing_offers),
    path(
        "housing-requests/<uuid:request_id>/<slug:action>/",
        housing.housing_request_action,
    ),
    path("housing-offers/<uuid:offer_id>/<slug:action>/", housing.housing_offer_action),
    path(
        "leases/<uuid:lease_id>/condition-report-context/",
        conditions.condition_report_context,
    ),
    path("leases/<uuid:lease_id>/condition-reports/", conditions.condition_reports),
    path("condition-reports/<uuid:report_id>/", conditions.condition_report_detail),
    path(
        "condition-reports/<uuid:report_id>/<slug:action>/",
        conditions.condition_report_action,
    ),
    path("leases/<uuid:lease_id>/move-out-notices/", transitions.move_out_notices),
    path(
        "leases/<uuid:lease_id>/replacement-requests/", transitions.replacement_requests
    ),
    path(
        "leases/<uuid:lease_id>/replacement-candidates/",
        transitions.replacement_candidates,
    ),
    path(
        "move-out-notices/<uuid:transition_id>/",
        transitions.transition_detail_action,
        {"kind": "moveOutNotice"},
    ),
    path(
        "move-out-notices/<uuid:transition_id>/<slug:action>/",
        transitions.transition_detail_action,
        {"kind": "moveOutNotice"},
    ),
    path(
        "replacement-requests/<uuid:transition_id>/",
        transitions.transition_detail_action,
        {"kind": "replacement"},
    ),
    path(
        "replacement-requests/<uuid:transition_id>/candidate-consent/",
        transitions.replacement_candidate_consent,
    ),
    path(
        "replacement-requests/<uuid:transition_id>/<slug:action>/",
        transitions.transition_detail_action,
        {"kind": "replacement"},
    ),
    path("replacement-invitations/", transitions.replacement_invitations),
    path("commute-searches/", discovery.commute_searches),
    path("commute-searches/<uuid:search_id>/", discovery.commute_detail),
    path("commute-searches/<uuid:search_id>/cancel/", discovery.commute_cancel),
    path("commute-searches/<uuid:search_id>/results/", discovery.commute_results),
    path("tenant-assistant/turns/", discovery.tenant_assistant_turns),
]

from . import shared_housing_views as shared_housing
urlpatterns += [
    path("shared-housing-plans/", shared_housing.plans),
    path("shared-housing-plans/<uuid:plan_id>/", shared_housing.detail),
    path("shared-housing-plans/<uuid:plan_id>/proposals/", shared_housing.proposals),
    path("shared-housing-plans/<uuid:plan_id>/proposals/<uuid:proposal_id>/<slug:action>/", shared_housing.proposal_action),
    path("shared-housing-plans/<uuid:plan_id>/<slug:action>/", shared_housing.action),
    path("shared-housing-demand/", shared_housing.demand),
    path("owner-shared-housing-applications/", shared_housing.applications),
]
