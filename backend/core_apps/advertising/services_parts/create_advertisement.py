"""Services: create advertisement."""

import json
from datetime import timezone as datetime_timezone
from django.db import IntegrityError, transaction
from ..models import (
    Advertisement,
    AdvertisementMedia,
    AdvertisementOperation,
    AdvertisingPlan,
)
from .validate_banner import (
    CAIRO,
    AdvertisingServiceError,
    plan_payload,
    validate_banner,
    validate_destination,
    payload_fingerprint,
)


def create_advertisement(owner, attrs, language):
    raw, banner_sha256, content_type = validate_banner(attrs["banner"])
    fingerprint = payload_fingerprint(attrs, banner_sha256)
    operation_id = attrs["operation_id"]

    saved_media = None
    try:
        with transaction.atomic():
            operation = (
                AdvertisementOperation.objects.select_for_update()
                .filter(owner=owner, operation_id=operation_id)
                .first()
            )
            if operation:
                if operation.state == AdvertisementOperation.State.FOUND:
                    if operation.payload_fingerprint != fingerprint:
                        raise AdvertisingServiceError(
                            "This operation ID was already used with different data.",
                            status_code=409,
                            errors={"operation_id": ["idempotency_conflict"]},
                        )
                    return operation.advertisement, False
                if operation.state == AdvertisementOperation.State.PROCESSING:
                    raise AdvertisingServiceError(
                        "This operation is still processing.",
                        status_code=409,
                        errors={"operation_id": ["operation_processing"]},
                    )
                operation.payload_fingerprint = fingerprint
                operation.state = AdvertisementOperation.State.PROCESSING
                operation.retry_allowed = False
                operation.rejection_errors = None
                operation.save()
            else:
                try:
                    operation = AdvertisementOperation.objects.create(
                        owner=owner,
                        operation_id=operation_id,
                        state=AdvertisementOperation.State.PROCESSING,
                        payload_fingerprint=fingerprint,
                    )
                except IntegrityError:
                    raise AdvertisingServiceError(
                        "This operation is already being processed.",
                        status_code=409,
                        errors={"operation_id": ["operation_processing"]},
                    )

            plan = (
                AdvertisingPlan.objects.select_for_update()
                .filter(id=attrs["plan_id"], active=True)
                .first()
            )
            if not plan:
                raise AdvertisingServiceError(
                    "The selected plan is unavailable.",
                    errors={"plan_id": ["not_available"]},
                )
            if plan.revision != attrs["plan_revision"]:
                raise AdvertisingServiceError(
                    "The selected plan changed. Review the current plan before continuing.",
                    status_code=409,
                    errors={"plan_revision": ["plan_changed"]},
                )
            property_obj = validate_destination(
                owner, attrs.get("property_id"), attrs.get("offer_id", "")
            )
            snapshot = plan_payload(plan, language)
            advertisement = Advertisement.objects.create(
                owner=owner,
                operation=operation,
                title=attrs["title"],
                description=attrs.get("description", ""),
                property=property_obj,
                offer_id=attrs.get("offer_id", ""),
                plan_snapshot=snapshot,
            )
            upload = attrs["banner"]
            upload.seek(0)
            saved_media = AdvertisementMedia.objects.create(
                advertisement=advertisement,
                banner=upload,
                sha256=banner_sha256,
                content_type=content_type,
                size_bytes=len(raw),
            )
            operation.state = AdvertisementOperation.State.FOUND
            operation.save(update_fields=["state", "updated_at"])
            return advertisement, True
    except Exception:
        if saved_media and saved_media.banner.name:
            try:
                saved_media.banner.storage.delete(saved_media.banner.name)
            except Exception:
                pass
        raise


def record_rejected_operation(owner, operation_id, errors):
    if not operation_id or len(str(operation_id)) > 128:
        return
    serializable_errors = (
        json.loads(json.dumps(errors, default=str)) if errors else None
    )
    with transaction.atomic():
        operation = (
            AdvertisementOperation.objects.select_for_update()
            .filter(owner=owner, operation_id=operation_id)
            .first()
        )
        if operation and operation.state in {
            AdvertisementOperation.State.FOUND,
            AdvertisementOperation.State.PROCESSING,
        }:
            return
        if operation:
            operation.retry_allowed = True
            operation.rejection_errors = serializable_errors
            operation.save(
                update_fields=["retry_allowed", "rejection_errors", "updated_at"]
            )
        else:
            try:
                with transaction.atomic():
                    AdvertisementOperation.objects.create(
                        owner=owner,
                        operation_id=operation_id,
                        state=AdvertisementOperation.State.REJECTED,
                        retry_allowed=True,
                        rejection_errors=serializable_errors,
                    )
            except IntegrityError:
                return


def _valid_local_datetime(naive, fold):
    aware = naive.replace(tzinfo=CAIRO, fold=fold)
    round_trip = aware.astimezone(datetime_timezone.utc).astimezone(CAIRO)
    return aware if round_trip.replace(tzinfo=None) == naive else None
