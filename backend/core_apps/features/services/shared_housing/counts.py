from django.db.models import Exists, OuterRef, Q, Count, F
from django.utils import timezone
from ...shared_housing_models import (
    SharedHousingPlan,
    SharedHousingProposal,
    SharedHousingConsent,
)


def pending_count(user, *, owner=False):
    active = SharedHousingPlan.objects.filter(
        expires_at__gt=timezone.now(), connection__status="accepted"
    )
    if owner:
        proposals = SharedHousingProposal.objects.filter(
            plan__in=active, property__owner=user
        )
        waiting_terms = (
            proposals.filter(status="terms")
            .annotate(
                approved=Count(
                    "consents",
                    filter=Q(
                        consents__kind="independent", consents__revision=F("revision")
                    ),
                )
            )
            .filter(approved=2)
        )
        return (
            proposals.filter(status="submitted").values("plan_id").distinct().count()
            + waiting_terms.values("plan_id").distinct().count()
        )
    own = active.filter(Q(connection__first=user) | Q(connection__second=user))
    invitations = own.filter(status="invited").exclude(coordinator=user).count()
    proposals = SharedHousingProposal.objects.filter(
        plan__in=own, status__in=["candidate", "terms"]
    )
    consent = SharedHousingConsent.objects.filter(
        proposal=OuterRef("pk"), actor=user, revision=OuterRef("revision")
    )
    awaiting = proposals.annotate(
        selection_done=Exists(consent.filter(kind="selection")),
        terms_done=Exists(consent.filter(kind="independent")),
    ).filter(
        Q(status="candidate", selection_done=False)
        | Q(status="terms", terms_done=False)
    )
    return invitations + awaiting.values("plan_id").distinct().count()
