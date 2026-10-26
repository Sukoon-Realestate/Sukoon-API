from django.contrib import admin
from django.db import transaction
from .content_models import PublicContentPage


class ManagedContentAdmin(admin.ModelAdmin):
    readonly_fields = ("revision", "updated_at")

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            from core_apps.admin_api.services.content_registry import (
                REGISTRY,
                projection,
            )
            from .content_models import ContentEditAudit

            kind = next(
                key for key, entry in REGISTRY.items() if entry.model is type(obj)
            )
            before = {}
            if change:
                previous = type(obj).objects.select_for_update().get(pk=obj.pk)
                before = projection(kind, previous)
                obj.revision = previous.revision + 1
            obj.full_clean()
            super().save_model(request, obj, form, change)
            ContentEditAudit.objects.create(
                kind=kind,
                object_id=str(obj.pk),
                revision=obj.revision,
                actor=request.user,
                reason="Django content administration",
                before=before,
                after=projection(kind, obj),
            )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PublicContentPage)
class PublicContentPageAdmin(ManagedContentAdmin):
    list_display = ("slug", "title_en", "active", "revision", "updated_at")
    list_filter = ("active",)

    def get_readonly_fields(self, request, obj=None):
        return (*self.readonly_fields, "slug") if obj else self.readonly_fields


from .content_models import ReleaseNote


@admin.register(ReleaseNote)
class ReleaseNoteAdmin(ManagedContentAdmin):
    list_display = ("version", "workspace", "active", "publish_at", "revision")
    list_filter = ("workspace", "active")
