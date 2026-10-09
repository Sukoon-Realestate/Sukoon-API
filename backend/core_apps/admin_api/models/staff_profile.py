from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core_apps.common.models import TimeStampedModel


class StaffProfile(TimeStampedModel):
    class RoleName(models.TextChoices):
        SYSTEM_OWNER = "system_owner", _("System Owner")
        MAIN_ADMIN = "main_admin", _("Main Admin")
        KYC_REVIEWER = "kyc_reviewer", _("KYC Reviewer")
        PROPERTY_REVIEWER = "property_reviewer", _("Property Reviewer")
        SUPPORT = "support", _("Customer Support")
        FINANCIAL_APPROVER = "financial_approver", _("Financial Approver")
        PSP_RECONCILIATION = "psp_reconciliation", _("PSP Reconciliation")
        PAYOUT_OPERATOR = "payout_operator", _("Payout Operator")
        REFUND_OPERATOR = "refund_operator", _("Refund Operator")
        DISPUTE_RESOLVER = "dispute_resolver", _("Dispute Resolver")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_profile",
        verbose_name=_("User"),
    )
    role_name = models.CharField(
        _("Role Name"),
        max_length=50,
        choices=RoleName.choices,
        default=RoleName.KYC_REVIEWER,
        db_index=True,
    )
    display_role = models.CharField(
        _("Display Role"), max_length=100, blank=True, default=""
    )
    is_active = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        verbose_name = _("Staff Profile")
        verbose_name_plural = _("Staff Profiles")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.get_full_name or self.user.email} - {self.get_role_name_display()}"
