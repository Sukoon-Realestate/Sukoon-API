"""Planning discovery views: tenant assistant turns."""

from datetime import timedelta
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from core_apps.properties.models import City
from ..planning_models import TenantAssistantTurn
from ..services.planning_providers import (
    mock_discovery,
    extract_criteria,
    provider_budget,
)
from ..services.commands import command_identity
from ..services.rental_phase2 import replay_operation, fingerprint
from ..services.planning import mutate, planning_api, text_field
from ..services.rental_phase2 import RentalConflict
from .catalog_matches import catalog_matches


from .assistant_context import assistant_context
from .assistant_grounding import assistant_filters, assistant_matches
from .assistant_reply import assistant_reply


@planning_api(["POST"], "tenant_assistant")
def tenant_assistant_turns(request):
    key, _ = command_identity(request.data)
    replay = replay_operation(request.user, "assistant.turn", key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    text = text_field(request.data, "text", required=True, limit=4000)
    language = request.data.get("language")
    if language not in {"ar", "en"} or request.data.get("retain_history") is not False:
        raise ValidationError("Use language ar/en and retain_history=false.")
    session_id = text_field(request.data, "session_id", required=True, limit=100)
    context, comparison_ids, selected_properties = assistant_context(
        request, session_id
    )
    extracted = None
    lock_key = None
    if not mock_discovery():
        lock_key = "planning-assistant:" + fingerprint(
            {"user": str(request.user.id), "key": key}
        )
        if not cache.add(lock_key, True, timeout=90):
            raise RentalConflict(
                "This assistant request is already processing.",
                code="operation_in_progress",
            )
        try:
            provider_budget(request.user, "assistant")
            catalog = {
                "cities": [
                    {"id": str(x.id), "name": x.name}
                    for x in City.objects.filter(
                        is_active=True, governorate__is_active=True
                    ).order_by("pkid")
                ],
                "amenities": [
                    "wifi",
                    "elevator",
                    "garage",
                    "security",
                    "balcony",
                    "air_conditioning",
                    "near_metro",
                    "natural_gas",
                    "electricity_meter",
                    "water_meter",
                ],
            }
            extracted = extract_criteria(
                text, language, catalog, {"filters": context.get("filters", {})}
            )
            # Reject unsupported typed operators and invalid prices before using model output.
            next(
                catalog_matches({**context.get("filters", {}), **extracted["filters"]}),
                None,
            )
        except Exception:
            cache.delete(lock_key)
            raise

    def apply(_, revision):
        text = text_field(request.data, "text", required=True, limit=4000)
        session_id = text_field(request.data, "session_id", required=True, limit=100)
        language = request.data.get("language")
        if (
            language not in {"ar", "en"}
            or request.data.get("retain_history") is not False
        ):
            raise ValidationError("Use language ar/en and retain_history=false.")
        previous = None
        if request.data.get("previous_turn_id"):
            previous = get_object_or_404(
                TenantAssistantTurn,
                id=request.data["previous_turn_id"],
                user=request.user,
                session_id=session_id,
                expires_at__gt=timezone.now(),
            )
        filters, unresolved = assistant_filters(text, language, context, extracted)
        matches = assistant_matches(
            filters, selected_properties, context, comparison_ids
        )
        reply = assistant_reply(
            matches, context, filters, unresolved, extracted, language
        )
        # Keep no raw prompt; a short-lived reply supports same-key recovery.
        return TenantAssistantTurn.objects.create(
            user=request.user,
            session_id=session_id,
            previous_turn=previous,
            reply=reply,
            expires_at=timezone.now() + timedelta(hours=24),
        )

    try:
        return mutate(
            request,
            "assistant.turn",
            lambda: None,
            apply,
            lambda x: {"id": str(x.id), "revision": x.revision, **x.reply},
            creating=True,
        )
    finally:
        if lock_key:
            cache.delete(lock_key)
