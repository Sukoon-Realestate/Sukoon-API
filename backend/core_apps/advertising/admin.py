from django.contrib import admin

from .models import (
    Advertisement,
    AdvertisementMedia,
    AdvertisementOperation,
    AdvertisingPlan,
    MockAdvertisementPayment,
)


@admin.register(AdvertisingPlan)
class AdvertisingPlanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title_en",
        "amount_minor",
        "revision",
        "active",
        "sort_order",
    )
    list_filter = ("active", "duration_unit", "currency")


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
admin.site.register(MockAdvertisementPayment)
