from django.db import models
import uuid


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Conversation(BaseModel):
    class State(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    conversation_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=255, blank=True, default="")
    state = models.CharField(max_length=32, choices=State.choices, default=State.ACTIVE)

    def __str__(self):
        return f"{self.conversation_id} -{self.title or 'Untitled'}"


class Message(BaseModel):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"
        TOOL = "tool", "Tool"

    message_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    role = models.CharField(max_length=32, choices=Role.choices)
    content = models.TextField()
    token_count = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    sequence_no = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.role}:{self.content[:30]}"