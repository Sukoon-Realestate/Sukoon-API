"""Djoser permissions/actions with Sokoun's JSON command response contract."""

from djoser.views import UserViewSet
from rest_framework.routers import DefaultRouter


class CanonicalUserViewSet(UserViewSet):
    from .services.recovery_tokens import recovery_token_generator as token_generator

    from rest_framework.decorators import action

    @action(["post"], detail=False)
    def reset_password_confirm(self, request, *args, **kwargs):
        from rest_framework.response import Response
        from .services.passwords import reset_inherited_password

        reset_inherited_password(request, self.get_serializer)
        return Response(status=204)

    @action(["post"], detail=False)
    def set_password(self, request, *args, **kwargs):
        from rest_framework.response import Response
        from .services.passwords import change_inherited_password

        change_inherited_password(request, self.get_serializer)
        return Response(status=204)

    def perform_update(self, serializer, *args, **kwargs):
        from .services.inherited_accounts import update_account

        update_account(self.request, serializer, sender=self.__class__,
                       check_permissions=self.check_object_permissions)

    @action(["post"], detail=False)
    def activation(self, request, *args, **kwargs):
        from rest_framework.response import Response
        from .services.inherited_accounts import activate_account

        activate_account(request, self.get_serializer, sender=self.__class__)
        return Response(status=204)

    @action(["post"], detail=False, url_path="set_email")
    def set_username(self, request, *args, **kwargs):
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied(
            "Contact changes require approved verification of the new contact."
        )

    def destroy(self, request, *args, **kwargs):
        from rest_framework.response import Response
        from .services.account_closure import closure_required

        self.get_object()
        return Response(closure_required(), status=409)

    def perform_destroy(self, instance):
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied("Accounts close only through the reviewed closure request.")

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
