from django.urls import path
from .views import (
    ConversationCreateView,
    ConversationMessagesView,
    ConversationChatView,
)
from .views import HealthCheckView

urlpatterns = [
    path("conversations/", ConversationCreateView.as_view(), name="conversation-create"),
    path(
        "conversations/<int:conversation_id>/messages/",
        ConversationMessagesView.as_view(),
        name="conversation-messages",
    ),
    path(
        "conversations/<int:conversation_id>/chat/",
        ConversationChatView.as_view(),
        name="conversation-chat",
    ),
    path("health/", HealthCheckView.as_view(), name="health-check"),
]