"""VisitReview operations owned by PropertyVisitService."""

from datetime import datetime
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied, ValidationError
from ....models import PropertyRating, PropertyVisit, PropertyVisitReview


class VisitReviewMixin:
    @classmethod
    @transaction.atomic
    def create_review(cls, tenant, visit_obj, validated_data):
        """Create the tenant's one-time review after a confirmed visit took place."""
        visit_obj = (
            PropertyVisit.objects.select_for_update()
            .select_related("property")
            .get(pk=visit_obj.pk)
        )
        if visit_obj.tenant != tenant:
            raise PermissionDenied(_("You cannot review another tenant's visit."))

        if visit_obj.status != PropertyVisit.Status.CONFIRMED:
            raise ValidationError(_("Only confirmed visits can be reviewed."))

        now = timezone.localtime()
        scheduled_at = datetime.combine(
            visit_obj.visit_date, visit_obj.visit_time, now.tzinfo
        )
        if scheduled_at > now:
            raise ValidationError(
                _("The visit cannot be reviewed before it takes place.")
            )

        if PropertyVisitReview.objects.filter(visit=visit_obj).exists():
            raise ValidationError(_("This visit has already been reviewed."))

        # ? Calculate overall_rating as the rounded average of the sub-ratings
        cleanliness = validated_data.get("cleanliness_rating")
        accuracy = validated_data.get("listing_accuracy_rating")
        interaction = validated_data.get("owner_interaction_rating")
        sub_ratings = [r for r in (cleanliness, accuracy, interaction) if r is not None]
        if sub_ratings:
            validated_data["overall_rating"] = round(
                sum(sub_ratings) / len(sub_ratings)
            )

        review = PropertyVisitReview.objects.create(visit=visit_obj, **validated_data)
        # ? Keep the existing property aggregate API in sync with visit reviews.
        PropertyRating.objects.update_or_create(
            user=tenant,
            property=visit_obj.property,
            defaults={"rating": review.overall_rating},
        )
        return review
