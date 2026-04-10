from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    MessageSerializer,
    SendChatMessageSerializer,
)
from .services import ChatService


class ConversationCreateView(APIView):
    def post(self, request):
        title = request.data.get("title", "新会话")
        conversation = Conversation.objects.create(title=title)
        return Response(ConversationSerializer(conversation).data, status=status.HTTP_201_CREATED)


class ConversationMessagesView(APIView):
    def get(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        messages = Message.objects.filter(conversation=conversation).order_by("created_at", "id")
        return Response(MessageSerializer(messages, many=True).data)


class ConversationChatView(APIView):
    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        serializer = SendChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = ChatService.send_user_message_and_generate_reply(
            conversation=conversation,
            content=serializer.validated_data["content"],
        )

        return Response(
            {
                "conversation_id": conversation.id,
                "user_message": MessageSerializer(result["user_message"]).data,
                "assistant_message": MessageSerializer(result["assistant_message"]).data,
            },
            status=status.HTTP_201_CREATED,
        )


class HealthCheckView(APIView):
    def get(self, request):
        api_key = os.getenv("OPENAI_API_KEY")

        if api_key and api_key.startswith("sk-"):
            llm_mode = "openai"
        else:
            llm_mode = "stub"

        return Response({
            "status": "ok",
            "llm_mode": llm_mode,
        })