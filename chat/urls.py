from django.urls import path
from .views import (
    ConversationCreateView,
    ConversationMessagesView,
    ConversationChatView,
)

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
]