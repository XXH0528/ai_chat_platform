from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("conversation_id", "title", "state", "created_at", "updated_at")
    search_fields = ("conversation_id", "title")
    list_filter = ("state",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("message_id", "conversation", "role", "created_at")
    search_fields = ("message_id", "content")
    list_filter = ("role",)