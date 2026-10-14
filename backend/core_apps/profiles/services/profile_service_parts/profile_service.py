"""Profile service: profile service."""

from typing import Any, Dict, Optional
from django.db import transaction
from core_apps.profiles.models import Contract, Profile, UserSettings
from .arabic_months import ARABIC_MONTHS, format_arabic_month_year, format_arabic_count


from .profile_service_operations.profile_account import ProfileAccountMixin
from .profile_service_operations.profile_status import ProfileStatusMixin
from .profile_service_operations.profile_edit import ProfileEditMixin
from .profile_service_operations.profile_unread import ProfileUnreadMixin


class ProfileService(
    ProfileAccountMixin, ProfileStatusMixin, ProfileEditMixin, ProfileUnreadMixin
):
    """Public service dispatch with domain-specific responsibilities."""

    """
    Service layer for tenant profile, mobile account screens, and data aggregation.
    """
