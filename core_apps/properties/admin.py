from django.contrib import admin

from .models import (
    OwnerAvailabilitySlot,
    Property,
    PropertyFavorite,
    PropertyImage,
    PropertyRating,
    PropertyType,
    PropertyVisit,
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
        "city",
        "district",
        "owner__email",
        "owner__first_name",
        "owner__last_name",
    ]
    inlines = [PropertyImageInline]


admin.site.register(OwnerAvailabilitySlot)
admin.site.register(PropertyVisit)
admin.site.register(PropertyFavorite)
admin.site.register(SavedProperty)
admin.site.register(PropertyRating)
