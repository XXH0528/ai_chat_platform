import time


class ToolExecutionError(Exception):
    pass


class BaseTool:
    name = "base_tool"
    description = ""
    input_schema = {}

    def validate(self, arguments: dict):
        required = self.input_schema.get("required", [])
        for key in required:
            if key not in arguments:
                raise ToolExecutionError(f"Missing required argument:{key}")

    def run(self, arguments: dict):
        raise NotImplementedError


class GetWeatherTool(BaseTool):
    name = "get_weather"
    description = "根据城市名查询天气（课堂演示版，返回模拟结果）"
    input_schema = {
        "type": "object",
        "properties": {
            "city": {"type": "string"},
        },
        "required": ["city"],
    }

    def run(self, arguments: dict):
        self.validate(arguments)
        city = arguments["city"]
        return {
            "city": city,
            "weather": "晴",
            "temperature": "26C",
            "source": "mock_weather_service",
        }


class SearchDocsTool(BaseTool):
    name = "search_docs"
    description = "根据关键词搜索知识库（课堂演示版）"
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
        },
        "required": ["query"],
    }

    def run(self, arguments: dict):
        self.validate(arguments)
        query = arguments["query"]
        return {
            "query": query,
            "results": [
                {"title": "Django 官方文档", "snippet": "Django makes it easier..."},
                {"title": "DRF 教程", "snippet": "Serialization is the process..."},
            ],
            "source": "mock_kb",
        }


class ToolRegistry:
    def __init__(self):
        self.tools = {
            "get_weather": GetWeatherTool(),
            "search_docs": SearchDocsTool(),
        }

    def list_tool_specs(self):
        specs = []
        for tool in self.tools.values():
            specs.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
            )
        return specs

    def get_tool(self, tool_name: str):
        if tool_name not in self.tools:
            raise ToolExecutionError(f"Unknown tool:{tool_name}")
        return self.tools[tool_name]

    def execute(self, tool_name: str, arguments: dict):
        tool = self.get_tool(tool_name)
        start = time.perf_counter()
        result = tool.run(arguments)
        latency_ms = int((time.perf_counter() - start) * 1000)
        return result, latency_ms