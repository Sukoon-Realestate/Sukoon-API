"""Keep the canonical Django admin registry with account recovery enforcement."""

from django.contrib.admin.apps import AdminConfig


class SokounAdminConfig(AdminConfig):
    default_site = "core_apps.common.admin_site.SokounAdminSite"
