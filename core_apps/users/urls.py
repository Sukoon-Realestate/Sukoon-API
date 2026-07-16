from django.urls import path, re_path
from .views import (
    CustomProviderAuthView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LogoutAPIView,
    GoogleAuthView,
    AppleAuthView,
    FacebookAuthView,
)


urlpatterns = [
    re_path(
        r"^o/(?P<provider>\S+)/$",
        CustomProviderAuthView.as_view(),
        name="provider-auth",
    ),
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),
    path("refresh/", CustomTokenRefreshView.as_view(), name="refresh"),
    path("logout/", LogoutAPIView.as_view()),
    path("google/", GoogleAuthView.as_view(), name="google-login"),
    path("apple/", AppleAuthView.as_view(), name="apple-login"),
    path("facebook/", FacebookAuthView.as_view(), name="facebook-login"),
]
