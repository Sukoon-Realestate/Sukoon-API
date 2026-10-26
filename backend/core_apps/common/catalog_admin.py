from django.contrib import admin


class CatalogHistoryAdmin(admin.ModelAdmin):
    """Edits use the shared, versioned content editor; historical rows stay visible."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
