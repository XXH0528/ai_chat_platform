from abc import ABC, abstractmethod
from django.conf import settings
from openai import OpenAI


class BaseLLMAdapter(ABC):
    @abstractmethod
    def generate(self, messages):
        raise NotImplementedError


class StubLLMAdapter(BaseLLMAdapter):
    def generate(self, messages):
        last_user_message = ""
        for item in reversed(messages):
            if item["role"] == "user":
                last_user_message = item["content"]
                break

        return f"这是 Stub LLM 的回复。你刚才说的是：{last_user_message}"


class OpenAIAdapter(BaseLLMAdapter):
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def generate(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
        )
        return response.choices[0].message.content or ""


def get_llm_adapter():
    if settings.OPENAI_API_KEY:
        return OpenAIAdapter()
    return StubLLMAdapter()