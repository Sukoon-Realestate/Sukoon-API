"""Bilateral versioned negotiation over the existing private rental interest."""

from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.properties.models import Property
from ..models import TermsProposal
from ..renderers import FeatureJsonRenderer
from ..rental_serializers import TermsProposalBodySerializer, TermsProposalSerializer
from ..services.rental_phase2 import RentalConflict
from ..services.rental_lifecycle.common import command, require_revision
from ..services import negotiation_terms as negotiation
from ..services.tenancy_invitations import resolve_offer_snapshot
from .owner_payment_profile import _paginate, _participant_interest, _participant_proposal


class ProposalFilters(serializers.Serializer):
    property_id = serializers.UUIDField(required=False)
    offer_id = serializers.CharField(max_length=64, required=False)
    academic_plan_id = serializers.UUIDField(required=False)
    active_agreements = serializers.BooleanField(default=False)


def interest_parties(request, interest_id):
    return negotiation.participant_ids(_participant_interest(request, interest_id, provider_required=False))


def proposal_parties(request, proposal_id):
    return negotiation.participant_ids(_participant_proposal(request, proposal_id, provider_required=False).interest)


def selection(request, interest, data):
    from core_apps.users.services.new_business import require_new_business
    from core_apps.chat.moderation.policy import require_business_participants

    require_new_business(*negotiation.participant_ids(interest))
    require_business_participants(interest.property.owner, interest.tenant)
    prop = interest.property
    if not prop.is_verified or not prop.is_ownership_verified or prop.status != "verified":
        raise RentalConflict("The owner must complete the listing review.", code="property_unavailable")
    if data["offer_id"] != interest.offer_id:
        raise RentalConflict("Keep the exact accommodation selected in this application.", code="offer_mismatch")
    return negotiation.with_context(
        resolve_offer_snapshot(prop, data["offer_id"], data["offer_revision"], request)[1], prop,
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def terms_proposals(request):
    if request.method == "GET":
        workspace = request.query_params.get("workspace")
        if workspace == "owner":
            queryset = TermsProposal.objects.filter(owner=request.user)
        elif workspace in {"tenant", "individual", "student"}:
            queryset = TermsProposal.objects.filter(interest__tenant=request.user)
            if workspace == "student":
                queryset = queryset.filter(Q(interest__academic_plan__isnull=False)
                    | Q(invitations__group_booking_participant__isnull=False)).distinct()
            elif workspace == "individual":
                queryset = queryset.filter(interest__academic_plan__isnull=True).exclude(
                    invitations__group_booking_participant__isnull=False,
                )
        else:
            raise ValidationError({"workspace": "Choose the current rental workspace."})
        filters = ProposalFilters(data=request.query_params)
        filters.is_valid(raise_exception=True)
        values = filters.validated_data
        for key, lookup in (("property_id", "interest__property__id"), ("offer_id", "interest__offer_id"),
                            ("academic_plan_id", "interest__academic_plan__id")):
            if key in values:
                queryset = queryset.filter(**{lookup: values[key]})
        if values["active_agreements"]:
            queryset = queryset.filter(author__isnull=False, status="accepted", expires_at__gt=timezone.now())
        response = _paginate(request, queryset.select_related(
            "owner", "author", "interest__tenant", "interest__property",
        ), TermsProposalSerializer)
        response["Cache-Control"] = "private, no-store"
        return response
    serializer = TermsProposalBodySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    def authorize():
        root = _participant_interest(request, data["interest_id"], provider_required=False)
        Property.objects.select_for_update().get(pk=root.property_id)
        return _participant_interest(request, root.id, lock=True, provider_required=False)

    def execute(interest):
        require_revision(interest, data["interest_revision"])
        if data["expected_revision"] != 0 or interest.status in {"withdrawn", "rejected", "invited"}:
            raise RentalConflict("Review the current application.", code="invalid_state")
        if negotiation.active_negotiation(interest):
            raise RentalConflict("Continue the existing negotiation.", code="proposal_exists")
        snapshot = selection(request, interest, data)
        terms = negotiation.validate(interest, data["terms"], snapshot, data["expires_at"])
        from ..services.rental_application_records import create_terms
        proposal = create_terms(interest=interest, owner=interest.property.owner, author=request.user,
                                terms=terms, snapshot=snapshot, expires_at=data["expires_at"])
        negotiation.notify(proposal, request.user, "terms.proposed")
        return proposal, TermsProposalSerializer(proposal, context={"request": request}).data, 201

    output, status = command(user=request.user, operation="terms_proposal.create", data=request.data,
                             authorize=authorize, execute=execute,
                             account_parties=lambda: interest_parties(request, data["interest_id"]))
    return Response(output, status=status)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def terms_proposal_detail(request, proposal_id):
    if request.method == "GET":
        return Response(TermsProposalSerializer(
            _participant_proposal(request, proposal_id), context={"request": request},
        ).data, headers={"Cache-Control": "private, no-store"})
    serializer = TermsProposalBodySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    def authorize():
        return _participant_proposal(request, proposal_id, lock=True, provider_required=False)

    def execute(proposal):
        require_revision(proposal.interest, data["interest_revision"])
        if str(data["interest_id"]) != str(proposal.interest.id):
            raise ValidationError({"interest_id": "Cannot replace the source application."})
        snapshot = selection(request, proposal.interest, data)
        proposal = negotiation.revise(proposal, request.user, data, snapshot)
        return proposal, TermsProposalSerializer(proposal, context={"request": request}).data, 200

    output, status = command(user=request.user, operation=f"terms_proposal.update.{proposal_id}",
                             data=request.data, authorize=authorize, execute=execute,
                             account_parties=lambda: proposal_parties(request, proposal_id))
    return Response(output, status=status)
