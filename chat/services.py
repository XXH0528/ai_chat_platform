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
    def run_agent_once(conversation: Conversation, content: str):
        user_message = Message.objects.create(
            conversation=conversation,
            role="user",
            content=content,
            token_count=0,
            metadata={},
        )

        registry = ToolRegistry()
        recent_messages = list(
            Message.objects.filter(conversation=conversation).order_by("created_at", "id")[:30]
        )
        tool_specs = registry.list_tool_specs()
        llm_messages = build_agent_messages(recent_messages, tool_specs)

        llm_adapter = get_llm_adapter()
        decision_text = llm_adapter.generate(llm_messages)
        decision = ChatService._parse_json(decision_text)

        if decision.get("type") == "final":
            assistant_message = Message.objects.create(
                conversation=conversation,
                role="assistant",
                content=decision.get("answer", ""),
                token_count=0,
                metadata={"mode": "direct_answer"},
            )
            return {
                "user_message": user_message,
                "assistant_message": assistant_message,
                "tool_call": None,
            }

        if decision.get("type") == "tool_call":
            tool_name = decision.get("tool_name", "")
            arguments = decision.get("arguments", {})

            tool_call = ToolCall.objects.create(
                conversation=conversation,
                tool_name=tool_name,
                request_args=arguments,
                status="running",
            )

            try:
                result, latency_ms = registry.execute(tool_name, arguments)
                tool_call.response_payload = result
                tool_call.latency_ms = latency_ms
                tool_call.status = "success"
                tool_call.save(update_fields=["response_payload", "latency_ms", "status", "updated_at"])

                Message.objects.create(
                    conversation=conversation,
                    role="tool",
                    content=json.dumps(
                        {
                            "tool_name": tool_name,
                            "result": result,
                        },
                        ensure_ascii=False,
                    ),
                    token_count=0,
                    metadata={
                        "tool_call_id": tool_call.id,
                        "tool_name": tool_name,
                    },
                )
            except ToolExecutionError as e:
                tool_call.status = "failed"
                tool_call.error_message = str(e)
                tool_call.save(update_fields=["status", "error_message", "updated_at"])

                assistant_message = Message.objects.create(
                    conversation=conversation,
                    role="assistant",
                    content=f"工具调用失败：{str(e)}",
                    token_count=0,
                    metadata={"mode": "tool_error"},
                )
                return {
                    "user_message": user_message,
                    "assistant_message": assistant_message,
                    "tool_call": tool_call,
                }

            recent_messages = list(
                Message.objects.filter(conversation=conversation).order_by("created_at", "id")[:30]
            )
            llm_messages = build_agent_messages(recent_messages, tool_specs)
            final_text = llm_adapter.generate(llm_messages)
            final_decision = ChatService._parse_json(final_text)
            final_answer = final_decision.get("answer", final_text)

            assistant_message = Message.objects.create(
                conversation=conversation,
                role="assistant",
                content=final_answer,
                token_count=0,
                metadata={
                    "mode": "tool_augmented_answer",
                    "tool_name": tool_name,
                    "tool_call_id": tool_call.id,
                },
            )
            return {
                "user_message": user_message,
                "assistant_message": assistant_message,
                "tool_call": tool_call,
            }

        assistant_message = Message.objects.create(
            conversation=conversation,
            role="assistant",
            content="当前模型输出格式异常，请稍后重试。",
            token_count=0,
            metadata={"mode": "fallback"},
        )
        return {
            "user_message": user_message,
            "assistant_message": assistant_message,
            "tool_call": None,
        }
