from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from core_apps.users.views import PasswordResetConfirmView
from django.conf.urls.static import static
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions


schema_view = get_schema_view(
    openapi.Info(
        title="Darak API",
        default_version="v1",
        description="Darak Real Estate API.",
        contact=openapi.Contact("zeyadslama23@gmail.com"),
        license=openapi.License("MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    path("password-reset/<str:uid>/<str:token>/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password-reset/<str:uid>/<str:token>", PasswordResetConfirmView.as_view()),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("api/v1/auth/", include("djoser.urls")),
    path("api/v1/auth/", include("core_apps.users.urls")),
    path("api/v1/profiles/", include("core_apps.profiles.urls")),
    path(settings.ADMIN_URL, admin.site.urls),
]


admin.site.site_header = "Darak Admin"
admin.site.site_title = "Darak Admin Portal"
admin.site.index_title = "Welcome To Darak Admin Portal"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
