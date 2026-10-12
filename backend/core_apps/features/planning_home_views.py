"""Bounded private Home summaries. Every destination still loads fresh permissions."""

from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Lease, RentalChange
from .planning_models import HousingGroup, HousingRequest, TenancyTransition
from .services.planning import planning_api, enabled_services


@planning_api(["GET"], None)
def planning_home(request):
    workspace = request.query_params.get("workspace", "tenant")
    if workspace not in {"tenant", "owner"}:
        raise ValidationError({"workspace": "Use tenant or owner."})
    entries = []
    enabled = enabled_services()
    if workspace == "tenant":
        if "housing_groups" in enabled:
            group = (
                HousingGroup.objects.filter(
                    status="active",
                    memberships__user=request.user,
                    memberships__status="active",
                )
                .order_by("-updated_at")
                .first()
            )
            if group:
                entries.append(
                    {"kind": "group", "id": str(group.id), "title": group.name}
                )
        if "housing_requests" in enabled:
            demand = (
                HousingRequest.objects.filter(
                    user=request.user, status="published", expires_at__gt=timezone.now()
                )
                .order_by("-updated_at")
                .first()
            )
            if demand:
                entries.append(
                    {"kind": "request", "id": str(demand.id), "title": demand.title}
                )
        if "replacements" in enabled:
            invitation = (
                TenancyTransition.objects.filter(
                    candidate__tenant=request.user,
                    status="candidate_pending",
                    kind="replacement",
                )
                .order_by("-updated_at")
                .first()
            )
            if invitation:
                entries.append(
                    {
                        "kind": "replacement_invitation",
                        "id": str(invitation.id),
                        "title": "",
                    }
                )
    today = timezone.localdate()
    party = Q(owner=request.user) if workspace == "owner" else Q(tenant=request.user)
    lease = (
        Lease.objects.filter(
            party,
            legacy_read_only=False,
            status="active",
            end_date__gt=today,
            end_date__lte=today
            + timedelta(days=max(0, settings.PLANNING_LEASE_REMINDER_DAYS)),
        )
        .exclude(occupancy_status="returned")
        .exclude(private_access_revocations__user=request.user)
        .exclude(
            pk__in=RentalChange.objects.filter(kind="renewal", status="applied").values(
                "lease_id"
            )
        )
        .select_related("property")
        .order_by("end_date")
        .first()
    )
    if lease:
        entries.append(
            {
                "kind": "lease_end",
                "id": str(lease.id),
                "title": lease.property.title,
                "date": str(lease.end_date),
            }
        )
    return Response({"entries": entries})
