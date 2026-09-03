import json

import httpx

from ...config import Settings
from ..schemas import LLMResponse, Message, ToolCall


class OllamaLLMProvider:
    """Local Ollama chat completion adapter with tool support."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = settings.ollama_reasoning_model
        self.base_url = settings.ollama_base_url.rstrip("/")
        self._timeout = httpx.Timeout(120.0, connect=10.0)

    def _to_ollama_messages(self, messages: list[Message]) -> list[dict]:
        out: list[dict] = []
        for m in messages:
            item: dict = {"role": m.role}
            if m.content:
                item["content"] = m.content
            if m.tool_calls:
                item["tool_calls"] = [
                    {
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        }
                    }
                    for tc in m.tool_calls
                ]
            if m.tool_call_id:
                item["tool_call_id"] = m.tool_call_id
            out.append(item)
        return out

    def generate(
        self,
        messages: list[Message],
        *,
        tools: list | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        payload: dict = {
            "model": self.model,
            "messages": self._to_ollama_messages(messages),
            "stream": False,
        }
        if tools is not None:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.input_schema,
                    },
                }
                for t in tools
            ]
        if temperature is not None:
            payload["options"] = {"temperature": temperature}
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        message = data.get("message", {})
        content = message.get("content") or None
        tool_calls = []
        for tc in message.get("tool_calls", []):
            fn = tc.get("function", {})
            args = fn.get("arguments")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            tool_calls.append(
                ToolCall(
                    id=tc.get("id", "unknown"),
                    name=fn.get("name", ""),
                    arguments=args or {},
                )
            )
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason="tool_calls" if tool_calls else "stop",
            model=self.model,
            usage=data.get("usage"),
        )
