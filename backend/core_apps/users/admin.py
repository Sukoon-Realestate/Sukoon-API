from django.contrib import admin
from django.db import transaction
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .forms import UserChangeForm, UserCreationForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


from .models import SecurityEvent


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "action",
        "decision",
        "security_epoch",
        "policy_version",
    )
    list_filter = ("action", "decision")
    readonly_fields = tuple(field.name for field in SecurityEvent._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    @transaction.atomic
    def save_model(self, request, obj, form, change):
        previous = (
            User.objects.select_for_update().filter(pk=obj.pk).first()
            if change
            else None
        )
        if previous:
            if previous.closed_at:
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied("A deleted account is read-only.")
            # A form opened before another revocation must not restore its epoch.
            obj.security_epoch = previous.security_epoch
            obj.requires_bound_session = previous.requires_bound_session
        super().save_model(request, obj, form, change)
        if previous and previous.is_active and not obj.is_active:
            from .services.sessions import revoke_all

            revoke_all(obj, actor=request.user, action="account.admin_suspended")

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return not (obj and obj.closed_at) and super().has_change_permission(request, obj)

    readonly_fields = ("is_verified", "is_email_verified")
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = [
        "pkid",
        "id",
        "email",
        "first_name",
        "last_name",
        "is_verified",
        "is_superuser",
    ]
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
                    "is_verified",
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
