"""Non-rent catalogs and entitlements; financial records stay in RentInvoice."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from core_apps.common.models import TimeStampedModel


class SubscriptionPlan(TimeStampedModel):
    name_en = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100)
    description_en = models.TextField(blank=True)
    description_ar = models.TextField(blank=True)
    workspace = models.CharField(max_length=10, choices=[("tenant", "Tenant"), ("owner", "Owner"), ("both", "Both")])
    period_months = models.PositiveSmallIntegerField(default=1)
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    revision = models.PositiveIntegerField(default=1, editable=False)
    active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            models.CheckConstraint(check=models.Q(amount_minor__gt=0), name="subscription_plan_positive_price"),
            models.CheckConstraint(check=models.Q(period_months__gte=1, period_months__lte=120), name="subscription_plan_valid_period"),
            models.CheckConstraint(check=models.Q(currency="EGP", exponent=2), name="subscription_plan_supported_money"),
        ]

    def clean(self):
        if self.currency != "EGP" or self.exponent != 2:
            raise ValidationError("Only EGP with exponent 2 is currently supported.")
        if not self.name_ar.strip() or not self.name_en.strip():
            raise ValidationError("Arabic and English plan names are required.")

    def __str__(self):
        return self.name_en


class AccountSubscription(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    invoice = models.OneToOneField("features.RentInvoice", on_delete=models.PROTECT, related_name="subscription")
    workspace = models.CharField(max_length=10)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)
    plan_snapshot = models.JSONField()

    class Meta:
        constraints = [models.CheckConstraint(check=models.Q(ends_at__gt=models.F("starts_at")), name="subscription_valid_period")]
