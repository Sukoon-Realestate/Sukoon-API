"""Explicit academic contracts; no implicit price, disclosure or consent defaults."""

from rest_framework import serializers as s
from .rental_lifecycle_serializers import StrictSerializer, CommandBody

PERIODS = [
    "semester",
    "academic_year",
    "year_and_summer",
    "summer",
    "internship",
    "other",
]


class Preferences(StrictSerializer):
    study_times = s.CharField(max_length=200, required=False, allow_blank=True)
    sleep = s.CharField(max_length=200, required=False, allow_blank=True)
    guests = s.CharField(max_length=200, required=False, allow_blank=True)
    groceries = s.CharField(max_length=200, required=False, allow_blank=True)
    cleaning = s.CharField(max_length=200, required=False, allow_blank=True)
    smoking = s.CharField(max_length=200, required=False, allow_blank=True)
    cooking = s.CharField(max_length=200, required=False, allow_blank=True)
    shared_room = s.CharField(max_length=200, required=False, allow_blank=True)
    weekends = s.CharField(max_length=200, required=False, allow_blank=True)
    accessibility = s.CharField(max_length=200, required=False, allow_blank=True)
    exam_quiet = s.CharField(max_length=200, required=False, allow_blank=True)


class StudentProfileBody(CommandBody):
    campus_id = s.UUIDField(required=False, allow_null=True)
    institution_name = s.CharField(
        max_length=200, required=False, allow_blank=True, default=""
    )
    academic_stage = s.CharField(
        max_length=100, required=False, allow_blank=True, default=""
    )
    enrollment_status = s.ChoiceField(
        choices=[
            "admission_pending",
            "admitted",
            "enrolled",
            "graduated",
            "not_enrolled",
        ]
    )
    study_start = s.DateField(required=False, allow_null=True)
    study_end = s.DateField(required=False, allow_null=True)
    preferences = Preferences(required=False, default=dict)
    roommate_disclosures = s.ListField(
        child=s.ChoiceField(choices=list(Preferences().fields) + ["campus"]),
        default=list,
    )

    def validate(self, values):
        if (
            values.get("study_start")
            and values.get("study_end")
            and values["study_end"] <= values["study_start"]
        ):
            raise s.ValidationError({"study_end": "End must follow start."})
        return values


class StudyRequirements(StrictSerializer):
    campus_ids = s.ListField(child=s.UUIDField(), max_length=10, default=list)
    internship_destination = s.CharField(max_length=200, allow_blank=True, default="")
    commute_mode = s.ChoiceField(
        choices=["walking", "cycling", "driving", "transit"], default="transit"
    )
    max_commute_minutes = s.IntegerField(
        min_value=1, max_value=240, allow_null=True, default=None
    )
    study_space = s.CharField(max_length=500, allow_blank=True, default="")
    internet = s.CharField(max_length=500, allow_blank=True, default="")
    summer_intention = s.ChoiceField(
        choices=[
            "undecided",
            "keep_paying",
            "vacate",
            "request_storage",
            "request_return",
            "renew",
        ],
        default="undecided",
    )
    admission_contingency = s.BooleanField(default=False)


class PlanBody(CommandBody):
    group_id = s.UUIDField(required=False, allow_null=True)
    previous_plan_id = s.UUIDField(required=False, allow_null=True)
    current_lease_id = s.UUIDField(required=False, allow_null=True)
    label = s.CharField(max_length=160)
    period_kind = s.ChoiceField(choices=PERIODS)
    starts_on = s.DateField()
    ends_on_exclusive = s.DateField()
    budget_basis = s.ChoiceField(choices=["per_person", "whole_group"])
    criteria = s.DictField()
    requirements = StudyRequirements()
    participant_ids = s.ListField(child=s.UUIDField(), min_length=1, max_length=20)

    def validate(self, values):
        if values["ends_on_exclusive"] <= values["starts_on"]:
            raise s.ValidationError(
                {"ends_on_exclusive": "End must follow start (exclusive)."}
            )
        if len(set(values["participant_ids"])) != len(values["participant_ids"]):
            raise s.ValidationError({"participant_ids": "Participants must be unique."})
        return values


class ParticipantBody(CommandBody):
    requirements = StudyRequirements()
    budget_min = s.DictField()
    budget_max = s.DictField()
    owner_disclosures = s.ListField(
        child=s.ChoiceField(
            choices=["campuses", "affordability", "study_requirements"]
        ),
        max_length=3,
    )


class ConsentBody(CommandBody):
    digest = s.RegexField(r"^[0-9a-f]{64}$")
    consent = s.BooleanField()


class PublishBody(ConsentBody):
    pass


class ArrangementRules(StrictSerializer):
    quiet_hours = s.CharField(max_length=500, allow_blank=True, default="")
    guests = s.CharField(max_length=500, allow_blank=True, default="")
    cleaning = s.CharField(max_length=500, allow_blank=True, default="")
    shared_purchases = s.CharField(max_length=500, allow_blank=True, default="")
    common_spaces = s.CharField(max_length=500, allow_blank=True, default="")
    communication = s.CharField(max_length=500, allow_blank=True, default="")
    nonurgent_maintenance = s.CharField(max_length=500, allow_blank=True, default="")


class ArrangementBody(CommandBody):
    plan_revision = s.IntegerField(min_value=1)
    kind = s.ChoiceField(choices=["shared_living", "exam"])
    starts_on = s.DateField()
    ends_on_exclusive = s.DateField()
    rules = ArrangementRules()


class StudentPolicyBody(CommandBody):
    offer_id = s.CharField(max_length=64)
    offer_revision = s.IntegerField(min_value=1)
    eligibility = s.ChoiceField(
        choices=["open", "current_enrollment", "admission_or_enrollment"]
    )
    period_kinds = s.ListField(
        child=s.ChoiceField(choices=PERIODS), min_length=1, max_length=6
    )
    starts_on = s.DateField()
    ends_on_exclusive = s.DateField()
    expires_at = s.DateTimeField()
    exam_extension_requests = s.BooleanField(default=False)
    renewal_requests = s.BooleanField(default=False)
    summer_storage_requests = s.BooleanField(default=False)


class LinkBody(CommandBody):
    lease_id = s.UUIDField()


class CheckInBody(CommandBody):
    lease_id = s.UUIDField()
    kind = s.ChoiceField(
        choices=[
            "access",
            "wrong_space",
            "missing_facility",
            "maintenance",
            "roommate_support",
            "academic_transition",
            "admission_request",
        ]
    )
    note = s.CharField(max_length=2000)


class SummaryGrantBody(CommandBody):
    recipient_email = s.EmailField()
    scopes = s.ListField(
        child=s.ChoiceField(choices=["booking", "invoice", "receipt"]),
        min_length=1,
        max_length=3,
    )
    invoice_id = s.UUIDField(required=False, allow_null=True)
    receipt_id = s.UUIDField(required=False, allow_null=True)
    expires_at = s.DateTimeField()
    consent = s.BooleanField()
