"""Account-scoped pending inbox totals, independent of collection pagination.

These are outstanding incoming requests, not read receipts or permission grants.
Opening a collection does not resolve a request. The normal command endpoints
remain responsible for checking current authority and completing a response.
"""

from django.db.models import Count, F, OuterRef, Q, Subquery
from django.utils import timezone


def pending_request_counts(user, *, owner=False):
    from ..models import RentalInterest, TenancyInvitation, TermsProposal
    from ..planning_models import (
        GroupProcess,
        HousingOffer,
        RoommateConnection,
        TenancyTransition,
    )

    if not user.is_active or not user.is_verified:
        return {}
    from .shared_housing.counts import pending_count
    from .housing_request_reviews import LIVE

    shared_count = pending_count(user, owner=owner)
    interests = RentalInterest.objects.filter(
        Q(shared_allocation__isnull=True)
        | Q(shared_allocation__proposal__plan__status="handed_off")
    ).annotate(
        latest_proposal_status=Subquery(
            TermsProposal.objects.filter(interest_id=OuterRef("pk"))
            .order_by("-created_at", "-id")
            .values("status")[:1]
        )
    )
    if owner:
        return {
            "housing_offers": HousingOffer.objects.filter(
                owner=user,
                status__in=LIVE,
                review_state__in=["pending_reconfirm", "incompatible"],
                request__status="published",
                request__expires_at__gt=timezone.now(),
                tender_line__isnull=True,
            ).count(),
            "shared_housing_plans": shared_count,
            "rental_interests": interests.filter(
                Q(status__in=["submitted", "under_review"], waiting_for="owner")
                | Q(status="proposed", latest_proposal_status="changes_requested"),
                property__owner=user,
            ).count(),
            "group_applications": GroupProcess.objects.filter(
                property__owner=user,
                kind="application",
                status="under_review",
                group__status="active",
            ).count(),
        }
    now = timezone.now()
    return {
        "shared_housing_plans": shared_count,
        "roommate_connections": RoommateConnection.objects.filter(
            Q(first=user) | Q(second=user), status="pending"
        )
        .exclude(requester=user)
        .count(),
        "tenancy_invitations": TenancyInvitation.objects.filter(
            tenant=user,
            status="pending",
            expires_at__gt=now,
            consumed_at__isnull=True,
            lease__isnull=True,
        ).count(),
        "rental_interests": interests.filter(
            Q(status__in=["submitted", "under_review"], waiting_for="tenant")
            | Q(status="proposed", latest_proposal_status="proposed"),
            tenant=user,
        ).count(),
        "housing_offers": HousingOffer.objects.filter(
            request__user=user,
            status__in=LIVE,
            request__status="published",
            request__expires_at__gt=now,
            reviewed_content_revision=F("request__content_revision"),
            review_state="current",
            tender_line__isnull=True,
        ).count(),
        "replacement_invitations": TenancyTransition.objects.filter(
            candidate__tenant=user,
            kind="replacement",
            status="candidate_pending",
            candidate_revision=F("candidate__revision"),
        ).count(),
    }


def company_approval_counts(user):
    from ..company_models import CompanyBookingItem

    if not user.is_active or not user.is_verified:
        return {}
    rows = (
        CompanyBookingItem.objects.filter(
            status="approval_pending",
            assigned_approver__user=user,
            assigned_approver__is_active=True,
            assigned_approver__is_approver=True,
            assigned_approver__company=F("request__company"),
        )
        .values("request__company__id")
        .annotate(total=Count("pk"))
    )
    from .company.role_context import http_context
    from .company.role_notifications import audience_current

    request = http_context(user)
    if request is not None:
        company_id = request.headers.get("X-Sukoon-Company-Id", "")
        if request.headers.get(
            "X-Sukoon-Company-Role"
        ) != "approver" or not audience_current(
            user, {"company_id": company_id, "company_role": "approver"}
        ):
            return {}
        rows = rows.filter(request__company__id=company_id)
    return {str(row["request__company__id"]): row["total"] for row in rows}
