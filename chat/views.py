from django.shortcuts import render

# Create your views here.
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    CreateConversationSerializer,
    MessageSerializer,
    SendMessageSerializer,
)
from .services import (
    create_conversation,
    append_user_message,
    append_mock_assistant_message,
)


class ConversationCreateView(APIView):
    def post(self, request):
        serializer = CreateConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        conversation = create_conversation(
            title=serializer.validated_data.get("title", "")
        )
        return Response(
            ConversationSerializer(conversation).data,
            status=status.HTTP_201_CREATED
        )


class ConversationMessageListView(APIView):
    def get(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, conversation_id=conversation_id)
        messages = conversation.messages.all().order_by("created_at")
        return Response(MessageSerializer(messages, many=True).data)


class ConversationSendMessageView(APIView):
    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, conversation_id=conversation_id)

        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_content = serializer.validated_data["content"]
        client_message_id = serializer.validated_data.get("client_message_id", "")

        user_message = append_user_message(
            conversation=conversation,
            content=user_content,
            client_message_id=client_message_id,
        )

        assistant_message = append_mock_assistant_message(
            conversation=conversation,
            user_content=user_content,
        )

        return Response(
            {
                "user_message": MessageSerializer(user_message).data,
                "assistant_message": MessageSerializer(assistant_message).data,
            },
            status=status.HTTP_201_CREATED
        )

class ConversationArchiveView(APIView):
    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, conversation_id=conversation_id)

        conversation.state = "archived"
        conversation.save()

        return Response({
            "conversation_id": str(conversation.conversation_id),
            "state": conversation.state
        }, status=status.HTTP_200_OK)