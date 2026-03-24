from rest_framework import serializers
from .models import Conversation, Message


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = [
            "conversation_id",
            "title",
            "state",
            "created_at",
            "updated_at",
        ]


class CreateConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ["title"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "message_id",
            "conversation",
            "role",
            "content",
            "token_count",
            "metadata",
            "created_at",
            "updated_at",
            "sequence_no"，
        ]


class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField()
    client_message_id = serializers.CharField(required=False, allow_blank=True)