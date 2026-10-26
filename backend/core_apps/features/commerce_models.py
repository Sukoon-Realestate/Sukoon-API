"""Additive commerce records. Provider secrets and raw purchase proofs never live here."""

import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q
from core_apps.common.models import TimeStampedModel


class CommerceFeature(TimeStampedModel):
    revision = models.PositiveIntegerField(default=1, editable=False)
    code = models.SlugField(unique=True)
    workspace = models.CharField(
        max_length=10, choices=[("tenant", "Tenant"), ("owner", "Owner")]
    )
    label_en = models.CharField(max_length=120)
    label_ar = models.CharField(max_length=120)
    description_en = models.TextField(blank=True)
    description_ar = models.TextField(blank=True)
    unit_label_en = models.CharField(max_length=100, blank=True)
    unit_label_ar = models.CharField(max_length=100, blank=True)
    available = models.BooleanField(default=False)
    free = models.BooleanField(default=False)
    free_limit = models.PositiveIntegerField(null=True, blank=True)
    # Enforcement requires an explicit rollout after grants have been installed.
    enforced = models.BooleanField(default=False)


class PlanBenefit(TimeStampedModel):
    revision = models.PositiveIntegerField(default=1, editable=False)
    plan = models.ForeignKey(
        "features.SubscriptionPlan", on_delete=models.CASCADE, related_name="benefits"
    )
    feature = models.ForeignKey(CommerceFeature, on_delete=models.PROTECT)
    included = models.BooleanField(default=True)
    limit = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "feature"], name="unique_plan_feature"
            )
        ]


class EntitlementGrant(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )
    organization = models.ForeignKey(
        "features.Company", on_delete=models.PROTECT, null=True, blank=True
    )
    feature = models.ForeignKey(CommerceFeature, on_delete=models.PROTECT)
    source = models.CharField(
        max_length=16, choices=[("grandfathered", "Grandfathered"), ("free", "Free")]
    )
    limit = models.PositiveIntegerField(null=True, blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    policy_reference = models.CharField(max_length=200)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(user__isnull=False, organization__isnull=True)
                    | Q(user__isnull=True, organization__isnull=False)
                ),
                name="grant_exactly_one_subject",
            )
        ]


class FeatureUsage(TimeStampedModel):
    """Durable command receipts, never incremented by an entitlement GET."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )
    organization = models.ForeignKey(
        "features.Company", on_delete=models.PROTECT, null=True, blank=True
    )
    feature = models.ForeignKey(CommerceFeature, on_delete=models.PROTECT)
    request_key = models.UUIDField()
    resource_id = models.UUIDField()
    fingerprint = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "feature", "request_key"],
                condition=Q(organization__isnull=True),
                name="unique_personal_feature_command",
            ),
            models.UniqueConstraint(
                fields=["organization", "feature", "request_key"],
                condition=Q(organization__isnull=False),
                name="unique_company_feature_command",
            ),
        ]


class StoreAccount(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    platform = models.CharField(
        max_length=10, choices=[("ios", "iOS"), ("android", "Android")]
    )
    environment = models.CharField(
        max_length=10, choices=[("sandbox", "Sandbox"), ("live", "Live")]
    )
    app_account_token = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "platform", "environment"],
                name="unique_store_account_environment",
            )
        ]


class StoreProduct(TimeStampedModel):
    plan = models.ForeignKey(
        "features.SubscriptionPlan",
        on_delete=models.PROTECT,
        related_name="store_products",
    )
    platform = models.CharField(
        max_length=10, choices=[("ios", "iOS"), ("android", "Android")]
    )
    environment = models.CharField(
        max_length=10, choices=[("sandbox", "Sandbox"), ("live", "Live")]
    )
    product_id = models.CharField(max_length=200)
    active = models.BooleanField(default=False)
    # Prices/periods must be reconciled against the store before publishing.
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    period_months = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["platform", "environment", "product_id"],
                name="unique_store_sku",
            ),
            models.UniqueConstraint(
                fields=["plan", "platform", "environment"],
                name="unique_plan_store_product",
            ),
        ]


class StorePurchaseIntent(TimeStampedModel):
    attempt = models.OneToOneField(
        "features.PaymentAttempt", on_delete=models.PROTECT, related_name="store_intent"
    )
    account = models.ForeignKey(StoreAccount, on_delete=models.PROTECT)
    product = models.ForeignKey(StoreProduct, on_delete=models.PROTECT)
    route_snapshot = models.JSONField()
    expires_at = models.DateTimeField()
    fulfilled_at = models.DateTimeField(null=True, blank=True)


class StoreTransaction(TimeStampedModel):
    intent = models.ForeignKey(
        StorePurchaseIntent, on_delete=models.PROTECT, related_name="transactions"
    )
    platform = models.CharField(max_length=10)
    environment = models.CharField(max_length=10)
    transaction_id = models.CharField(max_length=200)
    original_transaction_id = models.CharField(max_length=200)
    proof_digest = models.CharField(max_length=64)
    verified_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["platform", "environment", "transaction_id"],
                name="unique_verified_store_transaction",
            )
        ]


class BillingSourceLink(TimeStampedModel):
    invoice = models.ForeignKey(
        "features.RentInvoice", on_delete=models.PROTECT, related_name="source_links"
    )
    source_kind = models.CharField(max_length=30)
    source_id = models.UUIDField()
    source_version = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source_kind", "source_id", "source_version"],
                name="unique_source_charge_version",
            )
        ]


class StoreNotification(TimeStampedModel):
    platform = models.CharField(max_length=10)
    environment = models.CharField(max_length=10)
    event_id = models.CharField(max_length=200)
    payload_digest = models.CharField(max_length=64)
    account = models.ForeignKey(StoreAccount, on_delete=models.PROTECT)
    processed_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["platform", "environment", "event_id"],
                name="unique_store_notification",
            )
        ]


class StoreSubscriptionHead(TimeStampedModel):
    account = models.ForeignKey(StoreAccount, on_delete=models.PROTECT)
    original_transaction_id = models.CharField(max_length=200)
    observed_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account", "original_transaction_id"],
                name="unique_store_subscription_head",
            )
        ]


class StorePurchaseReview(TimeStampedModel):
    """Durable reconciliation queue for verified but undelivered purchases."""

    account = models.ForeignKey(StoreAccount, on_delete=models.PROTECT)
    transaction_id = models.CharField(max_length=200)
    product_id = models.CharField(max_length=200)
    proof_digest = models.CharField(max_length=64)
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3)
    exponent = models.PositiveSmallIntegerField()
    reason_code = models.CharField(max_length=80)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account", "transaction_id"],
                name="unique_store_purchase_review",
            )
        ]
