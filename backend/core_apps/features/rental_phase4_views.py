"""Stable public imports for rental phase4 views.

Implementation modules separate domain responsibilities without changing routes.
"""

import hashlib
import uuid
from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    parser_classes,
    permission_classes,
    renderer_classes,
)
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.admin_api.models import StaffProfile
from .models import (
    Lease,
    DepositAgreement,
    OwnerPayable,
    OwnerPaymentProfile,
    PaymentAttempt,
    PayoutAuditEvent,
    PayoutBatch,
    RentalEvidence,
    RentalHandover,
    RentalPayout,
)
from .providers import get_rental_provider, require_rental_provider
from .renderers import FeatureJsonRenderer
from .services.lease_permissions import handover_actions
from .services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from .services.rental_phase3 import post_ledger_transaction

from .rental_phase4_views_parts.handover_payload import (
    PNG_MAGIC,
    MAX_EVIDENCE_BYTES,
    _money,
    _lease,
    evidence_payload,
    handover_payload,
    _handover,
    _validate_evidence,
)
from .rental_phase4_views_parts.rental_evidence_upload import (
    rental_evidence_upload,
    _evidence,
    rental_evidence_detail,
    rental_evidence_download,
    rental_evidence_content,
)
from .rental_phase4_views_parts.lease_handovers import (
    lease_handovers,
    handover_detail,
    deposit_payload,
)
from .rental_phase4_views_parts.handover_respond import (
    lease_deposit,
    evaluate_owner_payables,
    handover_respond,
    payout_payload,
)
from .rental_phase4_views_parts.operations_execute_payout import (
    payouts,
    payout_detail,
    _require_payout_role,
    operations_execute_payout,
)
from .rental_phase4_views_parts.operations_reconcile_payout import (
    operations_reconcile_payout,
)
from .rental_phase4_views_parts.payout_review import (
    payout_review, payout_preview, reauthorize_payout, payout_queue, payable_queue, retry_failed_payout,
)
