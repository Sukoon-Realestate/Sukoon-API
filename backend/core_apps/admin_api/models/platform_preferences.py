from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


# Existing dashboard preferences. These are not authorization or KYC policy.
def default_platform_preferences():
    return {
        "maxReviewHours": True,
        "tenantDocsRequired": False,
        "landlordDocsRequired": True,
        "autoVerification": True,
        "maxPhotosLimit": True,
        "reviewPeriodDays": False,
        "approxLocation": True,
        "hidePhoneDefault": True,
    }


class PlatformPreferences(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    values = models.JSONField(default=default_platform_preferences)
    revision = models.PositiveIntegerField(default=1, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(id=1), name="single_platform_preferences"
            )
        ]

    def clean(self):
        if (
            not isinstance(self.values, dict)
            or set(self.values) != set(default_platform_preferences())
            or any(type(value) is not bool for value in self.values.values())
        ):
            raise ValidationError("Supply the supported boolean platform preferences.")


class PlatformPreferenceAudit(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    revision = models.PositiveIntegerField()
    before = models.JSONField()
    after = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
