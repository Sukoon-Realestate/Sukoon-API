from django.db.models import F, Case, When, Value
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Property, PropertyImage


@receiver(post_save, sender=PropertyImage)
@receiver(post_delete, sender=PropertyImage)
def invalidate_media_revision(sender, instance, **kwargs):
    Property.objects.filter(pk=instance.property_id).update(
        media_revision=F("media_revision") + 1,
        review_revision=F("review_revision") + 1,
        is_verified=False,
        status=Case(
            When(moderation_blocked=True, then=Value(Property.Status.HIDDEN)),
            When(status=Property.Status.HIDDEN, then=Value(Property.Status.HIDDEN)),
            default=Value(Property.Status.UNDER_REVIEW),
        ),
    )


@receiver(post_save, sender=Property)
def update_search_document(sender, instance, raw=False, **kwargs):
    if raw:
        return
    from .services.search_document import document

    Property.objects.filter(pk=instance.pk).update(search_document=document(instance))
