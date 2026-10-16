from rest_framework import serializers
from .company_serializers import CommandBody, StrictBody


class StaffFields(StrictBody):
    employee_code = serializers.CharField(max_length=60, allow_blank=True, default="")
    display_name = serializers.CharField(max_length=200)
    work_email = serializers.EmailField()
    mobile = serializers.CharField(max_length=32, allow_blank=True, default="")
    job_title = serializers.CharField(max_length=150, allow_blank=True, default="")
    department = serializers.CharField(max_length=100, allow_blank=True, default="")
    project_code = serializers.CharField(max_length=100, allow_blank=True, default="")
    roles = serializers.ListField(
        child=serializers.ChoiceField(
            choices=["admin", "coordinator", "approver", "employee"]
        ),
        allow_empty=False,
        max_length=4,
    )


class StaffBody(StaffFields, CommandBody):
    pass


class StaffRow(StaffFields):
    row_key = serializers.UUIDField()


class StaffBatchBody(CommandBody):
    batch_key = serializers.UUIDField()
    rows = StaffRow(many=True, allow_empty=False)

    def validate(self, data):
        rows = data["rows"]
        codes = [r["employee_code"].strip() for r in rows if r["employee_code"].strip()]
        emails = [r["work_email"].strip().casefold() for r in rows]
        if (
            len(rows) > 50
            or len({r["row_key"] for r in rows}) != len(rows)
            or len(set(codes)) != len(codes)
            or len(set(emails)) != len(emails)
        ):
            raise serializers.ValidationError(
                "Submit at most 50 distinct staff rows without duplicate contacts or employee codes."
            )
        return data


class ActivationPreviewBody(StrictBody):
    token = serializers.CharField(min_length=32, max_length=200)


class ActivationResponseBody(CommandBody, ActivationPreviewBody):
    proposal_revision = serializers.IntegerField(min_value=1)


class ContactProofBody(CommandBody, ActivationPreviewBody):
    pass


class ContactProofVerifyBody(StrictBody):
    code = serializers.RegexField(r"^[0-9]{8}$")


class ApprovalRouteBody(CommandBody):
    default_approver_id = serializers.UUIDField(allow_null=True)
    backup_approver_id = serializers.UUIDField(allow_null=True)
    reason = serializers.CharField(max_length=1000)


class ApprovalReassignmentBody(CommandBody):
    approver_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=1000)
