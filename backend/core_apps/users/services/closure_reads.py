"""Request-scoped closure projections; no cross-request/private authority cache."""
from ..models import AccountClosureDecision, AccountProfileErasureFile
from ..read_pages import prepare_history
from .closure_blockers import blockers_for_users


def prepare_projections(items, *, page=None):
    items = list(items)
    facts = blockers_for_users([item.user for item in items if item.active])
    pending = set(AccountProfileErasureFile.objects.filter(
        request_id__in=[item.pk for item in items], deleted_at__isnull=True,
    ).values_list("request_id", flat=True)) if items else set()
    for item in items:
        item.prepared_blockers = facts.get(item.user_id, [])
        item.prepared_erasure = item.pk in pending
    return prepare_history(items, AccountClosureDecision, "request", page=page)
