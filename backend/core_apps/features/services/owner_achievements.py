from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from ..models import Lease, OwnerRentalAchievement, OwnerMilestone

TIERS = (("bronze", 2), ("silver", 6), ("gold", 16), ("diamond", 31))


def level(count):
    return next(
        (name for name, threshold in reversed(TIERS) if count >= threshold), "starter"
    )


def summary(owner):
    count = OwnerRentalAchievement.objects.filter(owner=owner, revoked=False).count()
    tier = level(count)
    next_level = next(
        ((name, threshold) for name, threshold in TIERS if threshold > count), None
    )
    pending = (
        OwnerMilestone.objects.filter(
            owner=owner, acknowledged_at__isnull=True, threshold__lte=count
        )
        .order_by("-threshold")
        .first()
    )
    return {
        "tier": tier,
        "successful_rentals": count,
        "next_tier": next_level[0] if next_level else None,
        "next_threshold": next_level[1] if next_level else None,
        "remaining": next_level[1] - count if next_level else 0,
        "pending_event": (
            {"id": str(pending.id), "tier": pending.tier} if pending else None
        ),
    }


@receiver(post_save, sender=Lease, dispatch_uid="owner_successful_rental_achievement")
def record_success(sender, instance, raw=False, **kwargs):
    if (
        raw
        or instance.legacy_read_only
        or not instance.activated_at
        or instance.occupancy_status not in {"occupied", "move_out_pending", "returned"}
        or instance.status in {"draft", "cancelled", "expired"}
    ):
        return
    with transaction.atomic():
        owner = get_user_model().objects.select_for_update().get(pk=instance.owner_id)
        OwnerRentalAchievement.objects.get_or_create(
            tenancy_root_id=instance.tenancy_root_id,
            defaults={"owner": owner, "lease": instance},
        )
        count = OwnerRentalAchievement.objects.filter(
            owner=owner, revoked=False
        ).count()
        for tier, threshold in TIERS:
            if count >= threshold:
                OwnerMilestone.objects.get_or_create(
                    owner=owner, tier=tier, defaults={"threshold": threshold}
                )


def acknowledge(owner, identity):
    from django.shortcuts import get_object_or_404

    with transaction.atomic():
        event = get_object_or_404(
            OwnerMilestone.objects.select_for_update(), owner=owner, id=identity
        )
        OwnerMilestone.objects.filter(
            owner=owner, threshold__lte=event.threshold, acknowledged_at__isnull=True
        ).update(acknowledged_at=timezone.now())
    return summary(owner)
