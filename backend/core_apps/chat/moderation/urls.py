from django.urls import path
from .views import (
    ChatPolicyView,
    RentalContextView,
    AccountPolicyView,
    AppealView,
    AdminCasesView,
    AdminCaseView,
    AdminCaseMediaView,
    AdminPolicyStatusView,
)

urlpatterns = [
    path("admin/policy-status/", AdminPolicyStatusView.as_view()),
    path("conversations/<uuid:id>/policy/", ChatPolicyView.as_view()),
    path("conversations/<uuid:id>/rental-context/", RentalContextView.as_view()),
    path("account-policy/", AccountPolicyView.as_view()),
    path("policy-cases/<uuid:id>/appeal/", AppealView.as_view()),
    path("admin/policy-cases/", AdminCasesView.as_view()),
    path("admin/policy-cases/<uuid:id>/", AdminCaseView.as_view()),
    path(
        "admin/policy-cases/<uuid:id>/attachments/<uuid:attachment_id>/",
        AdminCaseMediaView.as_view(),
    ),
]
