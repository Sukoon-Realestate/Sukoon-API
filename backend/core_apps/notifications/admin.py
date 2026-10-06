from django.contrib import admin

from .models import DeviceToken, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "title",
        "notification_type",
        "category",
        "is_read",
        "created_at",
    ]
    list_filter = ["notification_type", "is_read", "category"]
    search_fields = ["title", "body", "user__email"]
    ordering = ["-created_at"]


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "device_type", "is_active", "token_snippet", "created_at"]
    list_filter = ["device_type", "is_active"]
    search_fields = ["token", "user__email", "device_name"]
    ordering = ["-created_at"]

    def token_snippet(self, obj: DeviceToken) -> str:
        return f"{obj.token[:20]}..." if obj.token else ""
    token_snippet.short_description = "Token"
