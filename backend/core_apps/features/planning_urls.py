from django.urls import path
from core_apps.chat.views.group_history import GroupChatSummaryAPIView

from . import planning_condition_views as conditions
from . import planning_discovery_views as discovery
from . import planning_group_views as groups
from . import planning_housing_views as housing
from . import planning_roommate_views as roommates
from . import planning_transition_views as transitions
from . import decision_views
from .planning_home_views import PlanningHomeView
from .planning_housing_views_parts.housing_offer_inventory import (
    HousingOfferInventoryView,
)


urlpatterns = [
    path("decision-notebook/", decision_views.NotebookView.as_view()),
    path("decision-notebook/resolve/", decision_views.ResolveView.as_view()),
    path("housing-groups/<uuid:group_id>/chat/", GroupChatSummaryAPIView.as_view()),
    path("planning-home/", PlanningHomeView.as_view()),
    path("open-housing-groups/", groups.OpenGroupsView.as_view()),
    path("group-join-requests/", groups.MyGroupJoinRequestsView.as_view()),
    path("group-join-requests/<uuid:join_id>/", groups.GroupJoinDetailView.as_view()),
    path(
        "housing-groups/<uuid:group_id>/join-requests/",
        groups.GroupJoinRequestView.as_view(),
    ),
    path(
        "group-join-requests/<uuid:join_id>/<slug:action>/",
        groups.GroupJoinDecisionView.as_view(),
    ),
    path("owner-group-applications/", groups.OwnerGroupApplicationsView.as_view()),
    path(
        "group-applications/<uuid:application_id>/",
        groups.OwnerGroupApplicationDetailView.as_view(),
    ),
    path(
        "group-applications/<uuid:application_id>/<slug:action>/",
        groups.OwnerGroupApplicationActionView.as_view(),
    ),
    path("lifestyle-profile/", roommates.LifestyleProfileView.as_view()),
    path("roommate-candidates/", roommates.RoommateCandidatesView.as_view()),
    path("roommate-connections/", roommates.RoommateConnectionsView.as_view()),
    path(
        "roommate-candidates/<uuid:candidate_id>/<slug:action>/",
        roommates.RoommateCandidateActionView.as_view(),
    ),
    path(
        "roommate-connections/<uuid:connection_id>/<slug:action>/",
        roommates.RoommateConnectionActionView.as_view(),
    ),
    path("housing-groups/", groups.HousingGroupsView.as_view()),
    path("housing-groups/<uuid:group_id>/", groups.HousingGroupDetailView.as_view()),
    path(
        "housing-groups/<uuid:group_id>/invitations/",
        groups.GroupInvitationCreateView.as_view(),
    ),
    path(
        "housing-groups/<uuid:group_id>/<slug:action>/",
        groups.HousingGroupActionView.as_view(),
    ),
    path("group-invitations/preview/", groups.GroupInvitationPreviewView.as_view()),
    path("group-invitations/join/", groups.GroupInvitationJoinView.as_view()),
    path(
        "group-invitations/<uuid:invitation_id>/",
        groups.GroupInvitationDetailView.as_view(),
    ),
    path("housing-requests/", housing.HousingRequestsView.as_view()),
    path("housing-demand/", housing.HousingDemandView.as_view()),
    path("owner-housing-offers/", housing.OwnerHousingOffersView.as_view()),
    path(
        "housing-requests/<uuid:request_id>/",
        housing.HousingRequestDetailView.as_view(),
    ),
    path(
        "housing-requests/<uuid:request_id>/changes/",
        housing.HousingRequestChangesView.as_view(),
    ),
    path("housing-offers/<uuid:offer_id>/", housing.HousingOfferDetailView.as_view()),
    path(
        "housing-requests/<uuid:request_id>/offers/",
        housing.HousingOffersView.as_view(),
    ),
    path(
        "housing-requests/<uuid:request_id>/offer-inventory/<uuid:property_id>/",
        HousingOfferInventoryView.as_view(),
    ),
    path(
        "housing-requests/<uuid:request_id>/<slug:action>/",
        housing.HousingRequestActionView.as_view(),
    ),
    path(
        "housing-offers/<uuid:offer_id>/<slug:action>/",
        housing.HousingOfferActionView.as_view(),
    ),
    path(
        "leases/<uuid:lease_id>/condition-report-context/",
        conditions.ConditionReportContextView.as_view(),
    ),
    path(
        "leases/<uuid:lease_id>/condition-reports/",
        conditions.ConditionReportsView.as_view(),
    ),
    path(
        "condition-reports/<uuid:report_id>/",
        conditions.ConditionReportDetailView.as_view(),
    ),
    path(
        "condition-reports/<uuid:report_id>/<slug:action>/",
        conditions.ConditionReportActionView.as_view(),
    ),
    path(
        "leases/<uuid:lease_id>/move-out-notices/",
        transitions.MoveOutNoticesView.as_view(),
    ),
    path(
        "leases/<uuid:lease_id>/replacement-requests/",
        transitions.ReplacementRequestsView.as_view(),
    ),
    path(
        "leases/<uuid:lease_id>/replacement-candidates/",
        transitions.ReplacementCandidatesView.as_view(),
    ),
    path(
        "move-out-notices/<uuid:transition_id>/",
        transitions.TransitionDetailActionView.as_view(),
        {"kind": "moveOutNotice"},
    ),
    path(
        "move-out-notices/<uuid:transition_id>/<slug:action>/",
        transitions.TransitionDetailActionView.as_view(),
        {"kind": "moveOutNotice"},
    ),
    path(
        "replacement-requests/<uuid:transition_id>/",
        transitions.TransitionDetailActionView.as_view(),
        {"kind": "replacement"},
    ),
    path(
        "replacement-requests/<uuid:transition_id>/candidate-consent/",
        transitions.ReplacementCandidateConsentView.as_view(),
    ),
    path(
        "replacement-requests/<uuid:transition_id>/<slug:action>/",
        transitions.TransitionDetailActionView.as_view(),
        {"kind": "replacement"},
    ),
    path("replacement-invitations/", transitions.ReplacementInvitationsView.as_view()),
    path("commute-searches/", discovery.CommuteSearchesView.as_view()),
    path("commute-searches/<uuid:search_id>/", discovery.CommuteDetailView.as_view()),
    path(
        "commute-searches/<uuid:search_id>/cancel/",
        discovery.CommuteCancelView.as_view(),
    ),
    path(
        "commute-searches/<uuid:search_id>/results/",
        discovery.CommuteResultsView.as_view(),
    ),
    path("tenant-assistant/turns/", discovery.TenantAssistantTurnsView.as_view()),
]

from . import shared_housing_views as shared_housing

urlpatterns += [
    path("shared-housing-plans/", shared_housing.PlansView.as_view()),
    path("shared-housing-plans/<uuid:plan_id>/", shared_housing.DetailView.as_view()),
    path(
        "shared-housing-plans/<uuid:plan_id>/proposals/",
        shared_housing.ProposalsView.as_view(),
    ),
    path(
        "shared-housing-plans/<uuid:plan_id>/proposals/<uuid:proposal_id>/<slug:action>/",
        shared_housing.ProposalActionView.as_view(),
    ),
    path(
        "shared-housing-plans/<uuid:plan_id>/<slug:action>/",
        shared_housing.ActionView.as_view(),
    ),
    path("shared-housing-demand/", shared_housing.DemandView.as_view()),
    path(
        "owner-shared-housing-applications/", shared_housing.ApplicationsView.as_view()
    ),
]
