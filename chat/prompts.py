from django.conf import settings


def build_chat_messages(recent_messages):
    """
    将数据库中的 Message 记录转换为 LLM 所需的 messages 格式。
    当前版本仅拼接：
    1. system prompt
    2. recent window
    """
    messages = [
        {
            "role": "system",
            "content": settings.SYSTEM_PROMPT,
        }
    ]

    for msg in recent_messages:
        if msg.role not in {"user", "assistant", "system"}:
            continue

        messages.append(
            {
                "role": msg.role,
                "content": msg.content,
            }
        )

    return messages