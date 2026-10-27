"""Serializers: rent invoice serializer."""

from rest_framework import serializers
from core_apps.common.locale_middleware import resolve_request_language
from core_apps.common.translation import translate_message
from ..models import RentInvoice


class LeaseCreateSerializer(serializers.Serializer):
    property_id = serializers.UUIDField()
    tenant_id = serializers.UUIDField()
    template_id = serializers.CharField(max_length=80)
    template_version = serializers.CharField(max_length=40)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    rent = serializers.DictField()
    request_key = serializers.CharField(max_length=100)
    offer_id = serializers.CharField(max_length=64, required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["end_date"] <= attrs["start_date"]:
            raise serializers.ValidationError(
                {"end_date": "End date must be after start date."}
            )
        rent = attrs["rent"]
        if (
            not isinstance(rent, dict)
            or not isinstance(rent.get("amount_minor"), int)
            or rent["amount_minor"] <= 0
        ):
            raise serializers.ValidationError(
                {"rent": "A positive integer amount_minor is required."}
            )
        if rent.get("currency") != "EGP" or rent.get("exponent", 2) != 2:
            raise serializers.ValidationError(
                {"rent": "Only EGP with exponent 2 is supported."}
            )
        return attrs


class RentInvoiceSerializer(serializers.ModelSerializer):
    billing_period_id = serializers.UUIDField(
        source="billing_period.id", read_only=True
    )
    lease_id = serializers.UUIDField(source="lease.id", read_only=True)
    property_title = serializers.CharField(
        source="lease.property.title", read_only=True
    )
    amount = serializers.SerializerMethodField()
    can_pay = serializers.SerializerMethodField()
    offer_id = serializers.CharField(source="lease.offer_id", read_only=True)
    offer_snapshot = serializers.JSONField(
        source="lease.offer_snapshot", read_only=True
    )
    invoice_status = serializers.CharField(source="status", read_only=True)
    balance = serializers.SerializerMethodField()
    allowed_actions = serializers.SerializerMethodField()
    blocking_reasons = serializers.SerializerMethodField()
    lines = serializers.SerializerMethodField()
    payment_attempt_id = serializers.SerializerMethodField()
    charges = serializers.SerializerMethodField()
    credits = serializers.SerializerMethodField()
    applied = serializers.SerializerMethodField()

    class Meta:
        model = RentInvoice
        fields = [
            "id",
            "lease_id",
            "property_title",
            "reference",
            "due_date",
            "amount",
            "status",
            "receipt_url",
            "can_pay",
            "offer_id",
            "offer_snapshot",
            "revision",
            "invoice_status",
            "balance",
            "allowed_actions",
            "blocking_reasons",
            "invoice_type",
            "billing_period_id",
            "charges",
            "credits",
            "applied",
            "period_start",
            "period_end_exclusive",
            "due_at",
            "deferred_until",
            "lines",
            "payment_attempt_id",
            "receipt_id",
        ]

    def get_amount(self, obj):
        return {
            "amount_minor": obj.amount_minor,
            "currency": obj.currency,
            "exponent": obj.exponent,
        }

    def get_can_pay(self, obj):
        from ..services.rental_phase3 import invoice_payment_allowed

        request = self.context.get("request")
        return invoice_payment_allowed(request.user if request else None, obj)

    def _money(self, obj, amount):
        return {
            "amount_minor": amount,
            "currency": obj.currency,
            "exponent": obj.exponent,
        }

    def get_charges(self, obj):
        return self._money(obj, obj.charges_minor)

    def get_credits(self, obj):
        return self._money(obj, obj.credits_minor)

    def get_applied(self, obj):
        return self._money(obj, obj.applied_minor)

    def get_balance(self, obj):
        from ..services.rental_phase3 import invoice_balance_minor

        amount = invoice_balance_minor(obj)
        return {
            "amount_minor": amount,
            "currency": obj.currency,
            "exponent": obj.exponent,
        }

    def get_allowed_actions(self, obj):
        return ["quote", "checkout"] if self.get_can_pay(obj) else []

    def get_lines(self, obj):
        language = resolve_request_language(self.context.get("request"))
        generated_descriptions = {
            "base_rent": "Base rent",
            "security_deposit": "Security deposit",
        }
        return [
            {
                "id": str(line.id),
                "type": line.line_type,
                "description": (
                    translate_message(line.description, language)
                    if generated_descriptions.get(line.line_type) == line.description
                    else line.description
                ),
                "amount": {
                    "amount_minor": line.amount_minor,
                    "currency": line.currency,
                    "exponent": line.exponent,
                },
            }
            for line in obj.lines.all()
        ]

    def get_payment_attempt_id(self, obj):
        attempt = obj.payment_attempts.filter(
            payment_status__in=["created", "pending", "authorized"]
        ).first()
        return str(attempt.id) if attempt else None

    def get_blocking_reasons(self, obj):
        from ..providers import checkout_available

        if self.get_can_pay(obj):
            return []
        if not checkout_available():
            return ["Secure rent checkout is not available yet."]
        return ["This invoice is not currently payable."]


class RevisionRequestSerializer(serializers.Serializer):
    revision = serializers.IntegerField(min_value=1)
    request_key = serializers.CharField(max_length=100)


class TenancyInvitationCreateSerializer(serializers.Serializer):
    property_id = serializers.UUIDField()
    tenant_id = serializers.UUIDField()
    offer_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    expected_offer_revision = serializers.IntegerField(min_value=1, required=False)
    request_key = serializers.CharField(max_length=100)
    source_visit_id = serializers.UUIDField(required=False)
    source_decision_id = serializers.UUIDField(required=False)
