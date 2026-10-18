from django.utils import timezone
from ..models import PolicyDecision
from .rental_phase2 import RentalConflict


def approved_policy(code, action):
    policies = PolicyDecision.objects.filter(
        code=code, status="approved", effective_at__lte=timezone.now()
    ).order_by("-effective_at")
    policy = next((item for item in policies if action in item.scope), None)
    if policy is None:
        raise RentalConflict(
            "This action awaits an approved policy.", code="awaiting_policy"
        )
    return policy
