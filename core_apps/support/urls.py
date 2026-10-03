from django.urls import path

from core_apps.support.views import (
    HelpCenterAPIView,
    TicketDetailAPIView,
    TicketListCreateAPIView,
    TicketReplyAPIView,
)

urlpatterns = [
    path("help-center/", HelpCenterAPIView.as_view(), name="support-help-center"),
    path(
        "tickets/", TicketListCreateAPIView.as_view(), name="support-ticket-list-create"
    ),
    path(
        "tickets/<str:id>/", TicketDetailAPIView.as_view(), name="support-ticket-detail"
    ),
    path(
        "tickets/<str:id>/replies/",
        TicketReplyAPIView.as_view(),
        name="support-ticket-reply",
    ),
]
