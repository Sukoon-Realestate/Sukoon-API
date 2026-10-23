from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from django.db import transaction
from rest_framework.exceptions import PermissionDenied

from core_apps.admin_api.permissions import require_staff_actor
from core_apps.admin_api.services import (
    approve_admin_property,
    reject_admin_property,
    request_admin_property_revision,
)

from .models import (
    City,
    Governorate,
    OwnerAvailabilitySlot,
    Property,
    PropertyFavorite,
    PropertyImage,
    PropertyRating,
    PropertyRequest,
    PropertyType,
    PropertyVisit,
    PropertyVisitReview,
    SavedProperty,
)


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


class PropertyModerationActionForm(ActionForm):
    reason = forms.CharField(
        label="Review reason",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text="Required when rejecting a listing or requesting revisions.",
    )


@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_at"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["name"]


@admin.register(Governorate)
class GovernorateAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_at"]
    search_fields = ["name", "slug"]
    readonly_fields = ["slug"]
    ordering = ["name"]


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ["name", "governorate", "slug", "created_at"]
    list_filter = ["governorate"]
    search_fields = ["name", "slug", "governorate__name"]
    readonly_fields = ["slug"]
    ordering = ["name"]


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    action_form = PropertyModerationActionForm
    actions = [
        "approve_selected_properties",
        "request_property_revisions",
        "reject_selected_properties",
    ]

    # Physical topology uses the versioned property/portfolio services. Generic
    # admin edits must not bypass aggregate holds or rewrite historical scope.
    readonly_fields = [
        "building",
        "complex",
        "unit_code",
        "occupancy_capacity",
        "rental_inventory",
        "portfolio_inheritance",
        "retired_at",
        "replaces",
        "status",
        "is_verified",
    ]

    def has_can_moderate_properties_permission(self, request):
        try:
            require_staff_actor(
                request.user,
                {"system_owner", "main_admin", "property_reviewer"},
            )
        except PermissionDenied:
            return False
        return True

    def _apply_moderation_decision(self, request, queryset, decision, reason=""):
        reason = reason.strip()
        if decision != "approve" and not reason:
            self.message_user(
                request,
                "Enter a review reason before rejecting a listing or requesting revisions.",
                level=messages.ERROR,
            )
            return

        transitions = {
            "approve": approve_admin_property,
            "request_revision": request_admin_property_revision,
            "reject": reject_admin_property,
        }
        transition = transitions[decision]
        updated_count = 0
        try:
            with transaction.atomic():
                for property_obj in queryset:
                    transition(
                        property_obj.id,
                        reviewer=request.user,
                        **({"reason": reason} if decision != "approve" else {}),
                    )
                    updated_count += 1
        except PermissionDenied as error:
            self.message_user(request, str(error.detail), level=messages.ERROR)
            return

        decision_labels = {
            "approve": "approved",
            "request_revision": "marked for revision",
            "reject": "rejected",
        }
        self.message_user(
            request,
            f"{updated_count} property listing(s) {decision_labels[decision]}.",
            level=messages.SUCCESS,
        )

    @admin.action(
        description="Approve selected property listings",
        permissions=["can_moderate_properties"],
    )
    def approve_selected_properties(self, request, queryset):
        self._apply_moderation_decision(request, queryset, "approve")

    @admin.action(
        description="Request revisions for selected property listings",
        permissions=["can_moderate_properties"],
    )
    def request_property_revisions(self, request, queryset):
        self._apply_moderation_decision(
            request, queryset, "request_revision", request.POST.get("reason", "")
        )

    @admin.action(
        description="Reject selected property listings",
        permissions=["can_moderate_properties"],
    )
    def reject_selected_properties(self, request, queryset):
        self._apply_moderation_decision(
            request, queryset, "reject", request.POST.get("reason", "")
        )

    def has_delete_permission(self, request, obj=None):
        if obj and (obj.building_id or obj.complex_id or obj.portfolio_offers.exists()):
            return False
        return super().has_delete_permission(request, obj)

    def delete_queryset(self, request, queryset):
        from django.core.exceptions import PermissionDenied
        from django.db.models import Q

        if queryset.filter(
            Q(building__isnull=False)
            | Q(complex__isnull=False)
            | Q(portfolio_offers__isnull=False)
        ).exists():
            raise PermissionDenied(
                "Portfolio inventory is retained. Hide listings through their controlled lifecycle."
            )
        return super().delete_queryset(request, queryset)

    list_display = [
        "title",
        "owner",
        "property_type",
        "price",
        "price_period",
        "status",
        "is_verified",
        "created_at",
    ]
    list_filter = [
        "status",
        "property_type",
        "price_period",
        "is_verified",
        "is_furnished",
        "suitable_for",
        "smoking_allowed",
    ]
    search_fields = [
        "title",
        "description",
        "city__name",
        "governorate__name",
        "district",
        "owner__email",
        "owner__first_name",
        "owner__last_name",
    ]
    inlines = [PropertyImageInline]


@admin.register(PropertyRequest)
class PropertyRequestAdmin(PropertyAdmin):
    list_display = ["title", "owner", "status", "is_verified", "created_at"]
    list_filter = ["status", "is_verified"]
    list_select_related = ["owner"]
    ordering = ["-created_at", "-pk"]

    # Share the existing property permissions instead of granting new authority
    # through a separate proxy model.
    def has_view_permission(self, request, obj=None):
        return (
            request.user.has_perm("properties.view_property")
            or self.has_change_permission(request, obj)
        )

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm("properties.change_property")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OwnerAvailabilitySlot)
class OwnerAvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ["property", "owner", "date", "time", "is_enabled"]
    list_filter = ["is_enabled", "date"]
    search_fields = ["property__title", "owner__email"]
    autocomplete_fields = ["property"]
    exclude = ["owner"]

    def save_model(self, request, obj, form, change):
        # ? Keep the legacy owner field consistent while availability is property-scoped.
        obj.owner = obj.property.owner
        super().save_model(request, obj, form, change)


admin.site.register(PropertyVisit)
admin.site.register(PropertyVisitReview)
admin.site.register(PropertyFavorite)
admin.site.register(SavedProperty)
admin.site.register(PropertyRating)


from .models import District


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "is_active"]
    list_filter = ["is_active", "city"]
    search_fields = ["name", "city__name"]
