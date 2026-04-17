import json

def sse_event(event: str, data: dict):
    payload = json.dumps(data, ensure_ascii=False)
    return f"event:{event}\ndata:{payload}\n\n"