from django.contrib import admin
from django.db import transaction
from .catalog_models import PromotionOption


@admin.register(PromotionOption)
class PromotionOptionAdmin(admin.ModelAdmin):
    list_display = ["id", "title_en", "duration_days", "active", "revision"]
    list_filter = ["active"]
    readonly_fields = ["revision"]

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            if change:
                current = PromotionOption.objects.select_for_update().get(pk=obj.pk)
                obj.revision = current.revision + 1
            obj.full_clean()
            super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        # Existing campaign identities remain meaningful after retirement.
        return False
