"""Stable public imports for settlements.

Implementation modules separate domain responsibilities without changing routes.
"""

import uuid
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ..models import (
    DepositAgreement,
    FinalSettlement,
    InvoiceLine,
    Lease,
    OwnerPayable,
    PaymentAttempt,
    RefundRequest,
    RentInvoice,
)
from .rental_phase2 import RentalConflict, fingerprint
from .rental_phase3 import invoice_balance_minor, post_ledger_transaction
from .refunds import remaining_components

from .settlements_parts.financial_snapshot import (
    CHARGE_TYPES,
    LINE_TYPES,
    financial_snapshot,
)
from .settlements_parts.prepare_settlement import (
    prepare_settlement,
)
# Supported private imports stay outside the public star-import surface.
from .settlements_parts.apply_credit import (  # noqa: F401
    _apply_credit,
)
from .settlements_parts.execute_settlement import (
    execute_settlement,
)

# Preserve the existing public import surface, including compatibility seams.
__all__ = [
    'uuid',
    'transaction',
    'timezone',
    'ValidationError',
    'DepositAgreement',
    'FinalSettlement',
    'InvoiceLine',
    'Lease',
    'OwnerPayable',
    'PaymentAttempt',
    'RefundRequest',
    'RentInvoice',
    'RentalConflict',
    'fingerprint',
    'invoice_balance_minor',
    'post_ledger_transaction',
    'remaining_components',
    'CHARGE_TYPES',
    'LINE_TYPES',
    'financial_snapshot',
    'prepare_settlement',
    'execute_settlement',
]
