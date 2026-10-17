"""Thin adapters for confirmed experience records and historical rollups."""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from .reputation_views import ReviewView, identity
from .models import (
    CompanyLeaseBinding,
    CompanyMembership,
    EmployeeAssignment,
    LeaseResponsibilityTransition,
    Lease,
    CompanyBookingItem,
    RentalEvidence,
)
from .services.reputation import (
    company_bindings as bindings,
    employee_occupancy as occupancy,
    responsibility,
    rollups,
    recovery,
    visibility,
)
from .services.reputation.company_authority import membership


class ExperienceView(ReviewView):
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method in {"POST", "PUT", "PATCH"}:
            for name in (
                "lease_id",
                "booking_id",
                "renter_company_id",
                "landlord_company_id",
                "membership_id",
                "employee_id",
                "evidence_id",
                "source_id",
            ):
                if name in request.data:
                    identity(request.data[name])


class PortfolioReviewsView(ReviewView):
    permission_classes = [AllowAny]

    def get(self, request, kind, identity, aggregate=False):
        summary = rollups.summary(kind, identity)
        if aggregate:
            return Response(summary)
        rows = rollups.rows(kind, identity)
        rating = request.query_params.get("rating")
        if rating:
            rows = [r for r in rows if str(r.overall_score) == rating]
        return self.page(
            request, rows, lambda r: visibility.section_payload(r, public_only=True)
        )


class PropertyPortfolioLinksView(ReviewView):
    permission_classes = [AllowAny]

    def get(self, request, identity):
        return Response({"results": rollups.property_links(identity)})


class CompanyBindingsView(ExperienceView):
    def get(self, request):
        member_companies = (
            CompanyMembership.objects.filter(user=request.user, is_active=True)
            .filter(Q(is_admin=True) | Q(is_coordinator=True))
            .values("company_id")
        )
        query = CompanyLeaseBinding.objects.filter(
            Q(lease__owner=request.user)
            | Q(lease__tenant=request.user)
            | Q(renter_company_id__in=member_companies)
            | Q(landlord_company_id__in=member_companies)
            | Q(lease__responsibility_transitions__next_owner=request.user)
        ).distinct()
        company_id = request.query_params.get("company_id")
        if company_id:
            query = query.filter(
                Q(renter_company__id=identity(company_id))
                | Q(landlord_company__id=identity(company_id))
            )
        return self.page(
            request,
            [
                x
                for x in query.order_by("-created_at")
                if bindings.can_read(request.user, x)
            ],
            lambda x: bindings.payload(x, request.user),
        )

    def post(self, request):
        return Response(bindings.propose(request.user, request.data), status=201)


class CompanyBindingView(ExperienceView):
    def get(self, request, identity):
        return Response(
            bindings.payload(bindings.get(request.user, identity), request.user)
        )

    def post(self, request, identity):
        return Response(bindings.confirm(request.user, identity, request.data))


class CompanyAuthoritiesView(ExperienceView):
    def get(self, request, identity):
        item = bindings.get(request.user, identity)
        company = get_object_or_404(
            CompanyMembership,
            company__id=request.query_params.get("company_id"),
            user=request.user,
            is_active=True,
            is_admin=True,
        ).company
        if company.pk not in {item.renter_company_id, item.landlord_company_id}:
            raise NotFound()
        records = {
            x.membership_id: x
            for x in item.review_authorities.filter(membership__company=company)
        }

        def payload(member):
            record = records.get(member.pk)
            return {
                "id": str(member.id),
                "name": member.user.get_full_name,
                "revision": record.revision if record else 0,
                "is_active": bool(record and record.is_active),
                "can_submit": bool(record and record.can_submit),
                "can_view_reputation": bool(record and record.can_view_reputation),
            }

        return self.page(
            request,
            company.memberships.filter(is_active=True)
            .select_related("user")
            .order_by("id"),
            payload,
        )

    def post(self, request, identity):
        return Response(bindings.authority(request.user, identity, request.data))


