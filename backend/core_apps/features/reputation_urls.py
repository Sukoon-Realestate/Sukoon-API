from django.urls import path
from . import reputation_views as v

urlpatterns = [
    path("reviews/capabilities/", v.ReviewCapabilitiesView.as_view()),
    path("reviews/opportunities/", v.ReviewOpportunitiesView.as_view()),
    path("reviews/opportunities/<uuid:identity>/", v.ReviewOpportunityView.as_view()),
    path("reviews/opportunities/<uuid:identity>/draft/", v.ReviewDraftView.as_view()),
    path("reviews/opportunities/<uuid:identity>/submit/", v.ReviewSubmitView.as_view()),
    path(
        "reviews/operations/by-key/<str:request_key>/", v.ReviewOperationView.as_view()
    ),
    path("reviews/mine/", v.ReviewCollectionView.as_view(), {"collection": "mine"}),
    path(
        "reviews/received/",
        v.ReviewCollectionView.as_view(),
        {"collection": "received"},
    ),
    path(
        "reviews/subjects/<str:kind>/<uuid:identity>/summary/",
        v.ReviewSubjectView.as_view(),
        {"aggregate": True},
    ),
    path("reviews/subjects/<str:kind>/<uuid:identity>/", v.ReviewSubjectView.as_view()),
    path("reviews/eligibility-requests/", v.ReviewEligibilityRequestView.as_view()),
    path("reviews/<uuid:identity>/", v.ReviewDetailView.as_view()),
    *[
        path(
            f"reviews/<uuid:identity>/{action}/",
            v.ReviewActionView.as_view(),
            {"action": action},
        )
        for action in ["reply", "withdraw", "reports"]
    ],
    path(
        "reviews/replies/<uuid:identity>/withdraw/", v.ReviewReplyWithdrawView.as_view()
    ),
    path(
        "reviews/moderation-decisions/<uuid:identity>/appeals/",
        v.ReviewAppealView.as_view(),
    ),
    path("reviews/cases/", v.ReviewCaseHistoryView.as_view()),
    path("reviews/cases/<uuid:identity>/", v.ReviewCaseView.as_view()),
    path("reputation-grants/recipients/", v.ReputationRecipientsView.as_view()),
    path("reputation-grants/", v.ReputationGrantsView.as_view()),
    path("reputation-grants/<uuid:identity>/revoke/", v.ReputationGrantView.as_view()),
    path("reputation-grants/<uuid:identity>/summary/", v.ReputationGrantView.as_view()),
]

from . import reputation_experience_views as experiences

urlpatterns += [
    path(
        "reviews/portfolios/<str:kind>/<uuid:identity>/summary/",
        experiences.PortfolioReviewsView.as_view(),
        {"aggregate": True},
    ),
    path(
        "reviews/portfolios/<str:kind>/<uuid:identity>/",
        experiences.PortfolioReviewsView.as_view(),
    ),
    path(
        "reviews/properties/<uuid:identity>/portfolios/",
        experiences.PropertyPortfolioLinksView.as_view(),
    ),
    path("reviews/company-bindings/", experiences.CompanyBindingsView.as_view()),
    path(
        "reviews/company-bindings/<uuid:identity>/",
        experiences.CompanyBindingView.as_view(),
    ),
    path(
        "reviews/company-bindings/<uuid:identity>/authorities/",
        experiences.CompanyAuthoritiesView.as_view(),
    ),
    path(
        "reviews/company-bindings/<uuid:identity>/assignments/",
        experiences.CompanyAssignmentsView.as_view(),
    ),
    path("reviews/employee-assignments/", experiences.CompanyAssignmentsView.as_view()),
    path(
        "reviews/employee-assignments/<uuid:identity>/",
        experiences.EmployeeOccupancyView.as_view(),
    ),
    path(
        "reviews/occupancy-confirmations/<uuid:identity>/confirm/",
        experiences.EmployeeOccupancyConfirmView.as_view(),
    ),
    path(
        "reviews/ownership-transitions/", experiences.OwnershipTransitionsView.as_view()
    ),
    path(
        "reviews/ownership-transitions/<uuid:identity>/",
        experiences.OwnershipTransitionView.as_view(),
    ),
    path("reviews/experience-choices/", experiences.ExperienceChoicesView.as_view()),
]
