from django.urls import path, re_path
from .views import (
    CustomProviderAuthView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LogoutAPIView,
    GoogleAuthView,
    AppleAuthView,
    FacebookAuthView,
    UserDeleteAPIView,
    UserRegisterAPIView,
    VerifyEmailAPIView,
    ResendOtpAPIView,
)


urlpatterns = [
    re_path(
        r"^o/(?P<provider>\S+)/$",
        CustomProviderAuthView.as_view(),
        name="provider-auth",
    ),
    path("register/", UserRegisterAPIView.as_view(), name="user-register"),
    path("verify/", VerifyEmailAPIView.as_view(), name="verify-email"),
    path("verify-email/", VerifyEmailAPIView.as_view()),
    path("verify-otp/", VerifyEmailAPIView.as_view()),
    path("resend-otp/", ResendOtpAPIView.as_view(), name="resend-otp"),
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),
    path("refresh/", CustomTokenRefreshView.as_view(), name="refresh"),
    path("logout/", LogoutAPIView.as_view()),
    path("delete-account/", UserDeleteAPIView.as_view(), name="user-delete"),
    path("google/", GoogleAuthView.as_view(), name="google-login"),
    path("apple/", AppleAuthView.as_view(), name="apple-login"),
    path("facebook/", FacebookAuthView.as_view(), name="facebook-login"),
]
