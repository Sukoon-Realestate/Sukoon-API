from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from core_apps.common.models import TimeStampedModel

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
    id_face = models.ImageField(
        _("ID Face"), upload_to="profile_documents/id_face/", null=True, blank=True
    )
    id_back = models.ImageField(
        _("ID Back"), upload_to="profile_documents/id_back/", null=True, blank=True
    )
    confirmation_selfi = models.ImageField(
        _("Confirmation Selfie"),
        upload_to="profile_documents/selfie/",
        null=True,
        blank=True,
    )
    national_id = models.CharField(
        _("National ID"), max_length=50, blank=True, default=""
    )

    def __str__(self):
        return f"{self.user.email} profile"
