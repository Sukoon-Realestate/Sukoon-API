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
    path("terms-proposals/<uuid:proposal_id>/propose-answer/", terms.propose_answer),
    path("operations/verification-claims/", claims.verification_claims),
    path("operations/verification-claims/<uuid:claim_id>/revoke/", claims.revoke_claim),
    path("operations/rental-cases/", cases.rental_cases, {"operations": True}),
    path(
        "operations/rental-cases/<uuid:case_id>/actions/",
        cases.rental_case,
        {"operations": True},
    ),
    path("group-booking-proposals/", group_bookings.group_bookings),
    path("group-booking-proposals/<uuid:booking_id>/", group_bookings.group_booking),
    path(
        "group-booking-proposals/<uuid:booking_id>/submit/",
        group_bookings.group_booking,
        {"action": "submit_group_booking"},
    ),
    path(
        "group-booking-proposals/<uuid:booking_id>/consents/",
        group_bookings.group_booking,
        {"action": "consent_group_booking"},
    ),
    path(
        "group-booking-proposals/<uuid:booking_id>/withdraw/",
        group_bookings.group_booking,
        {"action": "withdraw_group_booking"},
    ),
    path("application-profile/", applications.application_profile),
    path("application-profile/versions/", applications.application_version),
    path(
        "application-profile/versions/<uuid:version_id>/",
        applications.application_version_detail,
    ),
    path("application-shares/preview/", applications.application_share_review),
    path("application-shares/", applications.application_shares),
    path("application-shares/<uuid:share_id>/", applications.application_share),
    path("application-shares/<uuid:share_id>/revoke/", applications.application_share),
    path(
        "properties/<uuid:property_id>/decision-summary/", decisions.property_decision
    ),
    path("properties/<uuid:property_id>/decision-facts/", decisions.property_fact),
    path(
        "properties/<uuid:property_id>/availability-confirmation/",
        decisions.availability_confirmation,
    ),
    path("availability-blocks/", reservations.reservation_holds, {"external": True}),
    path("reservation-holds/", reservations.reservation_holds),
    path("reservation-holds/<uuid:hold_id>/", reservations.reservation_hold),
    path(
        "reservation-holds/<uuid:hold_id>/extend/",
        reservations.reservation_hold,
        {"action": "extend_hold"},
    ),
    path(
        "reservation-holds/<uuid:hold_id>/release/",
        reservations.reservation_hold,
        {"action": "release_hold"},
    ),
    path("deals/<uuid:subject_id>/", deals.rental_deal),
    path("owner-application-queue/", deals.owner_application_queue),
    path("move-in-cases/", cases.rental_cases),
    path("rental-cases/", cases.rental_cases),
    path("rental-cases/<uuid:case_id>/", cases.rental_case),
    path("rental-cases/<uuid:case_id>/actions/", cases.rental_case),
]
