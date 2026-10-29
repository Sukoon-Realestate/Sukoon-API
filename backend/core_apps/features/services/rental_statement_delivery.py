"""Drain only durable statement requests, without financial or provider work."""

import logging
from django.db import transaction
from django.utils import timezone
from ..models import RentalDocument
from .private_rental_documents import generate

logger = logging.getLogger(__name__)
MAX_BATCH = 5


def generate_requested(*, limit=1):
    if type(limit) is not int or not 1 <= limit <= MAX_BATCH:
        raise ValueError("Statement batch limit must be between 1 and 5.")
    counts = {"selected": 0, "generated": 0, "retry_pending": 0}
    seen = []
    for _ in range(limit):
        with transaction.atomic():
            document = (
                RentalDocument.objects.filter(
                    document_type=RentalDocument.DocumentType.STATEMENT,
                    status=RentalDocument.Status.QUEUED,
                    generation_requested_at__isnull=False,
                )
                .exclude(pk__in=seen)
                .select_related("lease")
                .select_for_update(skip_locked=True, of=("self",))
                .order_by("updated_at", "pk")
                .first()
            )
            if document is None:
                break
            seen.append(document.pk)
            counts["selected"] += 1
            try:
                # Preserve the claim lock while rolling back partial generation.
                with transaction.atomic():
                    if not generate(document):
                        raise RuntimeError("Statement generation did not complete.")
            except Exception as error:
                # Fixed metadata only; no actor, ledger, document bytes or errors.
                RentalDocument.objects.filter(pk=document.pk).update(
                    failure_code="statement_generation_retry_pending",
                    updated_at=timezone.now(),
                )
                logger.warning("Statement generation deferred (%s)", type(error).__name__)
                counts["retry_pending"] += 1
            else:
                counts["generated"] += 1
    return counts
