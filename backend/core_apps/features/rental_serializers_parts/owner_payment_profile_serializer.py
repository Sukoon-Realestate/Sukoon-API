"""Rental serializers: owner payment profile serializer."""

from rest_framework import serializers
from ..models import OwnerPaymentProfile, RentalCommercialPolicy


class MoneySerializer(serializers.Serializer):
    amount_minor = serializers.IntegerField(min_value=0)
    currency = serializers.ChoiceField(choices=["EGP"])
    exponent = serializers.IntegerField(min_value=2, max_value=2)


class RentalTermsSerializer(serializers.Serializer):
    starts_on = serializers.DateField()
    ends_on_exclusive = serializers.DateField()
    handover_on = serializers.DateField()
    monthly_rent = MoneySerializer()
    deposit = MoneySerializer()
    deposit_holder = serializers.ChoiceField(choices=["owner", "platform"])
    included_services = serializers.ListField(
        child=serializers.CharField(), default=list
    )
    excluded_services = serializers.ListField(
        child=serializers.CharField(), default=list
    )
    termination_policy = serializers.JSONField()
    renewal_policy = serializers.JSONField()
    policy_version = serializers.CharField(max_length=40)
    template_id = serializers.CharField(max_length=80)
    template_version = serializers.CharField(max_length=40)
    timezone = serializers.ChoiceField(choices=["Africa/Cairo"])
    occupants = serializers.IntegerField(min_value=1)
    billing_anchor_day = serializers.IntegerField(min_value=1, max_value=31)
    commission_rate_bps = serializers.IntegerField(min_value=0)
    commission_payer = serializers.ChoiceField(choices=["owner"])
    commission_basis = serializers.ChoiceField(choices=["first_period_base_rent"])
    processing_fee_payer = serializers.ChoiceField(choices=["platform"])
    renewal_commission_rate_bps = serializers.IntegerField(min_value=0)

    def validate(self, attrs):
        if attrs["ends_on_exclusive"] <= attrs["starts_on"]:
            raise serializers.ValidationError(
                {"ends_on_exclusive": "Must be after starts_on."}
            )
        if not attrs["starts_on"] <= attrs["handover_on"] < attrs["ends_on_exclusive"]:
            raise serializers.ValidationError(
                {"handover_on": "Must fall inside the tenancy period."}
            )
        expected = {
            "policy_version": "rental-policy-v1",
            "commission_rate_bps": 1000,
            "renewal_commission_rate_bps": 0,
        }
        for key, value in expected.items():
            if attrs[key] != value:
                raise serializers.ValidationError({key: f"Must be {value}."})
        return attrs


class OwnerPaymentProfileSerializer(serializers.ModelSerializer):
    policy_summary = serializers.SerializerMethodField()
    structured_summary = serializers.SerializerMethodField()
    required_policy_versions = serializers.SerializerMethodField()
    allowed_actions = serializers.SerializerMethodField()
    blocking_reasons = serializers.SerializerMethodField()
    masked_beneficiary = serializers.SerializerMethodField()

    class Meta:
        model = OwnerPaymentProfile
        fields = [
            "id",
            "revision",
            "status",
            "masked_beneficiary",
            "provider",
            "requirements",
            "accepted_policy_versions",
            "policy_summary",
            "structured_summary",
            "required_policy_versions",
            "allowed_actions",
            "blocking_reasons",
        ]

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if request and request.query_params.get("projection") == "mobile_v1":
            # Provider routing is carried by the session descriptor. The policy
            # summary is the reviewed mobile consent text; retain the structured
            # internal policy and historical/default projection unchanged.
            fields.pop("provider")
            fields.pop("structured_summary")
        return fields

    def _is_arabic(self):
        request = self.context.get("request")
        if not request:
            return False
        lang = getattr(request, "LANGUAGE_CODE", "")
        if not lang:
            headers = getattr(request, "headers", {})
            accept_lang = (
                headers.get("Accept-Language") if hasattr(headers, "get") else ""
            )
            if not accept_lang and hasattr(request, "META"):
                accept_lang = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
            return "ar" in str(accept_lang).lower()
        return str(lang).lower().startswith("ar")

    def get_policy_summary(self, obj):
        if self._is_arabic():
            return "عمولة 10% على إيجار الفترة الأولى يدفعها المالك. عمولة تجديد 0%. رسوم خدمة المستأجر 0 ج.م."
        return "10% commission on first-period base rent, paid by owner. 0% renewal commission. 0 EGP tenant service fee."

    def get_structured_summary(self, obj):
        policy = RentalCommercialPolicy.objects.filter(
            version="rental-policy-v1", is_active=True
        ).first()
        return policy.summary if policy else {}

    def get_masked_beneficiary(self, obj):
        if not obj.masked_beneficiary:
            return ""
        if isinstance(obj.masked_beneficiary, str):
            return obj.masked_beneficiary
        if isinstance(obj.masked_beneficiary, dict):
            bank = obj.masked_beneficiary.get("bank_name") or ""
            account = str(
                obj.masked_beneficiary.get("account_last4")
                or obj.masked_beneficiary.get("last4")
                or obj.masked_beneficiary.get("account_number")
                or ""
            )[-4:]
            if bank and account:
                return f"{bank} •••• {account}"
            return str(account or bank or "")
        return ""

    def get_required_policy_versions(self, obj):
        return ["rental-policy-v1"]

    def get_allowed_actions(self, obj):
        from ..providers import fake_provider_available

        request = self.context.get("request")
        return (
            ["onboard_beneficiary"]
            if (
                request
                and request.user.pk == obj.owner_id
                and request.user.is_active
                and request.user.is_verified
                and fake_provider_available()
                and obj.status != OwnerPaymentProfile.Status.READY
            )
            else []
        )

    def get_blocking_reasons(self, obj):
        from ..providers import fake_provider_available

        is_ar = self._is_arabic()
        reasons = []
        if not fake_provider_available():
            reasons.append(
                "خدمة إعداد المستفيد غير متاحة حالياً."
                if is_ar
                else "Beneficiary onboarding is unavailable in this environment."
            )
        if obj.status != OwnerPaymentProfile.Status.READY:
            reasons.append(
                "يلزم استكمال إعداد حساب المستفيد."
                if is_ar
                else "Beneficiary onboarding is incomplete."
            )
        if "rental-policy-v1" not in obj.accepted_policy_versions:
            reasons.append(
                "لم يتم قبول سياسة التأجير المطلوبة."
                if is_ar
                else "The required rental policy has not been accepted."
            )
        return reasons


class OwnerOnboardingBodySerializer(serializers.Serializer):
    expected_revision = serializers.IntegerField(min_value=1)
    request_key = serializers.UUIDField()
    accepted_policy_versions = serializers.ListField(
        child=serializers.CharField(max_length=40), allow_empty=False
    )


class RentalInterestBodySerializer(serializers.Serializer):
    academic_plan_id = serializers.UUIDField(required=False)
    academic_revision = serializers.IntegerField(min_value=1, required=False)
    source_housing_offer_id = serializers.UUIDField(required=False)
    source_housing_offer_revision = serializers.IntegerField(
        min_value=1, required=False
    )
    application_share_id = serializers.UUIDField(required=False)
    property_id = serializers.UUIDField()
    offer_id = serializers.CharField(max_length=64)
    offer_revision = serializers.IntegerField(min_value=1)
    desired_start = serializers.DateField()
    months = serializers.IntegerField(min_value=1, max_value=60)
    occupants = serializers.IntegerField(min_value=1, max_value=20)
    message = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    request_key = serializers.UUIDField()
    expected_revision = serializers.IntegerField(min_value=0, max_value=0)
