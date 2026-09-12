from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from core_apps.common.models import TimeStampedModel
from cloudinary.models import CloudinaryField
from phonenumber_field.modelfields import PhoneNumberField

User = get_user_model()


class Profile(TimeStampedModel):
    class Gender(models.TextChoices):
        MALE = ("male", _("Male"))
        FEMALE = ("female", _("Female"))

    user = models.OneToOneField(
        User, verbose_name=_("User"), on_delete=models.CASCADE, related_name="profile"
    )
    gender = models.CharField(
        _("Gender"), max_length=6, choices=Gender.choices, default=Gender.MALE
    )
    birth_date = models.DateField(_("Birth Date"), null=True, blank=True)
    phone_number = PhoneNumberField(_("Phone Number"), blank=True, default="")
    avatar = CloudinaryField(
        folder="profile_documents/avatar/",
        null=True,
        blank=True,
        verbose_name=_("Avatar"),
    )
    id_face = CloudinaryField(
        folder="profile_documents/id_face/",
        null=True,
        blank=True,
        verbose_name=_("ID Face"),
    )
    id_back = CloudinaryField(
        folder="profile_documents/id_back/",
        null=True,
        blank=True,
        verbose_name=_("ID Back"),
    )
    confirmation_selfi = CloudinaryField(
        folder="profile_documents/selfie/",
        null=True,
        blank=True,
        verbose_name=_("Confirmation Selfie"),
    )
    national_id = models.CharField(
        _("National ID"), max_length=50, blank=True, default=""
    )

    def __str__(self):
        return f"{self.user.email} profile"


class UserSettings(TimeStampedModel):
    user = models.OneToOneField(
        User,
        verbose_name=_("User"),
        on_delete=models.CASCADE,
        related_name="settings",
    )

    # * Notification Settings ("الإشعارات")
    visit_notifications = models.BooleanField(
        _("Visit Notifications"),
        default=True,
        help_text=_("Notifications for property visits"),
    )
    new_properties_in_area = models.BooleanField(
        _("New Properties in Area"),
        default=True,
        help_text=_("Alerts for new properties in user's area"),
    )
    owner_messages = models.BooleanField(
        _("Owner Messages"),
        default=True,
        help_text=_("Notifications for messages from property owners"),
    )
    property_updates = models.BooleanField(
        _("Property Updates"),
        default=False,
        help_text=_("Notifications for property price and status updates"),
    )
    security_alerts = models.BooleanField(
        _("Security Alerts"),
        default=True,
        help_text=_("Alerts for new logins and password changes"),
    )
    promotions_and_updates = models.BooleanField(
        _("Updates and Offers"),
        default=False,
        help_text=_("Marketing promotions, news, and special offers"),
    )

    # * Privacy Settings ("الخصوصية")
    always_hide_mobile_number = models.BooleanField(
        _("Always Hide Mobile Number"),
        default=True,
        help_text=_("Always hide mobile number for privacy protection (fixed)"),
    )
    share_location_for_search = models.BooleanField(
        _("Share My Location for Search"),
        default=True,
        help_text=_("Allow location access for search optimization"),
    )
    show_profile_in_search = models.BooleanField(
        _("Appear in Search"),
        default=False,
        help_text=_("Allow account to appear in search results"),
    )

    class Meta:
        verbose_name = _("User Settings")
        verbose_name_plural = _("User Settings")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Settings for {self.user.email}"

