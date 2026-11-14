from django.urls import path
from .rental_lifecycle_views import (
    applications,
    reservations,
    decisions,
    deals,
    cases,
    group_bookings,
)
from .rental_lifecycle_views import claims, terms

urlpatterns = [
    path(
        "terms-proposals/<uuid:proposal_id>/propose-answer/",
        terms.ProposeAnswerView.as_view(),
    ),
    path("operations/verification-claims/", claims.VerificationClaimsView.as_view()),
    path(
        "operations/verification-claims/<uuid:claim_id>/revoke/",
        claims.RevokeClaimView.as_view(),
    ),
    path(
        "operations/rental-cases/",
        cases.RentalCasesView.as_view(),
        {"operations": True},
    ),
    path(
        "operations/rental-cases/<uuid:case_id>/actions/",
        cases.RentalCaseView.as_view(),
        {"operations": True},
    ),
    path("group-booking-proposals/", group_bookings.GroupBookingsView.as_view()),
    path(
        "group-booking-proposals/<uuid:booking_id>/",
        group_bookings.GroupBookingView.as_view(),
    ),
    path(
        "group-booking-proposals/<uuid:booking_id>/submit/",
        group_bookings.GroupBookingView.as_view(),
        {"action": "submit_group_booking"},
    ),
    path(
        "group-booking-proposals/<uuid:booking_id>/consents/",
        group_bookings.GroupBookingView.as_view(),
        {"action": "consent_group_booking"},
    ),
    path(
        "group-booking-proposals/<uuid:booking_id>/withdraw/",
        group_bookings.GroupBookingView.as_view(),
        {"action": "withdraw_group_booking"},
    ),
    path("application-profile/", applications.ApplicationProfileView.as_view()),
    path(
        "application-profile/versions/", applications.ApplicationVersionView.as_view()
    ),
    path(
        "application-profile/versions/<uuid:version_id>/",
        applications.ApplicationVersionDetailView.as_view(),
    ),
    path(
        "application-shares/preview/", applications.ApplicationShareReviewView.as_view()
    ),
    path("application-shares/", applications.ApplicationSharesView.as_view()),
    path(
        "application-shares/<uuid:share_id>/",
        applications.ApplicationShareView.as_view(),
    ),
    path(
        "application-shares/<uuid:share_id>/revoke/",
        applications.ApplicationShareView.as_view(),
    ),
    path(
        "properties/<uuid:property_id>/decision-summary/",
        decisions.PropertyDecisionView.as_view(),
    ),
    path(
        "properties/<uuid:property_id>/decision-facts/",
        decisions.PropertyFactView.as_view(),
    ),
    path(
        "properties/<uuid:property_id>/availability-confirmation/",
        decisions.AvailabilityConfirmationView.as_view(),
    ),
    path(
        "availability-blocks/",
        reservations.ReservationHoldsView.as_view(),
        {"external": True},
    ),
    path("reservation-holds/", reservations.ReservationHoldsView.as_view()),
    path(
        "reservation-holds/<uuid:hold_id>/", reservations.ReservationHoldView.as_view()
    ),
    path(
        "reservation-holds/<uuid:hold_id>/extend/",
        reservations.ReservationHoldView.as_view(),
        {"action": "extend_hold"},
    ),
    path(
        "reservation-holds/<uuid:hold_id>/release/",
        reservations.ReservationHoldView.as_view(),
        {"action": "release_hold"},
    ),
    path("deals/<uuid:subject_id>/", deals.RentalDealView.as_view()),
    path("owner-application-queue/", deals.OwnerApplicationQueueView.as_view()),
    path("move-in-cases/", cases.RentalCasesView.as_view()),
    path("rental-cases/", cases.RentalCasesView.as_view()),
    path("rental-cases/<uuid:case_id>/", cases.RentalCaseView.as_view()),
    path("rental-cases/<uuid:case_id>/actions/", cases.RentalCaseView.as_view()),
]

urlpatterns += [
    path(
        f"group-booking-proposals/<uuid:booking_id>/terms/{suffix}/",
        group_bookings.GroupBookingView.as_view(),
        {"action": action},
    )
    for suffix, action in [
        ("edit", "edit_group_terms"),
        ("counter", "counter_group_terms"),
        ("accept", "accept_group_terms"),
        ("reject", "reject_group_terms"),
        ("request-changes", "request_group_terms_changes"),
        ("withdraw", "withdraw_group_terms"),
    ]
]
