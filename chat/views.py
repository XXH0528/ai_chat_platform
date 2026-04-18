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
import json
from django.http import StreamingHttpResponse
from .streaming import sse_event
from .prompts import build_agent_messages
from .llm import get_llm_adapter
from .tools import ToolRegistry
from .models import ToolCall


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


class ConversationAgentChatView(APIView):
    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        serializer = SendChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = ChatService.run_agent_loop(
            conversation=conversation,
            content=serializer.validated_data["content"],
        )

        return Response(
            {
                "conversation_id": conversation.id,
                "user_message": MessageSerializer(result["user_message"]).data,
                "assistant_message": MessageSerializer(result["assistant_message"]).data,
                "tool_call_id": result["tool_call"].id if result["tool_call"] else None,
            },
            status=status.HTTP_201_CREATED,
        )



class ConversationAgentStreamView(APIView):
    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        serializer = SendChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        content = serializer.validated_data["content"]

        def event_generator():
            user_message = Message.objects.create(
                conversation=conversation,
                role="user",
                content=content,
                token_count=0,
                metadata={},
            )

            yield sse_event("message.started", {"conversation_id": conversation.id})

            registry = ToolRegistry()
            tool_specs = registry.list_tool_specs()

            recent_messages = list(
                Message.objects.filter(conversation=conversation)
                .order_by("created_at", "id")[:30]
            )

            llm_messages = build_agent_messages(recent_messages, tool_specs)
            llm_adapter = get_llm_adapter()

            decision_text = llm_adapter.generate(llm_messages)
            decision = json.loads(decision_text)

            # 👉 tool_call
            if decision.get("type") == "tool_call":
                tool_name = decision.get("tool_name")
                arguments = decision.get("arguments", {})

                yield sse_event("tool.call.started", {
                    "tool_name": tool_name,
                    "arguments": arguments,
                })

                tool_call = ToolCall.objects.create(
                    conversation=conversation,
                    tool_name=tool_name,
                    request_args=arguments,
                    status="running",
                )

                result, latency_ms = registry.execute(tool_name, arguments)

                tool_call.response_payload = result
                tool_call.latency_ms = latency_ms
                tool_call.status = "success"
                tool_call.save()

                Message.objects.create(
                    conversation=conversation,
                    role="tool",
                    content=json.dumps({
                        "tool_name": tool_name,
                        "result": result
                    }, ensure_ascii=False),
                    token_count=0,
                    metadata={"tool_call_id": tool_call.id},
                )

                yield sse_event("tool.call.finished", {
                    "tool_name": tool_name,
                    "result": result,
                })

            # 👉 final streaming
            recent_messages = list(
                Message.objects.filter(conversation=conversation)
                .order_by("created_at", "id")[:30]
            )

            llm_messages = build_agent_messages(recent_messages, tool_specs)

            buffer = []

            for delta in llm_adapter.stream_generate(llm_messages):
                buffer.append(delta)
                yield sse_event("token.delta", {"delta": delta})

            final_text = "".join(buffer)

            assistant_message = Message.objects.create(
                conversation=conversation,
                role="assistant",
                content=final_text,
                token_count=0,
                metadata={"mode": "streaming"},
            )

            yield sse_event("final.message", {
                "message_id": assistant_message.id,
                "content": final_text,
            })

        return StreamingHttpResponse(
            event_generator(),
            content_type="text/event-stream",
        )