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

    def __str__(self):
        return f"{self.user.email} profile"
