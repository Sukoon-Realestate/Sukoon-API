from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class TicketInformationRequest(TimeStampedModel):
    ticket = models.ForeignKey("support.Ticket", on_delete=models.PROTECT, related_name="information_requests")
    source_message = models.ForeignKey("support.TicketMessage", on_delete=models.PROTECT, related_name="information_questions")
    prompt = models.CharField(max_length=2000)
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, default="requested", choices=[
        (value, value) for value in ("requested", "answer_sent", "accepted", "withdrawn")])
    answer = models.ForeignKey("support.TicketMessage", on_delete=models.PROTECT, null=True, related_name="information_answers")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    evidence_requirement = models.JSONField(default=dict)


class TicketEvidenceSubmission(TimeStampedModel):
    request = models.ForeignKey(TicketInformationRequest, on_delete=models.PROTECT, related_name="evidence_versions")
    message = models.OneToOneField("support.TicketMessage", on_delete=models.PROTECT)
    version = models.PositiveIntegerField()
    files = models.JSONField(default=list)
    review_status = models.CharField(max_length=16, default="submitted")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True)
    reviewed_at = models.DateTimeField(null=True)
    review_reason = models.CharField(max_length=1000, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["request", "version"], name="unique_support_evidence_version")]


class TicketInformationEvent(TimeStampedModel):
    request = models.ForeignKey(TicketInformationRequest, on_delete=models.PROTECT, related_name="history")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=30)
    revision = models.PositiveIntegerField()
    reason = models.CharField(max_length=2000, blank=True)
    answer = models.ForeignKey("support.TicketMessage", on_delete=models.PROTECT, null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["request", "revision"], name="unique_support_information_revision")]
