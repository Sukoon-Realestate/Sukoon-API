from django.contrib import admin
from django.db import transaction
import uuid
from core_apps.features.billing_admin import FinancialHistoryAdmin

from .models import (
    Advertisement,
    AdvertisementMedia,
    AdvertisementOperation,
    AdvertisingPlan,
    MockAdvertisementPayment,
)


@admin.register(AdvertisingPlan)
class AdvertisingPlanAdmin(admin.ModelAdmin):
    readonly_fields = ("revision",)
    list_display = (
        "id",
        "title_en",
        "amount_minor",
        "revision",
        "active",
        "sort_order",
    )
    list_filter = ("active", "duration_unit", "currency")

    def get_readonly_fields(self, request, obj=None):
        return (*self.readonly_fields, "id") if obj else self.readonly_fields

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            if change:
                AdvertisingPlan.objects.select_for_update().get(pk=obj.pk)
                obj.revision = uuid.uuid4().hex
            obj.full_clean()
            super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner",
        "title",
        "status",
        "starts_at",
        "ends_at",
        "created_at",
    )
    list_filter = ("status", "placement")
    search_fields = ("id", "owner__email", "title", "operation__operation_id")
    readonly_fields = ("plan_snapshot", "starts_at", "ends_at", "activated_at")


admin.site.register(AdvertisementMedia)
admin.site.register(AdvertisementOperation)
admin.site.register(MockAdvertisementPayment, FinancialHistoryAdmin)