class CompanyAssignmentsView(ExperienceView):
    def get(self, request, identity=None):
        if identity:
            item = bindings.get(request.user, identity)
            query = EmployeeAssignment.objects.filter(item=item.booking)
        else:
            query = EmployeeAssignment.objects.filter(
                employee=request.user, item__confirmed_lease_binding__state="accepted"
            )
        return self.page(
            request,
            query.order_by("-created_at"),
            lambda x: occupancy.payload(x, request.user),
        )

    def post(self, request, identity):
        return Response(
            occupancy.assign(request.user, identity, request.data), status=201
        )


class EmployeeOccupancyView(ExperienceView):
    def get(self, request, identity):
        return Response(
            occupancy.payload(
                get_object_or_404(EmployeeAssignment, id=identity), request.user
            )
        )

    def post(self, request, identity):
        return Response(
            occupancy.propose(request.user, identity, request.data), status=201
        )


class EmployeeOccupancyConfirmView(ExperienceView):
    def post(self, request, identity):
        return Response(occupancy.confirm(request.user, identity, request.data))


class OwnershipTransitionsView(ExperienceView):
    def get(self, request):
        query = LeaseResponsibilityTransition.objects.filter(
            Q(previous_owner=request.user)
            | Q(next_owner=request.user)
            | Q(tenant=request.user)
        )
        return self.page(
            request,
            query.order_by("-created_at"),
            lambda x: responsibility.payload(x, request.user),
        )

    def post(self, request):
        return Response(
            responsibility.propose(
                request.user, identity(request.data.get("lease_id")), request.data
            ),
            status=201,
        )


class OwnershipTransitionView(ExperienceView):
    def get(self, request, identity):
        return Response(
            responsibility.payload(
                get_object_or_404(LeaseResponsibilityTransition, id=identity),
                request.user,
            )
        )

    def post(self, request, identity):
        return Response(responsibility.confirm(request.user, identity, request.data))


class ExperienceChoicesView(ReviewView):
    def get(self, request):
        kind = request.query_params.get("kind")
        company_id = request.query_params.get("company_id")
        if kind == "leases":
            query = Lease.objects.filter(
                Q(owner=request.user)
                | Q(tenant=request.user)
                | Q(property__owner=request.user),
                legacy_read_only=False,
            )
            return self.page(
                request,
                query.order_by("-created_at"),
                lambda x: {
                    "id": str(x.id),
                    "name": x.property.title,
                    "detail": f"{x.start_date} – {x.end_date}",
                    "revision": x.revision,
                },
            )
        if kind == "evidence":
            lease = get_object_or_404(
                Lease.objects.filter(
                    Q(owner=request.user)
                    | Q(tenant=request.user)
                    | Q(property__owner=request.user)
                ),
                id=identity(request.query_params.get("lease_id")),
            )
            query = RentalEvidence.objects.filter(
                lease=lease, malware_status="safe", deleted_at__isnull=True
            )
            return self.page(
                request,
                query.order_by("-created_at"),
                lambda x: {
                    "id": str(x.id),
                    "name": x.original_name,
                    "detail": x.created_at.date().isoformat(),
                },
            )
        if kind in {"bookings", "employees"}:
            member = get_object_or_404(
                CompanyMembership,
                company__id=identity(company_id),
                user=request.user,
                is_active=True,
            )
            if not (member.is_admin or member.is_coordinator):
                raise NotFound()
            if kind == "employees":
                return self.page(
                    request,
                    member.company.memberships.filter(is_active=True, is_employee=True)
                    .select_related("user")
                    .order_by("id"),
                    lambda x: {
                        "id": str(x.user.id),
                        "name": x.user.get_full_name,
                        "detail": "",
                    },
                )
            query = CompanyBookingItem.objects.filter(request__company=member.company)
            if not member.is_admin:
                query = query.filter(request__coordinator=request.user)
            return self.page(
                request,
                query.order_by("-created_at"),
                lambda x: {
                    "id": str(x.id),
                    "name": x.snapshot.get("title") or x.offer.get_scope_display(),
                    "detail": x.status,
                },
            )
        raise NotFound()


class ReviewRecoveryView(ExperienceView):
    def post(self, request):
        return Response(recovery.recover(request.user, request.data), status=201)


class ReviewWindowExtensionView(ExperienceView):
    def post(self, request, identity):
        return Response(recovery.extend(request.user, identity, request.data))
