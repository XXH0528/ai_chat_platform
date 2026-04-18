import json
from django.db import transaction
from .models import Conversation, Message, ToolCall
from .prompts import build_agent_messages
from .llm import get_llm_adapter
from .tools import ToolRegistry, ToolExecutionError


class ChatService:
    @staticmethod
    def _parse_json(text: str):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {
                "type": "final",
                "answer": text,
            }

    @staticmethod
    @transaction.atomic
    def run_agent_loop(conversation, content):
        user_message = Message.objects.create(
            conversation=conversation,
            role="user",
            content=content,
            token_count=0,
            metadata={},
        )

        registry = ToolRegistry()
        llm_adapter = get_llm_adapter()

        max_steps = 3
        tool_call = None

        for step in range(max_steps):

            recent_messages = list(
                Message.objects.filter(conversation=conversation)
                .order_by("created_at", "id")[:30]
            )

            llm_messages = build_agent_messages(
                recent_messages,
                registry.list_tool_specs()
            )

            decision_text = llm_adapter.generate(llm_messages)
            decision = ChatService._parse_json(decision_text)

            if decision.get("type") == "final":
                assistant_message = Message.objects.create(
                    conversation=conversation,
                    role="assistant",
                    content=decision.get("answer", ""),
                    token_count=0,
                    metadata={},
                )
                return {
                    "user_message": user_message,
                    "assistant_message": assistant_message,
                    "tool_call": tool_call,
                }

            if decision.get("type") == "tool_call":
                tool_name = decision.get("tool_name")
                arguments = decision.get("arguments", {})

                tool_call = ToolCall.objects.create(
                    conversation=conversation,
                    tool_name=tool_name,
                    request_args=arguments,
                    status="running",
                )

                tool_result = registry.execute(tool_name, arguments)

                if tool_result["status"] == "success":
                    tool_call.response_payload = tool_result["result"]
                    tool_call.latency_ms = tool_result["latency_ms"]
                    tool_call.status = "success"
                    tool_call.save()

                    Message.objects.create(
                        conversation=conversation,
                        role="tool",
                        content=json.dumps({
                            "tool_name": tool_name,
                            "result": tool_result["result"]
                        }, ensure_ascii=False),
                        token_count=0,
                        metadata={},
                    )

                    continue

                else:
                    tool_call.status = "failed"
                    tool_call.error_message = tool_result["error"]
                    tool_call.metadata = {
                        "error_type": tool_result.get("error_type")
                    }
                    tool_call.save()

                    error_type = tool_result.get("error_type")

                    if error_type == "timeout":
                        reply = "工具执行超时，请稍后再试。"
                    elif error_type == "validation_error":
                        reply = "工具参数错误，请检查输入。"
                    else:
                        reply = "工具执行失败，请稍后重试。"

                    assistant_message = Message.objects.create(
                        conversation=conversation,
                        role="assistant",
                        content=reply,
                        token_count=0,
                        metadata={"error_type": error_type},
                    )

                    return {
                        "user_message": user_message,
                        "assistant_message": assistant_message,
                        "tool_call": tool_call,
                    }
