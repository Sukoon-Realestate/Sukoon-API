import copy
import json
from datetime import timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.conf import settings
from django.db import models, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core_apps.properties.models import Property
from core_apps.notifications.models import Notification
from core_apps.notifications.services.notification_service import NotificationService

from .models import (
    IdempotencyRecord,
    Lease,
    OwnerOnboardingSession,
    OwnerPaymentProfile,
    RentalInterest,
    RentalInventoryDayLock,
    RentalTimelineEvent,
    SigningSession,
    TenancyInvitation,
    TermsProposal,
)
from .pagination import FeaturePagination
from .providers import fake_provider_available, get_rental_provider, verify_fake_webhook
from .renderers import FeatureJsonRenderer
from .rental_serializers import (
    LeasePhase2Serializer,
    OwnerOnboardingBodySerializer,
    OwnerPaymentProfileSerializer,
    RentalAgreementDraftBodySerializer,
    RentalDecisionSerializer,
    RentalInterestBodySerializer,
    RentalInterestSerializer,
    RentalInvitationBodySerializer,
    RentalSigningBodySerializer,
    TermsProposalBodySerializer,
    TermsProposalSerializer,
)
from .serializers import TenancyInvitationSerializer
from .services.rental_phase2 import (
    RentalConflict,
    activate_inventory,
    assert_owner_ready,
    fingerprint,
    get_or_create_owner_profile,
    remember_mutation,
    replay_operation,
    reserve_inventory_days,
    validate_interest_capacity,
)
from .services.tenancy_invitations import (
    create_notification_for_invitation,
    resolve_offer_snapshot,
)


def _paginate(request, queryset, serializer_class):
    paginator = FeaturePagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = serializer_class(page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)


def _replay_response(user, operation, request_key, payload):
    replay = replay_operation(user, operation, request_key, payload)
    if replay:
        data, response_status = replay
        return Response(data, status=response_status)
    return None


def _remember_session(
    *,
    user,
    operation,
    request_key,
    payload,
    request_subject_id,
    result_subject_id,
    result_revision,
    response_data,
    response_status=201,
):
    record = IdempotencyRecord.objects.create(
        user=user,
        operation=operation,
        request_key=str(request_key),
        fingerprint=fingerprint(payload),
        response_data={},
        response_status=response_status,
        is_rental_operation=True,
        request_subject_id=request_subject_id,
        result_subject_id=result_subject_id,
        result_revision=result_revision,
    )
    response_data["operation_receipt_id"] = str(record.id)
    record.response_data = response_data
    record.save(update_fields=["response_data", "updated_at"])
    return response_data


def _participant_interest(request, interest_id, lock=False):
    queryset = RentalInterest.objects.select_related("property__owner", "tenant")
    if lock:
        queryset = queryset.select_for_update()
    interest = get_object_or_404(queryset, id=interest_id)
    if request.user not in (interest.tenant, interest.property.owner):
        raise NotFound()
    return interest


def _participant_proposal(request, proposal_id, lock=False):
    queryset = TermsProposal.objects.select_related(
        "owner", "interest__tenant", "interest__property"
    )
    if lock:
        queryset = queryset.select_for_update()
    proposal = get_object_or_404(queryset, id=proposal_id)
    if request.user not in (proposal.owner, proposal.interest.tenant):
        raise NotFound()
    return proposal


def _participant_lease(request, lease_id, lock=False):
    queryset = Lease.objects.select_related("property", "owner", "tenant")
    if lock:
        queryset = queryset.select_for_update()
    lease = get_object_or_404(queryset, id=lease_id)
    if request.user not in (lease.owner, lease.tenant):
        raise NotFound()
    return lease


def _money_minor_from_offer(snapshot):
    try:
        return int(
            (Decimal(str(snapshot["terms"]["price"])) * 100).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )
    except (KeyError, TypeError, InvalidOperation):
        raise ValidationError({"offer_id": "The offer has no valid monthly price."})


