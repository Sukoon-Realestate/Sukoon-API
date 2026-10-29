"""Only an explicit JSON boolean can acknowledge shortening contract notice."""

from rest_framework import serializers


class ExplicitBoolean(serializers.BooleanField):
    def to_internal_value(self, data):
        if type(data) is not bool:
            self.fail("invalid", input=data)
        return data


class TerminationNoticeCreateSerializer(serializers.Serializer):
    termination_mode = serializers.ChoiceField(
        choices=["contract_notice", "mutual_short_notice", "natural_expiry"]
    )
    notice_basis_digest = serializers.RegexField(r"^[a-f0-9]{64}$")
    short_notice_acknowledged = ExplicitBoolean(required=False, default=False)


class TerminationNoticeAcceptSerializer(serializers.Serializer):
    termination_notice_digest = serializers.RegexField(r"^[a-f0-9]{64}$")
    short_notice_acknowledged = ExplicitBoolean(required=False, default=False)
