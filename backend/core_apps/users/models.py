import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from core_apps.users.managers import UserManager
from core_apps.common.models import TimeStampedModel


class User(AbstractUser):
    pkid = models.BigAutoField(primary_key=True, editable=False)
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    first_name = models.CharField(_("First Name"), max_length=50)
    last_name = models.CharField(_("Last Name"), max_length=50)
    email = models.EmailField(_("Email"), max_length=254, unique=True)
    is_verified = models.BooleanField(_("Is Verified"), default=False)
    is_email_verified = models.BooleanField(
        _("Email possession verified"), default=False
    )

    security_epoch = models.PositiveIntegerField(default=0)
    sensitive_actions_frozen = models.BooleanField(default=False)

    username = None

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-date_joined"]

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class SocialAccount(TimeStampedModel):
    PROVIDER_GOOGLE = "google"
    PROVIDER_APPLE = "apple"
    PROVIDER_FACEBOOK = "facebook"

    PROVIDER_CHOICES = [
        (PROVIDER_GOOGLE, "Google"),
        (PROVIDER_APPLE, "Apple"),
        (PROVIDER_FACEBOOK, "Facebook"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="social_accounts"
    )
    provider = models.CharField(max_length=16, choices=PROVIDER_CHOICES, db_index=True)
    provider_uid = models.CharField(max_length=255, db_index=True)
    email = models.EmailField(blank=True)

    class Meta:
        verbose_name = _("Social Account")
        verbose_name_plural = _("Social Accounts")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_uid"],
                name="uniq_provider_uid",
            ),
        ]

    def __str__(self):
        return f"{self.provider}:{self.provider_uid} -> {self.user.email}"


class AuthSession(TimeStampedModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="auth_sessions"
    )
    security_epoch = models.PositiveIntegerField()
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)


class SecurityEvent(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    actor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="security_actions",
    )
    action = models.CharField(max_length=70)
    security_epoch = models.PositiveIntegerField()
    subject_id = models.UUIDField(null=True, blank=True)
    policy_version = models.CharField(max_length=80, blank=True, default="")
    decision = models.CharField(max_length=30)


class SensitiveAuthorization(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    session = models.ForeignKey(AuthSession, on_delete=models.PROTECT)
    security_epoch = models.PositiveIntegerField()
    action = models.CharField(max_length=80)
    resource_id = models.UUIDField()
    resource_revision = models.PositiveIntegerField()
    payload_digest = models.CharField(max_length=64)
    policy = models.ForeignKey("features.PolicyDecision", on_delete=models.PROTECT)
    expires_at = models.DateTimeField()
    provider_challenge = models.CharField(max_length=200, blank=True, default="")
    proof_digest = models.CharField(max_length=64, blank=True, default="")
    verified_at = models.DateTimeField(null=True, blank=True)
    consumed_at = models.DateTimeField(null=True, blank=True)
    assurance = models.CharField(max_length=80, blank=True, default="")
