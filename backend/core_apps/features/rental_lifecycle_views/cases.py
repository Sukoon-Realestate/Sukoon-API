from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from core_apps.properties.models import Property
from ..models import Lease, RentalEvidence
from ..rental_lifecycle_serializers import CaseBody, CaseActionBody
from ..services.rental_lifecycle.cases import (
    case_queryset,
    case_payload,
    open_system_case,
)
from ..services.rental_lifecycle.common import require_revision
from ..services.rental_phase2 import RentalConflict
from .common import endpoint, page, validated, mutate


@endpoint(["GET", "POST"])
def rental_cases(request, operations=False):
    if operations:
        from ..services.rental_lifecycle.common import require_staff
        from ..services.rental_lifecycle.cases import ROLES

        require_staff(request.user, ROLES)
    if request.method == "GET":
        return page(
            request,
            case_queryset(request.user).order_by("due_at", "id"),
            lambda item: case_payload(item, request.user),
        )
    data = validated(CaseBody, request.data)

    def authorize():
        lease = get_object_or_404(Lease, id=data["lease_id"])
        if request.user.pk not in {lease.owner_id, lease.tenant_id}:
            raise NotFound()
        Property.objects.select_for_update().get(pk=lease.property_id)
        return Lease.objects.select_for_update().get(pk=lease.pk)

    def execute(lease):
        require_revision(lease, data["expected_revision"])
        if lease.legacy_read_only:
            raise RentalConflict("Historical agreements require operational review.")
        evidence = list(
            RentalEvidence.objects.filter(
                id__in=data["evidence_ids"],
                lease=lease,
                uploader=request.user,
                malware_status="safe",
                deleted_at__isnull=True,
            )
        )
        if len(evidence) != len(set(data["evidence_ids"])):
            raise ValidationError(
                {"evidence_ids": "Use your clean evidence from this agreement."}
            )
        item = open_system_case(
            kind=data["kind"],
            source_key=f"participant-case:{request.user.id}:{data['request_key']}",
            lease=lease,
            actor=request.user,
            evidence=evidence,
            reason=data["reason"],
            next_action="Review the agreed selection and both participant accounts.",
        )
        if data["kind"] == "habitability":
            from ..services.rental_lifecycle.habitability import report

            report(item, data)
        return item, case_payload(item, request.user), 201

    return mutate(request, "rental_case.create", authorize, execute)


@endpoint(["GET", "POST"])
def rental_case(request, case_id, operations=False):
    if operations:
        from ..services.rental_lifecycle.common import require_staff
        from ..services.rental_lifecycle.cases import ROLES

        require_staff(request.user, ROLES)
    item = get_object_or_404(case_queryset(request.user), id=case_id)
    if request.method == "GET":
        return Response(case_payload(item, request.user))
    data = validated(CaseActionBody, request.data)

    from ..services.rental_lifecycle.case_commands import act_on_case

    output, status = act_on_case(request.user, case_id, data, command_data=request.data)
    return Response(output, status=status)