def _json_safe(value):
    return json.loads(json.dumps(value, default=str))


def _validate_terms_offer(terms, snapshot):
    if snapshot.get("terms", {}).get("price_period") != "monthly":
        raise ValidationError({"offer_id": "V1 supports monthly offers only."})
    if terms["monthly_rent"]["amount_minor"] != _money_minor_from_offer(snapshot):
        raise RentalConflict(
            "The agreement rent does not match the selected offer.",
            code="document_changed",
        )


def _event(lease, actor, kind, label, resource_id=None, description=""):
    RentalTimelineEvent.objects.create(
        lease=lease,
        actor=actor,
        kind=kind,
        label=label,
        description=description,
        resource_id=resource_id or lease.id,
    )


def _notify(user, notification_type, title, action_type, target_id, **context):
    payload = {
        "action_type": action_type,
        "target_id": str(target_id),
        **{key: str(value) for key, value in context.items() if value is not None},
    }
    NotificationService.create_notification(
        user=user,
        notification_type=notification_type,
        title=title,
        data=payload,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def owner_payment_profile(request):
    profile = get_or_create_owner_profile(request.user)
    return Response(OwnerPaymentProfileSerializer(profile).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def owner_onboarding_session(request):
    serializer = OwnerOnboardingBodySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    profile = get_or_create_owner_profile(request.user)
    operation = "rental.owner_onboarding.create"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    if "rental-policy-v1" not in data["accepted_policy_versions"]:
        raise ValidationError(
            {"accepted_policy_versions": "rental-policy-v1 must be accepted."}
        )
    with transaction.atomic():
        profile = OwnerPaymentProfile.objects.select_for_update().get(pk=profile.pk)
        if data["expected_revision"] != profile.revision:
            raise RentalConflict(
                "Owner profile revision conflict.", code="stale_revision"
            )
        replay = _replay_response(
            request.user, operation, data["request_key"], request.data
        )
        if replay:
            return replay
        provider_session = get_rental_provider().create_onboarding_session(
            profile.id, data["request_key"]
        )
        expires_at = timezone.now() + timedelta(
            minutes=settings.RENTAL_ONBOARDING_TTL_MINUTES
        )
        session = OwnerOnboardingSession.objects.create(
            owner_profile=profile,
            request_key=data["request_key"],
            profile_revision=profile.revision,
            provider_session_id=provider_session.provider_session_id,
            hosted_url=provider_session.hosted_url,
            expires_at=expires_at,
        )
        profile.accepted_policy_versions = data["accepted_policy_versions"]
        profile.status = OwnerPaymentProfile.Status.PENDING
        profile.provider = get_rental_provider().name
        profile.revision += 1
        profile.save(
            update_fields=[
                "accepted_policy_versions",
                "status",
                "provider",
                "revision",
                "updated_at",
            ]
        )
        output = {
            "session_id": str(session.id),
            "subject_id": str(profile.id),
            "request_key": str(data["request_key"]),
            "revision": profile.revision,
            "hosted_url": session.hosted_url,
            "expires_at": expires_at.isoformat(),
        }
        output = _remember_session(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=profile.id,
            result_subject_id=profile.id,
            result_revision=profile.revision,
            response_data=output,
        )
    return Response(output, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rental_interests(request):
    if request.method == "GET":
        workspace = request.query_params.get("workspace")
        if workspace == "tenant":
            queryset = RentalInterest.objects.filter(tenant=request.user)
        elif workspace == "owner":
            queryset = RentalInterest.objects.filter(property__owner=request.user)
        else:
            raise ValidationError({"workspace": "Must be owner or tenant."})
        return _paginate(
            request,
            queryset.select_related("property__owner", "tenant"),
            RentalInterestSerializer,
        )

    serializer = RentalInterestBodySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    property_obj = get_object_or_404(
        Property.objects.select_related("owner"), id=data["property_id"]
    )
    if property_obj.owner_id == request.user.pk:
        raise ValidationError("An owner cannot submit interest in their own property.")
    if not request.user.is_active or not request.user.is_verified:
        raise PermissionDenied("A verified active tenant is required.")
    operation = "rental_interest.create"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        property_obj = Property.objects.select_for_update().get(pk=property_obj.pk)
        offer_id, snapshot = resolve_offer_snapshot(
            property_obj, data["offer_id"], data["offer_revision"], request
        )
        if snapshot.get("terms", {}).get("price_period") != "monthly":
            raise ValidationError({"offer_id": "V1 supports monthly offers only."})
        validate_interest_capacity(snapshot, data["occupants"])
        if data["desired_start"] < timezone.localdate():
            raise ValidationError({"desired_start": "Cannot be in the past."})
        interest = RentalInterest.objects.create(
            property=property_obj,
            tenant=request.user,
            offer_id=offer_id,
            offer_revision=data["offer_revision"],
            offer_snapshot=snapshot,
            desired_start=data["desired_start"],
            months=data["months"],
            occupants=data["occupants"],
            message=data.get("message", ""),
        )
        resource = RentalInterestSerializer(interest, context={"request": request}).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=property_obj.id,
            result_subject_id=interest.id,
            result_revision=interest.revision,
            resource=resource,
            response_status=201,
        )
        transaction.on_commit(
            lambda: _notify(
                property_obj.owner,
                Notification.NotificationType.RENTAL_INTEREST,
                "New rental interest",
                "open_rental_interest",
                interest.id,
                rental_interest_id=interest.id,
                workspace="owner",
            )
        )
    return Response(output, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rental_interest_detail(request, interest_id):
    interest = _participant_interest(request, interest_id)
    return Response(
        RentalInterestSerializer(interest, context={"request": request}).data
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rental_interest_respond(request, interest_id):
    _participant_interest(request, interest_id)
    serializer = RentalDecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    operation = f"rental_interest.respond.{interest_id}"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        interest = _participant_interest(request, interest_id, lock=True)
        if data["expected_revision"] != interest.revision:
            raise RentalConflict("Interest revision conflict.", code="stale_revision")
        decision = data["decision"]
        if decision == "reject" and request.user == interest.property.owner:
            interest.status = RentalInterest.Status.REJECTED
        elif decision == "withdraw" and request.user == interest.tenant:
            interest.status = RentalInterest.Status.WITHDRAWN
        else:
            raise PermissionDenied(
                "This decision is not allowed for the current actor."
            )
        interest.revision += 1
        interest.save(update_fields=["status", "revision", "updated_at"])
        resource = RentalInterestSerializer(interest, context={"request": request}).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=interest.id,
            result_subject_id=interest.id,
            result_revision=interest.revision,
            resource=resource,
        )
    return Response(output)


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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def terms_proposal_respond(request, proposal_id):
    proposal = _participant_proposal(request, proposal_id)
    serializer = RentalDecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    operation = f"terms_proposal.respond.{proposal_id}"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        proposal = _participant_proposal(request, proposal_id, lock=True)
        if data["expected_revision"] != proposal.revision:
            raise RentalConflict("Proposal revision conflict.", code="stale_revision")
        if proposal.status in {
            TermsProposal.Status.REJECTED,
            TermsProposal.Status.ACCEPTED,
        }:
            raise RentalConflict("This proposal is already closed.")
        decision = data["decision"]
        actor_id = str(request.user.id)
        if decision == "accept":
            proposal.accepted_by = list(
                dict.fromkeys([*proposal.accepted_by, actor_id])
            )
            required = {str(proposal.owner.id), str(proposal.interest.tenant.id)}
            proposal.status = (
                TermsProposal.Status.ACCEPTED
                if required.issubset(set(proposal.accepted_by))
                else TermsProposal.Status.PROPOSED
            )
        elif decision == "reject":
            proposal.status = TermsProposal.Status.REJECTED
        elif decision == "request_changes":
            proposal.status = TermsProposal.Status.CHANGES_REQUESTED
            proposal.accepted_by = []
        else:
            raise ValidationError({"decision": "Unsupported proposal decision."})
        proposal.revision += 1
        proposal.save(update_fields=["accepted_by", "status", "revision", "updated_at"])
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


def create_interest_invitation(request):
    serializer = RentalInvitationBodySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    interest = _participant_interest(request, data["interest_id"])
    if request.user != interest.property.owner:
        raise PermissionDenied("Only the property owner can create the invitation.")
    assert_owner_ready(request.user, interest.property)
    operation = "rental_invitation.create"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        interest = _participant_interest(request, data["interest_id"], lock=True)
        proposal = _participant_proposal(request, data["terms_proposal_id"], lock=True)
        if proposal.interest_id != interest.pk:
            raise ValidationError(
                {"terms_proposal_id": "Proposal does not belong to interest."}
            )
        if proposal.status != TermsProposal.Status.ACCEPTED:
            raise RentalConflict("Both parties must accept the current terms first.")
        if data["interest_revision"] != interest.revision:
            raise RentalConflict("Interest revision conflict.", code="stale_revision")
        if str(data["property_id"]) != str(interest.property.id) or str(
            data["tenant_id"]
        ) != str(interest.tenant.id):
            raise ValidationError("Invitation participants do not match the interest.")
        _, snapshot = resolve_offer_snapshot(
            interest.property, data["offer_id"], data["offer_revision"], request
        )
        if TenancyInvitation.objects.filter(
            owner=request.user,
            property=interest.property,
            tenant=interest.tenant,
            offer_id=interest.offer_id,
            status__in=[
                TenancyInvitation.Status.PENDING,
                TenancyInvitation.Status.ACCEPTED,
            ],
            lease__isnull=True,
        ).exists():
            raise RentalConflict("A live invitation already exists for this offer.")
        invitation = TenancyInvitation.objects.create(
            property=interest.property,
            owner=request.user,
            tenant=interest.tenant,
            offer_id=interest.offer_id,
            offer_snapshot=snapshot,
            expires_at=timezone.now() + timedelta(days=7),
            initiated_by=request.user,
            interest=interest,
            terms_proposal=proposal,
            eligibility_snapshot={
                "interest_revision": interest.revision,
                "proposal_revision": proposal.revision,
                "offer_revision": data["offer_revision"],
            },
        )
        interest.status = RentalInterest.Status.INVITED
        interest.revision += 1
        interest.save(update_fields=["status", "revision", "updated_at"])
        resource = TenancyInvitationSerializer(
            invitation, context={"request": request}
        ).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=interest.id,
            result_subject_id=invitation.id,
            result_revision=invitation.revision,
            resource=resource,
            response_status=201,
        )
        create_notification_for_invitation(request, invitation)
    return Response(output, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def tenancy_invitation_revoke(request, invitation_id):
    serializer = RentalDecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    operation = f"rental_invitation.revoke.{invitation_id}"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        invitation = get_object_or_404(
            TenancyInvitation.objects.select_for_update().select_related(
                "property", "owner", "tenant", "lease"
            ),
            id=invitation_id,
            owner=request.user,
        )
        if data["decision"] != "revoke_invitation":
            raise ValidationError({"decision": "Must be revoke_invitation."})
        if data["expected_revision"] != invitation.revision:
            raise RentalConflict("Invitation revision conflict.", code="stale_revision")
        if invitation.lease_id or invitation.consumed_at:
            raise RentalConflict(
                "A consumed invitation cannot be revoked.", code="invitation_consumed"
            )
        if invitation.status not in {
            TenancyInvitation.Status.PENDING,
            TenancyInvitation.Status.ACCEPTED,
        }:
            raise RentalConflict("This invitation can no longer be revoked.")
        invitation.status = TenancyInvitation.Status.REVOKED
        invitation.revoked_at = timezone.now()
        invitation.revision += 1
        invitation.save(
            update_fields=["status", "revoked_at", "revision", "updated_at"]
        )
        resource = TenancyInvitationSerializer(
            invitation, context={"request": request}
        ).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=invitation.id,
            result_subject_id=invitation.id,
            result_revision=invitation.revision,
            resource=resource,
        )
    return Response(output)


def create_structured_lease(request):
    serializer = RentalAgreementDraftBodySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    invitation = get_object_or_404(
        TenancyInvitation.objects.select_related("property", "owner", "tenant"),
        id=data["invitation_id"],
        owner=request.user,
    )
    operation = "rental_agreement.create"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        invitation = (
            TenancyInvitation.objects.select_for_update()
            .select_related("property", "owner", "tenant", "terms_proposal")
            .get(pk=invitation.pk)
        )
        assert_owner_ready(request.user, invitation.property)
        if invitation.status != TenancyInvitation.Status.ACCEPTED:
            raise RentalConflict(
                "The invitation is not accepted.", code="offer_unavailable"
            )
        if invitation.lease_id or invitation.consumed_at:
            raise RentalConflict(
                "The invitation was already consumed.", code="invitation_consumed"
            )
        if invitation.expires_at <= timezone.now():
            raise RentalConflict("The invitation expired.", code="invitation_expired")
        if data["invitation_revision"] != invitation.revision:
            raise RentalConflict("Invitation revision conflict.", code="stale_revision")
        if str(data["property_id"]) != str(invitation.property.id) or str(
            data["tenant_id"]
        ) != str(invitation.tenant.id):
            raise ValidationError("Agreement participants do not match the invitation.")
        _, snapshot = resolve_offer_snapshot(
            invitation.property, data["offer_id"], data["offer_revision"], request
        )
        _validate_terms_offer(data["terms"], snapshot)
        if (
            invitation.terms_proposal
            and _json_safe(data["terms"]) != invitation.terms_proposal.terms
        ):
            raise RentalConflict("The reviewed terms changed.", code="document_changed")
        lease = Lease.objects.create(
            property=invitation.property,
            owner=request.user,
            tenant=invitation.tenant,
            template_id=data["terms"]["template_id"],
            template_version=data["terms"]["template_version"],
            start_date=data["terms"]["starts_on"],
            end_date=data["terms"]["ends_on_exclusive"],
            rent_amount_minor=data["terms"]["monthly_rent"]["amount_minor"],
            rent_currency="EGP",
            rent_exponent=2,
            offer_id=data["offer_id"],
            offer_snapshot=snapshot,
            terms=_json_safe(data["terms"]),
            policy_version="rental-policy-v1",
            legacy_read_only=False,
            hold_expires_at=timezone.now()
            + timedelta(minutes=settings.RENTAL_HOLD_TTL_MINUTES),
        )
        reserve_inventory_days(
            lease,
            data["terms"]["starts_on"],
            data["terms"]["ends_on_exclusive"],
            lease.hold_expires_at,
        )
        invitation.lease = lease
        invitation.consumed_at = timezone.now()
        invitation.save(update_fields=["lease", "consumed_at", "updated_at"])
        _event(lease, request.user, "draft_created", "Agreement draft created")
        resource = LeasePhase2Serializer(lease, context={"request": request}).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=invitation.id,
            result_subject_id=lease.id,
            result_revision=lease.revision,
            resource=resource,
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)


def update_structured_lease(request, lease_id):
    serializer = RentalAgreementDraftBodySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    visible = _participant_lease(request, lease_id)
    if request.user != visible.owner:
        raise PermissionDenied("Only the owner can edit the draft.")
    operation = f"rental_agreement.update.{lease_id}"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        lease = _participant_lease(request, lease_id, lock=True)
        if lease.status != Lease.Status.DRAFT or lease.legacy_read_only:
            raise RentalConflict("Only a new workflow draft can be edited.")
        if data["expected_revision"] != lease.revision:
            raise RentalConflict("Lease revision conflict.", code="stale_revision")
        invitation = get_object_or_404(
            TenancyInvitation.objects.select_for_update(),
            id=data["invitation_id"],
            lease=lease,
        )
        if data["invitation_revision"] != invitation.revision:
            raise RentalConflict("Invitation revision conflict.", code="stale_revision")
        if str(data["property_id"]) != str(lease.property.id) or str(
            data["tenant_id"]
        ) != str(lease.tenant.id):
            raise ValidationError("Participants and property cannot be changed.")
        if data["offer_id"] != lease.offer_id:
            raise ValidationError({"offer_id": "The accommodation cannot be changed."})
        _, snapshot = resolve_offer_snapshot(
            lease.property, data["offer_id"], data["offer_revision"], request
        )
        _validate_terms_offer(data["terms"], snapshot)
        RentalInventoryDayLock.objects.filter(lease=lease).delete()
        lease.start_date = data["terms"]["starts_on"]
        lease.end_date = data["terms"]["ends_on_exclusive"]
        lease.rent_amount_minor = data["terms"]["monthly_rent"]["amount_minor"]
        lease.terms = _json_safe(data["terms"])
        lease.offer_snapshot = snapshot
        lease.reviewed_by = []
        lease.document_id = None
        lease.document_hash = ""
        lease.revision += 1
        lease.hold_expires_at = timezone.now() + timedelta(
            minutes=settings.RENTAL_HOLD_TTL_MINUTES
        )
        lease.save()
        reserve_inventory_days(
            lease, lease.start_date, lease.end_date, lease.hold_expires_at
        )
        _event(lease, request.user, "draft_updated", "Agreement draft updated")
        resource = LeasePhase2Serializer(lease, context={"request": request}).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=lease.id,
            result_subject_id=lease.id,
            result_revision=lease.revision,
            resource=resource,
        )
    return Response(output)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_review(request, lease_id):
    lease = _participant_lease(request, lease_id)
    serializer = RentalDecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    operation = f"rental_agreement.review.{lease_id}"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        lease = _participant_lease(request, lease_id, lock=True)
        if lease.legacy_read_only or lease.status != Lease.Status.DRAFT:
            raise RentalConflict("This agreement cannot be reviewed.")
        if data["expected_revision"] != lease.revision:
            raise RentalConflict("Lease revision conflict.", code="stale_revision")
        actor_id = str(request.user.id)
        if data["decision"] == "accept_review":
            lease.reviewed_by = list(dict.fromkeys([*lease.reviewed_by, actor_id]))
        elif data["decision"] == "request_changes":
            lease.reviewed_by = []
        else:
            raise ValidationError({"decision": "Unsupported review decision."})
        lease.revision += 1
        lease.save(update_fields=["reviewed_by", "revision", "updated_at"])
        _event(lease, request.user, "review", data["decision"])
        resource = LeasePhase2Serializer(lease, context={"request": request}).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=lease.id,
            result_subject_id=lease.id,
            result_revision=lease.revision,
            resource=resource,
        )
    return Response(output)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_submit_for_signature(request, lease_id):
    lease = _participant_lease(request, lease_id)
    if request.user != lease.owner:
        raise PermissionDenied("Only the owner can submit the agreement.")
    serializer = RentalDecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    operation = f"rental_agreement.submit_signature.{lease_id}"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        lease = _participant_lease(request, lease_id, lock=True)
        assert_owner_ready(request.user, lease.property)
        if data["decision"] != "submit_for_signature":
            raise ValidationError({"decision": "Must be submit_for_signature."})
        if data["expected_revision"] != lease.revision:
            raise RentalConflict("Lease revision conflict.", code="stale_revision")
        required = {str(lease.owner.id), str(lease.tenant.id)}
        if not required.issubset(set(lease.reviewed_by)):
            raise RentalConflict("Both participants must review the current agreement.")
        if not lease.hold_expires_at or lease.hold_expires_at <= timezone.now():
            raise RentalConflict("The inventory hold expired.", code="hold_expired")
        required_days = (lease.end_date - lease.start_date).days
        held_days = RentalInventoryDayLock.objects.filter(
            lease=lease,
            kind=RentalInventoryDayLock.Kind.HOLD,
            expires_at__gt=timezone.now(),
        ).count()
        if held_days != required_days:
            raise RentalConflict("The inventory hold expired.", code="hold_expired")
        document = get_rental_provider().generate_agreement(
            lease.id, lease.revision, lease.terms
        )
        lease.document_id = document.document_id
        lease.document_hash = document.digest
        lease.status = Lease.Status.PENDING_SIGNATURES
        lease.revision += 1
        lease.save(
            update_fields=[
                "document_id",
                "document_hash",
                "status",
                "revision",
                "updated_at",
            ]
        )
        _event(lease, request.user, "signature_requested", "Submitted for signature")
        resource = LeasePhase2Serializer(lease, context={"request": request}).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=lease.id,
            result_subject_id=lease.id,
            result_revision=lease.revision,
            resource=resource,
        )
    return Response(output)


