"""Views: lease cancel."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import Lease, RentInvoice
from ..renderers import FeatureJsonRenderer
from ..serializers import (
    LeaseSerializer,
    RentInvoiceSerializer,
    RevisionRequestSerializer,
)
from ..services.tenancy_invitations import InvitationConflict, localized
from ..services.lease_permissions import can_cancel_draft
from .rental_operation_lookup import _replay, _remember, _paginate
from .leases import _get_authorized_lease


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_signing_session(request, lease_id):
    lease = _get_authorized_lease(request, lease_id)
    if not lease.legacy_read_only and "document_id" in request.data:
        from ..rental_phase2_views import create_structured_signing_session

        return create_structured_signing_session(request, lease_id)
    # The old hosted URL was a placeholder, not a provider signing session.
    # Structured signing uses document_id and its existing readiness checks.
    raise InvitationConflict(
        localized(
            request,
            "Signing is not available for template invitation drafts.",
            "التوقيع غير متاح لمسودات دعوات الإيجار بالقالب.",
        )
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_cancel(request, lease_id):
    structured = "expected_revision" in request.data
    if structured:
        from ..rental_serializers import RentalDecisionSerializer

        serializer = RentalDecisionSerializer(data=request.data)
    else:
        serializer = RevisionRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if structured and serializer.validated_data["decision"] != "cancel_draft":
        raise ValidationError({"decision": "Must be cancel_draft."})
    with transaction.atomic():
        from core_apps.properties.models import Property

        root = get_object_or_404(Lease, id=lease_id, owner=request.user)
        Property.objects.select_for_update().get(pk=root.property_id)
        lease = get_object_or_404(
            Lease.objects.select_for_update(), id=lease_id, owner=request.user
        )
        replay = _replay(
            request.user,
            "lease.cancel",
            serializer.validated_data["request_key"],
            request.data,
        )
        if replay:
            return replay
        if (
            serializer.validated_data["expected_revision" if structured else "revision"]
            != lease.revision
        ):
            raise InvitationConflict("Lease revision conflict.")
        if not can_cancel_draft(request.user, lease):
            raise InvitationConflict(
                localized(
                    request,
                    "This agreement cannot be cancelled by this account.",
                    "لا يمكن لهذا الحساب إلغاء هذا العقد.",
                )
            )
        from ..services.rental_lifecycle.inventory import unresolved_payment

        if unresolved_payment(lease):
            raise InvitationConflict(
                "Reconcile the original payment before releasing accommodation."
            )
        lease.status = Lease.Status.CANCELLED
        lease.revision += 1
        lease.save(update_fields=["status", "revision", "updated_at"])
        from ..services.rental_phase6 import evaluate_financial_closure

        # Cancellation and its derived financial state are one lease mutation.
        evaluate_financial_closure(lease, increment_revision=False)
        lease.inventory_day_locks.filter(kind="hold").delete()
        from ..models import ReservationHold
        from django.db.models import F

        ReservationHold.objects.filter(
            lease=lease, status__in=["active", "reconciliation_pending"]
        ).update(
            status="cancelled", released_at=timezone.now(), revision=F("revision") + 1
        )
        data = {
            "id": str(lease.id),
            "subject_id": str(lease.id),
            "status": "cancelled",
            "lease_status": lease.status,
            "occupancy_status": lease.occupancy_status,
            "financial_closure_status": lease.financial_closure_status,
            "revision": lease.revision,
        }
        if structured:
            from ..services.rental_phase2 import remember_mutation

            return Response(
                remember_mutation(
                    user=request.user,
                    operation="lease.cancel",
                    request_key=serializer.validated_data["request_key"],
                    payload=request.data,
                    request_subject_id=lease.id,
                    result_subject_id=lease.id,
                    result_revision=lease.revision,
                    resource=LeaseSerializer(lease, context={"request": request}).data,
                )
            )
        _remember(
            request.user,
            "lease.cancel",
            serializer.validated_data["request_key"],
            request.data,
            data,
            200,
            request_subject_id=lease.id,
            result_subject_id=lease.id,
            result_revision=lease.revision,
            is_rental_operation=True,
        )
    return Response(data)


def _invoice_queryset(user, workspace):
    if workspace == "owner":
        return RentInvoice.objects.filter(lease__owner=user)
    if workspace == "tenant":
        return RentInvoice.objects.filter(lease__tenant=user)
    raise ValidationError({"workspace": "Must be owner or tenant."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rent_invoices(request):
    # The billing worker owns overdue transitions, including approved extensions
    # and revision changes. Listing invoices must remain a read-only projection.
    queryset = _invoice_queryset(
        request.user, request.query_params.get("workspace")
    ).select_related("lease", "lease__property")
    if request.query_params.get("lease_id"):
        queryset = queryset.filter(lease__id=request.query_params["lease_id"])
    if request.query_params.get("status"):
        statuses = request.query_params["status"].split(",")
        invalid = set(statuses) - set(RentInvoice.Status.values)
        if invalid:
            raise ValidationError(
                {"status": f"Unsupported statuses: {', '.join(sorted(invalid))}"}
            )
        queryset = queryset.filter(status__in=statuses)
    ordering = request.query_params.get("ordering", "-created_at")
    if ordering not in {"due_date", "-due_date", "created_at", "-created_at"}:
        raise ValidationError({"ordering": "Unsupported ordering."})
    return _paginate(request, queryset.order_by(ordering, "id"), RentInvoiceSerializer)


def _get_authorized_invoice(request, invoice_id):
    invoice = get_object_or_404(
        RentInvoice.objects.select_related("lease", "lease__property"),
        id=invoice_id,
        purpose="rent",
    )
    if request.user not in (invoice.lease.owner, invoice.lease.tenant):
        raise NotFound()
    return invoice


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rent_invoice_detail(request, invoice_id):
    return Response(
        RentInvoiceSerializer(
            _get_authorized_invoice(request, invoice_id), context={"request": request}
        ).data
    )
