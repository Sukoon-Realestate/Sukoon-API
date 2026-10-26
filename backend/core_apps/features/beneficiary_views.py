"""Confirm only the exact already verified recipient presented to its owner."""

from django.db import transaction
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.users.models import User
from core_apps.users.services import sensitive_actions, totp
from .models import OwnerPaymentProfile, RentalAuditEvent
from .providers import require_verified_rental_account
from .renderers import FeatureJsonRenderer
from .rental_serializers import (
    OwnerOnboardingBodySerializer,
    OwnerPaymentProfileSerializer,
)
from .services import (
    beneficiary_confirmation as service,
    beneficiary_details,
    paymob_payout_client as client,
)


class BeneficiaryDetailsBody(serializers.Serializer):
    expected_revision = serializers.IntegerField(min_value=1)
    details_revision = serializers.IntegerField(min_value=0)
    request_key = serializers.UUIDField()
    channel = serializers.ChoiceField(choices=sorted(client.WALLETS | client.BANKS))
    beneficiary_name = serializers.CharField(max_length=200)
    bank_name = serializers.CharField(
        max_length=200, required=False, allow_blank=True, default=""
    )
    account_number = serializers.CharField(max_length=34)
    accepted_policy_versions = serializers.ListField(
        child=serializers.CharField(max_length=40), allow_empty=False
    )

    def validate(self, data):
        import re

        account = data["account_number"].replace(" ", "").upper()
        if data["channel"] == "bank_card":
            if not data["bank_name"] or not re.fullmatch(r"[A-Z0-9]{6,34}", account):
                raise serializers.ValidationError(
                    {
                        "account_number": "Enter the bank name and a valid account number or IBAN."
                    }
                )
        elif not re.fullmatch(r"01[0125][0-9]{8}", account):
            raise serializers.ValidationError(
                {
                    "account_number": "Enter the Egyptian mobile-wallet number (11 digits)."
                }
            )
        elif data["bank_name"]:
            raise serializers.ValidationError(
                {"bank_name": "A bank name is only used for a bank account."}
            )
        data["account_number"] = account
        return data


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def submit_details(request):
    body = BeneficiaryDetailsBody(data=request.data)
    body.is_valid(raise_exception=True)
    value, code = beneficiary_details.submit(request, body.validated_data)
    return Response(value, status=code, headers={"Cache-Control": "private, no-store"})


from .services.rental_phase2 import (
    RentalConflict,
    get_or_create_owner_profile,
    replay_operation,
    remember_mutation,
)


class ConfirmationBody(OwnerOnboardingBodySerializer):
    candidate_digest = serializers.RegexField(r"^[0-9a-f]{64}$")

    def to_internal_value(self, data):
        if set(data) - set(self.fields):
            raise serializers.ValidationError(
                "Only the reviewed beneficiary confirmation is supported."
            )
        return super().to_internal_value(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def confirm(request):
    serializer = ConfirmationBody(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    operation = "owner_beneficiary.confirm"
    with transaction.atomic():
        actor = User.objects.select_for_update().get(pk=request.user.pk)
        require_verified_rental_account(actor)
        totp.require_sensitive_access(actor)
        replay = replay_operation(actor, operation, data["request_key"], request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        profile = get_or_create_owner_profile(actor)
        profile = OwnerPaymentProfile.objects.select_for_update().get(pk=profile.pk)
        if profile.revision != data["expected_revision"]:
            raise RentalConflict(
                "Review the current beneficiary.", code="stale_revision"
            )
        identity, recipient, public = service.candidate(profile)
        if public["digest"] != data["candidate_digest"]:
            raise RentalConflict(
                "The prepared beneficiary changed.", code="beneficiary_changed"
            )
        if "rental-policy-v1" not in data["accepted_policy_versions"]:
            raise serializers.ValidationError(
                {"accepted_policy_versions": "Review the current rental policy."}
            )
        sensitive_actions.consume(
            request,
            action="beneficiary.onboarding",
            resource_id=profile.id,
            revision=profile.revision,
            payload=request.data,
        )
        profile.provider, profile.provider_account_id = client.PROVIDER, identity
        profile.masked_beneficiary = {
            "account_last4": (
                recipient.get("msisdn") or recipient.get("bank_card_number")
            )[-4:]
        }
        profile.status, profile.payout_ready = "ready", True
        profile.requirements = []
        profile.accepted_policy_versions = list(
            dict.fromkeys(
                [*profile.accepted_policy_versions, *data["accepted_policy_versions"]]
            )
        )
        profile.revision += 1
        profile.save()
        submission = beneficiary_details.latest(profile)
        if submission and submission.status == "pending_verification":
            submission.status = "confirmed"
            submission.save(update_fields=["status", "updated_at"])
        RentalAuditEvent.objects.create(
            actor=actor,
            subject_kind="ownerpaymentprofile",
            subject_id=profile.id,
            subject_revision=profile.revision,
            action="beneficiary_confirmed",
            metadata={
                "candidate_digest": public["digest"],
                "policy_versions": data["accepted_policy_versions"],
            },
        )
        service.record(profile)
        response = Response(
            remember_mutation(
                user=actor,
                operation=operation,
                request_key=data["request_key"],
                payload=request.data,
                request_subject_id=profile.id,
                result_subject_id=profile.id,
                result_revision=profile.revision,
                resource=OwnerPaymentProfileSerializer(
                    profile, context={"request": request}
                ).data,
            )
        )
        response["Cache-Control"] = "private, no-store"
        return response
