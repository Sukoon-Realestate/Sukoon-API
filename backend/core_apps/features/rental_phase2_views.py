"""Stable public imports for rental phase2 views.

Implementation modules separate domain responsibilities without changing routes.
"""

import copy
import json
from datetime import timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.conf import settings
from django.db import models, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from core_apps.properties.models import Property
from core_apps.notifications.models import Notification
from core_apps.notifications.services.notification_service import NotificationService
from .models import (
    IdempotencyRecord,
    Lease,
    OwnerOnboardingSession,
    OwnerPaymentProfile,
    RentalInterest,
    RentalInventoryDayLock,
    RentalTimelineEvent,
    SigningSession,
    TenancyInvitation,
    TermsProposal,
)
from .pagination import FeaturePagination
from .providers import (
    mock_completion_metadata,
    fake_provider_available,
    get_rental_provider,
    require_rental_provider,
    verify_fake_webhook,
)
from .renderers import FeatureJsonRenderer
from .rental_serializers import (
    LeasePhase2Serializer,
    OwnerOnboardingBodySerializer,
    OwnerPaymentProfileSerializer,
    RentalAgreementDraftBodySerializer,
    RentalDecisionSerializer,
    RentalInterestBodySerializer,
    RentalInterestSerializer,
    RentalInvitationBodySerializer,
    RentalSigningBodySerializer,
    TermsProposalBodySerializer,
    TermsProposalSerializer,
)
from .serializers import TenancyInvitationSerializer
from .services.lease_permissions import can_revoke_invitation
from .services.rental_phase2 import (
    RentalConflict,
    assert_owner_ready,
    fingerprint,
    get_or_create_owner_profile,
    remember_mutation,
    replay_operation,
    reserve_inventory_days,
    validate_interest_capacity,
)
from .services.tenancy_invitations import (
    create_notification_for_invitation,
    resolve_offer_snapshot,
)

from .rental_phase2_views_parts.owner_payment_profile import (
    _paginate,
    _replay_response,
    _remember_session,
    _participant_interest,
    _participant_proposal,
    _participant_lease,
    _money_minor_from_offer,
    _json_safe,
    _validate_terms_offer,
    _event,
    _notify,
    owner_payment_profile,
)
from .rental_phase2_views_parts.owner_onboarding_session import (
    owner_onboarding_session,
)
from .rental_phase2_views_parts.rental_interests import (
    rental_interests,
    rental_interest_detail,
    rental_interest_respond,
)
from .rental_phase2_views_parts.terms_proposals import (
    terms_proposals,
    terms_proposal_detail,
)
from .rental_phase2_views_parts.create_interest_invitation import (
    terms_proposal_respond,
    create_interest_invitation,
)
from .rental_phase2_views_parts.tenancy_invitation_revoke import (
    tenancy_invitation_revoke,
)
from .rental_phase2_views_parts.create_structured_lease import (
    create_structured_lease,
)
from .rental_phase2_views_parts.update_structured_lease import (
    update_structured_lease,
    lease_review,
)
from .rental_phase2_views_parts.create_structured_signing_session import (
    lease_submit_for_signature,
    create_structured_signing_session,
)
from .rental_phase2_views_parts.lease_billing_schedule import (
    lease_timeline,
    lease_billing_schedule,
)
from .rental_phase2_views_parts.apply_fake_rental_event import (
    apply_fake_rental_event,
    fake_rental_provider_webhook,
)
