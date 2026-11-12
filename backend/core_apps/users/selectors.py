"""Prepared identity reads; projections do not perform per-row database work."""
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import AccountClosureRequest, AuthSession
from .services import account_closure
from .read_pages import collection_requested, collection_page, history_page


def closure_queue(request):
    account_closure.require_reviewer(request)
    rows = AccountClosureRequest.objects.select_related("user").order_by("created_at")
    if request.query_params.get("history") != "true":
        rows = rows.filter(active=True)
    return rows


def closure_review(request, identity):
    account_closure.require_reviewer(request)
    item = get_object_or_404(
        AccountClosureRequest.objects.select_related("user"), id=identity
    )
    from .services.closure_reads import prepare_projections

    prepare_projections([item], page=history_page(request.query_params))
    return account_closure.projection(item, review=True)


def active_sessions(user, claims, params=None):
    rows = AuthSession.objects.filter(
        user=user, revoked_at__isnull=True, expires_at__gt=timezone.now()
    )
    metadata = {}
    if params is not None and collection_requested(params):
        rows, metadata = collection_page(rows.order_by("-created_at", "-pk"), params)
    return {
        **metadata,
        "sensitive_actions_frozen": user.sensitive_actions_frozen,
        "results": [
            {
                "id": str(item.id),
                "created_at": item.created_at.isoformat(),
                "expires_at": item.expires_at.isoformat(),
                "current": str(item.id) == (claims or {}).get("session_id"),
                "client_platform": item.client_platform or "",
                "device_model": item.device_model or "",
                "os_version": item.os_version or "",
                "app_version": item.app_version or "",
                "last_seen_at": item.last_seen_at.isoformat() if item.last_seen_at else "",
            }
            for item in rows
        ],
    }


def staff_identity_projection(user, identity, factor, recovery_pending):
    return {
        "user_id": str(user.id),
        "email": user.email,
        "name": user.get_full_name,
        "documented": bool(identity),
        "configured": bool(factor and factor.confirmed_at and factor.secret_ciphertext),
        "recovery_pending": recovery_pending,
        "identity_reference": identity.evidence_reference if identity else "",
        "known_channel_reference": identity.known_channel_reference if identity else "",
    }


def staff_identities(actor, params=None):
    """One current-authority read, with no queries hidden in each projection."""
    from django.db.models import Exists, OuterRef, Q
    from .models import User, TotpRecoveryRequest

    rows = (
        User.objects.filter(is_active=True)
        .filter(Q(staff_profile__is_active=True) | Q(is_superuser=True))
        .exclude(pk=actor.pk)
        .select_related("staffsecurityidentity", "totpfactor")
        .annotate(recovery_pending=Exists(
            TotpRecoveryRequest.objects.filter(user=OuterRef("pk"), active=True)
        ))
        .order_by("email")
        .distinct()
    )
    metadata = None
    if params is not None and collection_requested(params):
        rows, metadata = collection_page(rows, params)
    results = [staff_identity_projection(
        target, getattr(target, "staffsecurityidentity", None),
        getattr(target, "totpfactor", None), target.recovery_pending,
    ) for target in rows]
    return {**metadata, "results": results} if metadata is not None else results
