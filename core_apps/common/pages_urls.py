from django.urls import path
from .pages_views import (
    AboutUsPageAPIView,
    PrivacyPolicyPageAPIView,
    TermsPageAPIView,
    StaticPageAPIView,
)

urlpatterns = [
    path("about-us/", AboutUsPageAPIView.as_view(), name="page-about-us"),
    path(
        "privacy-policy/",
        PrivacyPolicyPageAPIView.as_view(),
        name="page-privacy-policy",
    ),
    path("terms/", TermsPageAPIView.as_view(), name="page-terms"),
    path("<str:slug>/", StaticPageAPIView.as_view(), name="page-dynamic"),
]
