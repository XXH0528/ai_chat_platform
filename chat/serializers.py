from rest_framework import serializers
from .models import Conversation, Message


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ["id", "title", "state", "created_at", "updated_at"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "role",
            "content",
            "token_count",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["id", "token_count", "metadata", "created_at"]


class SendChatMessageSerializer(serializers.Serializer):
    content = serializers.CharField()