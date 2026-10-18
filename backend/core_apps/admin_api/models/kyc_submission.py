from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core_apps.common.models import TimeStampedModel


class KYCSubmission(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending Review")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")

    profile = models.ForeignKey(
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="kyc_submissions",
        verbose_name=_("Profile"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_kycs",
        verbose_name=_("Reviewer"),
    )
    reviewed_at = models.DateTimeField(_("Reviewed At"), null=True, blank=True)
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True, default="")
    notes = models.TextField(_("Admin Notes"), blank=True, default="")
    evidence_snapshot = models.JSONField(default=dict, editable=False)
    evidence_digest = models.CharField(
        max_length=64, blank=True, default="", editable=False
    )
    submission_fingerprint = models.CharField(
        max_length=64, blank=True, default="", editable=False
    )
    superseded_at = models.DateTimeField(null=True, blank=True, editable=False)

    def save(self, *args, **kwargs):
        if self.pk:
            before = (
                type(self)
                .objects.filter(pk=self.pk)
                .values(
                    "evidence_snapshot", "evidence_digest", "submission_fingerprint"
                )
                .first()
            )
            if before and any(
                before[field] != getattr(self, field) for field in before
            ):
                from django.core.exceptions import ValidationError

                raise ValidationError(
                    "Submitted identity evidence is immutable; submit a new version."
                )
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("KYC Submission")
        verbose_name_plural = _("KYC Submissions")
        ordering = ["-created_at"]

    def __str__(self):
        return f"KYC for {self.profile.user.email} - {self.get_status_display()}"
