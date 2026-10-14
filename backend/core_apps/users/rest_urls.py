"""Djoser permissions/actions with Sokoun's JSON command response contract."""

from djoser.views import UserViewSet
from rest_framework.routers import DefaultRouter


class CanonicalUserViewSet(UserViewSet):
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
