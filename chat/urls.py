from django.urls import path
from .views import (
    ConversationCreateView,
    ConversationMessageListView,
    ConversationSendMessageView,
    ConversationArchiveView, 
)

urlpatterns = [
    path("conversations/", ConversationCreateView.as_view(), name="conversation-create"),
    path("conversations/<uuid:conversation_id>/messages/", ConversationMessageListView.as_view(), name="conversation-messages"),
    path("conversations/<uuid:conversation_id>/send/", ConversationSendMessageView.as_view(), name="conversation-send"),
    path("conversations/<uuid:conversation_id>/archive/", ConversationArchiveView.as_view()),
]