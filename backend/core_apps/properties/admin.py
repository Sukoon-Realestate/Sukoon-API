from django import forms
from django.contrib import admin, messages
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, APIException
from django.http import HttpResponseRedirect
from uuid import uuid4

from core_apps.admin_api.permissions import require_staff_actor
from core_apps.common.catalog_admin import CatalogHistoryAdmin


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


class PropertyRequestImageInline(PropertyImageInline):
    extra = 0
    readonly_fields = ["image", "name", "description"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class PropertyModerationForm(forms.ModelForm):
    decision = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Choose a review decision"),
            ("approve", "Approve"),
            ("reject", "Reject for correction"),
            ("request_revision", "Request revision"),
            ("block", "Block"),
            ("unblock", "Lift block"),
        ],
    )
    reason = forms.CharField(
        required=False,
        max_length=2000,
        widget=forms.Textarea,
        label="Reason shown to owner",
    )
    internal_note = forms.CharField(
        required=False,
        max_length=4000,
        widget=forms.Textarea,
        label="Internal reviewer note",
    )
    expected_version = forms.CharField(widget=forms.HiddenInput)
    request_key = forms.UUIDField(widget=forms.HiddenInput)

    class Meta:
        model = Property
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and not self.is_bound:
            from .services.moderation import version

            self.initial["expected_version"] = version(self.instance)
            self.initial["request_key"] = uuid4()

    def clean(self):
        data = super().clean()
        if (
            data.get("decision")
            and data["decision"] != "approve"
            and not data.get("reason", "").strip()
        ):
            self.add_error("reason", "Explain the decision to the owner.")
        return data


@admin.register(PropertyType)
class PropertyTypeAdmin(CatalogHistoryAdmin):
    list_display = ["name", "slug", "is_active", "revision", "created_at"]
    search_fields = ["name", "slug"]
    ordering = ["name"]


@admin.register(Governorate)
class GovernorateAdmin(CatalogHistoryAdmin):
    list_display = ["name", "slug", "created_at"]
    search_fields = ["name", "slug"]
    readonly_fields = ["slug"]
    ordering = ["name"]


@admin.register(City)
class CityAdmin(CatalogHistoryAdmin):
    list_display = ["name", "governorate", "slug", "created_at"]
    list_filter = ["governorate"]
    search_fields = ["name", "slug", "governorate__name"]
    readonly_fields = ["slug"]
    ordering = ["name"]


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    form = PropertyModerationForm
    actions = []

    def get_readonly_fields(self, request, obj=None):
        return [
            field.name
            for field in self.model._meta.fields + self.model._meta.many_to_many
        ]

    def has_change_permission(self, request, obj=None):
        try:
            require_staff_actor(
                request.user, {"system_owner", "main_admin", "property_reviewer"}
            )
        except PermissionDenied:
            return False
        return super().has_change_permission(request, obj)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @transaction.atomic
    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if request.method == "POST":
            try:
                require_staff_actor(
                    request.user,
                    {"system_owner", "main_admin", "property_reviewer"},
                    lock=True,
                )
            except PermissionDenied as error:
                from django.core.exceptions import (
                    PermissionDenied as DjangoPermissionDenied,
                )

                raise DjangoPermissionDenied(str(error.detail)) from error
        if object_id is not None:
            Property.objects.select_for_update().filter(pk=object_id).first()
        return super().changeform_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        from .services.moderation import decide

        data = form.cleaned_data
        if not data.get("decision"):
            request.property_review_error = True
            self.message_user(
                request, "Choose a review decision.", level=messages.ERROR
            )
            return
        try:
            decide(
                obj.id,
                reviewer=request.user,
                action=data["decision"],
                expected_version=data["expected_version"],
                request_key=str(data["request_key"]),
                reason=data.get("reason", ""),
                internal_note=data.get("internal_note", ""),
            )
        except APIException as error:
            request.property_review_error = True
            self.message_user(request, str(error.detail), level=messages.ERROR)

    def save_related(self, request, form, formsets, change):
        # The admin log expects formset bookkeeping even when writes are forbidden.
        for formset in formsets:
            formset.new_objects = []
            formset.changed_objects = []
            formset.deleted_objects = []

    def response_change(self, request, obj):
        if getattr(request, "property_review_error", False):
            return HttpResponseRedirect(request.path)
        return super().response_change(request, obj)

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
    inlines = [PropertyRequestImageInline]


@admin.register(PropertyRequest)
class PropertyRequestAdmin(PropertyAdmin):
    list_display = ["title", "owner", "status", "is_verified", "created_at"]
    list_filter = ["status", "is_verified"]
    list_select_related = ["owner"]
    ordering = ["-created_at", "-pk"]
    inlines = [PropertyRequestImageInline]

    def get_readonly_fields(self, request, obj=None):
        return [
            field.name
            for field in self.model._meta.fields + self.model._meta.many_to_many
        ]

    # Share the existing property permissions instead of granting new authority
    # through a separate proxy model.
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm(
            "properties.view_property"
        ) or self.has_change_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        try:
            require_staff_actor(
                request.user, {"system_owner", "main_admin", "property_reviewer"}
            )
        except PermissionDenied:
            return False
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
class DistrictAdmin(CatalogHistoryAdmin):
    list_display = ["name", "city", "is_active"]
    list_filter = ["is_active", "city"]
    search_fields = ["name", "city__name"]
