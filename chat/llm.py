import json
from abc import ABC, abstractmethod
from django.conf import settings
from openai import OpenAI


class BaseLLMAdapter(ABC):
    @abstractmethod
    def generate(self, messages):
        raise NotImplementedError

    @abstractmethod
    def stream_generate(self, messages):
        raise NotImplementedError


class StubLLMAdapter(BaseLLMAdapter):
    def generate(self, messages):
        last_user_message = ""
        for item in reversed(messages):
            if item["role"] == "user":
                last_user_message = item["content"]
                break

        if "天气" in last_user_message:
            return json.dumps(
                {
                    "type": "tool_call",
                    "tool_name": "get_weather",
                    "arguments": {"city": "北京"},
                },
                ensure_ascii=False,
            )

        return json.dumps(
            {
                "type": "final",
                "answer": f"这是 Stub 的最终回答。你刚才说的是：{last_user_message}",
            },
            ensure_ascii=False,
        )

    def stream_generate(self, messages):
        text = self.generate(messages)
        for ch in text:
            yield ch


class OpenAIAdapter(BaseLLMAdapter):
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def generate(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or "{}"

    def stream_generate(self, messages):
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield delta


def get_llm_adapter():
    if settings.OPENAI_API_KEY:
        return OpenAIAdapter()
    return StubLLMAdapter()