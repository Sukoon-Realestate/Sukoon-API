"""Djoser permissions/actions with Sokoun's JSON command response contract."""

from djoser.views import UserViewSet
from rest_framework.routers import DefaultRouter


class CanonicalUserViewSet(UserViewSet):
    from .services.recovery_tokens import recovery_token_generator as token_generator

    # Djoser's identity/token validation remains authoritative. Validate again
    # under the account lock so a reset link cannot be replayed concurrently.
    from rest_framework.decorators import action

    @action(["post"], detail=False)
    def reset_password_confirm(self, request, *args, **kwargs):
        from django.db import transaction
        from .models import User
        from .services.sessions import revoke_all

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=serializer.user.pk)
            response = super().reset_password_confirm(request, *args, **kwargs)
            if response.status_code == 204:
                revoke_all(user, action="password.reset")
            return response

    @action(["post"], detail=False)
    def set_password(self, request, *args, **kwargs):
        from django.db import transaction
        from .models import User
        from .services.sessions import revoke_all

        with transaction.atomic():
            request.user = User.objects.select_for_update().get(pk=request.user.pk)
            response = super().set_password(request, *args, **kwargs)
            if response.status_code == 204:
                revoke_all(request.user, action="password.change")
            return response

    @action(["post"], detail=False, url_path="set_email")
    def set_username(self, request, *args, **kwargs):
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied(
            "Contact changes require approved verification of the new contact."
        )

    @action(["post"], detail=False, url_path="reset_email")
    def reset_username(self, request, *args, **kwargs):
        return self.set_username(request, *args, **kwargs)

    @action(["post"], detail=False, url_path="reset_email_confirm")
    def reset_username_confirm(self, request, *args, **kwargs):
        return self.set_username(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        if response.status_code == 204:
            messages = {
                "reset_password": "If this account exists, password reset instructions have been sent.",
                "reset_password_confirm": "Password changed successfully.",
                "set_password": "Password changed successfully.",
                "activation": "Account activated successfully.",
                "resend_activation": "Activation instructions have been sent.",
                "destroy": "User account deleted successfully.",
            }
            response.status_code = 200
            response.data = {
                "message": messages.get(self.action, "Updated successfully."),
                "data": None,
            }
        return super().finalize_response(request, response, *args, **kwargs)


router = DefaultRouter()
router.register("users", CanonicalUserViewSet, basename="user")
urlpatterns = router.urls
