from django.contrib import admin

from .models import (
    City,
    Governorate,
    OwnerAvailabilitySlot,
    Property,
    PropertyFavorite,
    PropertyImage,
    PropertyRating,
    PropertyType,
    PropertyVisit,
    PropertyVisitReview,
    SavedProperty,
)


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


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
