"""Organization bookmarks do not reserve inventory or share personal favorites."""

from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class CompanySavedList(TimeStampedModel):
    company = models.ForeignKey(
        "features.Company", on_delete=models.PROTECT, related_name="saved_lists"
    )
    name = models.CharField(max_length=120)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    archived = models.BooleanField(default=False)
    revision = models.PositiveIntegerField(default=1)


class CompanySavedItem(TimeStampedModel):
    saved_list = models.ForeignKey(
        CompanySavedList, on_delete=models.CASCADE, related_name="items"
    )
    property = models.ForeignKey(
        "properties.Property", null=True, blank=True, on_delete=models.PROTECT
    )
    offer_id = models.CharField(max_length=100, blank=True)
    portfolio_offer = models.ForeignKey(
        "features.PortfolioOffer", null=True, blank=True, on_delete=models.PROTECT
    )
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(property__isnull=False, portfolio_offer__isnull=True)
                    | models.Q(
                        property__isnull=True,
                        portfolio_offer__isnull=False,
                        offer_id="",
                    )
                ),
                name="company_saved_exact_target",
            ),
            models.UniqueConstraint(
                fields=["saved_list", "property", "offer_id"],
                condition=models.Q(property__isnull=False),
                name="company_saved_property_unique",
            ),
            models.UniqueConstraint(
                fields=["saved_list", "portfolio_offer"],
                condition=models.Q(portfolio_offer__isnull=False),
                name="company_saved_portfolio_unique",
            ),
        ]
