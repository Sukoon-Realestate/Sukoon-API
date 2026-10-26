"""Serializers: tenancy invitation serializer."""

from django.utils import timezone
from rest_framework import serializers
from ..services.lease_permissions import can_revoke_invitation
from ..models import TenancyInvitation


class TenancyInvitationResponseSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["accepted", "rejected"])
    revision = serializers.IntegerField(min_value=1)
    request_key = serializers.CharField(max_length=100)


class TenancyInvitationSerializer(serializers.ModelSerializer):
    requested_stay = serializers.SerializerMethodField()
    source_visit_id = serializers.UUIDField(
        source="source_visit.id", read_only=True, allow_null=True
    )
    source_decision_id = serializers.UUIDField(
        source="source_decision.id", read_only=True, allow_null=True
    )
    property_id = serializers.UUIDField(source="property.id", read_only=True)
    property_title = serializers.CharField(source="property.title", read_only=True)
    owner_id = serializers.UUIDField(source="owner.id", read_only=True)
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)
    tenant_name = serializers.CharField(source="tenant.get_full_name", read_only=True)
    lease_id = serializers.UUIDField(source="lease.id", read_only=True, allow_null=True)
    eligible_for_lease = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()
    interest_id = serializers.UUIDField(
        source="interest.id", read_only=True, allow_null=True
    )
    terms_proposal_id = serializers.UUIDField(
        source="terms_proposal.id", read_only=True, allow_null=True
    )
    allowed_actions = serializers.SerializerMethodField()
    blocking_reasons = serializers.SerializerMethodField()

    class Meta:
        model = TenancyInvitation
        fields = [
            "id",
            "property_id",
            "property_title",
            "owner_id",
            "owner_name",
            "tenant_id",
            "tenant_name",
            "offer_id",
            "offer_snapshot",
            "status",
            "revision",
            "created_at",
            "expires_at",
            "accepted_at",
            "rejected_at",
            "revoked_at",
            "lease_id",
            "eligible_for_lease",
            "actions",
            "interest_id",
            "terms_proposal_id",
            "consumed_at",
            "allowed_actions",
            "blocking_reasons",
            "source_visit_id",
            "requested_stay",
            "source_decision_id",
            "provenance_version",
        ]

    def get_requested_stay(self, obj):
        # Disclosed preferences only. They never override independently reviewed terms.
        if obj.source_visit_id:
            return obj.source_visit.stay_preferences
        if obj.interest_id:
            item = obj.interest
            return {
                "starts_on": str(item.desired_start),
                "ends_on_exclusive": str(item.desired_end) if item.desired_end else "",
                "occupants": item.occupants,
            }
        return None

    def get_eligible_for_lease(self, obj):
        from ..services.tenancy_invitations import invitation_is_eligible

        return invitation_is_eligible(obj)

    def get_actions(self, obj):
        request = self.context.get("request")
        can_respond = bool(
            request
            and request.user == obj.tenant
            and obj.status == TenancyInvitation.Status.PENDING
            and not obj.lease_id
            and not obj.consumed_at
            and obj.expires_at > timezone.now()
            and request.user.is_active
            and request.user.is_verified
        )
        from ..services.tenancy_invitations import current_invitation_problem

        return {
            "can_respond": can_respond,
            "can_accept": can_respond and current_invitation_problem(obj) is None,
            "can_reject": can_respond,
        }

    def get_allowed_actions(self, obj):
        request = self.context.get("request")
        actions = []
        if self.get_actions(obj)["can_respond"]:
            actions.append("respond")
        if can_revoke_invitation(request.user if request else None, obj):
            actions.append("revoke_invitation")
        return actions

    def get_blocking_reasons(self, obj):
        from ..services.tenancy_invitations import current_invitation_problem, localized

        request = self.context.get("request")
        if obj.consumed_at or obj.lease_id:
            return [
                localized(
                    request,
                    "This invitation has already been consumed.",
                    "استُخدمت هذه الدعوة بالفعل لإنشاء عقد.",
                )
            ]
        if obj.expires_at <= timezone.now():
            return [
                localized(
                    request, "This invitation has expired.", "انتهت صلاحية هذه الدعوة."
                )
            ]

        if (
            obj.status
            in {TenancyInvitation.Status.PENDING, TenancyInvitation.Status.ACCEPTED}
            and current_invitation_problem(obj) == "property_review_pending"
        ):
            return [
                localized(
                    request,
                    "Acceptance and lease creation are paused while the property is reviewed. Refresh after approval and review the current terms. The invitation deadline is unchanged.",
                    "القبول وإنشاء العقد متوقفان أثناء مراجعة العقار. حدّث الدعوة بعد الاعتماد وراجع الشروط الحالية. مهلة الدعوة لم تتغير.",
                )
            ]
        return []
