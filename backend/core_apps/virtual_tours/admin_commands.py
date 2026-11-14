"""Native administrative commands using canonical tour review and current authority."""

from django.db import transaction
from rest_framework.exceptions import PermissionDenied

from core_apps.admin_api.permissions import require_staff_actor
from .models import PropertyVirtualTour, TourRevision
from .review_access import reviewer
from .services import review


@transaction.atomic
def review_revision(actor, revision_id, body):
    actor = reviewer(actor, write=True, lock=True)
    revision = (
        TourRevision.objects.select_for_update(of=("self",))
        .select_related("tour__property")
        .get(pk=revision_id)
    )
    return review(revision, actor, body)


@transaction.atomic
def disable_viewing(actor, identities):
    """Supported native emergency suppression; cannot approve or republish."""
    actor = require_staff_actor(actor, lock=True)
    if not actor.has_perm("virtual_tours.change_propertyvirtualtour"):
        raise PermissionDenied("Current tour change permission is required.")
    return PropertyVirtualTour.objects.filter(pk__in=identities).update(disabled=True)
