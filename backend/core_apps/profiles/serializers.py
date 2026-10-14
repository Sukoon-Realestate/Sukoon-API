"""Stable public imports for serializers.

Implementation modules separate domain responsibilities without changing routes.
"""

import base64
import uuid
from typing import Optional
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from .models import Contract, Profile, UserSettings
from core_apps.users.journey import PrivateJourneySerializerMixin
from .services.profile_service import (
    ARABIC_MONTHS,
    format_arabic_date,
    mask_phone_number,
)

from .serializers_parts.update_profile_serializer import (
    CloudinarySerializerField,
    ProfileCitySerializer,
    ProfileSerializer,
    UpdateProfileSerializer,
    MyAccountUserSerializer,
    MyAccountStatsSerializer,
    MyAccountDetailsSerializer,
    MyAccountScreenSerializer,
    AccountSummaryUserSerializer,
    IdentityVerificationSerializer,
    AccountSummaryStatsSerializer,
)
from .serializers_parts.profile_edit_serializer import (
    AccountSummaryScreenSerializer,
    ProfileEditSerializer,
)
from .serializers_parts.user_settings_serializer import (
    UserSettingsSerializer,
    OwnerUnreadCountsSerializer,
    TenantUnreadCountsSerializer,
)
from .serializers_parts.tenant_my_rate_serializer import (
    TenantMyRateSerializer,
    VerificationStatusSerializer,
    TenantContractSerializer,
)
