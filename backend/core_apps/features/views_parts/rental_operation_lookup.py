"""Views: rental operation lookup."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import IdempotencyRecord
from ..pagination import FeaturePagination
from ..renderers import FeatureJsonRenderer
from ..services.rental_foundation import (
    capabilities_for,
    get_authorized_rental_subject,
    private_no_store,
)


User = get_user_model()


FEATURE_DECORATORS = [api_view]


LEASE_TEMPLATES = [
    {
        "id": "eg-residential-v1",
        "title": "Residential lease",
        "jurisdiction": "EG",
        "language": "ar",
        "version": "1",
    }
]


from ..services.operation_receipts import Conflict as Conflict


from ..services.operation_receipts import _fingerprint as _fingerprint


def _replay(user, operation, request_key, payload):
    from ..services.operation_receipts import _replay as replay

    result = replay(user, operation, request_key, payload)
    return Response(result.data, status=result.status) if result else None


from ..services.operation_receipts import _remember as _remember


class RentalCapabilitiesView(FeatureAPIView):
    name = "Rental Capabilities"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "rental_operation_lookup",
            "rental_capabilities",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        subject_id = request.query_params.get("subject_id")
        if not subject_id:
            raise ValidationError({"subject_id": "This query parameter is required."})
        subject = get_authorized_rental_subject(request.user, subject_id)
        response = Response(
            capabilities_for(
                request.user,
                subject,
                request.query_params.get("action", ""),
            )
        )
        return private_no_store(response)


# Stable callable import for integrations; URLs use the explicit class.
rental_capabilities = RentalCapabilitiesView.as_view()


class RentalOperationLookupView(FeatureAPIView):
    name = "Rental Operation Lookup"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "rental_operation_lookup",
            "rental_operation_lookup",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, request_key):
        subject_id = request.query_params.get("subject_id")
        if not subject_id:
            raise ValidationError({"subject_id": "This query parameter is required."})
        operation = IdempotencyRecord.objects.filter(
            user=request.user,
            request_key=str(request_key),
            request_subject_id=subject_id,
            is_rental_operation=True,
        ).first()
        departure_receipt = bool(
            operation
            and operation.operation == f"group.leave.{subject_id}"
            and str(operation.result_subject_id) == str(subject_id)
        )
        from ..services.company.responsibility_management import recovery_subject

        administrative_subject = recovery_subject(request.user, subject_id, operation)
        if not departure_receipt and administrative_subject is None:
            get_authorized_rental_subject(request.user, subject_id)
        if operation:
            if administrative_subject is not None:
                if str(operation.result_subject_id) != str(administrative_subject.id):
                    raise NotFound()
            elif not departure_receipt:
                get_authorized_rental_subject(request.user, operation.result_subject_id)
            receipt = {
                "id": str(operation.id),
                "subject_id": str(operation.result_subject_id),
                "request_key": operation.request_key,
                "revision": operation.result_revision,
                "status": operation.recovery_status,
            }
            lookup_status = operation.recovery_status
        else:
            # Database absence alone is not a permanent tombstone.
            receipt = None
            lookup_status = IdempotencyRecord.RecoveryStatus.UNKNOWN
        response = Response(
            {
                "request_key": str(request_key),
                "request_subject_id": str(subject_id),
                "status": lookup_status,
                "operation_receipt": receipt,
            }
        )
        return private_no_store(response)


# Stable callable import for integrations; URLs use the explicit class.
rental_operation_lookup = RentalOperationLookupView.as_view()


def _paginate(request, queryset, serializer_class):
    paginator = FeaturePagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = serializer_class(page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)


__all__ = [
    "Conflict",
    "FEATURE_DECORATORS",
    "LEASE_TEMPLATES",
    "RentalCapabilitiesView",
    "RentalOperationLookupView",
    "User",
    "_fingerprint",
    "_paginate",
    "_remember",
    "_replay",
    "rental_capabilities",
    "rental_operation_lookup",
]
