"""Serialize new commitments with account erasure requests, never settlement writes."""

from django.db import transaction
from rest_framework.exceptions import PermissionDenied


def restricted_accounts(*user_ids):
    """Read-only UI projection; mutations still take the account locks below."""
    from core_apps.users.models import User, AccountClosureRequest

    ids = {identity for identity in user_ids if identity is not None}
    return set(
        User.objects.filter(pk__in=ids, closed_at__isnull=False).values_list(
            "pk", flat=True
        )
    ) | set(
        AccountClosureRequest.objects.filter(user_id__in=ids, active=True).values_list(
            "user_id", flat=True
        )
    )


def require_new_business(*user_ids):
    from core_apps.users.models import User, AccountClosureRequest

    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Check new-business eligibility inside its transaction.")
    ids = {identity for identity in user_ids if identity is not None}
    # Serialize against closure and other business guards, without blocking the
    # FK key-share checks of existing obligations and their outbox events. A
    # full UPDATE lock can deadlock with a listing update awaiting its own
    # notification commit while this creation waits for that property's lock.
    users = list(
        User.objects.select_for_update(no_key=True).filter(pk__in=ids).order_by("pk")
    )
    if (
        any(user.closed_at is not None for user in users)
        or AccountClosureRequest.objects.filter(user_id__in=ids, active=True).exists()
    ):
        raise PermissionDenied(
            {
                "code": "account_closure_pending",
                "message": (
                    "لا يمكن بدء عمل جديد مع حساب قيد الحذف. تظل الالتزامات القائمة والدعم متاحة. / "
                    "New business is unavailable while account closure is pending. "
                    "Existing obligations and support remain available."
                ),
                "next_action": "review_account_closure",
            }
        )


class NewAccountBusinessMixin:
    """Opt-in protection on creation of explicit business roots, including workers.

    No guard on updates: existing cancellation, fulfillment, financial recovery,
    maintenance and evidence remain governed by their current lifecycle.
    """

    account_party_paths = ()

    def save(self, *args, **kwargs):
        if not self._state.adding:
            return super().save(*args, **kwargs)
        with transaction.atomic():
            parties = []
            for path in self.account_party_paths:
                value = self
                for component in path.split("."):
                    value = getattr(value, component) if value is not None else None
                parties.append(value)
            require_new_business(*parties)
            return super().save(*args, **kwargs)
