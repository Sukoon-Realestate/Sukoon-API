"""Stable public imports for rental phase4 views.

Implementation modules separate domain responsibilities without changing routes.
"""

from datetime import timedelta as timedelta
from django.db import transaction as transaction
from django.shortcuts import get_object_or_404 as get_object_or_404
from django.utils import timezone as timezone
from rest_framework import status as status
from rest_framework.decorators import (
    api_view as api_view,
    parser_classes as parser_classes,
    permission_classes as permission_classes,
    renderer_classes as renderer_classes,
)
from rest_framework.exceptions import (
    NotFound as NotFound,
    PermissionDenied as PermissionDenied,
    ValidationError as ValidationError,
)
from rest_framework.parsers import (
    FormParser as FormParser,
    JSONParser as JSONParser,
    MultiPartParser as MultiPartParser,
)
from rest_framework.permissions import IsAuthenticated as IsAuthenticated
from rest_framework.response import Response as Response
from core_apps.admin_api.models import StaffProfile as StaffProfile
from .models import (
    Lease as Lease,
    DepositAgreement as DepositAgreement,
    OwnerPayable as OwnerPayable,
    OwnerPaymentProfile as OwnerPaymentProfile,
    PaymentAttempt as PaymentAttempt,
    PayoutAuditEvent as PayoutAuditEvent,
    PayoutBatch as PayoutBatch,
    RentalEvidence as RentalEvidence,
    RentalHandover as RentalHandover,
    RentalPayout as RentalPayout,
)
from .providers import (
    get_rental_provider as get_rental_provider,
    require_rental_provider as require_rental_provider,
)
from .renderers import FeatureJsonRenderer as FeatureJsonRenderer
from .services.lease_permissions import handover_actions as handover_actions
from .services.rental_phase2 import (
    RentalConflict as RentalConflict,
    remember_mutation as remember_mutation,
    replay_operation as replay_operation,
)
from .services.rental_phase3 import post_ledger_transaction as post_ledger_transaction

from .rental_phase4_views_parts.handover_payload import (
    PNG_MAGIC as PNG_MAGIC,
    MAX_EVIDENCE_BYTES as MAX_EVIDENCE_BYTES,
    _money as _money,
    _lease as _lease,
    evidence_payload as evidence_payload,
    handover_payload as handover_payload,
    _handover as _handover,
    _validate_evidence as _validate_evidence,
)
from .rental_phase4_views_parts.rental_evidence_upload import (
    rental_evidence_upload as rental_evidence_upload,
    _evidence as _evidence,
    rental_evidence_detail as rental_evidence_detail,
    rental_evidence_download as rental_evidence_download,
    rental_evidence_content as rental_evidence_content,
    RentalEvidenceContentView as RentalEvidenceContentView,
    RentalEvidenceDetailView as RentalEvidenceDetailView,
    RentalEvidenceDownloadView as RentalEvidenceDownloadView,
    RentalEvidenceUploadView as RentalEvidenceUploadView,
)
from .rental_phase4_views_parts.lease_handovers import (
    lease_handovers as lease_handovers,
    handover_detail as handover_detail,
    deposit_payload as deposit_payload,
    HandoverDetailView as HandoverDetailView,
    LeaseHandoversView as LeaseHandoversView,
)
from .rental_phase4_views_parts.handover_respond import (
    lease_deposit as lease_deposit,
    evaluate_owner_payables as evaluate_owner_payables,
    handover_respond as handover_respond,
    payout_payload as payout_payload,
    HandoverRespondView as HandoverRespondView,
    LeaseDepositView as LeaseDepositView,
)
from .rental_phase4_views_parts.operations_execute_payout import (
    payouts as payouts,
    payout_detail as payout_detail,
    _require_payout_role as _require_payout_role,
    operations_execute_payout as operations_execute_payout,
    OperationsExecutePayoutView as OperationsExecutePayoutView,
    PayoutDetailView as PayoutDetailView,
    PayoutsView as PayoutsView,
)
from .rental_phase4_views_parts.operations_reconcile_payout import (
    operations_reconcile_payout as operations_reconcile_payout,
    OperationsReconcilePayoutView as OperationsReconcilePayoutView,
)
from .rental_phase4_views_parts.payout_review import (
    payout_review as payout_review,
    payout_preview as payout_preview,
    reauthorize_payout as reauthorize_payout,
    payout_queue as payout_queue,
    payable_queue as payable_queue,
    retry_failed_payout as retry_failed_payout,
    PayableQueueView as PayableQueueView,
    PayoutPreviewView as PayoutPreviewView,
    PayoutQueueView as PayoutQueueView,
    PayoutReviewView as PayoutReviewView,
    ReauthorizePayoutView as ReauthorizePayoutView,
    RetryFailedPayoutView as RetryFailedPayoutView,
)

__all__ = [
    "DepositAgreement",
    "FeatureJsonRenderer",
    "FormParser",
    "HandoverDetailView",
    "HandoverRespondView",
    "IsAuthenticated",
    "JSONParser",
    "Lease",
    "LeaseDepositView",
    "LeaseHandoversView",
    "MAX_EVIDENCE_BYTES",
    "MultiPartParser",
    "NotFound",
    "OperationsExecutePayoutView",
    "OperationsReconcilePayoutView",
    "OwnerPayable",
    "OwnerPaymentProfile",
    "PNG_MAGIC",
    "PayableQueueView",
    "PaymentAttempt",
    "PayoutAuditEvent",
    "PayoutBatch",
    "PayoutDetailView",
    "PayoutPreviewView",
    "PayoutQueueView",
    "PayoutReviewView",
    "PayoutsView",
    "PermissionDenied",
    "ReauthorizePayoutView",
    "RentalConflict",
    "RentalEvidence",
    "RentalEvidenceContentView",
    "RentalEvidenceDetailView",
    "RentalEvidenceDownloadView",
    "RentalEvidenceUploadView",
    "RentalHandover",
    "RentalPayout",
    "Response",
    "RetryFailedPayoutView",
    "StaffProfile",
    "ValidationError",
    "_evidence",
    "_handover",
    "_lease",
    "_money",
    "_require_payout_role",
    "_validate_evidence",
    "api_view",
    "deposit_payload",
    "evaluate_owner_payables",
    "evidence_payload",
    "get_object_or_404",
    "get_rental_provider",
    "handover_actions",
    "handover_detail",
    "handover_payload",
    "handover_respond",
    "lease_deposit",
    "lease_handovers",
    "operations_execute_payout",
    "operations_reconcile_payout",
    "parser_classes",
    "payable_queue",
    "payout_detail",
    "payout_payload",
    "payout_preview",
    "payout_queue",
    "payout_review",
    "payouts",
    "permission_classes",
    "post_ledger_transaction",
    "reauthorize_payout",
    "remember_mutation",
    "renderer_classes",
    "rental_evidence_content",
    "rental_evidence_detail",
    "rental_evidence_download",
    "rental_evidence_upload",
    "replay_operation",
    "require_rental_provider",
    "retry_failed_payout",
    "status",
    "timedelta",
    "timezone",
    "transaction",
]
