from django.contrib import admin
from core_apps.common.content_admin import ManagedContentAdmin
from .models import HelpContact, HelpArticle


@admin.register(HelpContact)
class HelpContactAdmin(ManagedContentAdmin):
    list_display = ("workspace", "email", "active", "revision")

    def get_readonly_fields(self, request, obj=None):
        return (*self.readonly_fields, "workspace") if obj else self.readonly_fields


@admin.register(HelpArticle)
class HelpArticleAdmin(ManagedContentAdmin):
    list_display = (
        "slug",
        "workspace",
        "question_en",
        "sort_order",
        "active",
        "revision",
    )
    list_filter = ("workspace", "active")
    search_fields = ("slug", "question_ar", "question_en")

    def get_readonly_fields(self, request, obj=None):
        return (*self.readonly_fields, "slug") if obj else self.readonly_fields
