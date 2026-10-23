from django.urls import path
from .group_urls import urlpatterns as group_urls
from .moderation.urls import urlpatterns as moderation_urls
from .views.search import MessageSearchAPIView, ConversationLibraryAPIView

from core_apps.chat.views.conversation import (
    ConversationCreateAPIView,
    ConversationDetailAPIView,
    ConversationListAPIView,
    ConversationReadAPIView,
)
from core_apps.chat.views.message import (
    MessageCreateAPIView,
    MessageListAPIView,
)

urlpatterns = (
    group_urls
    + moderation_urls
    + [
        path("messages/search/", MessageSearchAPIView.as_view(), name="message-search"),
        path(
            "conversations/<uuid:id>/library/",
            ConversationLibraryAPIView.as_view(),
            name="conversation-library",
        ),
        path(
            "conversations/",
            ConversationListAPIView.as_view(),
            name="conversation-list",
        ),
        path(
            "conversations/create/",
            ConversationCreateAPIView.as_view(),
            name="conversation-create",
        ),
        path(
            "conversations/<uuid:id>/",
            ConversationDetailAPIView.as_view(),
            name="conversation-detail",
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
)
