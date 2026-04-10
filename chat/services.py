from django.db import transaction
from .models import Conversation, Message
from .prompts import build_chat_messages
from .llm import get_llm_adapter


def get_recent_rounds(messages, max_rounds=10):
    rounds = []
    current_round = []

    for msg in reversed(messages):
        if msg.role not in ["user", "assistant"]:
            continue

        if msg.role == "assistant":
            current_round = [msg]

        elif msg.role == "user":
            if current_round:
                current_round.insert(0, msg)
                rounds.append(current_round)
                current_round = []

        if len(rounds) >= max_rounds:
            break

    result = []
    for r in reversed(rounds):
        result.extend(r)

    return result


def estimate_token_count(text: str) -> int:
    if not text:
        return 0

    has_chinese = any('\u4e00' <= ch <= '\u9fff' for ch in text)

    if has_chinese:
        return len(text)
    else:
        return len(text.split())




class ChatService:
    @staticmethod
    @transaction.atomic
    def send_user_message_and_generate_reply(conversation: Conversation, content: str):
        user_message = Message.objects.create(
            conversation=conversation,
            role="user",
            content=content,
            token_count=estimate_token_count(content),
            metadata={},
        )

        if conversation.title == "新会话":
            conversation.title = content[:20]
            conversation.save(update_fields=["title", "updated_at"])



        all_messages = list(Message.objects.filter(conversation=conversation).order_by("created_at", "id"))

        recent_messages = get_recent_rounds(all_messages, max_rounds=10)

        llm_messages = build_chat_messages(recent_messages)

        llm_adapter = get_llm_adapter()
        assistant_text = llm_adapter.generate(llm_messages)

        assistant_message = Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=assistant_text,
            token_count=estimate_token_count(assistant_text),
            metadata={
                "provider": llm_adapter.__class__.__name__,
            },
        )

        return {
            "user_message": user_message,
            "assistant_message": assistant_message,
        }

