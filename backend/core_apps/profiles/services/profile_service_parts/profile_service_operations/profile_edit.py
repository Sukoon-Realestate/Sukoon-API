"""ProfileEdit operations owned by ProfileService."""

from typing import Any, Dict
from django.db import transaction
from core_apps.profiles.models import Profile, UserSettings


class ProfileEditMixin:
    @classmethod
    @transaction.atomic
    def update_user_profile(cls, user: Any, validated_data: Dict[str, Any]) -> Profile:
        """
        Updates user and profile fields atomically for Screen 3: 'تعديل الملف'.
        """
        profile, _ = Profile.objects.get_or_create(user=user)

        from rest_framework.exceptions import PermissionDenied

        if {
            "id_face",
            "id_back",
            "confirmation_selfi",
            "national_id",
        } & validated_data.keys():
            raise PermissionDenied(
                "Identity evidence must be submitted through the versioned identity-review flow."
            )

        nested = validated_data.get("user", {})
        new_email = (
            nested.get("email", validated_data.get("email"))
            if isinstance(nested, dict)
            else None
        )
        if (new_email and new_email.casefold() != user.email.casefold()) or (
            "phone_number" in validated_data
            and str(validated_data["phone_number"]) != str(profile.phone_number)
        ):
            raise PermissionDenied(
                "Changing a contact requires approved re-verification and proof of the new contact; the verification provider is not configured."
            )
        user_fields_to_update = []

        # * Handle full_name or first_name / last_name
        if "full_name" in validated_data:
            full_name = validated_data.pop("full_name", "").strip()
            parts = full_name.split(maxsplit=1)
            user.first_name = parts[0] if parts else ""
            user.last_name = parts[1] if len(parts) > 1 else ""
            user_fields_to_update.extend(["first_name", "last_name"])

        # * Handle nested user dictionary from serializer source='user.*'
        user_data = validated_data.pop("user", {})
        if isinstance(user_data, dict):
            if "first_name" in user_data:
                user.first_name = user_data["first_name"]
                if "first_name" not in user_fields_to_update:
                    user_fields_to_update.append("first_name")
            if "last_name" in user_data:
                user.last_name = user_data["last_name"]
                if "last_name" not in user_fields_to_update:
                    user_fields_to_update.append("last_name")
            if "email" in user_data:
                new_email = user_data["email"]
                if new_email and new_email != user.email:
                    user.email = new_email
                    user_fields_to_update.append("email")

        if "first_name" in validated_data:
            user.first_name = validated_data.pop("first_name")
            if "first_name" not in user_fields_to_update:
                user_fields_to_update.append("first_name")

        if "last_name" in validated_data:
            user.last_name = validated_data.pop("last_name")
            if "last_name" not in user_fields_to_update:
                user_fields_to_update.append("last_name")

        if "email" in validated_data:
            new_email = validated_data.pop("email")
            if new_email and new_email != user.email:
                user.email = new_email
                user_fields_to_update.append("email")

        if user_fields_to_update:
            user.save(update_fields=list(set(user_fields_to_update)))

        # * Update profile fields (including avatar)
        for field, value in validated_data.items():
            if hasattr(profile, field):
                setattr(profile, field, value)

        profile.save()
        return profile

    @classmethod
    def get_user_settings(cls, user: Any) -> UserSettings:
        """
        Retrieves or initializes settings for the given user.
        """
        settings_obj, _ = UserSettings.objects.get_or_create(user=user)
        return settings_obj

    @classmethod
    @transaction.atomic
    def update_user_settings(
        cls, user: Any, validated_data: Dict[str, Any]
    ) -> UserSettings:
        """
        Updates settings for the given user within an atomic transaction.
        Enforces privacy constraints (e.g. always_hide_mobile_number cannot be disabled).
        """
        settings_obj, _ = UserSettings.objects.get_or_create(user=user)

        settings_obj = UserSettings.objects.select_for_update().get(pk=settings_obj.pk)
        from core_apps.profiles.models import NotificationPreferenceChange

        preference_fields = (
            "visit_notifications",
            "new_properties_in_area",
            "owner_messages",
            "property_updates",
            "security_alerts",
            "promotions_and_updates",
        )
        before = {key: getattr(settings_obj, key) for key in preference_fields}
        # ! Enforce privacy rule: always_hide_mobile_number cannot be turned off
        validated_data.pop("always_hide_mobile_number", None)

        for field, value in validated_data.items():
            if hasattr(settings_obj, field):
                setattr(settings_obj, field, value)

        after = {key: getattr(settings_obj, key) for key in preference_fields}
        if before != after:
            settings_obj.revision += 1
            NotificationPreferenceChange.objects.create(
                user=user,
                revision=settings_obj.revision,
                previous=before,
                current=after,
            )
        settings_obj.save()
        return settings_obj
