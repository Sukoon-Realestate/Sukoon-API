from django.urls import path
from . import student_views as views
from . import student_verification_views as verification
from . import rental_summary_views as sharing

urlpatterns = [
    path("shared-rental-summaries/", sharing.summary_grants),
    path("leases/<uuid:lease_id>/summary-sharing-options/", sharing.summary_options),
    path("leases/<uuid:lease_id>/summary-grants/", sharing.summary_grants),
    path("rental-summary-grants/<uuid:grant_id>/revoke/", sharing.revoke_summary),
    path("student-evidence/", verification.student_evidence),
    path("student-evidence/upload/", verification.student_evidence_upload),
    path(
        "student-evidence/<uuid:evidence_id>/metadata/",
        verification.student_evidence_metadata,
    ),
    path("student-evidence/<uuid:evidence_id>/", verification.student_evidence),
    path("operations/student-verifications/", verification.student_review),
    path(
        "operations/student-verifications/<uuid:profile_id>/review/",
        verification.student_review,
    ),
    path("student-profile/", views.student_profile),
    path("campuses/", views.campuses),
    path("academic-plans/", views.academic_plans),
    path("academic-plans/<uuid:plan_id>/", views.academic_plan),
    path("academic-plans/<uuid:plan_id>/history/", views.plan_history),
    path("academic-plans/<uuid:plan_id>/publication-preview/", views.plan_preview),
    path("academic-plans/<uuid:plan_id>/arrangements/", views.living_arrangements),
    path("academic-plans/<uuid:plan_id>/<slug:action>/", views.plan_action),
    path("student-arrangements/<uuid:arrangement_id>/", views.living_arrangement),
    path(
        "student-arrangements/<uuid:arrangement_id>/<slug:action>/",
        views.living_arrangement,
    ),
    path("properties/<uuid:property_id>/student-policies/", views.student_offer_policy),
]
