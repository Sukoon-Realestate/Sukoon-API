"""Rental phase2 views: lease billing schedule."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from core_apps.common.locale_middleware import resolve_request_language

from rest_framework.permissions import IsAuthenticated
from ..pagination import FeaturePagination
from ..renderers import FeatureJsonRenderer
from ..services.rental_notes import response_note_label
from .owner_payment_profile import _participant_lease


class LeaseTimelineView(FeatureAPIView):
    name = "Lease Timeline"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "lease_billing_schedule",
            "lease_timeline",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, lease_id):
        lease = _participant_lease(request, lease_id)
        paginator = FeaturePagination()
        page = paginator.paginate_queryset(lease.timeline_events.all(), request)
        return paginator.get_paginated_response(
            [
                {
                    "id": str(item.id),
                    "label": response_note_label(
                        item, resolve_request_language(request)
                    ),
                    "description": item.description,
                    "occurred_at": item.occurred_at.isoformat(),
                    "kind": item.kind,
                    "resource_id": str(item.resource_id) if item.resource_id else None,
                }
                for item in page
            ]
        )


# Stable callable import for integrations; URLs use the explicit class.
lease_timeline = LeaseTimelineView.as_view()


class LeaseBillingScheduleView(FeatureAPIView):
    name = "Lease Billing Schedule"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "lease_billing_schedule",
            "lease_billing_schedule",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, lease_id):
        lease = _participant_lease(request, lease_id)
        paginator = FeaturePagination()
        page = paginator.paginate_queryset(
            lease.billing_periods.select_related("invoice").all(), request
        )
        return paginator.get_paginated_response(
            [
                {
                    "id": str(period.id),
                    "sequence": period.sequence,
                    "starts_on": str(period.start),
                    "ends_on_exclusive": str(period.end_exclusive),
                    "issue_at": period.issue_at.isoformat(),
                    "due_at": period.due_at.isoformat(),
                    "amount": {
                        "amount_minor": period.amount_minor,
                        "currency": period.currency,
                        "exponent": period.exponent,
                    },
                    "status": period.status,
                    "invoice_id": (
                        str(period.invoice.id) if hasattr(period, "invoice") else None
                    ),
                }
                for period in page
            ]
        )


# Stable callable import for integrations; URLs use the explicit class.
lease_billing_schedule = LeaseBillingScheduleView.as_view()
