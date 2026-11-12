"""Private decision read projection, serialized against the decision commit."""

import uuid
from django.db import transaction
from django.shortcuts import get_object_or_404
from core_apps.features.models import IdempotencyRecord
from ..models import PropertyVisit, PropertyVisitDecision
from ..serializers.visit import (
    TenantVisitRequestDetailSerializer,
    OwnerVisitRequestDetailSerializer,
)
from .post_visit_decision import OPERATION, reason_visible, visit_context, invalid


def decision_context(actor, id, request_key=None, *, context=None):
    with transaction.atomic():
        visit = get_object_or_404(
            PropertyVisit.objects.select_for_update(of=("self",)).select_related(
                "property", "property__owner", "tenant"
            ),
            id=id,
        )
        from .viewing_access import can_read

        participant = can_read(visit, actor)
        if not participant and (not reason_visible(actor, visit)):
            from rest_framework.exceptions import NotFound

            raise NotFound()
        if participant:
            serializer = (
                TenantVisitRequestDetailSerializer
                if actor.pk != visit.property.owner_id
                else OwnerVisitRequestDetailSerializer
            )
            output = serializer(visit, context=context).data
        else:
            output = {"id": str(visit.id), **visit_context(visit, actor)}
            output["rental_continuation"]["next_action"] = None
            for field in ("invitation_id", "agreement_id", "invoice_id"):
                output["rental_continuation"][field] = None
        key = request_key
        if key is not None:
            try:
                key = str(uuid.UUID(key))
            except (ValueError, TypeError, AttributeError):
                invalid("request_key must be a UUID.", "invalid_request_key")
            recorded = (
                IdempotencyRecord.objects.filter(
                    user=actor,
                    operation=OPERATION,
                    request_key=key,
                    request_subject_id=visit.id,
                ).exists()
                or PropertyVisitDecision.objects.filter(
                    visit=visit, tenant=actor, request_key=key
                ).exists()
            )
            output["operation"] = {
                "request_key": key,
                "status": "recorded" if recorded else "absent",
            }
        return output
