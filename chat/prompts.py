import json
from django.conf import settings


def build_agent_messages(recent_messages, tool_specs):
    tool_text = json.dumps(tool_specs, ensure_ascii=False, indent=2)

    system_prompt = f"""
你是一个专业、准确、简洁的 AI 助手。

你可以使用以下工具：
{tool_text}

当你不需要工具时，请输出 JSON：
{{
  "type": "final",
  "answer": "你的最终回答"
}}

当你需要调用工具时，请输出 JSON：
{{
  "type": "tool_call",
  "tool_name": "工具名",
  "arguments":{{
    "参数名": "参数值"
}}
}}

注意：
- 只能输出 JSON
- 不要输出额外解释
- 如果信息不足但仍可以先问用户，可以直接输出 final
""".strip()

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    for msg in recent_messages:
        if msg.role not in {"user", "assistant", "tool", "system"}:
            continue
        messages.append(
            {
                "role": msg.role,
                "content": msg.content,
            }
        )

    return messages