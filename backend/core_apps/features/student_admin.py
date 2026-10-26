"""Catalog maintenance only; consequential student records are read-only."""

from django.contrib import admin
from . import student_models as models
from .billing_admin import FinancialHistoryAdmin
from .models import RentalSummaryGrant
from core_apps.common.catalog_admin import CatalogHistoryAdmin


@admin.register(models.University, models.Campus)
class AcademicCatalogAdmin(CatalogHistoryAdmin):
    list_display = ("name_en", "name_ar", "active", "checked_on")
    search_fields = ("name_en", "name_ar")


admin.site.register(
    [
        models.StudentProfile,
        models.AcademicHousingPlan,
        models.AcademicPlanParticipant,
        models.AcademicRequirementRevision,
        models.SharedLivingAgreement,
        models.StudentOfferPolicy,
        RentalSummaryGrant,
    ],
    FinancialHistoryAdmin,
)
