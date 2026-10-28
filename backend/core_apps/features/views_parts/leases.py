"""Views: leases."""

import copy
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.properties.models import Property
from ..models import Lease, TenancyInvitation
from ..renderers import FeatureJsonRenderer
from ..serializers import LeaseCreateSerializer, LeaseSerializer
from ..services.tenancy_invitations import (
    InvitationConflict,
    invitation_is_eligible,
    localized,
    refresh_effective_status,
    validate_accounts,
)
from .rental_operation_lookup import (
    User,
    LEASE_TEMPLATES,
    _replay,
    _remember,
    _paginate,
)
from .tenancy_invitation_respond import _lease_queryset


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def leases(request):
    if request.method == "GET":
        queryset = (
            _lease_queryset(request.user, request.query_params.get("workspace"))
            .exclude(private_access_revocations__user=request.user)
            .select_related("property", "owner", "tenant")
        )
        if request.query_params.get("property_id"):
            queryset = queryset.filter(property__id=request.query_params["property_id"])
        period = request.query_params.get("period", "all")
        if period not in {"all", "current", "upcoming", "ended", "pending_settlement"}:
            raise ValidationError(
                {"period": "Choose a supported rental period filter."}
            )
        today = timezone.localdate()
        if period == "current":
            queryset = queryset.filter(
                status__in=["active", "termination_pending"],
                start_date__lte=today,
                end_date__gt=today,
            )
        elif period == "upcoming":
            queryset = queryset.filter(start_date__gt=today).exclude(
                status__in=["ended", "cancelled"]
            )
        elif period in {"ended", "pending_settlement"}:
            queryset = queryset.filter(status__in=["ended", "cancelled"])
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(property__title__icontains=search)
        if period == "pending_settlement":
            from ..services.rental_phase6 import closure_blocking_reasons

            completed = [
                item.pk
                for item in queryset.filter(financial_closure_status="closed")
                if not closure_blocking_reasons(item)
            ]
            queryset = queryset.exclude(pk__in=completed)
        bucket = request.query_params.get("housing_bucket")
        if bucket:
            if bucket not in {"current", "history"}:
                raise ValidationError({"housing_bucket": "Choose current or history."})
            from ..services.rental_phase6 import closure_blocking_reasons

            # Historical membership cannot manufacture a personal contract party.
            queryset = queryset.filter(renter_company__isnull=True)
            completed_ids = [
                item.pk
                for item in queryset.filter(
                    status__in=["ended", "cancelled"], financial_closure_status="closed"
                )
                if not closure_blocking_reasons(item)
            ]
            queryset = (
                queryset.filter(pk__in=completed_ids)
                if bucket == "history"
                else queryset.exclude(pk__in=completed_ids)
            )
        response = _paginate(request, queryset, LeaseSerializer)
        if bucket:
            response.data["housing_bucket_version"] = 1
        response["Cache-Control"] = "private, no-store"
        return response
    if "invitation_id" in request.data and "terms" in request.data:
        from ..rental_phase2_views import create_structured_lease

        return create_structured_lease(request)
    serializer = LeaseCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data_in = serializer.validated_data
    property_obj = get_object_or_404(
        Property.objects.select_related("owner"),
        id=data_in["property_id"],
        owner=request.user,
    )
    tenant = get_object_or_404(User, id=data_in["tenant_id"])
    validate_accounts(request.user, tenant, request)
    replay = _replay(request.user, "lease.create", data_in["request_key"], request.data)
    if replay:
        return replay
    template = next(
        (
            item
            for item in LEASE_TEMPLATES
            if item["id"] == data_in["template_id"]
            and item["version"] == data_in["template_version"]
        ),
        None,
    )
    if not template:
        raise ValidationError({"template_id": "Unsupported template or version."})
    try:
        with transaction.atomic():
            property_obj = get_object_or_404(
                Property.objects.select_for_update().select_related("owner"),
                pk=property_obj.pk,
                owner=request.user,
            )
            tenant = get_object_or_404(User.objects.select_for_update(), pk=tenant.pk)
            validate_accounts(request.user, tenant, request)
            replay = _replay(
                request.user, "lease.create", data_in["request_key"], request.data
            )
            if replay:
                return replay
            offer_id = str(data_in.get("offer_id") or "")
            invitations = list(
                TenancyInvitation.objects.select_for_update()
                .filter(
                    property=property_obj,
                    owner=request.user,
                    tenant=tenant,
                    offer_id=offer_id,
                    status=TenancyInvitation.Status.ACCEPTED,
                    lease__isnull=True,
                )
                .select_related("property", "property__owner", "owner", "tenant")
                .order_by("-created_at", "-id")
            )
            for item in invitations:
                refresh_effective_status(item)
            invitation = next(
                (item for item in invitations if invitation_is_eligible(item)), None
            )
            if not invitation:
                raise InvitationConflict(
                    localized(
                        request,
                        "The selected tenant is no longer eligible for this accommodation.",
                        "لم يعد المستأجر المحدد مؤهلاً لمكان الإقامة هذا.",
                    )
                )
            from core_apps.properties.services.post_visit_decision import (
                validate_invitation_provenance,
            )

            validate_invitation_provenance(invitation)
            lease = Lease.objects.create(
                property=property_obj,
                owner=request.user,
                tenant=tenant,
                template_id=data_in["template_id"],
                template_version=data_in["template_version"],
                start_date=data_in["start_date"],
                end_date=data_in["end_date"],
                rent_amount_minor=data_in["rent"]["amount_minor"],
                rent_currency="EGP",
                rent_exponent=2,
                offer_id=offer_id,
                offer_snapshot=copy.deepcopy(invitation.offer_snapshot),
            )
            invitation.lease = lease
            invitation.save(update_fields=["lease", "updated_at"])
            out = LeaseSerializer(lease, context={"request": request}).data
            _remember(
                request.user,
                "lease.create",
                data_in["request_key"],
                request.data,
                out,
                201,
                request_subject_id=invitation.id,
                result_subject_id=lease.id,
                result_revision=lease.revision,
                is_rental_operation=True,
            )
    except IntegrityError:
        replay = _replay(
            request.user, "lease.create", data_in["request_key"], request.data
        )
        if replay:
            return replay
        raise InvitationConflict("The accommodation already has a conflicting lease.")
    return Response(out, status=status.HTTP_201_CREATED)


def _get_authorized_lease(request, lease_id):
    lease = get_object_or_404(
        Lease.objects.select_related("property", "owner", "tenant").exclude(
            private_access_revocations__user=request.user
        ),
        id=lease_id,
    )
    if request.user not in (lease.owner, lease.tenant):
        raise NotFound()
    if lease.renter_company_id:
        from ..services.company.tenancy_access import roles

        if "owner" not in roles(lease.company_tenancy, request.user):
            raise NotFound()
    return lease


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_detail(request, lease_id):
    if request.method == "PATCH":
        from ..rental_phase2_views import update_structured_lease

        return update_structured_lease(request, lease_id)
    lease = _get_authorized_lease(request, lease_id)
    return Response(LeaseSerializer(lease, context={"request": request}).data)
