from .views.public_owner import PublicOwnerProfileView, PublicOwnerListingsView
from .views.home_visit_reminder import HomeVisitReminderAPIView
from .views.operation_recovery import PropertyOperationRecovery
from django.urls import path
from .views.districts import DistrictListAPIView
from .views.viewing_commands import (
    ViewingCommandAPIView,
    ViewingReceiptAPIView,
    ResolveViewingCommandAPIView,
)
from .views.viewing_representatives import RepresentativesAPIView
from .views.post_visit_decision import PostVisitDecisionAPIView
from .views.ownership_proof import PropertyOwnershipProofAPIView

from .views import (
    CityListAPIView,
    GovernorateListAPIView,
    MyPropertyListAPIView,
    OwnerDashboardAPIView,
    OwnerProfileAPIView,
    OwnerRevenuesAPIView,
    PropertyCreateAPIView,
    PropertyDeleteAPIView,
    PropertyDetailAPIView,
    PropertyFilterOptionsAPIView,
    PropertyImageDetailAPIView,
    PropertyImageUploadAPIView,
    PropertyListAPIView,
    PropertyNewListAPIView,
    PropertyTypeListAPIView,
    PropertyUpdateAPIView,
    PropertyStatisticsAPIView,
    PropertyToggleVisibilityAPIView,
    PropertyVisitCreateAPIView,
    TenantPropertyVisitListAPIView,
    OwnerPropertyVisitListAPIView,
    PropertyVisitDetailAPIView,
    PropertyVisitUpdateAPIView,
    PropertyVisitCancelAPIView,
    PropertyVisitReviewCreateAPIView,
    PropertyReviewListAPIView,
    TenantVisitRequestDetailAPIView,
    TenantVisitRequestListAPIView,
    OwnerVisitRequestListAPIView,
    OwnerVisitRequestDetailAPIView,
    OwnerVisitRequestRejectAPIView,
    OwnerVisitRequestAcceptAPIView,
    AvailablePlacesAPIView,
    SavedPropertyCreateAPIView,
    SavedPropertyDeleteAPIView,
    SavedPropertyListAPIView,
    ConfirmPropertyAvailabilityAPIView,
)

from .views.image_order import OrderImagesAPIView
from .views.owner_availability import OwnerAvailabilityAPIView
from .views.hidden_listings import HiddenListingsAPIView
from .views.saved_search_reads import AcknowledgeSavedSearchAPIView
from .views.owner_draft_review import OwnerDraftReviewAPIView
from .views.availability_closures import AvailabilityClosuresAPIView
from .views.viewing_times import ViewingTimesAPIView
from .views.viewing_arrival import ViewingArrivalAPIView
from .views.viewing_day_plan import ViewingDayPlanAPIView
from .views.viewing_message_context import ViewingMessageContextAPIView

