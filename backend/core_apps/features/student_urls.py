from django.urls import path
from . import student_views as views
from . import student_verification_views as verification
from . import rental_summary_views as sharing

urlpatterns = [
    path("shared-rental-summaries/", sharing.SummaryGrantsView.as_view()),
    path(
        "leases/<uuid:lease_id>/summary-sharing-options/",
        sharing.SummaryOptionsView.as_view(),
    ),
    path("leases/<uuid:lease_id>/summary-grants/", sharing.SummaryGrantsView.as_view()),
    path(
        "rental-summary-grants/<uuid:grant_id>/revoke/",
        sharing.RevokeSummaryView.as_view(),
    ),
    path("student-evidence/", verification.StudentEvidenceView.as_view()),
    path("student-evidence/upload/", verification.StudentEvidenceUploadView.as_view()),
    path(
        "student-evidence/<uuid:evidence_id>/metadata/",
        verification.StudentEvidenceMetadataView.as_view(),
    ),
    path(
        "student-evidence/<uuid:evidence_id>/",
        verification.StudentEvidenceView.as_view(),
    ),
    path("operations/student-verifications/", verification.StudentReviewView.as_view()),
    path(
        "operations/student-verifications/<uuid:profile_id>/review/",
        verification.StudentReviewView.as_view(),
    ),
    path("student-profile/", views.StudentProfileView.as_view()),
    path("campuses/", views.CampusesView.as_view()),
    path("academic-plans/", views.AcademicPlansView.as_view()),
    path("academic-plans/<uuid:plan_id>/", views.AcademicPlanView.as_view()),
    path("academic-plans/<uuid:plan_id>/history/", views.PlanHistoryView.as_view()),
    path(
        "academic-plans/<uuid:plan_id>/publication-preview/",
        views.PlanPreviewView.as_view(),
    ),
    path(
        "academic-plans/<uuid:plan_id>/arrangements/",
        views.LivingArrangementsView.as_view(),
    ),
    path(
        "academic-plans/<uuid:plan_id>/<slug:action>/", views.PlanActionView.as_view()
    ),
    path(
        "student-arrangements/<uuid:arrangement_id>/",
        views.LivingArrangementView.as_view(),
    ),
    path(
        "student-arrangements/<uuid:arrangement_id>/<slug:action>/",
        views.LivingArrangementView.as_view(),
    ),
    path(
        "properties/<uuid:property_id>/student-policies/",
        views.StudentOfferPolicyView.as_view(),
    ),
]
