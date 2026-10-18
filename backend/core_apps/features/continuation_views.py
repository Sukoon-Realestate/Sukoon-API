"""Read-only continuation from canonical records; no replay queue or new intent."""

from django.db.models import CharField, F, Q, Value
from django.db.models.functions import Cast
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from core_apps.support.models import Ticket
from .models import Lease, PaymentAttempt, RentalOperationalCase
from core_apps.properties.models import Property
from .planning_models import HousingRequest
from .company_models import CompanyBookingItem
from .services.student_housing.access import plans_for
from .pagination import FeaturePagination
from .renderers import FeatureJsonRenderer
from .services.rental_foundation import private_no_store


def projection(queryset, kind, status, subject="id"):
    return (
        queryset.order_by()
        .annotate(
            resource_id=Cast("id", CharField()),
            resource_kind=Value(kind, output_field=CharField()),
            subject_id=Cast(subject, CharField()),
            resource_status=F(status),
            changed_at=F("updated_at"),
        )
        .values(
            "resource_id",
            "resource_kind",
            "subject_id",
            "resource_status",
            "changed_at",
        )
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def continuation_items(request):
    if not request.user.is_active:
        raise PermissionDenied()
    workspace = request.query_params.get("workspace", "tenant")
    if workspace not in {"tenant", "owner"}:
        raise ValidationError({"workspace": "Use tenant or owner."})
    user = request.user
    role = {workspace: user}
    attempts = PaymentAttempt.objects.filter(
        payer=user, payment_status__in=["created", "pending", "authorized"]
    )
    rent = attempts.filter(invoice__purpose="rent", invoice__lease__tenant=user)
    if workspace == "owner":
        rent = rent.none()
    purchase = attempts.filter(
        invoice__purpose__in=["subscription", "advertising"],
        invoice__payer=user,
        invoice__workspace=workspace,
    )
    leases = Lease.objects.filter(**role).filter(
        status__in=["draft", "pending_signatures", "signed"]
    )
    # Staff membership alone never turns an operations queue into a personal inbox.
    case_role = Q(**{f"lease__{workspace}": user}) | Q(
        opened_by=user, lease__isnull=True
    )
    cases = RentalOperationalCase.objects.filter(case_role).exclude(
        status__in=["resolved", "closed"]
    )
    tickets = Ticket.objects.filter(
        user=user, workspace=workspace, status__in=["open", "in_progress"]
    )
    plans = plans_for(user).filter(status="planning")
    requests = HousingRequest.objects.filter(
        user=user, status__in=["draft", "published"]
    ).filter(Q(academic_plan__isnull=True) | Q(academic_plan__in=plans_for(user)))
    properties = Property.objects.filter(
        owner=user, status__in=["under_review", "needs_revision"]
    )
    # Keep current organization membership and task assignment together, as in
    # company.access.company_subject. Employees do not inherit an admin inbox.
    relation = "request__company__memberships__"
    items = (
        CompanyBookingItem.objects.filter(
            Q(**{relation + "is_admin": True})
            | (
                (
                    Q(**{relation + "is_coordinator": True})
                    | Q(**{relation + "is_approver": True})
                )
                & (Q(request__coordinator=user) | Q(assigned_approver__user=user))
            ),
            **{relation + "user": user, relation + "is_active": True},
        )
        .exclude(status__in=["withdrawn", "rejected"])
        .distinct()
    )
    if workspace == "owner":
        plans, requests, items = plans.none(), requests.none(), items.none()
    else:
        properties = properties.none()
    rows = (
        projection(rent, "rent_payment", "payment_status", "invoice__id")
        .union(
            projection(purchase, "purchase_payment", "payment_status", "invoice__id"),
            projection(leases, "agreement", "status"),
            projection(cases, "rental_case", "status"),
            projection(tickets, "support", "status"),
            projection(plans, "student_plan", "status"),
            projection(requests, "housing_request", "status"),
            projection(properties, "property", "status"),
            projection(items, "company_work", "status", "request__company__id"),
            all=True,
        )
        .order_by("-changed_at", "resource_kind", "resource_id")
    )
    paginator = FeaturePagination()
    page = paginator.paginate_queryset(rows, request)
    return private_no_store(paginator.get_paginated_response(list(page)))
