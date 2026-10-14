"""Rental phase2 views: terms proposals."""

import copy
from django.db import models, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.notifications.models import Notification
from ..models import RentalInterest, TenancyInvitation, TermsProposal
from ..renderers import FeatureJsonRenderer
from ..rental_serializers import TermsProposalBodySerializer, TermsProposalSerializer
from ..services.rental_phase2 import (
    RentalConflict,
    assert_owner_ready,
    remember_mutation,
)
from ..services.tenancy_invitations import resolve_offer_snapshot
from .owner_payment_profile import (
    _paginate,
    _replay_response,
    _participant_interest,
    _participant_proposal,
    _json_safe,
    _validate_terms_offer,
    _notify,
)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def terms_proposals(request):
    if request.method == "GET":
        workspace = request.query_params.get("workspace")
        if workspace == "owner":
            queryset = TermsProposal.objects.filter(owner=request.user)
        elif workspace == "tenant":
            queryset = TermsProposal.objects.filter(interest__tenant=request.user)
        else:
            raise ValidationError({"workspace": "Must be owner or tenant."})
        return _paginate(
            request,
            queryset.select_related("owner", "interest__tenant", "interest__property"),
            TermsProposalSerializer,
        )

    serializer = TermsProposalBodySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    interest = _participant_interest(request, data["interest_id"])
    if request.user != interest.property.owner:
        raise PermissionDenied("Only the property owner can propose terms.")
    assert_owner_ready(request.user, interest.property)
    operation = "terms_proposal.create"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        interest = _participant_interest(request, data["interest_id"], lock=True)
        if data["interest_revision"] != interest.revision:
            raise RentalConflict("Interest revision conflict.", code="stale_revision")
        _, snapshot = resolve_offer_snapshot(
            interest.property, data["offer_id"], data["offer_revision"], request
        )
        _validate_terms_offer(data["terms"], snapshot)
        if data["terms"]["occupants"] != interest.occupants:
            raise ValidationError({"terms": "Occupants must match the interest."})
        proposal = TermsProposal.objects.create(
            interest=interest,
            owner=request.user,
            terms=_json_safe(data["terms"]),
            offer_snapshot=snapshot,
            accepted_by=[str(request.user.id)],
        )
        interest.status = RentalInterest.Status.PROPOSED
        interest.revision += 1
        interest.save(update_fields=["status", "revision", "updated_at"])
        resource = TermsProposalSerializer(proposal, context={"request": request}).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=interest.id,
            result_subject_id=proposal.id,
            result_revision=proposal.revision,
            resource=resource,
            response_status=201,
        )
        transaction.on_commit(
            lambda: _notify(
                interest.tenant,
                Notification.NotificationType.RENTAL_TERMS,
                "Rental terms proposed",
                "open_rental_terms",
                proposal.id,
                terms_proposal_id=proposal.id,
                workspace="tenant",
            )
        )
    return Response(output, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def terms_proposal_detail(request, proposal_id):
    proposal = _participant_proposal(request, proposal_id)
    if request.method == "GET":
        return Response(
            TermsProposalSerializer(proposal, context={"request": request}).data
        )
    if request.user != proposal.owner:
        raise PermissionDenied("Only the owner can edit proposed terms.")
    serializer = TermsProposalBodySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    operation = f"terms_proposal.update.{proposal_id}"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        proposal = _participant_proposal(request, proposal_id, lock=True)
        if data["expected_revision"] != proposal.revision:
            raise RentalConflict("Proposal revision conflict.", code="stale_revision")
        if data["interest_revision"] != proposal.interest.revision:
            raise RentalConflict("Interest revision conflict.", code="stale_revision")
        if str(data["interest_id"]) != str(proposal.interest.id):
            raise ValidationError({"interest_id": "Cannot change the source interest."})
        _, snapshot = resolve_offer_snapshot(
            proposal.interest.property,
            data["offer_id"],
            data["offer_revision"],
            request,
        )
        _validate_terms_offer(data["terms"], snapshot)
        proposal.previous_terms = [
            *proposal.previous_terms,
            copy.deepcopy(proposal.terms),
        ]
        proposal.terms = _json_safe(data["terms"])
        proposal.offer_snapshot = snapshot
        proposal.accepted_by = [str(request.user.id)]
        proposal.status = TermsProposal.Status.PROPOSED
        proposal.revision += 1
        proposal.save()
        TenancyInvitation.objects.filter(
            terms_proposal=proposal,
            lease__isnull=True,
            status__in=[
                TenancyInvitation.Status.PENDING,
                TenancyInvitation.Status.ACCEPTED,
            ],
        ).update(
            status=TenancyInvitation.Status.REVOKED,
            revoked_at=timezone.now(),
            revision=models.F("revision") + 1,
            updated_at=timezone.now(),
        )
        resource = TermsProposalSerializer(proposal, context={"request": request}).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=proposal.id,
            result_subject_id=proposal.id,
            result_revision=proposal.revision,
            resource=resource,
        )
    return Response(output)
