from django.urls import path
from .views import (
    ConversationCreateView,
    ConversationMessagesView,
    ConversationAgentChatView,
    ConversationAgentStreamView,
)

urlpatterns = [
    path("conversations/", ConversationCreateView.as_view(), name="conversation-create"),
    path(
        "conversations/<int:conversation_id>/messages/",
        ConversationMessagesView.as_view(),
        name="conversation-messages",
    ),
    path(
        "conversations/<int:conversation_id>/agent/chat/",
        ConversationAgentChatView.as_view(),
        name="conversation-agent-chat",
    ),
    path(
        "conversations/<int:conversation_id>/agent/stream/",
        ConversationAgentStreamView.as_view(),
        name="conversation-agent-stream",
    ),
]