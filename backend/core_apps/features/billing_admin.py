from django.contrib import admin
from django.db import transaction
from .models import AccountSubscription, SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = [
        "name_en",
        "workspace",
        "amount_minor",
        "period_months",
        "revision",
        "active",
    ]
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


from .commerce_models import (
    CommerceFeature,
    PlanBenefit,
    EntitlementGrant,
    StoreProduct,
    StoreAccount,
    StorePurchaseIntent,
    StoreTransaction,
    FeatureUsage,
    StoreNotification,
    StoreSubscriptionHead,
    StorePurchaseReview,
)


class PlanBenefitInline(admin.TabularInline):
    model = PlanBenefit
    extra = 0


SubscriptionPlanAdmin.inlines = [PlanBenefitInline]


@admin.register(CommerceFeature)
class CommerceFeatureAdmin(admin.ModelAdmin):
    list_display = ["code", "workspace", "available", "free", "enforced"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(EntitlementGrant)
class EntitlementGrantAdmin(admin.ModelAdmin):
    list_display = [
        "feature",
        "user",
        "organization",
        "source",
        "starts_at",
        "ends_at",
        "revoked_at",
    ]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(StoreProduct)
class StoreProductAdmin(admin.ModelAdmin):
    list_display = ["product_id", "plan", "platform", "environment", "active"]
    readonly_fields = ["id", "created_at", "updated_at"]

    def get_readonly_fields(self, request, obj=None):
        if obj and StorePurchaseIntent.objects.filter(product=obj).exists():
            return [f.name for f in obj._meta.fields if f.name != "active"]
        return super().get_readonly_fields(request, obj)


for commerce_model in (
    StoreAccount,
    StorePurchaseIntent,
    StoreTransaction,
    FeatureUsage,
    StoreNotification,
    StoreSubscriptionHead,
):
    admin.site.register(commerce_model, FinancialHistoryAdmin)


@admin.register(StorePurchaseReview)
class StorePurchaseReviewAdmin(FinancialHistoryAdmin):
    list_display = [
        "account",
        "transaction_id",
        "product_id",
        "amount_minor",
        "reason_code",
        "resolved_at",
    ]
    list_filter = ["reason_code", "resolved_at"]


from .paymob_models import PaymobPayment, PaymobRefund


@admin.register(PaymobPayment)
class PaymobPaymentAdmin(FinancialHistoryAdmin):
    list_display = [
        "attempt",
        "reference",
        "status",
        "order_id",
        "transaction_id",
        "failure_code",
    ]
    list_filter = ["status", "environment"]


@admin.register(PaymobRefund)
class PaymobRefundAdmin(FinancialHistoryAdmin):
    list_display = [
        "refund",
        "payment",
        "amount_minor",
        "status",
        "provider_transaction_id",
        "failure_code",
    ]
    list_filter = ["status"]