urlpatterns = [
    path(
        "<uuid:property_id>/ownership-proof/",
        PropertyOwnershipProofAPIView.as_view(),
        name="property-ownership-proof",
    ),
    path(
        "visits/<uuid:visit_id>/message-context/",
        ViewingMessageContextAPIView.as_view(),
        name="viewing-message-context",
    ),
    path("visits/day-plan/", ViewingDayPlanAPIView.as_view(), name="viewing-day-plan"),
    path(
        "visits/<uuid:visit_id>/arrival/",
        ViewingArrivalAPIView.as_view(),
        name="viewing-arrival",
    ),
    path(
        "visits/<uuid:visit_id>/time-proposals/",
        ViewingTimesAPIView.as_view(),
        name="viewing-time-proposals",
    ),
    path(
        "owner/properties/<uuid:property_id>/availability/closures/",
        AvailabilityClosuresAPIView.as_view(),
        name="availability-closures",
    ),
    path(
        "owner/properties/<uuid:property_id>/draft-review/",
        OwnerDraftReviewAPIView.as_view(),
        name="owner-draft-review",
    ),
    path(
        "saved-search-reads/<uuid:read_id>/ack/",
        AcknowledgeSavedSearchAPIView.as_view(),
        name="saved-search-read-ack",
    ),
    path("hidden-listings/", HiddenListingsAPIView.as_view(), name="hidden-listings"),
    path(
        "owner/properties/<uuid:property_id>/availability/",
        OwnerAvailabilityAPIView.as_view(),
    ),
    path("owners/<uuid:identity>/profile/", PublicOwnerProfileView.as_view()),
    path("owners/<uuid:identity>/listings/", PublicOwnerListingsView.as_view()),
    path(
        "visits/home-reminder/",
        HomeVisitReminderAPIView.as_view(),
        name="home-visit-reminder",
    ),
    path("<uuid:property_id>/images/order/", OrderImagesAPIView.as_view()),
    path(
        "operation-recovery/",
        PropertyOperationRecovery.as_view(),
        name="property-operation-recovery",
    ),
    path(
        "viewing-companies/<uuid:company_id>/representatives/",
        RepresentativesAPIView.as_view(),
        name="viewing-representatives",
    ),
    path(
        "visits/creation-receipt/",
        ViewingReceiptAPIView.as_view(),
        name="viewing-creation-receipt",
    ),
    path(
        "visits/<uuid:id>/commands/",
        ViewingCommandAPIView.as_view(),
        name="viewing-command",
    ),
    path(
        "visits/<uuid:id>/commands/resolve/",
        ResolveViewingCommandAPIView.as_view(),
        name="viewing-command-resolve",
    ),
    path(
        "cities/<uuid:city_id>/districts/",
        DistrictListAPIView.as_view(),
        name="district-list",
    ),
    path(
        "visits/<uuid:id>/post-visit-decision/",
        PostVisitDecisionAPIView.as_view(),
        name="post-visit-decision",
    ),
    path("governorates/", GovernorateListAPIView.as_view(), name="governorate-list"),
    path("cities/", CityListAPIView.as_view(), name="city-list"),
    path("types/", PropertyTypeListAPIView.as_view(), name="property-type-list"),
    path(
        "filter-options/",
        PropertyFilterOptionsAPIView.as_view(),
        name="property-filter-options",
    ),
    path(
        "available_places/",
        AvailablePlacesAPIView.as_view(),
        name="property-available-places",
    ),
    path("", PropertyNewListAPIView.as_view(), name="property-list"),
    path("create/", PropertyCreateAPIView.as_view(), name="property-create"),
    path("owned/", MyPropertyListAPIView.as_view(), name="my-property-list"),
    path("saved/", SavedPropertyListAPIView.as_view(), name="saved-property-list"),
    path("owner/dashboard/", OwnerDashboardAPIView.as_view(), name="owner-dashboard"),
    path("owner/profile/", OwnerProfileAPIView.as_view(), name="owner-profile"),
    path("owner/revenues/", OwnerRevenuesAPIView.as_view(), name="owner-revenues"),
    path("owner/earnings/", OwnerRevenuesAPIView.as_view(), name="owner-earnings"),
    path(
        "owner/visits/requests/",
        OwnerVisitRequestListAPIView.as_view(),
        name="owner-visit-request-list",
    ),
    path(
        "owner/visits/requests/<uuid:id>/",
        OwnerVisitRequestDetailAPIView.as_view(),
        name="owner-visit-request-detail",
    ),
    path(
        "owner/visits/requests/<uuid:id>/reject/",
        OwnerVisitRequestRejectAPIView.as_view(),
        name="owner-visit-request-reject",
    ),
    path(
        "owner/visits/requests/<uuid:id>/accept/",
        OwnerVisitRequestAcceptAPIView.as_view(),
        name="owner-visit-request-accept",
    ),
    path("<uuid:id>/", PropertyDetailAPIView.as_view(), name="property-detail"),
    path(
        "<uuid:property_id>/save/",
        SavedPropertyCreateAPIView.as_view(),
        name="saved-property-create",
    ),
    path(
        "<uuid:property_id>/unsave/",
        SavedPropertyDeleteAPIView.as_view(),
        name="saved-property-delete",
    ),
    path(
        "<uuid:property_id>/confirm-availability/",
        ConfirmPropertyAvailabilityAPIView.as_view(),
        name="property-confirm-availability",
    ),
    path(
        "<uuid:property_id>/reviews/",
        PropertyReviewListAPIView.as_view(),
        name="property-review-list",
    ),
    path("<uuid:id>/update/", PropertyUpdateAPIView.as_view(), name="property-update"),
    path("<uuid:id>/delete/", PropertyDeleteAPIView.as_view(), name="property-delete"),
    path(
        "<uuid:id>/statistics/",
        PropertyStatisticsAPIView.as_view(),
        name="property-statistics",
    ),
    path(
        "<uuid:id>/visibility/",
        PropertyToggleVisibilityAPIView.as_view(),
        name="property-toggle-visibility",
    ),
    path(
        "<uuid:property_id>/images/",
        PropertyImageUploadAPIView.as_view(),
        name="property-image-upload",
    ),
    path(
        "images/<uuid:id>/",
        PropertyImageDetailAPIView.as_view(),
        name="property-image-detail",
    ),
    # Property Visits (Bookings) URLs
    path(
        "<uuid:property_id>/visits/",
        PropertyVisitCreateAPIView.as_view(),
        name="property-visit-create",
    ),
    path(
        "visits/",
        TenantPropertyVisitListAPIView.as_view(),
        name="tenant-visit-list",
    ),
    path(
        "visits/received/",
        OwnerPropertyVisitListAPIView.as_view(),
        name="owner-visit-list",
    ),
    path(
        "visits/requests/",
        TenantVisitRequestListAPIView.as_view(),
        name="tenant-visit-request-list",
    ),
    path(
        "visits/requests/<uuid:id>/",
        TenantVisitRequestDetailAPIView.as_view(),
        name="tenant-visit-request-detail",
    ),
    path(
        "visits/<uuid:id>/cancel/",
        PropertyVisitCancelAPIView.as_view(),
        name="property-visit-cancel",
    ),
    path(
        "visits/<uuid:id>/review/",
        PropertyVisitReviewCreateAPIView.as_view(),
        name="property-visit-review-create",
    ),
    path(
        "visits/<uuid:id>/",
        PropertyVisitDetailAPIView.as_view(),
        name="property-visit-detail",
    ),
    path(
        "visits/<uuid:id>/update/",
        PropertyVisitUpdateAPIView.as_view(),
        name="property-visit-update",
    ),
]
