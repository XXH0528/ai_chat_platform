from .models import Conversation, Message


def create_conversation(title: str = "") -> Conversation:
    title = (title or "").strip()
    if not title:
        title = "新建会话"
    return Conversation.objects.create(title=title)


def append_user_message(conversation: Conversation, content: str, client_message_id: str = "") -> Message:
    metadata = {}
    if client_message_id:
        metadata["client_message_id"] = client_message_id

    message = Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        content=content,
        token_count=0,
        metadata=metadata,
    )

    if not conversation.title:
        if conversation.messages.filter(role=Message.Role.USER).count() == 1:
            conversation.title = content[:20]
            conversation.save()

    return message


def append_mock_assistant_message(conversation: Conversation, user_content: str) -> Message:
    reply = f"这是一个模拟回复：你刚刚说的是『{user_content}』。下一节课我们会把这里替换成真正的 LLM 调用。"

    return Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content=reply,
        token_count=0,
        metadata={"mock": True},
    )