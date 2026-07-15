from typing import Optional

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _


def validate_email_address(email: str):
    try:
        validate_email(email)
    except ValidationError:
        raise ValidationError(_("Enter a valid email address"))


class UserManager(BaseUserManager):
    def _create_user(self, email: str, password: Optional[str], **extra_fields):
        if not email:
            raise ValidationError(_("An email is required."))
        email = self.normalize_email(email)
        validate_email_address(email)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: Optional[str] = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: Optional[str] = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValidationError("A superuser must be a staff")
        if extra_fields.get("is_superuser") is not True:
            raise ValidationError("A superuser must be a superuser")

        return self._create_user(email, password, **extra_fields)
