from django.contrib import admin
from django.db import transaction
from .models import AccountSubscription, SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ["name_en", "workspace", "amount_minor", "period_months", "revision", "active"]
    list_filter = ["workspace", "active"]
    readonly_fields = ["id", "revision", "created_at", "updated_at"]

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            if change:
                current = SubscriptionPlan.objects.select_for_update().get(pk=obj.pk)
                obj.revision = current.revision + 1
            obj.full_clean()
            super().save_model(request, obj, form, change)


class FinancialHistoryAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AccountSubscription)
class AccountSubscriptionAdmin(FinancialHistoryAdmin):
    list_display = ["user", "plan", "workspace", "starts_at", "ends_at", "cancelled_at"]
    list_filter = ["workspace"]
