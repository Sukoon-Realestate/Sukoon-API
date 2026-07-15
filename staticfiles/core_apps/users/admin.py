from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .forms import UserChangeForm, UserCreationForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ["pkid", "id", "email", "first_name", "last_name", "is_superuser"]
    search_fields = ["first_name", "last_name", "email"]
    list_display_links = ["pkid", "id", "email"]
    ordering = ["pkid"]

    fieldsets = (
        (_("Login Credentials"), {"fields": ("email", "password")}),
        (_("Personal Information"), {"fields": ("first_name", "last_name")}),
        (
            _("Permissions and Groups"),
            {
                "fields": (
                    "is_active",
                    "is_superuser",
                    "is_staff",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important Dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                ),
            },
        ),
    )