def create_structured_signing_session(request, lease_id):
    lease = _participant_lease(request, lease_id)
    serializer = RentalSigningBodySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    operation = f"rental_agreement.signing_session.{lease_id}"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        lease = _participant_lease(request, lease_id, lock=True)
        if lease.status != Lease.Status.PENDING_SIGNATURES:
            raise RentalConflict("The agreement is not awaiting signatures.")
        if data["expected_revision"] != lease.revision:
            raise RentalConflict("Lease revision conflict.", code="stale_revision")
        if (
            data["document_id"] != lease.document_id
            or data["document_hash"] != lease.document_hash
        ):
            raise RentalConflict(
                "The agreement document changed.", code="document_changed"
            )
        provider = get_rental_provider().create_signing_session(
            lease.id, request.user.id, data["request_key"]
        )
        expires_at = timezone.now() + timedelta(
            minutes=settings.RENTAL_SIGNING_TTL_MINUTES
        )
        session = SigningSession.objects.create(
            lease=lease,
            signer=request.user,
            hosted_url=provider.hosted_url,
            expires_at=expires_at,
            request_key=data["request_key"],
            lease_revision=lease.revision,
            document_id=lease.document_id,
            document_hash=lease.document_hash,
            provider_session_id=provider.provider_session_id,
        )
        output = {
            "session_id": str(session.id),
            "subject_id": str(lease.id),
            "request_key": str(data["request_key"]),
            "revision": lease.revision,
            "document_id": str(lease.document_id),
            "document_hash": lease.document_hash,
            "hosted_url": session.hosted_url,
            "expires_at": expires_at.isoformat(),
        }
        output = _remember_session(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=lease.id,
            result_subject_id=lease.id,
            result_revision=lease.revision,
            response_data=output,
        )
    return Response(output, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_timeline(request, lease_id):
    lease = _participant_lease(request, lease_id)
    paginator = FeaturePagination()
    page = paginator.paginate_queryset(lease.timeline_events.all(), request)
    return paginator.get_paginated_response(
        [
            {
                "id": str(item.id),
                "label": item.label,
                "description": item.description,
                "occurred_at": item.occurred_at.isoformat(),
                "kind": item.kind,
                "resource_id": str(item.resource_id) if item.resource_id else None,
            }
            for item in page
        ]
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_billing_schedule(request, lease_id):
    lease = _participant_lease(request, lease_id)
    paginator = FeaturePagination()
    page = paginator.paginate_queryset(
        lease.billing_periods.select_related("invoice").all(), request
    )
    return paginator.get_paginated_response(
        [
            {
                "id": str(period.id),
                "sequence": period.sequence,
                "starts_on": str(period.start),
                "ends_on_exclusive": str(period.end_exclusive),
                "issue_at": period.issue_at.isoformat(),
                "due_at": period.due_at.isoformat(),
                "amount": {
                    "amount_minor": period.amount_minor,
                    "currency": period.currency,
                    "exponent": period.exponent,
                },
                "status": period.status,
                "invoice_id": (
                    str(period.invoice.id) if hasattr(period, "invoice") else None
                ),
            }
            for period in page
        ]
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@renderer_classes([FeatureJsonRenderer])
def fake_rental_provider_webhook(request):
    if not fake_provider_available():
        raise NotFound()
    if not verify_fake_webhook(request.data, request.headers.get("X-Rental-Signature")):
        raise PermissionDenied("Invalid provider signature.")
    event_type = request.data.get("type")
    provider_session_id = request.data.get("provider_session_id")
    with transaction.atomic():
        if event_type == "onboarding.completed":
            session = get_object_or_404(
                OwnerOnboardingSession.objects.select_for_update().select_related(
                    "owner_profile"
                ),
                provider_session_id=provider_session_id,
            )
            if session.status != "completed":
                session.status = "completed"
                session.completed_at = timezone.now()
                session.save(update_fields=["status", "completed_at", "updated_at"])
                profile = OwnerPaymentProfile.objects.select_for_update().get(
                    pk=session.owner_profile_id
                )
                profile.status = OwnerPaymentProfile.Status.READY
                profile.payout_ready = True
                profile.masked_beneficiary = {"account_last4": "4242"}
                profile.requirements = []
                profile.revision += 1
                profile.save()
        elif event_type == "signature.completed":
            session = get_object_or_404(
                SigningSession.objects.select_for_update().select_related(
                    "lease__owner", "lease__tenant"
                ),
                provider_session_id=provider_session_id,
            )
            if session.status != "completed":
                lease = Lease.objects.select_for_update().get(pk=session.lease_id)
                if (
                    session.document_id != lease.document_id
                    or session.document_hash != lease.document_hash
                    or session.lease_revision != lease.revision
                ):
                    raise RentalConflict(
                        "The signed document is stale.", code="document_changed"
                    )
                session.status = "completed"
                session.completed_at = timezone.now()
                session.save(update_fields=["status", "completed_at", "updated_at"])
                signer_ids = set(
                    SigningSession.objects.filter(
                        lease=lease,
                        status="completed",
                        document_id=lease.document_id,
                        document_hash=lease.document_hash,
                    ).values_list("signer_id", flat=True)
                )
                if {lease.owner_id, lease.tenant_id}.issubset(signer_ids):
                    activate_inventory(lease)
                    lease.status = Lease.Status.ACTIVE
                    lease.activated_at = timezone.now()
                    lease.revision += 1
                    lease.save(
                        update_fields=[
                            "status",
                            "activated_at",
                            "revision",
                            "updated_at",
                        ]
                    )
                    from .services.rental_phase3 import generate_billing_schedule

                    generate_billing_schedule(lease)
                    _event(lease, None, "activated", "Agreement activated")
                    for participant, workspace in (
                        (lease.owner, "owner"),
                        (lease.tenant, "tenant"),
                    ):
                        transaction.on_commit(
                            lambda participant=participant, workspace=workspace: _notify(
                                participant,
                                Notification.NotificationType.RENTAL_AGREEMENT,
                                "Rental agreement activated",
                                "open_rental_center",
                                lease.id,
                                lease_id=lease.id,
                                workspace=workspace,
                            )
                        )
        elif event_type == "change-signature.completed":
            from .rental_phase5_views import complete_change_signature

            complete_change_signature(provider_session_id)
        else:
            raise ValidationError({"type": "Unsupported fake-provider event."})
    return Response({"status": "accepted"})
