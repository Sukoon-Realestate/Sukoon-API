from django.contrib import admin
from .models import PlatformPreferenceAudit


@admin.register(PlatformPreferenceAudit)
class PlatformPreferenceAuditAdmin(admin.ModelAdmin):
    list_display = ("revision", "actor", "created_at")
    readonly_fields = ("revision", "actor", "created_at", "before", "after")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
