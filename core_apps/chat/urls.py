from django.urls import path

from core_apps.chat.views.conversation import (
    ConversationCreateAPIView,
    ConversationListAPIView,
    ConversationReadAPIView,
)
from core_apps.chat.views.message import (
    MessageCreateAPIView,
    MessageListAPIView,
)

urlpatterns = [
    path("conversations/", ConversationListAPIView.as_view(), name="conversation-list"),
    path(
        "conversations/create/",
        ConversationCreateAPIView.as_view(),
        name="conversation-create",
    ),
    path(
        "conversations/<uuid:id>/messages/",
        MessageListAPIView.as_view(),
        name="message-list",
    ),
    path(
        "conversations/<uuid:id>/messages/create/",
        MessageCreateAPIView.as_view(),
        name="message-create",
    ),
    path(
        "conversations/<uuid:id>/read/",
        ConversationReadAPIView.as_view(),
        name="conversation-read",
    ),
]
